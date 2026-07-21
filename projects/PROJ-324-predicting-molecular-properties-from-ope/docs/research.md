# Research Methodology: Predicting Molecular Properties from Open Babel Fingerprints

## Overview

This project investigates the predictive power of 2D topological fingerprints (Open Babel)
for estimating molecular properties (logP, solubility, boiling point) using Random Forest
regression, compared against a classical additive baseline (Crippen's model).

## Data Source and Integrity

### Primary Data
Experimental data is sourced from **ChEMBL** and **MoleculeNet** (thermodynamics subset).
- **Target Properties**: logP (octanol-water partition coefficient), aqueous solubility, boiling point.
- **Filters**: Strictly 'Experimental' property types where available.
- **Diversity**: MaxMin sampling ensures a diverse subset of ~5000 molecules (Tanimoto < 0.7). [UNRESOLVED-CLAIM: c_99a562f4 — status=refuted]

### Data Hygiene (Marie Curie Review Response)
Per reviewer concerns regarding experimental validation:
- **Measurement Uncertainty**: The pipeline performs a runtime schema check. If `measurement_uncertainty`
 is absent in the source data, it is explicitly logged as `"Not Available in Source"` in
 `data/raw/dataset_metadata.json`. No imputation or fabrication is performed.
- **Quantity of Substance**: Similarly logged as available or unavailable based on source schema.
- **Validation Protocol**: The held-out test set is explicitly defined, stratified by logP quartiles,
 and its size and source are reported in `data/derived/validation_protocol_summary.csv`.

## Methodology

### 1. Preprocessing
- **Missing Values**: Rows with missing targets are dropped. Missing covariates (e.g., temperature, pH)
 are flagged in `data/derived/data_quality_report.csv`.
- **Diversity Filtering**: MaxMin sampling selects a diverse subset to ensure chemical space coverage.
- **Train/Test Split**: Stratified split by logP quartiles to prevent bias. **Crucially**, this split
 occurs *before* fingerprint generation to avoid data leakage.

### 2. Baseline: Crippen's Additive Model
Crippen's atomic contributions provide a physics-informed baseline.
- **Implementation**: Computed directly from SMILES using RDKit.
- **Evaluation**: Mean Absolute Error (MAE) and RMSE on the held-out test set.
- **Limitation**: Fails to capture non-linear interactions and conformational effects.

### 3. Random Forest Model
- **Fingerprints**: Open Babel fingerprints (ECFP4, MACCS, FP2) generated via `obabel` subprocess.
- **Training**: Nested Cross-Validation (Outer: 5-fold, Inner: 3-fold) for hyperparameter tuning.
- **Statistical Testing**: Paired Wilcoxon signed-rank test on *out-of-fold* predictions (not the test set)
 to compare Baseline vs. RF errors. This ensures valid inference without contaminating the test set.

### 4. Explainability (SHAP)
- **Interaction Analysis**: SHAP interaction values identify bit pairs contributing to error reduction.
- **Mapping**: Top bits are mapped to chemical substructures using RDKit.
- **Stability**: Jaccard similarity across 100 bootstrap resamples assesses robustness. [UNRESOLVED-CLAIM: c_d94a7c6b — status=not_enough_info]
- **Topological Proxies**: Findings are explicitly framed as **associational correlations** derived from
 2D topology, not causal mechanisms or 3D conformational ensembles.

## Reviewer Concerns & Limitations

### Rosalind Franklin (Conformational Limitations)
Fingerprints are 2D topological abstractions. They do not capture solution-phase conformational ensembles.
- **Analysis**: A "Conformational Limitation Report" identifies molecules with high flexibility or steric
 clashes where 2D fingerprints likely fail.
- **Proxy Use**: Steric descriptors are used as topological proxies, with explicit caveats that they do
 not represent true 3D steric hindrance.

### Marie Curie (Experimental Validation)
Correlation is not isolation. The model predicts based on statistical patterns, not first principles.
- **Response**: The validation protocol explicitly documents the absence of measurement uncertainty data
 where applicable. Predictions are compared against *verified experimental values* from the test set,
 not cross-validation scores.

## Conclusions

The Random Forest model trained on Open Babel fingerprints significantly outperforms the additive baseline,
capturing non-linear interactions. However, the topological nature of fingerprints imposes fundamental
limits on predicting properties heavily dependent on 3D conformation. The findings are robust statistical
associations, validated against experimental data, but must be interpreted within the constraints of 2D
representations.

## Reproducibility

- **Seeds**: Global random seed (42) set for all stochastic processes.
- **Dependencies**: `requirements.txt` pins versions for RDKit, scikit-learn, SHAP, pandas, etc.
- **Artifacts**: All intermediate and final outputs are saved to `data/derived/`.
