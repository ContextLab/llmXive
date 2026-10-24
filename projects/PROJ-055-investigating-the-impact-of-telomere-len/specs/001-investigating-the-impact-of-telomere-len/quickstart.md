# Quickstart: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Prerequisites
- Python 3.11+ and R 4.3+ (both available on the GitHub Actions runner).  
- Internet access (Dryad API, AnAge export, BirdLife API, Open Tree of Life).  
- No GPU required.

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-055-investigating-the-impact-of-telomere-len
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r code/requirements.txt
Rscript code/R/install_packages.R   # installs nlme, ape, lme4, lmerTest, performance, ggplot2, patchwork
```

## Configuration
`code/config.yaml` is committed with static settings only. The `dataset_ids` list is **empty** initially and will be populated automatically by the discovery step; no placeholder comment is present.

```yaml
dryad_api_base: "https://datadryad.org/api/v2"
anage_export_url: " Name or service not known)"))]"
birdlife_api_url: ""
seed: 42
alpha: 0.05
dataset_ids: []   # populated at runtime by 01_discover_data.py
```

## Running the Full Pipeline

```bash
python code/01_discover_data.py   # discovers Dryad DOIs; aborts on Data Availability Error
python code/02_ingest_data.py
python code/03_clean_merge.py
python code/04_fit_pgls_base.py
python code/05_fit_pgls_interaction.py
python code/06_sensitivity_power.py   # LOOCV/jackknife + power simulation
python code/07_visualize.py
```

## Verification Steps

```bash
# Verify checksums of raw inputs
python code/utils.py --verify-checksums

# Validate processed dataset against JSON schema
python - <<'PY'
import yaml, jsonschema, pandas as pd
schema = yaml.safe_load(open('contracts/dataset.schema.yaml'))
df = pd.read_csv('data/processed/merged_analysis.csv')
jsonschema.validate(df.to_dict(orient='records'), schema)
print("Dataset schema validation passed.")
PY
```

Re‑running the pipeline on unchanged inputs must reproduce identical SHA‑2 hashes. (Constitution I). All values in `results/` are real measurements; a low‑species‑count run will produce the `"Low Power: Phylogenetic inference unreliable"` message with null statistics—no fabricated numbers.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Data Availability Error` | No usable Dryad datasets discovered, or AnAge/BirdLife export unreachable | Inspect `logs/discovery_log.json`; consider adding a new open dataset that meets the required variables, or request a scope revision. |
| `MemoryError` during cleaning | Extremely large raw CSVs | The cleaning script streams with `chunksize=100_000`; increase chunk size or run on a machine with more RAM. |
| R package not found | Fresh runner | Re‑run `Rscript code/R/install_packages.R`. |
| Low‑power message in `model_summary.csv` | `n_species < 15` | Expected per FR‑004; collect additional species data if feasible. |
| Interaction model not produced | Species count < 30 (interaction eligibility) or low‑power flag | Interaction model is optional under those conditions; the base model and power report remain valid. |
| Missing `body_mass_g` in model output | Dataset missing body‑mass column for some species | Those species are excluded from the analysis and logged in `missing_data_log.csv`. |

---

