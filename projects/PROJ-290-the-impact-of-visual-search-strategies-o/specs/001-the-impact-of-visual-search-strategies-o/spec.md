# Feature Specification: The Impact of Visual Search Strategies on Attentional Capture by Emotional Faces

**Feature Branch**: `001-visual-search-emotional-faces`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Research question about global vs local visual search strategies in emotional face detection using eye-tracking data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Verification (Priority: P1)

The research pipeline MUST successfully download and validate eye-tracking datasets containing emotional face stimuli with gaze coordinates and response times.

**Why this priority**: Without verified data access, no analysis can proceed. This is the foundational step that determines project feasibility.

**Independent Test**: Can be fully tested by executing the data download script and verifying dataset integrity without running any statistical analysis.

**Acceptance Scenarios**:

1. **Given** a valid dataset identifier (e.g., HuggingFace `eyetracking-emotion-face-search`), **When** the pipeline executes the download script, **Then** at least 30 participant records with complete gaze coordinates and response times are retrieved within 15 minutes.
2. **Given** a dataset with missing or corrupted records, **When** the validation step runs, **Then** ≥95% of records pass integrity checks (non-null gaze coordinates, valid response time values).
3. **Given** network connectivity issues, **When** the download fails, **Then** the system retries up to 3 times with exponential backoff (1s, 2s, 4s) before failing with a clear error message.

---

### User Story 2 - Feature Extraction and Strategy Classification (Priority: P2)

The pipeline MUST compute fixation metrics (eye vs. mouth region duration, saccade amplitude, dispersion) and classify participants into local vs. global processing strategies.

**Why this priority**: This transforms raw eye-tracking data into the predictor variable for the statistical model. Without this, the research question cannot be answered.

**Independent Test**: Can be tested by processing a subset of 10 participant records and verifying that clustering produces two distinct groups with interpretable fixation patterns.

**Acceptance Scenarios**:

1. **Given** validated eye-tracking data with ROI masks for eye and mouth regions, **When** the feature extraction module runs, **Then** fixation duration on eye regions and mouth regions is computed for each trial with ≤5% variance from ground-truth annotations (if available).
2. **Given** extracted fixation features for ≥30 participants, **When** k-means clustering (k=2) executes, **Then** both clusters contain at least 5 participants each to ensure statistical validity.
3. **Given** collinear predictors (e.g., eye fixation proportion and total fixation duration), **When** the collinearity diagnostic runs, **Then** variance inflation factors (VIF) are calculated and flagged if VIF ≥5.

---

### User Story 3 - Statistical Analysis and Power Validation (Priority: P3)

The pipeline MUST fit a linear mixed-effects model with detection time as outcome and processing strategy as fixed effect, while performing post-hoc power analysis and multiple-comparison corrections.

**Why this priority**: This directly answers the research question and provides the publishable results. Lower priority because it depends on successful data acquisition and feature extraction.

**Independent Test**: Can be tested by running the model on a mock dataset with known effect sizes and verifying that confidence intervals and p-values are correctly computed.

**Acceptance Scenarios**:

1. **Given** classified participants with fixation strategy labels and detection times, **When** the mixed-effects model executes, **Then** the model converges within 500 iterations with all fixed-effect coefficients reported (estimate, SE, t-value, p-value).
2. **Given** multiple hypothesis tests (e.g., comparing emotion types), **When** the multiplicity correction runs, **Then** family-wise error rate is controlled using Bonferroni or Benjamini-Hochberg method at α=0.05.
3. **Given** the final sample size (N participants), **When** the power analysis runs, **Then** achieved power is reported with target power ≥0.80 for effect size d=0.5; if underpowered, the report documents the limitation explicitly.

---

### Edge Cases

- What happens when the dataset lacks specific emotion categories (e.g., no fearful faces)? → Pipeline filters to available emotions and logs a warning; analysis proceeds with reduced scope.
- How does the system handle participants with incomplete gaze data (>20% missing coordinates)? → These participants are excluded from analysis; exclusion rate is documented and must be ≤10% of total sample.
- What if the mixed-effects model fails to converge? → The pipeline falls back to a simpler linear model with participant as fixed effect; this fallback is documented in results.
- How does the system handle datasets with different coordinate systems (pixel vs. normalized)? → Coordinate normalization is applied automatically; the transformation method is logged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (See US-1)**: System MUST download eye-tracking datasets from HuggingFace Datasets or OpenML repositories and verify record completeness (gaze coordinates and response times non-null) for ≥95% of trials within 15 minutes.
- **FR-002 (See US-1)**: System MUST implement retry logic with exponential backoff (1s, 2s, 4s) for network failures, attempting up to 3 retries before failing with explicit error documentation.
- **FR-003 (See US-2)**: System MUST compute fixation duration on predefined eye and mouth ROI masks, saccade amplitude, and dispersion metrics for each trial, outputting features in a structured format (CSV/JSON).
- **FR-004 (See US-2)**: System MUST classify participants into local vs. global processing strategies using k-means clustering (k=2) on fixation distribution features, ensuring both clusters contain ≥5 participants.
- **FR-005 (See US-2)**: System MUST calculate variance inflation factors (VIF) for all predictor pairs and flag any VIF ≥5 for collinearity review in the results report.
- **FR-006 (See US-3)**: System MUST fit a linear mixed-effects model with detection time as outcome, processing strategy as fixed effect, and participant as random intercept using statsmodels or equivalent CPU-compatible library.
- **FR-007 (See US-3)**: System MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) at α=0.05 when >1 hypothesis test is performed, reporting adjusted p-values.
- **FR-008 (See US-3)**: System MUST perform post-hoc power analysis for the final sample size and report achieved power for effect size d=0.5; if power <0.80, the limitation is documented.
- **FR-009 (See US-1)**: System MUST verify dataset-variable fit by confirming the dataset contains all required variables (gaze coordinates, response times, emotion labels, ROI annotations); any missing variable triggers a `[NEEDS CLARIFICATION: does <dataset> contain <variable>?]` marker.

### Key Entities

- **Participant**: Research subject with unique ID, associated with multiple trials; key attributes: participant_id, processing_strategy_label, demographic_metadata.
- **Trial**: Single experimental observation; key attributes: trial_id, participant_id, emotion_type, response_time, fixation_metrics (eye_duration, mouth_duration, saccade_amplitude, dispersion).
- **FixationMetric**: Computed eye-tracking feature; key attributes: metric_name, value, unit, trial_id, ROI_mask_reference.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001 (See US-1)**: Dataset download success rate is measured against the target of ≥95% of trials with complete gaze coordinates and response times; source: validation log output.
- **SC-002 (See US-2)**: Cluster validity is measured against the requirement that both local and global processing clusters contain ≥5 participants; source: clustering output report.
- **SC-003 (See US-3)**: Model convergence is measured against the target of ≤500 iterations with all fixed-effect coefficients successfully estimated; source: mixed-effects model convergence log.
- **SC-004 (See US-3)**: Statistical power is measured against the target of ≥0.80 for effect size d=0.5; source: post-hoc power analysis output; if not achieved, the gap is documented.
- **SC-005 (See US-3)**: Family-wise error rate is measured against the controlled α=0.05 threshold after multiplicity correction; source: adjusted p-values report.

## Assumptions

- The publicly available eye-tracking datasets contain all required variables (gaze coordinates, response times, emotion labels, ROI masks); if a variable is missing, the pipeline halts with a `[NEEDS CLARIFICATION]` marker rather than proceeding with incomplete data.
- The analysis is observational (no random assignment of processing strategy); therefore, all statistical findings are framed as associational relationships, not causal claims.
- The GitHub Actions free-tier runner provides sufficient resources (multiple CPU cores, adequate memory, and storage) to process the dataset.; if data exceeds a predetermined threshold, sampling is applied to ensure feasibility.
- The k-means clustering (k=2) produces interpretable local vs. global processing groups; if clusters are unbalanced (<5 participants in either cluster), the pipeline logs a warning and proceeds with descriptive statistics only.
- All eye-tracking instruments used in the source dataset are validated (citable validation literature); if instrument validation is unavailable, this limitation is documented in results.
- The linear mixed-effects model uses default convergence criteria (tolerance=1e-6, max_iter=500) without GPU acceleration; no CUDA or quantization methods are used.
- Multiple-comparison correction uses Bonferroni method as the default; Benjamini-Hochberg is available as an alternative if the number of tests exceeds 10.
- The allocated GHA job time limit is sufficient for all pipeline stages; if any stage exceeds a predefined duration threshold, it is decomposed into atomic sub-tasks.
- No post-task anxiety/rumination measures are required by the design; if the dataset lacks these variables, no analysis depends on them (no `[NEEDS CLARIFICATION]` needed for this specific case).
- The threshold for cluster assignment (k=2 in k-means) follows community-standard practice for binary processing strategy classification; sensitivity analysis sweeps k∈{1,2,3} and reports how cluster composition varies.
