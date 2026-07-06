# Methodology: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Overview

This document outlines the computational methodology employed in the `PROJ-355` project.
The primary goal is to quantify the relationship between impurity clustering descriptors
and grain boundary (GB) segregation energies using statistical regression models.

## Data Pipeline

1. **Data Acquisition**: Bulk crystal structures are downloaded from the Materials Project (MP)
 and the Open Quantum Materials Database (OQMD).
2. **GB Construction**: Grain boundary supercells are constructed using `pymatgen`.
3. **Impurity Insertion**: Impurity atoms are inserted at the GB interface.
4. **Descriptor Computation**: Local atomic environment descriptors (RDF peaks, pair correlation,
 Voronoi neighbor counts) are computed for the interface region.
5. **Energy Simulation**: Segregation energies are calculated using NIST EAM potentials
 with structural perturbation to break symmetry.

## Cross-Validation Procedure

To ensure robust model evaluation and prevent overfitting, a **K-Fold Cross-Validation**
strategy is employed.

### K-Fold Setup
- **K Value**: 5 folds (configurable via `code/config.py`).
- **Shuffle**: True.
- **Random Seed**: Fixed at **42** (defined in `code/config.py`) to ensure reproducibility
 across runs (Constitution Principle I).

### Procedure
1. The dataset is split into K mutually exclusive subsets of approximately equal size.
2. The model is trained K times. In each iteration:
 - K-1 folds are used for training.
 - The remaining 1 fold is used for validation.
3. Metrics (R², RMSE, p-values) are computed for each fold and aggregated.

### LOOCV Fallback Logic
If the dataset size is smaller than K (i.e., fewer than 5 samples), the procedure
automatically switches to **Leave-One-Out Cross-Validation (LOOCV)**:
- The number of folds is set to the number of samples.
- Each sample serves as the validation set exactly once.
- This ensures every data point is used for both training and validation.

## Statistical Analysis

- **Model**: Linear Regression (MVP) with `statsmodels` OLS.
- **Collinearity**: Variance Inflation Factor (VIF) is calculated. If VIF ≥ 10,
 a warning is logged, but features are retained as per FR-007 (Report, don't remove).
- **Significance**: p-values are calculated for coefficients using HC3 robust standard errors.
 Multiple comparison correction (Bonferroni/FDR) is applied in Phase 5.

## Reproducibility

All random operations (data splitting, structural perturbation) use the seed defined
in `code/config.py`. The seed is 42.
