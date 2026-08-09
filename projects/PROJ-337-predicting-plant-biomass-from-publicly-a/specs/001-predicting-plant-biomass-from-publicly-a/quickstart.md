# Quickstart: Predicting Plant Biomass from Publicly Available Hyperspectral Imagery

## Prerequisites

-   Python 3.11+
-   `pip` or `conda`
-   Git
-   ~15 GB disk space (for raw data and processing)
-   ~8 GB RAM (streaming/chunking will be used to stay within 7 GB)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/your-repo.git
    cd your-repo/projects/PROJ-337-predicting-plant-biomass-from-publicly-a
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Verify installation**:
    ```bash
    python -c "import sklearn; import torch; print('Dependencies OK')"
    ```

## Running the Pipeline

### Step 1: Download Data
Download the NEON dataset and verify checksums.
```bash
python code/data/download.py --source neon --verify
```
*Output*: `data/raw/neon_hyperspectral.zip`, `data/raw/neon_metadata.json` (with checksums).

### Step 2: Preprocess Data
Apply atmospheric correction and extract labels.
```bash
python code/data/preprocess.py --input data/raw/neon_hyperspectral.zip --output data/processed/
python code/data/extract_labels.py --input data/processed/ --output data/final/analysis_ready.csv
```
*Output*: `data/final/analysis_ready.csv` (clean dataset).

### Step 3: Train Models
Train Random Forest and TabPFN (with fallback).
```bash
python code/models/train.py --input data/final/analysis_ready.csv --output results/model_results.json
```
*Output*: `results/model_results.json` (metrics per fold).

### Step 4: Evaluate & Ablate
Compare against null baseline and run ablation study.
```bash
python code/models/evaluate.py --input results/model_results.json --output results/ablation_summary.json
python code/models/ablation.py --input data/final/analysis_ready.csv --output results/ablation_summary.json
```
*Output*: `results/ablation_summary.json` (delta in metrics).

### Step 5: Sensitivity Analysis
Sweep feature importance thresholds.
```bash
python code/analysis/sensitivity.py --input results/model_results.json --output results/sensitivity_sweep.json
```
*Output*: `results/sensitivity_sweep.json` (metrics per threshold).

## Testing

Run the test suite to verify pipeline integrity.
```bash
pytest tests/ -v
```

## Troubleshooting

-   **Memory Error**: Ensure `streaming=True` is used in data loading or reduce batch size.
-   **TabPFN Failure**: The pipeline automatically falls back to Random Forest. Check logs for `Fallback triggered`.
-   **Missing Data**: Check `data/final/analysis_ready.csv` for exclusion logs. If >5% rows dropped, review preprocessing steps.
