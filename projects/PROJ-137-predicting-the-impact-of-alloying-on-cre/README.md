# Predicting the Impact of Alloying on Creep Resistance via Public Data

This project implements an automated science pipeline to predict creep resistance in alloys using public datasets (NIMS, Materials Project) and machine learning. It compares thermodynamic-feature models against composition-only models using rigorous nested cross-validation and statistical significance testing.

## Project Structure

```
.
├── config/ # Configuration files (settings, synthetic params)
├── contracts/ # Data and output schema definitions
├── data/ # Generated datasets and outputs
├── docs/ # Documentation and reports
├── logs/ # Runtime and execution logs
├── src/ # Source code
│ ├── data/ # Data acquisition and preprocessing
│ ├── models/ # Model training, evaluation, and interpretation
│ ├── reports/ # Report generation
│ └── utils/ # Logging, hashing, validation utilities
├── tests/ # Unit, integration, and contract tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd predicting-impact-of-alloying-on-creep-resistance
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

4. (Optional) Configure API keys:
 - Set `MP_API_KEY` in `config/settings.yaml` for Materials Project access.
 - Set `NIMS_API_KEY` if using NIMS data (if available).

## Quickstart

### 1. Run the Data Pipeline

Generates synthetic data (default) or fetches real data if configured, preprocesses it, and outputs a validated CSV.

```bash
python src/data/pipeline.py
```

**Output**: `data/processed/alloy_dataset.csv`

### 2. Train and Evaluate Models

Trains two Gradient Boosting models (Thermodynamic vs. Composition-Only) and performs statistical significance testing (Permutation Test or Bootstrap).

```bash
python src/models/main_eval.py
```

**Output**:
- `logs/model_comparison.log`: Detailed metrics and p-values.
- `data/outputs/model_report.json`: Structured performance data.

### 3. Interpret Model Features (SHAP)

Generates SHAP summary plots and ranks feature importance.

```bash
python src/models/interpret.py
```

**Output**: `data/outputs/shap_summary.png`

### 4. Generate Final Report

Compiles all results into a human-readable report.

```bash
python src/reports/generate_report.py
```

**Output**: `docs/reports/final_report.md`

## Running Tests

Run the full test suite:

```bash
pytest tests/ -v
```

Run specific test categories:

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Contract tests
pytest tests/contract/ -v
```

## Configuration

- **`config/settings.yaml`**: General settings, random seeds, API keys, and paths.
- **`config/synthetic_params.yaml`**: Parameters for synthetic data generation (Arrhenius/Power-law constants).

## License

MIT License. See `LICENSE` for details.