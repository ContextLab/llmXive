# Quickstart: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Prerequisites
- Python 3.11+ and R 4.3+ (both pre‑installed on the GitHub Actions runner).  
- Internet access (to fetch data from Dryad, AnAge, and BirdLife).  
- No GPU required.

## Installation

```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-055-investigating-the-impact-of-telomere-len

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r code/requirements.txt

# Install R packages (run once)
Rscript code/R/install_packages.R
```

## Configuration
`code/config.yaml` is shipped with **static, verified URLs** for the Dryad telomere datasets and the lifespan CSVs. No manual editing is required; the discovery step has been removed.

```yaml
seed: 42
alpha: 0.05
dataset_urls:
  - "https://datadryad.org/stash/downloads/file1.csv"
  - "https://datadryad.org/stash/downloads/file2.csv"
lifespan_urls:
  - "https://example.org/lifespan_study1.csv"
  - "https://example.org/lifespan_study2.csv"
```

## Running the Full Pipeline

```bash
# Step 1 – download the raw CSVs (telomere and lifespan)
python code/02_ingest_data.py

# Step 2 – clean, standardise, and merge into analysis‑ready CSV
python code/03_clean_merge.py

# Step 3 – fetch ecological covariates from AnAge and BirdLife
python code/04_fetch_ecology.py

# Step 4 – verify required R packages are installed (Python‑driven verifier)
python code/04_verify_r_packages.py

# Step 5 – fit the base Linear Mixed‑Effects Model (includes body mass & latitude)
python code/05_fit_lmm_base.py

# Step 6 – fit the interaction model (migration & latitude interactions)
python code/06_fit_lmm_interaction.py

# Step 7 – sensitivity analysis & conditional power simulation
python code/07_sensitivity_power.py

# Step 8 – external significance validation (permutation test)
python code/08_permutation_test.py

# Step 9 – generate figures
python code/09_visualise.py

# Step 10 – validate all outputs against schemas and produce a summary report
python code/10_validate_report.py
```

## Verification Steps

```bash
# Verify checksums of raw inputs
python code/utils.py --verify-checksums

# Validate the processed dataset against its JSON schema
python - <<'PY'
import yaml, jsonschema, pandas as pd
schema = yaml.safe_load(open('contracts/dataset.schema.yaml'))
df = pd.read_csv('data/processed/analysis_ready.csv')
jsonschema.validate(df.to_dict(orient='records'), schema)
print("Dataset schema validation passed.")
PY

# Validate model outputs
python - <<'PY'
import yaml, jsonschema, pandas as pd
schema = yaml.safe_load(open('contracts/model_output.schema.yaml'))
for path in ['results/model_base.csv', 'results/model_interaction.csv']:
    df = pd.read_csv(path)
    jsonschema.validate(df.to_dict(orient='records'), schema)
    print(f"{path} validation passed.")
PY

# Check external permutation validation
python - <<'PY'
import yaml, json
perm = yaml.safe_load(open('results/permutation_pvalue.yaml'))
assert 'empirical_pvalue' in perm, "Permutation result missing"
print(f"Permutation empirical p‑value: {perm['empirical_pvalue']}")
PY
```

Re‑running the pipeline on unchanged inputs must reproduce identical SHA hash values for all files. (Constitution I). All generated artifacts (`results/*.csv`, `results/*.png`, `results/report.yaml`, `results/permutation_pvalue.yaml`) are real measurements; if the species count is below 15, the low‑power flag will appear, but **no power simulation** will be performed, preventing misleading inference.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Data Unavailable` error | No Dryad or lifespan URLs could be resolved | Verify the static URLs in `config.yaml` and ensure internet connectivity. |
| `Missing required column` | The downloaded CSV schema changed (column renamed) | Update the renaming map in `03_clean_merge.py` and re‑run. |
| `Model did not converge` | Extremely low variance or singular random‑effects structure | The script automatically switches to the `bobyqa` optimizer; if still failing, a low‑power flag will be written and power analysis skipped. |
| `Low‑power warning in model CSV` | Fewer than 15 distinct `species_id` values | Expected per FR‑004; consider obtaining additional species data or accept the limitation. |
| `R package verification failed` | Required R packages missing | Run `python code/04_verify_r_packages.py` which will install missing packages automatically. |
| `Permutation p‑value file missing` | Phase 8 was skipped due to earlier failure | Review logs from `08_permutation_test.py`; ensure `analysis_ready.csv` exists and contains rows. |
| `Power analysis not performed` | Species count below 15 | This is intentional; collect more species or acknowledge limited inferential power. |

---



