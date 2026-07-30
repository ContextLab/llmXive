# Quickstart: Predicting Glass Formation Tendency

## Prerequisites

- Python 3.10+
- `pip` or `conda`
- Access to a GitHub Actions runner (or local machine with 2+ CPU cores, 7GB RAM)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-480-predicting-glass-formation-tendency-with/code
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
    *Dependencies include: `pymatgen`, `xgboost`, `pandas`, `scikit-learn`, `pytest`, `matbench`.*

## Running the Pipeline

### 1. Data Download & Validation

Download raw data and validate availability:
```bash
python data/download.py
python data/validate.py
```
*Output*: `data/raw/` (downloaded CSVs) and a log of any validation errors (e.g., missing target variable).

### 2. Descriptor Computation

Compute atomic descriptors:
```bash
python data/preprocess.py
```
*Output*: `data/processed/composition_records.csv` with computed descriptors.

### 3. Model Training

Train the XGBoost model:
```bash
python model/train.py
```
*Output*: `data/processed/model.pkl` and `data/processed/metrics.json`.

### 4. Interpretability & Reporting

Generate feature importance and plots:
```bash
python model/interpret.py
```
*Output*: `data/processed/feature_importance.csv`, `data/processed/pdp_plot.png`, `data/processed/threshold_sensitivity.csv`.

## Testing

Run unit and integration tests:
```bash
pytest tests/
```

## Troubleshooting

- **"Unknown Element" errors**: The dataset contains an element not in `pymatgen`'s database. These samples are automatically excluded. Check `logs/exclusions.log`.
- **"Insufficient samples"**: The dataset has < 30 samples. The pipeline halts. Verify the source dataset.
- **"Out of Memory"**: Unlikely with < 1000 samples. If this occurs, reduce the dataset size or check for memory leaks in `pymatgen` calls.
- **"Tautology Detected"**: The target variable is derived from the same descriptors. The pipeline halts with a warning.
- **"Trivial Task"**: The binary classification task is trivial (perfect separation). The pipeline halts with a warning.