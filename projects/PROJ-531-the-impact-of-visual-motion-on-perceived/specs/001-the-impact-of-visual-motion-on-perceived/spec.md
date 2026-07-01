# Feature Specification: The Impact of Visual Motion on Perceived Agency in Virtual Interactions

**Feature Branch**: `001-visual-motion-agency`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "How do visual motion characteristics of virtual avatars (e.g., smoothness, responsiveness delay, and anticipatory lead cues) influence users' subjective sense of agency during virtual interactions?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing (Priority: P1)

As a researcher, I need to download and preprocess publicly available human-avatar interaction datasets so that I can extract motion features and agency scale responses for analysis.

**Why this priority**: This is the foundational step without which no analysis can occur. The entire research pipeline depends on obtaining clean, structured data with both predictor variables (motion parameters) and outcome variables (agency ratings).

**Independent Test**: Can be fully tested by successfully downloading a dataset (or generating synthetic data), extracting the required motion and agency variables, and producing a structured CSV/parquet file with ≥100 complete observations. Delivers usable analysis-ready data even if no modeling occurs.

**Acceptance Scenarios**:

1. **Given** a publicly available dataset URL from any repository (OpenML, HuggingFace, OSF, GitHub, etc.) containing human-avatar interaction logs and questionnaire responses, **When** the data download script executes, **Then** the dataset is stored locally with ≥100 complete observations containing motion features (latency, smoothness, lead time) and agency scale scores.
2. **Given** a raw dataset with missing values, **When** the preprocessing pipeline runs, **Then** observations with missing motion or agency variables are removed, leaving ≥80 complete cases for analysis.
3. **Given** Likert-scale agency questionnaire responses, **When** the outcome variable is constructed, **Then** the agency score is computed as a continuous variable (mean of items or summed scale) with documented scoring method.

---

### User Story 2 - Statistical Modeling and Hypothesis Testing (Priority: P2)

As a researcher, I need to fit regression and random forest models to quantify relationships between motion features and agency ratings so that I can identify which motion characteristics predict perceived agency.

**Why this priority**: This is the core research activity that answers the primary research question. Without modeling, there is no evidence for design guidelines.

**Independent Test**: Can be fully tested by fitting at least one regression model and one random forest model, producing feature importance scores and statistical significance tests, even without visualization or reporting.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset with motion features and agency scores, **When** multiple linear regression is fitted, **Then** coefficient estimates, standard errors, and p-values are computed for each motion feature (latency, smoothness, lead time).
2. **Given** the same dataset, **When** a random forest model is trained with 5-fold cross-validation, **Then** feature importance scores and out-of-sample performance metrics (R², RMSE) are computed.
3. **Given** ≥3 motion features are tested for association with agency, **When** statistical significance testing is performed, **Then** a multiple-comparison correction (Bonferroni or Benjamini-Hochberg) is applied to control family-wise error rate.

---

### User Story 3 - Visualization and Interpretation (Priority: P3)

As a researcher, I need to generate visualizations and interpret model results so that I can communicate findings about which motion features predict agency and support evidence-based design recommendations.

**Why this priority**: This enables dissemination of findings to stakeholders (designers, VR developers) who need actionable insights. Without visualization, results remain inaccessible to non-technical audiences.

**Independent Test**: Can be fully tested by generating at least 3 plots (scatter plots of motion features vs. agency, feature importance ranking, partial dependence plot) and producing a summary interpretation, even without full report generation.

**Acceptance Scenarios**:

1. **Given** fitted regression and random forest models, **When** visualization scripts execute, **Then** at least 3 plots are generated: scatter plot of each motion feature vs. agency scores, feature importance bar chart, and partial dependence plot for the top predictor.
2. **Given** statistically significant predictors from the analysis, **When** interpretation is documented, **Then** the direction and magnitude of each predictor's relationship with agency is described in plain language.
3. **Given** null results (no motion features significantly predict agency), **When** interpretation is documented, **Then** the finding is framed as evidence that agency may depend on other factors (task design, prior experience) rather than motion parameters alone.

---

### Edge Cases

- What happens when the downloaded dataset has fewer than 50 complete observations? **Then** the analysis is aborted with an error message recommending alternative data sources or synthetic data generation, as statistical power would be insufficient for meaningful inference.
- How does system handle datasets where motion features are highly collinear (e.g., smoothness and jerk metric)? **Then** a variance inflation factor (VIF) diagnostic is computed, and if VIF ≥5 for any predictor, the feature is excluded from multivariate models with documentation of the collinearity issue.
- What happens when agency questionnaire items use different scales across studies? **Then** all items are standardized to a 0–1 range before aggregation, with the standardization method documented in the preprocessing log.
- How does system handle datasets where the outcome variable (agency) has low variance (e.g., most participants rate agency as 4/5)? **Then** the analysis is flagged with a warning that low outcome variance limits detection of predictor effects.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and store publicly available human-avatar interaction datasets from any publicly accessible repository (e.g., OpenML, HuggingFace, OSF, GitHub) containing both motion telemetry logs and questionnaire responses, OR generate synthetic data if no real dataset exists (See US-1)
- **FR-002**: System MUST extract motion features including response latency (ms), trajectory smoothness (jerk metric), and anticipatory lead time (ms) from interaction logs (See US-1)
- **FR-003**: System MUST preprocess agency scale questionnaire responses into a continuous outcome variable using validated scoring methods for the specific instrument used (See US-1)
- **FR-004**: System MUST fit multiple linear regression and random forest models with 5-fold cross-validation to predict agency scores from motion features (See US-2)
- **FR-005**: System MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) when testing ≥3 motion features for association with agency (See US-2)
- **FR-006**: System MUST compute variance inflation factor (VIF) diagnostics for all motion predictors and flag collinearity when VIF ≥5 (See US-2)
- **FR-007**: System MUST generate scatter plots of each motion feature vs. agency scores, feature importance bar charts, and partial dependence plots for the top predictor (See US-3)
- **FR-008**: System MUST frame all reported associations as correlational rather than causal when the dataset is observational (no random assignment) (See US-2)
- **FR-009**: System MUST flag and exclude datasets that use agency questionnaires without validated instruments (See US-1)
- **FR-010**: System MUST perform sensitivity analysis sweeping decision thresholds (absolute regression coefficient magnitude ∈ {0.01, 0.05, 0.1}) and report how significance rates (p-values) vary across cutoffs to ensure robustness of inference (See US-2)
- **FR-011**: System MUST generate synthetic human-avatar interaction data with known ground-truth motion-agency relationships if no real dataset meeting FR-001 criteria is found (See US-1)
- **FR-012**: System MUST derive anticipatory lead time only if the 'user response trigger' used for calculation is distinct from the outcome variable (agency score) to prevent tautological coupling (See US-1)
- **FR-013**: System MUST verify instrument validity by checking for a DOI and ≥10 citations or inclusion in a recognized validation registry (See US-1)
- **FR-014**: System MUST perform a power analysis before modeling and limit Random Forest complexity (max_depth ≤ 3) when sample size N < 100 to prevent overfitting (See US-2)

### Key Entities *(include if feature involves data)*

- **MotionFeature**: Represents a measurable motion parameter from interaction logs; key attributes include feature_type (latency/smoothness/lead_time), value (numeric), unit (ms or dimensionless), source_dataset (string)
- **AgencyScore**: Represents a participant's subjective agency rating; key attributes include participant_id, scale_items (array of Likert responses), aggregated_score (continuous), instrument_name (string)
- **AnalysisResult**: Represents output from statistical modeling; key attributes include model_type (regression/random_forest), feature_importance (map), statistical_significance (map), cross_validation_metrics (map)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against the minimum viable sample size requirement (≥100 complete observations with both motion features and agency scores) (See US-1)
- **SC-002**: Model generalizability is measured against out-of-sample performance metrics from 5-fold cross-validation (R² and RMSE on held-out folds) (See US-2)
- **SC-003**: Statistical inference validity is measured against family-wise error rate control via multiple-comparison correction (See US-2)
- **SC-004**: Predictor independence is measured against variance inflation factor diagnostics (VIF <5 for all retained predictors) (See US-2)
- **SC-005**: Visualization interpretability is measured against ≥80% of 5 independent reviewers rating clarity ≥4/5 on a standardized rubric (See US-3)

---

## Assumptions

- Preferred data sources include OpenML, HuggingFace, OSF, and GitHub, but the system is designed to handle any publicly accessible repository if it meets data criteria.
- The analysis will run on GitHub Actions free-tier runners (2 CPU cores, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h per job).
- Classical statistical methods (multiple linear regression, random forest with scikit-learn) are computationally tractable on CPU-only infrastructure for datasets ≤500 observations.
- Agency questionnaires in available datasets use validated instruments (verified via DOI/citations as per FR-013).
- The research design is observational (no random assignment), so all reported findings will be framed as associational rather than causal.
- Sample size/power considerations are deferred to the implementation phase, with a note that ≥100 observations provides [deferred] power to detect medium effect sizes (r ≈ 0.3) at α = 0.05.
- Dataset-variable fit is assumed: the available data contains all required predictors (latency, smoothness, lead time) and outcome (agency ratings); If the selected dataset does not contain anticipatory lead time as a distinct variable, the system MUST derive it by calculating the temporal offset between the avatar's motion onset and the user's response trigger, provided the raw telemetry allows millisecond-level alignment and the trigger is independent of the agency score (See FR-012). If raw telemetry is unavailable, the feature is marked as missing, and the analysis proceeds with available features only (latency, smoothness), with a warning logged that lead time was not derivable (See US-1).
- Multiple-comparison correction method will be Bonferroni (conservative) unless the number of tests exceeds 10, in which case Benjamini-Hochberg (FDR control) will be used.
- Sensitivity analysis will sweep regression coefficient magnitude thresholds ∈ {0.01, 0.05, 0.1} as these represent small-to-medium effect sizes in behavioral research.
- The analysis requires post-task agency ratings. If the dataset contains only trait/personality measures, those variables MUST be excluded from the primary regression model predicting state agency. Instead, trait measures may be included as covariates in a secondary robustness check, but the primary hypothesis test (FR-004) is strictly limited to post-task state ratings. If no post-task ratings exist, the dataset is rejected for this specific feature branch (See US-1).
- Any validated instrument meeting the criteria in FR-013 (DOI + citations or registry inclusion) is acceptable; specific instruments like SoAS or PAS are preferred but not mandatory.