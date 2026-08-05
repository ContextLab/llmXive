#!/bin/bash
set -e

echo "=== llmXive Full Suite End-to-End Regression Test ==="
echo "Starting at: $(date)"

# 1. Clean state
echo "[1/6] Cleaning data/processed/..."
if [ -d "data/processed" ]; then
    rm -rf data/processed/*
    echo "  Cleared."
else
    mkdir -p data/processed
fi

# Ensure logs directory exists
mkdir -p logs

# 2. Run Full Sweep (T033b)
echo "[2/6] Running full N-sweep (T033b)..."
python src/main.py --run-full-sweep
if [ ! -f "data/processed/full_sweep_results.json" ]; then
    echo "ERROR: full_sweep_results.json not generated."
    exit 1
fi
echo "  Generated: data/processed/full_sweep_results.json"

# 3. Run Heavy-Tailed Validation (T034d/T065)
echo "[3/6] Running heavy-tailed validation (T034d)..."
python scripts/run_heavy_tailed_validation.py
if [ ! -f "data/processed/heavy_tailed_results.json" ]; then
    echo "ERROR: heavy_tailed_results.json not generated."
    exit 1
fi
echo "  Generated: data/processed/heavy_tailed_results.json"

# 4. Run Final Derivation Audit (T066)
echo "[4/6] Running final derivation audit (T066)..."
python scripts/run_final_derivation_audit.py
if [ ! -f "docs/peer_review_checklist.md" ]; then
    echo "ERROR: peer_review_checklist.md not updated."
    exit 1
fi
echo "  Updated: docs/peer_review_checklist.md"

# 5. Run Sample Size Enforcement Check (T064)
echo "[5/6] Verifying sample size enforcement (T064)..."
python scripts/verify_sample_size_enforcement.py
echo "  Verification passed."

# 6. Generate Final Statistical Report (T044)
echo "[6/6] Generating final statistical report (T044)..."
python src/analysis/stats.py --generate-report
if [ ! -f "data/processed/statistical_report.json" ]; then
    echo "ERROR: statistical_report.json not generated."
    exit 1
fi
echo "  Generated: data/processed/statistical_report.json"

echo "=== Suite Completed Successfully ==="
echo "Finished at: $(date)"
echo "All expected artifacts present."
exit 0
