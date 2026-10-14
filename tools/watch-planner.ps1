param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonPath
)

$ErrorActionPreference = 'Continue'

function Get-ContentFingerprint {
    $watched = @(
        Get-ChildItem -LiteralPath (Join-Path $ProjectRoot 'content') -Recurse -File
        Get-Item -LiteralPath (Join-Path $ProjectRoot 'planner.py')
    )
    return ($watched | Sort-Object FullName | ForEach-Object {
        '{0}|{1}|{2}' -f $_.FullName, $_.LastWriteTimeUtc.Ticks, $_.Length
    }) -join "`n"
}

$lastFingerprint = Get-ContentFingerprint
while ($true) {
    Start-Sleep -Milliseconds 700
    $nextFingerprint = Get-ContentFingerprint
    if ($nextFingerprint -ne $lastFingerprint) {
        Push-Location $ProjectRoot
        try {
            & $PythonPath '.\planner.py'
        }
        finally {
            Pop-Location
        }
        $lastFingerprint = $nextFingerprint
    }
}
