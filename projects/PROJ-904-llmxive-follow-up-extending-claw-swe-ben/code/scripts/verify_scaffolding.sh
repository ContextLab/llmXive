#!/bin/bash
set -e

PROJECT_ROOT="projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Verifying scaffolding in $PROJECT_DIR..."

# 1. Check directories exist
echo "Checking directories..."
REQUIRED_DIRS=(
    "data"
    "data/intermediate"
    "analysis"
    "experiments"
    "models"
    "utils"
    "tests"
    "tests/unit"
    "tests/integration"
    "specs"
    "specs/001-context-fidelity-scaling-tradeoff"
    "specs/001-context-fidelity-scaling-tradeoff/contracts"
    "state"
    "scripts"
    "docs"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$PROJECT_DIR/$dir" ]; then
        echo "ERROR: Directory missing: $PROJECT_DIR/$dir"
        exit 1
    fi
done
echo "✓ All directories exist"

# 2. Check __init__.py files
echo "Checking __init__.py files..."
INIT_DIRS=(
    "data"
    "analysis"
    "experiments"
    "models"
    "utils"
    "tests"
    "tests/unit"
    "tests/integration"
    "specs"
    "specs/001-context-fidelity-scaling-tradeoff"
    "specs/001-context-fidelity-scaling-tradeoff/contracts"
    "state"
    "scripts"
    "docs"
)

for dir in "${INIT_DIRS[@]}"; do
    if [ ! -f "$PROJECT_DIR/$dir/__init__.py" ]; then
        echo "ERROR: Missing __init__.py in: $PROJECT_DIR/$dir"
        exit 1
    fi
done
echo "✓ All __init__.py files exist"

# 3. Check requirements.txt packages
echo "Checking requirements.txt..."
REQ_FILE="$PROJECT_DIR/requirements.txt"
if [ ! -f "$REQ_FILE" ]; then
    echo "ERROR: requirements.txt not found"
    exit 1
fi

REQUIRED_PACKAGES=("transformers" "datasets" "scikit-learn" "statsmodels" "networkx" "pytest" "huggingface_hub" "pyyaml")
for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! grep -qi "^$pkg" "$REQ_FILE"; then
        echo "ERROR: Required package missing in requirements.txt: $pkg"
        exit 1
    fi
done
echo "✓ All required packages in requirements.txt"

# 4. Check config files exist
echo "Checking config files..."
if [ ! -f "$PROJECT_DIR/.ruff.toml" ]; then
    echo "ERROR: .ruff.toml not found"
    exit 1
fi
if [ ! -f "$PROJECT_DIR/pyproject.toml" ]; then
    echo "ERROR: pyproject.toml not found"
    exit 1
fi
echo "✓ Config files exist"

# 5. Run ruff check
echo "Running ruff check..."
if command -v ruff &> /dev/null; then
    ruff check "$PROJECT_DIR" --config "$PROJECT_DIR/.ruff.toml" || {
        echo "WARNING: ruff check found issues (non-fatal for scaffolding)"
    }
else
    echo "INFO: ruff not installed, skipping check"
fi

# 6. Run black check
echo "Running black check..."
if command -v black &> /dev/null; then
    black --check "$PROJECT_DIR" --config "$PROJECT_DIR/pyproject.toml" || {
        echo "WARNING: black check found issues (non-fatal for scaffolding)"
    }
else
    echo "INFO: black not installed, skipping check"
fi

echo "✓ Scaffolding verification complete"
