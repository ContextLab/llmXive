# Quickstart: Evaluating Calibration of Probabilistic Weather Forecasts

## Prerequisites
- Python 3.11 or newer  
- Internet access (for dataset download)  
- GitHub Actions runner (or local machine with ≥ 2 CPU cores, ~7 GB RAM, ~14 GB disk)

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-763-evaluating-calibration-of-probabilistic-/code

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Running the Full Pipeline

```bash
# Step 0: Download and verify the open‑source NOAA GFS dataset
bash data/download.sh
bash data/verify.sh   # exits with code 1 if `probability_value` missing

# Step 1: Baseline calibration assessment
python analysis/baseline/align.py
python analysis/baseline/metrics.py
python analysis/baseline/plots.py   # creates reliability_diagram_raw.png, pit_histogram_raw.png

# Step 2: Isotonic recalibration
python analysis/isotonic/train.py
python analysis/isotonic/evaluate.py
python analysis/isotonic/sensitivity.py   # runs 60/40 and 80/20 splits

# Step 3: Bayesian hierarchical recalibration
python analysis/bayesian/model.py          # may fall back to isotonic
python analysis/bayesian/prior_sensitivity.py
python analysis/bayesian/diagnostics.py

# Step 4: Statistical comparison & final summary
python analysis/comparison/diebold_mariano.py
python analysis/comparison/summary.py

echo "Pipeline completed. All results are in the `results/` folder."
```

## Expected Outputs (all under `results/`)

| File | Description |
|------|-------------|
| `results_baseline.csv` | Brier & CRPS for raw forecasts (per lead‑time/variable). |
| `reliability_diagram_raw.png` | Raw reliability diagram. |
| `pit_histogram_raw.png` | Raw PIT histogram. |
| `results_isotonic.csv` | Metrics after isotonic recalibration. |
| `reliability_diagram_isotonic.png` | Isotonic reliability diagram. |
| `sensitivity_analysis_log.csv` | 60/40 & 80/20 split results. |
| `results_bayesian.csv` *or* `results_fallback.csv` | Bayesian metrics (if converged) or isotonic fallback. |
| `convergence_diagnostics.json` | R‑hat, ESS, and timeout information. |
| `diebold_mariano_results.json` | DM or Block‑Bootstrap test outcomes. |
| `summary_table.csv` | Final comparison table (baseline vs. isotonic vs. Bayesian/fallback). |

## Troubleshooting

| Symptom | Action |
|---------|--------|
| **Dataset download fails** | Verify internet connection; re‑run `data/download.sh`; ensure the URL matches the verified HuggingFace link. |
| **`Data Availability Gate Failed`** | The downloaded file lacks `probability_value`/`precip_prob`. Check the raw parquet schema; if missing, the pipeline cannot proceed (per FR‑001). |
| **Bayesian convergence warnings** | Inspect `convergence_diagnostics.json`; if R‑hat > 1.05 or ESS < 400, the pipeline will have already generated `results_fallback.csv`. |
| **MemoryError** | Enable streaming (`datasets.load_dataset(..., streaming=True)`) or reduce sample size via `--sample-size` flag in `run_pipeline.sh`. |
| **DM test reports `normality_test_p < 0.05`** | The pipeline automatically switches to Block‑Bootstrap; review `diebold_mariano_results.json` for the selected method. |

## Verification

```bash
# Unit tests
pytest tests/unit/

# Integration tests (pipeline end‑to‑end on a tiny sample)
pytest tests/integration/

# Contract validation (ensures outputs match schemas)
pytest tests/contract/
```

All tests must pass and the total wall‑clock time must stay below 6 hours on the CI runner.

---
