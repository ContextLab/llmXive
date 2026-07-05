# Feature Specification: Predicting Avian Vocal Complexity from Environmental Noise Levels

**Feature Branch**: `001-predict-avian-vocal-complexity`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Avian Vocal Complexity from Environmental Noise Levels"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing (Priority: P1)

The system must retrieve bird vocalization recordings from Xeno-canto and assign ambient noise levels to each recording based on geographic metadata, then extract standardized vocal complexity metrics.

**Why this priority**: This is the foundational step; without clean, matched data linking noise levels to vocal metrics, no statistical modeling can occur. It delivers the primary dataset required for all downstream analysis.

**Independent Test**: Can be fully tested by executing the data pipeline script on a subset of 50 recordings and verifying that the output CSV contains valid noise dB(A) values, species IDs, and calculated complexity metrics (syllable count, duration, bandwidth) without errors.

**Acceptance Scenarios**:

1. **Given** a list of 50 Xeno-canto recording IDs, **When** the data acquisition module runs, **Then** the output file contains exactly 50 rows with non-null values for `noise_level_db`, `species_id`, `syllable_count`, `song_duration`, and `frequency_bandwidth`, AND the distribution satisfies ≥5 recordings per species per location.
2. **Given** a recording located in a known urban zone, **When** the noise estimation module cross-references the coordinates with the Global Soundscapes dataset, **Then** the assigned `noise_level_db` value falls within the expected urban range (≥50 dB(A)).
3. **Given** a recording with a signal-to-noise ratio <10 dB, **When** the filtering step executes, **Then** that recording is excluded from the final dataset and logged in a `filtered_records.csv` file.
4. **Given** a species with <5 valid recordings in a specific location, **When** the filtering step executes, **Then** that species is excluded from the final dataset for that location and logged in `filtered_records.csv`.

---

### User Story 2 - Statistical Modeling and Inference (Priority: P2)

The system must fit a linear mixed-effects model to quantify the association between ambient noise levels and vocal complexity metrics, controlling for species and location as random effects. The system must validate model robustness using Leave-One-Species-Out cross-validation.

**Why this priority**: This addresses the core research question. It transforms raw data into scientific evidence regarding the noise-vocalization relationship, providing the primary results for the study.

**Independent Test**: Can be fully tested by running the modeling script on the preprocessed dataset and verifying that the output includes model coefficients, p-values, effect sizes (Cohen's d) with confidence intervals, and model fit statistics (R², AIC) without crashing due to memory or convergence errors.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset of ≥50 species, **When** the mixed-effects model is fitted with `noise_level` as a fixed effect, **Then** the output report includes a p-value <0.05 for the noise coefficient IF the null hypothesis is rejected, specifically checking for a negative coefficient direction (one-tailed test), or a clear statement of non-significance.
2. **Given** multiple hypothesis tests (one per vocal metric), **When** the analysis completes, **Then** the results include a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) applied to the reported p-values.
3. **Given** a model fit, **When** residual diagnostics are performed, **Then** the output includes a Q-Q plot and residual vs. fitted plot confirming that assumptions of normality and homoscedasticity are reasonably met.
4. **Given** the model fit, **When** validation is performed, **Then** the system uses Leave-One-Species-Out (LOSO) cross-validation to estimate generalizability, preventing data leakage from species appearing in both train and test sets.

---

### User Story 3 - Visualization and Reporting (Priority: P3)

The system must generate publication-quality visualizations (scatter plots with regression lines, regional heatmaps) and a summary report detailing the correlation findings and model diagnostics.

**Why this priority**: While the statistical results are the core value, visualizations are essential for interpreting the magnitude and direction of effects, and the report consolidates findings for the research team.

**Independent Test**: Can be fully tested by executing the visualization script and verifying that the output directory contains at least three distinct image files (scatter plot, heatmap, residual plot) and a text summary file with the key statistical findings.

**Acceptance Scenarios**:

1. **Given** the model results, **When** the visualization module runs, **Then** a scatter plot is generated with `noise_level` on the x-axis, `vocal_complexity` on the y-axis, a regression line, and 95% confidence intervals.
2. **Given** data grouped by geographic region, **When** the heatmap is generated, **Then** the heatmap correctly maps average noise levels to average complexity metrics, with color intensity proportional to the magnitude of the correlation.
3. **Given** the full analysis output, **When** the summary report is generated, **Then** it explicitly states the direction of the correlation (positive/negative), the effect size with confidence intervals, and the corrected p-value for the primary hypothesis.

---

### Edge Cases

- What happens when a recording location in Xeno-canto does not have a corresponding entry in the Global Soundscapes dataset? (System must interpolate from nearest neighbors or flag for manual review).
- How does the system handle species with only a single recording in the dataset? (System must exclude these from mixed-effects modeling to avoid singular fits, consistent with the <5 recordings per location rule in FR-004).
- What happens if the audio file format is unsupported or corrupted during feature extraction? (System must skip the file, log the error, and continue processing without crashing).
- How does the system handle extreme outliers in noise levels (e.g., >100 dB)? (System must cap or flag these values to prevent model skew, applying a sensitivity analysis on the threshold).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download bird vocalization metadata and audio files from Xeno-canto API for a target list of species, ensuring at least 5 recordings per species per location (See US-1).
- **FR-002**: System MUST assign ambient noise levels (dB(A)) to each recording by cross-referencing geographic coordinates with the Global Soundscapes dataset as the primary source. If an alternative urban noise model is used, the system MUST validate the result against the primary dataset with a deviation ≤2 dB(A) (See US-1).
- **FR-003**: System MUST compute vocal complexity metrics (syllable count, song duration, frequency bandwidth, spectral entropy) using CPU-efficient audio processing libraries (e.g., librosa) without GPU acceleration (See US-1).
- **FR-004**: System MUST filter the dataset to retain only recordings with a signal-to-noise ratio >10 dB and exclude species with <5 valid recordings per location (See US-1).
- **FR-005**: System MUST fit linear mixed-effects models with noise level as a fixed effect and species/location as random intercepts, reporting coefficients, p-values, and effect sizes (See US-2).
- **FR-006**: System MUST apply multiple-comparison correction (e.g., Bonferroni or FDR) to p-values when testing >1 vocal complexity metric to control family-wise error (See US-2).
- **FR-007**: System MUST perform a sensitivity analysis on the signal-to-noise ratio threshold by sweeping the cutoff value (5 dB, 10 dB, 15 dB) and reporting the variation in sample size and headline correlation rates. This analysis is required to validate the robustness of the filtering logic (US-1) and the modeling results (US-2) against arbitrary threshold selection. The system MUST pass if the variation in correlation estimates across thresholds is ≤15% (See US-1, US-2).
- **FR-008**: System MUST generate scatter plots with regression lines and regional heatmaps visualizing the relationship between noise and vocal complexity (See US-3).
- **FR-009**: System MUST interpolate noise levels from nearest neighbors (within 50km) if the Global Soundscapes dataset lacks a value for a specific coordinate, and log these interpolated values separately (See US-1).

### Key Entities

- **Recording**: Represents a single audio file with attributes: `recording_id`, `species_id`, `latitude`, `longitude`, `audio_file_path`.
- **NoiseProfile**: Represents the ambient noise context for a location with attributes: `location_id`, `noise_level_db`, `source_dataset`.
- **VocalMetric**: Represents extracted features from a recording with attributes: `recording_id`, `syllable_count`, `duration_seconds`, `frequency_bandwidth_hz`, `spectral_entropy`.
- **ModelResult**: Represents the output of the statistical analysis with attributes: `metric_name`, `fixed_effect_coefficient`, `p_value`, `effect_size`, `random_effect_variance`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient (r) between noise level and vocal complexity is measured against the statistical null (r=0) with a 95% confidence interval to determine significance (See US-2).
- **SC-002**: The p-value for the noise effect in the mixed-effects model is calculated and reported, with the interpretation of significance performed as a separate analytical step (See US-2).
- **SC-003**: The effect size (Cohen's d) is estimated with 95% confidence intervals to determine practical significance, avoiding fixed pass/fail thresholds (See US-2).
- **SC-004**: The number of valid species included in the final analysis is measured against the minimum requirement of 50 species to ensure robust inference (See US-2).
- **SC-005**: The variation in false-positive rates across the noise threshold sensitivity sweep (FR-007) is measured against the baseline rate observed at the 10 dB threshold, with a tolerance of ≤10% variation (See FR-007).
- **SC-006**: The interpolation fallback mechanism (FR-009) is validated by confirming that all missing noise values within 50km of a known point are successfully interpolated and logged (See FR-009).

## Assumptions

- **Data Availability**: The Global Soundscapes dataset or equivalent public noise maps contain sufficient coverage for the geographic locations of the selected Xeno-canto recordings.
- **Compute Feasibility**: The total dataset size (audio files + metadata) fits within the memory and disk limits of the GitHub Actions free-tier runner, allowing processing in chunks of 100 files.
- **Methodological Framing**: Since the study uses observational data without random assignment, all findings are framed as associational; no causal claims regarding noise causing vocal changes are made.
- **Instrument Validity**: The vocal complexity metrics (syllable count, bandwidth) derived via `librosa` are valid proxies for biological vocal complexity as defined in external literature, assuming standard audio sampling rates (≥22 kHz).
- **Collinearity**: Noise level and species identity are not definitionally collinear; species are treated as random effects to account for phylogenetic or behavioral clustering without claiming independent predictive effects for noise and species simultaneously in a way that violates collinearity diagnostics.
- **Threshold Justification**: The 10 dB signal-to-noise ratio cutoff is based on standard bioacoustic practices for distinguishing vocalizations from background noise; a sensitivity analysis will sweep this value to confirm robustness.
- **No GPU Requirement**: The analysis relies on CPU-tractable methods (linear mixed-effects models, standard audio feature extraction) and does not require deep learning training or GPU-accelerated inference.