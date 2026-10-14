$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) { throw 'Project virtual environment not found. Run npm.cmd run setup once.' }
$python = $venvPython

Push-Location $root
try {
    & $python -m unittest discover -s '.\tests' -v
    if ($LASTEXITCODE -ne 0) { throw 'Planner tests failed.' }
}
finally {
    Pop-Location
}
