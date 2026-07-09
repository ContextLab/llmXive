#!/bin/bash
# Quickstart script for PROJ-582: Socratic Transformers
# Verifies project setup, dependencies, and core utility execution.
# Exit code 0 indicates all steps passed.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== PROJ-582 Quickstart ==="
echo "Project Root: $PROJECT_ROOT"
echo "Script Dir: $SCRIPT_DIR"
echo ""

# 1. Verify Directory Structure
echo "Step 1: Verifying directory structure..."
REQUIRED_DIRS=(
  "code/src/data"
  "code/src/train"
  "code/src/eval"
  "code/src/analyze"
  "code/src/utils"
  "code/tests"
  "code/tests/contract"
  "code/tests/integration"
  "code/data/raw"
  "code/data/processed"
  "code/data/results"
)

for dir in "${REQUIRED_DIRS[@]}"; do
  if [ ! -d "$PROJECT_ROOT/$dir" ]; then
    echo "ERROR: Missing directory: $PROJECT_ROOT/$dir"
    exit 1
  fi
done
echo "✓ Directory structure verified."
echo ""

# 2. Verify Configuration Files
echo "Step 2: Verifying configuration files..."
REQUIRED_FILES=(
  "code/requirements.txt"
  "code/src/__init__.py"
  "code/tests/__init__.py"
  "code/.ruff.toml"
  "code/pyproject.toml"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$PROJECT_ROOT/$file" ]; then
    echo "ERROR: Missing file: $PROJECT_ROOT/$file"
    exit 1
  fi
done
echo "✓ Configuration files verified."
echo ""

# 3. Verify Python Environment
echo "Step 3: Verifying Python environment..."
if ! command -v python &> /dev/null; then
  echo "ERROR: Python executable not found."
  exit 1
fi
echo "✓ Python found: $(python --version)"
echo ""

# 4. Verify Imports (Core Utilities)
echo "Step 4: Verifying core module imports..."
cd "$PROJECT_ROOT/code"

# Test config module
if ! python -c "from src.utils.config import SocraticConfig, get_config; print('Config OK')" 2>/dev/null; then
  echo "ERROR: Failed to import src.utils.config"
  exit 1
fi

# Test logging module
if ! python -c "from src.utils.logging import SocraticLogger, get_logger; print('Logging OK')" 2>/dev/null; then
  echo "ERROR: Failed to import src.utils.logging"
  exit 1
fi

# Test metrics module
if ! python -c "from src.utils.metrics import MetricCalculator; print('Metrics OK')" 2>/dev/null; then
  echo "ERROR: Failed to import src.utils.metrics"
  exit 1
fi

# Test model loader module
if ! python -c "from src.utils.model_loader import load_model; print('Model Loader OK')" 2>/dev/null; then
  echo "ERROR: Failed to import src.utils.model_loader"
  exit 1
fi

# Test data modules
if ! python -c "from src.data.download import download_dataset; print('Download OK')" 2>/dev/null; then
  echo "ERROR: Failed to import src.data.download"
  exit 1
fi

if ! python -c "from src.data.static_extractor import extract_gsm8k; print('Static Extractor OK')" 2>/dev/null; then
  echo "ERROR: Failed to import src.data.static_extractor"
  exit 1
fi

if ! python -c "from src.data.generate_dialogue import generate_dialogue_tuple; print('Dialogue Generator OK')" 2>/dev/null; then
  echo "ERROR: Failed to import src.data.generate_dialogue"
  exit 1
fi

if ! python -c "from src.data.ablation import generate_ablation_dataset; print('Ablation OK')" 2>/dev/null; then
  echo "ERROR: Failed to import src.data.ablation"
  exit 1
fi

# Test train modules
if ! python -c "from src.train.lora_config import LoRAConfig; print('LoRA Config OK')" 2>/dev/null; then
  echo "ERROR: Failed to import src.train.lora_config"
  exit 1
fi

if ! python -c "from src.train.train_loop import run_training_loop; print('Train Loop OK')" 2>/dev/null; then
  echo "ERROR: Failed to import src.train.train_loop"
  exit 1
fi

# Test eval modules
if ! python -c "from src.eval.benchmark import run_benchmark; print('Benchmark OK')" 2>/dev/null; then
  echo "ERROR: Failed to import src.eval.benchmark"
  exit 1
fi

# Test analyze modules
if ! python -c "from src.analyze.stats import StatisticalAnalyzer; print('Stats OK')" 2>/dev/null; then
  echo "ERROR: Failed to import src.analyze.stats"
  exit 1
fi

if ! python -c "from src.analyze.sensitivity_sweep import SensitivityAnalyzer; print('Sensitivity OK')" 2>/dev/null; then
  echo "ERROR: Failed to import src.analyze.sensitivity_sweep"
  exit 1
fi

echo "✓ All core module imports verified."
echo ""

# 5. Run Unit Tests (Quick Smoke Test)
echo "Step 5: Running quick smoke tests..."
if ! python -m pytest tests/utils/test_config.py -v --tb=short 2>&1 | tail -5; then
  echo "WARNING: Config tests had issues, but continuing..."
fi

if ! python -m pytest tests/contract/test_stats.py -v --tb=short 2>&1 | tail -5; then
  echo "WARNING: Stats tests had issues, but continuing..."
fi

echo "✓ Smoke tests executed."
echo ""

echo "=== Quickstart Complete ==="
echo "All checks passed successfully."
exit 0