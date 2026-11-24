# Quickstart: Ambient Temperature Influence on Moral Decision Speed (Re‑scoped)

## Prerequisites

- Python 3.11+ (recommended via `pyenv` or system Python)  
- `git`  
- Internet access (to download ERA5 and GHSL data)  
- No special API keys; all data are publicly hosted.

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

# 2. Download ERA5 hourly data (2014‑2018) – spatially filtered subset covering
#    only the convex hull of Moral Machine locations (≈ few hundred MB)
python code/download_era5.py \
    --output data/raw/era5_subset.h5

# 3. (Optional) Download GHSL urban/rural classification for indoor/outdoor proxy
python code/download_ghsl.py \
    --output data/raw/ghsl_urban_rural.parquet
```

Both download scripts compute SHA‑256 checksums and append them to `data/external/checksums.txt`.

### Auxiliary Response‑Time Data (FR‑016)

Place the CSV from the crowdsourced latency experiment at:

```
data/raw/latency_study.csv
```

The file **must contain two columns**: `scenario_id` (matching Moral Machine `dilemma_id`) and `mean_response_time_ms`. The pipeline will abort with a clear error if the file is missing or any scenario lacks a latency entry.

*Construct validity*: The proxy captures systematic speed differences driven by scenario difficulty, aligning with the research question while acknowledging that individual‑level RTs are unavailable.

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

### 1. Ingest & Match (geographic join, distance flagging, interpolation)

```bash
python code/ingestion.py \
    --moral data/raw/moral_machine.csv \
    --era5 data/raw/era5_subset.h5 \
    --ghsl data/raw/ghsl_urban_rural.parquet \
    --out data/processed/merged_dataset.parquet \
    --log results/logs/ingestion_log.json
```

The log contains the **percentage of records matched within 100 km** (SC‑001) and flags low‑confidence matches.

### 2. Preprocess (filtering, feature engineering, latency merge)

```bash
python code/preprocessing.py \
    --input data/processed/merged_dataset.parquet \
    --aux data/raw/latency_study.csv \
    --output data/processed/merged_dataset.parquet \
    --log results/logs/preprocessing_log.json
```

> **Important**: If any `scenario_id` lacks a `mean_response_time_ms` entry, the script aborts and logs the issue (fulfills FR‑016). The resulting `response_time_ms` column is a **scenario‑level average latency**.

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

Generates alternative temperature metric results, outlier‑threshold sweeps, indoor/outdoor stratified models (or bootstrap if GHSL missing), **spatially clustered standard errors**, and a multiple‑comparison‑corrected summary table (SC‑003).

### 5. Power & Sample Size Verification

```bash
python code/power_analysis.py \
    --output results/logs/power_analysis.txt \
    --log results/logs/power_analysis_log.json
```

Writes the required sample size (a sufficiently large magnitude) and confirms that the Moral Machine dataset exceeds this threshold (SC‑004).

## Verification Checklist

| ✅ | Item |
|----|------|
| 1 | `results/logs/validation_report.json` shows `"status": "OK"` (hourly ERA5 verified). |
| 2 | `results/logs/ingestion_log.json` reports match percentage (SC‑001) and flags any low‑confidence records. |
| 3 | `results/logs/preprocessing_log.json` confirms presence of `mean_response_time_ms`; aborts if missing (FR‑016). |
| 4 | `results/stats/model_results.json` contains a `temperature_c` entry with `estimate`, `std_error`, `p_value`. |
| 5 | Diagnostic files (`qq_plot.png`, `residuals.png`, `calibration_plot.png`) exist; Shapiro‑Wilk p > 0.05 recorded (SC‑005). |
| 6 | `results/logs/modeling_log.json` indicates `convergence: true` (SC‑004). |
| 7 | `results/stats/sensitivity_analysis.csv` lists coefficients for alternative specifications (SC‑003). |
| 8 | `results/logs/power_analysis.txt` reports required N ≈ a sufficiently large sample size and confirms dataset size > N. |
| 9 | All output files validate against the schemas in `contracts/`. |
| 10 | Spatial clustering of standard errors is applied (addresses methodology‑5810047b). |

## Troubleshooting

- **Missing `mean_response_time_ms`**: The pipeline stops with a clear message. Conduct a short crowdsourced latency experiment (e.g., Prolific, MTurk) and place the resulting CSV at `data/raw/latency_study.csv`.  
- **MemoryError**: Set `STREAM_DATA=True` in `code/config.py` to enable chunked reads.  
- **ConvergenceWarning**: Check `results/logs/modeling_log.json`; the script will automatically retry with a tighter optimizer tolerance.  
- **GHSL download fails**: The pipeline logs the limitation and proceeds with the bootstrap indoor/outdoor robustness check (FR‑012).  

---

