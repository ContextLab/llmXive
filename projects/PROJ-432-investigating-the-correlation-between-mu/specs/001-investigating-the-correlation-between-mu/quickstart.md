# Quickstart: Investigating the Correlation Between Muon Flux and Atmospheric Temperature Profiles

## Prerequisites

- Python 3.11+
- Git
- Access to a terminal (Linux/macOS/WSL)
- **CDS API Key** (for ERA5 data): Register at https://cds.climate.copernicus.eu and configure `~/.cdsapirc`.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-432-investigating-the-correlation-between-mu
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` will include `pandas`, `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `h5py`, `pyyaml`, `cdsapi`.*

## Running the Pipeline

### 1. Ingest and Align Data
Download and process the data from the verified sources.
```bash
python src/main.py --stage ingest
```
*Output: `data/processed/aligned_dataset.csv`*

### 2. Run Statistical Analysis
Compute correlations and regression (with pre-whitening and Newey-West SEs).
```bash
python src/main.py --stage analyze
```
*Output: `results/correlation_results.json`, `results/regression_model.json`*

### 3. Run Sensitivity & Stratification
Perform robustness checks (includes power check for seasonal split).
```bash
python src/main.py --stage sensitivity
```
*Output: `results/sensitivity_analysis.json`*

### 4. Full Pipeline
Run the entire workflow end-to-end.
```bash
python src/main.py --stage full
```

## Verifying Results

To verify the results against the contract:
```bash
pytest tests/contract/
```
This ensures the output JSON matches the schema defined in `contracts/analysis_output.schema.yaml`.

## Troubleshooting

- **Missing Data**: If the pipeline logs "No overlapping dates", check `logs/alignment.log`. The IceCube and ERA5 datasets may not cover the same time period. The pipeline will then attempt to load NOAA NCEI data. If that also fails, the pipeline aborts with `Data Mismatch`.
- **Memory Error**: Unlikely given the dataset size, but if it occurs, ensure no other heavy processes are running.
- **API Errors**: Ensure your CDS API key is configured correctly in `~/.cdsapirc` for ERA5 data.
- **Underpowered Seasonal Test**: If the output reports "Insufficient Data for Stratification", it means one season had fewer than 30 days of data. This is expected behavior per the power analysis.