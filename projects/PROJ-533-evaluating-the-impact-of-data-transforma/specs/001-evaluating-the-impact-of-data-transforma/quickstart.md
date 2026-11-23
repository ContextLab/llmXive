# Quickstart: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Prerequisites
- Python 3.11+  
- `pip` (standard Python package manager)  
- Internet access (to download the verified OpenML datasets and the six HuggingFace URLs)  
- At least **5 GB** free disk space  

## Installation
```bash
# 1. Clone the repository
git clone https://github.com/your-org/PROJ-533-evaluating-the-impact-of-data-transforma.git
cd PROJ-533-evaluating-the-impact-of-data-transforma

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Running the Full Pipeline
```bash
python -m src.main --stage all
```

### What the command does
1. **Download & checksum**: Queries OpenML for classification datasets meeting the size/feature criteria, streams them, computes SHA‑256, and records metadata in `data/datasets.csv`. If the OpenML pool is insufficient, the six verified HuggingFace URLs are inspected and added when they satisfy the same criteria.  
2. **Impute & filter**: Applies mean/median imputation (primary) and logs the method per variable; also runs a K‑NN‑imputation sensitivity branch. Filters out datasets failing Shapiro‑Wilk (*p* ≥ 0.05), *N* < 30, or missing > 10 %.  
3. **Simulate null & power datasets**: Generates synthetic data preserving each real dataset’s skewness/kurtosis and embeds Cohen’s *d* = 0.2, 0.5, 0.8 for power estimation.  
4. **Apply transformations**: Baseline, Box‑Cox, Yeo‑Johnson, rank‑inverse‑normal (log‑shift applied automatically when needed).  
5. **Estimate Type I error**: Stratified label shuffling (5 000 permutations, seed = 42) and parametric testing.  
6. **Estimate power**: Runs the same tests on simulated data; compares empirical power to analytical power from `statsmodels`.  
7. **Aggregate & infer**: Hierarchical bootstrap (target CI half‑width ≤ 0.07), Friedman test, Bonferroni‑corrected Wilcoxon post‑hoc, α‑sensitivity sweep.  
8. **Produce outputs**: `results/aggregated_results.csv`, `results/sensitivity_results.csv`, and figures in `results/figures/`.  

### Step‑by‑step (optional)
| Step | Command |
|------|---------|
| Download & checksum | `python src/data/download_datasets.py` |
| Impute & filter | `python src/data/impute_and_filter.py` |
| Simulate null & power datasets | `python src/data/simulate_datasets.py` |
| Transform & test (null) | `python src/analysis/null_simulation.py` |
| Transform & test (power) | `python src/analysis/power_estimation.py` |
| Aggregate & infer | `python src/analysis/aggregation.py && python src/analysis/inference.py` |
| Visualize | `python src/analysis/visualization.py` |

## Checkpointing & Resumption
If the run is interrupted (e.g., CI timeout), a checkpoint is written after each dataset in `results/checkpoints/`. To resume:
```bash
python -m src.main --stage all --resume
```

## Verifying Outputs
```bash
# Log
cat results/pipeline.log

# Aggregated statistics (first few rows)
head -n 20 results/aggregated_results.csv

# Figures
display results/figures/error_rates.png
display results/figures/power_curves.png
display results/figures/alpha_sweep.png
```

## Troubleshooting
- **Download failures** – Verify network connectivity; the OpenML query is deterministic and does not rely on hard‑coded URLs.  
- **Transformation errors** – Check `data/imputation_log.csv` for any log‑shift interventions.  
- **Memory errors** – The pipeline streams data; ensure at least 4 GB RAM is free.  
- **Friedman test ties** – See `results/friedman_summary.txt`; the fallback Wilcoxon analysis runs automatically.  
- **Missing group label** – Dataset will be excluded and recorded in `data/exclusions.csv`.  
- **Imputation impact** – Review `data/imputation_log.csv`; you can rerun with `--impute-method knn` to compare.  

---
