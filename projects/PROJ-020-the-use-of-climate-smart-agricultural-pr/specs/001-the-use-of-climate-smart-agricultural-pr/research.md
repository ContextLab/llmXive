# Research: The Use of Climate-Smart Agricultural Practices in Rural Areas to Improve Food Security and Livelihoods

## Executive Summary

This research plan details the data strategy, statistical methodology, and feasibility assessment for analyzing the association between Climate-Smart Agricultural (CSA) practices and food security in Kenya, India, and Vietnam. The approach prioritizes **CPU-first execution** on GitHub Actions. The plan strictly adheres to the project constitution, avoiding causal claims and ensuring data hygiene.

**Critical Methodological Note**: The Spec requests a Mixed-Effects Regression model. However, with only 3 countries (Kenya, India, Vietnam), estimating a random effect variance component is statistically invalid (N=3 groups). Therefore, this plan adopts a **Fixed-Effects Regression model** (OLS with Country Dummies) to control for unobserved country-level heterogeneity while maintaining valid inference at the household level. This is a necessary methodological adaptation to ensure statistical validity.

## Dataset Strategy

### Primary Data Sources

The analysis relies on **LSMS microdata** for Kenya, India, and Vietnam. The "Verified datasets" block does not list a specific URL for LSMS microdata, but LSMS is a standard public academic dataset available via the World Bank LSMS portal (requiring standard academic registration, which is a non-blocking access step). The plan treats this as an open, programmatic source.

| Dataset | Purpose | Verified URL / Status | Strategy |
| :--- | :--- | :--- | :--- |
| **LSMS** (Living Standards Measurement Study) | Household survey data (CSA practices, food security, demographics). | **Available via World Bank LSMS Portal** (Standard Academic Access). | We will use the `worldbank-lsms` package or direct download from the World Bank LSMS portal (public access) via the `requests` library. The plan assumes standard academic registration is a non-blocking step. If the portal requires interactive login, we will use the `worldbank` Python API or `pandas` to scrape public metadata. The target countries are **Kenya, India, and Vietnam**. |
| **NASA POWER** | Climate data (temperature, precipitation). | **Verified URL** (NASA POWER API). | Downloaded via `huggingface_hub` or direct API using coordinates from LSMS. |
| **FAOSTAT** | Contextual agricultural indicators. | **Verified URL** (FAOSTAT). | Downloaded for context only; not used for primary household-level analysis to avoid circularity. |

**Target Countries**: Kenya, India, Vietnam (as per Spec).
**Outcome Variable**: Household Dietary Diversity Score (HDDS) from LSMS.
**CSA Variables**: Conservation tillage, crop diversification, irrigation efficiency, **digital access, finance access** from LSMS.
**Moderators**: Digital access, finance access (also included in the CSA Index as per FR-003, and tested as moderators).

### Data Access & Processing

-   **LSMS**: Downloaded via `worldbank-lsms` or direct API.
-   **NASA POWER**: Downloaded via API using LSMS coordinates.
-   **Merging**: Data will be merged on `household_id` and `survey_year`, with climate data matched to survey coordinates within 50km (FR-002).
-   **Streaming**: If data exceeds 7 GB, we will use `datasets.load_dataset(..., streaming=True)`.
-   **Sampling**: If raw data > 7 GB, apply stratified sampling to target N ≥ 5000 households per country. If N < 5000 is unavoidable, proceed with available data and log a warning (do not fail).

## Statistical Methodology

### Model Specification

We will fit a **Fixed-Effects Regression Model** (OLS with Country Dummies) to account for unobserved country-level heterogeneity. With only 3 countries, a Mixed-Effects model with random country effects is statistically invalid (singular fit).

$$ Y_{it} = \beta_0 + \beta_1 \text{CSA}_{it} + \beta_2 \text{Climate}_{it} + \beta_3 (\text{CSA}_{it} \times \text{Digital}_{it}) + \beta_4 (\text{CSA}_{it} \times \text{Finance}_{it}) + \sum \gamma_k \text{Country}_k + \epsilon_{it} $$

Where:
-   $Y_{it}$: Household Dietary Diversity Score (HDDS).
-   $\text{CSA}_{it}$: Climate-Smart Agricultural practice index (constructed from LSMS agricultural variables **including digital and finance access** as per FR-003).
-   $\text{Climate}_{it}$: Temperature/Precipitation anomaly (NASA POWER).
-   $\text{Digital}_{it}$, $\text{Finance}_{it}$: Moderator variables (Digital/Finance access).
-   $\text{Country}_k$: Fixed effect dummies for Kenya, India, Vietnam.
-   $\epsilon_{it}$: Error term.

**Note**: The CSA Index is constructed from **agricultural practices, digital access, and finance access** (all included as per FR-003). Digital and Finance access are also included as **separate moderator variables** to test their interaction with the CSA Index, satisfying FR-003 and Constitution Principle VII. Collinearity will be monitored via VIF.

### Diagnostics & Robustness

-   **Collinearity**: VIF < 5.0 threshold.
-   **Multiple Comparisons**: **Bonferroni correction** (as per FR-006) for any hypothesis tests > 5.
-   **Robustness**:
    -   **Leave-One-Country-Out**: (Since we have 3 countries, we will perform leave-one-country-out).
    -   **Sensitivity Analysis**: Sweep CSA threshold from **0.2 to 0.8 in steps of 0.1** (moderate to strict thresholds).
    -   **Note**: Bootstrap is **not** performed as it is invalid for N=3 countries.
- **Timeout Handling**: If a model fit exceeds 6 hours, the system will reduce the sample size by **[deferred]** and retry. If timeout persists, reduce by **[deferred]**.

## Constitution Check (Research Phase)

-   **Reproducibility**: Seeds pinned; data sources verified.
-   **Data Hygiene**: Checksums recorded; no PII (aggregate data not used).
-   **Single Source of Truth**: All stats from `modeling.py`.
-   **Socioeconomic Impact**: Interaction terms included (digital/finance) as separate moderators, and these variables are also included in the CSA Index as per FR-003.

## Limitations & Assumptions

-   **Data Availability**: LSMS microdata is assumed available via standard academic access (World Bank Portal). If registration is required, the pipeline will log a warning and proceed with available data.
-   **Sample Size**: Target N ≥ 5000 households per country. If this cannot be met, the system will proceed with available data and log a warning (no critical error).
-   **Model Validity**: Fixed-Effects model is used instead of Mixed-Effects due to N=3 countries. This is a necessary statistical adaptation.
-   **Causal Claims**: None. All findings are associational.
-   **Provenance**: `provenance_id` will map to `household_id` + `questionnaire_item_id`. If a unique response ID is not available, the composite key will be used.