# Methodology Notes: Adoption of Sustainable Agricultural Practices

## 1. Data Acquisition and Preprocessing

### Source Selection
We prioritize World Bank LSMS and FAO FIES datasets for their coverage of low-income agricultural households. These sources provide granular data on farming practices, household demographics, and community participation.

### Handling Missing Data
- **Threshold**: Rows with >30% missing values in required variables (age, education, farm_size, credit, adoption, engagement items) are dropped.
- **Imputation**: For remaining missing values, we use mean imputation for continuous variables and mode imputation for categorical variables.
- **Validation**: `02_clean_data.py` logs missingness patterns and validates against the schema in `specs/018-adoption-sustainable-agriculture/contracts/dataset.schema.yaml`.

## 2. Feature Engineering

### Adoption Indicator (`adoption_binary`)
Defined as 1 if the respondent reports using **any** of the following sustainable practices:
- Crop rotation
- Organic fertilizer
- Water conservation techniques
- Integrated pest management
- Agroforestry

### Community Engagement Score (`engagement_score`)
Constructed as a weighted sum of proxy variables:
- Membership in farmer cooperatives
- Participation in extension programs
- Collective action involvement
- Knowledge exchange frequency

**Weights**: Equal-weight average is used as the default. If top-priority proxies are absent, the system falls back to available proxies (FR-011).

### Reliability and Validity
- **Cronbach's Alpha**: Calculated to assess internal consistency of the engagement score.
- **Exploratory Factor Analysis (EFA)**:
 - Extraction: Principal Axis Factoring
 - Rotation: Varimax (orthogonal)
 - Retention: Kaiser's rule (eigenvalues > 1)
- **Convergent Validity**: Assessed via correlation with theoretically related constructs (e.g., income, farm productivity).

## 3. Statistical Modeling

### Logistic Regression
Model specification:
```
adoption_binary ~ engagement_score + age + education + farm_size + credit_access + region
```

- **Estimation**: Maximum Likelihood via `statsmodels`.
- **Diagnostics**:
 - **VIF**: Variance Inflation Factor calculated for all predictors. VIF ≥ 5 triggers a collinearity warning (FR-007).
 - **FDR Correction**: Benjamini-Hochberg procedure applied to p-values (q ≤ 0.10) to control false discovery rate (FR-008).
 - **ROC Analysis**: AUC calculated and plotted to assess model discrimination (FR-009).

### Mediation Analysis
We investigate whether the effect of community engagement on adoption is mediated by access to credit or knowledge.

- **Approach**: Baron & Kenny steps with bootstrap confidence intervals (≥1000 resamples).
- **Sensitivity Analysis**:
 - **E-values**: Calculated to assess robustness to unmeasured confounding (using `evalues` library).
 - **Rosenbaum Bounds**: Calculated for gamma values including 2.5 to test sensitivity to hidden bias.
- **Interpretation**: All mediation results are labeled "exploratory" due to the observational design (FR-012).

## 4. Power and Sample Size Considerations

We calculate the ratio of `effective_N_events` (count of positive outcomes in `adoption_binary`) to `num_predictors`. If this ratio is < 10, a shortfall is logged in `modeling_log.yaml` as a study limitation (SC-006). Execution continues to ensure reproducibility, but results should be interpreted with caution.

## 5. Reproducibility

- **Random Seeds**: Fixed for all stochastic operations (synthetic generation, bootstrap resampling) via `config.py`.
- **Logging**: All decisions, warnings, and parameter choices are recorded in `modeling_log.yaml`.
- **Schemas**: Input and output data conform to YAML schemas defined in `specs/.../contracts/`.
- **Version Control**: Code and configuration are versioned to ensure exact replication.

## 6. Limitations and Ethical Considerations

- **Causality**: As an observational study, causal claims are limited. Mediation results are hypothesis-generating.
- **Data Quality**: If real API data is unavailable, synthetic data is used. This is explicitly documented.
- **Generalizability**: Findings are specific to low-income contexts; extrapolation to other regions requires caution.