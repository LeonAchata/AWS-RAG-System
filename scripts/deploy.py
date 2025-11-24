#!/usr/bin/env python3
"""
Script de deployment del sistema RAG
Facilita el deployment con opciones preconfiguradas
"""
import subprocess
import sys
import argparse


def run_command(command: str, description: str = None):
    """Ejecuta un comando y maneja errores"""
    if description:
        print(f"\n🔧 {description}...")
    
    print(f"$ {command}\n")
    
    result = subprocess.run(command, shell=True)
    
    if result.returncode != 0:
        print(f"\n❌ Error ejecutando: {command}")
        sys.exit(1)
    
    return result


def check_prerequisites():
    """Verifica que estén instalados los prerequisitos"""
    print("🔍 Verificando prerequisitos...")
    
    # Verificar Node.js
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        print("✅ Node.js instalado")
    except:
        print("❌ Node.js no encontrado. Instalar desde: https://nodejs.org/")
        sys.exit(1)
    
    # Verificar AWS CLI
    try:
        subprocess.run(["aws", "--version"], check=True, capture_output=True)
        print("✅ AWS CLI instalado")
    except:
        print("❌ AWS CLI no encontrado. Instalar: pip install awscli")
        sys.exit(1)
    
    # Verificar CDK
    try:
        subprocess.run(["cdk", "--version"], check=True, capture_output=True)
        print("✅ AWS CDK instalado")
    except:
        print("❌ AWS CDK no encontrado. Instalar: npm install -g aws-cdk")
        sys.exit(1)
    
    print("\n✅ Todos los prerequisitos están instalados\n")


def install_dependencies():
    """Instala dependencias de Python"""
    print("📦 Instalando dependencias...")
    
    # Dependencias de CDK
    run_command(
        "pip install -r requirements.txt",
        "Instalando dependencias de CDK"
    )
    
    # Dependencias de Lambdas
    run_command(
        "pip install -r ../lambda/ingestion/requirements.txt",
        "Instalando dependencias de Lambda Ingestion"
    )
    
    run_command(
        "pip install -r ../lambda/query/requirements.txt",
        "Instalando dependencias de Lambda Query"
    )
    
    # Dependencias compartidas
    run_command(
        "pip install -r ../requirements.txt",
        "Instalando dependencias compartidas"
    )


def bootstrap_cdk(profile: str = None):
    """Bootstrap de CDK en la cuenta AWS"""
    cmd = "cdk bootstrap"
    if profile:
        cmd += f" --profile {profile}"
    
    run_command(cmd, "Bootstrapping CDK (solo necesario la primera vez)")


def synthesize(profile: str = None):
    """Sintetiza el template de CloudFormation"""
    cmd = "cdk synth"
    if profile:
        cmd += f" --profile {profile}"
    
    run_command(cmd, "Sintetizando template de CloudFormation")


def diff(profile: str = None):
    """Muestra los cambios que se aplicarán"""
    cmd = "cdk diff"
    if profile:
        cmd += f" --profile {profile}"
    
    run_command(cmd, "Mostrando cambios a aplicar")


def deploy(profile: str = None, auto_approve: bool = False):
    """Deploya el stack en AWS"""
    cmd = "cdk deploy"
    if profile:
        cmd += f" --profile {profile}"
    if auto_approve:
        cmd += " --require-approval never"
    
    run_command(cmd, "Deployando stack en AWS")


def destroy(profile: str = None, force: bool = False):
    """Elimina el stack de AWS"""
    if not force:
        response = input("\n⚠️  ¿Estás seguro de que quieres eliminar el stack? (yes/no): ")
        if response.lower() != "yes":
            print("Operación cancelada")
            return
    
    cmd = "cdk destroy"
    if profile:
        cmd += f" --profile {profile}"
    if force:
        cmd += " --force"
    
    run_command(cmd, "Eliminando stack de AWS")


def main():
    parser = argparse.ArgumentParser(
        description="Script de deployment del sistema RAG"
    )
    
    parser.add_argument(
        "action",
        choices=["check", "install", "bootstrap", "synth", "diff", "deploy", "destroy", "all"],
        help="Acción a realizar"
    )
    
    parser.add_argument(
        "--profile",
        help="Perfil de AWS a usar",
        default=None
    )
    
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Auto-aprobar cambios (no pedir confirmación)"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar operación sin confirmación"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Sistema RAG - Deployment Script")
    print("=" * 60)
    
    try:
        if args.action == "check":
            check_prerequisites()
        
        elif args.action == "install":
            install_dependencies()
        
        elif args.action == "bootstrap":
            check_prerequisites()
            bootstrap_cdk(args.profile)
        
        elif args.action == "synth":
            synthesize(args.profile)
        
        elif args.action == "diff":
            diff(args.profile)
        
        elif args.action == "deploy":
            check_prerequisites()
            deploy(args.profile, args.auto_approve)
        
        elif args.action == "destroy":
            destroy(args.profile, args.force)
        
        elif args.action == "all":
            check_prerequisites()
            install_dependencies()
            bootstrap_cdk(args.profile)
            synthesize(args.profile)
            diff(args.profile)
            deploy(args.profile, args.auto_approve)
        
        print("\n" + "=" * 60)
        print("✅ Operación completada exitosamente")
        print("=" * 60 + "\n")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
