# PROJ-209: Quantifying the Influence of Topological Defects on 2D Material Properties

## Project Overview

This project investigates how topological defects (vacancies, grain boundaries, adatoms) affect the physical properties of 2D materials, specifically graphene and molybdenum disulfide (MoS₂). We combine real experimental data (where available) with physics-based synthetic data generation to train machine learning models that predict the impact of defects on:
- Electrical conductivity
- Young's modulus (stiffness)
- Fracture strength

The workflow integrates data acquisition from the Materials Project API, synthetic data generation using continuum mechanics principles, Random Forest regression modeling, permutation-based inference, and comprehensive validation.

## Key Features

- **Data Acquisition**: Fetches pristine structures from Materials Project; attempts to download the 2022 Supplementary Defect Dataset; falls back to physics-based synthetic generation if real data is unavailable.
- **Synthetic Data Generation**: Implements analytical continuum mechanics models (Griffith criterion, Rule of Mixtures, Matthiessen's rule) and Gaussian GP surrogates for hold-out sets.
- **Statistical Modeling**: Trains Random Forest regressors with 5-fold cross-validation, handles collinearity via Ridge regression, and performs permutation testing with Benjamini-Hochberg FDR control.
- **Validation & Sensitivity**: Conducts permutation importance stability analysis, sensitivity analysis on decision thresholds, and generates comprehensive validation reports.
- **Reproducibility**: Fully reproducible via Jupyter notebook and CI validation scripts with runtime/memory constraints.

## Directory Structure

```
PROJ-209-quantifying-the-influence-of-topological/
├── code/ # Core implementation
│ ├── 01_data_acquisition.py # Data download & synthetic generation
│ ├── 02_data_processing.py # Feature extraction & normalization
│ ├── 03_modeling.py # Random Forest training & collinearity handling
│ ├── 04_inference.py # Permutation importance & FDR control
│ ├── 05_validation.py # Validation analysis & sensitivity reports
│ ├── infrastructure/
│ │ └── error_handler.py # Retry logic with exponential backoff
│ └── generators/
│ └── synthetic_data_generator.py # Physics-based data generation
├── data/
│ ├── raw/ # Raw downloaded/generated data
│ │ ├── pristine_structures.csv
│ │ ├── defect_dataset_2022.csv (if available)
│ │ ├── synthetic_train.csv
│ │ ├── synthetic_holdout.csv
│ │ └── synthetic_defect_fallback.csv
│ ├── processed/ # Processed features & targets
│ │ ├── features.csv
│ │ ├── targets.csv
│ │ └── feature_selection_log.json
│ ├── validation/
│ │ └── external/ # External validation datasets
│ └── state/ # Checksums & version tracking
├── notebooks/
│ └── 01_full_workflow.ipynb # End-to-end reproducible workflow
├── scripts/
│ ├── update_state_hashes.py # Checksum tracking
│ └── run_ci_validation.sh # CI validation script
├── tests/ # Unit & integration tests
├── docs/ # Documentation
│ ├── README.md # This file
│ └── API.md # API documentation
└── specs/ # Feature specifications
 └── 001-quantify-defect-influence/
```

## Prerequisites

- Python 3.8+
- pip and virtual environment support
- Internet access for Materials Project API (optional; synthetic fallback available)
- System with at least 8GB RAM recommended for model training

## Setup Instructions

### 1. Clone and Initialize

```bash
git clone <repository-url>
cd PROJ-209-quantifying-the-influence-of-topological
python code/init_project_structure.py
```

### 2. Create Virtual Environment and Install Dependencies

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root (or set environment variables):

```bash
# Materials Project API key (optional; synthetic fallback available)
MP_API_KEY=your_api_key_here

# Random seed for reproducibility
RANDOM_SEED=42

# Output paths (optional; defaults used if not set)
DATA_RAW_PATH=data/raw
DATA_PROCESSED_PATH=data/processed
```

### 4. Run the Full Workflow

Execute the complete pipeline:

```bash
python code/01_data_acquisition.py
python code/02_data_processing.py
python code/03_modeling.py
python code/04_inference.py
python code/05_validation.py
```

Or run the Jupyter notebook for an interactive experience:

```bash
jupyter notebook notebooks/01_full_workflow.ipynb
```

### 5. CI Validation (Optional)

Run the validation script to ensure reproducibility within constraints:

```bash
bash scripts/run_ci_validation.sh
```

## Data Sources

- **Materials Project**: REST API for pristine graphene and MoS₂ structures.
- **2022 Supplementary Defect Dataset**: Attempted download; synthetic fallback if unavailable.
- **Synthetic Data**: Generated using analytical continuum mechanics models when real data is missing.

## Model Details

- **Algorithms**: Random Forest Regressors (3 models for conductivity, Young's modulus, fracture strength)
- **Validation**: 5-fold cross-validation with R² and MAPE metrics
- **Collinearity Handling**: Ridge regression with VIF-based feature selection fallback
- **Inference**: Permutation importance with Benjamini-Hochberg FDR control (q ≤ 0.05)
- **Sensitivity Analysis**: Threshold sweeps with FPR/FNR reporting

## Output Artifacts

After successful execution:

- `data/raw/pristine_structures.csv`: Downloaded pristine structures
- `data/raw/synthetic_train.csv`: Training data (real or synthetic)
- `data/processed/features.csv`: Processed feature matrix
- `data/processed/targets.csv`: Normalized target variables
- `data/processed/model_*.pkl`: Trained Random Forest models
- `data/validation/Validation_Report.json`: Validation status and metrics
- `state/projects/PROJ-209-...yaml`: Checksums and version tracking

## Known Limitations

- If external validation data (`exp_defect_graphene_mos2_v1`) is not present, validation reports will be marked as `SYNTHETIC_FALLBACK` or `NO_EXTERNAL_DATA`.
- Synthetic data claims are restricted to "Method Validation" scope per project specifications.
- Runtime constrained to 6 hours on CPU-only CI; memory limited to 7GB.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes following the task-based workflow in `tasks.md`
4. Ensure all tests pass
5. Submit a pull request

## License

[Insert License Information]

## Contact

For questions or issues, please open an issue in the repository or contact the project maintainers.