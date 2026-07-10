# Script to check and fix formatting/linting for PROJ-058 (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "Running Black formatting check..."
try {
    black --check code/ tests/
} catch {
    Write-Host "Formatting issues found. Running Black to fix..."
    black code/ tests/
}

Write-Host "Running Ruff linting check..."
try {
    ruff check code/ tests/
} catch {
    Write-Host "Linting issues found. Attempting auto-fix..."
    ruff check --fix code/ tests/
}

Write-Host "All checks passed."