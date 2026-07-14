# Predicting Adsorption Isotherm Parameters from Molecular Features

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

This project implements an automated machine learning pipeline to predict adsorption isotherm parameters (Langmuir capacity, Henry constant) from molecular descriptors. It supports both synthetic data generation for pipeline validation and external literature data for scientific verification.

## Features

- **Data Curation**: Automatic generation of synthetic datasets and loading of external literature data (e.g., Kr on CNTs).
- **Descriptor Calculation**: Computation of molecular features using RDKit (polarizability, kinetic diameter, etc.).
- **Model Training**: Training of Linear Regression, Random Forest, and Gradient Boosting models with material-level splitting.
- **Interpretability**: SHAP analysis and partial dependence plots to identify key drivers.
- **Validation**: Automated consensus checks against physicochemical literature (SC-002) and performance thresholds (SC-003).

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PROJ-245-predicting-adsorption-isotherm-parameter
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Pipeline

**Synthetic Data Flow (MVP Validation)**:
Generates synthetic data, preprocesses it, trains models, and runs SHAP analysis.
```bash
python code/main.py --mode synthetic
```

**External Data Flow (Scientific Validation)**:
Loads the curated external dataset (Kr on CNTs), trains models, and runs consensus validation.
```bash
python code/main.py --mode external
```

### Output Artifacts

After a successful run, check the `data/` and `figures/` directories:

- `data/processed/processed_data.csv`: Cleaned dataset with molecular descriptors.
- `data/validation/sc002_match_report.json`: Consensus check results (external mode only).
- `data/validation/sc003_r2_report.json`: R² performance report (external mode only).
- `figures/shap_summary.png`: SHAP summary plot.
- `figures/pdp_plots.png`: Partial dependence plots.

## Project Structure

```
.
├── code/
│ ├── data/ # Data generation, loading, and preprocessing
│ │ ├── synthetic_gen.py
│ │ ├── download.py
│ │ ├── load_external.py
│ │ ├── preprocess.py
│ │ └── descriptors.py
│ ├── models/ # Model training and evaluation
│ │ ├── train.py
│ │ ├── evaluate.py
│ │ ├── null_comparison.py
│ │ └── permutation_pvalue.py
│ ├── interpret/ # SHAP analysis and diagnostics
│ │ ├── shap_analysis.py
│ │ └── diagnostics.py
│ └── main.py # Orchestrator
├── data/
│ ├── raw/ # Raw synthetic/external data
│ ├── processed/ # Cleaned and feature-engineered data
│ ├── external/ # Manually curated external datasets
│ └── validation/ # Validation reports
├── contracts/ # Schema definitions
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── requirements.txt
└── README.md
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Linting and Formatting

```bash
ruff check code/
black code/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
