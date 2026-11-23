# Predicting Phase Transitions in Amorphous Solids Using Machine Learning

A research pipeline for predicting glass transition temperatures (Tg) and crystallization propensity in amorphous solids using molecular dynamics (MD) simulations and machine learning.

## Overview

This project implements a data-driven approach to understand the relationship between short-range order (SRO) structural descriptors and thermal properties in amorphous materials. The pipeline integrates:

- **MD Simulations**: Using LAMMPS/OpenMM to generate structural trajectories.
- **Descriptor Extraction**: Calculating RDF, bond-angle variance, and coordination numbers.
- **Machine Learning**: Random Forest models for regression (Tg) and classification (crystallization).
- **Interpretability**: SHAP analysis to identify universal vs. family-specific predictors.

## Key Features

- **Pilot Study**: Executed on a stratified sample of 24 compositions (N=24) to validate the pipeline. [UNRESOLVED-CLAIM: c_057d0b26 — status=not_enough_info]
- **Timescale Matching**: Implements alignment protocol to match MD and experimental cooling rates.
- **Statistical Rigor**: Includes Null Model/Permutation Tests and LOO jackknife resampling for small sample sizes.
- **Modular Design**: Independent user stories allow for parallel development and testing.

## Quickstart

See [`docs/quickstart.md`](docs/quickstart.md) for installation and execution instructions.

## Project Structure

```
.
├── code/ # Source code
│ ├── config.py # Configuration
│ ├── main.py # Pipeline entry point
│ ├── data/ # Data processing
│ ├── models/ # Model training/evaluation
│ └── utils/ # Utilities
├── data/ # Data storage
├── docs/ # Documentation
├── artifacts/ # Models and figures
└── tests/ # Tests
```

## Workflow

1. **Data Generation**: Validate literature data, run MD simulations, extract descriptors.
2. **Model Training**: Train Random Forest models on the generated dataset.
3. **Evaluation**: Assess performance (RMSE, ROC-AUC) and conduct sensitivity analysis.
4. **Interpretability**: Generate SHAP plots and stability reports to identify key predictors.

## Requirements

- Python 3.9+
- LAMMPS / OpenMM (for MD simulations)
- scikit-learn, pandas, numpy, shap, mdtraj, etc.

See `code/requirements.txt` for the full list.

## Contributing

This is a research implementation. Please follow the task list in `tasks.md` for development progress.

## License

[Add License Information]
