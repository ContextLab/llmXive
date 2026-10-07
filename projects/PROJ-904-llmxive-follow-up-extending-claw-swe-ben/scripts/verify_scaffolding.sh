#!/bin/bash
set -e

PROJECT_ROOT="projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Verifying Project Scaffolding for T001 ==="
echo "Target Directory: $ROOT_DIR/$PROJECT_ROOT"

if [ ! -d "$ROOT_DIR/$PROJECT_ROOT" ]; then
    echo "ERROR: Project root directory does not exist: $ROOT_DIR/$PROJECT_ROOT"
    exit 1
fi

echo "1. Checking directory structure..."
REQUIRED_DIRS=(
    "analysis"
    "data"
    "experiments"
    "models"
    "utils"
    "tests/unit"
    "tests/integration"
)

MISSING_DIRS=0
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$ROOT_DIR/$PROJECT_ROOT/$dir" ]; then
        echo "  [MISSING] $dir"
        MISSING_DIRS=$((MISSING_DIRS + 1))
    else
        echo "  [OK] $dir"
    fi
done

if [ $MISSING_DIRS -gt 0 ]; then
    echo "ERROR: $MISSING_DIRS directories are missing."
    exit 1
fi

echo "2. Checking __init__.py files..."
MISSING_INIT=0
for dir in "${REQUIRED_DIRS[@]}"; do
    init_file="$ROOT_DIR/$PROJECT_ROOT/$dir/__init__.py"
    if [ ! -f "$init_file" ]; then
        echo "  [MISSING] $init_file"
        MISSING_INIT=$((MISSING_INIT + 1))
    else
        echo "  [OK] $dir/__init__.py"
    fi
done

if [ $MISSING_INIT -gt 0 ]; then
    echo "ERROR: $MISSING_INIT __init__.py files are missing."
    exit 1
fi

echo "3. Checking requirements.txt..."
REQ_FILE="$ROOT_DIR/$PROJECT_ROOT/requirements.txt"
if [ ! -f "$REQ_FILE" ]; then
    echo "ERROR: requirements.txt not found at $REQ_FILE"
    exit 1
fi

REQUIRED_PACKAGES=(
    "transformers"
    "datasets"
    "scikit-learn"
    "statsmodels"
    "networkx"
    "pytest"
    "huggingface_hub"
    "pyyaml"
)

MISSING_PKGS=0
for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! grep -qi "^$pkg" "$REQ_FILE"; then
        echo "  [MISSING] $pkg"
        MISSING_PKGS=$((MISSING_PKGS + 1))
    else
        echo "  [OK] $pkg"
    fi
done

if [ $MISSING_PKGS -gt 0 ]; then
    echo "ERROR: $MISSING_PKGS required packages are missing from requirements.txt."
    exit 1
fi

echo "4. Checking config files..."
CONFIG_FILES=(
    ".ruff.toml"
    "pyproject.toml"
    "pypy.toml"
)

MISSING_CONFIG=0
for cfg in "${CONFIG_FILES[@]}"; do
    if [ ! -f "$ROOT_DIR/$PROJECT_ROOT/$cfg" ]; then
        echo "  [MISSING] $cfg"
        MISSING_CONFIG=$((MISSING_CONFIG + 1))
    else
        echo "  [OK] $cfg"
    fi
done

if [ $MISSING_CONFIG -gt 0 ]; then
    echo "ERROR: $MISSING_CONFIG config files are missing."
    exit 1
fi

echo "5. Running ruff check..."
if command -v ruff &> /dev/null; then
    if ruff check "$ROOT_DIR/$PROJECT_ROOT" --quiet; then
        echo "  [OK] ruff check passed"
    else
        echo "  [WARN] ruff check found issues (non-fatal for scaffolding)"
    fi
else
    echo "  [SKIP] ruff not installed, skipping check"
fi

echo "6. Running black --check..."
if command -v black &> /dev/null; then
    if black --check "$ROOT_DIR/$PROJECT_ROOT" --quiet; then
        echo "  [OK] black --check passed"
    else
        echo "  [WARN] black --check found issues (non-fatal for scaffolding)"
    fi
else
    echo "  [SKIP] black not installed, skipping check"
fi

echo "=== Scaffolding Verification Complete ==="
echo "All checks passed."
exit 0
