# Predicting Molecular Halide Binding Affinities with Machine Learning

**Project ID**: PROJ-446-predicting-molecular-halide-binding-affi

## Project Goal

This project aims to predict molecular halide binding affinities using machine learning techniques. The pipeline ingests experimental data from NIST/PubChem, generates molecular descriptors, trains Random Forest and Gradient Boosting models, and performs rigorous statistical analysis to identify robust predictive determinants of halide binding.

Key objectives include:
- Downloading and parsing experimental halide binding data
- Generating molecular descriptors (ECFP fingerprints, charge density, cavity volume)
- Training and evaluating machine learning models with host-identity stratified cross-validation
- Performing feature stability analysis and partial dependence plotting
- Generating statistically rigorous reports with bootstrap confidence intervals

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Access to NIST/PubChem databases (for real data ingestion)

## Dependencies

Install all required dependencies using pip:

```bash
pip install -r code/requirements.txt
```

The `requirements.txt` file includes:
- `scikit-learn>=1.4.0`: Machine learning models and utilities
- `rdkit`: Chemical informatics and descriptor calculation
- `pandas`: Data manipulation and analysis
- `numpy`: Numerical computing
- `requests`: HTTP library for data scraping
- `beautifulsoup4`: HTML parsing for web scraping
- `pyyaml`: YAML configuration parsing
- `pytest`: Testing framework

## Project Structure

```
PROJ-446-predicting-molecular-halide-binding-affi/
├── code/ # Source code
│ ├── utils/ # Utility modules
│ │ ├── config.py # Configuration management
│ │ ├── logger.py # Logging infrastructure
│ │ ├── validators.py # Schema validation
│ │ ├── state_manager.py # Project state tracking
│ │ ├── error_handler.py # Global error handling
│ │ └── performance_optimizer.py # Resource monitoring
│ ├── 01_data_ingestion.py # Data scraping and cleaning
│ ├── 02_feature_engineering.py # Molecular descriptor generation
│ ├── 03_model_training.py # Model training and cross-validation
│ ├── 04_feature_analysis.py # Feature stability and interpretation
│ ├── 05_statistical_reporting.py # Statistical analysis and reporting
│ ├── 06_generate_final_report.py # Final report generation
│ └──... # Other pipeline scripts
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed datasets and model artifacts
│ └── simulated/ # Simulated data fallback (if needed)
├── docs/ # Documentation
│ ├── paper/ # Research paper and figures
│ ├── quickstart.md # Quick start guide
│ └── API.md # API documentation
├── state.yaml # Project state tracking
├── requirements.txt # Python dependencies
└── README.md # This file
```

## How to Run the Pipeline

The pipeline is designed to run sequentially through the following stages:

### 1. Setup and Initialization

```bash
# Create project directories
python code/00_create_directories.py

# Initialize project state
python code/00_create_state.py
```

### 2. Data Ingestion and Preprocessing

```bash
# Run the data ingestion pipeline
python code/01_data_ingestion.py
```

This script will:
- Scrape NIST/PubChem for halide binding data
- Validate and clean the data
- Filter for hosts with multiple halide measurements
- If insufficient real data is found (<50 hosts), it will automatically switch to simulated data mode

### 3. Feature Engineering

```bash
# Generate molecular descriptors
python code/02_feature_engineering.py
```

### 4. Save Processed Data

```bash
# Save the final processed dataset
python code/02_save_processed_data.py
```

### 5. Model Training

```bash
# Train Random Forest and Gradient Boosting models
python code/03_model_training.py
```

### 6. Feature Analysis

```bash
# Run feature stability analysis and generate partial dependence plots
python code/04_feature_analysis.py

# Generate feature summary table
python code/05_feature_summary.py
```

### 7. Statistical Reporting

```bash
# Perform statistical analysis and generate report sections
python code/05_statistical_reporting.py
```

### 8. Final Report Generation

```bash
# Generate the final research report
python code/06_generate_final_report.py

# Save all feature outputs
python code/06_save_feature_outputs.py
```

### 9. Validation and State Update

```bash
# Validate the quickstart process
python code/07_validate_quickstart.py

# Update state with artifact hashes
python code/08_update_state_hashes.py
```

## Simulated Data Mode

If the pipeline cannot find sufficient real experimental data (<50 hosts with multiple halide measurements), it will automatically:
1. Identify the most abundant halide in the available data
2. Generate simulated binding constants using the formula: `log K_sim = 0.5 * charge_density + 0.3 * cavity_volume + N(0, 0.2)`
3. Store the simulated data and set a `SIMULATED_MODE=True` flag
4. Log a warning that comparative analysis will be aborted

When in simulated data mode, the statistical reporting stage will explicitly abort comparative analysis and generate a report noting that the primary research question cannot be answered with simulated data.

## Output Artifacts

The pipeline produces the following key artifacts:

- `data/processed/halide_binding_data.csv`: Processed dataset with molecular descriptors
- `data/processed/model_runs.json`: Model training metrics and feature importances
- `data/processed/feature_analysis.json`: Feature stability analysis results
- `data/processed/statistical_summary.json`: Statistical analysis results with confidence intervals
- `docs/paper/report.md`: Final research report
- `docs/paper/figures/`: Partial dependence plots and other visualizations

## Configuration

Project configuration is managed through `code/utils/config.py`. Key configurable parameters include:
- Random seeds for reproducibility
- File paths for data and outputs
- List of valid solvents (acetonitrile, chloroform, DCM)
- Simulated mode settings

## Constraints

- All modeling must run on CPU-only environments
- Maximum RAM usage: 7GB
- Maximum runtime: 6 hours
- No GPU/CUDA acceleration
- No large language models or quantization techniques

## Testing

Run tests using pytest:

```bash
pytest tests/ -v
```

## License

This project is part of the llmXive automated science pipeline.

## Contact

For issues or questions, please refer to the project documentation or contact the development team.