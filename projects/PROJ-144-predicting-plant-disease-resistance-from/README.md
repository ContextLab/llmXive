# Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

**Project ID**: PROJ-144
**Description**: This project implements a machine learning pipeline to predict plant disease resistance using publicly available metabolomic data from the Metabolomics Workbench. The pipeline includes data acquisition, preprocessing, model training, validation, and biological interpretation.

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Access to the Metabolomics Workbench API

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-144-predicting-plant-disease-resistance-from
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Install pre-commit hooks** (optional but recommended):
 ```bash
 pre-commit install
 ```

## Project Structure

```
.
├── code/ # Source code
│ ├── data/ # Data acquisition and preprocessing
│ ├── modeling/ # Model training, evaluation, and interpretation
│ ├── research/ # Research utilities and validation
│ ├── utils/ # Utility functions
│ └── setup_*.py # Project setup scripts
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed data artifacts
├── results/ # Model results and reports
├── state/ # State tracking (artifact hashes, etc.)
├── tests/ # Unit and integration tests
├── contracts/ # Data and output schemas
├── specs/ # Feature specifications
├── README.md # This file
├── requirements.txt # Python dependencies
├── quickstart.md # Quick start guide
└──.pre-commit-config.yaml # Pre-commit configuration
```

## Quick Start

See [quickstart.md](quickstart.md) for a step-by-step guide to running the full pipeline.

## Execution Instructions

The pipeline is executed in phases. Follow the order below to ensure all dependencies are met.

### Phase 0: Data Acquisition & Verification

Identify and verify public datasets with specific Study IDs.

```bash
python code/research/verify_studies.py
```

This will update `research.md` with specific Metabolomics Workbench Study IDs.

### Phase 1: Setup

Initialize the project structure and dependencies (should already be done if following installation steps).

```bash
python code/setup_project_structure.py
python code/setup_linting.py
```

### Phase 2: Foundational

Set up contracts and validation schemas.

```bash
python code/research/validate_schema.py
```

### Phase 3: User Story 1 - Data Acquisition and Preprocessing

Download, normalize, align, and harmonize public metabolomics datasets.

```bash
# Validate temporal consistency
python code/data/validate_temporal.py

# Preprocess data (download, normalize, batch correct)
python code/data/run_preprocess.py
```

This generates:
- `data/processed/batch_corrected_matrix.csv`
- `data/processed/labels.csv`

### Phase 4: User Story 2 - Model Training and Validation

Train a Random Forest classifier with rigorous validation.

```bash
# Train the model
python code/modeling/train.py

# Evaluate model and perform correlation analysis
python code/modeling/evaluate.py

# Run collinearity diagnostics
python code/modeling/collinearity.py

# Generate final metrics and reports
python code/modeling/generate_final_metrics.py
python code/modeling/generate_associational_report.py
```

This generates:
- `results/metrics.json`
- `results/shap_analysis.json`

### Phase 5: User Story 3 - Biological Interpretation

Map top metabolites to biological pathways.

```bash
# Interpret model and map pathways
python code/modeling/interpret.py

# Save pathway results
python code/modeling/save_pathway_results.py

# Visualize pathway importance
python code/modeling/visualize_pathways.py
```

This generates:
- `results/pathway_analysis.json`
- `results/pathway_barplot.png`

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

## Configuration

Key configuration parameters are defined in `code/utils/constants.py`:

- `RANDOM_STATE`: Random seed for reproducibility (default: 42)
- `HOLD_OUT_FRACTION`: Fraction of data for hold-out set (default: 0.20)
- `HYPOTHESIS_THRESHOLD`: Minimum balanced accuracy for hypothesis validation (default: 0.75)

## Output Artifacts

The pipeline produces the following key artifacts:

### Data Artifacts
- `data/processed/batch_corrected_matrix.csv`: Preprocessed metabolite matrix
- `data/processed/labels.csv`: Harmonized resistance labels
- `data/processed/split_indices.json`: Train/hold-out split indices

### Model Artifacts
- `results/metrics.json`: Model performance metrics (balanced accuracy, ROC-AUC, p-values)
- `results/shap_analysis.json`: SHAP values and feature importance
- `results/pathway_analysis.json`: Pathway mapping results

### Visualization Artifacts
- `results/pathway_barplot.png`: Visualization of pathway importance

### State Artifacts
- `state/artifact_hashes.yaml`: Checksums of all data and model artifacts

## Dependencies

See `requirements.txt` for the complete list of dependencies. Key packages include:

- `pandas`, `numpy`: Data manipulation
- `scikit-learn`: Machine learning (Random Forest, preprocessing)
- `statsmodels`: Statistical analysis (VIF, correlation)
- `shap`: Model interpretability
- `matplotlib`, `seaborn`: Visualization
- `requests`: API calls to Metabolomics Workbench

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

[Insert License Information Here]

## Contact

For questions or issues, please open an issue in the repository.
