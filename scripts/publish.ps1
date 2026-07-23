param(
    [string]$Message = "notes: update",
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

git -C $ProjectRoot rev-parse --is-inside-work-tree | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "This is not a Git clone. Clone the homepage repository before publishing."
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Output "Creating the local Python environment..."
    python -m venv (Join-Path $ProjectRoot ".venv")
    & $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& $VenvPython (Join-Path $ProjectRoot "scripts\generate_site_data.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $VenvPython (Join-Path $ProjectRoot "scripts\prepublish_check.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $VenvPython -m mkdocs build --strict --config-file (Join-Path $ProjectRoot "mkdocs.yml")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Output ""
Write-Output "Files that differ from the latest local commit:"
$WorkingChanges = @(git -C $ProjectRoot status --short)
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ($WorkingChanges.Count -eq 0) {
    Write-Output "  (none)"
} else {
    $WorkingChanges | ForEach-Object { Write-Output "  $_" }
}

if ($NoPush) {
    Write-Output ""
    Write-Output "Checks passed. No commit was created and nothing was uploaded."
    exit 0
}

$Branch = (git -C $ProjectRoot branch --show-current).Trim()
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ($Branch -ne "main") {
    throw "Publishing is only allowed from main. Current branch: $Branch"
}

git -C $ProjectRoot add -A -- .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

git -C $ProjectRoot diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Output "No changes to publish."
    exit 0
}

Write-Output ""
Write-Output "Files included in this commit:"
git -C $ProjectRoot diff --cached --name-status |
    ForEach-Object { Write-Output "  $_" }
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

git -C $ProjectRoot commit -m $Message
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

git -C $ProjectRoot push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Output ""
    Write-Output "Upload failed. The commit is safe in the local repository but is not on GitHub."
    Write-Output "Do not run the script repeatedly. Check the error above and run git status -sb."
    exit $LASTEXITCODE
}

Write-Output ""
Write-Output "Upload complete. GitHub Pages should update in a few minutes."
