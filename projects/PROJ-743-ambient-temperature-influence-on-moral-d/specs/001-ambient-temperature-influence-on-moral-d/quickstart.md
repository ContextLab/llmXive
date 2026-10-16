# Quickstart: Ambient Temperature Influence on Moral Decision Speed (Re‑scoped)

## Prerequisites

- Python 3.11+ (recommended via `pyenv` or system Python)  
- `git`  
- Internet access (to download datasets)  
- No special API keys are required; the ERA5 1982 file is hosted on HuggingFace (but will be **rejected** by validation due to hourly‑resolution rule).

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
# 1. Download Moral Machine CSV (verified public URL)
python code/download_moral_machine.py \
    --output data/raw/moral_machine.csv \
    --url https://raw.githubusercontent.com/ethanluoyc/Moral-Machine-Data/master/shared_responses.csv

# 2. (Optional) Download the ERA5 1982 grid (HDF5) – will be validated and **rejected** for lacking hourly resolution.
python code/download_era5.py \
    --output data/raw/era5_1982.h5
```

Both commands compute SHA‑256 checksums and write them to `data/external/checksums.txt`.

## Pipeline Execution

All scripts write logs to `results/logs/` and artifacts to `results/`.

### 1. Validate Sources (FR‑014 – **will abort** if no hourly source is found)

```bash
python code/validate_sources.py \
    --moral data/raw/moral_machine.csv \
    --era5 data/raw/era5_1982.h5 \
    --report results/logs/validation_report.json
```

If an **hourly** ERA5 source is unavailable, the script exits with an informative error and the pipeline stops, ensuring compliance with the Verified Accuracy principle.

### 2. Download WorldPop Urban/Rural Proxy (mandatory indoor/outdoor confound)

```bash
python code/download_worldpop.py \
    --output data/raw/worldpop_2020.tif
```

If the download fails, the script aborts with a clear message.

### 3. Ingest & Match (geographic join, distance flagging)

```bash
python code/ingestion.py \
    --moral data/raw/moral_machine.csv \
    --era5 data/raw/era5_1982.h5 \
    --out data/processed/merged_dataset.parquet \
    --log results/logs/ingestion_log.json
```

### 4. Preprocess (filtering, feature engineering)

```bash
python code/preprocessing.py \
    --input data/processed/merged_dataset.parquet \
    --output data/processed/cleaned_dataset.parquet \
    --log results/logs/preprocessing_log.json
```

### 5. Fit Primary Model & Diagnostics

```bash
python code/modeling.py \
    --input data/processed/cleaned_dataset.parquet \
    --model-output results/stats/model_results.json \
    --fig-dir results/figures/ \
    --log results/logs/modeling_log.json
```

### 6. Robustness & Sensitivity Analyses

```bash
python code/robustness.py \
    --input data/processed/cleaned_dataset.parquet \
    --output results/stats/sensitivity_analysis.csv \
    --fig-dir results/figures/robustness/ \
    --log results/logs/robustness_log.json
```

## Verification Checklist

1. **Validation Report** (`results/logs/validation_report.json`) contains `"status": "ABORT"` if no hourly source is present (as required by FR‑014).  
2. **Ingestion Log** reports the percentage of records matched within 100 km (SC‑001).  
3. **Model Results** (`results/stats/model_results.json`) includes a `latitude_covariate` fixed‑effect entry with `estimate`, `std_error`, and `p_value`.  
4. **Diagnostics**: `hosmer_lemeshow.png` and `calibration_plot.png` exist; Hosmer‑Lemeshow p‑value > 0.05 is recorded in the JSON diagnostics.  
5. **Robustness Table** (`sensitivity_analysis.csv`) lists coefficients for alternative specifications (SC‑003).  

## Troubleshooting

- **MemoryError**: Ensure `STREAM_DATA=True` in `code/config.py`; this forces chunked reads.  
- **ConvergenceWarning**: Check `results/logs/modeling_log.json`; if convergence fails, the script automatically retries with a smaller optimizer tolerance.  
- **Missing Hourly Temperature Source**: The pipeline will abort with a clear message; at that point you may supply an open hourly temperature dataset (if one becomes available) and re‑run from the validation step.  

---



