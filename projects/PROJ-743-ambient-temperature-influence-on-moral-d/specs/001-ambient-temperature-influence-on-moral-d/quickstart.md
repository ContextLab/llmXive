# Quickstart: Ambient Temperature Influence on Moral Decision Speed (Re‑scoped)

## Prerequisites

- Python 3.11+ (recommended via `pyenv` or system Python)  
- `git`  
- Internet access (to download datasets)  
- No special API keys are required; the ERA5 file is fetched from a verified HuggingFace URL.

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
# 1. Download Moral Machine CSV (public dataset; no verified URL, but script knows the canonical location)
python code/download_moral_machine.py \
    --output data/raw/moral_machine.csv

# 2. Download ERA5 hourly data (2014‑2018) – verified hourly resolution
python code/download_era5.py \
    --output data/raw/era5_2014_2018.h5
```

Both commands compute SHA‑256 checksums and write them to `data/external/checksums.txt`.

## Pipeline Execution

All scripts write logs to `results/logs/` and artifacts to `results/`.

### 1. Validate Sources (FR‑014 – will abort if ERA5 is not hourly)

```bash
python code/validate_sources.py \
    --moral data/raw/moral_machine.csv \
    --era5 data/raw/era5_2014_2018.h5 \
    --report results/logs/validation_report.json
```

If the hourly ERA5 source is unavailable, the script exits with a clear error and the pipeline stops, complying with the Verified Accuracy principle.

### 2. (Optional) Download WorldPop raster for indoor/outdoor proxy

> No verified public URL exists for WorldPop; the script will attempt to download from the official WorldPop portal. If the download fails, the pipeline records the limitation and continues without the proxy.

```bash
python code/download_worldpop.py \
    --output data/raw/worldpop_2020.tif
```

### 3. Ingest & Match (geographic join, distance flagging)

```bash
python code/ingestion.py \
    --moral data/raw/moral_machine.csv \
    --era5 data/raw/era5_2014_2018.h5 \
    --out data/processed/merged_dataset.parquet \
    --log results/logs/ingestion_log.json
```

### 4. Preprocess (filtering, feature engineering)

```bash
python code/preprocessing.py \
    --input data/processed/merged_dataset.parquet \
    --output data/processed/merged_dataset.parquet \
    --log results/logs/preprocessing_log.json
```

> **Important**: If `response_time_ms` is absent, this script aborts with an informative error and logs the issue. The specification must be updated to provide a dataset that includes response times.

### 5. Fit Primary Mixed‑Effects Model & Diagnostics

```bash
python code/modeling.py \
    --input data/processed/merged_dataset.parquet \
    --model-output results/stats/model_results.json \
    --fig-dir results/figures/ \
    --log results/logs/modeling_log.json
```

### 6. Robustness & Sensitivity Analyses

```bash
python code/robustness.py \
    --input data/processed/merged_dataset.parquet \
    --output results/stats/sensitivity_analysis.csv \
    --fig-dir results/figures/robustness/ \
    --log results/logs/robustness_log.json
```

### 7. Power & Sample Size Verification

```bash
python code/power_analysis.py \
    --output results/logs/power_analysis.txt \
    --log results/logs/power_analysis_log.json
```

## Verification Checklist

1. **Validation Report** (`results/logs/validation_report.json`) contains `"status": "OK"` if an hourly ERA5 source is present; otherwise it aborts (FR‑014).  
2. **Ingestion Log** reports the percentage of records matched within 100 km (SC‑001).  
3. **Preprocessing Log** confirms presence of `response_time_ms`; if missing, the pipeline aborts and the issue is recorded.  
4. **Model Results** (`results/stats/model_results.json`) includes a `temperature_c` entry with `estimate`, `std_error`, and `p_value`.  
5. **Diagnostics**: `qq_plot.png`, `residuals.png`, `calibration_plot.png` exist; Shapiro‑Wilk p‑value > 0.05 recorded in JSON (SC‑005).  
6. **Robustness Table** (`sensitivity_analysis.csv`) lists coefficients for alternative specifications (SC‑003).  
7. **Power Analysis** (`results/logs/power_analysis.txt`) reports required N ≈ 20 000 and confirms that the available dataset exceeds this threshold (SC‑004).  

## Troubleshooting

- **Missing `response_time_ms`**: The pipeline will stop with a clear message. Supply a Moral Machine release that includes response latency or update the specification accordingly.  
- **MemoryError**: Ensure `STREAM_DATA=True` in `code/config.py` to force chunked reads.  
- **ConvergenceWarning**: Check `results/logs/modeling_log.json`; the script will retry with a tighter tolerance if needed.  
- **WorldPop unavailable**: The pipeline logs the limitation and proceeds without the indoor/outdoor proxy (FR‑012).  

---

