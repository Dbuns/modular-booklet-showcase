$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) { throw 'Project virtual environment not found. Run npm.cmd run setup once.' }
$python = $venvPython

Push-Location $root
try {
    & $python '.\planner.py'
    if ($LASTEXITCODE -ne 0) { throw 'The layout planner failed.' }

    $spreadPdf = '.\output\pdf\Modular_Booklet_Showcase_spreads.pdf'
    $printPdf = '.\output\pdf\Modular_Booklet_Showcase_A5.pdf'
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $spreadPdf) | Out-Null

    & '.\node_modules\.bin\typst.cmd' compile '.\main.typ' $spreadPdf
    if ($LASTEXITCODE -ne 0) { throw 'Typst compilation failed.' }

    & $python '.\tools\split_spreads.py' $spreadPdf $printPdf
    if ($LASTEXITCODE -ne 0) { throw 'A5 print export failed.' }
}
finally {
    Pop-Location
}
