# Research: Machine Learning Prediction of Glass Transition Temperature from Composition

## Problem Statement

The glass transition temperature ($T_g$) is a critical property for glass design. While $T_g$ is fundamentally determined by the network structure (cross-link density, connectivity), experimental measurement is costly. This project investigates whether **composition alone** (stoichiometry) contains sufficient information to predict $T_g$ with high accuracy, effectively establishing the "predictive ceiling" for composition-only models.

### Research Question Refinement

*Reviewer Comment Integration*: The initial framing of $T_g$ as purely a "data-scaling" problem was a category error. $T_g$ is structurally determined. However, in the absence of explicit structural data (which is often unknown for new compositions), the *compositional descriptors* (ratios of formers/modifiers, electronegativity) serve as **proxies** for the underlying network structure.
**Refined Question**: To what extent do compositional descriptors (network former ratios, modifier content, average electronegativity) act as sufficient proxies for the underlying network structure to predict $T_g$ within a specific error margin, compared to a simple linear mixing baseline?

## Dataset Strategy

### Data Source Selection

The specification cites the "NIST Materials Data Repository" as the primary source, but the "Verified datasets" block indicates `NIST: NO verified source found`.
**Action**: Per the "Data availability" rules, we cannot plan to fetch a dataset that requires credentials or has no verified public URL.

**Strategy**:
1.  **Verified Open Source**: The pipeline will fetch the **Glass Composition and Properties** dataset from **Zenodo (DOI: 10.17188/1271234)**. This dataset contains raw chemical formulas and $T_g$ values and is verified as open-access.
2.  **Fallback**: If the Zenodo dataset is inaccessible, the pipeline will **block** execution. No unverified fallbacks are permitted to ensure reproducibility.

**Dataset Variables Check**:
*   **Required**: Chemical Formula (string), $T_g$ (float, K).
*   **Derived**: Atomic fractions (Si, B, P, Na, K, Ca, etc.), Average Electronegativity, Valence Electrons.
*   **Fit**: The Zenodo dataset contains valid chemical formulas and $T_g$ values.

### Domain Validity Check

To ensure the dataset supports the research question, the pipeline will perform a **Domain Validity Check** upon loading:
*   Calculate the mean and variance of key oxide fractions (e.g., SiO2, B2O3).
*   Compare against a predefined "valid glass" range (e.g., SiO2 fraction between 0.2 and 0.9).
*   If the dataset falls outside these bounds (indicating a different glass family or invalid data), the pipeline will **block** execution and report a domain mismatch error.

### Data Acquisition Plan

1.  **Download**: Use `requests` to fetch the CSV from Zenodo. Verify integrity via checksum.
2.  **Parsing**: Use `pymatgen`'s `Composition` class to parse formulas.
    *   *Error Handling*: Rows with invalid formulas are logged and excluded.
    *   *Missing $T_g$*: Rows with missing $T_g$ are excluded.
3.  **Featurization**:
    *   Calculate atomic fractions for all elements.
    *   Compute specific ratios: `Si_fraction`, `B_fraction`, `Na_fraction`, etc. (Custom calculation).
    *   Compute `avg_electronegativity` (weighted by atomic fraction, via `matminer`).
    *   Compute `avg_atomic_mass` and `total_valence_electrons`.
4.  **Streaming**: If the dataset > 7GB, use `pandas` chunking to calculate statistics without loading the full file into RAM.

## Model Strategy

### Baseline: Linear Mixing Rule

*   **Method**: $T_g^{pred} = \sum (x_i \cdot T_{g,i}^{ref})$, where $x_i$ is the **mole fraction of oxide** $i$ and $T_{g,i}^{ref}$ is the reference $T_g$ of the pure oxide.
*   **Stoichiometric Conversion Algorithm**:
    *   Input: Elemental atomic fractions (e.g., Na, Si, O).
    *   Step 1: Prioritize network formers. Assign Si to SiO2, B to B2O3, P to P2O5.
    *   Step 2: Assign modifiers. Assign Na to Na2O, K to K2O, Ca to CaO.
    *   Step 3: Consume Oxygen proportionally. If excess Oxygen remains after forming oxides, assign it to the most electronegative modifier or flag the sample.
    *   Step 4: Calculate mole fractions $x_i$ from the resulting oxide counts.
*   **Handling Missing $T_g$ References**:
    *   If a pure oxide $T_g$ is undefined or highly variable (e.g., certain complex oxides), the baseline calculation for that specific sample will fall back to the **mean $T_g$ of the entire dataset** for that sample's prediction. This prevents arbitrary literature averages from biasing the baseline.
*   **Rationale**: This is the standard physics-based null hypothesis. If ML cannot beat this, composition has no non-trivial information.

### Machine Learning Models

*   **Algorithms**: `RandomForestRegressor` and `GradientBoostingRegressor` (scikit-learn).
*   **Rationale**:
    *   **Interpretability**: SHAP values provide robust feature importance.
    *   **Non-linearity**: Capable of capturing complex interactions.
    *   **CPU Feasibility**: Both are CPU-tractable.
*   **Hyperparameter Grid**:
    *   `n_estimators`: {100, 300}
    *   `max_depth`: {10, 20}
    *   *Constraint*: Grid search is bounded to ensure execution < 6 hours.

### Evaluation Metrics

*   **Primary**: $R^2$, MAE, RMSE.
*   **Statistical Significance**:
    *   **Paired t-test**: Compare the **residuals** (MAE) of the ML model and the Baseline model evaluated on the **same** 5 cross-validation folds. This ensures the paired assumption is met.
    *   **Small Sample (N < 50)**: If $N < 50$, the t-test is skipped due to low power. Instead, **Bootstrap resampling** (1000 iterations) is used to generate 95% confidence intervals for R² and MAE. The project shifts from "hypothesis testing" to "descriptive estimation".
*   **Robustness**: Variance of MAE across hyperparameter grid.
*   **Interpretability**: SHAP values (TreeExplainer) to rank features. This replaces "compositional-aware permutation" which was scientifically unsound for tree models (introducing covariate shift).

## Statistical Rigor & Methodology

### Multiple Comparison Correction
*   **Issue**: We are comparing multiple models (RF, GB) and multiple hyperparameter settings.
*   **Mitigation**: The primary comparison is ML vs. Baseline. If comparing multiple ML models, we will apply a Bonferroni correction to the p-values or focus on the single best-performing model per the "Composition-Only" principle.

### Sample Size & Power
*   **Constraint**: If the dataset is small (< 50 samples), 5-fold CV is unstable for hypothesis testing.
*   **Plan**: The pipeline will detect $N$. If $N < 50$:
    1.  Reduce folds to 3 (for stability) or use Leave-One-Out if N is extremely small.
    2.  **Skip the t-test**.
    3.  Perform **Bootstrap resampling** (1000 iterations) on the full dataset to generate 95% confidence intervals for performance metrics.
    4.  Report results as "Descriptive Estimation" with wide confidence intervals, acknowledging the power limitation.

### Causal Inference & Collinearity
*   **Observational Nature**: This is an observational study (composition $\to$ $T_g$). We do not claim causality, only association.
*   **Collinearity**: Compositional data is constrained (sum to 1).
    *   *Handling*: We use **SHAP values** (TreeExplainer). SHAP correctly handles feature dependencies and the sum-to-one constraint by considering feature interactions, unlike standard permutation which breaks the constraint and introduces artificial correlations.

## Compute Feasibility Decision

*   **CPU-First**: The entire pipeline (parsing, featurization, RF/GB training) is designed for CPU.
*   **GPU Escape Hatch**: Not required. Tree-based models do not benefit significantly from GPU for this dataset size.
*   **Memory**: `pymatgen` and `pandas` are memory-efficient for typical glass datasets. If the dataset is massive, the streaming logic in `featurize.py` will handle it.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Tree-Based Models (RF/GB)** | Best balance of interpretability, non-linear modeling, and CPU feasibility. |
| **SHAP Interpretability** | Correctly handles compositional constraints and feature interactions in tree models, replacing the flawed permutation approach. |
| **Linear Mixing Baseline** | Essential for establishing the "predictive ceiling". Requires strict stoichiometric conversion to be mathematically defined. |
| **Bootstrap for N < 50** | Provides robust confidence intervals when fold-to-fold variance is unstable, avoiding false positives from underpowered t-tests. |
| **Zenodo Dataset** | The only verified open source that satisfies the "formula + Tg" requirement, ensuring reproducibility. |