# Quickstart: Predict Protein‑Protein Interactions from Co‑expression Networks

## Prerequisites
- **Operating System**: Linux (Ubuntu 22.04 recommended) on a GitHub Actions runner or local machine with Docker.
- **Python**: ≥ 3.11 (managed via `requirements.txt`).
- **R**: ≥ 4.2 with `renv` lockfile (automatically restored).
- **Git**: to clone the repository.

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourorg/ppi-coexpression.git
cd ppi-coexpression

# 2. Create a Python virtual environment and install deps
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Initialise the R environment (install packages from renv.lock)
Rscript -e 'renv::restore()'
```

## Configuration
Edit `config/species.yaml` to list GEO series per species (default contains *Arabidopsis thaliana* `GSEXXXXX`).  
Edit `config/parameters.yaml` to change optional parameters:

```yaml
norm_method: "tpm"          # or "vst"
correlation_threshold: 0.8   # cannot be < 0.8
seed: 42
corr_method: "pearson"      # "spearman" or "biweight"
batch_correct: false        # set true to apply limma batch correction
```

## Run the Full Pipeline

```bash
# Execute all steps (download → enrichment) on the default species
make all
```

This will produce, for each species:

- `results/predicted_ppi_<species>.tsv` – predicted edges with STRING protein IDs.
- `evaluation_metrics.json` **(AUROC > 0.70, AUPRC ≥ 0.65, baseline p‑value < 0.05)**.
- `go_enrichment_<species>.tsv` – GO terms with adjusted p‑values.
- `pipeline.log` – full execution log with timestamps.

## Validation & Reproducibility Checks

```bash
# Verify that outputs meet success criteria
make validate
```

`make validate` re‑runs the pipeline with the same `--seed` and checks that hashes of `evaluation_metrics.json` and `go_enrichment_<species>.tsv` match the reference hashes stored in `data/checksums.yaml`.  

## Performance Benchmark

```bash
make benchmark
```
The benchmark target prints **total wall‑clock time**; CI will fail if it exceeds **6 hours**.  

## Common Issues

| Symptom | Resolution |
|---------|------------|
| `Insufficient sample count (<20)` | Check `config/species.yaml` accession list; replace with a series that has ≥ 20 samples. |
| `STRING reference not found or unreadable` | Verify internet connectivity; the STRING parquet file is downloaded automatically by `datasets.load_dataset`. |
| No edges meeting threshold | Lower the `correlation_threshold` (must stay ≥ 0.8) or verify that the RNA‑seq data have sufficient variability. |
| High memory usage | The pipeline automatically pre‑selects a sizable set of the most variable genes to keep the correlation matrix manageable. |
| Unexpected correlations | Try alternative `--corr-method` options (`spearman`, `biweight`). |
| Missing output files | Run `make validate` which will invoke `test_outputs.py` to pinpoint missing artifacts. |

For further details, see the full documentation in `docs/` or run `make help` for a list of Makefile targets.

--- 
