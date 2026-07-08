# Research: Identifying Structure-Property Relationships in Polymer Blends

## Dataset Strategy

The project relies on public datasets to fulfill FR-001. Per the "Verified datasets" constraint, we will utilize the following sources.

**Critical Note on Data Availability**: The "Verified datasets" block provided in the prompt does not contain a specific dataset for "Polymer Blends" with "Tg (K)" and "Young's Modulus (GPa)" columns. The block lists datasets for drug-like molecules, APIs, and general text.
* **Decision**: The implementation will attempt to fetch from the *named* APIs (NIST, Materials Project) as per the spec's FR-001.
* **Hard Halt Condition**: If these APIs do not return polymer blend data containing the required target variables (Tg, Modulus), the pipeline will **halt** with a "Data Insufficiency" error. **No synthetic or simulated target variables will be generated.** This ensures the scientific validity of the results and compliance with the Single Source of Truth principle.
* **No Fallback to Drug-like Data**: Datasets like `MKEChem/mke-novel-druglike-smiles` or `fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors` are **not** suitable for this research question as they lack the specific polymer property data (Tg, Modulus). They will not be used for the core analysis.

**Dataset Table**:

| Dataset Name | Source URL | Usage | Status |
|:--- |:--- |:--- |:--- |
| NIST WebBook (API) | *API Endpoint (Not in verified list)* | Primary source for Tg/Modulus | **Conditional** (Must return polymer blend data; otherwise Halt) |
| Materials Project (API) | *API Endpoint (Not in verified list)* | Primary source for Tg/Modulus | **Conditional** (Must return polymer blend data; otherwise Halt) |
| SMILES (Drug-like) | ` | Not used for core analysis | **Verified but Inapplicable** (Lacks Tg/Modulus) |
| RDKit Descriptors | ` | Not used for core analysis | **Verified but Inapplicable** (Lacks Tg/Modulus) |

**Gap Analysis**:
* **Risk**: No verified public dataset currently exists in the provided list that contains polymer blend Tg/Modulus data.
* **Mitigation**: The pipeline attempts to fetch from NIST/Materials Project APIs. If successful, it proceeds. If not, it halts.
* **Consequence**: If no verified source is found, the research question "Identifying Structure-Property Relationships in Polymer Blends" cannot be answered with the current data resources. The project will be marked as "Data Insufficient" and no further analysis will be performed.

## Methodology & Statistical Rigor

### 1. Data Ingestion & Harmonization (FR-001, FR-002)
* **Unit Conversion**: All temperature values converted to Kelvin (K); Modulus to GPa.
* **Validation**:
 * Weight fraction sum check: $| \sum w_i - 1.0 | \le 0.02$. Rows failing this are excluded (FR-002).
 * SMILES validity: Parsed via RDKit; invalid entries excluded (FR-003).
* **Robustness**: Exponential backoff (max 5 retries) for API rate limits.
* **Data Quality Metric**: Calculate `Data_Quality_Rate = (Valid Records / Total Fetched) * 100` (SC-004).

### 2. Feature Engineering (FR-003, FR-004, FR-008)
* **Descriptors**: Generate $\ge 15$ descriptors per monomer (MW, TPSA, Rotatable Bonds, Fractional Free Volume, etc.) using RDKit.
* **Interaction Features**:
 * Weighted averages of descriptors.
 * Absolute differences between components.
 * **Baseline Physical Models**: Compute Fox Equation and Gordon-Taylor Equation for Tg prediction. **These are used as baselines for comparison, NOT as predictors in the ML model.** This prevents circular validation where the model learns the mixing rule it is given.
* **Collinearity (FR-008)**:
 * Calculate Variance Inflation Factor (VIF) for all predictors.
 * Flag pairs with VIF > 5.0.
 * **Sensitivity Analysis**: Train model excluding the highest VIF predictor, compare MAE. Report impact *without* auto-exclusion.

### 3. Model Training & Validation (FR-005, FR-006, FR-007)
* **Models**: Random Forest (RF) and XGBoost (XGB).
* **Baselines**:
 1. Linear Regression (on descriptors).
 2. Physical Mixing Rule (Fox/Gordon-Taylor equation predictions).
* **Validation**: K-Fold Cross-Validation (if $N \ge 100$). If $N < 100$, halt with "Data Insufficiency" error.
* **Hyperparameter Tuning**: Grid search or Bayesian optimization (CPU-tractable) on validation set.
* **Selection**: Model with lowest validation MAE.
* **Statistical Test (FR-006)**: Paired t-test on absolute errors (ML vs. Physical Mixing Rule Baseline). Report p-value.
 * **Multiplicity Correction**: Apply Bonferroni or FDR correction for multiple comparisons (Assumption).
* **Interpretability (FR-007)**: SHAP values for top-ranked predictions.
* **Stability Analysis (SC-003)**: Execute **5 independent training runs** with different seeds. Measure feature importance stability.

### 4. Confounder Control (Addressing `methodology-b9c4dce2`)
* **Challenge**: Specific processing parameters (e.g., annealing history) are likely missing from public datasets.
* **Strategy**:
 * **Observed Covariates**: Include any available processing parameters as covariates if present.
 * **Unmeasured Confounding**: Calculate **E-values** post-hoc using the `sensemakr` package or manual calculation. The E-value quantifies the minimum strength of association that an unmeasured confounder would need to have with both the treatment (molecular structure) and the outcome (Tg/Modulus) to explain away the observed effect.
 * **Reporting**: Report the E-value and interpret it in the context of the observed effect size. This provides a measure of robustness against unmeasured confounding without requiring the missing data.
 * **Framing**: All findings are explicitly framed as **associational**, not causal, due to the observational nature of the data.

### 5. Compute Feasibility
* **Environment**: 2 CPU, 7 GB RAM.
* **Strategy**:
 * Use CPU-only `xgboost` and `scikit-learn`.
 * Sample data if raw fetch > 7 GB.
 * Avoid GPU-specific libraries (no `bitsandbytes`, no CUDA).
 * Target runtime < 5 hours.
 * **Hard Halt**: If data is insufficient or missing, stop immediately to save resources.

## Success Metrics (SC)

* **SC-001**: MAE of best ML model vs. Physical Mixing Rule Baseline (Test Set).
* **SC-002**: p-value from paired t-test (Significance of improvement over baseline).
* **SC-003**: Feature stability (Top 3 descriptors in $\ge 80\%$ of 5 independent runs).
* **SC-004**: Data Quality (a high proportion of fetched records pass validation).
* **SC-005**: Runtime < 5 hours on GitHub Actions free-tier.