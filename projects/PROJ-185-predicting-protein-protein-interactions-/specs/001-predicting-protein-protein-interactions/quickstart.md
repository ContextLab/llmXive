# Quickstart: Predict Plant PPIs from Co‑expression

## Prerequisites

1. **GitHub Actions runner** (or local Linux environment) with:
 - Python 3.11
 - R 4.2 and Bioconductor packages (`DESeq2`, `org.At.tair.db`, `biomaRt`, `GEOquery`, `sva`)
2. **Git** access to the repository.
3. Internet connectivity (to download GEO and STRING files).

## Setup

```bash
# Clone the repository
git clone
cd plant-ppi-pipeline

# Create a virtual environment and install Python dependencies
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt

# Install R dependencies via renv (executed once)
R -e "renv::restore()"
```

## Configuration

Edit `src/config/species.yaml` to list GEO series per species. Example (default includes Arabidopsis):

```yaml
Arabidopsis_thaliana:
 - GSEXXXXX # replace with actual accession numbers
 - GSEYYYYY
```

Adjust thresholds or seed in `src/config/parameters.yaml` if needed:

```yaml
correlation_threshold: 0.8 # must be >= 0.8
random_seed: 42
normalization: "TPM" # or "VST"
```

## Running the Full Pipeline

```bash
# Execute all steps (download → batch correction → normalize → filter → predict → evaluate → enrich)
make all
```

The Makefile targets:

| Target | Description |
|--------|-------------|
| `all` | Runs the complete pipeline for every species listed in `species.yaml`. |
| `evaluate` | Computes AUROC/AUPRC against STRING and writes `results/evaluation_metrics.json`. |
| `enrich` | Performs GO enrichment; outputs `results/go_enrichment_<species>.tsv`. |
| `validate` | Runs schema validation against `contracts/evaluation.schema.yaml` and `contracts/predicted_ppi.schema.yaml`. |
| `clean` | Removes all derived files (keeps raw downloads). |

All output files will appear in `results/`:

- `predicted_ppi_<species>.tsv` – edge list with Pearson r.
- `evaluation_metrics.json` – AUROC/AUPRC plus baseline.
- `go_enrichment_<species>.tsv` – GO terms with adjusted p‑values.
- `pipeline.log` – timestamped log of the run (ISO‑8601 format).

## Reproducibility Check

Rerun with the same seed to verify identical outputs:

```bash
make clean
make all SEED=42
```

The resulting `evaluation_metrics.json` and `go_enrichment_*.tsv` should be byte‑identical to the previous run.

## Troubleshooting

- **Insufficient samples**: If a GEO series has fewer than 20 samples, the pipeline aborts that series and logs `Insufficient sample count (<20)` in `pipeline.log`.
- **Mapping failures**: Unmapped genes generate `mapping_warnings_<species>.log`; the edge list simply omits those genes.
- **No edges meet threshold**: An empty `predicted_ppi_<species>.tsv` (header only) is written and evaluation for that species is skipped, with a warning in `pipeline.log`.
- **Validation errors**: If `make validate` reports schema violations, inspect the offending file and fix the formatting before re‑running.

---

