# Quickstart: Predicting Avian Vocal Complexity from Environmental Noise Levels

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the project repository.

## Setup Instructions

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-255-predicting-avian-vocal-complexity-from-e
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: This installs `librosa`, `statsmodels`, `pandas`, `scikit-learn`, `geopy`, `requests`, and `pytest`.*

4.  **Verify Environment**:
    ```bash
    python -c "import librosa; import statsmodels; print('Environment OK')"
    ```

## Running the Pipeline

The pipeline is executed via the main script in `code/`.

### 1. Data Acquisition (Subset Mode)
To test with a small subset (e.g., 50 recordings) as per US-1:
```bash
python code/main.py --mode acquisition --subset 50
```
*Output*: `data/raw/metadata_subset.csv`, `data/raw/audio_subset/`

### 2. Preprocessing & Feature Extraction
```bash
python code/main.py --mode process --input data/raw/metadata_subset.csv
```
*Output*: `data/processed/final_dataset.csv`, `data/processed/filtered_records.csv`

### 3. Statistical Modeling
```bash
python code/main.py --mode model --input data/processed/final_dataset.csv
```
*Output*: `data/processed/model_results.csv`, `data/processed/sensitivity_analysis.csv`

### 4. Visualization
```bash
python code/main.py --mode viz --input data/processed/model_results.csv
```
*Output*: `data/figures/scatter_plot.png`, `data/figures/heatmap.png`, `data/figures/residuals.png`

### 5. Full Report Generation
```bash
python code/main.py --mode report
```
*Output*: `data/reports/summary_report.md`

## Testing

Run the contract and unit tests:
```bash
pytest tests/ -v
```

*   **Contract Tests**: Validate that output CSVs match `contracts/*.schema.yaml`.
*   **Unit Tests**: Verify `librosa` metric extraction logic and SNR calculation.

## Troubleshooting

*   **Audio File Not Found**: Ensure `data/raw/audio_subset/` contains the downloaded files. Re-run `--mode acquisition`.
*   **Memory Error**: Reduce the `--subset` size or ensure `--chunk-size` is set correctly in `code/utils/config.py`.
*   **Noise Interpolation Fallback**: If "Global Soundscapes" is unavailable, the script will automatically switch to nearest-neighbor interpolation and log the event. Check `data/interim/interpolated_noise.log`.
