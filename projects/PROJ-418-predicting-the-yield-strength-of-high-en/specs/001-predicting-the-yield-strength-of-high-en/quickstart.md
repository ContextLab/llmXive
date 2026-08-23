# Quickstart: Predicting HEA Yield Strength

This guide walks you through running the full pipeline on a fresh GitHub Actions runner (or locally).

## Prerequisites
- Python 3.11+
- `git` and internet access
- Multi‑core CPU (minimum) and approximately several GB of RAM

## Step‑by‑Step

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourorg/hea-yield-predictor.git
   cd hea-yield-predictor
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the pipeline (default settings)**
   ```bash
   python -m code.cli run \
       --dataset-url https://zenodo.org/record/02000374/files/hea_yield_strength.csv \
       --external-validation-url https://openmaterialsdb.org/collections/hea_mech.csv \
       --output-dir output/
   ```

   The CLI will:
   - download and checksum the raw CSV,
   - validate against `contracts/dataset.schema.yaml`,
   - deduplicate rows (logging count removed),
   - abort if any required field is missing (FR‑009) or if an element is unknown (FR‑015),
   - compute deterministic descriptors,
   - train a Random Forest with 5‑fold CV,
   - evaluate on a held‑out test set,
   - compute permutation importance with **exactly 1000** permutations per feature,
   - run bootstrap CI and VIF analysis,
   - write `manifest.json` (validated programmatically for completeness),
   - generate a `README.md` with usage instructions and inline code comments,
   - produce linting (`ruff`) and formatting (`black --check`) reports,
   - write `pipeline_runtime.json` and verify total runtime ≤ 7200 s (SC‑004).

4. **Inspect results**
   ```bash
   less output/report.md          # human‑readable summary
   cat output/metrics.json        # JSON with R², r, p‑values, CIs, runtime
   cat output/pipeline_runtime.json
   ```

5. **Run reproducibility check (optional)**
   ```bash
   pytest -vv tests/contract/
   ```

   The test suite validates **all** contract files listed in `contracts/` against the generated artifacts (including `dataset.schema.yaml`, `descriptor.schema.yaml`, `importance.schema.yaml`, `metrics.schema.yaml`, `runtime.schema.yaml`, etc.).

## Expected Output Files
| File | Description |
|------|-------------|
| `output/model.pkl` | Serialized Random Forest model. |
| `output/report.md` | Full markdown report (dataset stats, VIF summary, model performance, importance with corrected p‑values, bootstrap CIs, stability analysis, disclaimer). |
| `output/manifest.json` | Reproducibility manifest (FR‑007). |
| `output/metrics.json` | R², Pearson r, p‑values, bootstrap CIs, runtime. |
| `output/pipeline_runtime.json` | `{ "status": "pass", "total_seconds": <value> }` (SC‑004). |
| `output/stability_rankings.json` | Top‑ranked feature rankings from three independent runs; rank‑difference ≤ 1 (SC‑006). |
| `output/importance.json` | Permutation importance scores with raw and Bonferroni‑corrected p‑values (SC‑003). |
| `output/lint_report.txt` | Ruff warnings count (≤ 5) and black formatting status (SC‑008). |
| `output/contract_validation.log` | Results of JSON‑schema validation for all artifacts. |
| `README.md` | Usage instructions, dependency list, and code‑comment guidelines (FR‑011). |

## Re‑running with a Different Seed
```bash
python -m code.cli run \
    --seed 12345 \
    --output-dir output/run_12345
```
Changing the seed will produce a new `manifest.json` but the top‑N rankings should differ by at most one position (SC‑006).

