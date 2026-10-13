# Quickstart: Gut Microbiome – PD Progression Pipeline

## Prerequisites
* Python 3.11 (available on the CI runner)  
* Internet access (to download the two HF datasets)  

## Setup
```bash
# 1. Create a fresh virtualenv (CI does this automatically)
python -m venv .venv
source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r requirements.txt
```

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
| Data download & CRC check | < 2 min |
| Filtering + CLR (with pseudocount) | < 5 min |
| Slope computation | < 3 min |
| Correlation + BH | < 2 min |
| Mixed‑effects fitting | < 10 min |
| Permutation (multiple iterations, many taxa, block‑wise) | several hours |
| PDF report generation | < 1 min |
| **Total** | **≤ 4 h** (well under the 6 h limit) |

**Important:** The pipeline requires a longitudinal motor‑score column (`UPDRS_partIII` **or** an alternative such as `MDS_UPDRS_total`) in the clinical metadata. If neither column is present, the pipeline will abort with an informative error, and the researcher must provide an open dataset that includes this outcome before re‑running.

---


