# Quickstart: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Prerequisites

*   Python 3.11+
*   `git`
*   Access to GitHub Actions (for CI execution)

## Setup

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

## Running the Pipeline

### 1. Data Ingestion & Curation
Downloads real data from the verified source (or halts if unavailable) and filters for FCC/Self.
```bash
python code/data/ingestion.py
python code/data/curation.py
```
*Output*: `data/curated/filtered.csv`, `data/curated/data_provenance.json`

### 2. Feature Engineering
Computes atomic descriptors.
```bash
python code/features/descriptors.py
```
*Output*: `data/curated/enriched.csv`

### 3. Model Training
Trains RF, GB, and Linear models with Grid Search.
```bash
python code/models/train.py
```
*Output*: `models/final_rf.pkl`, `models/final_gb.pkl`, `models/linear_coef.json`

### 4. Validation & Sensitivity
Evaluates performance and runs threshold sensitivity analysis.
```bash
python code/validation/baseline.py
python code/models/evaluate.py
python code/validation/sensitivity.py
```
*Output*: `results/metrics.json`, `results/sensitivity_plot.png`

## Testing

Run the test suite to verify data filtering and feature calculations:
```bash
pytest tests/ -v
```

## Expected Results

*   **Linear Model**: Should show a statistically significant negative or positive coefficient for `size_mismatch` (p < 0.05), depending on the real data trend. If N < 50, results are labeled "Exploratory".
*   **Sensitivity**: The classification rate for "significant shift" should vary smoothly as the threshold moves from 0.45 to 0.55 eV.
*   **Resource Usage**: Total runtime < 15 minutes on a 2-core CPU.