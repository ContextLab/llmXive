# Feature Specification: Adoption of Sustainable Agricultural Practices in Low‑Income Areas through Community Engagement

**Feature Branch**: `018-adoption-sustainable-agriculture`  
**Created**: 2026‑06‑24  
**Status**: Draft  
**Input**: User description: "Investigate what factors influence the adoption of sustainable agricultural practices in low‑income communities and how community‑engagement intensity mediates this relationship using publicly available agricultural survey data (FAO STAT, World Bank) and logistic regression analysis."  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Acquire & Pre‑process Survey Data (Priority: P1) (US-1)

A researcher needs to obtain the relevant agricultural survey dataset, filter it to low‑income countries, and prepare it for analysis.

**Why this priority**: Without reliable data the entire study cannot proceed; this is the foundational step.

**Independent Test**: The pipeline can be executed end‑to‑end to produce a cleaned CSV file containing all required variables, and the test passes if the file is generated without errors and contains ≥ 95% of all available records matching the low‑income country filter in the source API.

**Acceptance Scenarios**:

1. **Given** the World Bank LSMS (or FAO STAT) API endpoint, **When** the data‑download script is run with the filter "World Bank income classification = Low‑income", **Then** a raw dataset file is saved locally.  
2. **Given** the raw dataset, **When** the preprocessing module handles missing values, normalises categorical codes, and selects required columns, **Then** a cleaned dataset is output with no missing values for the variables listed in FR‑001.

---

### User Story 2 – Construct Community‑Engagement Score & Adoption Indicator (Priority: P2)

A researcher needs to create a composite index for community‑engagement intensity and a binary indicator for sustainable‑practice adoption.

**Why this priority**: These derived variables are the primary predictor and outcome for the regression model.

**Independent Test**: Running the "feature engineering" script on the cleaned dataset must produce two new columns (`engagement_score`, `adoption_binary`) and report reliability statistics; the test passes if the columns are generated and reliability statistics are reported (regardless of threshold achievement).

**Acceptance Scenarios**:

1. **Given** a cleaned dataset containing the survey items on collective action, **When** the composite score function is applied, **Then** a numeric `engagement_score` is added to every record.  
2. **Given** the same dataset, **When** the adoption‑definition rule (e.g. ≥ 1 sustainable practice reported) is applied, **Then** a binary `adoption_binary` column is added (1 = adopted, 0 = not adopted).

---

### User Story 3 – Fit Logistic Regression & Mediation Analysis & Generate Report (Priority: P3) (US-3)

A researcher wants to estimate the association between community‑engagement intensity and practice adoption, control for covariates, assess model performance, AND test whether community engagement mediates the relationship between other factors and adoption.

**Why this priority**: This delivers the empirical answer to the research question and produces the deliverables (coefficients, mediation effects, ROC, visualisations).

**Independent Test**: Executing the analysis script must output a regression summary, mediation analysis results, AUC value, and a PDF report; the test passes if all outputs are generated and documented, regardless of whether performance thresholds are met.

**Acceptance Scenarios**:

1. **Given** the engineered dataset, **When** the logistic regression model (statsmodels) is run with `adoption_binary` as dependent variable and `engagement_score` + covariates as predictors, **Then** a table of coefficients, odds ratios, and 95% confidence intervals is produced.
2. **Given** the fitted model, **When** the ROC curve is plotted and AUC computed, **Then** the AUC is reported (regardless of whether it meets any threshold).
3. **Given** the candidate predictors (farm size, credit access, education), **When** the mediation analysis is run (Baron & Kenny approach with Sobel test or bootstrap CI), **Then** indirect effects through engagement_score are reported with p‑values and 95% bootstrap confidence intervals for the mediation proportion.

---

### Edge Cases

- **Given** the selected dataset lacks community‑engagement variables, **When** the preprocessing module runs, **Then** the system flags this limitation, documents reduced construct validity, and proceeds with available proxy variables.
- **Given** records with > 30% missing values in any required field, **When** the cleaning module runs, **Then** those records are excluded and the exclusion count is logged.
- **Given** the sample size after filtering is insufficient to meet the events‑per‑predictor rule (5 predictors, minimum 10% event rate assumed), **When** the power analysis runs, **Then** the shortfall is documented and reported as a study limitation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download agricultural survey data from the World Bank LSMS or FAO STAT APIs given a country‑income filter.  
- **FR-002**: System MUST verify that the downloaded dataset contains all required variables: farmer age, education, farm size, credit access, sustainable‑practice adoption indicators, and community‑engagement survey items. If the primary source (World Bank LSMS) lacks required variables, the system SHALL attempt to retrieve them from alternative microdata sources (e.g., FAO FIES, national agricultural surveys) and document any data gaps.
- **FR-003**: System MUST clean the dataset by (a) imputing or removing rows with missing values, (b) normalising categorical encodings, and (c) exporting a cleaned CSV file.  
- **FR-004**: System MUST compute a composite "community‑engagement intensity" score from available survey items and report internal consistency (Cronbach's α).
- **FR-005**: System MUST create a binary "adoption" variable indicating whether a farmer uses any of the target sustainable practices (agroforestry, organic inputs, water‑conservation).  
- **FR-006**: System MUST fit a logistic regression model with `adoption_binary` as the dependent variable and `engagement_score`, farmer age, education, farm size, and credit access as independent variables.  
- **FR-007**: System MUST calculate variance‑inflation factors (VIF) for all predictors and flag any VIF ≥ 5 as a collinearity warning.  
- **FR-008**: System MUST apply false discovery rate (FDR) control using the Benjamini-Hochberg procedure (q ≤ 0.10) to all hypothesis tests and report adjusted p‑values.
- **FR-009**: System MUST evaluate model discrimination using ROC curve and report Area‑Under‑Curve (AUC).  
- **FR-010**: System MUST generate a reproducible PDF report containing (i) descriptive statistics, (ii) regression table, (iii) VIF diagnostics, (iv) ROC plot, (v) interpretation of the community‑engagement effect, AND (vi) mediation analysis results.  
- **FR-011**: System MUST construct the community‑engagement score from available proxy variables in FAO/World Bank datasets. Where direct community‑engagement items are unavailable, the system SHALL use the following proxy indicators (in priority order): () membership in farmer groups/cooperatives, (2) participation in extension programs, (3) collective action participation (e.g. shared resource management), (4) frequency of farmer‑to‑farmer knowledge exchange. If ≥3 such proxy variables exist in the dataset, they SHALL be combined into the engagement_score using a weighted sum (equal weights unless Cronbach's α < 0.70, in which case equal‑weight averaging SHALL be used). If <3 proxy variables are available, the system SHALL flag this limitation, document the reduced construct validity, and proceed with available proxies while noting this as a study constraint. This approach follows common practice in agricultural survey research where community‑engagement is operationalized via participation/collective‑action indicators (see FAO FIES methodology, World Bank LSMS surveys). (See US-2)
- **FR-012**: System MUST perform mediation analysis to test whether community‑engagement intensity mediates the relationship between predictor variables (farm size, credit access, education) and adoption outcomes. The mediation test SHALL use the Baron & Kenny approach with Sobel test or bootstrap confidence intervals with a sufficient number of resamples (≥ 1000), reporting (a) direct effect of predictors on adoption, (b) indirect effect through engagement_score, (c) total effect, and (d) proportion of effect mediated. CAVEAT: Results are interpreted as exploratory associations; causal claims require stronger identification strategies not available in observational survey data. (See US-3)

### Key Entities

- **SurveyRecord**: Represents a single farmer's survey response; key attributes include `age`, `education_level`, `farm_size_ha`, `credit_access`, `practice_adoption_flags`, `engagement_item_1…n`.  
- **EngagementScore**: Numeric composite index (0–100) derived from `engagement_item_*`.  
- **AdoptionIndicator**: Binary flag (0/1) indicating adoption of any sustainable practice.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: ≥ 95% of the required variables listed in FR‑002 are present in the downloaded raw dataset.  
- **SC-002**: Internal consistency of the community‑engagement composite score (Cronbach's α) is reported; if α < 0.70, the limitation is documented and analysis proceeds with this constraint noted.
- **SC-003**: Logistic regression model AUC is reported on the held‑out validation set; null results (AUC < 0.70) are documented as valid scientific outcomes rather than failures.
- **SC-004**: All variance‑inflation factors are < 5, confirming acceptable collinearity among predictors.
- **SC-005**: FDR correction is applied (Benjamini-Hochberg, q ≤ 0.10) and either (a) at least one predictor (community engagement) shows an FDR‑adjusted p‑value < 0.10, OR (b) a documented null result where no predictor meets this threshold is reported as a valid scientific outcome.
- **SC-006**: Power analysis (using the rule of 10 events per predictor, 5 predictors, minimum 10% event rate assumed) confirms that the effective sample size after filtering meets the minimum required for the specified number of predictors; if not, the shortfall is documented. (See US-1)

## Assumptions

- The World Bank LSMS or FAO STAT Open Data APIs provide up‑to‑date, publicly accessible surveys that include the necessary demographic and practice‑adoption variables. FAO STAT provides aggregate country-level statistics; individual-level microdata must come from World Bank LSMS, FAO FIES, or national agricultural surveys.
- Community‑engagement intensity can be validly captured by a set of ≥ 3 survey items that reflect collective decision‑making, participation in farmer groups, and shared resource management. If <3 items are available, construct validity is reduced and this limitation is documented.
- Logistic regression is an appropriate inferential framework for binary adoption outcomes given the observational nature of the data; findings will be framed as associational, not causal.
- Mediation analysis using the Baron & Kenny approach with bootstrap confidence intervals provides exploratory evidence to assess indirect effects, with explicit caveats about unmeasured confounding in non-experimental data.
- Sample size after low‑income country filtering will be sufficient to satisfy the events‑per‑predictor rule; if not, the limitation will be reported rather than ignored.
- Standard statistical software (Python pandas, statsmodels, matplotlib) is available in the execution environment.
- **Data Source Limitation**: FAO STAT provides aggregate country-level data only. Individual-level survey data with community engagement items must be sourced from World Bank LSMS, FAO FIES, or equivalent microdata surveys. The system SHALL attempt multiple sources and document which sources provided usable data.