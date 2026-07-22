param(
    [Parameter(Mandatory = $true)]
    [string]$Source,

    [string]$Name = "",

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

$ImportArguments = @((Join-Path $ProjectRoot "scripts\import_notes.py"), $Source)
if ($Name) {
    $ImportArguments += @("--name", $Name)
}

& $VenvPython @ImportArguments
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

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
    throw "This is not a Git repository. Clone the homepage repository first."
}

git -C $ProjectRoot add -- docs/notes
git -C $ProjectRoot diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Output "No note changes to publish."
    exit 0
}

$CourseLabel = if ($Name) { $Name } else { Split-Path -Leaf (Resolve-Path -LiteralPath $Source) }
git -C $ProjectRoot commit -m "notes: update $CourseLabel"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git -C $ProjectRoot push origin main
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Output "Upload complete. GitHub Pages should update in a few minutes."
