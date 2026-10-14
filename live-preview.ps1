$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) { throw 'Project virtual environment not found. Run npm.cmd run setup once.' }
$python = $venvPython
$pdf = '.\output\pdf\Modular_Booklet_Showcase_spreads.pdf'

Push-Location $root
try {
    & $python '.\planner.py'
    if ($LASTEXITCODE -ne 0) { throw 'The layout planner failed.' }

    $watcher = Start-Process -FilePath 'powershell.exe' `
        -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $root 'tools\watch-planner.ps1'), '-ProjectRoot', $root, '-PythonPath', $python) `
        -WindowStyle Hidden -PassThru

    Write-Host 'Live preview is running.' -ForegroundColor Green
    Write-Host 'Save a content, design, image, or layout file to rebuild the PDF.'
    Write-Host 'Keep this window open; press Ctrl+C to stop.'
    & '.\node_modules\.bin\typst.cmd' watch '.\main.typ' $pdf --open
}
finally {
    if ($watcher -and -not $watcher.HasExited) {
        Stop-Process -Id $watcher.Id -Force
    }
    Pop-Location
}
