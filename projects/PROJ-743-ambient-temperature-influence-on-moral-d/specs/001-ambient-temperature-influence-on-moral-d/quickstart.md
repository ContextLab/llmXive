# Quickstart: Ambient Temperature Influence on Moral Decision Speed

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Internet access (for dataset download)
- CDS API Key (for ERA5 data)

## Installation

1. **Clone Repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-743-ambient-temperature-influence-on-moral-d
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Configure CDS API**:
 - Register at https://cds.climate.copernicus.eu/
 - Create `.cdsapirc` in your home directory with your API key.

## Data Setup

1. **Download Moral Machine Data**:
 - Download from: https://www.science.org/doi/ (or the provided CSV link).
 - Save as `data/raw/moral_machine.csv`.

2. **Download Temperature Data**:
 - **Option A (ERA5 - Required)**: Run `python code/fetch_era5_data.py` to fetch the 2014-2018 subset via CDS API.
 - Save to `data/raw/era5_data/`.

## Running the Pipeline

### 1. Validate Sources (FR-014)

```bash
python code/validate_sources.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output results/logs/validation_report.json
```

### 2. Ingest and Merge

```bash
python code/ingestion.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output data/processed/merged_dataset.parquet
```

### 3. Preprocess

```bash
python code/preprocessing.py --input data/processed/merged_dataset.parquet --output data/processed/cleaned_dataset.parquet
```

### 4. Run Analysis

```bash
python code/modeling.py --input data/processed/cleaned_dataset.parquet --output results/stats/model_results.json --figs results/figures/
```

### 5. Robustness Check

```bash
python code/robustness.py --input data/processed/cleaned_dataset.parquet --output results/stats/sensitivity_analysis.csv
```

## Verification

1. Check `results/logs/validation_report.json` for "PASS" status.
2. Check `results/logs/processing_log.txt` for "SUCCESS" messages.
3. Verify `results/stats/model_results.json` contains a `temperature_c` coefficient and `p_value`.
4. Inspect `results/figures/residual_qq.png` for normality.

## Troubleshooting

- **Memory Error**: If the dataset is too large, enable streaming in `config.py` (`STREAM_DATA = True`).
- **Convergence Warning**: The model may fail to converge. Check `results/logs/model_diagnostics.txt` and try reducing random effects or switching to GLMM.
- **Missing Data**: If >10% of records are dropped, check `data/processed/data_quality_log.json` for reasons.
- **CDS API Error**: Ensure `.cdsapirc` is correctly configured and you have a valid API key.
