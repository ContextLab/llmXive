# Methodology: Detecting Statistical Power Drift in Replicated Studies

This document details the statistical methodology employed in the `llmXive` pipeline (Project PROJ-150) to detect temporal drift in statistical power across replicated studies. The analysis relies on a **Linear Mixed-Effects Model (LMM)** framework,辅以 robustness checks via permutation testing and cross-field aggregation.

## 1. Data Source and Preprocessing

### 1.1 Data Acquisition
The analysis utilizes the **OSF Reproducibility Project** dataset (`osf/reproducibility_project`), specifically the `data.csv` file. Data is fetched programmatically using the `huggingface_hub` library.
- **Integrity Check**: A title-token-overlap metric (threshold ≥ 0.7) is computed to verify the dataset source matches the expected "OSF Reproducibility Project".
- **Constraint**: The loader fails loudly if the source is unreachable; no synthetic fallbacks are permitted.

### 1.2 Preprocessing and Cleaning
Raw data is processed in `code/preprocess.py`:
1. **Missing Data Handling**: Rows with missing values in critical columns (`year`, `effect_size`, `sample_size`) are skipped. A warning is logged for each skipped row (format: `WARNING: Skipping row {index} due to {reason}`).
2. **Grouping Validation**: The grouping variables `field` and `original_study_id` are validated for cardinality and variance.
 - Factors with only one unique level are flagged as `"single_level"` in `data/derived/grouping_validation.json`.
 - **Crucial Note**: This flagging is for logging purposes only. The downstream model fitting does **not** dynamically exclude these terms. Instead, the model handles zero-variance groups by fixing the random effect variance to a small epsilon (e.g., `1e-6`) to preserve the required model structure (Constitution Principle VII).

## 2. Power Estimation and Residualization

### 2.1 Power Calculation
Statistical power ($1-\beta$) is estimated for each study using the observed effect size (Cohen's $d$) and sample size ($N$). The calculation follows standard procedures for t-tests, implemented in `code/power_calc.py`.

### 2.2 Pilot OLS Model (Deterministic Relationship)
To isolate the temporal drift component from the mechanical relationship between power and its inputs, a **Pilot OLS Model** is fitted:
$$ \text{power\_est} = \beta_0 + \beta_1(\text{effect\_size}) + \beta_2(\text{sample\_size}) + \epsilon $$
- **Purpose**: This model captures the deterministic variance in power attributable to the study's design parameters.
- **Output**: The fitted model is saved to `data/derived/pilot_ols_model.pkl`.

### 2.3 Residualization
The target variable for the primary drift analysis is the **residual power**:
$$ \text{power\_residual} = \text{power\_est} - \widehat{\text{power}}_{\text{OLS}} $$
- **Rationale**: By regressing out the effects of effect size and sample size, `power_residual` represents the portion of power not explained by the study's specific parameters. This isolates potential systematic drift (e.g., changes in methodology, publication bias, or analysis practices) over time.
- **Output**: Residuals are saved to `data/derived/residuals.csv`.

## 3. Primary Analysis: Linear Mixed-Effects Model (LMM)

The core hypothesis test for temporal drift is conducted using a Linear Mixed-Effects Model implemented in `code/models.py`.

### 3.1 Model Specification
The **Full LMM** is specified as follows:
$$ \text{power\_residual}_{ij} = \beta_0 + \beta_1(\text{year}_{ij}) + u_{0j}(\text{field}) + v_{0k}(\text{original\_study\_id}) + \epsilon_{ij} $$

Where:
- $\beta_1(\text{year})$ is the **fixed effect** of interest. The coefficient $\beta_1$ (slope) represents the annual drift in residual power.
- $u_{0j}$ and $v_{0k}$ are **random intercepts** for `field` and `original_study_id`, respectively.
- **Constraint**: The model formula **MUST** include `(1|field) + (1|original_study_id)` unconditionally. No dynamic exclusion of random effects is permitted, even if a grouping factor has zero variance. If a factor has a single level, the optimizer is constrained (e.g., via `start` parameters) to fix the variance to a small value rather than removing the term.

### 3.2 Primary Metric
The primary metric for drift is the **slope of the year coefficient** (`slope_year`) extracted from the Full LMM.
- **Significance**: A negative slope indicates a decline in statistical power over time, controlling for study design and field-specific effects.
- **Confidence Intervals**: Calculated using the Wald method.

### 3.3 Significance Validation (Likelihood-Ratio Test)
To validate the significance of the `year` term, a **Likelihood-Ratio Test (LRT)** is performed:
- **Full Model**: `power_residual ~ year + (1|field) + (1|original_study_id)`
- **Reduced Model**: `power_residual ~ (1|field) + (1|original_study_id)` (no `year` term)
- **Statistic**: $\chi^2 = -2(\log L_{\text{reduced}} - \log L_{\text{full}})$
- **Output**: The LRT p-value (`p_value_lrt`) is reported in `results/lmm_final_summary.json`.

## 4. Robustness and Sensitivity Analysis

### 4.1 Non-Parametric Permutation Test
To verify that the observed drift is not an artifact of the model assumptions, a permutation test is conducted (implemented in `code/robustness.py`):
- **Procedure**: The `year` labels are shuffled across the dataset while keeping `effect_size`, `sample_size`, and grouping variables constant.
- **Iterations**: Target of 10,000 permutations. Fallback to 1,000 if resource limits (time > 300s or memory > 6GB) are exceeded.
- **Metric**: The empirical p-value is calculated as the proportion of permuted slopes that are as extreme as or more extreme than the observed `slope_year`.
- **Output**: `results/permutation_pvalue.json`.

### 4.2 Sensitivity Analysis
The stability of the drift conclusion is tested by sweeping the significance threshold ($\alpha$) across a range of values (e.g., 0.001 to 0.1).
- **Output**: `results/sensitivity_report.json` reports the significance of the drift at each threshold and includes a `threshold_dependence_statement`.

## 5. Cross-Field Aggregation

To combine evidence across heterogeneous scientific fields, a meta-analytic approach is used (implemented in `code/robustness.py`).

### 5.1 Field-Specific Slopes
Separate LMMs are fitted for each `field` to extract field-specific drift estimates (`slope_year`) and standard errors.
- **Input**: `data/derived/residuals.csv`.
- **Output**: `data/derived/field_slopes.csv`.

### 5.2 DerSimonian-Laird Weighting
An inverse-variance weighted average of the field-specific slopes is calculated, adjusted for heterogeneity ($\tau^2$).
- **Algorithm**: DerSimonian-Laird method.
- **Output**: `results/aggregated_drift.json` containing the combined drift estimate and confidence interval.
- **Comparison**: The aggregated estimate is compared against the primary LMM slope in `results/comparison_aggregated_vs_lmm.json`.

## 6. Input Permutation Framework

To validate that the drift is driven by temporal factors rather than confounding changes in effect sizes or sample sizes over time:
- **Procedure**: `effect_size` and `sample_size` are shuffled while `year` is held constant.
- **Re-fitting**: The LMM is refitted on each permuted dataset to generate a null distribution of slopes.
- **Output**: `results/input_permutation_pvalue.json` and `results/null_distribution_implied_power.csv`.

## 7. Visualization

Key visualizations are generated by `code/visualize.py`:
- **Scatter Plot**: `power_residual` vs. `year` with a regression line (`results/power_drift_scatter.png`).
- **Null Distribution**: Comparison of the observed slope against the input-permutation null distribution.

## 8. Implementation Notes

- **Software**: Python 3.x, `statsmodels` (for LMM), `scipy`, `pandas`, `numpy`.
- **Reproducibility**: All random seeds are fixed where applicable. The pipeline is orchestrated via `code/main.py`.
- **Data Integrity**: Strict adherence to "No Synthetic Fallback" principles. All results are derived from real, fetched data.