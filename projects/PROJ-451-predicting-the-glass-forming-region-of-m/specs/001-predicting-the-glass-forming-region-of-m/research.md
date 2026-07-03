# Research: Predicting the Glass Forming Region of Metallic Glass Alloys Using Machine Learning

## Problem Statement

Metallic glasses (amorphous alloys) exhibit superior mechanical properties but are difficult to synthesize due to narrow glass-forming regions. This project aims to predict whether a given alloy composition will form an amorphous or crystalline phase using machine learning models trained on atomic-scale descriptors derived from elemental properties.

## Dataset Strategy

| Dataset Name | Source Reference | Access Method | Notes |
|--------------|------------------|---------------|-------|
| Metallic Glass Compositions (Zenodo) | DOI: `` (Placeholder for verified DOI) | Programmatic fetch (`requests`) | Primary source for ≥1,000 labeled compositions. If fetch fails or DOI is placeholder, fallback to **Synthetic Generation** (see below). |
| Materials Project API | Materials Project (mp.org) | Programmatic API (`requests` + API key) | Provides elemental properties (atomic radius, electronegativity, valence electron concentration) for descriptor computation. |
| Miedema Parameters (Okamoto et al.) | NIST/Thermo-Calc Data (Local JSON) | Local file `data/raw/miedema_params.json` | Provides binary interaction parameters for ΔHmix calculation. Not available via MP API. |

**Synthetic Data Fallback Strategy**:
To ensure reproducibility on a fresh CI runner (Constitution Principle I), if the primary Zenodo dataset is unavailable or the DOI is a placeholder, the pipeline will generate a synthetic dataset. This synthetic data will be generated using:
1. Random sampling of elemental fractions from known metallic glass formers (Zr, Cu, Al, Mg, Y, etc.).
2. Assignment of phase labels based on known empirical rules (e.g., atomic size mismatch > 0.1, negative mixing enthalpy).
3. Inclusion of realistic noise to mimic experimental error.
This ensures the pipeline can be executed and tested without manual intervention.

## Feature Engineering Strategy

The following atomic-scale descriptors will be computed for each alloy composition:

1. **Atomic Size Mismatch (δ)**:
 \( \delta = \sqrt{\sum_i c_i (1 - r_i / \bar{r})^2} \)
 where \( c_i \) is atomic fraction, \( r_i \) is atomic radius, \( \bar{r} \) is weighted average radius.

2. **Electronegativity Difference (Δχ)**:
 \( \Delta\chi = \sqrt{\sum_i c_i (\chi_i - \bar{\chi})^2} \)

3. **Mixing Enthalpy (ΔHmix)**:
 Computed using the Miedema model with binary interaction parameters sourced from `data/raw/miedema_params.json` (based on Okamoto et al.).
 **Approximation Handling**: If a specific binary pair is missing from the database, a default parameter is used, and the record is flagged with `miedema_approximation_flag = true`.

4. **Valence Electron Concentration (VEC)**:
 \( VEC = \sum_i c_i \cdot VEC_i \)

5. **Atomic Packing Fraction (APF)**: Derived from atomic radii and fractions.

**Multicollinearity Handling**:
To address the risk of multicollinearity (e.g., ΔHmix derived from δ and Δχ), the pipeline will:
1. Calculate Variance Inflation Factors (VIF) for all descriptors.
2. If VIF > 5 for a derived feature, apply Recursive Feature Elimination (RFE) or Principal Component Analysis (PCA) to reduce dimensionality before model training.
3. Report feature importance only for non-collinear features or use SHAP interaction values to distinguish main effects from interactions.

## Model Strategy

| Model | Library | Hyperparameter Tuning | Validation |
|-------|---------|------------------------|------------|
| Random Forest | `scikit-learn` | GridSearchCV (n_estimators, max_depth, min_samples_split) | k-fold stratified CV

The specific value to remove/generalize: 'k'

Rewritten passage: |
| XGBoost | `xgboost` | GridSearchCV (learning_rate, max_depth, n_estimators) | 5-fold stratified CV |
| Logistic Regression (Baseline) | `scikit-learn` | Default (no tuning) | 5-fold stratified CV |

**Stratification**: By alloy system (e.g., Zr-based, Mg-based) to ensure generalization across chemistries. **Integrity Check**: The pipeline will verify that phase labels are balanced *within* each alloy system stratum. If a system is confounded (e.g., [deferred] amorphous), it will be flagged and handled via stratified sampling within the system or exclusion.

**Data Split**: [deferred] Training, [deferred] Validation, [deferred] Test (held out). The Test set is strictly disjoint from training and validation to prevent data leakage.

**Statistical Comparison**: Nadeau & Bengio corrected t-test on fold-level balanced accuracy scores. Bonferroni correction applied if >2 models compared (FR-008).

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Bonferroni correction applied to all pairwise model comparisons (FR-008).
- **Power Analysis**: A post-hoc power analysis will be conducted. For a binary classification task with 80% power, α=0.05, and an expected effect size (Cohen's d) of 0.5, a minimum of ~128 samples per class is required. If the dataset falls below this threshold, the study will report confidence intervals and effect sizes rather than relying solely on p-values to avoid Type II errors.
- **Causal Inference**: Observational study; claims limited to associational (no randomization).
- **Measurement Validity**: Elemental properties sourced from Materials Project (validated database); descriptors computed via standard thermodynamic formulas.
- **Collinearity**: Addressed via VIF analysis and RFE/PCA as described above.

## Compute Feasibility

- **Dataset Size**: Capped at [deferred] compositions (FR-007).
- **Memory**: All operations use pandas/numpy with float32; expected peak RAM < 7 GB.
- **Runtime**: 5-fold CV on 3 models with ≤1,000 samples per fold; estimated < 2 hours on 2-core CPU.
- **No GPU**: All models trained in CPU-only mode (default scikit-learn/xgboost settings).

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Science Advances data unavailable | Pipeline logs warning; proceeds with synthetic fallback; FR-001 may fail if N < 1,000 (but pipeline remains reproducible) |
| Materials Project API rate limits | Retry with exponential backoff; cache responses locally |
| Class imbalance (amorphous vs. crystalline) | Stratified splitting; report balanced accuracy (not raw accuracy) |
| Descriptor computation fails for rare elements | Skip composition with missing properties; log warning; ensure ≥95% completeness (FR-001) |
| Miedema parameters missing | Use default parameters and flag record (`miedema_approximation_flag`); perform sensitivity analysis |