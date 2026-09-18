# Predicting the Impact of Alloying on Creep Resistance via Public Data

**Project ID**: PROJ-137
**Status**: Research Pipeline Implementation

## Overview

This project implements an automated scientific pipeline to predict the impact of alloying elements on creep resistance. It ingests alloy composition and experimental creep data, computes thermodynamic descriptors (mixing enthalpy, radius mismatch), and trains Gradient Boosting models to compare composition-only features against thermodynamic-enhanced features.

The pipeline includes:
1. **Data Acquisition**: Fetches real data from NIMS (if available) or generates synthetic data adhering to Arrhenius/Power-law physical laws.
2. **Preprocessing**: Normalizes compositions, calculates descriptors, and validates against strict schema contracts.
3. **Modeling**: Trains and evaluates models using Nested Cross-Validation with statistical significance testing (Permutation Test/Bootstrap).
4. **Interpretability**: Generates SHAP analysis to rank feature importance.

## Prerequisites

- Python 3.11+
- pip
- (Optional) Materials Project API Key (for real thermodynamic data)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-137-predicting-the-impact-of-alloying-on-cre
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. (Optional) Configure API keys in `config/settings.yaml` if using real Materials Project data.

## Quickstart

Execute the full research pipeline from data generation to final reporting.

### Run the Data Pipeline (US1)
Generates or fetches data, preprocesses it, and outputs a validated CSV.
```bash
python src/data/pipeline.py
```
*Output*: `data/processed/alloy_creep_dataset.csv`

### Run Model Training & Evaluation (US2)
Trains Composition-Only and Thermodynamic models, performs Nested CV, and runs statistical tests.
```bash
python src/models/main_eval.py
```
*Output*: `logs/model_metrics.log`, `data/outputs/model_comparison.json`

### Run Interpretability Analysis (US3)
Generates SHAP plots and feature importance reports.
```bash
python src/models/interpret.py
```
*Output*: `data/outputs/shap_summary.png`, `docs/reports/feature_importance_report.md`

### Run Full End-to-End Pipeline
Executes all stages sequentially and logs total runtime.
```bash
python tests/integration/test_runtime.py
```
*Output*: `logs/runtime.log` (contains measured duration), final consolidated report in `docs/reports/`.

## Project Structure

```text
.
├── config/ # Configuration files (settings, params)
├── contracts/ # Schema definitions for data validation
├── data/ # Data artifacts (raw, processed, outputs)
│ └── outputs/ # Generated plots and JSON reports
├── docs/ # Documentation and final reports
├── logs/ # Execution logs and runtime metrics
├── src/ # Source code
│ ├── data/ # Data acquisition and preprocessing
│ ├── models/ # Training, evaluation, and interpretation
│ ├── reports/ # Report generation
│ └── utils/ # Logging, hashing, validation utilities
├── tests/ # Test suite (unit, integration, contract)
├──.gitignore
├── pyproject.toml # Project metadata and tool config
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Configuration

- **`config/settings.yaml`**: Define random seeds, file paths, and API keys.
- **`config/synthetic_params.yaml`**: Parameters for synthetic data generation (Arrhenius/Power-law constants).

## Testing

Run the test suite using pytest:
```bash
pytest tests/ -v
```

Specific test categories:
- **Unit Tests**: `pytest tests/unit/`
- **Integration Tests**: `pytest tests/integration/`
- **Contract Tests**: `pytest tests/contract/`

## License

This project is part of the llmXive automated science pipeline.
See LICENSE for details.