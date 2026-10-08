# Quickstart: Predicting Yield Strength of BCC Alloys

## Prerequisites

- Python 3.11+
- `pip`
- Access to a GitHub Actions runner (for CI) or local Linux environment.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-525-predicting-the-yield-strength-of-bcc-all
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Dependencies include: `pandas`, `numpy`, `scikit-learn`, `scipy`, `periodictable`, `requests`, `pyyaml`, `pymatgen`.*

## Running the Pipeline

1. **Initialize directories**:
   ```bash
   mkdir -p data/raw data/processed data/logs reports
   ```

2. **Run the full pipeline**:
   ```bash
   python code/main.py
   ```
   This script executes:
   - Data download and filtering (FR-001, FR-002)
   - Yield Definition Verification (Halt if invalid)
   - Data Scarcity Check (Halt if N < 80)
   - Feature Engineering (ILR + Scalars, inside CV)
   - Model training and validation (FR-005, FR-006)
   - Report generation (SC-002, SC-003, SC-004)

3. **Check logs**:
   - `data/logs/pipeline_runtime.log`: Runtime metrics.
   - `data/logs/rejected_entries.log`: Entries excluded during filtering.

## Expected Outputs

- `data/processed/features_engineered.csv`: Final dataset with descriptors.
- `reports/results.json`: Model performance metrics (R², MAE, RMSE, CI, Feature Stability, Practical Utility).
- `data/processed/models/`: Trained model artifacts.

## Troubleshooting

- **Data Scarcity Error**: If the log shows "DATA_SCARCITY: Insufficient BCC alloys (N < 80)", the dataset does not meet the minimum sample size. The pipeline has halted as per spec.
- **Yield Definition Error**: If the log shows "YIELD_DEFINITION_INVALID: Source data lacks standard yield strength definition", the raw data does not specify the yield strength method (e.g., [deferred] offset). The pipeline has halted to ensure construct validity.
- **Data Unavailable**: If the log shows "DATA_UNAVAILABLE: MPEA requires access credentials", the MPEA database is not accessible. No fallback is available.
- **Complementarity Failure**: If the log shows "COMPLEMENTARITY_FAILURE: Feature selection removed all ILR or all Scalar features", the feature selection step violated FR-003.1. The pipeline has halted.
- **Missing Element**: If a specific element is not found in the periodic table reference, check the raw data for typos.
- **Memory Error**: If OOM occurs, ensure the dataset is streamed or sampled. The pipeline is designed for < 7 GB RAM.