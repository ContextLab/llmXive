# Predicting the Impact of Alloying on Creep Resistance

Automated science pipeline for predicting creep resistance in alloys using public data, thermodynamic descriptors, and machine learning.

## Prerequisites

- Python 3.11+
- pip (package installer)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-137-predicting-the-impact-of-alloying-on-cre
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Quickstart

### 1. Data Acquisition and Preprocessing (User Story 1)

Run the full data pipeline to download (if available) or generate synthetic data, merge with thermodynamic descriptors, and output a validated CSV:

```bash
python src/data/pipeline.py
```

**Output**: `data/processed/alloy_dataset.csv`

This script:
- Attempts to fetch NIMS data (if configured).
- Falls back to synthetic data generation using Arrhenius/Power-law laws if external sources fail.
- Computes thermodynamic descriptors (mixing enthalpy, radius mismatch) via Materials Project.
- Validates output against `contracts/dataset.schema.yaml`.
- Logs exclusion counts and physics consistency checks.

### 2. Model Training and Evaluation (User Story 2)

Train and compare Gradient Boosting models (Thermodynamic vs. Composition-Only) using Nested Cross-Validation and statistical significance testing:

```bash
python src/models/main_eval.py
```

**Output**:
- Model performance metrics (R², RMSE) logged to console.
- Statistical test results (Permutation Test p-value, Bootstrap CI) printed to stdout.
- Detailed logs saved to `logs/model_evaluation.log`.

### 3. Feature Importance and Reporting (User Story 3)

Generate SHAP plots and interpretability reports:

```bash
python src/models/interpret.py
```

**Output**:
- SHAP summary plot: `data/outputs/shap_summary.png`
- Feature importance report: `docs/reports/feature_importance.md`

### 4. Full Pipeline Execution

To run the entire pipeline end-to-end (Data → Modeling → Reporting):

```bash
python tests/integration/test_runtime.py
```

This script measures total execution time and logs it to `logs/runtime.log`.

## Project Structure

```
.
├── config/ # Configuration files (settings, parameters)
├── contracts/ # Data and output schema definitions
├── data/ # Raw and processed datasets
│ └── outputs/ # Generated plots and intermediate results
├── docs/ # Documentation and reports
│ └── reports/ # Final generated reports
├── logs/ # Execution logs
├── src/ # Source code
│ ├── data/ # Data acquisition and preprocessing
│ ├── models/ # Model training, evaluation, and interpretation
│ ├── reports/ # Report generation
│ └── utils/ # Utilities (logging, hashing, validation)
├── tests/ # Test suites
│ ├── contract/ # Schema and physics consistency tests
│ ├── integration/ # End-to-end pipeline tests
│ └── unit/ # Unit tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Configuration

Edit `config/settings.yaml` to set:
- `nims_url`: URL for NIMS data fetch (optional).
- `mp_api_key`: Materials Project API key (optional, required for real thermodynamic data).
- `random_seed`: Seed for reproducibility.

## Testing

Run all tests:

```bash
pytest tests/
```

Run specific test suites:
- Unit tests: `pytest tests/unit/`
- Contract tests: `pytest tests/contract/`
- Integration tests: `pytest tests/integration/`

## License

[Insert License Information]