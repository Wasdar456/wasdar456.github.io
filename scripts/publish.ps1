param(
    [string]$Message = "notes: update",
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    python -m venv (Join-Path $ProjectRoot ".venv")
    & $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
}

& $VenvPython (Join-Path $ProjectRoot "scripts\generate_site_data.py")
& $VenvPython (Join-Path $ProjectRoot "scripts\prepublish_check.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $VenvPython -m mkdocs build --strict --config-file (Join-Path $ProjectRoot "mkdocs.yml")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($NoPush) {
    Write-Output "Checks passed. Push skipped."
    exit 0
}

git -C $ProjectRoot rev-parse --is-inside-work-tree | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "This is not a Git clone. Clone the homepage repository before publishing."
}

git -C $ProjectRoot add -- docs/notes data/resources.yml docs/resources/index.md
git -C $ProjectRoot diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Output "No note or resource changes to publish."
    exit 0
}

git -C $ProjectRoot commit -m $Message
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git -C $ProjectRoot push origin main
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Output "Upload complete. GitHub Pages should update in a few minutes."
