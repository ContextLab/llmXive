# Quickstart: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Prerequisites
- Python 3.11+  
- `pip` (standard Python package manager)  
- Internet access (to download datasets)  
- At least 5 GB free disk space  

## Installation
```bash
# 1. Clone the repository (or navigate to the project root)
git clone 
cd PROJ-533-evaluating-the-impact-of-data-transforma

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Running the Full Pipeline
```bash
python -m code.main --stage all
```

### What the command does
1. **Downloads** the six verified numeric datasets (Wine Quality, Breast Cancer, Iris, Adult, Statlog Heart, Vehicle Silhouettes) via HuggingFace/OpenML loaders and streams additional OpenML datasets (size‑capped at 5 MB) until a total of ≥ 50 are collected.  
2. **Computes SHA‑256** checksums while streaming each file chunk (no full load into memory).  
3. **Imputes** missing values (≤ 10 % missing) using mean for symmetric variables and median for skewed variables; a **sensitivity analysis** can be toggled with `--impute-method median` to compare median vs mean imputation impact.  
4. **Filters** for non‑normality across three Shapiro‑Wilk p‑value bands (0.01‑0.05, 0.05‑0.10, 0.10‑0.20) and ensures *N* ≥ 30.  
5. **Estimates Type I error** by **dual null‑simulation**: (i) stratified label shuffling, (ii) residual permutation, each with several thousand iterations per dataset, using a fixed random seed.  
6. **Generates** simulated datasets with known effect sizes (Cohen’s *d* ∈ {0.2, 0.5, 0.8}) **per real dataset**, preserving each dataset’s own skewness/kurtosis.  
7. **Applies** Box‑Cox, Yeo‑Johnson, rank‑based inverse normal, and baseline transformations.  
8. **Runs** t‑tests / ANOVAs on both real (null) and simulated (alternative) data.  
9. **Aggregates** results, computes 95 % bootstrap CIs (target half‑width ≤ 0.02).  
10. **Performs** a Friedman test with Bonferroni‑corrected post‑hoc comparisons.  
11. **Sweeps** α ∈ {0.01, 0.05, 0.10} for sensitivity analysis.  
12. **Produces** summary tables (`results/aggregated_results.csv`) and figures (`results/figures/`).  

### Step‑by‑step (optional)
| Step | Command |
|------|---------|
| Download & checksum | `python code/data/download_datasets.py && python code/data/checksum_datasets.py` |
| Impute & filter | `python code/data/filters.py` |
| Simulate data | `python code/data/simulations.py` |
| Transform & test | `python code/data/transformations.py && python code/utils/statistical_tests.py` |
| Aggregate & infer | `python code/analysis/aggregation.py && python code/analysis/inference.py` |
| Visualize | `python code/analysis/visualization.py` |

## Checkpointing & Resumption
If the run is interrupted (e.g., CI timeout), a checkpoint is written to `results/checkpoints/`. To resume:
```bash
python -m code.main --stage all --resume
```

## Verifying Outputs
```bash
# Log file
cat results/pipeline.log

# Aggregated statistics (first few rows)
head -n 20 results/aggregated_results.csv

# Figures
display results/figures/error_rates.png
display results/figures/power_curves.png
```

## Troubleshooting
- **Download failures** – Verify network connectivity; loaders are listed in `data/datasets.csv`.  
- **Transformation errors** – Check `data/imputation_log.csv` for log‑shift interventions.  
- **Memory errors** – The pipeline streams files; ensure at least 4 GB RAM is available.  
- **Friedman test issues** – See `results/friedman_summary.txt`; if ties prevent the Friedman test, a fallback Wilcoxon signed‑rank analysis is used automatically.  
- **Missing group label** – Dataset will be excluded and recorded in `data/exclusions.csv`.  
- **Imputation impact** – Review `data/imputation_log.csv` and the optional median‑vs‑mean sensitivity run (use `--impute-method median` to toggle).  

---



