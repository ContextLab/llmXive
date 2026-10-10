#!/usr/bin/env bash
# Single-command entry point for the full analysis pipeline.
# Stages are added as their implementing tasks complete; each stage
# fails loudly (set -e) so a broken stage aborts the run.
set -euo pipefail

echo "=== [0/5] Environment check ==="
make env-check

echo "=== [1/5] Data ingestion & preprocessing ==="
python code/ingest/ingest.py

echo "=== [2/5] Feature-set construction ==="
if [ -f code/features/build_features.py ]; then
  python code/features/build_features.py
else
  echo "NOTE: feature construction not yet implemented (pending T004); skipping."
fi

echo "=== [3/5] Model training ==="
if [ -f scripts/run_full_training.sh ]; then
  bash scripts/run_full_training.sh
else
  echo "NOTE: full training not yet implemented (pending T005/T006); skipping."
fi

echo "=== [4/5] Statistical evaluation & mediation ==="
if [ -f code/eval/verify_improvement.py ]; then
  python code/eval/verify_improvement.py
else
  echo "NOTE: evaluation not yet implemented (pending T007-T009); skipping."
fi

echo "=== [5/5] Reporting ==="
if [ -f code/report/generate_report.py ]; then
  python code/report/generate_report.py
else
  echo "NOTE: report generation not yet implemented (pending T010); skipping."
fi

echo "Pipeline finished."
