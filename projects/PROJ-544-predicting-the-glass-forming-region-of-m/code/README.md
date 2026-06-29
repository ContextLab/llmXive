# Code Directory

This directory contains the source code for the **Predicting the Glass Forming Region of Multi-Component Alloys via Machine Learning** project (PROJ-544).

## Purpose

The `code/` directory houses all Python modules, scripts, and configuration files required to:
- Compute thermodynamic descriptors for alloy compositions
- Train and evaluate machine learning classifiers for glass-forming prediction
- Generate feature importance analysis and SHAP visualizations
- Manage project data flows and artifact provenance

## Directory Structure

```
code/
├── config/ # Project configuration files (environment settings, seeds)
├── descriptors/ # Thermodynamic descriptor computation modules
│ ├── compute.py
│ ├── validate_elements.py
│ ├── utils.py
│ └──...
├── models/ # Machine learning model training and evaluation
│ ├── train.py
│ ├── evaluate.py
│ └── importance.py
└── README.md # This file
```

## Module Responsibilities

### `descriptors/`
- **validate_elements.py**: Validates elemental symbols against pymatgen's periodic table
- **compute.py**: Calculates atomic size mismatch (δ), mixing enthalpy (ΔH), and electronegativity variance (Δχ)
- **utils.py**: Provides fallback mechanisms for missing elemental properties

### `models/`
- **train.py**: Trains Random Forest and Gradient Boosting classifiers with cross-validation
- **evaluate.py**: Computes ROC-AUC, precision, recall, and other performance metrics
- **importance.py**: Generates permutation importance and SHAP visualizations

### `config/`
- **env.yaml**: Environment configuration including random seeds, memory limits, and experimental parameters

## Dependencies

All Python dependencies are pinned in `requirements.txt` at the project root. Key packages include:
- `pymatgen` for materials data and periodic table access
- `dscribe` for descriptor computation
- `scikit-learn` for machine learning
- `shap` for model interpretability

## Running Scripts

Execute scripts from the project root using the virtual environment:
```bash
source.venv/bin/activate
python scripts/<script_name>.py
```

## Artifact Outputs

All scripts produce outputs in the `data/`, `results/`, and `logs/` directories as specified in their respective task definitions. Provenance and checksums are tracked in `state/`.

## Reviewer Notes

Per reviewer rosalind-franklin-simulated: This ML pipeline computes statistical correlations between composition descriptors and glass-forming ability. The model does not determine structural properties directly—cooling rate and thermal history must be measured experimentally. See `docs/causal_vs_associational_claims.md` for discussion of correlational vs. causal claims.