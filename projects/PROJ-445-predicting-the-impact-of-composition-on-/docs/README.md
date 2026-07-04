# Chalcogenide Glass Transition Temperature Prediction Pipeline

## Overview
This project implements an automated scientific pipeline to predict the impact of chemical composition on the glass transition temperature (Tg) of chalcogenide glasses. It utilizes real experimental data, computes compositional descriptors, trains machine learning models, and performs rigorous statistical analysis including SHAP-based interpretability.

## Project Structure
```
.
├── code/
│ ├── src/
│ │ ├── data/ # Data download, preprocessing, splitting
│ │ ├── models/ # Model training, evaluation, explainability
│ │ └── utils/ # Constants, metrics, manifest management
│ ├── tests/ # Unit and integration tests
│ └── setup_directories.py # Project initialization script
├── data/
│ ├── raw/ # Downloaded raw dataset
│ ├── processed/ # Processed features and splits
│ └── residualized/ # Residualized features (if collinearity detected)
├── artifacts/ # Final reports and metrics
├── state/ # Execution state, manifests, logs
├── docs/ # Documentation
└── requirements.txt # Python dependencies
```

## Prerequisites
- Python 3.11+
- pip
- Access to the internet (for dataset download)

## Installation

1. Clone the repository and navigate to the project root.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### 1. Initialize Project Structure
Ensure all necessary directories exist:
```bash
python code/setup_directories.py
```

### 2. Download and Preprocess Data
This step fetches the chalcogenide dataset, validates columns, computes descriptors (MCN, electronegativity variance, etc.), and performs the train/test split.
```bash
python code/src/data/download.py
python code/src/data/preprocess.py
python code/src/data/split.py
```
*Note: If any chemical family has fewer than 10 samples, the system automatically switches to Leave-One-Family-Out (LOFO) cross-validation.*

### 3. Train and Evaluate Models
Trains a Linear Regression baseline and a Gradient Boosting Regressor. Handles collinearity detection and mitigation if necessary.
```bash
python code/src/models/train.py
python code/src/models/evaluate.py
```

### 4. Generate SHAP Analysis and Reports
Computes SHAP values, confidence intervals, and generates the final scientific report.
```bash
python code/src/models/explain.py
python code/src/utils/generate_metrics.py
```

### 5. Finalize Manifest
Records all artifact hashes for reproducibility.
```bash
python code/src/utils/manifest_finalizer.py
```

## Output Artifacts
Upon successful execution, the following artifacts will be generated:
- `data/processed/processed_data.csv`: Processed dataset with engineered features.
- `data/splits/`: Train and test split indices.
- `artifacts/performance_metrics.json`: RMSE, R², VIF, MDES, and CI results.
- `artifacts/shap_report.md`: Comprehensive report including feature importance, transferability metrics, and power analysis.
- `state/manifest.json`: Integrity manifest with file hashes.

## Data Dictionary

### Input Data
- **Composition**: Chemical formula string (e.g., "Ge20Se80").
- **Tg**: Glass transition temperature in Kelvin.

### Engineered Features
- **mean_coordination_number (MCN)**: Average coordination number of constituent elements.
- **electronegativity_variance**: Variance of Pauling electronegativity values.
- **atomic_radius_variance**: Variance of atomic radii.
- **chemical_family**: Categorical label derived from chalcogenide system (e.g., Ge-Se, As-S).

### Model Metrics
- **RMSE**: Root Mean Squared Error.
- **R²**: Coefficient of Determination.
- **VIF**: Variance Inflation Factor (for collinearity check).
- **MDES**: Minimum Detectable Effect Size.

## Testing
Run the test suite using pytest:
```bash
pytest code/tests/ -v
```

## License
[Insert License Information]
