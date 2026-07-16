# Quickstart Guide: Predicting Rate Constants of SN1 Reactions

This guide provides step-by-step instructions to run the full pipeline for
predicting SN1 reaction rate constants from molecular structure.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- 8GB+ RAM (for full dataset processing)
- CPU-only execution (no GPU required)

## 1. Installation

Clone the repository and install dependencies:

```bash
# Navigate to project root
cd PROJ-373-predicting-rate-constants-of-sn1-reactio

# Install dependencies
pip install -r requirements.txt
```

**Required Dependencies**:
- `rdkit`: Molecular descriptor calculation
- `torch`: Model training (CPU-only)
- `scikit-learn`: Baseline models and metrics
- `shap`: Interpretability analysis
- `pandas`: Data manipulation
- `pyyaml`: Configuration and schema handling
- `datasets`: HuggingFace dataset loading
- `pytest`: Testing framework

## 2. Data Pipeline

The data pipeline ingests public SN1 kinetic datasets, computes molecular
descriptors, and produces a clean, stratified dataset.

### 2.1 Ingest Data

Fetch SN1 kinetic data from HuggingFace:

```bash
python code/data/ingest.py
```

**Output**: `data/raw/sn1_kinetics.csv`

### 2.2 Compute Descriptors

Calculate Gasteiger partial charges and topological indices:

```bash
python code/data/descriptors.py
```

**Output**: Augmented dataset with descriptor columns

### 2.3 Clean and Filter

Canonicalize SMILES and filter out primary alkyl halides:

```bash
python code/data/clean.py
```

**Output**: `data/processed/cleaned_sn1.csv`, `data/processed/exclusion_report.csv`

### 2.4 Split Dataset

Perform stratified split by substrate class:

```bash
python code/data/split.py
```

**Output**: `data/processed/train.csv`, `data/processed/val.csv`, `data/processed/test.csv`

## 3. Model Training

Train a Message Passing Neural Network (MPNN) with hyperparameter optimization.

### 3.1 Train Model

Run random search hyperparameter optimization:

```bash
python code/models/train.py
```

**Output**: `artifacts/hyperparameter_search.log`

### 3.2 Evaluate Model

Calculate R² and MAE, compare with linear baseline:

```bash
python code/models/evaluate.py
```

**Output**: `artifacts/metrics.json`

### 3.3 Save Best Model

Save the best model weights and metrics:

```bash
python code/models/save_artifacts.py
```

**Output**: `artifacts/best_model.pt`, `artifacts/metrics.json`

## 4. Interpretability and Analysis

Generate SHAP values, perform sensitivity analysis, and validate findings.

### 4.1 Interpretability

Generate SHAP rankings and perturbation study:

```bash
python code/analysis/interpret.py
```

**Output**: `artifacts/shap_rankings.json`, `artifacts/perturbation_results.csv`

### 4.2 Sensitivity Analysis

Analyze model sensitivity to descriptor inclusion:

```bash
python code/analysis/sensitivity_runner.py
python code/analysis/sensitivity.py
```

**Output**: `artifacts/sensitivity_report.csv`

### 4.3 Consistency Analysis

Verify stability across random seeds:

```bash
python code/analysis/consistency.py
```

**Output**: `artifacts/shap_consistency_report.md`

### 4.4 Collinearity Diagnostics

Calculate VIF and perform PCA if needed:

```bash
python code/analysis/collinearity.py
```

**Output**: `artifacts/collinearity_report.json`

### 4.5 Generate Reports

Aggregate all analysis results:

```bash
python code/analysis/generate_reports.py
```

**Output**: `artifacts/feature_importance.png`, `artifacts/sensitivity_report.csv`, `artifacts/perturbation_results.csv`

## 5. Expected Outputs

After running the full pipeline, the following artifacts should exist:

### Data Files
- `data/processed/cleaned_sn1.csv`: Cleaned dataset with descriptors
- `data/processed/exclusion_report.csv`: Log of excluded rows
- `data/processed/train.csv`, `val.csv`, `test.csv`: Stratified splits

### Model Artifacts
- `artifacts/best_model.pt`: Trained MPNN weights
- `artifacts/metrics.json`: Model performance metrics (R², MAE)
- `artifacts/hyperparameter_search.log`: Top hyperparameter configurations

### Analysis Reports
- `artifacts/feature_importance.png`: SHAP summary plot
- `artifacts/sensitivity_report.csv`: Sensitivity analysis results
- `artifacts/perturbation_results.csv`: Perturbation study results
- `artifacts/shap_consistency_report.md`: Consistency across seeds
- `artifacts/collinearity_report.json`: VIF and PCA diagnostics

## 6. Validation

Validate that the quickstart instructions match actual execution:

```bash
python code/validation/validate_quickstart.py
```

This script verifies:
- All expected artifacts exist and are non-empty
- `quickstart.md` contains required sections
- Paths in documentation match actual file locations

## 7. Testing

Run the test suite:

```bash
pytest tests/ -v --cov=code
```

Run specific test categories:
- Unit tests: `pytest tests/unit/ -v`
- Integration tests: `pytest tests/integration/ -v`
- Contract tests: `pytest tests/contract/ -v`

## 8. Troubleshooting

### Common Issues

**1. Missing Dependencies**
```bash
pip install -r requirements.txt --upgrade
```

**2. Data Fetch Failures**
Ensure internet connectivity and check HuggingFace dataset availability:
```bash
python -c "from datasets import load_dataset; load_dataset('chemistry/dts-sn1', split='train[:1]')"
```

**3. Out of Memory**
Reduce batch size in `config.py` or use a subset of the data for testing.

**4. CUDA Errors**
This project is CPU-only. Ensure PyTorch is installed without CUDA support:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

## 9. Next Steps

- Review `artifacts/metrics.json` for model performance
- Examine `artifacts/feature_importance.png` for key structural features
- Read `artifacts/shap_consistency_report.md` for stability analysis
- Explore `specs/001-predict-sn1-rate-constants/` for detailed documentation

## 10. References

- Project Specification: `specs/001-predict-sn1-rate-constants/spec.md`
- Implementation Plan: `specs/001-predict-sn1-rate-constants/plan.md`
- Dataset Schema: `specs/001-predict-sn1-rate-constants/contracts/dataset.schema.yaml`
- Model Output Schema: `specs/001-predict-sn1-rate-constants/contracts/model_output.schema.yaml`