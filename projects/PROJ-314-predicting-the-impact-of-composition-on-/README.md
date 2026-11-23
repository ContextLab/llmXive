# Predicting the Impact of Composition on the Weibull Modulus of Ceramics

**Project ID**: PROJ-314

## Overview

This project aims to predict the Weibull modulus of ceramic materials based on their chemical composition and processing parameters. The pipeline ingests raw data from multiple sources, computes elemental descriptors, trains predictive models, and provides mechanistic interpretations.

## Project Structure

```
PROJ-314-predicting-the-impact-of-composition-on-/
├── code/ # Source code
│ ├── ingestion.py # Data ingestion and cleaning
│ ├── descriptors.py # Descriptor computation
│ ├── modeling.py # Model training and evaluation
│ ├── diagnostics.py # Diagnostics and SHAP analysis
│ ├── report.py # Report generation
│ └──...
├── data/
│ ├── raw/ # Raw data files
│ ├── processed/ # Cleaned and processed data
│ ├── artifacts/ # Intermediate artifacts
│ ├── models/ # Trained models
│ ├── results/ # Model results and metrics
│ └── reports/ # Final reports
├── tests/ # Unit and integration tests
├── specs/ # Feature specifications
└── logs/ # Log files
```

## Quick Start

1. **Setup Environment**:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 pip install -r requirements.txt
 ```

2. **Verify Data Sources**:
 ```bash
 python code/verify_hf_dataset.py
 ```

3. **Run Pipeline**:
 ```bash
 python code/run_pipeline_timing.py
 ```

4. **Generate Test Data** (for gap testing):
 ```bash
 python code/scripts/create_test_n_dataset.py
 ```

## Key Features

- **Multi-source Ingestion**: Aggregates data from Zenodo, NIST, and arXiv.
- **Descriptor Computation**: Calculates mean atomic radius, electronegativity std, VEC, etc.
- **Predictive Modeling**: Random Forest and Gradient Boosting with stratified CV.
- **Interpretability**: SHAP analysis with collinearity-aware ranking.
- **Compliance**: Adheres to Constitution Principles (fail loudly, no synthetic data).

## License

[Insert License]
