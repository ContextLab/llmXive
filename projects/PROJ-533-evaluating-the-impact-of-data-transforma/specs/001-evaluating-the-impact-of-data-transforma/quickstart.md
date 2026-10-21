# Quickstart: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Prerequisites
- Python 3.11+  
- `pip` (Python package manager)  
- Internet access (to download datasets)  
- sufficient free disk space (on the order of tens of gigabytes)  

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
What happens:
1. **Downloads** verified datasets, computes SHA‑256 checksums.  
2. **Filters** for non‑normal continuous variables and imputes missing values.  
3. **Characterizes** distribution shape (skewness, kurtosis).  
4. **Estimates Type I error** by **shuffling group labels on the filtered real datasets** (multiple iterations, fixed seed).  
5. **Generates** simulated datasets with known effect sizes for power analysis.  
6. **Applies** Box‑Cox, Yeo‑Johnson, and rank‑based inverse‑normal transformations.  
7. **Runs** t‑tests/ANOVAs on both real (for Type I) and simulated (for power) data.  
8. **Aggregates** results, computes bootstrap confidence intervals (target half‑width ±0.02).  
9. **Assesses transformation effects** with a **Friedman test** and Bonferroni‑corrected pairwise post‑hoc comparisons.  
10. **Produces** summary tables (`results/aggregated_results.csv`) and figures (`results/figures/`).  

### Step‑by‑Step (optional)
| Step | Command |
|------|---------|
| Download & filter | `python code/data/download_datasets.py && python code/data/filters.py` |
| Simulate data | `python code/data/simulations.py` |
| Transform & test | `python code/data/transformations.py && python code/utils/statistical_tests.py` |
| Aggregate & analyze | `python code/analysis/aggregation.py` |
| Visualization | `python code/analysis/visualization.py` |

## Checkpointing & Resumption
If the run is interrupted (e.g., CI timeout), a checkpoint is written to `results/checkpoints/`. To resume:
```bash
python -m code.main --stage all --resume --run-id your_run_id
```

## Verifying Outputs
```bash
# Log file
cat results/pipeline.log

# Aggregated statistics
head -n 20 results/aggregated_results.csv

# Figures
display results/figures/error_rates.png
```

## Troubleshooting
- **Dataset download failures** – Verify network connectivity; URLs are listed in `data/datasets.csv`.  
- **Transformation errors** – Check `data/imputation_log.csv` for log‑shift interventions.  
- **Memory errors** – The pipeline streams large files; ensure the runner has at least 4 GB RAM.  
- **Friedman test non‑convergence** – Review `results/friedman_summary.txt`; a fallback pairwise Wilcoxon signed‑rank test will be used automatically.  
- **Missing group label** – Exclude and record in `data/exclusions.csv`.