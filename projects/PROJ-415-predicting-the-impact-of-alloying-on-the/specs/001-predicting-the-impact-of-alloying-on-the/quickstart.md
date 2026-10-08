# Quickstart: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a verified NIST SRD 150 dataset (or a pre-cached copy in `data/raw/`).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-415-predicting-the-impact-of-alloying-on-the
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Data Setup

1.  **Verify Data Availability**:
    Ensure the file `data/raw/nist_diffusion_raw.csv` (or the verified source file) exists.
    *   *Note*: If the dataset is not present, the pipeline will halt with an error. Do not use synthetic data.

2.  **Run the Ingestion Script**:
    ```bash
    python code/data/streaming_loader.py
    ```
    *   This script checks for FCC self-diffusion and solute-diffusion data.
    *   Output: `data/curated/baselines.csv`, `data/curated/filtered.csv`, `data/curated/data_provenance.json`.

## Running the Pipeline

### 1. Feature Engineering
```bash
python code/processing/feature_engineering.py
```
*   Generates atomic descriptors and baseline shifts.

### 2. Model Training
```bash
# Train Random Forest
python code/models/train_rf.py

# Train Gradient Boosting
python code/models/train_gb.py

# Train Linear Regression
python code/models/train_linear.py
```

### 3. Validation & Sensitivity Analysis
```bash
python code/validation/sensitivity_analysis.py
```
*   Generates `validation/stability_index_report.json` and plots.

## Verification

Run the test suite to ensure all components function correctly:
```bash
pytest tests/ -v
```

## Expected Outputs

*   `data/curated/filtered.csv`: Curated dataset (Solute diffusion).
*   `data/curated/baselines.csv`: Baseline dataset (Self diffusion).
*   `models/final_rf.pkl`, `models/final_gb.pkl`, `models/linear_coef.json`: Trained models.
*   `validation/stability_index_report.json`: Stability analysis results.
*   `plots/`: Generated figures (threshold sensitivity, feature importance).