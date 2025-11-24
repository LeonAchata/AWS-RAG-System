# PowerShell script para deployment rápido
# Uso: .\deploy.ps1 [action] [options]

param(
    [Parameter(Position=0)]
    [ValidateSet("check", "install", "bootstrap", "synth", "diff", "deploy", "destroy", "all")]
    [string]$Action = "check",
    
    [Parameter()]
    [string]$Profile = "",
    
    [Parameter()]
    [switch]$AutoApprove,
    
    [Parameter()]
    [switch]$Force
)

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "🚀 Sistema RAG - Deployment Script" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Cambiar al directorio infrastructure
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InfraDir = Join-Path (Split-Path -Parent $ScriptDir) "infrastructure"
Set-Location $InfraDir

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Invoke-Step {
    param(
        [string]$Command,
        [string]$Description
    )
    
    if ($Description) {
        Write-Host "`n🔧 $Description..." -ForegroundColor Green
    }
    
    Write-Host "$ $Command`n" -ForegroundColor Gray
    
    Invoke-Expression $Command
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n❌ Error ejecutando: $Command" -ForegroundColor Red
        exit 1
    }
}

function Test-Prerequisites {
    Write-Host "🔍 Verificando prerequisitos..." -ForegroundColor Cyan
    
    $allGood = $true
    
    # Node.js
    if (Test-Command "node") {
        Write-Host "✅ Node.js instalado" -ForegroundColor Green
    } else {
        Write-Host "❌ Node.js no encontrado. Instalar desde: https://nodejs.org/" -ForegroundColor Red
        $allGood = $false
    }
    
    # AWS CLI
    if (Test-Command "aws") {
        Write-Host "✅ AWS CLI instalado" -ForegroundColor Green
    } else {
        Write-Host "❌ AWS CLI no encontrado. Instalar: pip install awscli" -ForegroundColor Red
        $allGood = $false
    }
    
    # CDK
    if (Test-Command "cdk") {
        Write-Host "✅ AWS CDK instalado" -ForegroundColor Green
    } else {
        Write-Host "❌ AWS CDK no encontrado. Instalar: npm install -g aws-cdk" -ForegroundColor Red
        $allGood = $false
    }
    
    if (-not $allGood) {
        exit 1
    }
    
    Write-Host "`n✅ Todos los prerequisitos están instalados`n" -ForegroundColor Green
}

function Install-Dependencies {
    Write-Host "📦 Instalando dependencias..." -ForegroundColor Cyan
    
    Invoke-Step "pip install -r requirements.txt" "Instalando dependencias de CDK"
}

function Invoke-Bootstrap {
    $cmd = "cdk bootstrap"
    if ($Profile) { $cmd += " --profile $Profile" }
    Invoke-Step $cmd "Bootstrapping CDK"
}

function Invoke-Synth {
    $cmd = "cdk synth"
    if ($Profile) { $cmd += " --profile $Profile" }
    Invoke-Step $cmd "Sintetizando template de CloudFormation"
}

function Invoke-Diff {
    $cmd = "cdk diff"
    if ($Profile) { $cmd += " --profile $Profile" }
    Invoke-Step $cmd "Mostrando cambios a aplicar"
}

function Invoke-Deploy {
    $cmd = "cdk deploy"
    if ($Profile) { $cmd += " --profile $Profile" }
    if ($AutoApprove) { $cmd += " --require-approval never" }
    Invoke-Step $cmd "Deployando stack en AWS"
}

function Invoke-Destroy {
    if (-not $Force) {
        $response = Read-Host "`n⚠️  ¿Estás seguro de que quieres eliminar el stack? (yes/no)"
        if ($response -ne "yes") {
            Write-Host "Operación cancelada" -ForegroundColor Yellow
            return
        }
    }
    
    $cmd = "cdk destroy"
    if ($Profile) { $cmd += " --profile $Profile" }
    if ($Force) { $cmd += " --force" }
    Invoke-Step $cmd "Eliminando stack de AWS"
}

# Ejecutar acción
try {
    switch ($Action) {
        "check" {
            Test-Prerequisites
        }
        "install" {
            Install-Dependencies
        }
        "bootstrap" {
            Test-Prerequisites
            Invoke-Bootstrap
        }
        "synth" {
            Invoke-Synth
        }
        "diff" {
            Invoke-Diff
        }
        "deploy" {
            Test-Prerequisites
            Invoke-Deploy
        }
        "destroy" {
            Invoke-Destroy
        }
        "all" {
            Test-Prerequisites
            Install-Dependencies
            Invoke-Bootstrap
            Invoke-Synth
            Invoke-Diff
            Invoke-Deploy
        }
    }
    
    Write-Host "`n" -NoNewline
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 59) -ForegroundColor Cyan
    Write-Host "✅ Operación completada exitosamente" -ForegroundColor Green
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 59) -ForegroundColor Cyan
    Write-Host ""
    
} catch {
    Write-Host "`n❌ Error: $_" -ForegroundColor Red
    exit 1
}
