# Quickstart: Predicting HEA Yield Strength

This guide shows how to run the full pipeline on a fresh GitHub Actions runner (or locally) and generate the final `report.md`.

## Prerequisites
- Python 3.11 (available on the CI runner).
- Internet access to download the open HEA dataset (URL must be supplied in `config.yaml`).

## Step‑by‑Step

1. **Clone the repository**
 ```bash
 git clone
 cd hea-yield-predictor
 ```

2. **Create a virtual environment and install dependencies**
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 pip install -r requirements.txt
 ```

3. **Configure dataset URLs**
 Edit `config.yaml`:
 ```yaml
 primary_dataset_url: ""
 external_dataset_url: ""
 ```

4. **Run the pipeline**
 ```bash
 python -m code.run_pipeline \
 --config config.yaml \
 --seed 42 \
 --output_dir output/
 ```

 The script will:
 - Download and validate the datasets.
 - Compute descriptors.
 - Perform power analysis, VIF screening, model training, CV, test evaluation, external validation, permutation importance, and stability assessment.
 - Write all artifacts (`model.pkl`, `metrics.json`, `importance.json`, `stability_rankings.json`, `manifest.json`).
 - Produce `report.md` in the project root.

5. **Inspect the report**
 ```bash
 less report.md
 ```
 The report contains:
 - Dataset statistics.
 - Power‑analysis justification.
 - VIF table.
 - CV performance with bootstrap CI.
 - Test & external validation metrics (R², r, p).
 - Permutation‑importance table with Holm‑Bonferroni‑adjusted p‑values.
 - Stability ranking summary.
 - Provenance manifest linking every number to a source.

6. **Run the CI tests (optional)**
 ```bash
 pytest -q
 ruff check.
 black --check.
 ```

 Results are stored in `output/pipeline_runtime.json`.

## Expected Runtime
On the free GitHub Actions runner (a modest CPU allocation and typical memory for the free tier) the full pipeline completes in **[deferred]**, well under the 6‑hour limit.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Dataset download failed` | URL missing or inaccessible | Verify `config.yaml` URLs; ensure they point to a publicly downloadable file. |
| `Schema validation error` | Input CSV missing required columns | Check column names (`element`, `fraction`, `yield_strength`). |
| `Power analysis abort` | Insufficient N for target power | Collect more data or relax target R² (requires spec change). |
| `VIF > 5 for many descriptors` | Highly collinear descriptor set | Review descriptor definitions; consider dropping redundant ones. |

---
