# Quickstart: Ambient Temperature Influence on Moral Decision Speed (Re‑scoped)

## Prerequisites

- Python 3.11+ (recommended via `pyenv` or system Python)  
- `git`  
- Internet access (to download ERA5 and GHSL data)  
- No special API keys are required (all data are publicly hosted).  

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-743-ambient-temperature-influence-on-moral-d

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Data Setup

```bash
# 1. Download Moral Machine CSV (public dataset; script knows the canonical URL)
python code/download_moral_machine.py \
    --output data/raw/moral_machine.csv

# 2. Download ERA5 hourly data (2014‑2018) – **spatially filtered subset** covering only the convex hull of Moral Machine locations (≈ few hundred MB)
python code/download_era5.py \
    --output data/raw/era5_subset.h5

# 3. (Optional) Download GHSL urban/rural classification for indoor/outdoor proxy
python code/download_ghsl.py \
    --output data/raw/ghsl_urban_rural.parquet
```

Both download scripts compute SHA‑256 checksums and append them to `data/external/checksums.txt`.

### Auxiliary Response‑Time Data (FR‑016)

Place the CSV produced by the auxiliary crowdsourced experiment at:

```
data/raw/aux_response_times.csv
```

The file **must contain two columns**: `scenario_id` (matching the Moral Machine `dilemma_id`) and `mean_response_time_ms`. The script will merge this table to the Moral Machine records **by `scenario_id`**, assigning each record the **average latency for that scenario**. If the file is missing, the pipeline aborts with a clear error message, prompting a specification update.

## Pipeline Execution (ordered steps)

All scripts write logs to `results/logs/` and artifacts to `results/`.

### 0. Validate Sources (FR‑014)

```bash
python code/validate_sources.py \
    --moral data/raw/moral_machine.csv \
    --era5 data/raw/era5_subset.h5 \
    --report results/logs/validation_report.json
```

If ERA5 is not hourly, the script exits with an informative error.

### 1. Ingest & Match (geographic join, distance flagging)

```bash
python code/ingestion.py \
    --moral data/raw/moral_machine.csv \
    --era5 data/raw/era5_subset.h5 \
    --ghsl data/raw/ghsl_urban_rural.parquet \
    --out data/processed/merged_dataset.parquet \
    --log results/logs/ingestion_log.json
```

The log contains the **percentage of records matched within 100 km** (SC‑001).

### 2. Preprocess (filtering, feature engineering, response‑time check)

```bash
python code/preprocessing.py \
    --input data/processed/merged_dataset.parquet \
    --aux data/raw/aux_response_times.csv \
    --output data/processed/merged_dataset.parquet \
    --log results/logs/preprocessing_log.json
```

> **Important**: If any `scenario_id` lacks a `mean_response_time_ms` entry, the script aborts and logs the issue (fulfills FR‑016). The merged `response_time_ms` column therefore represents a **scenario‑level average latency**, not an individual‑level measurement.

### 3. Fit Primary Mixed‑Effects Model & Diagnostics

```bash
python code/modeling.py \
    --input data/processed/merged_dataset.parquet \
    --model-output results/stats/model_results.json \
    --fig-dir results/figures/ \
    --log results/logs/modeling_log.json
```

Outputs include coefficient tables, convergence flag, Shapiro‑Wilk p‑value, QQ‑plot, residuals plot, and calibration plot.

### 4. Robustness & Sensitivity Analyses

```bash
python code/robustness.py \
    --input data/processed/merged_dataset.parquet \
    --output results/stats/sensitivity_analysis.csv \
    --fig-dir results/figures/robustness/ \
    --log results/logs/robustness_log.json
```

Generates alternative temperature metric results, outlier‑threshold sweeps, indoor/outdoor‑stratified models (or bootstrap if GHSL missing), and a multiple‑comparison‑corrected summary table (SC‑003).

### 5. Power & Sample Size Verification

```bash
python code/power_analysis.py \
    --output results/logs/power_analysis.txt \
    --log results/logs/power_analysis_log.json
```

Writes the required sample size (≈ tens of thousands) and confirms that the available dataset exceeds this threshold (SC‑004).

## Verification Checklist

| ✅ | Item |
|----|------|
| 1 | `results/logs/validation_report.json` shows `"status": "OK"` (hourly ERA5 verified). |
| 2 | `results/logs/ingestion_log.json` reports match percentage (SC‑001) and flags any `LOW_CONF` records. |
| 3 | `results/logs/preprocessing_log.json` confirms presence of `mean_response_time_ms`; aborts if missing (FR‑016). |
| 4 | `results/stats/model_results.json` contains a `temperature_c` entry with `estimate`, `std_error`, `p_value`. |
| 5 | Diagnostics: `qq_plot.png`, `residuals.png`, `calibration_plot.png` exist; Shapiro‑Wilk p > 0.05 recorded (SC‑005). |
| 6 | `results/logs/modeling_log.json` indicates convergence (`convergence: true`). |
| 7 | `results/stats/sensitivity_analysis.csv` lists coefficients for alternative specifications (SC‑003). |
| 8 | `results/logs/power_analysis.txt` reports required N ≈ 20 000 and confirms dataset size > N. |
| 9 | All output files validate against the schemas in `contracts/`. |

## Troubleshooting

- **Missing `mean_response_time_ms`**: The pipeline stops with a clear message. Collect response latency via a short online experiment (e.g., Prolific, MTurk) and place the CSV at `data/raw/aux_response_times.csv`.  
- **MemoryError**: Ensure `STREAM_DATA=True` in `code/config.py` to enable chunked reads.  
- **ConvergenceWarning**: Check `results/logs/modeling_log.json`; the script will automatically retry with a tighter optimizer tolerance.  
- **GHSL download fails**: The pipeline logs the limitation and proceeds with the bootstrap indoor/outdoor robustness check (FR‑012).  

--- 



