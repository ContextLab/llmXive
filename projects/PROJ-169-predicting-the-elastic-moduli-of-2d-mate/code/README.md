# Project: Predicting the Elastic Moduli of 2D Materials

This project implements a surrogate model to interpolate pre-computed DFT results. It does NOT solve the Schrödinger equation or perform first-principles calculations.

## Reproducibility Instructions

To ensure reproducibility, the random seeds are pinned in `code/utils/config.py`.
The project uses the following dependencies (defined in `code/requirements.txt`):

* pymatgen
* torch
* torch-geometric
* shap
* pandas
* numpy
* scikit-learn
* ruff
* black

To run the project, follow these steps:

1. Install dependencies: `pip install -r code/requirements.txt`
2. Run the analysis pipeline (see `quickstart.md`).
