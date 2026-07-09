# Feature Specification: The Role of Temporal Discounting in Procrastination on Cognitive Tasks

**Feature Branch**: `001-temporal-discounting-procrastination`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "To what extent does working memory load moderate the relationship between individual temporal discounting rates and procrastination behaviors on cognitively demanding tasks?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The research pipeline must successfully ingest, harmonize, and process raw data from three distinct sources (Delay Discounting, Procrastination Scale, and n-back task) into a unified analysis-ready dataset. This is the foundational step; without a clean, merged dataset containing individual discount rates (k), procrastination scores, and working memory metrics, no statistical analysis can occur.

**Why this priority**: This is the minimum viable product (MVP) for the research phase. If data cannot be loaded and harmonized, the project cannot proceed to hypothesis testing. It is independent of the statistical modeling complexity.

**Independent Test**: The pipeline can be fully tested by executing the data ingestion script and verifying the output DataFrame contains the required columns (`discount_rate_k`, `procrastination_score`, `wm_accuracy`, `wm_rt`, `age`, `gender`, `education`) with zero null values in the key predictor/outcome columns after imputation or filtering.

**Acceptance Scenarios**:

1. **Given** raw ARFF/CSV files from validated sources exist locally, **When** the ingestion script runs, **Then** a single pandas DataFrame is produced with harmonized participant IDs and all required variables present.
2. **Given** the raw discounting data contains indifference points, **When** the hyperbolic model fitting script runs, **Then** a numeric `discount_rate_k` is calculated for each participant, or the participant is flagged/excluded if fitting fails.
3. **Given** mixed data types across sources (e.g., different date formats or ID schemes), **When** the harmonization step runs, **Then** the script successfully merges the datasets using a common key (e.g., `participant_id`) without dropping >10% of the initial sample due to ID mismatch.

---

### User Story 2 - Moderation Regression Analysis (Priority: P2)

The system must execute a statistical moderation analysis (OLS regression) to test the primary hypothesis: that working memory load moderates the relationship between temporal discounting and procrastination. This includes calculating the interaction term and determining statistical significance.

**Why this priority**: This delivers the core scientific value of the project. It directly answers the research question. It depends on the data being ready (US-1) but is independent of robustness checks (US-3).

**Independent Test**: The analysis can be fully tested by running the regression script and verifying that the output includes a coefficient and p-value for the interaction term (`log(k) * wm_metric`), and that the model assumptions (normality, multicollinearity) are reported.

**Acceptance Scenarios**:

1. **Given** a clean dataset with calculated variables, **When** the OLS regression model is fitted, **Then** the output includes the main effects (discount rate, WM metric) and the interaction effect with corresponding p-values.
2. **Given** the interaction term is calculated, **When** the model summary is generated, **Then** the p-value for the interaction term is explicitly reported to determine if `p < 0.05`.
3. **Given** the regression assumptions are checked, **When** the diagnostic tests run, **Then** the Variance Inflation Factor (VIF) for all predictors is reported, and any collinearity issues are flagged if VIF > 5.

---

### User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

The system must perform robustness checks, specifically bootstrapping with a sufficient number of resamples to verify the stability of the interaction effect. Additionally, an exploratory sensitivity analysis will be performed on the working memory load threshold (if a binary load classification is used for subgroup analysis) or the discount rate cutoff to ensure findings are not artifacts of specific cutoffs. This ensures the findings are not artifacts of a specific sample or arbitrary cutoff.

**Why this priority**: This adds scientific rigor and defensibility to the results. It is a "nice-to-have" for the initial pass but critical for publication-quality output. It depends on the primary analysis (US-2) being successful.

**Independent Test**: The robustness check can be independently tested by running the bootstrapping script and verifying that the confidence intervals for the interaction coefficient do not include zero (if the primary effect was significant) or that the stability metric is calculated.

**Acceptance Scenarios**:

1. **Given** the primary OLS model results, **When** the bootstrapping routine runs (1000 resamples), **Then** a 95% confidence interval for the interaction coefficient is generated and reported.
2. **Given** a potential threshold for "high" vs "low" working memory load (if applied for exploratory analysis), **When** the sensitivity analysis runs, **Then** the interaction effect is re-evaluated across distinct threshold values (median, median ± 0.05*SD, median ± 0.10*SD) and the variation in effect size is reported.
3. **Given** the full analysis pipeline, **When** executed on a standard CPU, **Then** the total runtime is ≤ 6 hours and memory usage remains ≤ 7 GB.

### Edge Cases

- **What happens when** the hyperbolic model fitting for discount rates fails for a specific participant (e.g., no indifference points found)?
  - *Handling*: The participant is excluded from the analysis, and a warning log is generated with the count of excluded participants.
- **How does the system handle** missing data in covariates (age, gender) or the primary outcome?
  - *Handling*: The system applies listwise deletion for missing primary variables or a defined imputation strategy (e.g., mean imputation for covariates) if the missingness is < 5%, otherwise it flags the dataset as insufficient.
- **What happens when** the VIF indicates high multicollinearity between the main effects and the interaction term?
  - *Handling*: The system centers the predictors (mean-centering) before creating the interaction term to mitigate non-essential multicollinearity and re-runs the diagnostic.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST ingest data from validated datasets containing Delay Discounting, Procrastination Scale, and n-back task constructs. Before analysis, the system MUST verify the presence of all core constructs (discount rate, procrastination score, WM metrics) in the loaded data. (See US-1)
- **FR-002**: The system MUST calculate individual temporal discount rates (k) by fitting the hyperbolic model `V = A / (1 + k·D)` to indifference points using `scipy.optimize.curve_fit`. (See US-1)
- **FR-003**: The system MUST extract working memory capacity metrics (accuracy and reaction time) from the n-back task dataset and harmonize them with the other variables. (See US-1)
- **FR-004**: The system MUST construct an OLS regression model with procrastination score as the dependent variable, and log-transformed discount rate (log(k)), continuous working memory metric (accuracy or RT), and their interaction term (log(k) * wm_metric) as predictors. (See US-2)
- **FR-005**: The system MUST calculate and report the Variance Inflation Factor (VIF) for all predictors to detect multicollinearity, flagging any VIF > 5. (See US-2)
- **FR-006**: The system MUST perform a bootstrapping analysis with a sufficient number of resamples to generate confidence intervals for the interaction coefficient. (See US-3)
- **FR-007**: The system MUST execute an exploratory sensitivity analysis sweeping the cutoff value for working memory load (median, median ± 0.05*SD(WM), median ± 0.10*SD(WM)) and discount rate (median of log(k), median ± 0.05*SD(log(k)), median ± 0.10*SD(log(k))) and report the variation in the interaction p-value. (See US-3)
- **FR-008**: The system MUST halt the analysis if core constructs (discount rate, procrastination score, WM metrics) are missing from the dataset. (See US-1)
- **FR-009**: The system MUST ensure that data harmonization drops no more than 10% of the initial sample due to ID mismatch. If missing core constructs cause a drop >10%, the system MUST halt. If missing covariates (age, gender) cause a drop >10%, the system MUST proceed with a reduced model excluding those covariates. (See US-1)
- **FR-010**: The system MUST complete the entire analysis pipeline within 6 hours of runtime and 7 GB of memory usage on a standard CPU environment. (See US-3)

### Key Entities

- **Participant**: An individual subject in the study, uniquely identified by `participant_id`, possessing attributes for age, gender, education, discount rate, procrastination score, and WM metrics.
- **Discount Rate (k)**: A derived numeric variable representing the steepness of temporal discounting for a participant, calculated via hyperbolic fitting.
- **Procrastination Score**: A derived numeric variable representing the total score on the Procrastination Scale for a participant.
- **Working Memory Metric**: A derived variable (accuracy or RT) representing the participant's cognitive load capacity.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The primary interaction effect (log(k) × continuous WM metric) is measured against a statistical significance threshold of p < 0.05 to determine hypothesis support. (See US-2)
- **SC-002**: The stability of the interaction effect is measured against a confidence interval derived from bootstrap resamples; the interval must not cross zero if the primary effect is significant. (See US-3)
- **SC-003**: Multicollinearity is measured against a VIF threshold of 5; all predictors must have VIF < 5 to validate the model's independence assumptions. (See US-2)
- **SC-004**: The sensitivity of the results is measured against the variation in the interaction p-value across the defined threshold sweeps (median, median ± 0.05*SD, median ± 0.10*SD); instability is flagged if the 95% CI for the interaction effect crosses zero in more than 50% of the swept thresholds. (See US-3)
- **SC-005**: The total analysis runtime is measured against a practical upper-bound limit on a CPU-only GitHub Actions runner; the pipeline must complete within this bound. (See US-3)

## Assumptions

- **Dataset-variable fit**: The analysis requires the presence of core constructs (discount rate, procrastination score, WM metrics) in the loaded data. If critical covariates (age, gender) are missing, the analysis will proceed with a reduced model excluding them. If core constructs are absent, the analysis will halt.
- **Inference framing**: The analysis is framed as observational and correlational. No causal claims regarding the effect of WM load on the discounting-procrastination link will be made, as there is no random assignment to load conditions in the aggregated dataset; findings will be reported as associations.
- **Multiplicity & power**: The study acknowledges that interaction effects in psychology are often small (f² < 0.02). The sample size may be insufficient to detect such small effects with high power; thus, the study is framed as exploratory regarding the interaction magnitude.
- **Threshold justification & sensitivity**: The sensitivity analysis for the WM load threshold (if a binary split is used for exploratory analysis) uses the median of the continuous WM metric as the baseline, with sensitivity sweeps at ±0.05*SD and ±0.10*SD around this baseline.
- **Measurement validity**: The study assumes the "Procrastination Scale" and "n-back" datasets used are from validated instruments with established reliability (Cronbach's α > 0.7) in prior literature.
- **Predictor collinearity**: The study assumes that while discount rate and WM load are distinct constructs, the interaction term may introduce multicollinearity, necessitating mean-centering of predictors before interaction creation.
- **Compute feasibility**: The entire analysis is assumed to run on a CPU-only environment with ≤ 7 GB RAM. No GPU-accelerated libraries or large language models are required; the analysis relies on `scipy`, `statsmodels`, and `pandas` which are CPU-tractable.