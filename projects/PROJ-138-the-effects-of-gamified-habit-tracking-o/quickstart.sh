#!/bin/bash
# Quickstart Script for PROJ-138: The Effects of Gamified Habit Tracking
# This script orchestrates the full pipeline from data generation to reporting.

set -e  # Exit immediately on error

# Set up environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure Python virtual environment is activated or create one if needed
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "WARNING: requirements.txt not found. Installing common dependencies manually."
    pip install pandas numpy scikit-learn statsmodels seaborn matplotlib pyyaml pingouin scipy lifelines
fi

# Create directory structure if not exists
echo "Ensuring directory structure..."
python code/setup_project_structure.py

# Step 1: Consent Check (Pre-flight)
echo ">>> Step 1: Consent Check"
python code/data/validation.py --action consent_check

# Step 2: Data Generation (Synthetic)
echo ">>> Step 2: Generating Synthetic Data"
python code/data/synthetic_generator.py --seed 42 --n_users 100 --weeks 50

# Step 3: Ingestion
echo ">>> Step 3: Ingesting Data"
python code/data/ingestion.py

# Step 4: Aggregation
echo ">>> Step 4: Aggregating Data"
python code/data/aggregation.py

# Step 5: Merge
echo ">>> Step 5: Merging Datasets"
python code/data/merge.py

# Step 6: Psychometrics (Cronbach's Alpha)
echo ">>> Step 6: Calculating Psychometrics"
python code/data/validation.py --action cronbach

# Step 7: Modeling
echo ">>> Step 7: Running Statistical Models"
python code/analysis/modeling.py

# Step 8: Survival Analysis
echo ">>> Step 8: Running Survival Analysis"
python code/analysis/survival.py

# Step 9: Robustness (Bootstrapping)
echo ">>> Step 9: Running Robustness Checks"
python code/analysis/robustness.py

# Step 10: Report Generation
echo ">>> Step 10: Generating Final Report"
python code/reports/generate_report.py

# Step 11: Versioning
echo ">>> Step 11: Updating Versioning State"
python code/utils/versioning.py --action hash

echo ">>> Pipeline Complete. Check data/reports/final_analysis.html for results."
echo ">>> Run 'python code/scripts/run_quickstart_validation.py' to verify artifacts."
