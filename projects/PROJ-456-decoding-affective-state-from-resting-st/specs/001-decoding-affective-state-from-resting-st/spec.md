# Feature Specification: Decoding Affective State from Resting-State EEG Microstates

**Feature Branch**: `001-decoding-affective-state`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Decoding Affective State from Resting-State EEG Microstates"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - EEG Data Acquisition and Preprocessing Pipeline (Priority: P1)

The research team MUST be able to download resting-state EEG data from OpenNeuro datasets (e.g., ds003501, ds004137), preprocess it through bandpass filtering (1-40 Hz), artifact removal via ICA, and average re-referencing, then segment the EEG into canonical microstate classes using K-means clustering on topographic maps.

**Why this priority**: This is the foundational capability without which no analysis can proceed. The entire research question depends on having clean, properly segmented microstate data.

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a single OpenNeuro dataset and verifying output files (microstate class labels, temporal feature matrices) exist and contain valid numeric data for ≥10 subjects.

**Acceptance Scenarios**:

1. **Given** an OpenNeuro dataset identifier exists in the configuration, **When** the preprocessing pipeline executes, **Then** bandpass filtering (1-40 Hz) is applied and filtered EEG data is saved with verified frequency response within ±0.5 dB of passband.
2. **Given** raw EEG data with artifacts, **When** ICA-based artifact removal runs, **Then** ≥90% of identified ocular/muscle components are removed while retaining ≥85% of original signal variance.
3. **Given** preprocessed EEG, **When** microstate segmentation executes, **Then** exactly 4 canonical microstate classes are identified with global explained variance ≥75%.

---

### User Story 2 - Affective Correlation Analysis (Priority: P2)

The research team MUST be able to extract temporal microstate features (mean duration, occurrence rate, coverage, transition probability for each of 4 classes), collect self-reported valence/arousal scores from associated questionnaires (PANAS, SAM), and compute Pearson/Spearman correlations between microstate features and affective scores with Bonferroni correction for multiple comparisons.

**Why this priority**: This directly addresses the research question about whether microstate dynamics vary with affective dimensions. Without this analysis, the project cannot produce evidence on the relationship.

**Independent Test**: Can be fully tested by running correlation analysis on extracted features and questionnaire scores from ≥10 subjects, verifying that correlation coefficients, p-values, and corrected significance flags are produced for all feature-dimension pairs.

**Acceptance Scenarios**:

1. **Given** microstate feature matrices and affective questionnaire scores for ≥10 subjects, **When** correlation analysis executes, **Then** Pearson/Spearman correlation coefficients are computed for all combinations (4 microstate classes × 4 temporal features × 2 affective dimensions = 32 tests).
2. **Given** 32 hypothesis tests, **When** multiple comparison correction runs, **Then** Bonferroni correction is applied (α_corrected = 0.05/32 = 0.00156) and corrected p-values are reported.
3. **Given** significant correlations at p < 0.05, **When** effect sizes are computed, **Then** Cohen's d and 95% confidence intervals are generated for each significant finding.

---

### User Story 3 - Validation and Cross-Validation (Priority: P3)

The research team MUST be able to validate findings using leave-one-subject-out cross-validation where sample size permits, and generate effect size estimates with confidence intervals for replication assessment across multiple datasets or cross-validation splits.

**Why this priority**: This ensures the findings are robust and not overfit to a specific sample. Essential for scientific credibility but builds upon the core analysis pipeline.

**Independent Test**: Can be fully tested by running leave-one-subject-out cross-validation on ≥15 subjects and verifying that correlation stability is measured across folds with variance reported.

**Acceptance Scenarios**:

1. **Given** ≥15 subjects in the dataset, **When** leave-one-subject-out cross-validation executes, **Then** correlation coefficients are computed for each fold (N-1 subjects) and stability metrics (mean, std across folds) are reported.
2. **Given** multiple OpenNeuro datasets available, **When** replication analysis runs, **Then** effect size consistency is measured across datasets with heterogeneity statistics (I² or Q-test) computed.
3. **Given** any correlation threshold decision, **When** sensitivity analysis runs, **Then** the threshold is swept over {0.01, 0.05, 0.1} absolute difference and false-positive/false-negative rates are reported across the sweep.

---

### Edge Cases

- What happens when an OpenNeuro dataset lacks required affective questionnaire data? → Pipeline must gracefully skip that dataset and log a `[NEEDS CLARIFICATION: dataset dsXXXXX missing affective questionnaire]` marker.
- How does system handle subjects with insufficient EEG data quality (e.g., >30% artifact rejection)? → Subjects are excluded with a documented exclusion log; analysis requires ≥8 subjects minimum.
- What happens when microstate clustering converges to fewer than 4 classes? → The algorithm MUST enforce exactly 4 classes via constrained initialization and report convergence diagnostics.
- How does system handle affective scores with missing values? → Subjects with missing questionnaire data are excluded from correlation analysis; ≥80% response rate required per questionnaire.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download resting-state EEG data from specified OpenNeuro datasets (ds003501, ds004137) and verify dataset-variable fit by confirming each contains both raw EEG (≥128 Hz sampling) and self-report affective questionnaire data (See US-1)
- **FR-002**: System MUST preprocess EEG through bandpass filtering (1-40 Hz), ICA-based artifact removal, and average re-referencing, outputting cleaned EEG with ≥85% signal variance retained (See US-1)
- **FR-003**: System MUST segment EEG into exactly 4 canonical microstate classes using K-means clustering on topographic maps with global explained variance ≥75% (See US-1)
- **FR-004**: System MUST extract temporal microstate features (mean duration, occurrence rate, coverage, transition probability) for each of the 4 microstate classes (See US-2)
- **FR-005**: System MUST compute Pearson/Spearman correlations between all microstate features (4 classes × 4 features = 16) and affective dimensions (valence, arousal = 2), yielding 32 hypothesis tests (See US-2)
- **FR-006**: System MUST apply Bonferroni correction for multiple comparisons (α_corrected = 0.00156) and report family-wise error rate (See US-2)
- **FR-007**: System MUST frame all findings as ASSOCIATIONAL (not causal) since the design is observational with no random assignment (See US-2)
- **FR-008**: System MUST compute effect sizes (Cohen's d) and 95% confidence intervals for all significant correlations (See US-2)
- **FR-009**: System MUST implement leave-one-subject-out cross-validation for ≥15 subjects to assess correlation stability across folds (See US-3)
- **FR-010**: System MUST perform sensitivity analysis on any decision thresholds by sweeping cutoffs over {0.01, 0.05, 0.1} and reporting how false-positive/false-negative rates vary (See US-3)
- **FR-011**: System MUST run all analysis on CPU-only hardware (no GPU/CUDA) within 6 hours on 2 cores, ~7 GB RAM, ~14 GB disk (See US-1)
- **FR-012**: System MUST use validated affective instruments (PANAS, SAM) with citable validation literature and require ≥80% questionnaire response rate per subject (See US-2)
- **FR-013**: System MUST include collinearity diagnostics (VIF or correlation matrix) for microstate metrics since some are definitionally related (e.g., coverage bounded by duration × occurrence) (See US-2)

### Key Entities *(include if feature involves data)*

- **EEGRecording**: Raw resting-state EEG data with attributes (subject_id, sampling_rate, duration_seconds, electrode_count, file_path)
- **MicrostateSegmentation**: Segmented microstate classes with attributes (subject_id, class_labels[timepoints], global_explained_variance, convergence_iterations)
- **MicrostateFeatures**: Extracted temporal metrics with attributes (subject_id, microstate_class, mean_duration_ms, occurrence_rate_per_s, coverage_percent, transition_probabilities[4×4])
- **AffectiveScores**: Self-report questionnaire data with attributes (subject_id, valence_score[1-9], arousal_score[1-9], instrument_type[PANAS/SAM], completion_timestamp)
- **CorrelationResult**: Analysis outcome with attributes (microstate_class, feature_type, affective_dimension, correlation_coefficient, p_value, p_corrected, effect_size, confidence_interval)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Pipeline execution time is measured against the 6-hour GitHub Actions free-tier runner constraint (See US-1)
- **SC-002**: Memory usage is measured against the ~7 GB RAM limit during peak preprocessing (See US-1)
- **SC-003**: Global explained variance for microstate segmentation is measured against the ≥75% community-standard threshold (See US-1)
- **SC-004**: Correlation stability across cross-validation folds is measured against the leave-one-subject-out validation protocol (See US-3)
- **SC-005**: Multiple comparison correction is measured against the Bonferroni-corrected α = 0.00156 threshold (See US-2)
- **SC-006**: Effect size confidence interval width is measured against the 95% CI standard (See US-2)
- **SC-007**: Sensitivity analysis sweep coverage is measured against the {0.01, 0.05, 0.1} threshold set (See US-3)
- **SC-008**: Dataset-variable fit is measured against the requirement that OpenNeuro datasets contain both EEG and affective questionnaire data (See US-1)

## Assumptions

- OpenNeuro datasets ds003501 and ds004137 contain both resting-state EEG recordings (≥128 Hz sampling) and validated affective questionnaire data (PANAS, SAM); if not, `[NEEDS CLARIFICATION: does dataset dsXXXXX contain required affective questionnaire variables?]` will be logged.
- The analysis runs entirely on CPU-only hardware (no GPU/CUDA/bitsandbytes) within 6 hours on GitHub Actions free-tier (2 cores, ~7 GB RAM, ~14 GB disk).
- PANAS and SAM questionnaires are validated instruments with citable validation literature; no new instrument validation is required.
- Bonferroni correction (α_corrected = 0.05/32 = 0.00156) is the chosen multiple comparison method; alternative methods (e.g., FDR) are out of scope.
- The design is observational (no random assignment), so all findings are framed as ASSOCIATIONAL correlations, not causal effects.
- Sample size is sufficient for power (≥15 subjects for cross-validation); if power is inadequate, `[NEEDS CLARIFICATION: sample size power analysis]` will be logged.
- Microstate metrics may exhibit collinearity (e.g., coverage = duration × occurrence × class proportion); VIF diagnostics are required but independent predictive effects are NOT claimed.
- The 4 canonical microstate classes follow the standard A-D topology convention from previous literature.
- Bandpass filter (1-40 Hz) excludes line noise (50/60 Hz) and high-frequency artifacts while preserving microstate-relevant frequencies.
- ICA artifact removal uses standard components (ocular, muscle) identified by automated algorithms (e.g., ADJUST, MARA) with ≥90% detection accuracy.
- No training of deep neural networks (GNN/transformer) is required; only classical statistics (correlation, effect sizes) and K-means clustering are used.
- The threshold for "significant correlation" is |r| > 0.3, p < 0.05 (uncorrected) or p_corrected < 0.00156 (Bonferroni-corrected); sensitivity analysis sweeps this threshold over {0.01, 0.05, 0.1}.
- Leave-one-subject-out cross-validation requires ≥15 subjects; if fewer subjects are available, the validation step is skipped with a documented power limitation.
- All questionnaires require ≥80% completion rate per subject; subjects with missing affective scores are excluded from correlation analysis.
- The analysis produces no causal claims about microstate → affective directionality; all results are correlational associations.
