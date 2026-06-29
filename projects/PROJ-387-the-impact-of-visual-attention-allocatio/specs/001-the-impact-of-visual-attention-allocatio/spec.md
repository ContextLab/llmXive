# Feature Specification: The Impact of Visual Attention Allocation on Recall of Emotionally Valenced Stories

**Feature Branch**: `001-visual-attention-recall`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Does visual attention allocation during reading—measured by fixation duration, saccade patterns, and gaze distribution—predict subsequent recall accuracy for emotionally valenced narrative content?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Variable Validation (Priority: P1)

The system MUST load public eye-tracking datasets and validate the presence of required variables (fixation duration, saccade amplitude, gaze distribution, recall accuracy, valence label) before proceeding to analysis.

**Why this priority**: Without verified input data, no statistical analysis can occur. This is the foundational step that determines project feasibility.

**Independent Test**: Can be fully tested by running the ingestion script against a sample dataset file and verifying the output log confirms all required columns exist AND data quality metrics pass.

**Acceptance Scenarios**:

1. **Given** a valid eye-tracking dataset file, **When** the ingestion script runs, **Then** the system confirms the presence of fixation duration, saccade amplitude, gaze distribution, recall accuracy, and valence label columns.
2. **Given** a dataset missing valence label, **When** the ingestion script runs, **Then** the system flags the dataset as incompatible and halts further processing.
3. **Given** a dataset with eye-tracking data, **When** data quality validation runs, **Then** the system confirms ≤5% track loss and calibrated eye-tracker status (Constitution VI).
4. **Given** a dataset with valence annotations, **When** valence annotation validation runs, **Then** the system confirms standardized rating scale format and storage location data/valence/ (Constitution VII).

---

### User Story 2 - Statistical Analysis and Association Modeling (Priority: P2)

The system MUST compute linear mixed-effects models (LMM) between attentional metrics and recall accuracy, applying multiple-comparison corrections across all metric-category combinations and framing results as associational rather than causal.

**Why this priority**: This is the core research function that answers the primary research question.

**Independent Test**: Can be fully tested by running the analysis module on pre-processed data and verifying the output includes LMM coefficients with corrected p-values.

**Acceptance Scenarios**:

1. **Given** validated input data, **When** the analysis module executes, **Then** the system outputs LMM coefficients for each attention metric vs. recall accuracy per valence category.
2. **Given** multiple hypothesis tests (across valence categories AND attention metrics), **When** significance testing completes, **Then** the system applies Bonferroni correction across all metric-category combinations and reports adjusted p-values.
3. **Given** the observational nature of the data, **When** results are generated, **Then** the output explicitly labels findings as "associational" and avoids causal language.

---

### User Story 3 - Visualization and Reporting (Priority: P3)

The system MUST generate visualizations of attentional metric distributions by valence, scatter plots of attention metrics vs. recall performance, and output a summary report.

**Why this priority**: This enables interpretation of the statistical results and supports the "Expected results" section of the idea.

**Independent Test**: Can be fully tested by checking that plot files are generated in the output directory and contain labeled axes matching the defined metrics.

**Acceptance Scenarios**:

1. **Given** completed statistical analysis, **When** the reporting module runs, **Then** scatter plots showing attention metric vs. recall accuracy are generated for each valence category.
2. **Given** completed statistical analysis, **When** the reporting module runs, **Then** distribution histograms for each attention metric by valence category are generated.
3. **Given** the analysis results, **When** the summary report is compiled, **Then** it includes the LMM coefficients, corrected p-values, and the associational disclaimer.

---

### Edge Cases

- What happens when the dataset exceeds available RAM (7 GB) on the CI runner?
- How does the system handle participants with missing recall scores for specific passages?
- What happens if the p-value sensitivity analysis shows no stable threshold across the sweep?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load eye-tracking data from standard formats (e.g., CSV, EDF) without requiring GPU acceleration (See US-1)
- **FR-002**: System MUST validate that every required variable (fixation duration, saccade amplitude, gaze distribution, recall accuracy, valence label) exists in the input dataset AND that data quality metrics pass (≤5% track loss, calibrated eye-tracker) (See US-1)
- **FR-003**: System MUST compute linear mixed-effects models (LMM) between attentional metrics (fixation duration, saccade amplitude, gaze distribution) and recall accuracy for each valence category, accounting for hierarchical data structure (See US-2)
- **FR-004**: System MUST apply Bonferroni correction for multiple comparisons across all metric-category combinations (3 attention metrics × 3 valence categories = 9 tests minimum) (See US-2)
- **FR-005**: System MUST explicitly label all statistical findings as "associational" and prohibit causal language in the output report (See US-2)
- **FR-006**: System MUST perform a sensitivity analysis on the significance threshold by sweeping p-values across {0.01, 0.05, 0.1} and reporting rate variations (See US-2)
- **FR-007**: System MUST generate (a) scatter plots with labeled axes (Attention Metric vs. Recall Accuracy) for each valence category AND (b) distribution histograms for each attention metric by valence category (See US-3)
- **FR-008**: System MUST complete the full analysis pipeline within 6 hours on a 2-core CPU environment (See US-2)

### Key Entities *(include if data)*

- **EyeTrackingRecord**: Represents a single reading event; key attributes include participant_id, fixation_duration_ms, saccade_amplitude_deg, gaze_distribution_density, passage_id, valence_label.
- **RecallScore**: Represents memory performance; key attributes include participant_id, passage_id, free_recall_accuracy, recognition_score.
- **AnalysisResult**: Represents the statistical output; key attributes include lmm_coefficient, p_value_raw, p_value_corrected, attention_metric, valence_category, association_label.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data ingestion success rate is measured against the total number of available public datasets; ≥95% of datasets must complete ingestion with all required columns present AND data quality metrics passing (See US-1)
- **SC-002**: Statistical test completion rate is measured against the total number of participant-passages analyzed; LMM tests must complete without runtime error (See US-2)
- **SC-003**: Multiple-comparison correction application is measured against the number of hypothesis tests performed; All tests must have corrected p-values present in output (See US-2)
- **SC-004**: Total pipeline runtime is measured against the predefined CPU limit constraint (See US-2)
- **SC-005**: Visualization output completeness is measured against the number of valence categories defined in the input; all valence categories must have ≥2 plot files (scatter + histogram) with labeled axes (See US-3)

## Assumptions

- The public eye-tracking datasets referenced (e.g., OpenNeuro) contain the necessary columns for fixation duration, saccade metrics, and recall accuracy.
- Valence annotations will be sourced from dataset metadata OR computed via NLP sentiment scoring (e.g., VADER, TextBlob) with explicit fallback procedure when metadata is unavailable.
- Valence categories are derived from dataset metadata or NLP sentiment scoring; if three categories (positive, negative, neutral) are not available, the system will use the available categories with documentation of the actual categories used.
- The analysis will rely on linear mixed-effects models (LMM) rather than deep learning to ensure CPU feasibility and handle hierarchical data structure.
- All recall measures used in the source datasets are validated instruments with citable validation (e.g., standard free-recall protocols).
- The CI runner environment provides sufficient RAM to load the sampled dataset without memory overflow.
- Findings will be framed as associational due to the observational nature of the data (no random assignment of attention).
- If NLP-based sentiment scoring is required for valence, a sensitivity analysis on the sentiment cutoff score will be performed alongside the p-value sweep.