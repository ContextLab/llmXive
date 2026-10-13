# Quickstart: Gut Microbiome – PD Progression Pipeline

## Prerequisites
* Python 3.11 (available on the CI runner)  
* Internet access only for `pip` package installation; **no automatic dataset download** – the user must provide an **open, verified dataset** as described in `research.md`.

## Setup
```bash
# 1. Create a fresh virtual environment (CI does this automatically)
python -m venv .venv
source .venv/bin/activate

# 2. Install pinned dependencies (includes parquet engine)
pip install -r requirements.txt
```

## Prepare Input Data
1. **Microbiome ASV table** – place a CSV file named `open_asv.csv` in `data/raw/`. It must contain at least the columns `sample_id`, `patient_id`, `visit_date`, plus one column per taxon with raw integer counts.  
2. **Clinical metadata** – place a Parquet file named `open_clinical.parquet` in `data/raw/`. Required columns are `patient_id`, `visit_date`, `age`, `sex`, `levodopa_eq_dose`, and `MDS_UPDRS_total` (the exclusive clinical outcome for this study).

The ingest step aborts with a clear error message if any required file or required column is missing. If the outcome column is absent, the pipeline aborts early (required for FR‑005).

## Validate Inputs (Phase 0)
```bash
python -m src.pipeline.ingest
```
*Checks*: file existence, parsability, required columns. A JSON validation record is written to `data/raw/ingest_validation.json`. Exit code 0 → continue; non‑zero → fix inputs.

## Run the Full Pipeline
```bash
python -m src.pipeline \
    --seed 42 \
    --max_taxa 100 \
    --perm_iterations 1000
```

### Flags
| Flag | Meaning |
|------|---------|
| `--seed` | Random seed for reproducibility (default 42). |
| `--max_taxa` | Upper bound on taxa to retain after filtering (default 100). |
| `--perm_iterations` | Number of permutation iterations (default 1000). |

All deliverables are written under `results/`:
- `taxa_correlations.csv` (covariate‑adjusted Spearman results)  
- `mixed_effects_summary.csv`  
- `permutation_pvalues.csv`  
- `PD_microbiome_progression_report.pdf`  

## Verify Outputs
```bash
# Run contract‑based tests
pytest -q src/tests

# Quick glance at a result file
head -n 5 results/taxa_correlations.csv
```

## Expected Runtime (benchmark on CI)
| Step | Approx. Wall‑time |
|------|-------------------|
| Data validation & loading | < 2 min |
| Filtering + CLR | < 5 min |
| Slope computation (≥ 2 visits) | < 3 min |
| Correlation + BH | < 2 min |
| Mixed‑effects fitting | < 12 min |
| Permutation (1 000 it., ≤ 100 taxa) | 3–4 h |
| PDF report generation | < 1 min |
| **Total** | **≤ 4 h** (well under the 6 h limit) |

**Important:** The pipeline **requires** the `MDS_UPDRS_total` column. If it is missing, the run stops with an informative error; the researcher must supply the correct clinical file before re‑running.

---

