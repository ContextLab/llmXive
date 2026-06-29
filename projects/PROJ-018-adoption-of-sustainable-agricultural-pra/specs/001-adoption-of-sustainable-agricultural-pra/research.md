# Research: Adoption of Sustainable Agricultural Practices in Low‑Income Areas through Community Engagement

## Dataset Strategy

### Verified Datasets Status
Per the project's Verified Datasets block, **no verified URLs exist for World Bank LSMS or FAO FIES microdata**. The available verified sources (e.g., `LRS3_landmarks.zip`, `NY_Math_Test_Results`) do not contain the required agricultural survey variables (farmer age, education, farm size, credit access, sustainable practice adoption, community engagement items).

| Dataset Name | Verified URL | Variable Fit | Status |
| :--- | :--- | :--- | :--- |
| World Bank LSMS | NO verified source found | High (Required) | **Gap** |
| FAO FIES | NO verified source found | High (Required) | **Gap** |
| FAO STAT | NO verified source found | Low (Aggregate only) | **Gap** |
| Synthetic Generator | N/A (Internal) | High (Schema Match) | **Fallback for CI** |

### Strategy
1.  **CI Execution**: Use a deterministic synthetic data generator (`code/01_download_data.py --synthetic`) that produces records conforming to the `SurveyRecord` schema (see `data-model.md`). This ensures the pipeline is runnable on free-tier GitHub Actions without external API dependencies or rate limits.
2.  **Research Execution**: Researchers must manually download LSMS/FAO FIES data from official sources (unverified in this context) and place it in `data/raw/`. The pipeline will detect raw files and process them accordingly.
3.  **Data Gap Documentation**: `research.md` explicitly states the lack of verified URLs to satisfy Constitution Principle II (Verified Accuracy).

## Methodology

### Statistical Model
- **Model**: Logistic Regression (StatsModels).
- **Outcome**: `adoption_binary` (1 = adopts ≥ 1 sustainable practice).
- **Predictors**: `engagement_score`, `age`, `education_level`, `farm_size_ha`, `credit_access`.
- **Mediation**: Baron & Kenny approach with bootstrap confidence intervals (≥ 1000 resamples) for predictors (`farm_size`, `credit_access`, `education`) → `engagement_score` → `adoption_binary`.
- **Causality Caveat**: Data is observational. Results are framed as **associational**. No causal claims are made regarding engagement or predictors.

### Statistical Rigor
- **Multiple Comparisons**: FR-008 mandates Benjamini-Hochberg FDR correction (q ≤ 0.10) on all hypothesis tests.
- **Power Analysis**: SC-006 requires checking the Established events-per-predictor rule for logistic regression AND a minimum of 500 observations for stable mediation bootstrap estimates. If `N * event_rate < 5 predictors * 10` OR `N < 500`, the limitation is documented.
- **Collinearity**: FR-007 mandates VIF calculation AND correlation matrix analysis. VIF ≥ 5 triggers a warning. **Additionally, pairwise correlations > 0.70 and PCA will be used to detect non-linear multicollinearity**. Predictors like `farm_size` and `credit_access` may be correlated; comprehensive collinearity checks address this.
- **Measurement Validity**: `engagement_score` is a composite of proxy variables (membership, extension, collective action, knowledge exchange). Cronbach's α is reported (SC-002). **Exploratory factor analysis (EFA) and convergent validity correlations will be computed to assess construct validity beyond reliability**. If α < 0.70, validity is flagged and limitations documented.
- **Mediation Sensitivity**: FR-012 mandates sensitivity analysis (E-values, Rosenbaum bounds) to assess robustness to unmeasured confounding in the mediator-outcome relationship. **Baron & Kenny approach in observational data cannot establish causality; unobserved confounders may produce spurious indirect effects**.

## Decision Rationale

### Why Synthetic Data for CI?
- **Reproducibility (Constitution I)**: External APIs (LSMS/FAO) may change endpoints or require authentication, breaking CI reproducibility.
- **Feasibility**: Verified dataset block lacks agricultural microdata. Using verified datasets (e.g., Math Test Results) would violate **Dataset-variable fit** (fatal flaw).
- **Solution**: A schema-compliant synthetic generator ensures the code pipeline works, while `research.md` documents the data source limitation for actual research.

### Why Logistic Regression?
- Appropriate for binary outcomes (`adoption_binary`).
- Interpretable odds ratios for policy recommendations.
- CPU-tractable (no GPU required).

### Why Mediation Analysis?
- Addresses the research question on *how* engagement influences adoption (indirect effects).
- Bootstrap CIs account for non-normality in indirect effects.
- **Explicitly labeled as exploratory (FR-012)** with sensitivity analysis for robustness assessment.
- **Minimum N=500 required for stable bootstrap indirect effect estimates; smaller samples will be flagged as power limitations**.

### Collinearity Assessment Rationale
- VIF detects linear multicollinearity but misses non-linear patterns.
- **Correlation matrix and PCA provide comprehensive assessment of all collinearity forms**.
- **Farm size and credit access may be definitionally related; correlation analysis will flag this, and effects will be reported descriptively with collinearity caveats**.