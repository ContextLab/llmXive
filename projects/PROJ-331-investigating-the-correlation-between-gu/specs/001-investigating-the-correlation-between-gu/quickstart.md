# Quickstart: Gut Microbiome – PD Progression Pipeline

## Prerequisites
* Python 3.11 (available on the CI runner)  
* Internet access (only needed to fetch `pip` packages; **no automatic dataset download**).

## Setup
```bash
# 1. Create a fresh virtualenv (CI does this automatically)
python -m venv .venv
source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r requirements.txt
```

## Prepare Input Data
1. **Microbiome ASV table** – place a CSV file named `ppmi_asv.csv` in `data/raw/`. The file must contain at least the columns `sample_id`, `patient_id`, `visit_date`, plus one column per taxon with raw count values.  
2. **Clinical metadata** – place a Parquet file named `ppmi_clinical.parquet` in `data/raw/`. Required columns are `patient_id`, `visit_date`, `age`, `sex`, `levodopa_eq_dose`, and **either** `UPDRS_partIII` **or** `MDS_UPDRS_total`.  

The pipeline will abort with a clear error message if any required file or column is missing.

## Run the Full Pipeline
```bash
# Execute the end‑to‑end analysis (all phases 0‑6)
python -m src.pipeline.run_all \
    --seed 42 \
    --max_taxa 100 \
    --perm_iterations 1000 \
    --output_dir results/
```

### Flags
| Flag | Meaning |
|------|---------|
| `--seed` | Random seed for reproducibility |
| `--max_taxa` | Upper bound on taxa to retain (default 100) |
| `--perm_iterations` | Number of permutation iterations (default 1000) |
| `--output_dir` | Directory where CSVs and PDF will be written |

## Verify Outputs
```bash
# Contract tests (pytest)
pytest -q tests/contract

# Spot‑check a result file
head -n 5 results/taxa_correlations.csv
```

## Expected Runtime (benchmark on CI)
| Step | Approx. Wall‑time |
|------|-------------------|
| Data validation & loading | < 2 min |
| Filtering + CLR | < 5 min |
| Slope computation (≥3 visits) | < 3 min |
| Correlation + BH | < 2 min |
| Mixed‑effects fitting (raw data) | < 12 min |
| Permutation (1 000 iterations, ≤ 100 taxa) | 3–4 h |
| PDF report generation | < 1 min |
| **Total** | **≤ 4 h** (well under the 6 h limit) |

**Important:** The pipeline requires a longitudinal motor‑score column (`UPDRS_partIII` **or** `MDS_UPDRS_total`) in the clinical metadata. If neither column is present, the pipeline aborts with an informative error and the researcher must supply an appropriate open dataset before re‑running.

---

