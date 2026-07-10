# Quickstart: Quantifying the Effect of Alloying Elements on the Glass-Forming Ability of Metallic Glasses

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or a local environment with sufficient RAM to support the workflow.

## Installation

1. **Clone the repository** (or navigate to the project directory).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note*: `requirements.txt` pins versions for `pymatgen`, `scikit-learn`, `pandas`, `numpy`, `shap`, `statsmodels`.

## Running the Pipeline

### Option 1: Full Pipeline (Recommended)
Run the orchestration script to download, process, train, and screen:
```bash
python code/main.py
```
This will:
1. Download data from HuggingFace.
2. Engineer features.
3. Train models (RF, GB) and select the best one.
4. Perform residual analysis and retrain if needed.
5. Screen ternary combinations.
6. Output `output/candidates.csv` and `output/verification_requests.json`.

### Option 2: Step-by-Step

**Step 1: Download Data**
```bash
python code/data/download.py
```

**Step 2: Feature Engineering**
```bash
python code/data/features.py
```

**Step 3: Train Models**
```bash
python code/models/train.py
```

**Step 4: Screen Candidates**
```bash
python code/models/predict.py
```

## Expected Outputs

- `data/raw/`: Raw CSVs (checksummed).
- `data/processed/features.csv`: Feature-engineered dataset.
- `output/best_model.pkl`: The selected regression model.
- `output/shap_feature_importance.json`: Global feature importance.
- `output/candidates.csv`: Top 10 novel alloy candidates.
- `output/verification_requests.json`: JSON for experimental validation.

## Troubleshooting

- **Missing `log10_Rc`**: The pipeline will fail with an explicit error. Verify the dataset schema.
- **Unknown Elements**: Rows with unknown elements are skipped. Check logs for warnings.
- **Memory Error**: Unlikely on this dataset. If it occurs, reduce the number of bootstrapped models (configurable).
- **No Candidates**: If no compositions fall below the threshold, `candidates.csv` will be empty (header only).

## Verification

Run the test suite to ensure correctness:
```bash
pytest tests/
```
This includes contract tests against the YAML schemas defined in `contracts/`.
