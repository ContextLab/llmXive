#!/bin/bash
# Full experiment suite runner for llmXive project
# This script executes the complete experiment and generates all required outputs.

set -e  # Exit on error

echo "=========================================="
echo "llmXive Full Experiment Suite"
echo "=========================================="
echo ""

# Set environment variables for CPU constraints
export OMP_NUM_THREADS=2
echo "Set OMP_NUM_THREADS=$OMP_NUM_THREADS"

# Ensure we're in the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"
echo ""

# Step 1: Verify required artifacts exist
echo "Step 1: Verifying required artifacts..."
if [ ! -f "data/processed/empirical_results.json" ]; then
    echo "  Note: empirical_results.json not found. It will be generated in Step 2."
else
    echo "  ✓ empirical_results.json exists"
fi

if [ ! -f "src/config/defaults.yaml" ]; then
    echo "  ✗ ERROR: src/config/defaults.yaml not found!"
    exit 1
else
    echo "  ✓ src/config/defaults.yaml exists"
fi

if [ ! -f "scripts/run_symbolic_verification.py" ]; then
    echo "  ✗ ERROR: scripts/run_symbolic_verification.py not found!"
    exit 1
else
    echo "  ✓ scripts/run_symbolic_verification.py exists"
fi

echo ""

# Step 2: Run symbolic verification
echo "Step 2: Running symbolic verification..."
python scripts/run_symbolic_verification.py
echo "  ✓ Symbolic verification complete"
echo ""

# Step 3: Run heavy-tailed validation
echo "Step 3: Running heavy-tailed validation..."
python scripts/run_heavy_tailed_validation.py
echo "  ✓ Heavy-tailed validation complete"
echo ""

# Step 4: Run full experiment sweep
echo "Step 4: Running full experiment sweep..."
python src/main.py --run-full-sweep
echo "  ✓ Full experiment sweep complete"
echo ""

# Step 5: Verify output files
echo "Step 5: Verifying output files..."
REQUIRED_FILES=(
    "data/processed/empirical_results.json"
    "data/processed/statistical_report.json"
    "data/processed/heavy_tailed_results.json"
    "data/processed/construct_validity_report.json"
    "data/processed/correlation_sweep_results.json"
    "logs/symbolic_verification.log"
)

ALL_FILES_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file exists"
    else
        echo "  ✗ ERROR: $file not found!"
        ALL_FILES_EXIST=false
    fi
done

echo ""

if [ "$ALL_FILES_EXIST" = true ]; then
    echo "=========================================="
    echo "✓ All steps completed successfully!"
    echo "=========================================="
    echo ""
    echo "Generated artifacts:"
    ls -lh data/processed/
    echo ""
    echo "Log files:"
    ls -lh logs/
    exit 0
else
    echo "=========================================="
    echo "✗ Some required files are missing!"
    echo "=========================================="
    exit 1
fi
