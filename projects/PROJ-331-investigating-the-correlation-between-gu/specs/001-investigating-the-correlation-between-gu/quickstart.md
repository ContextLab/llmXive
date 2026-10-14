# Quickstart: Gut Microbiome – PD Progression Pipeline

## Prerequisites
* Python 3.11 (available on the CI runner)  
* Internet access **only** for installing packages; the pipeline **does not** download any dataset automatically. You must provide an open, verified ASV table and matching clinical metadata as described in `research.md`.

## Setup
```bash
# 1. Create a fresh virtual environment (CI does this automatically)
python -m venv .venv
source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r requirements.txt
```

## Prepare Input Data
1. **Microbiome ASV table** – place a CSV named `open_asv.csv` (or `ppmi_asv.csv`) in `data/raw/`. It must contain at least the columns `sample_id`, `patient_id`, `visit_date`, plus one column per taxon with raw integer counts.  
2. **Clinical metadata** – place a Parquet file named `open_clinical.parquet` (or `ppmi_clinical.parquet`) in `data/raw/`. Required columns are `patient_id`, `visit_date`, `age`, `sex`, `levodopa_eq_dose`, and `MDS_UPDRS_total`.  

If either file or any required column is missing, the ingest step aborts with a clear error message.

## Validate Inputs (Phase 0)
```bash
python -m src.pipeline.ingest
```
*Checks*: existence, parsability, required columns. A JSON validation record is written to `data/raw/ingest_validation.json`. Exit code 0 → continue; non‑zero → fix inputs.

## Run the Full Pipeline
```bash
python -m src.pipeline \
    --seed 42 \
    --max_taxa 100 \
    --perm_iterations 1000
```

### Flags
| Flag | Meaning | Default |
|------|---------|---------|
| `--seed` | Random seed for reproducibility. | 42 |
| `--max_taxa` | Upper bound on taxa retained after filtering (enforces FR‑010). | 100 |
| `--perm_iterations` | Number of permutation iterations (FR‑007). | 1000 |

The command executes all phases (0 → 6) and writes the four deliverables under `results/`.

## Run the Permutation Robustness Test Separately
```bash
python -m src.pipeline.run_permutation --iterations 1000 --seed 42
```
This runs phases 0 → 5, producing `mixed_effects_summary.csv` and `permutation_pvalues.csv`. Runtime is bounded by a 4‑hour wall‑clock guard (SC‑003).

## Verify Outputs
```bash
# Contract‑based tests
pytest -q src/tests

# Quick glance at a result file
head -n 5 results/taxa_correlations.csv
```

## Expected Runtime (benchmark on CI)
| Step | Approx. Wall‑time |
|------|-------------------|
| Data validation & loading | < 2 min |
| Filtering + CLR | < 5 min |
| Slope computation | < 3 min |
| Plain Spearman + BH | < 2 min |
| Mixed‑effects fitting | < 12 min |
| Permutation (1 000 it., ≤ 100 taxa) | 3–4 h |
| PDF report generation | < 1 min |
| **Total** | **≤ 4 h** (well under the 6 h limit) |

**Important:** The pipeline **requires** the `MDS_UPDRS_total` column. If it is missing, the pipeline aborts with an informative error; no synthetic data are generated.

---


