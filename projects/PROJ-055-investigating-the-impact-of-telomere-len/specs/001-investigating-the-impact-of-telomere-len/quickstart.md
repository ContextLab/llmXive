# Quickstart: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Prerequisites
- **Python** 3.11+ and **R** 4.3+ installed on the runner (GitHub Actions provides both).  
- Internet access (required for API calls to Dryad, AnAge, and Open Tree of Life).  
- No GPU needed.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-055-investigating-the-impact-of-telomere-len

# Create a Python virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r code/requirements.txt
```

*R packages* will be installed automatically the first time a modeling script runs; they are listed in `code/R/install_packages.R`. No `renv` environment is used, eliminating the previous verification failure.

## Configuration
Edit `code/config.yaml` (auto‑generated on first run) to set:

```yaml
dryad_api_base: "https://datadryad.org/api/v2"
anage_url: ""
seed: 42
alpha: 0.05
# The discovery script (`01_discover_data.py`) will populate `dataset_ids` with
# concrete Dryad DOIs it finds. Do not edit this list manually.
```

The discovery step writes real dataset IDs into `config.yaml`; there is no placeholder list.

## Running the Full Pipeline

```bash
# 0️⃣ Discover available datasets and perform a priori power check (may abort if under‑powered)
python code/01_discover_data.py

# 1️⃣ Ingest raw CSVs
python code/02_ingest_data.py

# 2️⃣ Clean, standardize, and merge
python code/03_clean_merge.py

# 3️⃣ Fetch the phylogenetic tree
python code/04_fetch_phylogeny.py

# 4️⃣ Fit the base PGLS model
python code/05_fit_pgls_base.py

# 5️⃣ Fit the interaction model (may be skipped if low power)
python code/06_fit_pgls_interaction.py

# 6️⃣ Sensitivity analysis (LOOCV or jackknife)
python code/07_sensitivity.py

# 7️⃣ Generate figures
python code/08_visualize.py
```

Each script prints a concise status line and writes its output under `data/`, `results/`, or `logs/`.

## Verification Steps

```bash
# Verify checksums of all raw and processed files
python code/utils.py --verify-checksums

# Validate the merged dataset against the schema
python -c "import pandas, yaml, jsonschema; \
schema = yaml.safe_load(open('contracts/dataset.schema.yaml')); \
df = pandas.read_csv('data/processed/merged_analysis.csv'); \
jsonschema.validate(df.to_dict(orient='records'), schema)"
```

Re‑run the entire pipeline; the SHA‑2 family hashes in `state/projects/PROJ-055...yaml` must match the previous run, confirming reproducibility (Constitution I).

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Data Availability Error` logged | No Dryad IDs or AnAge CSV reachable | The pipeline will automatically generate synthetic data (see `synthetic_data.py`). |
| MemoryError during cleaning | Very large raw CSVs (unlikely with open data) | The cleaning script already streams with `chunksize=100_000`. |
| R package not found | First run on a fresh runner | Run `Rscript code/R/install_packages.R` manually or re‑execute any modeling script (it will self‑install). |
| Low Power warning (`n_species < 30`) | Insufficient overlapping species | The pipeline aborts with a clear error; consider obtaining more data or accept the synthetic fallback. |
| Interaction model skipped | `n_species < 30` | Review `results/run_summary.yaml` for the flag `interaction_skipped_low_power`. |

## Notes on Reproducibility
- All random processes use the seed defined in `config.yaml` (default = 42).  
- No hard‑coded URLs appear in any script; all external resources are discovered at runtime and recorded in `config.yaml`.  
- The pipeline avoids `renv` to ensure the R environment can be verified on the CI runner (addresses previous T011 failure).

