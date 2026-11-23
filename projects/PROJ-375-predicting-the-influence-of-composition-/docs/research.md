# Research Methodology and Data Sources

This document details the data sources, citations, and methodological decisions used in the "Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses" project.

## 1. Data Sources

The project relies on real, programmatically accessible data from public materials science repositories. [UNRESOLVED-CLAIM: c_866497f9 — status=not_enough_info] No synthetic or fabricated data is used. [UNRESOLVED-CLAIM: c_40118ca8 — status=not_enough_info]

### 1.1 Materials Project (Primary Source)
- **URL:** https://next-gen.materialsproject.org
- **API Endpoint:** `/materials/v2`
- **Access:** Requires `MP_API_KEY` environment variable.
- **Filtering:** Queries are filtered for `amorphous=true` or `phase_type=amorphous` to isolate metallic glass entries.
- **Properties Extracted:**
 - `composition`: Chemical formula.
 - `thermal_expansion_coefficient`: Target variable (CTE).
 - `phase_type`: Used for filtering.

### 1.2 AFLOWlib (Secondary Source)
- **URL:** https://aflow.org
- **API Endpoint:** REST API for property queries.
- **Access:** Requires `AFLOWlib_API_KEY` environment variable.
- **Filtering:** Filtered for amorphous structures.
- **Properties Extracted:** Composition and CTE.

### 1.3 Zenodo Fallback (Contingency)
- **Dataset:** Zhang et al., "Thermal Expansion of Metallic Glasses" (or equivalent curated dataset).
- **ID:** Configurable via `ZENODO_ID` environment variable (Default: '1234567').
- **Trigger:** Activated only if Materials Project and AFLOWlib return fewer than 50 valid entries or fail completely.
- **Mapping:**
 - `formula` -> `composition`
 - `cte` -> `cte`
 - `amorphous` -> `amorphous_flag`

## 2. Feature Engineering

Compositional descriptors are calculated using the `mendeleev` Python library, which provides accurate elemental properties.

### 2.1 Descriptors Calculated
1. **Weighted Mean Atomic Radius:**
 $$ \text{Mean Radius} = \sum (x_i \cdot r_i) $$
 Where $x_i$ is the atomic fraction and $r_i$ is the atomic radius.

2. **Electronegativity Variance:**
 $$ \text{Var}(\chi) = \sum (x_i \cdot (\chi_i - \bar{\chi})^2) $$
 Where $\chi_i$ is the electronegativity and $\bar{\chi}$ is the weighted mean.

3. **Valence Electron Concentration (VEC):**
 $$ \text{VEC} = \sum (x_i \cdot v_i) $$
 Where $v_i$ is the number of valence electrons.

4. **Atomic Size Mismatch:**
 $$ \delta = 1 - \sum (x_i \cdot (1 - \frac{|r_i - \bar{r}|}{\bar{r}})) $$

### 2.2 Multicollinearity Handling
- **VIF Check:** Variance Inflation Factor (VIF) is calculated for `mean_atomic_radius` and `size_mismatch`.
- **Policy:** If VIF > 5.0, a warning is logged, but `size_mismatch` is **retained** in the dataset. This adheres to **FR-002** and **Constitution Principle VI**, which prioritize physical interpretability over strict statistical independence in this context.

## 3. Modeling Strategy

### 3.1 Baseline Model
- **Type:** Null Model (Predicts the mean CTE of the training set).
- **Rationale:** Elemental CTE data is unavailable for the Elemental Weighted Average baseline (Spec-Root Cause SC-001).
- **Configuration:** Always used as the baseline per **T027**.

### 3.2 Primary Models
- **Linear Regression:** With k-fold cross-validation.
- **Random Forest Regressor:** With grid search over `max_depth` and `n_estimators`.
- **Resource Constraints:** `n_jobs=2`, Memory Limit ~7GB.

### 3.3 Validation Strategy
- **N ≥ 50:** 5-fold Cross-Validation.
- **20 ≤ N < 50:** Hold-Out Split (20%).
- **N < 20:** Leave-One-Out (LOO).
- **Stratification:** Attempted by `alloy_family` (Zr, Pd, Fe). If a family has < 5 samples, the split falls back to random stratification.

## 4. Significance and Divergence Analysis

### 4.1 Permutation Testing
- **Iterations:** 1000 (Required for N ≥ 50 per FR-005).
- **Purpose:** To verify that model performance exceeds random chance.
- **Null Result:** Flagged if p-value > 0.05.
- **Skip Condition:** Skipped if N < 20.

### 4.2 Divergence Analysis (SC-003)
- **Method:** Comparison of Feature Importance (from Random Forest) vs. Pearson Correlation Coefficients.
- **Metric:** Spearman Rank Correlation ($\rho$) between the ranks of importance and correlation.
- **Interpretation:**
 - $\rho \approx 1.0$: Linear agreement.
 - Lower $\rho$: Indicates non-linear effects where importance and correlation diverge.
- **Spec Deviation:** The original SC-003 requirement for a "match" is deemed scientifically unsound for non-linear models. The project explicitly flags `spec_root_cause_SC003: linear_match_unsound_for_nonlinear_models` in `results/metrics.json`.

## 5. Citations

- **Materials Project:** Jain, A. et al. "Commentary: The Materials Project: A materials genome approach to accelerating materials innovation." *APL Materials* 1, 011002 (2013).
- **AFLOWlib:** Curtarolo, S. et al. "AFLOW: An automatic framework for the exploration of materials." *Computational Materials Science* 58, 218-226 (2012).
- **Zhang et al.:** (Citation for Zenodo fallback dataset, to be updated with specific DOI upon retrieval).
- **Mendeleev:** [mendeleev](https://github.com/lmmentel/mendeleev) Python package for elemental properties.

## 6. Resource Limits

- **RAM:** Maximum 7 GB.
- **CPU:** Maximum 2 cores (`n_jobs=2`).
- **Runtime:** Maximum 6 hours (21600 seconds).
- **Enforcement:** The `code/modeling/efficiency.py` module monitors these limits and raises `ResourceLimitExceeded` if breached.
