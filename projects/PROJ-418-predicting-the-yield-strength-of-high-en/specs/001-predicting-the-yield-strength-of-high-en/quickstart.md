# Quickstart: Predicting HEA Yield Strength

This guide walks you through reproducing the full pipeline on a fresh GitHub Actions runner (or locally).

## Prerequisites
- Python 3.11
- Git
- Internet access (to download OpenML dataset & elemental property table)

## Setup

```bash
# Clone the repository
git clone https://github.com/yourorg/hea-yield-prediction.git
cd hea-yield-prediction

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r requirements.txt
```

## Run the End‑to‑End Pipeline

```bash
# Execute the main script (all steps are sequenced)
python scripts/run_pipeline.py \
  --seed 42 \
  --n_estimators 500 \
  --n_permutations 1000 \
  --output_dir output/
```

The script will:

1. **Download** and checksum‑verify the OpenML HEA yield‑strength dataset (ID 4539) and the elemental property table (HuggingFace URL).  
2. **Validate** raw inputs against `dataset.schema.yaml`, `elemental_properties.schema.yaml`, and `hea_composition.schema.yaml`; abort with a clear error if any required field is missing (FR‑009) or if duplicate rows are detected (deduplication).  
3. **Compute** deterministic descriptors (mixing entropy, atomic size mismatch, electronegativity variance, VEC, melting‑temperature variance) using the single elemental property table; output validated against `descriptor.schema.yaml`.  
4. **Split** the data (**[deferred] train / [deferred] test**, fixed seed) before any model training; perform k‑fold cross‑validation on the training portion; train a Random Forest and store the model artifact (`random_forest.joblib`).
5. **Evaluate** on the held‑out test set, writing `output/metrics/performance.json` (validated against `performance.schema.yaml`).  
6. **Compute** permutation importance with exactly 1 000 permutations per feature **on the held‑out test set**, deriving empirical mean/std, performing a two‑tailed t‑test (normality checked) and applying Bonferroni correction; results saved to `output/metrics/importance.json` (validated against `importance.schema.yaml`).  
7. **Generate** a markdown report (`output/report/report.md`) summarizing dataset statistics, model performance, VIF analysis, importance rankings (with traceability IDs), and the reproducibility manifest.  
8. **Create** `output/manifest/manifest.json` recording random seeds, hyper‑parameters, software versions, timestamps, SHA‑256 checksums of all key artifacts, and a `traceability` map linking each figure/table to its source row and code hash.  
9. **Record** total runtime in `output/runtime/runtime.json` (validated against `runtime.schema.yaml`).  
10. **Lint** (`ruff`) and **format** (`black`) the codebase; ensure ≤ 5 warnings and that the lint/formatting status is reflected in `runtime.json`.

## Verify Results

```bash
# Check that all success criteria are met
cat output/report/report.md | grep "R²"
cat output/report/report.md | grep "Pearson r"
cat output/report/report.md | grep "p‑value"
cat output/runtime/runtime.json
```

Expected (or better) values:

- R² ≥ 0.6  
- |r| ≥ 0.5  
- Importance p‑values (Bonferroni‑corrected) < 0.05 for flagged features  
- Runtime ≤ 7200 seconds  

## Linting & Formatting (Quality Checks)

```bash
# Lint (ruff) – must produce ≤ 5 warnings; capture output
ruff src/ tests/ > logs/ruff.log || true
# Check warning count
grep -c "warning" logs/ruff.log || true
# Formatting check (black) – must pass
black --check src/ tests/ > logs/black.log || true
```

Both commands will exit with status 0 if the warning count is ≤ 5 and formatting is correct. The logs are saved under `logs/` for audit.

## Re‑run for Stability Check

Run the pipeline three times with the same seed to confirm top‑5 feature ranking stability (SC‑006). The `report.md` will list the rankings; the rank‑difference across runs should be ≤ 1.

```bash
for i in {1..3}; do
  python scripts/run_pipeline.py --seed 42 --output_dir output/run_$i
done
# Compare rankings in output/run_*/report.md
```

The manifest’s `traceability` section records the IDs used for each ranking table, enabling automated comparison.

--- 
