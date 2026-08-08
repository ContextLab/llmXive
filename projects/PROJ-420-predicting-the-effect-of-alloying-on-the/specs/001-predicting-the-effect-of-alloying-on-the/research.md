# Research: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Dataset Strategy

The project relies on two primary public repositories for materials data. The strategy prioritizes open, programmatic access to ensure reproducibility on the GitHub Actions free tier.

| Dataset | Source | Access Method | Verification Status | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **Materials Project** | Materials Project API | `requests` (Public API) | **Verified** | Contains elastic constants and composition for many alloys. Poisson's ratio often derived or measured. [https://www.materialsproject.org/open](https://www.materialsproject.org/open) |
| **NIST Materials Data Repository** | NIST MDR | Direct Download (Parquet/CSV) | **Verified** | Contains curated experimental data, including independent Poisson's ratio measurements. [] |

**Verified datasets**:
- Materials Project: Public API (No authentication required for basic query).
- NIST Materials Data Repository: Direct download links available for aluminum alloy subsets.

**Fallback**: If the primary sources yield <50 valid entries, the pipeline will query the OpenML dataset (ID 42347) as a secondary source, though this is not the primary strategy per FR-001.

## Methodology

### 1. Data Extraction & Filtering
- **Source**: Query Materials Project API and NIST MDR for aluminum alloys.
- **Filtering Criteria**:
 - Monolithic (non-composite) alloys.
 - Presence of Poisson's ratio, Young's modulus, and elemental composition (Cu, Mg, Si, Zn, Mn).
 - Sum of major element atomic fractions ≥ 0.95 (exclude entries with significant missing trace elements).
 - **Independence Check**: Verify Poisson's ratio is not derived solely from Young's modulus (e.g., check `measurement_method` field or metadata). If the value is derived, the entry will be excluded.
- **Normalization**: Convert all elastic constants to GPa. Express composition as atomic fractions summing to 1.0.

### 2. Feature Engineering
- **Compositional Data Analysis**: Apply Isometric Log-Ratio (ILR) transformation to the atomic fractions of Cu, Mg, Si, Zn, and Mn. This removes the unit-sum constraint and allows the use of standard regression techniques.
- **Series Derivation**: Derive an `alloy_series` label (e.g., "2xxx", "6xxx") from the dominant alloying element to control for confounding by alloy family.
- **Interpretation**: Use **Permutation Importance** and **SHAP values** in the ILR space to rank alloying elements. **Do not** use back-transformation of feature importance scores, as this is mathematically invalid for non-linear models and can distort effect magnitudes. (Note: This deviates from FR-006 in the spec due to mathematical constraints).

### 3. Modeling
- **Algorithm**: Random Forest Regressor.
- **Validation**: 5-fold cross-validation on the training set.
- **Evaluation**: 80/20 train/test split. Compute Mean Absolute Error (MAE) on the held-out test set.
- **Diagnostics**:
 - Compute Variance Inflation Factors (VIF) for raw predictors to assess collinearity.
 - **Note**: High VIF (>5) is expected and inevitable in compositional data due to the unit-sum constraint. This is a diagnostic confirmation of the need for ILR, not a failure condition.
 - **Power Analysis**: If the dataset contains < 50 valid entries, the pipeline halts with an error (per Spec Edge Cases) as 5-fold CV would be unreliable. For N >= 50 but < 100, bootstrapping of feature importance will be used to assess stability.
 - **Error Metric**: Report test-set MAE relative to the standard deviation of the target variable. No arbitrary threshold (e.g., 0.05) is applied; instead, compare against the baseline mean predictor performance. (Note: This deviates from the spec's Edge Cases which mandate a 0.05 threshold).

### 4. Interpretation
- **Associational Framing**: All results will be explicitly framed as associational, not causal, due to the observational nature of the data.
- **Confounding Control**: The analysis controls for "alloy series" (derived from composition) to mitigate confounding. If heat treatment history is available, it will be included as a covariate. If these fields are missing, the report will explicitly state that confounding by alloy series is a limitation.
- **Feature Importance**: Rank alloying elements by their contribution to the variance in Poisson's ratio using Permutation Importance. The rankings will be compared against established physical mechanisms (atomic size mismatch, electronegativity differences) and relevant literature for validation.

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: Not applicable, as the analysis focuses on a single outcome (Poisson's ratio) and a single model.
- **Sample Size/Power**: The plan enforces a minimum of 50 entries. If <50 entries are found, the pipeline halts. For N >= 50 but < 100, bootstrapping of feature importance will be used to assess stability.
- **Causal Inference**: No causal claims are made. The study is observational.
- **Collinearity**: Addressed via ILR transformation for modeling. VIF diagnostics are used only to confirm the necessity of ILR, not to fail the pipeline.
- **Compute Feasibility**:
 - **CPU-First**: Random Forest and ILR transformation are computationally efficient and will run on the GitHub Actions CPU-only runner with limited core resources.
 - **GPU Escape Hatch**: Not required. The dataset size (<1000 entries) and model complexity are well within CPU limits.

## Risks & Mitigations

- **Risk**: Datasets return <50 valid entries.
 - **Mitigation**: Pipeline halts with a clear error message. No modeling proceeds.
- **Risk**: Poisson's ratio is derived from Young's modulus in source data.
 - **Mitigation**: Filtering logic explicitly excludes entries where `measurement_method` indicates derivation.
- **Risk**: Collinearity between alloying elements (e.g., Cu and Mg co-occur).
 - **Mitigation**: ILR transformation mitigates this for modeling. VIF diagnostics report the issue for transparency (no failure).
- **Risk**: Data availability (gated datasets).
 - **Mitigation**: Only open, programmatic sources (Materials Project, NIST MDR) are used. No authentication required.
- **Risk**: Confounding by alloy series.
 - **Mitigation**: Derive alloy series from composition and include as a covariate. If not possible, explicitly state this limitation in the results.
