# Quickstart Guide: Predicting SN1 Rate Constants

This guide walks you through setting up the environment, running the full data pipeline, training the model, and generating interpretability reports.

## Prerequisites

- Python 3.11+
- `pip` (Python package installer)
- Access to the HuggingFace dataset `chemistry/dts-sn1` (for real data ingestion)

## 1. Setup Environment

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd PROJ-373-predicting-rate-constants-of-sn1-reactio
pip install -r requirements.txt
```

Ensure the following tools are available for linting and testing (optional but recommended):
- `ruff` (or `flake8`)
- `black`
- `pytest`

## 2. Directory Structure

The project uses the following structure:

```
.
├── code/ # Source code
│ ├── config.py # Hyperparameters and paths
│ ├── utils/ # Logging, checksum utilities
│ ├── data/ # Ingestion, cleaning, descriptors, splitting
│ ├── models/ # MPNN architecture, training, evaluation
│ ├── analysis/ # SHAP, sensitivity, collinearity, power analysis
│ └── main.py # Orchestration script
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Cleaned and split datasets
├── artifacts/ # Model weights, metrics, reports
├── specs/ # Design documents and schemas
└── tests/ # Unit and integration tests
```

## 3. Run the Data Pipeline (User Story 1)

The data pipeline ingests real SN1 kinetic data, cleans SMILES, computes descriptors, and splits the dataset.

**Step 3.1: Ingest Data**

Fetches data from the HuggingFace dataset `chemistry/dts-sn1`.

```bash
python code/data/ingest.py
```

*Output*: `data/raw/sn1_raw.csv`, `data/processed/exclusion_report.csv`

**Step 3.2: Clean and Filter**

Canonicalizes SMILES and removes primary alkyl halides.

```bash
python code/data/clean.py
```

*Output*: `data/processed/cleaned_sn1.csv` (intermediate)

**Step 3.3: Compute Descriptors**

Calculates Gasteiger charges and topological indices using RDKit.

```bash
python code/data/descriptors.py
```

*Output*: `data/processed/descriptors_added.csv`

**Step 3.4: Split Dataset**

Performs a stratified split by substrate class.

```bash
python code/data/split.py
```

*Output*: `data/processed/train.csv`, `data/processed/val.csv`, `data/processed/test.csv`

**Step 3.5: Finalize Dataset**

Combines splits and saves checksums.

```bash
python code/data/finalize_dataset.py
```

*Output*: `data/processed/cleaned_sn1.csv` (final), `data/processed/cleaned_sn1.csv.sha256`

## 4. Train the Model (User Story 2)

Trains a Message Passing Neural Network (MPNN) with hyperparameter optimization.

**Step 4.1: Train with Hyperparameter Search**

Runs random search over up to 50 configurations.

```bash
python code/models/train.py
```

*Output*: `artifacts/best_model.pt`, `artifacts/hyperparameter_search.log`

**Step 4.2: Evaluate Model**

Compares MPNN against a linear regression baseline using bootstrap.

```bash
python code/models/evaluate.py
```

*Output*: `artifacts/metrics.json`

**Step 4.3: Save Artifacts**

Consolidates best model and logs.

```bash
python code/models/save_artifacts.py
```

*Output*: `artifacts/best_model.pt`, `artifacts/metrics.json`, `artifacts/hyperparameter_search.log`

## 5. Interpretability and Analysis (User Story 3)

Generates SHAP values, sensitivity reports, and perturbation studies.

**Step 5.1: Run Interpretability Analysis**

Computes SHAP values and performs perturbation studies.

```bash
python code/analysis/interpret.py
```

*Output*: `artifacts/feature_importance.png`, `artifacts/perturbation_results.csv`

**Step 5.2: Sensitivity Analysis**

Sweeps descriptor cutoffs to assess robustness.

```bash
python code/analysis/sensitivity.py
```

*Output*: `artifacts/sensitivity_report.csv`

**Step 5.3: Collinearity Diagnostics**

Calculates VIF and performs PCA if needed.

```bash
python code/analysis/collinearity.py
```

*Output*: `artifacts/collinearity_report.csv`

**Step 5.4: Power Analysis**

Calculates Minimum Detectable Effect (MDE) and sample size requirements.

```bash
python code/analysis/power.py
```

*Output*: `artifacts/power_analysis_report.csv`

**Step 5.5: Generate Final Reports**

Consolidates all analysis outputs.

```bash
python code/analysis/generate_reports.py
```

*Output*: `artifacts/feature_importance.png`, `artifacts/sensitivity_report.csv`, `artifacts/perturbation_results.csv`

## 6. Running Tests

Run the full test suite to verify correctness:

```bash
pytest tests/
```

Specific test categories:
- **Contract Tests**: `tests/contract/` (validates YAML schemas)
- **Unit Tests**: `tests/unit/` (individual function logic)
- **Integration Tests**: `tests/integration/` (end-to-end flows)

## 7. Full Pipeline Execution

To run the entire pipeline from ingestion to analysis:

```bash
python code/main.py --stage all
```

This will sequentially execute all stages defined in `code/main.py`.

## Troubleshooting

- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed.
- **Data Fetch Failures**: If the HuggingFace dataset is unreachable, check your internet connection or network proxy settings. The script will fail loudly without synthetic fallbacks.
- **Memory Errors**: For large datasets, ensure sufficient RAM or use the streaming option in `code/data/ingest.py` if implemented.
- **CUDA Errors**: This project is CPU-only. If you see CUDA errors, ensure `torch` is installed with CPU support only (`torch-cpu`).

## Configuration

Edit `code/config.py` to modify:
- Random seeds
- File paths
- Hyperparameter search ranges
- Data split ratios

## Contributing

When adding new features:
1. Update `tasks.md` with new tasks.
2. Write unit tests first (TDD).
3. Ensure new data artifacts follow the schemas in `specs/001-predict-sn1-rate-constants/contracts/`.