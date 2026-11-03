$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
& "$PSScriptRoot\py313venv\Scripts\python.exe" -m uvicorn turbineopt.api.main:app --host 127.0.0.1 --port 8000
