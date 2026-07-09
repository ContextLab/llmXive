# Quickstart: Predicting Plant Stress Response from Publicly Available Proteomic Data

## Prerequisites

-   Python 3.11+
-   R (for `biomaRt` via `rpy2` or system call)
-   Git
-   GitHub Actions Runner (or local equivalent with 7GB RAM)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-267-predicting-plant-stress-response-from-pu
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### 1. Data Ingestion & Preprocessing

Run the ingestion and preprocessing script. This will attempt to download data from the verified sources and process it.

```bash
python code/data/ingest.py --species Arabidopsis --stress Drought
python code/data/preprocess.py
```

*Note: If no valid paired data is found, the script will log a warning and proceed with dummy data for pipeline validation.*

### 2. Model Training

Train the Random Forest and SVR models with 5-fold cross-validation.

```bash
python code/models/train.py --method random_forest --cv_folds 5
python code/models/train.py --method svr --cv_folds 5
```

### 3. Evaluation & Reporting

Evaluate the models on cross-stress splits and generate visualizations.

```bash
python code/models/evaluate.py --train_stress Drought --test_stress Salinity
python code/viz/plots.py
```

### 4. Runtime Metrics

Check the `runtime_metrics.json` file to ensure the pipeline completed within the 6-hour limit.

```bash
cat results/runtime_metrics.json
```

## Troubleshooting

-   **Missing Data**: If the ingestion script fails to find paired data, check `logs/ingest.log` for the specific reason (e.g., "No matched transcriptomic data found").
-   **Memory Error**: If the process exceeds 7GB RAM, reduce the dataset size by adding the `--sample_size 1000` flag to the preprocessing step.
-   **biomaRt Error**: Ensure R and the `biomaRt` package are installed and accessible.
