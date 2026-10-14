# Quickstart: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Prerequisites
- Python 3.11+ and R 4.3+ (available on the GitHub Actions runner).
- Internet access (Dryad API, AnAge export, BirdLife API, Open Tree of Life).
- No GPU needed.

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-055-investigating-the-impact-of-telomere-len
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r code/requirements.txt
Rscript code/R/install_packages.R   # installs phylolm, ape, rotl, pwr; no renv
```

## Configuration
`code/config.yaml` is committed with only static settings; **the `dataset_ids` list is intentionally empty and will be populated automatically by `01_discover_data.py` at runtime**—no manual editing or placeholder comment is required.

```yaml
dryad_api_base: "https://datadryad.org/api/v2"
anage_export_name: "anage_data"
birdlife_api_url: "https://birdlife.org/api/v1/ecology"
seed: 42
alpha: 0.05
dataset_ids: []   # will be filled with real DOIs by the discovery step
```

## Running the Full Pipeline

```bash
python code/01_discover_data.py   # discovers Dryad DOIs; halts on Data Availability Error
python code/02_ingest_data.py
python code/03_clean_merge.py
python code/04_fetch_phylogeny.py
python code/05_fit_pgls_base.py
python code/06_fit_pgls_interaction.py
python code/07_sensitivity.py     # LOOCV or jackknife + power report
python code/08_visualize.py
```

## Verification Steps

```bash
python code/utils.py --verify-checksums

python -c "import pandas, yaml, jsonschema; \
schema = yaml.safe_load(open('contracts/dataset.schema.yaml')); \
df = pandas.read_csv('data/processed/merged_analysis.csv'); \
jsonschema.validate(df.to_dict(orient='records'), schema)"
```

Re‑running the pipeline on unchanged inputs must reproduce identical SHA‑256 hashes (Constitution I). All values in `results/` are real measurements; a low‑species‑count run produces the `"Low Power: Phylogenetic inference unreliable"` message with null statistics — never placeholder numbers.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Data Availability Error` | No usable Dryad datasets discovered, or AnAge/BirdLife export unreachable | Inspect `logs/discovery_log.json`; the pipeline halts by design — no synthetic fallback. Raise a scope revision if the source is permanently unavailable. |
| `MemoryError` during cleaning | Very large raw CSVs | The cleaning script streams with `chunksize=100_000`. |
| R package not found | Fresh runner | Re‑run `Rscript code/R/install_packages.R`. |
| Low‑power message in `model_summary.csv` | n_species < 15 | Expected behavior per FR‑004; statistics are null by design. |
| Interaction model not in output | Base model did not run (data or low‑power halt) | Check `results/run_summary.yaml`. |
| Interaction model skipped (n < 30) | Interaction model requires ≥ 30 species for reliable λ estimation | Collect more data or note limitation. |
