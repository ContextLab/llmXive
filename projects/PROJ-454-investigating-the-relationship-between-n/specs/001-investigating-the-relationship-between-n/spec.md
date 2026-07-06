# Feature Specification: Neural Entropy and Cognitive Flexibility in Aging

**Feature Branch**: `001-neural-entropy-cognitive-flexibility`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Neural Entropy and Cognitive Flexibility in Aging"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - EEG Data Pipeline and Entropy Computation (Priority: P1)

Researcher downloads resting-state EEG datasets from OpenNeuro, preprocesses the raw EEG signals to remove artifacts, and computes neural entropy metrics (sample entropy and approximate entropy) across five standard frequency bands (delta, theta, alpha, beta, gamma).

**Why this priority**: This is the foundational data preparation step without which no analysis can proceed. All downstream statistical work depends on clean, correctly computed entropy values.

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a subset of EEG data and verifying that entropy values are computed for all multiple frequency bands with no NaN outputs for valid participants.

**Acceptance Scenarios**:

1. **Given** an OpenNeuro EEG dataset (ds or ds003104) with participants aged +, **When** the preprocessing pipeline runs, **Then** EEG signals are filtered (low-frequency to a designated high-frequency bandpass, /60 Hz notch), bad channels are interpolated, and ICA artifacts are removed.
2. **Given** preprocessed EEG data segmented into -second non-overlapping epochs, **When** entropy computation runs, **Then** sample entropy and approximate entropy values are output for each of the frequency bands (delta: -4 Hz, theta: low-frequency range, alpha: -12 Hz, beta: Hz, gamma: a high-frequency band within the gamma range).
3. **Given** participants with missing or corrupted EEG segments exceeding a substantial proportion of recording time, **When** data quality checks run, **Then** those participants are flagged and excluded from entropy computation.

---

### User Story 2 - Statistical Correlation Analysis (Priority: P2)

Researcher performs partial Pearson correlation analyses between neural entropy metrics and Wisconsin Card Sorting Test (WCST) perseverative errors, controlling for age, education, and task accuracy (derived from a separate attention task), with Benjamini-Hochberg False Discovery Rate (FDR) correction applied across all frequency band comparisons.

**Why this priority**: This is the core hypothesis test that directly addresses the research question. Without valid correlation analysis, the biomarker relationship cannot be established.

**Independent Test**: Can be fully tested by running the correlation pipeline on computed entropy values and behavioral scores, verifying that p-values are FDR-corrected and effect sizes (partial r) are reported with confidence intervals.

**Acceptance Scenarios**:

1. **Given** entropy metrics and WCST perseverative error scores, **When** partial Pearson correlation runs with covariates (age, education, task accuracy from separate task), **Then** correlation coefficients and p-values are output for each entropy-frequency band combination.
2. **Given** A number of hypothesis tests (5 frequency bands × entropy measures) will be conducted., **When** multiple comparison correction runs, **Then** Benjamini-Hochberg FDR correction is applied (α ≤ 0.05) and adjusted p-values are reported.
3. **Given** statistically significant correlations (p < 0.05 after correction), **When** effect size calculation runs, **Then** partial r values are computed and classified (≥ 0.3 = clinically meaningful).

---

### User Story 3 - Sensitivity Analysis and Reporting (Priority: P3)

Researcher conducts sensitivity analyses excluding participants with neurological conditions or confounding medications, sweeps entropy thresholds over a small parameter range, and generates final results with all methodological documentation.

**Why this priority**: This ensures result robustness and methodological soundness, addressing potential confounds and threshold sensitivity that could invalidate findings.

**Independent Test**: Can be fully tested by running the sensitivity pipeline on the same dataset with exclusion criteria applied and verifying that headline correlation rates are compared across exclusion scenarios.

**Acceptance Scenarios**:

1. **Given** the full participant cohort, **When** sensitivity analysis excludes participants with neurological conditions or medication use affecting EEG, **Then** correlation results are recomputed and compared to the main analysis.
2. **Given** any decision cutoff in the pipeline (e.g., data quality threshold, artifact rejection criteria), **When** sensitivity sweep runs, **Then** the cutoff is varied over a range of absolute differences and the variation in correlation coefficients (r) and p-values is reported across the sweep.
3. **Given** completed analysis, **When** final report is generated, **Then** it includes correlation matrices, effect sizes, FDR-corrected p-values, and sensitivity analysis comparisons in a single reproducible output.

---

### Edge Cases

- What happens when an OpenNeuro dataset lacks behavioral task data for cognitive flexibility (e.g., only EEG recordings available)? → The system MUST verify that the selected OpenNeuro dataset (ds000246 or ds003104) contains validated cognitive flexibility behavioral scores (e.g., WCST perseverative errors) prior to analysis. If a dataset lacks these specific behavioral measures, the system MUST flag that specific dataset as excluded and proceed only with the remaining datasets satisfying this variable-fit requirement (See US-1, FR-010). If no datasets remain, the pipeline fails with an error.
- How does system handle participants with missing covariate data (age, education, task accuracy)? → Pipeline must exclude those participants from partial correlation analysis and report exclusion count.
- What happens when entropy computation produces NaN or infinite values due to numerical instability? → Pipeline must flag those epochs and recompute using `float64` precision. If NaN persists, the participant is excluded.
- How does system handle EEG recordings shorter than 60 seconds (insufficient for 2-second epochs)? → Pipeline must exclude participants with <60 seconds of valid resting-state EEG.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download resting-state EEG datasets from OpenNeuro (ds, ds) containing both EEG recordings and behavioral task data for participants aged + years (See US-1)
- **FR-002**: System MUST preprocess EEG data by applying a bandpass filter within a low-frequency to mid-frequency range, notch filter (mains frequency), bad channel interpolation, and ICA artifact removal (See US-1)
- **FR-003**: System MUST compute sample entropy and approximate entropy metrics across 5 frequency bands (delta: 1-4 Hz, theta: 4-8 Hz, alpha: 8-12 Hz, beta: 12 Hz, gamma: high-frequency band) (See US-1)
- **FR-004**: System MUST perform partial Pearson correlation between entropy metrics and WCST perseverative errors controlling for age, education, and task accuracy (derived from a separate attention task) as covariates (See US-2)
- **FR-005**: System MUST apply Benjamini-Hochberg False Discovery Rate (FDR) correction for multiple comparisons across Multiple hypothesis tests (multiple frequency bands × entropy measures) with α ≤ 0.05 (See US-2)
- **FR-006**: System MUST conduct sensitivity analysis excluding participants with neurological conditions or medication use affecting EEG measures (See US-3)
- **FR-007**: System MUST perform threshold sensitivity sweep over {, 0.05, 0.1} absolute difference for any decision cutoffs and report the variation in correlation coefficients (r) and p-values across the sweep (See US-3)
- **FR-008**: System MUST run all computations on CPU-only hardware (GitHub Actions ubuntu-latest runner) with ≤7 GB RAM and ≤14 GB disk usage (via streaming/chunked processing), completing within 6 hours (See US-1, US-2, US-3)
- **FR-009**: System MUST frame all findings as associational (not causal) given the observational study design without random assignment (See US-2)
- **FR-010**: System MUST verify dataset-variable fit by confirming OpenNeuro datasets contain all required variables (entropy predictors, cognitive flexibility outcomes, age/education covariates) before analysis begins (See US-1)
- **FR-011**: System MUST use validated cognitive flexibility instruments (e.g., Wisconsin Card Sorting Test with citable validation) for behavioral scores (See US-2)
- **FR-012**: System MUST include collinearity diagnostics when reporting joint relationships between entropy measures from definitionally related frequency bands, specifically because SampEn and ApEn are mathematically related estimators (See US-2)

### Key Entities

- **Participant**: Individual aged 50+ with EEG recording and behavioral assessment; key attributes include age, education level, neurological condition status, medication use
- **EEG Recording**: Resting-state EEG data with key attributes including sampling rate, duration, channel count, artifact flags
- **Entropy Metric**: Computed neural entropy value with key attributes including frequency band, entropy type (sample/approximate), participant ID
- **Cognitive Flexibility Score**: Behavioral assessment score with key attributes including test type (WCST perseverative errors), participant ID, task accuracy

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Neural entropy values are measured against quality thresholds (≥95% of epochs must have valid entropy computation) and reference against baseline signal-to-noise ratio (median SNR of preprocessed data relative to 1-45 Hz band power must be ≥ 5 dB) (See US-1)
- **SC-002**: Correlation strength between neural entropy and cognitive flexibility is measured against effect size benchmark (partial r ≥ 0.3) and statistical significance benchmark (p < 0.05 after FDR correction) (See US-2)
- **SC-003**: Result robustness is measured against sensitivity analysis by comparing headline correlation rates across exclusion scenarios (neurological conditions, medication use) and threshold sweeps (, low, medium) (See US-3)
- **SC-004**: Computation feasibility is measured against free-tier CI constraints (CPU cores, ~7 GB RAM, ≤6 hours) with total disk usage documented (See US-1, US-2, US-3)
- **SC-005**: Methodological validity is measured against observational study framing by verifying all findings are reported as associational (not causal) and covariate controls are applied (See US-2)

## Assumptions

- OpenNeuro datasets contain both resting-state EEG recordings and behavioral cognitive flexibility assessments for participants aged + years
- Resting-state EEG recordings are ≥60 seconds in duration to support 2-second epoch segmentation
- Wisconsin Card Sorting Test or equivalent validated cognitive flexibility assessment is available in dataset metadata
- No GPU acceleration is available; all entropy computation and statistical analysis must complete on CPU-only hardware
- Participant The sample size is sufficient for partial correlation analysis with a set of hypothesis tests. after FDR correction (power analysis deferred to implementation phase)
- All participants provide informed consent and data usage complies with OpenNeuro licensing terms
- EEG artifacts (ocular, muscular) can be adequately removed using ICA without significant signal loss
- Age and education covariate data are complete for ≥80% of participants in the dataset
- No random assignment or identification strategy is available; causal claims are out of scope
- Power analysis sample size requirements are deferred to implementation with explicit acknowledgement of power limitations in final report
- Task accuracy used as a covariate is derived from a separate attention task to avoid collinearity with the WCST outcome