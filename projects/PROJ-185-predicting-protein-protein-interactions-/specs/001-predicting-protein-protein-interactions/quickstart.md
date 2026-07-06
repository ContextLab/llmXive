# Quickstart: Predict Protein‑Protein Interactions from Co‑expression Networks

## Prerequisites
- Python 3.11 (installed via `python -m venv venv && source venv/bin/activate`)
- R 4.2 with Bioconductor (installed automatically by the `install_r_deps.sh` script)
- Internet access (to download GEO and STRING data)
- GitHub Actions runner (or local Linux environment with ≥ 2 CPU, 7 GB RAM)

## Setup

```bash
# 1. Clone the repository (already done in CI)
git clone
cd ppi-coexpression

# 2. Create a Python virtual environment and install dependencies
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt

# 3. Install R dependencies (run once)
bash scripts/install_r_deps.sh
```

## Configuration
Edit `config/species_gse.yaml` to list GEO series per species, e.g.:

```yaml
Arabidopsis thaliana:
 - GSE12345
 - GSE67890
# add more species as needed
```

Optional flags (default values shown):

| Flag | Description | Default |
|------|-------------|---------|
| `--norm {vst, tpm}` | Normalization method | `vst` |
| `--threshold FLOAT` | Correlation threshold (must be ≥ 0.75) | `0.80` |
| `--seed INT` | Global random seed for reproducibility | `42` |
| `--max-genes INT` | Upper bound on retained genes after variance filtering | `5000` |

## Running the Pipeline

### Full end‑to‑end execution
```bash
make all SEED=12345 NORM=vst THRESHOLD=0.80
```
- Downloads data, builds the network, evaluates against STRING, runs GO enrichment, and writes per‑species summaries plus `final_report.txt`.

### Individual targets (useful for debugging)

| Target | What it does |
|--------|--------------|
| `make download` | Download GEO series only. |
| `make normalize` | Normalize and filter genes. |
| `make corr` | Compute raw correlations (`raw_correlations_*.tsv.gz`). |
| `make map` | Map genes to STRING IDs. |
| `make edges` | Apply threshold & write predicted edges. |
| `make evaluate` | Perform evaluation against STRING and write `evaluation_metrics.json`. |
| `make enrich` | Run GO enrichment (`go_enrichment_*.tsv`). |
| `make summary` | Generate per‑species and final reports. |
| `make clean` | Remove all intermediate files. |

## Verifying Results
After each target, the verification script runs automatically and will abort if any schema validation fails. To manually validate:

```bash
python scripts/validate.py results/predicted_ppi_Arabidopsis.tsv contracts/predicted_edges.schema.yaml
python scripts/validate.py results/evaluation_metrics.json contracts/evaluation.schema.yaml
python scripts/validate.py results/threshold_sensitivity_Arabidopsis.tsv contracts/threshold_sensitivity.schema.yaml
```

All logs are in `logs/pipeline.log`. Re‑run the pipeline with the same seed to obtain identical outputs (SC‑004).

## Expected Outputs (per species)

- `results/predicted_ppi_<species>.tsv` – predicted edges (≥ 10 000 rows for typical species).
- `results/evaluation_metrics.json` – AUROC, AUPRC, baseline metrics, `baseline_p`.
- `results/go_enrichment_<species>.tsv` – GO terms with adjusted p‑values (or “No significant enrichment”).
- `results/summary_<species>.txt` – concise report with construct‑validity justification.
- `results/final_report.txt` – aggregated report across all species.

Enjoy reproducible PPI prediction!

---
