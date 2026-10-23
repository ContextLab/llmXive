# Quickstart: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Prerequisites
- Python 3.11+  
- `pip` (standard Python package manager)  
- Internet access (to download the verified datasets)  
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
1. **Download & checksum** the datasets by issuing a programmatic OpenML query that selects public classification datasets with ≥ 30 rows, at least one continuous feature, and a categorical target (the seven URLs listed in the constitution are excluded because they lack the required structure).  
2. **Impute missing values** (mean for near‑symmetric variables, median for skewed) and also run a K‑NN‑imputation sensitivity branch.  
3. **Filter** for non‑normality (Shapiro‑Wilk *p* ∈ [0.01, 0.20]) and *N* ≥ 30.  
4. **If < 50 datasets survive**, the pipeline continues querying OpenML until the ≥ 50‑dataset goal is reached.  
5. **Apply transformations** (Box‑Cox, Yeo‑Johnson, rank‑inverse‑normal, baseline).  
6. **Estimate Type I error** using stratified label shuffling (5 000 iterations each).  
7. **Generate simulated power datasets** for Cohen’s *d* = 0.2, 0.5, 0.8 (1 000 per effect size per real dataset).  
8. **Run t‑tests / ANOVAs** on all transformed versions.  
9. **Bootstrap** (10 000 resamples) to obtain 95 % CIs with **target half‑width ≤ 0.02**; if the target cannot be met, the actual half‑width is reported.  
10. **Friedman test** with Bonferroni‑corrected post‑hoc comparisons.  
11. **α‑sensitivity sweep** (α = 0.01, 0.05, 0.10).  
12. **Produce** `results/aggregated_results.csv` and figures in `results/figures/`.  

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
- **Memory errors** – The pipeline streams files; ensure at least 4 GB RAM is free.  
- **Friedman test ties** – See `results/friedman_summary.txt`; the fallback Wilcoxon analysis runs automatically.  
- **Missing group label** – Dataset will be excluded and recorded in `data/exclusions.csv`.  
- **Imputation impact** – Review `data/imputation_log.csv`; you can rerun with `--impute-method median` to compare.  

---



