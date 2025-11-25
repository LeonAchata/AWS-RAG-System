#!/usr/bin/env python3
"""
AWS CDK App - Punto de entrada para la infraestructura
"""
import os
from aws_cdk import App, Environment
from stacks.rag_stack import RagStack


app = App()

# Configuración del entorno
env = Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION', 'us-east-1')
)

# Crear el stack principal
RagStack(
    app,
    "RagSystemStack",
    env=env,
    description="Sistema RAG completo con Amazon Bedrock y OpenSearch"
)

app.synth()
