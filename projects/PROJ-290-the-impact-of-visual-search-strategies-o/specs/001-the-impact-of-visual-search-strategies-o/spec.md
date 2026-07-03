# Feature Specification: The Impact of Visual Search Strategies on Attentional Capture by Emotional Faces

**Feature Branch**: `001-visual-search-emotional-faces`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Research question about global vs local visual search strategies in emotional face detection using eye-tracking data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Verification (Priority: P1)

The research pipeline MUST successfully download and validate eye-tracking datasets containing emotional face stimuli with gaze coordinates and response times from HuggingFace Datasets or equivalent repositories.

**Why this priority**: Without verified data access, no analysis can proceed. This is the foundational step that determines project feasibility.

**Independent Test**: Can be fully tested by executing the data download script and verifying dataset integrity without running any statistical analysis.

**Acceptance Scenarios**:

1. **Given** a valid dataset identifier (e.g., HuggingFace `eyetracking-emotion-face-search`), **When** the pipeline executes the download script, **Then** all available records up to a target of [deferred] participant records with complete gaze coordinates and response times are retrieved.
2. **Given** a dataset with missing or corrupted records, **When** the validation step runs, **Then** ≥95% of records pass integrity checks (non-null gaze coordinates, valid response time values).
3. **Given** network connectivity issues, **When** the download fails, **Then** the system retries up to 3 times with exponential backoff (1s, 2s, 4s) before failing with a clear error message.

---

### User Story 2 - Feature Extraction and Strategy Classification (Priority: P2)

The pipeline MUST compute fixation metrics (eye vs. mouth region duration, saccade amplitude, dispersion) and classify participants into local vs. global processing strategies, with fallback handling for unimodal data distributions.

**Why this priority**: This transforms raw eye-tracking data into the predictor variable for the statistical model. Without this, the research question cannot be answered.

**Independent Test**: Can be tested by processing a subset of 10 participant records and verifying that clustering produces interpretable results or correctly triggers a fallback to descriptive statistics.

**Acceptance Scenarios**:

1. **Given** validated eye-tracking data with ROI masks for eye and mouth regions, **When** the feature extraction module runs, **Then** fixation duration on eye regions and mouth regions is computed for each trial with ≤5% RMSE variance from ground-truth annotations (if available); if ground truth is missing, the system logs a warning.
2. **Given** extracted fixation features for ≥[deferred] participants, **When** k-means clustering (k=2) executes, **Then** if N >= 10, both clusters contain at least 5 participants each; otherwise, the system logs a warning and proceeds with descriptive statistics only.
3. **Given** collinear predictors (e.g., eye fixation proportion and total fixation duration), **When** the collinearity diagnostic runs, **Then** variance inflation factors (VIF) are calculated and flagged if VIF ≥5.

---

### User Story 3 - Statistical Analysis and Power Validation (Priority: P3)

The pipeline MUST fit a linear mixed-effects model with detection time as outcome and processing strategy as fixed effect, while performing post-hoc power analysis and multiple-comparison corrections.

**Why this priority**: This directly answers the research question and provides the publishable results. Lower priority because it depends on successful data acquisition and feature extraction.

**Independent Test**: Can be tested by running the model on a mock dataset with known effect sizes and verifying that confidence intervals and p-values are correctly computed.

**Acceptance Scenarios**:

1. **Given** classified participants with fixation strategy labels and detection times, **When** the mixed-effects model executes, **Then** the model converges within 500 iterations with all fixed-effect coefficients reported (estimate, SE, t-value, p-value).
2. **Given** multiple hypothesis tests (e.g., comparing emotion types), **When** the multiplicity correction runs, **Then** family-wise error rate is controlled using Bonferroni or Benjamini-Hochberg method at α=0.05.
3. **Given** the final sample size (N participants), **When** the power analysis runs, **Then** the system MUST calculate and report achieved power for effect size d=0.5; if power <0.80, the report documents the limitation explicitly.

---

### Edge Cases

- What happens when the dataset lacks specific emotion categories (e.g., no fearful faces)? → Pipeline filters to available emotions and logs a warning; analysis proceeds with reduced scope.
- How does the system handle participants with incomplete gaze data (>20% missing coordinates)? → These participants are excluded from analysis; exclusion rate is documented and must be ≤10% of total sample.
- What if the mixed-effects model fails to converge? → If the model fails to converge within 500 iterations or if the gradient norm remains > 1e-4 after max_iter, the pipeline falls back to a simpler linear model with participant as fixed effect; this fallback is documented in results.
- How does the system handle datasets with different coordinate systems (pixel vs. normalized)? → Coordinate normalization is applied automatically; the transformation method is logged.
- What happens if critical variables (gaze_coordinates, response_times, emotion_labels, roi_annotations) are missing? → The pipeline halts execution, logs a specific error identifying the missing variable, and documents the limitation in the results report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (See US-1)**: System MUST download eye-tracking datasets from HuggingFace Datasets or equivalent repositories and verify record completeness (gaze coordinates and response times non-null) for ≥95% of trials.
- **FR-002 (See US-1)**: System MUST implement retry logic with exponential backoff (1s, 2s, 4s) for network failures, attempting up to 3 retries before failing with explicit error documentation.
- **FR-003 (See US-2)**: System MUST compute fixation duration on predefined eye and mouth ROI masks, saccade amplitude, and dispersion metrics for each trial, outputting features in a structured format (CSV/JSON).
- **FR-004 (See US-2)**: System MUST attempt to classify participants into local vs. global processing strategies using k-means clustering (k=2) on fixation distribution features. System MUST calculate silhouette scores; if mean silhouette < 0.25, the system MUST log a warning that clusters may be artificial and proceed with descriptive statistics only. If the clustering fails to produce valid clusters (e.g., <5 participants in either cluster), the system MUST log a warning and proceed with descriptive statistics only.
- **FR-005 (See US-2)**: System MUST calculate variance inflation factors (VIF) for all predictor pairs and flag any VIF ≥5 for collinearity review in the results report.
- **FR-006 (See US-3)**: System MUST fit a linear mixed-effects model with detection time as outcome, processing strategy (derived cluster label) as fixed effect, and participant as random intercept using statsmodels or equivalent CPU-compatible library.
- **FR-007 (See US-3)**: System MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) at α=0.05 when >1 hypothesis test is performed, reporting adjusted p-values.
- **FR-008 (See US-3)**: System MUST perform post-hoc power analysis for the final sample size and report achieved power for effect size d=0.5; if power <0.80, the limitation is documented.
- **FR-009 (See US-1)**: System MUST validate the presence of critical variables (`gaze_coordinates`, `response_times`, `emotion_labels`, `roi_annotations`) in the selected dataset prior to feature extraction. If any critical variable is missing, the system MUST halt execution, log a specific error identifying the missing variable, and document the limitation in the results report.
- **FR-010 (See US-2)**: System MUST perform a sensitivity analysis on the clustering strategy by sweeping k over a set of small integer values and reporting how cluster composition and downstream model coefficients vary to ensure robustness against artificial splits.
- **FR-011 (See US-2)**: System MUST perform k-fold cross-validation (k=5) when deriving strategy labels; strategy labels for the outcome model MUST be derived from folds excluding the test participants to prevent data leakage.

### Key Entities

- **Participant**: Research subject with unique ID, associated with multiple trials; key attributes: participant_id, processing_strategy_label, demographic_metadata.
- **Trial**: Single experimental observation; key attributes: trial_id, participant_id, emotion_type, response_time, fixation_metrics (eye_duration, mouth_duration, saccade_amplitude, dispersion).
- **FixationMetric**: Computed eye-tracking feature; key attributes: metric_name, value, unit, trial_id, ROI_mask_reference.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001 (See US-1)**: Dataset download success rate is measured against the target of ≥95% of trials with complete gaze coordinates and response times; source: validation log output.
- **SC-002 (See US-2)**: Cluster validity is measured against the requirement that both local and global processing clusters contain ≥5 participants (if N >= 10) and mean silhouette score ≥ 0.25; source: clustering output report.
- **SC-003 (See US-3)**: Model convergence is measured against the target of ≤500 iterations with all fixed-effect coefficients successfully estimated; source: mixed-effects model convergence log.
- **SC-004 (See US-3)**: Statistical power is measured against the target of ≥0.80 for effect size d=0.5; source: post-hoc power analysis output; if not achieved, the gap is documented.
- **SC-005 (See US-3)**: Family-wise error rate is measured against the controlled α=0.05 threshold after multiplicity correction; source: adjusted p-values report.
- **SC-006 (See US-2)**: Sensitivity of clustering is measured against the variance in cluster composition and model coefficients across a range of cluster counts k.; source: sensitivity analysis report.

## Assumptions

- The publicly available eye-tracking datasets contain all required variables (gaze coordinates, response times, emotion labels, ROI masks); if a critical variable is missing, the pipeline halts with a specific error log and documents the limitation as per FR-009.
- The analysis is observational (no random assignment of processing strategy); therefore, all statistical findings are framed as associational relationships, not causal claims.
- The GitHub Actions free-tier runner provides sufficient resources (multiple CPU cores, adequate memory, and storage) to process the dataset.; if data exceeds a predetermined threshold, sampling is applied to ensure feasibility.
- The k-means clustering (k=2) produces interpretable local vs. global processing groups; if clusters are unbalanced (<5 participants in either cluster), the pipeline logs a warning and proceeds with descriptive statistics only.
- All eye-tracking instruments used in the source dataset are validated (citable validation literature); if instrument validation is unavailable, this limitation is documented in results.
- The linear mixed-effects model uses default convergence criteria (tolerance=1e-6, max_iter=500) without GPU acceleration; no CUDA or quantization methods are used.
- Multiple-comparison correction uses Bonferroni method as the default; Benjamini-Hochberg is available as an alternative if the number of tests is sufficiently large.
- The allocated GHA job time limit is sufficient for all pipeline stages; if any stage exceeds a predefined duration threshold, it is decomposed into atomic sub-tasks.
- No post-task anxiety/rumination measures are required by the design; the pipeline ignores these variables if present and does not halt.
- The threshold for cluster assignment (k=2 in k-means) follows community-standard practice for binary processing strategy classification; sensitivity analysis sweeps k∈{2,3} and reports how cluster composition varies.
- Data download is best-effort; target completion time is within a reasonable duration under standard network conditions.