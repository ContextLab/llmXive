# Quickstart: Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

## 1. Prerequisites

-   **Python**: 3.11 or higher.
-   **Memory**: 7 GB+ RAM (recommended for full dataset processing).
-   **Disk**: 14 GB+ free space.
-   **Network**: Access to OpenNeuro.

## 2. Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-295-predicting-cognitive-load-eeg
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
    *Note: `requirements.txt` pins versions compatible with CPU-only execution (e.g., `mne`, `scikit-learn`).*

## 3. Data Download

The pipeline automatically downloads the dataset if not present.

```bash
python code/data/download.py
```

-   **Output**: Raw data stored in `data/raw/`.
-   **Verification**: A manifest file `data/manifest.yaml` is generated with checksums.

## 4. Running the Pipeline

Execute the full pipeline (Preprocessing → Feature Extraction → Modeling → Sensitivity):

```bash
python code/main.py
```

### Configuration
Modify `pipeline_config.yaml` to adjust parameters:
-   `filter_low`: 1.0
-   `filter_high`: 45.0
-   `sampling_rate`: 250
-   `ica_components`: [1, 2] (example indices for blink removal)

## 5. Testing

Run unit and integration tests:

```bash
pytest tests/ -v
```

-   **Unit Tests**: Verify feature extraction logic and label generation.
-   **Integration Tests**: Verify end-to-end data flow, memory constraints, and quality checks (SC-004, SC-005).

## 6. Expected Outputs

-   **Processed Data**: `data/processed/feature_matrix.csv`, `data/processed/labels.csv`.
-   **Model Results**: `results/model_metrics.json` (R², RMSE, p-values, permutation results).
-   **Sensitivity Report**: `results/sensitivity_report.csv` (R² for different window sizes).
-   **Logs**: `logs/pipeline.log` (includes memory usage, chunked loading events, and quality check results).

## 7. Troubleshooting

-   **OOM Error**: The pipeline automatically switches to chunked loading. If it fails, reduce `batch_size` in `config.py`.
-   **Missing Gaze Data**: The script will halt with an error if `gaze.tsv` is not found in the raw data.
-   **Quality Check Failure**: If epoch retention < 70%, the pipeline halts and logs the exclusion count.
-   **Slow Runtime**: Ensure no other heavy processes are running; the pipeline is optimized for 2-core CPUs.