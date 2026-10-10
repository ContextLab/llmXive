#!/usr/bin/env bash
# run_pipeline.sh – orchestrates the end‑to‑end analysis for the project.
# Each stage aborts the pipeline on error (set -e).  Stages that are not yet
# implemented will simply be skipped with a clear message.

set -euo pipefail

echo "=== Step 1: Environment verification ==="
bash scripts/env_check.sh

echo "=== Step 2: Data ingestion ==="
# The ingestion module writes the unified CSV to data/processed/unified_fatigue.csv
python -m code.ingest.ingest

echo "=== Step 3: Preprocessing (placeholder) ==="
# Future preprocessing script – currently a no‑op placeholder to keep the pipeline functional.
if [ -f "code/preprocess/preprocess.py" ]; then
  python -m code.preprocess.preprocess
else
  echo "Preprocessing script not present – skipping."
fi

echo "=== Step 4: Feature‑set construction (placeholder) ==="
if [ -f "code/features/build_features.py" ]; then
  python -m code.features.build_features
else
  echo "Feature‑set builder not present – skipping."
fi

echo "=== Step 5: Model training (placeholder) ==="
if [ -f "code/models/train.py" ]; then
  python -m code.models.train --feature-set A
  python -m code.models.train --feature-set B
  python -m code.models.train --feature-set C
else
  echo "Model training script not present – skipping."
fi

echo "=== Step 6: Evaluation (placeholder) ==="
if [ -f "code/eval/verify_improvement.py" ]; then
  python -m code.eval.verify_improvement
else
  echo "Evaluation script not present – skipping."
fi

echo "=== Step 7: Mediation analysis (placeholder) ==="
if [ -f "code/mediation/boot_mediation.py" ]; then
  python -m code.mediation.boot_mediation --resamples 10000
else
  echo "Mediation script not present – skipping."
fi

echo "=== Step 8: Report generation (placeholder) ==="
if [ -f "code/report/generate_report.py" ]; then
  python -m code.report.generate_report
else
  echo "Report generation script not present – skipping."
fi

echo "=== Pipeline completed successfully ==="
exit 0