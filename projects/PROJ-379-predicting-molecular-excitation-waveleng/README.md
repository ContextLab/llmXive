# Predicting Molecular Excitation Wavelengths with Graph Neural Networks

This project implements a pipeline to predict molecular excitation wavelengths (λmax) from SMILES strings using Graph Neural Networks (GNNs). It includes data ingestion, preprocessing, model training, evaluation, and feature attribution analysis.

## Project Structure

```
.
├── code/ # Source code for the pipeline
│ ├── ingest.py # Data ingestion and preprocessing
│ ├── validate_data.py # Data validity checks
│ ├── split.py # Scaffold-based data splitting
│ ├── model.py # GNN and baseline model definitions
│ ├── train.py # Model training script
│ ├── evaluate.py # Model evaluation and metrics calculation
│ ├── collinearity_check.py # Collinearity and redundancy analysis
│ ├── explain.py # Feature attribution and explanation
│ ├── sensitivity.py # Sensitivity analysis on decision thresholds
│ ├── analyze_results.py # Aggregation of final results
│ ├── utils.py # Utility functions (RDKit, logging, etc.)
│ ├── models.py # Pydantic data models
│ └──... # Other helper scripts
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed datasets, splits, and results
├── tests/ # Unit and integration tests
├── docs/ # Documentation
└── README.md # This file
```

## Quickstart

### 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Requirements**:
- Python 3.9+
- RDKit
- PyTorch (CPU version)
- PyTorch Geometric
- Pandas, Scikit-learn, NumPy

### 2. Data Ingestion and Preprocessing

Run the ingestion pipeline to fetch UV-Vis data, parse SMILES, and generate scaffold splits:

```bash
python code/ingest.py
python code/validate_data.py
python code/split.py
```

**Outputs**:
- `data/raw/processed.csv`: Cleaned molecule data
- `data/processed/splits/`: Train, validation, and test CSV files

### 3. Model Training

Train the MPNN GNN and baseline models:

```bash
python code/train.py
```

**Outputs**:
- `data/processed/model.pt`: Trained GNN model weights
- `state/projects/PROJ-379-predicting-molecular-excitation-waveleng.yaml`: Versioned artifact hashes

### 4. Evaluation

Evaluate model performance and compute metrics:

```bash
python code/evaluate.py
```

**Outputs**:
- `data/processed/metrics.json`: Contains `mae`, `r2`, `wilcoxon_p_value`, `sc001_status`, and power analysis results.

**Interpreting `metrics.json`**:
- `mae`: Mean Absolute Error in nanometers (nm). Lower is better.
- `r2`: Coefficient of determination. Closer to 1.0 is better.
- `wilcoxon_p_value`: P-value from the Wilcoxon signed-rank test comparing GNN vs. baseline.
- `sc001_status`: "PASS" if `p < 0.05` AND `MAE < 30`; otherwise "FAIL".
- `power_status`: Result of the power analysis (n≥50 constraint).

### 5. Feature Attribution and Sensitivity Analysis

Analyze feature importance and perform sensitivity sweeps:

```bash
python code/collinearity_check.py
python code/explain.py
python code/sensitivity.py
python code/analyze_results.py
```

**Outputs**:
- `data/processed/redundancy_masks.json`: Masks for redundant features
- `data/processed/attribution_results.json`: Feature attribution weights
- `data/processed/metrics.json`: Updated with collinearity flags, redundancy masks, and power status

### 6. Full Pipeline Validation

Run the end-to-end validation script to verify all artifacts:

```bash
python code/run_quickstart_validation.py
```

This script executes all steps above and verifies that expected output files are generated correctly.

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

## Configuration

- **CPU-Only**: All scripts are configured to run on CPU.
- **Random Seeds**: Fixed seeds are used for reproducibility.
- **Logging**: Logs are written to `logs/` directory with timestamps.

## License

[Insert License Information Here]