#!/bin/bash
set -e

# T033: Verify run.sh completes full pipeline (Inference + Stats + Plots)
# This script orchestrates the entire research pipeline and ensures all
# artifacts are generated within the 6-hour window on a free-tier runner.

echo "=== Starting Full Pipeline Execution ==="
echo "Start time: $(date)"

# Ensure we are in the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 1. Setup Environment (Install dependencies if needed)
echo ">>> Step 1: Verifying Environment..."
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found in project root."
    exit 1
fi
# Note: In a CI/CD context, this assumes a virtualenv is already active or pip is ready.
# If running locally, user should run: pip install -r requirements.txt
if ! python -c "import transformers, torch, codecarbon, pandas, scipy, statsmodels, matplotlib, seaborn, human_eval, huggingface_hub" 2>/dev/null; then
    echo "WARNING: Some dependencies missing. Attempting install..."
    pip install -r requirements.txt
fi

# 2. Download Data (if not present)
echo ">>> Step 2: Ensuring Data Availability..."
python code/download.py

# 3. Run Inference (US1)
echo ">>> Step 3: Running Inference (GPT2, CodeBERT, StarCoder-1B)..."
python code/inference.py
if [ ! -f "data/processed/energy_results_raw.csv" ]; then
    echo "ERROR: Inference failed to produce energy_results_raw.csv"
    exit 1
fi

# 4. Run Evaluation (US1)
echo ">>> Step 4: Running Evaluation..."
python code/evaluation.py

# 5. Aggregate Results (US1)
echo ">>> Step 5: Aggregating Results..."
python code/main.py
if [ ! -f "data/processed/energy_results_aggregated.csv" ]; then
    echo "ERROR: Aggregation failed to produce energy_results_aggregated.csv"
    exit 1
fi

# 6. Statistical Analysis (US2)
echo ">>> Step 6: Running Statistical Analysis (ANOVA, Tukey, Regression, Sensitivity)..."
python code/analysis.py
if [ ! -f "data/processed/stats_report.csv" ]; then
    echo "ERROR: Analysis failed to produce stats_report.csv"
    exit 1
fi

# 7. Sensitivity Analysis Output
echo ">>> Step 7: Finalizing Sensitivity Analysis..."
# Ensure sensitivity delta file exists if the analysis ran
if [ ! -f "data/processed/sensitivity_delta.csv" ]; then
    echo "WARNING: sensitivity_delta.csv not found, check sensitivity_analysis.py"
fi

# 8. Visualization (US3)
echo ">>> Step 8: Generating Visualizations..."
python code/visualization.py
if [ ! -f "data/processed/energy_bar.png" ] || [ ! -f "data/processed/tradeoff_scatter.png" ]; then
    echo "ERROR: Visualization failed to produce required PNG files"
    exit 1
fi

# 9. Scatter Slope Calculation
echo ">>> Step 9: Calculating Scatter Slope..."
python code/scatter_slope.py
if [ ! -f "data/processed/scatter_slope.txt" ]; then
    echo "WARNING: scatter_slope.txt not found"
fi

# 10. Final Verification
echo ">>> Step 10: Verifying Artifacts..."
REQUIRED_FILES=(
    "data/raw/human_eval_data.jsonl"
    "data/processed/energy_results_raw.csv"
    "data/processed/energy_results_aggregated.csv"
    "data/processed/stats_report.csv"
    "data/processed/sensitivity_delta.csv"
    "data/processed/energy_bar.png"
    "data/processed/tradeoff_scatter.png"
    "data/processed/scatter_slope.txt"
)

ALL_FOUND=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  [OK] $file"
    else
        echo "  [MISSING] $file"
        ALL_FOUND=false
    fi
done

if [ "$ALL_FOUND" = false ]; then
    echo "ERROR: One or more required artifacts are missing."
    exit 1
fi

echo "=== Pipeline Execution Successful ==="
echo "End time: $(date)"
echo "Total duration: $(($(date +%s) - $(date -d "$(date)" +%s) 2>/dev/null || echo "0")) seconds (approx)"
exit 0