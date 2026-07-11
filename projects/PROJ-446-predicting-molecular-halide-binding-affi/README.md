# Predicting Molecular Halide Binding Affinities with Machine Learning

**Project ID**: PROJ-446

## Project Goal

This project aims to predict molecular halide binding affinities using machine learning techniques.
The pipeline ingests experimental data from NIST and PubChem, generates molecular descriptors,
trains Random Forest and Gradient Boosting models with host-identity stratified cross-validation,
and performs rigorous statistical analysis to identify robust predictive determinants.

**Key Features**:
- Automated data ingestion from NIST/PubChem with fallback to simulated data.
- Host-identity stratified splitting to prevent data leakage.
- Feature stability analysis and physical plausibility checks.
- Bootstrap confidence intervals for statistical rigor.
- Automated report generation.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- A POSIX-compliant shell (bash, zsh) or Windows Subsystem for Linux (WSL)

## Dependencies

Install all required dependencies using pip:

```bash
pip install -r code/requirements.txt
```

The `requirements.txt` file includes:
- `scikit-learn`: For machine learning models and metrics.
- `rdkit`: For molecular descriptor generation and structure parsing.
- `pandas`: For data manipulation and analysis.
- `numpy`: For numerical operations.
- `requests`: For data scraping.
- `beautifulsoup4`: For HTML parsing.
- `pyyaml`: For configuration and state management.
- `pytest`: For testing (optional).

## Project Structure

```text
PROJ-446-predicting-molecular-halide-binding-affi/
├── code/ # Source code for the pipeline
│ ├── utils/ # Shared utilities (config, logging, validators)
│ ├── 00_create_directories.py
│ ├── 01_data_ingestion.py
│ ├── 02_feature_engineering.py
│ ├── 03_model_training.py
│ ├── 04_feature_analysis.py
│ ├── 05_statistical_reporting.py
│ └──... (other pipeline scripts)
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Cleaned and processed datasets
│ └── simulated/ # State and temporary files for simulated mode
├── docs/
│ ├── paper/ # Generated reports and figures
│ └──...
├── specs/ # Feature specifications
├── requirements.txt # Python dependencies
└── README.md # This file
```

## How to Run the Pipeline

The pipeline is designed to be executed sequentially. Ensure you are in the project root directory.

### 1. Setup Directories (If not already created)
```bash
python code/00_create_directories.py
```

### 2. Data Ingestion and Preprocessing
Downloads data from NIST/PubChem, validates, cleans, and filters.
If insufficient real data is found, it automatically switches to simulated data mode.
```bash
python code/01_data_ingestion.py
```
*Output*: `data/processed/halide_binding_data.csv`

### 3. Feature Engineering
Generates molecular descriptors (ECFP fingerprints, charge density, cavity volume, etc.).
```bash
python code/02_feature_engineering.py
```

### 4. Model Training
Trains Random Forest and Gradient Boosting models with host-identity stratified k-fold cross-validation.
```bash
python code/03_model_training.py
```
*Output*: `data/processed/model_runs.json`

### 5. Feature Analysis
Performs stability analysis, generates partial dependence plots, and checks physical plausibility.
```bash
python code/04_feature_analysis.py
```
*Output*: `data/processed/feature_analysis.json`, `docs/paper/figures/`

### 6. Statistical Reporting
Calculates bootstrap confidence intervals and generates the final report section.
```bash
python code/05_statistical_reporting.py
```
*Output*: `data/processed/statistical_summary.json`

### 7. Final Report Generation
Compiles all results into a comprehensive markdown report.
```bash
python code/06_generate_final_report.py
```
*Output*: `docs/paper/report.md`

## Configuration

Configuration is managed via `code/utils/config.py`.
Key settings include random seeds, file paths, and solvent lists.
To modify settings, edit the `config.py` file or the `state.yaml` file if present.

## Validation & Testing

Run the test suite (if available):
```bash
pytest tests/
```

Run linters and formatters:
```bash
python code/setup_linting.py
```

## Notes

- **Simulated Data Mode**: If the pipeline cannot find at least 50 unique host molecules in the real data, it will automatically switch to simulated data mode to allow the modeling pipeline to complete. This mode is explicitly logged and reported in the final analysis.
- **Resource Constraints**: All models are CPU-only and designed to run within 6 hours and 7GB RAM limits.
- **Associational Nature**: Results are associational, not causal.

## License

[Insert License Information Here]