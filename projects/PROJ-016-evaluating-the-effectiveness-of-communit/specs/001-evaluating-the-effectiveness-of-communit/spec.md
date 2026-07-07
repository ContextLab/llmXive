# Feature Specification: Evaluating CBNRM vs State-Led Management

**Feature Branch**: `001-evaluating-cbnrm-effectiveness`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How does the implementation of community-based natural resource management (CBNRM) compare to state-led management in achieving sustainable land use outcomes across developing countries?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Harmonization (Priority: P1)

As a researcher, I need to download and merge land-use data from FAO STAT with governance/policy data from the World Bank Open Data API for low- and middle-income countries, explicitly classifying each country-year as either 'CBNRM' or 'State-led' management, so that I have a unified panel dataset ready for comparative analysis.

**Why this priority**: Without a clean, merged dataset containing both the outcome (land-use change), the predictor (regime type), and the covariates, no comparative statistical analysis can occur. This is the foundational block of the entire research pipeline.

**Independent Test**: The system can be tested by running the data ingestion script in isolation. If the script successfully produces a CSV file with at least [deferred] rows (target ≥ 50, contingent on data availability) containing non-null values for `land_use_change_rate`, `regime_type` (CBNRM/State-led), `gdp_per_capita`, and `population_density`, the story is complete. The test verifies that [deferred] of *available* matching records are included.

**Acceptance Scenarios**:

1. **Given** the World Bank and FAO APIs are accessible, **When** the ingestion script runs, **Then** it produces a merged CSV with [deferred] of requested country codes for the years 2000–2020.
2. **Given** a country code exists in FAO but not in the World Bank governance dataset, **When** the merge operation occurs, **Then** that row is excluded from the final dataset with a log entry indicating the missing governance data.
3. **Given** the input datasets contain inconsistent year formats (e.g., strings vs integers), **When** the cleaning step runs, **Then** all year columns are standardized to integer format before merging.
4. **Given** the source data contains general governance indices, **When** the classification step runs, **Then** the system maps records to 'CBNRM' or 'State-led' categories based on validated policy thresholds or specific CBNRM dataset flags.

---

### User Story 2 - Panel Regression and Inference (Priority: P2)

As a researcher, I need to run a fixed-effects panel regression comparing CBNRM adoption against state-led management (reference category) while controlling for GDP and population density, so that I can estimate the differential effect of regime type on land-use change.

**Why this priority**: This is the core analytical step that directly answers the research question. It must correctly frame the results as associational (since the study is observational) and control for the specified covariates.

**Independent Test**: The analysis can be tested by running the regression script on a synthetic dataset where the relationship between the predictor and outcome is known. The script must use a fixed random seed to generate data with a known coefficient (β=0.15) and noise level (σ=0.1). The script must output a coefficient for the CBNRM index that matches the synthetic truth within a 1% tolerance, and correctly label the output as "associational."

**Acceptance Scenarios**:

1. **Given** a valid merged dataset, **When** the regression model runs, **Then** it outputs a coefficient table including the CBNRM index (vs State-led baseline), GDP, and population density with p-values.
2. **Given** the data represents an observational study (no randomization), **When** the results are generated, **Then** the output explicitly states that findings represent "associations" rather than "causal effects."
3. **Given** the model includes country fixed effects, **When** the F-test for joint significance is performed, **Then** the result indicates whether the governance interaction terms are jointly significant at the p < 0.05 level.
4. **Given** the linear assumption, **When** the robustness check runs, **Then** the system tests for non-linearity (e.g., quadratic term) and reports the result.

---

### User Story 3 - Visualization and Reporting (Priority: P3)

As a researcher, I need to generate scatter plots of the residuals and a coefficient plot of the regression results, so that I can visually inspect the model fit and communicate the effect sizes clearly.

**Why this priority**: While the statistical inference is the core, visual validation is required to check for outliers or model misspecification, and visualization is necessary for the final report.

**Independent Test**: The system can be tested by verifying that the script generates two image files (`.png`) in the output directory: one scatter plot and one coefficient plot. The plots must be readable and contain axis labels derived from the variable names.

**Acceptance Scenarios**:

1. **Given** the regression results are available, **When** the visualization script runs, **Then** it generates a scatter plot with "Predicted vs. Residuals" on the axes.
2. **Given** the regression coefficients, **When** the coefficient plot is generated, **Then** it displays the CBNRM index effect (vs State-led) with error bars representing the 95% confidence interval.
3. **Given** a memory constraint (RAM < 7GB), **When** the plotting library attempts to render, **Then** it completes without crashing and uses standard CPU rendering (no GPU acceleration).

---

### Edge Cases

- What happens if a country has missing data for >20% of the time period (2000–2020)? The system must exclude such countries to prevent bias, logging the exclusion.
- How does the system handle the case where the World Bank API returns a 503 error? The script must retry up to 3 times with exponential backoff before failing gracefully and logging the error.
- What if the CBNRM policy index is constant for a specific country over time? The fixed-effects model cannot estimate the coefficient for that country; the system must flag this in the logs and exclude the variable for that specific country's contribution.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download land-use change rates from FAO STAT and specific CBNRM adoption data (or validated proxies distinct from general governance indices) from the World Bank API for all low- and middle-income countries between 2000 and 2020. It MUST derive a binary `regime_type` variable (1=CBNRM, 0=State-led) (See US-1).
- **FR-002**: System MUST merge datasets on country codes and years, excluding any records where either the outcome or predictor variable is missing (See US-1).
- **FR-003**: System MUST perform a fixed-effects panel regression with land-use change as the dependent variable and `regime_type` (CBNRM vs State-led) as the independent variable, controlling for GDP per capita and population density (See US-2).
- **FR-004**: System MUST explicitly label all statistical findings as "associational" in the output report, acknowledging the observational nature of the data (See US-2).
- **FR-005**: System MUST generate a coefficient plot and a residual scatter plot using `matplotlib` without requiring GPU acceleration (See US-3).
- **FR-006**: System MUST apply a multiple-comparison correction (Benjamini-Hochberg FDR) ONLY when ≥ 2 distinct hypothesis tests are performed (e.g., primary test + sensitivity analysis suite). Standard control variables (GDP, population) are NOT subject to this correction (See US-2).
- **FR-007**: System MUST verify that the dataset contains all required variables before initiating the regression. If a variable is missing, the system MUST gracefully degrade by excluding only the affected records and logging the specific missing variable, rather than raising a hard error (See US-1).
- **FR-008**: System MUST perform a robustness check for non-linearity (e.g., by adding a quadratic term for the CBNRM index or running a non-parametric check) to validate the linear assumption (See US-2).

### Key Entities

- **Country-Year Panel**: A unique record identified by a country code and a year, containing land-use metrics and governance indices.
- **Regime Type**: A binary variable derived from source data, classifying the management regime as 'CBNRM' (1) or 'State-led' (0). This must be an exogenous measure of policy adoption, distinct from general governance quality.
- **Land-Use Change Rate**: The annual percentage change in forest cover or land use, derived from FAO STAT.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The proportion of successfully merged country-year records is measured against the total available records in the source APIs (Target: [deferred] coverage for low/middle-income countries) (See US-1).
- **SC-002**: The statistical significance of the CBNRM coefficient (vs State-led baseline) is measured against the standard p < 0.05 threshold, with results explicitly framed as associational (See US-2).
- **SC-003**: The runtime of the entire analysis pipeline (download, merge, regress, plot) is measured against the GitHub Actions free-tier limit of 6 hours (Target: [deferred]) (See US-3).
- **SC-004**: The memory usage of the analysis script is measured against the runner limit of ~7 GB RAM (Target: [deferred]) (See US-3).
- **SC-005**: The sensitivity of the results to the inclusion of covariates is measured by comparing the CBNRM coefficient magnitude in the full model vs. a model without GDP controls (See US-2).

## Assumptions

- The World Bank Open Data API and FAO STAT provide sufficient historical data (2000–2020) for at least [deferred] low- and middle-income countries to achieve statistical power.
- A specific CBNRM adoption index or a validated proxy distinct from general governance indices is available; if only general governance indices are available, they must be explicitly validated as a proxy for CBNRM adoption before use.
- The relationship between CBNRM and land-use change is linear enough to be approximated by a standard OLS fixed-effects model for the purpose of this initial study, subject to the robustness check in FR-008.
- No GPU hardware is available or required; all statistical computations will be performed using standard CPU-optimized libraries (`statsmodels`, `pandas`, `numpy`).
- The "low- and middle-income" classification is based on the World Bank's official list for the year 2020, and countries are not re-classified mid-study.
- Any threshold for "significant" association (p < 0.05) is based on the community standard for social science research, as specified in the idea.