# Script para construir Lambda Layer usando Docker (compatible con Linux/Lambda)
Write-Host "=== Construyendo Lambda Layer con Docker ===" -ForegroundColor Green

# Limpiar directorio anterior
if (Test-Path "layer_build") {
    Remove-Item -Recurse -Force "layer_build"
}

# Crear estructura
New-Item -ItemType Directory -Force -Path "layer_build/python/shared" | Out-Null

# Copiar código compartido
Write-Host "Copiando código compartido..." -ForegroundColor Yellow
Copy-Item -Path "shared/*" -Destination "layer_build/python/shared/" -Recurse -Force

# Crear requirements.txt
$requirements = @"
psycopg2-binary>=2.9.9
pypdf2>=3.0.0
pdfplumber>=0.10.0
python-docx>=1.1.0
"@

Set-Content -Path "layer_build/requirements.txt" -Value $requirements

# Usar Docker para instalar dependencias en ambiente Linux
Write-Host "Instalando dependencias con Docker (Linux)..." -ForegroundColor Yellow
$absolutePath = Resolve-Path "layer_build"
$dockerCmd = "docker"
$dockerArgs = @(
    "run",
    "--rm",
    "-v",
    "${absolutePath}:/var/task",
    "--entrypoint",
    "",
    "public.ecr.aws/lambda/python:3.11",
    "pip",
    "install",
    "-r",
    "/var/task/requirements.txt",
    "-t",
    "/var/task/python/",
    "--no-cache-dir"
)
& $dockerCmd $dockerArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Lambda layer construido exitosamente en: layer_build" -ForegroundColor Green
    Write-Host "Ahora ejecuta: cd infrastructure; cdk deploy" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Error al construir el layer" -ForegroundColor Red
    exit 1
}
