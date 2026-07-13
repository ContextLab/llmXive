# Quickstart: Predicting the Impact of Cold Work on Recrystallization Kinetics

## Prerequisites

* Python 3.11+
* Git
* (Optional) A CSV file containing experimental data (see **Data Setup** below).

## Installation

1. **Clone the repository**  
   ```bash
   git clone <repo-url>
   cd projects/PROJ-240-predicting-the-impact-of-cold-work-on-re
   ```

2. **Create a virtual environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```
   All dependencies are pinned to CPU‑only wheels (`pandas`, `scikit-learn`, `numpy`, `scipy`, `pyyaml`).

## Data Setup

The pipeline requires a CSV with the exact columns listed in the Data Model (`cold_work_pct`, `mg_wt`, `si_wt`, `cu_wt`, `mn_wt`, `annealing_temp_k`, `time_to_peak`).  

You have two options:

### Option A: Supply Your Own Experimental CSV
1. Place a file named `alloy_data.csv` in `data/raw/`.  
2. The file **must** contain **all** required columns (case‑sensitive).  
3. The pipeline will verify column presence, compute a SHA‑256 checksum, and record it in `state/projects/PROJ-240.yaml`. Missing columns cause a clear abort (Constitution I).

### Option B: Automatic Synthetic Generation (deterministic fallback)
If no CSV is found, the pipeline automatically runs `code/simulate_data.py` (seed = 42) to create `data/raw/synthetic_alloy_data.csv` with ≥ 100 synthetic rows covering the full variable space.  
- The synthetic generator is version‑controlled; its output checksum is stored in `state/projects/PROJ-240.yaml`.  
- This guarantees that the entire pipeline can run on a fresh CI runner without manual data provision.

## Running the Full Pipeline

```bash
python -m code.pipeline
```

The script will:

1. Ingest the data (user CSV or synthetic fallback).  
2. Clean, clip outliers, and engineer interaction features.  
3. Train the Random Forest model with 5‑fold CV and an 80/20 hold‑out test set.  
4. Perform the permutation test for interaction significance.  
5. Write `results/metrics.json` and generate figures in `results/figures/`.  

## Interpreting Results

- Open `results/metrics.json` to see R², MAE, CV statistics, and the permutation‑test p‑value.  
- Feature‑importance and partial‑dependence plots are saved as PNGs in `results/figures/`.  
- If you supplied real experimental data, the results reflect that dataset; otherwise they reflect the deterministic synthetic data.

## Notes

- The pipeline aborts with an informative error if the dataset contains an insufficient number of rows for 5‑fold CV.  
- Outliers (`time_to_peak` > 1000 h) are clipped to the 99th percentile; see `results/outlier_log.txt` for details.  
- All random seeds are fixed (`seed=42`) to ensure reproducibility (Constitution I).  
