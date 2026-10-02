# Quickstart: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Prerequisites

-   Python 3.11+
-   Git
-   Access to the "Verified datasets" URLs (see `research.md` for current status).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-415-predicting-the-impact-of-alloying-on-the
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
    *Note: `requirements.txt` will pin `scikit-learn`, `pandas`, `numpy`, `mendeleev`, `pytest`.*

## Running the Pipeline

### 1. Data Ingestion & Curation
This step filters the raw data and checks for validity.
```bash
python code/ingestion/curation.py
```
-   **Output**: `data/curated/filtered.csv`, `data/curated/data_provenance.json`.
-   **Failure Mode**: If no valid FCC self-diffusion data is found in the verified URLs, the script exits with `ERROR: No verified real dataset found...`.

### 2. Feature Engineering
Computes atomic descriptors.
```bash
python code/features/engineering.py
```
-   **Output**: `data/curated/enriched.csv`.

### 3. Model Training
Trains RF, GB, and Linear models.
```bash
python code/models/train.py
```
-   **Output**: `models/final_rf.pkl`, `models/final_gb.pkl`, `models/linear_coef.json`.

### 4. Validation & Sensitivity Analysis
Generates baseline reports and threshold stability plots.
```bash
python code/validation/baseline.py
python code/validation/sensitivity.py
```
-   **Output**: `results/baseline_report.json`, `results/sensitivity_plot.png`, `results/stability_index.json`.

## Testing

Run the full test suite:
```bash
pytest tests/ -v
```

Run specific unit tests:
```bash
pytest tests/unit/test_feature_engineering.py -v
```

## Troubleshooting

-   **"No verified real dataset found"**: The provided verified URLs do not contain the required metallurgical data. The pipeline correctly halts. Do not use synthetic data.
-   **"Stratification failed"**: If the dataset contains only one host metal, the script will fallback to a random split and log a warning.
-   **Memory Error**: The dataset size is expected to be small (<10 MB). If this error occurs, check for infinite loops or data leaks in the ingestion step.
