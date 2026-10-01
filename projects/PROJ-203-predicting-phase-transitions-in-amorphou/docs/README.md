# Predicting Phase Transitions in Amorphous Solids Using Machine Learning

## Overview

This project implements a machine learning pipeline to predict glass transition temperatures ($T_g$) and crystallization propensity in amorphous solids. The pipeline integrates molecular dynamics (MD) simulations, structural descriptor extraction, and Random Forest models to analyze the relationship between short-range structural features and thermal properties.

## Scope

- **Pilot Study**: N=24 compositions (stratified by chemical family: oxide, sulfide, organic).
- **Goals**:
 - Achieve RMSE ≤ 15 K for $T_g$ prediction (validated via Null Model/Permutation Tests).
 - Achieve ROC-AUC > 0.7 for crystallization classification.
 - Identify universal vs. family-specific structural predictors.

## Key Features

- **Virtual Alignment Protocol**: Aligns MD simulation timescales with experimental DSC cooling rates.
- **Robust Validation**: Includes Null Model, Permutation Tests, Collinearity Analysis (VIF), and LOO Jackknife Resampling for small sample stability.
- **Interpretability**: SHAP analysis with Bonferroni correction for family-wise error control.

## Getting Started

See [`docs/quickstart.md`](quickstart.md) for installation and execution instructions.

## Project Structure

```
├── code/ # Source code
├── data/ # Data inputs and outputs
├── docs/ # Documentation
├── tests/ # Tests
├── artifacts/ # Models and figures
└── specs/ # Design documents
```

## Pipeline Stages

1. **Data Generation**: MD simulations (LAMMPS/OpenMM) for 24 pilot compositions.
2. **Descriptor Extraction**: RDF, bond-angle variance, coordination numbers.
3. **Dataset Assembly**: Merge descriptors with experimental $T_g$ and $T_x$ labels.
4. **Model Training**: Random Forest regression and classification.
5. **Evaluation**: Metrics, SHAP analysis, sensitivity analysis, collinearity checks.
6. **Reporting**: Final interpretability report and visualizations.

## Dependencies

- Python 3.9+
- NumPy, Pandas, Scikit-learn, SciPy
- Matplotlib, Seaborn, SHAP
- MDTraj, OpenMM, LAMMPS
- Pyaml, Pydantic, Datasets

See `code/requirements.txt` for the full list.

## License

[Insert License Information Here]

## Contact

[Insert Contact Information Here]
