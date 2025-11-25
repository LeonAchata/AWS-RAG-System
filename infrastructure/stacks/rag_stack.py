"""
Stack principal del sistema RAG
Define toda la infraestructura necesaria
"""
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    RemovalPolicy,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    aws_s3_notifications as s3n,
)
from constructs import Construct


class RagStack(Stack):
    """Stack principal del sistema RAG con AWS Bedrock y RDS PostgreSQL + pgvector"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Crear S3 Buckets
        self.create_s3_buckets()

        # 2. Crear RDS PostgreSQL con pgvector (público)
        self.create_rds_database()

        # 3. Crear Lambda Layer con dependencias compartidas
        self.create_lambda_layers()

        # 4. Crear Lambda de Ingesta
        self.create_ingestion_lambda()

        # 5. Crear Lambda de Query
        self.create_query_lambda()

        # 6. Crear API Gateway
        self.create_api_gateway()

        # 7. Configurar triggers S3
        self.configure_s3_triggers()

        # 8. Outputs útiles
        self.create_outputs()

    def create_s3_buckets(self):
        """Crea los buckets S3 necesarios"""
        
        # Bucket para documentos raw (sin procesar)
        self.raw_bucket = s3.Bucket(
            self,
            "RawDocumentsBucket",
            bucket_name=None,  # Auto-generado
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,  # Para desarrollo
            auto_delete_objects=True,  # Limpieza automática en destroy
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldVersions",
                    noncurrent_version_expiration=Duration.days(30)
                )
            ]
        )

        # Bucket para documentos procesados (opcional, para backup)
        self.processed_bucket = s3.Bucket(
            self,
            "ProcessedDocumentsBucket",
            bucket_name=None,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

    def create_rds_database(self):
        """Crea RDS PostgreSQL público con extensión pgvector (Free Tier)"""
        
        # Usar VPC por defecto
        self.vpc = ec2.Vpc.from_lookup(
            self,
            "DefaultVPC",
            is_default=True
        )
        
        # Credenciales en Secrets Manager
        self.db_credentials = rds.DatabaseSecret(
            self,
            "DBCredentials",
            username="rag_admin"
        )

        # Instancia RDS PostgreSQL pública
        self.database = rds.DatabaseInstance(
            self,
            "RagDatabase",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.MICRO  # Free Tier
            ),
            vpc=self.vpc,  # Usar VPC por defecto
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            credentials=rds.Credentials.from_secret(self.db_credentials),
            database_name="ragdb",
            allocated_storage=20,  # GB - Free Tier
            storage_type=rds.StorageType.GP2,
            backup_retention=Duration.days(0),  # Sin backups para desarrollo
            delete_automated_backups=True,
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False,
            publicly_accessible=True,  # RDS público
            multi_az=False  # Single AZ para Free Tier
        )

        # Security Group: permitir acceso desde cualquier IP (solo para demo)
        # En producción, limitar a IPs específicas
        self.database.connections.allow_default_port_from_any_ipv4(
            "Allow PostgreSQL from Lambda and internet"
        )

    def create_lambda_layers(self):
        """Crea Lambda Layers con dependencias compartidas"""
        
        # Layer con código compartido y dependencias
        self.shared_layer = lambda_.LayerVersion(
            self,
            "SharedCodeLayer",
            code=lambda_.Code.from_asset("../layer_build"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Código compartido y dependencias: Bedrock, PostgreSQL, PDF processing"
        )

    def create_ingestion_lambda(self):
        """Crea la función Lambda de ingesta de documentos"""
        
        # Rol IAM para Lambda de Ingesta
        ingestion_role = iam.Role(
            self,
            "IngestionLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # Permisos para Bedrock
        ingestion_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=["*"]
            )
        )

        # Función Lambda de Ingesta (sin VPC)
        self.ingestion_lambda = lambda_.Function(
            self,
            "IngestionLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/ingestion"),
            timeout=Duration.minutes(5),
            memory_size=2048,
            role=ingestion_role,
            layers=[self.shared_layer],
            environment={
                "DB_SECRET_ARN": self.db_credentials.secret_arn,
                "DB_NAME": "ragdb",
                "BEDROCK_EMBEDDING_MODEL": "amazon.titan-embed-text-v2:0",
                "CHUNK_SIZE": "800",
                "CHUNK_OVERLAP": "100"
            }
        )

        # Permisos para leer secret
        self.db_credentials.grant_read(self.ingestion_lambda)

        # Permisos de S3
        self.raw_bucket.grant_read(self.ingestion_lambda)
        self.processed_bucket.grant_write(self.ingestion_lambda)

    def create_query_lambda(self):
        """Crea la función Lambda para queries"""
        
        # Rol IAM para Lambda de Query
        query_role = iam.Role(
            self,
            "QueryLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # Permisos para Bedrock
        query_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=["*"]
            )
        )

        # Función Lambda de Query (sin VPC)
        self.query_lambda = lambda_.Function(
            self,
            "QueryLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/query"),
            timeout=Duration.seconds(60),
            memory_size=1024,
            role=query_role,
            layers=[self.shared_layer],
            environment={
                "DB_SECRET_ARN": self.db_credentials.secret_arn,
                "DB_NAME": "ragdb",
                "BEDROCK_EMBEDDING_MODEL": "amazon.titan-embed-text-v2:0",
                "BEDROCK_LLM_MODEL": "anthropic.claude-3-sonnet-20240229-v1:0",
                "TOP_K": "5",
                "MIN_SIMILARITY": "0.1",
                "USE_CACHE": "true"
            }
        )

        # Permisos para leer secret
        self.db_credentials.grant_read(self.query_lambda)

    def create_api_gateway(self):
        """Crea API Gateway REST para exponer endpoints"""
        
        # API Gateway REST
        self.api = apigateway.RestApi(
            self,
            "RagApi",
            rest_api_name="RAG System API",
            description="API para el sistema RAG con Bedrock",
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                throttling_rate_limit=100,
                throttling_burst_limit=200
            ),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # Recurso /query para consultas
        query_resource = self.api.root.add_resource("query")
        
        # Integración con Lambda de Query
        query_integration = apigateway.LambdaIntegration(
            self.query_lambda,
            proxy=True
        )
        
        # Método POST /query
        query_resource.add_method(
            "POST",
            query_integration,
            api_key_required=False  # Cambiar a True si se necesita API key
        )

        # Recurso /ingest para carga directa (opcional)
        ingest_resource = self.api.root.add_resource("ingest")
        
        # Integración con Lambda de Ingesta
        ingest_integration = apigateway.LambdaIntegration(
            self.ingestion_lambda,
            proxy=True
        )
        
        # Método POST /ingest
        ingest_resource.add_method(
            "POST",
            ingest_integration
        )

        # Health check endpoint
        health_resource = self.api.root.add_resource("health")
        health_resource.add_method(
            "GET",
            apigateway.MockIntegration(
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_templates={
                            "application/json": '{"status": "ok", "service": "RAG System"}'
                        }
                    )
                ],
                request_templates={
                    "application/json": '{"statusCode": 200}'
                }
            ),
            method_responses=[
                apigateway.MethodResponse(status_code="200")
            ]
        )

    def configure_s3_triggers(self):
        """Configura triggers de S3 para Lambda de ingesta"""
        
        # Notificación cuando se sube un archivo al bucket raw
        self.raw_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.ingestion_lambda),
            s3.NotificationKeyFilter(
                prefix="documents/",  # Solo procesar archivos en esta carpeta
                suffix=".pdf"  # Agregar más sufijos según necesidad
            )
        )
        
        # Agregar más notificaciones para otros formatos
        for suffix in [".docx", ".txt", ".md", ".html"]:
            self.raw_bucket.add_event_notification(
                s3.EventType.OBJECT_CREATED,
                s3n.LambdaDestination(self.ingestion_lambda),
                s3.NotificationKeyFilter(
                    prefix="documents/",
                    suffix=suffix
                )
            )

    def create_outputs(self):
        """Crea outputs útiles del stack"""
        
        # URL de la API
        CfnOutput(
            self,
            "ApiUrl",
            value=self.api.url,
            description="URL base de la API REST",
            export_name="RagApiUrl"
        )

        # Endpoint de query
        CfnOutput(
            self,
            "QueryEndpoint",
            value=f"{self.api.url}query",
            description="Endpoint para realizar consultas"
        )

        # Endpoint de ingest
        CfnOutput(
            self,
            "IngestEndpoint",
            value=f"{self.api.url}ingest",
            description="Endpoint para ingestar documentos"
        )

        # Nombre del bucket raw
        CfnOutput(
            self,
            "RawBucketName",
            value=self.raw_bucket.bucket_name,
            description="Nombre del bucket para documentos raw",
            export_name="RagRawBucketName"
        )

        # Endpoint de RDS
        CfnOutput(
            self,
            "DatabaseEndpoint",
            value=self.database.db_instance_endpoint_address,
            description="Endpoint de la base de datos PostgreSQL"
        )

        # Secret ARN
        CfnOutput(
            self,
            "DatabaseSecretArn",
            value=self.db_credentials.secret_arn,
            description="ARN del secret con credenciales de DB"
        )

        # ARN de Lambda de Ingesta
        CfnOutput(
            self,
            "IngestionLambdaArn",
            value=self.ingestion_lambda.function_arn,
            description="ARN de Lambda de Ingesta"
        )

        # ARN de Lambda de Query
        CfnOutput(
            self,
            "QueryLambdaArn",
            value=self.query_lambda.function_arn,
            description="ARN de Lambda de Query"
        )
