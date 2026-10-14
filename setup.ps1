$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$bootstrapPython = if ($env:BOOKLET_PYTHON) { $env:BOOKLET_PYTHON } elseif (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }
$venvPython = Join-Path $root '.venv\Scripts\python.exe'

Push-Location $root
try {
    if (-not (Test-Path -LiteralPath $venvPython)) {
        & $bootstrapPython -m venv '.venv'
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the project virtual environment.' }
    }

    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw 'Could not update pip in the project virtual environment.' }

    & $venvPython -m pip install -r '.\requirements.txt'
    if ($LASTEXITCODE -ne 0) { throw 'Could not install the Python project requirements.' }

    & npm.cmd install
    if ($LASTEXITCODE -ne 0) { throw 'Could not install the Node.js project requirements.' }

    Write-Host 'Project environment ready. Use npm.cmd run build or npm.cmd test.'
}
finally {
    Pop-Location
}
