# Feature Specification: The Influence of Metacognitive Awareness on Reality Testing

**Feature Branch**: `001-influence-metacognitive-awareness-reality-testing`  
**Created**: 2025-02-15  
**Status**: Draft  
**Input**: User description: "Do individuals with higher metacognitive awareness exhibit more accurate reality testing, as measured by reduced source‑monitoring errors on ambiguous perceptual tasks?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Primary Association Analysis (Priority: P1)

Researchers can compute and visualize the correlation between metacognitive awareness (confidence ratings) and reality testing accuracy (source-monitoring performance) to answer the core research question.

**Why this priority**: This delivers the primary scientific output of the project. Without this analysis, the research question remains unanswered. It forms the minimum viable research product.

**Independent Test**: Can be fully tested by running the correlation/regression pipeline and verifying that (1) confidence scores are computed correctly via cross-validation, (2) source-monitoring accuracy is computed correctly, and (3) a correlation coefficient with confidence interval is produced.

**Acceptance Scenarios**:

1. **Given** the OpenNeuro ds003386 dataset and confidence ratings are loaded, **When** the primary analysis pipeline executes, **Then** a Pearson correlation coefficient (r) with 95% bootstrapped confidence interval is produced for confidence score versus source-monitoring accuracy.
2. **Given** the correlation is computed, **When** results are rendered to the output report, **Then** the report displays the correlation magnitude, direction, p-value, and confidence interval in a format suitable for scientific publication.

---

### User Story 2 - Hierarchical Regression with Covariates (Priority: P2)

Researchers can test whether metacognitive awareness contributes unique variance to reality testing accuracy after controlling for age, gender, and working memory capacity.

**Why this priority**: This addresses the "unique contribution" claim in the expected results. It is essential for ruling out confounding by general cognitive ability but depends on the primary correlation being established first.

**Independent Test**: Can be fully tested by running the hierarchical regression and verifying that (1) Step 1 covariates are included, (2) Step 2 adds confidence score, and (3) incremental R² change is reported with significance testing.

**Acceptance Scenarios**:

1. **Given** the primary correlation is established, **When** the hierarchical regression executes, **Then** the output includes R² change (ΔR²) and F-change statistic for adding confidence score in Step 2.
2. **Given** the regression model is fitted, **When** results are rendered, **Then** the confidence coefficient (β), standard error, t-statistic, and p-value are reported alongside the covariate coefficients.

---

### User Story 3 - Modality-Specific Robustness Analysis (Priority: P3)

Researchers can replicate the primary analysis separately for ambiguous visual versus auditory stimuli to test whether the metacognitive awareness–reality testing relationship is modality-specific.

**Why this priority**: This provides robustness validation for the primary finding. It is important for theoretical generalization but does not block the core research question answer.

**Independent Test**: Can be fully tested by filtering the dataset to visual-only and auditory-only trials, running the correlation analysis on each subset, and verifying that separate correlation coefficients are produced.

**Acceptance Scenarios**:

1. **Given** the full dataset is loaded, **When** the modality filter is applied to visual stimuli only, **Then** a separate correlation coefficient (r_visual) with confidence interval is computed.
2. **Given** the full dataset is loaded, **When** the modality filter is applied to auditory stimuli only, **Then** a separate correlation coefficient (r_auditory) with confidence interval is computed.

---

### Edge Cases

- What happens when the OpenNeuro ds003386 dataset does not contain confidence rating fields or the required source-monitoring trial labels?
- How does the system handle missing participant responses (e.g., incomplete confidence scoring or missing trial data)?
- What happens when the bootstrap resampling (1,000 resamples) fails to converge within the 6-hour GitHub Actions runtime limit?
- How does the system handle participants with extreme outliers in confidence scores or accuracy that violate normality assumptions?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the OpenNeuro ds003386 dataset stimulus files and participant response logs to extract trial-wise source labels (imagined vs. perceived) and participant responses (See US-1).
- **FR-002**: System MUST compute metacognitive scores from trial-wise confidence ratings (0-100%) by normalizing to 0-1 scale and averaging per participant; confidence must be computed via cross-validation where trials used for confidence estimation are held out from trials used for accuracy computation (See US-1).
- **FR-003**: System MUST calculate source-monitoring accuracy (hits + correct rejections / total trials) and signal-detection measures (d′, criterion) for each participant (See US-1).
- **FR-004**: System MUST perform Pearson correlation between metacognitive scores and source-monitoring accuracy/d′ with 1,000 bootstrap resamples for 95% confidence intervals (See US-1).
- **FR-005**: System MUST execute hierarchical linear regression: Step 1 (age, gender, working-memory span if available), Step 2 (add metacognitive score) and report incremental variance; if working-memory data is unavailable, system MUST exclude it and report n-1 model with adjusted R² (See US-2).
- **FR-006**: System MUST apply Bonferroni or Benjamini-Hochberg correction for multiple-comparison family-wise error when testing >1 hypothesis (See US-3).
- **FR-007**: System MUST replicate the primary correlation analysis separately for visual-only and auditory-only stimulus subsets (See US-3).
- **FR-008**: System MUST check regression assumptions (normality of residuals, homoscedasticity) and flag violations in the output report (See US-2).
- **FR-009**: System MUST implement collinearity diagnostics (VIF ≥ 5 threshold) when multiple predictors are included in the regression model (See US-2).
- **FR-010**: System MUST implement cross-validation for confidence computation: for each participant, split trials into K=5 folds; compute mean confidence from K-1 folds and accuracy from held-out fold, rotating across all folds to ensure predictor and outcome are not from identical trial instances (See US-1).

### Key Entities *(include if feature involves data)*

- **Participant**: Represents a study subject with attributes (participant_id, age, gender, metacognitive_score, working_memory_score, source_monitoring_accuracy, d_prime, criterion).
- **Trial**: Represents a single source-monitoring trial with attributes (trial_id, participant_id, stimulus_modality, source_label, participant_response, confidence_rating, reaction_time).
- **AnalysisResult**: Represents a statistical output with attributes (analysis_type, correlation_coefficient, p_value, confidence_interval, sample_size).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.
>
> **Note on Design Targets**: SC-002 (ΔR² ≥ 0.02) and SC-003 (CI width ≤ 0.20) are methodological design targets based on community standards for meaningful effect sizes and estimation precision in psychological research, not empirical measurements deferred to implementation.

- **SC-001**: Correlation magnitude (r) between metacognitive score and source-monitoring accuracy is measured against expected range r ≥ 0.20 based on meta-analytic effect sizes for metacognition-reality testing associations (See US-1).
- **SC-002**: Incremental variance (ΔR²) added by metacognitive score in hierarchical regression is measured against defensible threshold ≥ 0.02 for meaningful unique contribution in psychological research (See US-2).
- **SC-003**: Bootstrapped confidence interval width for the primary correlation is measured against criterion ≤ 0.20 to ensure estimation precision (See US-1).
- **SC-004**: Multiple-comparison correction method achieves family-wise error rate controlled at α ≤ 0.05 (See US-3).
- **SC-005**: Sample size (n=120 participants) is measured against power analysis requirements for detecting r ≈ 0.30 at α = 0.05 with 80% power (See US-1).

## Data Constraints

<!--
  Critical data availability notes that affect requirement feasibility.
-->

- **OpenNeuro ds003386 does not contain the Metacognitive Awareness Questionnaire (MAQ)**. It contains trial-wise confidence ratings (0-100%) which serve as the metacognitive measure (proxy for MAQ, see ds003386 README). Confidence ratings are used per source-monitoring convention and are normalized to 0-1 scale for analysis.
- **Cross-validation requirement**: To avoid circularity between confidence (predictor) and accuracy (outcome), FR-010 mandates that confidence and accuracy are computed from different trial instances via K-fold cross-validation.

## Assumptions

- The OpenNeuro ds003386 dataset contains sufficient trial-level data (≥ 30 trials per participant) to compute reliable source-monitoring accuracy and signal-detection measures.
- Working-memory span measures are available in the OpenNeuro ds003386 dataset for covariate control in the hierarchical regression; if not, FR-005 fallback excludes this covariate (See FR-005).
- The participants in the selected dataset are healthy adults (ages 18–35) as stated in the idea, with no clinical diagnoses that would confound the metacognitive awareness–reality testing relationship.
- The GitHub Actions free-tier runner (2 CPU, ~7 GB RAM, ≤6 h) is sufficient for the entire analysis pipeline including 1,000 bootstrap resamples; if runtime exceeds this, the bootstrap count will be reduced to 500.
- The confidence rating instrument has established psychometric validation (citable) for use as a metacognitive measure in source-monitoring tasks; the validation source will be cited from the idea's Related Work section.
- The analysis treats all findings as ASSOCIATIONAL (observational design without randomization); causal or moderation claims are excluded from the scope.
- Any decision thresholds introduced (e.g., VIF ≥ 5 for collinearity, ΔR² ≥ 0.02 for meaningful variance) will carry sensitivity analysis sweeping the threshold over {0.01, 0.05, 0.1} and reporting how rates vary across it.

## Research-question Validation

<!--
  Verify predictor and outcome independence per Constitution Principle VI.
-->

**Verdict**: Conditional pass

**Rationale**: The predictor (metacognitive confidence) and outcome (source-monitoring accuracy) are derived from the same task modality (source-monitoring trials), which would normally violate Constitution Principle VI. However, FR-010 implements K-fold cross-validation ensuring that confidence is computed from K-1 folds while accuracy is computed from the held-out fold, preventing any single trial from contributing to both predictor and outcome. This cross-validation approach breaks the circularity and satisfies the independence requirement.

**Constitution Principle VI Compliance**: Predictor and outcome are stored in separate derived files (confidence_summary.csv and accuracy_summary.csv); no derived transformation creates one from the other because FR-010 ensures trial-level separation via cross-validation.