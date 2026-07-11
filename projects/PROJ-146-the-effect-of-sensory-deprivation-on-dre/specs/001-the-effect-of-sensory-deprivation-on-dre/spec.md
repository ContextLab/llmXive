# Feature Specification: The Effect of Sensory Deprivation on Dream Recall and Bizarreness (Simulation Study)

**Feature Branch**: `001-sensory-deprivation-dreams`  
**Created**: 2026-07-04  
**Status**: Draft  
**Input**: User description: "Does experimentally induced brief sensory deprivation immediately before sleep increase the likelihood of dream recall and the subjective bizarreness of recalled dream content compared to a control condition with normal sensory input?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Synthetic Simulation Fallback (Priority: P1)

The system MUST successfully ingest dream data from a CSV source or, if specific "sensory deprivation" metadata is absent, generate a statistically valid synthetic dataset based on published floatation therapy parameters to enable downstream analysis. This project is explicitly defined as a **Simulation Study** to validate statistical pipelines and explore hypothetical effect sizes, as no public dataset with experimentally controlled sensory deprivation conditions linked to standardized bizarreness scores currently exists.

**Why this priority**: Without a structured dataset containing the predictor (sensory condition) and outcomes (recall/bizarreness), no statistical analysis can occur. This is the foundational block; the synthetic data generation path is the primary mechanism for this study to validate the analysis pipeline's ability to detect effects under known ground truths.

**Independent Test**: The pipeline can be tested by running the data loading script against a mock CSV or a generated synthetic CSV and verifying the output dataframe contains the required columns (`condition`, `recall`, `bizarreness`, `participant_id`) with non-null values.

**Acceptance Scenarios**:

1. **Given** a CSV file exists but lacks "sensory deprivation" tags, **When** the ingestion script runs, **Then** it automatically triggers the synthetic data generator using parameters (Extended isolation in conditions of darkness and silence.) and outputs a dataset with N=200 simulated participants.
2. **Given** the synthetic generator is triggered, **When** it creates data, **Then** it ensures the system generates datasets with *multiple* ground truths to validate Type I and Type II error rates:
   - Scenario A: Positive effect (Cohen's d = 0.5)
   - Scenario B: Null effect (Cohen's d = 0.0)
   - Scenario C: Negative effect (small magnitude)
   The system MUST report whether the statistical model correctly identifies the presence or absence of an effect in each scenario.
3. **Given** a valid CSV subset with explicit "sensory deprivation" metadata (if available), **When** the ingestion script runs, **Then** it filters and loads exactly those records, preserving the `recall` and `bizarreness` scores.

---

### User Story 2 - Mixed-Effects Statistical Modeling (Priority: P1)

The system MUST fit a mixed-effects logistic regression for dream recall (binary outcome) and a linear mixed-effects model for dream bizarreness (ordinal/continuous outcome), treating participant ID as a random intercept and sensory condition as a fixed effect. Additionally, the system MUST perform a robustness check using an ordinal mixed-effects model (cumulative link mixed model) to ensure validity for the Likert-scale data.

**Why this priority**: This directly addresses the research question's core hypothesis. The statistical model is the mechanism that translates raw data into the "odds ratios" and "coefficients" required to answer the question. The ordinal model check ensures the statistical method matches the data type (ordinal vs. continuous).

**Independent Test**: The analysis script can be tested by running it on a small, hardcoded dataset with known effect sizes and verifying that the output JSON contains the correct model coefficients (within floating-point tolerance) and p-values.

**Acceptance Scenarios**:

1. **Given** a dataset with 2 conditions and repeated measures per participant, **When** the logistic regression model runs, **Then** it outputs an odds ratio for the sensory deprivation condition with a confidence interval and a p-value.
2. **Given** a dataset with recalled dreams only, **When** the linear mixed-effects model runs, **Then** it outputs a beta coefficient for the sensory deprivation condition and a corresponding p-value.
3. **Given** the model fits, **When** the results are generated, **Then** they are formatted as a table including fixed effects estimates, standard errors, and degrees of freedom.
4. **Given** a dataset with ordinal bizarreness scores (1-7), **When** the ordinal mixed-effects model runs, **Then** it outputs a cumulative log-odds ratio and a p-value, which are compared against the linear model results to assess robustness.

---

### User Story 3 - Robustness and Sensitivity Analysis (Priority: P2)

The system MUST perform a sensitivity analysis by varying the definition of "sensory deprivation" (strict vs. moderate vs. partial) and a bootstrap validation (sufficient resamples for robustness) to verify the stability of the effect estimates. This multi-level sweep is required to determine the "dose-response" relationship of sensory deprivation, as the exact threshold of "deprivation" is ambiguous in the literature.

**Why this priority**: The idea explicitly requires robustness checks. Without these, the findings are fragile. This step ensures the results are not artifacts of a single arbitrary threshold or specific sample configuration.

**Independent Test**: The script can be tested by manually altering a threshold parameter in the configuration and verifying the output logs show the recalculated p-values and effect sizes for the new threshold.

**Acceptance Scenarios**:

1. **Given** the primary model results, **When** the sensitivity analysis runs with a relaxed definition of deprivation, **Then** it outputs a comparison table showing how the odds ratio changes (e.g., varying magnitudes) across the defined thresholds (100%, 70%, 40%).
2. **Given** the primary model results, **When** the 1,000-iteration bootstrap runs, **Then** it outputs a bootstrap confidence interval that overlaps with the original parametric CI.
3. **Given** the analysis completes, **When** the final report is generated, **Then** it includes a "Robustness" section summarizing whether the main findings hold across different thresholds.

---

### Edge Cases

- **What happens when no real-world data exists?** The system MUST default to the synthetic data generation path and clearly flag the results as "Simulation-based" in the final report.
- **How does the system handle zero dream recall in a condition?** The logistic regression MUST use a penalized likelihood or Firth correction to avoid infinite odds ratios if a condition has **zero count of recalled dreams (count=0)**.
- **What if the sample size is too small for mixed-effects?** The system MUST detect if the number of participants is < 10 and issue a warning, potentially falling back to a fixed-effects model or bootstrapping only.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST ingest dream data from a CSV source or generate a synthetic dataset with columns for `condition`, `recall` (binary), `bizarreness` (1-7), and `participant_id` (See US-1).
- **FR-002**: The system MUST fit a mixed-effects logistic regression model with `recall` as the outcome and `condition` as the fixed effect, including `participant_id` as a random intercept (See US-2).
- **FR-003**: The system MUST fit a linear mixed-effects model for `bizarreness` scores among recalled dreams, with `condition` as the fixed effect and `participant_id` as a random intercept (See US-2).
- **FR-004**: The system MUST perform a sensitivity analysis by sweeping the "sensory deprivation" definition threshold across exactly three values: **strict ([deferred] isolation)**, **moderate ([deferred] isolation)**, and **partial ([deferred] isolation)**, and report the variation in effect estimates (See US-3).
- **FR-005**: The system MUST execute a non-parametric bootstrap with a sufficient number of resamples to ensure stable statistical estimates to generate stability intervals for the primary effect estimates (See US-3).
- **FR-006**: The system MUST output a final report containing odds ratios, beta coefficients, % confidence intervals, and p-values for all models (See US-2).
- **FR-007**: The system MUST explicitly frame all findings as "associational" in the report text, avoiding causal language unless randomization is confirmed in the metadata (See US-2).
- **FR-008**: The system MUST fit an ordinal mixed-effects model (cumulative link mixed model) for `bizarreness` as a robustness check against the linear mixed-effects model (See US-2).

### Key Entities

- **DreamRecord**: Represents a single sleep episode, containing attributes for sensory condition, recall status, bizarreness score, and participant ID.
- **StatisticalModel**: Represents the fitted model object, containing attributes for fixed effects estimates, random effects variance, and goodness-of-fit metrics.
- **SensitivityResult**: Represents the output of the threshold sweep, containing attributes for the specific threshold value used and the resulting model statistics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of nights with reported dream recall is measured against the control condition to determine the odds ratio (See US-2).
- **SC-002**: The average subjective bizarreness score is measured against the control condition to determine the beta coefficient (See US-2).
- **SC-003**: The stability of the effect estimates is measured against bootstrap resamples to ensure the 95% CI does not cross zero (See US-3).
- **SC-004**: The variation in effect estimates is measured across the sensitivity analysis thresholds (strict vs. moderate vs. partial) to ensure the headline finding remains consistent (See US-3).
- **SC-005**: The total computation time is measured against the GitHub Actions time limit to ensure the full pipeline (data generation, modeling, bootstrapping) completes successfully (See US-1).

## Assumptions

- The DreamBank dataset (or a suitable open-access sleep diary) will either contain explicit "sensory deprivation" tags or the synthetic data generator will be the primary source of truth for the analysis.
- The "bizarreness" score is treated as a continuous variable for the linear mixed-effects model, assuming the 1-7 Likert scale approximates interval data for the purpose of this analysis, with an ordinal model used for robustness.
- The "sensory deprivation" condition in the synthetic data is modeled with a **hypothetical** effect size (Cohen's d = 0.5) for pipeline stress-testing, acknowledging this is an assumption for the simulation and not a claim derived from floatation therapy literature (which lacks consensus on dream bizarreness).
- The analysis will run on a CPU-only environment (GitHub Actions free tier), so no GPU-accelerated deep learning methods will be used; all statistical modeling will rely on `statsmodels` or `scikit-learn` which are CPU-tractable.
- The study design is observational or quasi-experimental (based on existing logs or simulation), so all reported relationships are framed as associational, not causal.
- The sample size for the synthetic data is fixed at N=200, which is derived from a standard power analysis for mixed-effects models with a medium effect size (d=0.5), alpha=0.05, and desired power=0.80.
- The "sensory deprivation" definition sweep will test exactly three thresholds: **strict (complete isolation)**, **moderate ([deferred] isolation)**, and **partial ([deferred] isolation)** to satisfy the sensitivity analysis requirement and enable a dose-response analysis.