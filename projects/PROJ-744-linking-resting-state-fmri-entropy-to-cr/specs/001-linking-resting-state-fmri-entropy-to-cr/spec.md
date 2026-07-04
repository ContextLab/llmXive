# Feature Specification: Linking Resting‑State fMRI Entropy to Creative Problem Solving

**Feature Branch**: `001-linking-resting-state-fmri-entropy-to-creative-problem-solving`  
**Created**: 2026-06-20  
**Status**: Draft  
**Input**: User description: "Linking Resting‑State fMRI Entropy to Creative Problem Solving"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

The researcher MUST be able to download pre-processed resting-state fMRI 4-D volumes and associated behavioral phenotypes (NIH Toolbox Creativity Composite scores) from the Human Connectome Project (HCP) via the OpenNeuro/HCP S3 bucket, apply the HCP multimodal cortical atlas (360 parcels) to extract voxel time series, and compute covariates (age, sex, head-motion) from the phenotypic file.

**Why this priority**: Without reliable data ingestion and parcellation, no entropy calculation or statistical modeling can occur. This is the foundational step that determines data validity.

**Independent Test**: The system can be tested by verifying that the script successfully retrieves a sample of subjects, extracts parcel time series per subject, and outputs a clean CSV containing the global mean entropy and all covariates, without requiring any downstream statistical modeling.

**Acceptance Scenarios**:

1. **Given** a valid OpenNeuro/HCP S3 access configuration, **When** the ingestion script runs for a batch of 50 subjects, **Then** the script outputs a structured dataset containing time-series data for all 360 parcels and behavioral scores for all 50 subjects.
2. **Given** a subject with excessive head motion (>0.2 mm framewise displacement), **When** the preprocessing step calculates motion metrics, **Then** the subject is flagged in the output log but included in the dataset for subsequent robustness checks, rather than being silently dropped.
3. **Given** the HCP 4-D volume files, **When** the parcellation step applies the 360-parcel atlas, **Then** the output time series for each parcel matches the expected dimension (timepoints × 360) and contains no NaN values due to atlas misalignment.

---

### User Story 2 - Entropy Computation and Aggregation (Priority: P2)

The researcher MUST be able to compute Multiscale Sample Entropy (MSE) for each parcel's time series using a vectorized Python implementation, including a coarse-graining procedure for a range of scale factors, and derive two aggregate metrics: (a) a global mean entropy across all 360 parcels, and (b) network-specific averages for canonical networks (DMN, FPN, CON, VAN, SMN, VN).

**Why this priority**: This step transforms raw time-series data into the primary predictor variables required for the research question. It is computationally intensive but distinct from the statistical modeling phase.

**Independent Test**: The system can be tested by running the entropy calculation on a fixed subset of subjects with known parameters, verifying that the computed MSE values match a pre-calculated reference file within an appropriate tolerance, and that network aggregation correctly averages the parcel values.

**Acceptance Scenarios**:

1. **Given** a time series of length 1000 for a single parcel, **When** the MSE algorithm runs with default parameters (template length m=2, tolerance r=0.2, scale factors 1-20), **Then** the output entropy value matches the pre-calculated reference file within a tolerance of 1e-6.
2. **Given** the global mean entropy and network-specific averages for 100 subjects, **When** the aggregation step runs, **Then** the network-specific average for the DMN is exactly the arithmetic mean of the 60 DMN parcel entropies for that subject.
3. **Given** a request to compute entropy with alternative parameters (r over {0.15, 0.20, 0.25}), **When** the robustness check runs, **Then** the system outputs a separate set of entropy metrics without overwriting the primary results.

---

### User Story 3 - Statistical Modeling and Inference (Priority: P3)

The researcher MUST be able to fit robust linear regression models (RLM) with entropy metrics as the predictor and the NIH Toolbox Creativity Composite as the outcome, using HC3 robust standard errors to account for heteroscedasticity, followed by a permutation-based cluster correction for network-specific tests, and generate a summary report of associations. Additionally, the researcher MUST perform a reverse-causality check by swapping the predictor and outcome variables.

**Why this priority**: This step directly answers the research question by testing the association between entropy and creativity. It relies on the successful completion of the previous two steps and ensures statistical validity for cross-sectional data.

**Independent Test**: The system can be tested by running the modeling pipeline on a synthetic dataset where the relationship between entropy and creativity is known (e.g., a generated positive correlation), and verifying that the model recovers a statistically significant positive coefficient with the correct p-value range.

**Acceptance Scenarios**:

1. **Given** a dataset of 100 subjects with global entropy and NIH Toolbox Creativity scores, **When** the robust linear regression model runs, **Then** the output includes a fixed effect coefficient for entropy, a robust p-value, and a 95% confidence interval.
2. **Given** p-values from 6 network-specific tests, **When** the permutation-based cluster correction (10,000 permutations) runs, **Then** the output includes adjusted p-values where the number of significant findings (p < 0.05) is controlled for spatial autocorrelation.
3. **Given** a null dataset where entropy and creativity scores are uncorrelated, **When** the model runs 1000 Monte Carlo iterations, **Then** the proportion of runs yielding p < 0.05 is ≤ 0.05, correctly indicating no association.
4. **Given** the primary model results, **When** the reverse-causality check runs (swapping entropy and creativity), **Then** the coefficient for the reversed model is non-significant (p > 0.05), confirming the directionality of the primary finding.

### Edge Cases

- What happens when the S3 bucket is temporarily unavailable or the download rate is throttled below 1 MB/s? (System must retry up to 3 times with exponential backoff, then fail gracefully with a clear error message).
- How does the system handle subjects with missing NIH Toolbox scores or incomplete fMRI scans? (Subjects with missing primary outcome or predictor data are excluded from the main analysis but logged in a separate "excluded" report).
- What happens if the entropy calculation returns NaN for a specific parcel due to a flat time series? (The system replaces NaN with the median entropy of that parcel across all subjects and logs a warning).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download pre-processed resting-state fMRI volumes and behavioral phenotypes (NIH Toolbox Creativity Composite) from the HCP OpenNeuro bucket, ensuring data integrity via checksum verification. (See US-1)
- **FR-002**: System MUST apply the HCP multimodal cortical atlas to extract voxel time series per parcel for every subject in the dataset. (See US-1)
- **FR-003**: System MUST compute Multiscale Sample Entropy (MSE) for each parcel's time series using a vectorized Python implementation, including a coarse-graining procedure for a range of scale factors, with configurable parameters (m, r). (See US-2)
- **FR-004**: System MUST derive (a) a global mean entropy (arithmetic mean across parcels) and (b) network-specific averages for canonical networks (DMN, FPN, CON, VAN, SMN, VN) for each subject. This aggregation method is chosen as the standard convention for global complexity metrics in fMRI literature when parcels are of equal size. (See US-2)
- **FR-005**: System MUST fit robust linear regression (RLM) models with entropy metrics as predictors and the NIH Toolbox Creativity Composite as the outcome, using HC3 robust standard errors. (See US-3)
- **FR-006**: System MUST apply permutation-based cluster correction (10,000 permutations) to the p-values of all network-specific association tests to control for spatial autocorrelation and network dependence. (See US-3)
- **FR-007**: System MUST perform a sensitivity analysis sweeping the entropy tolerance parameter (r) over {0.15, 0.20, 0.25} and report the variation in headline association rates. (See US-3)
- **FR-008**: System MUST execute the entire pipeline on a CPU-only environment (no GPU/CUDA) within 45 minutes of wall-clock time for the full HCP S1200 cohort subset (N=1000 subjects) on a 2-core CPU runner with 7 GB RAM. (See US-1, US-2, US-3)
- **FR-009**: System MUST perform a reverse-causality robustness check by swapping the entropy predictor and creativity outcome variables and reporting the resulting p-values. (See US-3)

### Key Entities

- **Subject**: Represents an individual participant, containing attributes: `subject_id`, `age`, `sex`, `framewise_displacement`, `nih_creativity_score`.
- **ParcelTimeSeries**: Represents the extracted BOLD signal for a specific parcel, containing attributes: `subject_id`, `parcel_id`, `network_name`, `time_series_values`.
- **EntropyMetric**: Represents a computed entropy value, containing attributes: `subject_id`, `parcel_id` (or `network_name`), `entropy_value`, `scale_factor`, `parameters_used`.
- **AssociationResult**: Represents a statistical test outcome, containing attributes: `network_name`, `coefficient`, `standard_error`, `p_value`, `adjusted_p_value`.
- **CanonicalNetwork**: Defines the set of canonical networks: DMN (Default Mode Network), FPN (Frontoparietal Network), CON (Cingulo-Opercular Network), VAN (Ventral Attention Network), SMN (Somatomotor Network), VN (Visual Network).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The association between global entropy and NIH Toolbox Creativity scores is measured against the null hypothesis of zero correlation using a robust linear regression model with HC3 standard errors. (See US-3)
- **SC-002**: The false discovery rate of network-specific associations is measured against the permutation-based cluster correction (10,000 permutations) threshold of 0.05. (See US-3)
- **SC-003**: The robustness of the entropy-creativity association is measured against the variation in p-values when the tolerance parameter (r) is swept across {0.15, 0.20, 0.25}. (See US-3)
- **SC-004**: The computational feasibility is measured against the constraint of ≤45 minutes total wall-clock time on a 2-core CPU runner with 7 GB RAM for N=1000 subjects. (See US-1, US-2, US-3)
- **SC-005**: The data completeness is measured against the requirement that ≥95% of the N=1000 subjects in the initial HCP S1200 cohort download have valid entropy values for all 360 parcels. (See US-1)
- **SC-006**: The stability of the global mean entropy metric is measured against the Coefficient of Variation (CV) of parcel-wise entropies, which must be reported for every subject. (See US-2)

## Assumptions

- The Human Connectome Project (HCP) OpenNeuro bucket provides stable, public access to pre-processed 4-D fMRI volumes and phenotypic files without requiring additional authentication beyond standard S3 permissions.
- The HCP multimodal cortical atlas (a set of cortical parcels) is spatially aligned with the pre-processed fMRI data such that no additional registration or resampling is required.
- The `pyentropy` library (or equivalent vectorized Python implementation) is available in the GitHub Actions environment and can compute Multiscale Sample Entropy on CPU within the 45-minute runtime limit.
- The relationship between resting-state fMRI entropy and creative problem solving is purely associational; no causal claims are made as the study design is observational.
- The HCP S1200 cohort (N=1000) provides sufficient statistical power to detect a moderate effect size (Cohen's f² ≥ 0.15) at α = 0.05 after permutation correction; if power is insufficient, the limitation will be explicitly reported.
- The NIH Toolbox Creativity Composite (derived from Flanker and DCCS tests) is a valid and reliable proxy for executive function and creative control, consistent with standard scoring protocols, in the absence of direct Alternative Uses Test scores.
- Head motion (framewise displacement) is an adequate proxy for motion artifacts in the fMRI signal, and controlling for it statistically is sufficient to mitigate motion-related confounds.
- The default parameters for Multiscale Sample Entropy (m=2, r=0.2, scales 1-20) are appropriate for fMRI time series of the HCP data length; alternative parameters will be tested in sensitivity analysis but are not required for the primary result.
- The arithmetic mean of parcel-wise entropies is the standard convention for deriving a "global brain complexity" metric in fMRI literature when parcels are of equal size.
- The GitHub Actions free-tier runner (2 CPU, 7 GB RAM) can handle the memory requirements of storing 360 time series per subject for the full cohort without swapping to disk.
- No GPU acceleration is available or required; all computations (entropy, regression) are performed using standard CPU-based floating-point arithmetic.