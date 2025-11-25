#!/usr/bin/env python3
"""
Script de validación de sintaxis CDK v2
Verifica que todos los archivos usen la sintaxis correcta de CDK v2
"""
import os
import re
from pathlib import Path


def check_file(file_path: str) -> tuple[bool, list[str]]:
    """
    Verifica que un archivo use sintaxis CDK v2
    
    Returns:
        Tuple de (es_valido, lista_de_errores)
    """
    errors = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Patrón obsoleto: import aws_cdk as cdk
    if re.search(r'import\s+aws_cdk\s+as\s+cdk', content):
        errors.append(f"❌ Usando 'import aws_cdk as cdk' (obsoleto)")
        errors.append(f"   Debe ser: from aws_cdk import App, Stack, ...")
    
    # Patrón obsoleto: from aws_cdk import core
    if re.search(r'from\s+aws_cdk\s+import\s+core', content):
        errors.append(f"❌ Usando 'from aws_cdk import core' (obsoleto)")
        errors.append(f"   Debe ser: from aws_cdk import Stack, Duration, ...")
    
    # Patrón obsoleto: cdk.App()
    if re.search(r'cdk\.App\(\)', content):
        errors.append(f"❌ Usando 'cdk.App()' (obsoleto)")
        errors.append(f"   Debe ser: App()")
    
    # Patrón obsoleto: cdk.Stack
    if re.search(r'cdk\.Stack', content):
        errors.append(f"❌ Usando 'cdk.Stack' (obsoleto)")
        errors.append(f"   Debe ser: Stack")
    
    # Patrón obsoleto: core.Stack
    if re.search(r'core\.Stack', content):
        errors.append(f"❌ Usando 'core.Stack' (obsoleto)")
        errors.append(f"   Debe ser: Stack")
    
    # Verificar imports correctos de CDK v2
    correct_patterns = [
        r'from aws_cdk import',
        r'from constructs import Construct'
    ]
    
    has_correct_import = any(re.search(pattern, content) for pattern in correct_patterns)
    
    if 'aws_cdk' in content and not has_correct_import:
        errors.append(f"⚠️  Referencias a aws_cdk pero sin imports correctos")
    
    return len(errors) == 0, errors


def main():
    """Valida todos los archivos Python en infrastructure"""
    print("🔍 Validando sintaxis CDK v2 en infrastructure/\n")
    print("=" * 60)
    
    infra_dir = Path(__file__).parent.parent / "infrastructure"
    python_files = list(infra_dir.rglob("*.py"))
    
    all_valid = True
    files_checked = 0
    
    for file_path in python_files:
        # Ignorar archivos de cache y venv
        if '__pycache__' in str(file_path) or 'venv' in str(file_path):
            continue
        
        files_checked += 1
        relative_path = file_path.relative_to(infra_dir.parent)
        
        is_valid, errors = check_file(str(file_path))
        
        if is_valid:
            print(f"✅ {relative_path}")
        else:
            print(f"\n❌ {relative_path}")
            for error in errors:
                print(f"   {error}")
            all_valid = False
    
    print("=" * 60)
    print(f"\n📊 Resumen:")
    print(f"   Archivos revisados: {files_checked}")
    
    if all_valid:
        print(f"   ✅ Todos los archivos usan CDK v2 correctamente")
        print(f"\n🎉 ¡Validación exitosa! El proyecto está listo para CDK v2")
    else:
        print(f"   ❌ Algunos archivos necesitan corrección")
        print(f"\n⚠️  Por favor, corrige los errores antes de hacer deploy")
    
    return 0 if all_valid else 1


if __name__ == "__main__":
    exit(main())
