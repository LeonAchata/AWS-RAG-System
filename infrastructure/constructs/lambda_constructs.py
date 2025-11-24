"""
Constructs reutilizables para el sistema RAG
"""
from aws_cdk import (
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class BedrockEnabledFunction(lambda_.Function):
    """
    Lambda Function con permisos de Bedrock preconfigurados
    Construct reutilizable para funciones que usan Bedrock
    """
    
    def __init__(
        self,
        scope: Construct,
        id: str,
        bedrock_models: list = None,
        **kwargs
    ):
        """
        Args:
            scope: Construct padre
            id: ID del construct
            bedrock_models: Lista de modelos de Bedrock a los que dar acceso
            **kwargs: Argumentos adicionales para lambda.Function
        """
        
        # Modelos por defecto si no se especifican
        if bedrock_models is None:
            bedrock_models = [
                "amazon.titan-embed-text-v2:0",
                "anthropic.claude-3-sonnet-20240229-v1:0",
                "anthropic.claude-3-5-sonnet-20240620-v1:0"
            ]
        
        # Crear rol si no se proporciona
        if 'role' not in kwargs:
            role = iam.Role(
                scope,
                f"{id}Role",
                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "service-role/AWSLambdaBasicExecutionRole"
                    )
                ]
            )
            
            # Agregar permisos de Bedrock
            role.add_to_policy(
                iam.PolicyStatement(
                    actions=[
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    resources=["*"]  # Bedrock requiere wildcard
                )
            )
            
            kwargs['role'] = role
        
        # Configuraciones por defecto
        if 'timeout' not in kwargs:
            kwargs['timeout'] = Duration.minutes(1)
        
        if 'memory_size' not in kwargs:
            kwargs['memory_size'] = 1024
        
        if 'log_retention' not in kwargs:
            kwargs['log_retention'] = logs.RetentionDays.ONE_WEEK
        
        # Llamar al constructor padre
        super().__init__(scope, id, **kwargs)


class RagLambdaLayer(lambda_.LayerVersion):
    """
    Lambda Layer preconfigurado para el sistema RAG
    """
    
    def __init__(
        self,
        scope: Construct,
        id: str,
        asset_path: str,
        description: str = "RAG System dependencies",
        **kwargs
    ):
        """
        Args:
            scope: Construct padre
            id: ID del construct
            asset_path: Ruta al código del layer
            description: Descripción del layer
        """
        
        super().__init__(
            scope,
            id,
            code=lambda_.Code.from_asset(asset_path),
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_11,
                lambda_.Runtime.PYTHON_3_10
            ],
            description=description,
            **kwargs
        )
