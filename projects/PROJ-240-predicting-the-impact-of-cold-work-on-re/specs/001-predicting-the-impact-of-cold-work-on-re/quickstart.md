# Quickstart: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

## Prerequisites

- Python 3.11+
- Git
- (Optional) `conda` or `venv` for environment management.

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline consists of three main stages: Ingestion, Training, and Validation.

### Step 1: Data Ingestion & Validation
This step attempts to download real data from specified sources. If unavailable, it generates a **Noisy Synthetic Dataset** with realistic noise characteristics.

```bash
python code/ingest.py --input data/raw/synthetic_data.csv --output data/processed/validated.csv
```
*Note: If no input file is provided, the script generates a synthetic dataset for demonstration purposes. The generator uses a pinned seed (42) for reproducibility.*

**Output**:
- `data/processed/validated.csv`: Cleaned data.
- `artifacts/reports/validation_report.json`: Log of excluded rows, warnings, and the **source** of the data (Real URL or Synthetic Generator).

### Step 2: Model Training
Trains the Random Forest Regressor and calculates feature importance.

```bash
python code/train.py --input data/processed/validated.csv --output artifacts/models/model.pkl
```

**Output**:
- `artifacts/models/model.pkl`: Trained model.
- `artifacts/reports/feature_importance.json`: Ranked features with confidence intervals.
- `artifacts/reports/collinearity_report.json`: VIF scores for main effects and correlation checks for interactions.

### Step 3: Validation & Sensitivity Analysis
Evaluates the model on the test set and performs **Input Perturbation Sensitivity Analysis**.

```bash
python code/validate.py --model artifacts/models/model.pkl --test data/split/test.csv
```

**Output**:
- `artifacts/reports/metrics.json`: R², MAE, and sensitivity sweep results (±1%, ±5%, ±10% input noise).
- `artifacts/reports/sensitivity_report.csv`: Error rates at different input perturbation levels.

## Testing

Run the test suite to ensure pipeline integrity:

```bash
pytest tests/ -v
```

## Data Note

**Important**: The provided "Verified datasets" block does not contain the specific aluminum alloy recrystallization data required for this study. The `ingest.py` script defaults to **Noisy Synthetic Data generation** to ensure the pipeline runs successfully. For real-world analysis, a specific materials science dataset (e.g., from NIST Materials Data Repository) must be manually placed in `data/raw/` and referenced in the `--input` argument. The synthetic data is designed to simulate experimental noise to prevent tautological validation.