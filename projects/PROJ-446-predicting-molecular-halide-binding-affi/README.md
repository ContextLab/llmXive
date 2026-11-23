# Predicting Molecular Halide Binding Affinities with Machine Learning

**Project ID**: PROJ-446-predicting-molecular-halide-binding-affi

## Project Goal

This project implements an automated scientific pipeline to predict molecular halide binding affinities using machine learning. The primary objective is to analyze experimental data from NIST and PubChem to determine how host molecular properties (such as charge density and cavity volume) influence binding constants (log K) for different halides (F⁻, Cl⁻, Br⁻, I⁻).

If real-world data is insufficient (fewer than 50 unique hosts with multi-halide measurements), the pipeline automatically switches to a "Simulated Mode" to generate synthetic data for method validation, while explicitly aborting comparative analysis and documenting the limitation.

## Key Features

- **Data Ingestion**: Scrapes and cleans experimental data from NIST/PubChem.
- **Feature Engineering**: Generates ECFP fingerprints and RDKit descriptors (charge density, cavity volume).
- **Model Training**: Trains Random Forest and Gradient Boosting models with host-identity stratified splitting to prevent data leakage.
- **Physical Plausibility Checks**: Validates model coefficients against Coulombic attraction principles.
- **Statistical Reporting**: Generates bootstrap confidence intervals and final associational reports.
- **Resource Constraints**: Enforces CPU-only execution with RAM and time limits.

## Dependencies

The project requires Python 3.11+ and the following libraries:

- `scikit-learn>=1.4.0`
- `rdkit`
- `pandas`
- `numpy`
- `requests`
- `beautifulsoup4`
- `pyyaml`
- `pytest`

Install all dependencies using:

```bash
pip install -r code/requirements.txt
```

## Project Structure

```text
projects/PROJ-446-predicting-molecular-halide-binding-affi/
├── code/
│ ├── 01_data_ingestion.py # Data scraping, cleaning, and simulation logic
│ ├── 02_feature_engineering.py # Descriptor generation
│ ├── 03_model_training.py # Model training and resource monitoring
│ ├── 04_feature_analysis.py # Stability analysis and physical checks
│ ├── 05_statistical_reporting.py # Power analysis and reporting
│ ├── utils/ # Configuration, logging, validation utilities
│ └──...
├── data/
│ ├── raw/ # Downloaded and cleaned raw data
│ ├── processed/ # Final datasets, models, and metrics
│ └── simulated/ # State and synthetic data (if triggered)
├── docs/
│ ├── paper/ # Final report and figures
│ └── quickstart.md
├── state.yaml # Artifact tracking
└── README.md
```

## How to Run the Pipeline

The pipeline is designed to run sequentially through its phases. Ensure you are in the project root directory.

### 1. Setup and Initialization

Ensure the project root and necessary directories exist:

```bash
python code/00_create_project_root.py
python code/00_create_data_dirs.py
python code/00_create_state.py
```

### 2. Data Ingestion and Preprocessing (User Story 1)

Run the data pipeline to download, clean, and filter data. This step will automatically detect if real data is sufficient or switch to simulated mode.

```bash
python code/01_data_ingestion.py
```

*Output*: `data/processed/halide_binding_data.csv`

### 3. Feature Engineering (User Story 1)

Generate molecular descriptors and fingerprints.

```bash
python code/02_feature_engineering.py
```

*Output*: Updates to `data/raw/descriptors_added.csv`

### 4. Model Training (User Story 2)

Train Random Forest and Gradient Boosting models with resource monitoring.

```bash
python code/03_model_training.py
```

*Output*: `data/processed/models/*.pkl`, `data/processed/metrics/*.json`, `data/processed/model_runs.json`

### 5. Feature Analysis (User Story 3)

Perform stability analysis and physical plausibility checks.

```bash
python code/04_feature_analysis.py
```

*Output*: `data/processed/feature_analysis.json`, `docs/paper/figures/`

### 6. Statistical Reporting (User Story 4)

Generate the final statistical summary and report.

```bash
python code/05_statistical_reporting.py
python code/06_generate_final_report.py
```

*Output*: `docs/paper/report.md`, `data/processed/statistical_summary.json`

### 7. Validation

Verify the pipeline execution and artifacts.

```bash
python code/07_validate_quickstart.py
python code/08_update_state_hashes.py
```

## Running Individual Scripts

Each script in the `code/` directory can be run independently as shown above. They are designed to handle their specific dependencies and file I/O paths relative to the project root.

## Testing

Run the test suite using pytest:

```bash
pytest tests/
```

## Notes

- **Simulated Mode**: If the dataset contains fewer than 50 unique hosts with multi-halide measurements, the pipeline will automatically generate synthetic data and abort comparative analysis, logging a warning.
- **Resource Limits**: Model training scripts enforce a 7GB RAM limit and a 6-hour runtime limit. If exceeded, the process will terminate and log a failure report.
- **Data Privacy**: All data processing is local. No external APIs are called for model inference.