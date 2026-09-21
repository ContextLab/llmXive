#!/bin/bash
set -e

echo "=== PROJ-342 CI Pipeline: Final Verification ==="

# 1. Setup Environment
echo "[1/6] Setting up environment..."
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi
export PYTHONPATH="${PYTHONPATH}:$(pwd)/code"

# 2. Data Ingestion (US1)
echo "[2/6] Running data ingestion..."
python code/ingest.py

# Verify T012/T014 outputs
if [ ! -f "data/processed/cleaned_mg.csv" ]; then
    echo "ERROR: data/processed/cleaned_mg.csv not found."
    exit 1
fi
if [ ! -f "data/ingestion_stats.json" ]; then
    echo "ERROR: data/ingestion_stats.json not found."
    exit 1
fi

# 3. Feature Engineering (US2)
echo "[3/6] Computing descriptors..."
python code/descriptors.py

# Verify T026 output
if [ ! -f "data/processed/descriptors.csv" ]; then
    echo "ERROR: data/processed/descriptors.csv not found."
    exit 1
fi

# 4. Model Training (US2)
echo "[4/6] Training model with LOFO CV..."
python code/train.py

# Verify T024a/b outputs
if [ ! -f "artifacts/models/best_model.pkl" ]; then
    echo "ERROR: artifacts/models/best_model.pkl not found."
    exit 1
fi
if [ ! -f "artifacts/metrics/metrics.json" ]; then
    echo "ERROR: artifacts/metrics/metrics.json not found."
    exit 1
fi

# 5. Analysis & Diagnostics (US2/US3)
echo "[5/6] Running analysis (VIF, Correlation, Sensitivity, Collinearity)..."
python code/analyze.py

# Verify T035b, T037b, T060a, T034 outputs
if [ ! -f "data/processed/vif_diagnostic_log.json" ]; then
    echo "ERROR: data/processed/vif_diagnostic_log.json not found."
    exit 1
fi
if [ ! -f "artifacts/metrics/sensitivity_analysis.json" ]; then
    echo "ERROR: artifacts/metrics/sensitivity_analysis.json not found."
    exit 1
fi
if [ ! -f "data/processed/collinearity_log.json" ]; then
    echo "ERROR: data/processed/collinearity_log.json not found."
    exit 1
fi
if [ ! -f "data/processed/fdr_corrected_pvalues.json" ]; then
    echo "ERROR: data/processed/fdr_corrected_pvalues.json not found."
    exit 1
fi

# 6. Reporting (US3)
echo "[6/6] Generating final report..."
python code/report.py

# Verify T050, T039a-c outputs
if [ ! -f "artifacts/reports/final_report.md" ]; then
    echo "ERROR: artifacts/reports/final_report.md not found."
    exit 1
fi
if [ ! -f "artifacts/reports/pdp_radius_mismatch.png" ]; then
    echo "ERROR: artifacts/reports/pdp_radius_mismatch.png not found."
    exit 1
fi
if [ ! -f "artifacts/reports/correlation_heatmap.png" ]; then
    echo "ERROR: artifacts/reports/correlation_heatmap.png not found."
    exit 1
fi

# Final Verification: Check Report Content
echo "=== Final Verification Checks ==="

# Check for mandatory phrase
if grep -q "These findings are associational only" artifacts/reports/final_report.md; then
    echo "PASS: Mandatory phrase 'These findings are associational only' found."
else
    echo "FAIL: Mandatory phrase 'These findings are associational only' NOT found."
    exit 1
fi

# Check for causal language (basic heuristic)
if grep -qi "causes\|determines\|proves\|guarantees" artifacts/reports/final_report.md; then
    echo "WARNING: Potential causal language detected. Review required."
else
    echo "PASS: No obvious causal language detected."
fi

echo "=== CI Pipeline Completed Successfully ==="
exit 0
