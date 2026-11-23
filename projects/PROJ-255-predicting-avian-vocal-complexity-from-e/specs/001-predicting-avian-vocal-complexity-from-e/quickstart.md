# Quickstart: Predicting Avian Vocal Complexity

## Prerequisites

*   Python 3.11+
*   pip
*   Access to Xeno-canto API (public)
*   14GB free disk space

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-255-predicting-avian-vocal-complexity-from-e
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import librosa; import statsmodels; print('Dependencies OK')"
    ```

## Running the Pipeline

### Option A: Full Pipeline (End-to-End)

Execute the main orchestrator script:
```bash
python src/main.py --config src/config/config.yaml --mode full
```
*This will download data, extract features, fit models, and generate reports.*

### Option B: Step-by-Step

1.  **Acquire Data**:
    ```bash
    python src/data/acquisition.py --species-list data/species_list.txt
    ```
2.  **Extract Features**:
    ```bash
    python src/data/extraction.py --input data/raw/xc_metadata.csv
    ```
3.  **Preprocess & Filter**:
    ```bash
    python src/data/preprocessing.py --input data/interim/extracted_features.csv
    ```
4.  **Model & Analyze**:
    ```bash
    python src/models/lmm.py --input data/processed/final_dataset.csv
    ```
5.  **Generate Visuals**:
    ```bash
    python src/viz/plots.py --results data/processed/model_results.csv
    ```

## Configuration

Edit `src/config/config.yaml` to adjust:
*   `snr_threshold`: Default 10.0 (dB)
*   `random_seed`: Default 42
*   `species_list`: Path to target species file

## Verification

Run the contract tests to ensure data integrity:
```bash
pytest tests/contract/ -v
```

Run unit tests:
```bash
pytest tests/unit/ -v
```

Check for missing artifacts:
*   `data/processed/final_dataset.csv`
*   `data/processed/model_results.csv`
*   `data/interim/filtered_records.csv`
*   `data/interim/validation_log.csv`
