# Feature Specification: The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

**Feature Branch**: `001-simulated-social-comparison-self-esteem`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "How does exposure to idealized avatars in virtual reality environments affect self-esteem, and does individual social comparison tendency moderate this relationship?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Discovery and Validation (Priority: P1)

As a researcher, I need to locate and validate public datasets containing self-esteem measures (Rosenberg Self-Esteem Scale), social comparison orientation measures (Iowa-Netherlands Comparison Orientation Measure), AND longitudinal self-esteem data (pre/post) OR verify that a synthetic dataset generation path is required.

**Why this priority**: Without valid data sources (real or synthetic with known ground truth), no analysis can proceed. This is the foundational prerequisite for all downstream work.

**Independent Test**: Can be fully tested by successfully querying HuggingFace Datasets, OpenML, and Open Science Framework repositories and documenting either: (a) at least one real dataset with N ≥ 100 participants containing RSES, INCOM, and pre/post scores, OR (b) a successful initialization of the synthetic data generator with defined ground-truth parameters.

**Acceptance Scenarios**:

1. **Given** the researcher has access to HuggingFace Datasets, OpenML, and Open Science Framework, **When** they query for datasets containing RSES, INCOM, and pre/post self-esteem scores, **Then** at least one dataset with N ≥ 100 participants is identified and documented as a valid source for empirical inquiry.
2. **Given** no real VR-specific combined datasets with longitudinal data exist, **When** the researcher triggers the fallback, **Then** the system initializes a synthetic data generator configured with known ground-truth effect sizes (interaction β = 0.2) and explicitly labels the output as "Pipeline Validation Only," confirming that the real-world research question cannot be answered by this path.

---

### User Story 2 - Statistical Analysis Pipeline (Priority: P2)

As a researcher, I need to preprocess the identified (validated) datasets and fit a linear regression model (self-esteem_change ~ avatar_condition + comparison_tendency + interaction) so that I can test the main research hypothesis about VR exposure effects and moderation.

**Why this priority**: The statistical analysis is the core research activity that produces the primary findings. Without this, the research question cannot be answered.

**Independent Test**: Can be fully tested by running the complete analysis pipeline on a sample dataset (real or synthetic) and producing reproducible output artifacts (a CSV file containing regression coefficients and a JSON file containing diagnostic metrics) within ≤6 hours on CPU-only hardware.

**Acceptance Scenarios**:

1. **Given** a validated dataset with ≥100 participants (real or synthetic), **When** the analysis pipeline processes missing values using Multiple Imputation by Chained Equations (MICE) for missingness < 20%, **Then** at least 95% of records have complete data after preprocessing, and rows with > 20% missingness in key variables are excluded and reported.
2. **Given** the preprocessed data, **When** the linear regression model is fitted using 'avatar_condition' (normalized to 0/1 if binary, or continuous if continuous) and 'comparison_tendency', **Then** all model assumptions are validated (normality of residuals via Shapiro-Wilk p > 0.05, homoscedasticity via Breusch-Pagan p > 0.05, VIF < 5) and results are produced.
3. **Given** the regression results, **When** the interaction effect is tested, **Then** the effect size estimate with 95% confidence interval is generated, and the interpretation is framed as 'Empirical Association' for real data or 'Simulated Causal Effect' for synthetic data.

---

### User Story 3 - Methodological Robustness and Sensitivity Analysis (Priority: P3)

As a researcher, I need to conduct sensitivity analyses including bootstrap resampling (sufficient iterations to ensure stable estimates) and threshold sweeps so that I can demonstrate the stability and validity of the findings under different analytical conditions.

**Why this priority**: Sensitivity analysis strengthens the credibility of findings and addresses methodological soundness concerns, but can proceed after core analysis is complete.

**Independent Test**: Can be fully tested by executing bootstrap resampling and threshold sensitivity sweeps on the fitted model and documenting how parameter recovery error (for synthetic data) or significance stability (for real data) varies across different cutoff values.

**Acceptance Scenarios**:

1. **Given** the fitted regression model, **When** Multiple bootstrap iterations are executed, **Then** the stability of the interaction effect is quantified with confidence intervals where the CI width variance is < 0.01.
2. **Given** the synthetic dataset (if used), **When** the system compares estimated coefficients to known ground-truth values, **Then** the parameter recovery error (Bias = |beta_hat - beta_true|) is calculated and reported; if Bias > 0.05, the pipeline is flagged as failing recovery.
3. **Given** multiple hypothesis tests are performed, **When** family-wise error correction is applied, **Then** adjusted p-values are reported alongside unadjusted values.

---

### Edge Cases

- What happens when no public datasets containing RSES, INCOM, and pre/post self-esteem measures are found after systematic search of HuggingFace Datasets, OpenML, and Open Science Framework? -> System triggers synthetic data generation (FR-011) and labels results as "Pipeline Validation Only".
- How does System handle missing data exceeding 20% in key variables (self-esteem or social comparison measures)? -> System excludes the affected rows and reports the exclusion count (FR-013).
- What happens when the interaction effect in the regression model is not statistically significant (p > 0.05)? -> System reports the non-significant result with the full confidence interval and frames it as "No evidence of moderation found".
- How does System handle collinearity diagnostics showing VIF ≥ 5 between predictor variables? -> System flags the multicollinearity and frames the interpretation descriptively without claiming independent predictive effects.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST query HuggingFace Datasets, OpenML, and Open Science Framework repositories to identify datasets containing RSES, INCOM, AND longitudinal self-esteem data (pre/post) with N ≥ 100 participants (See US-1)
- **FR-002**: System MUST preprocess survey data by cleaning missing values using Multiple Imputation by Chained Equations (MICE) for missingness < 20%, and exclude rows with > 20% missingness in key variables, then compute change scores (post-pre) for self-esteem measures. If 'avatar_condition' is binary, normalize to 0/1; if continuous, retain as is (See US-2)
- **FR-003**: System MUST fit a linear regression model with self-esteem_change as outcome and avatar_condition (continuous exposure intensity OR binary indicator 0/1), comparison_tendency, and their interaction as predictors. The interpretation of the interaction term MUST adapt based on the variable type (linear dose-response vs. group difference) (See US-2)
- **FR-004**: System MUST validate model assumptions using Shapiro-Wilk test (p > 0.05) for normality of residuals, Breusch-Pagan test (p > 0.05) for homoscedasticity, and VIF < 5 for multicollinearity (See US-2)
- **FR-005**: System MUST execute bootstrap resampling with exactly 1,000 iterations to estimate stability of the interaction effect (See US-3)
- **FR-006**: System MUST apply family-wise error correction (Bonferroni or Holm-Bonferroni) when multiple hypothesis tests are performed (See US-3)
- **FR-007**: System MUST conduct two distinct sensitivity analyses: (1) Test stability of significance across p-value thresholds {0.05, 0.10} and report if the conclusion (significant vs. non-significant) changes; (2) Test parameter recovery stability across imputation fraction limits {0.05, 0.10, 0.15, 0.20} and report the Bias (|beta_hat - beta_true|) for synthetic data or coefficient variance for real data (See US-3)
- **FR-008**: System MUST document all code and data versions in a GitHub repository with requirements.txt for reproducibility (See US-1)
- **FR-009**: System MUST verify that the dataset contains ALL required variables (avatar exposure condition, pre/post self-esteem, social comparison tendency) before analysis proceeds; if missing, the system MUST trigger synthetic data generation (See US-1)
- **FR-010**: System MUST frame all findings as ASSOCIATIONAL rather than causal when the design is observational (secondary analysis without randomization), or as 'simulated causal effect' when using synthetic data (See US-2)
- **FR-011**: System MUST generate a synthetic dataset with N ≥ 100 participants, known ground-truth effect sizes (interaction β = 0.2), and pre/post self-esteem scores if no real dataset meeting FR-001 criteria is found. The output MUST be explicitly labeled "Pipeline Validation Only" and MUST NOT be used to answer the real-world research question regarding the effect of VR on self-esteem in the general population (See US-1)
- **FR-012**: System MUST report which data path was taken (Real Data vs. Synthetic Data) and the corresponding interpretation framing (Empirical Association vs. Pipeline Validation) in the final results. If Synthetic Data is used, the report MUST state that the results validate the statistical pipeline's ability to recover known parameters but do not constitute empirical evidence for the real-world research question (See US-1, US-2)
- **FR-013**: System MUST exclude rows with > 20% missingness in key variables and report the exact count of excluded rows in the final output (See US-2)

### Key Entities *(include if feature involves data)*

- **Dataset**: Psychological survey data containing participant responses to RSES and INCOM measures, with attributes including participant ID, self-esteem scores (pre/post), social comparison tendency scores, and exposure condition (or synthetic generation parameters)
- **Regression Model**: Statistical model object containing coefficients, standard errors, p-values, confidence intervals, and assumption validation diagnostics

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset discovery success is measured against the requirement of identifying at least one dataset with N ≥ 100 participants containing RSES, INCOM, and pre/post scores, OR successful initialization of synthetic generation (See US-1)
- **SC-002**: Analysis pipeline execution time is measured against a predefined CPU-only compute constraint on GitHub Actions free-tier runner, as established by the platform's resource limits. (See US-2)
- **SC-003**: Model validity is measured against assumption validation criteria (Shapiro-Wilk p > 0.05, Breusch-Pagan p > 0.05, VIF < 5) (See US-2)
- **SC-004**: Result stability is measured against bootstrap resampling confidence intervals from 1,000 iterations where the CI width variance is < 0.01 (See US-3)
- **SC-005**: Methodological validity is measured against Parameter Recovery for synthetic data (Bias = |beta_hat - beta_true| < 0.05) OR Confidence Interval Width for real data (CI width < 0.2). Post-hoc power analysis is explicitly excluded from this assessment. (See US-2, US-3)

## Assumptions

- Public datasets containing RSES, INCOM, and longitudinal self-esteem data may not exist; if none are found, the system MUST proceed with FR-011 to generate a synthetic dataset with known ground-truth parameters, explicitly labeling the results as "Pipeline Validation Only" and NOT as an answer to the real-world research question.
- The analysis runs on CPU-only hardware (GitHub Actions free-tier: multiple CPU cores, ~7 GB RAM, ~14 GB disk, ≤6 h per job) without GPU/CUDA accelerators.
- RSES and INCOM are validated instruments with citable validation literature (no new citations will be fabricated).
- The research design is observational (secondary analysis) OR simulated (synthetic data); findings from real data are framed as associational, while synthetic data findings are framed as 'simulated causal effects' based on ground truth, with no claim of external validity for the latter.
- If key variables have > 20% missingness, rows are excluded (FR-013); if key variables are missing entirely, synthetic data is generated (FR-011).
- Any thresholds introduced in the analysis will carry justification naming community-standard basis and require sensitivity analysis.
- Predictor collinearity will be checked via VIF; if VIF ≥ 5, joint relationships will be framed descriptively without claiming independent predictive effects.
- The VR exposure condition is modeled as a continuous variable representing exposure intensity if the source data provides it; if a real dataset provides a binary condition, it is treated as a discrete approximation (0/1) without median splitting, and the interaction interpretation is adjusted accordingly.
- The system does NOT rely on post-hoc power analysis. For synthetic data, validity is measured by Parameter Recovery (Bias < 0.05). For real data, validity is measured by Confidence Interval Width (< 0.2).