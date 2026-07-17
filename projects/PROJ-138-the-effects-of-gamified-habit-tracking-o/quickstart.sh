#!/bin/bash
set -e

echo "=== llmXive Quickstart Validation ==="
echo "Project: PROJ-138-the-effects-of-gamified-habit-tracking-o"
echo "Task: T038 - Validation of pipeline execution"

# Ensure we are in the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Step 1: Verifying directory structure..."
python -c "from code.setup_project_structure import main; main()"

echo "Step 2: Generating synthetic data (if needed)..."
python -c "from code.data.synthetic_generator import main; main()"

echo "Step 3: Running data ingestion and validation..."
python -c "from code.data.ingestion import main; main()"

echo "Step 4: Running weekly aggregation..."
python -c "from code.data.aggregation import main; main()"

echo "Step 5: Merging datasets..."
python -c "from code.data.merge import main; main()"

echo "Step 6: Running statistical modeling..."
python -c "from code.analysis.modeling import main; main()"

echo "Step 7: Running survival analysis..."
python -c "from code.analysis.survival import main; main()"

echo "Step 8: Running robustness analysis..."
python -c "from code.analysis.robustness import main; main()"

echo "Step 9: Generating final report..."
python -c "from code.reports.generate_report import main; main()"

echo "Step 10: Updating versioning state..."
python -c "from code.utils.versioning_runner import main; main()"

echo "=== Quickstart Validation Complete ==="
echo "All pipeline stages executed successfully."