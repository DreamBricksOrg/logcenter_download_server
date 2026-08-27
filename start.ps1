# Starts the LogCenter Download Flask app.
# Creates the virtualenv and installs dependencies on first run, then
# launches the dev server.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Criando virtualenv em .venv ..."
    python -m venv .venv
}

if (-not (Test-Path ".env")) {
    Write-Host "Nenhum .env encontrado, copiando .env.example. Edite-o com suas credenciais reais antes de rodar aggregations de verdade."
    Copy-Item ".env.example" ".env"
}

Write-Host "Instalando dependencias..."
& $venvPython -m pip install -q -r requirements.txt

Write-Host "Subindo o servidor em http://127.0.0.1:5000 (Ctrl+C para parar)"
& $venvPython -m flask --app app run --debug
