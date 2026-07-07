# Feature Specification: Neural Correlates of Anticipatory Reward Processing in Vocal Learning

**Feature Branch**: `001-neural-correlates-anticipatory-reward`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Analyze pre-existing electrophysiology datasets to regress trial-by-trial neural firing rates in songbird Area X against known reward magnitudes to determine if anticipatory activity scales with expected reward."

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Pre-processing Pipeline (Priority: P1)

**User Journey**: As a researcher, I want to load pre-processed spike train data and trial metadata from public repositories (OpenNeuro/Zenodo) so that I can prepare the dataset for statistical analysis without manual data wrangling.

**Why this priority**: Without a reliable pipeline to ingest and align neural data with behavioral metadata (reward magnitude), no analysis can proceed. This is the foundational step for the entire study.

**Independent Test**: The pipeline can be tested by running the ingestion script against a small, synthetic dataset containing known spike counts and reward values, verifying that the output DataFrame correctly links each trial's firing rate to its specific reward magnitude.

**Acceptance Scenarios**:
1. **Given** a directory containing CSV/Neurodata files with spike timestamps and a metadata file with reward magnitudes, **When** the ingestion script executes, **Then** a unified Pandas DataFrame is produced with columns for `trial_id`, `neuron_id`, `spike_count`, `reward_magnitude`, and `timestamp_relative_to_reward`.
2. **Given** a missing or malformed metadata file, **When** the ingestion script executes, **Then** the process fails with a clear error message identifying the missing file and halts execution rather than proceeding with incomplete data.

---

### User Story 2 - Statistical Modeling and Significance Testing (Priority: P2)

**User Journey**: As a researcher, I want to fit a Generalized Linear Model (GLM) regressing firing rates on reward magnitude and run a permutation test to validate the coefficient, so that I can determine if the relationship is statistically significant.

**Why this priority**: This is the core scientific contribution. It directly answers the research question regarding value encoding. Without this, the project is merely a data loader.

**Independent Test**: The analysis module can be tested by running it on a dataset where the reward magnitude is known to have no correlation with firing rates (null data), verifying that the resulting p-value exceeds the significance threshold (e.g., p > 0.05).

**Acceptance Scenarios**:
1. **Given** a dataset with aligned neural and behavioral data, **When** the GLM fitting function is called, **Then** a model object is returned containing the estimated coefficient for `reward_magnitude` and its standard error.
2. **Given** the fitted model, **When** the permutation test (1000 iterations) is executed, **Then** a null distribution of coefficients is generated, and a p-value is calculated representing the proportion of null coefficients exceeding the observed absolute coefficient.

---

### User Story 3 - Visualization and Reporting (Priority: P3)

**User Journey**: As a researcher, I want to generate scatter plots of firing rate vs. reward magnitude with confidence intervals and a summary statistics report, so that I can visually inspect the relationship and interpret the results.

**Why this priority**: Visualization is essential for exploratory data analysis and communicating findings. It allows the researcher to spot non-linearities or outliers that a scalar p-value might miss.

**Independent Test**: The reporting module can be tested by generating a plot from a small dataset and verifying that the output image file exists and contains the expected axes labels, data points, and confidence interval bands.

**Acceptance Scenarios**:
1. **Given** the fitted GLM results and the raw data, **When** the visualization function is executed, **Then** a scatter plot is saved as a PNG file showing `reward_magnitude` on the x-axis, `firing_rate` on the y-axis, and a regression line with a 95% confidence interval.
2. **Given** the analysis results, **When** the summary report is generated, **Then** a text file is produced containing the coefficient estimate, p-value, sample size, and the outcome of the permutation test.

---

### Edge Cases

- What happens when the dataset contains trials with zero reward magnitude (baseline condition) versus positive magnitudes? The analysis must handle the zero value correctly as a valid predictor level, not as missing data.
- How does the system handle neurons with zero spikes across all trials (silent neurons)? These must be filtered out or explicitly handled to prevent division-by-zero errors when calculating firing rates.
- What if the metadata indicates reward magnitudes that are not distinct (e.g., all trials have 0.5μL)? The system must detect lack of variance in the predictor and halt, as regression requires variance to estimate a slope.

## Requirements

### Functional Requirements

- **FR-001**: System MUST load pre-processed spike train data and trial metadata from public repositories and align them by trial ID. (See US-1)
- **FR-002**: System MUST calculate anticipatory firing rates by counting spikes in the -500ms to 0ms pre-reward time window for each neuron-trial pair. (See US-2)
- **FR-003**: System MUST fit a Negative Binomial Generalized Linear Model (GLM) with firing rate as the dependent variable and reward magnitude as the independent predictor. If the dispersion parameter is < 1.1, the system MAY fall back to a Poisson GLM. (See US-2)
- **FR-004**: System MUST perform a permutation test with at least 1000 iterations to generate a null distribution for the reward coefficient. (See US-2)
- **FR-005**: System MUST generate a scatter plot of firing rate vs. reward magnitude with a regression line and confidence intervals. (See US-3)
- **FR-006**: System MUST output a summary report containing the coefficient estimate, p-value, and permutation test result. (See US-3)
- **FR-007**: System MUST validate that the dataset contains at least 30 trials per reward magnitude level. If this condition is not met, the system MUST halt and report the specific level(s) with insufficient trials. (See US-1)
- **FR-008**: System MUST implement 5-fold cross-validation to evaluate the predictive performance of the GLM on held-out data, ensuring the model is not overfitting. (See US-2)
- **FR-009**: System MUST validate that the dataset's inter-trial intervals and cue-reward delays are consistent with the fixed -500ms anticipatory window. If a cue occurs within 500ms of reward in a way that confounds anticipation, the system MUST flag the dataset as invalid for this specific analysis. (See US-2)
- **FR-010**: System MUST test for over-dispersion in the spike count data and report the dispersion parameter before model fitting. (See US-2)

### Key Entities

- **Trial**: A single instance of vocalization and reward delivery, characterized by a unique ID, associated reward magnitude, and timestamp.
- **Neuron**: A single recorded unit within Area X, characterized by a unique ID and its spike train data.
- **FiringRate**: The computed count of spikes per neuron per trial within the specified anticipatory time window.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The coefficient for `reward_magnitude` in the GLM is measured against the null hypothesis of zero effect using a permutation test p-value < 0.05. (See US-2)
- **SC-002**: The statistical power of the analysis is measured by calculating the Minimum Detectable Effect Size (MDES) given the actual sample size and observed variance. (See US-2)
- **SC-003**: The visual output is measured against the requirement to plot all valid data points and correctly render confidence interval bands calculated using the 2.5th and 97.5th percentiles. (See US-3)
- **SC-004**: The data ingestion process is measured against the requirement to successfully load and align all trials where reward_magnitude is not null and timestamp is within [-500ms, 0ms] without data loss. (See US-1)
- **SC-005**: If multiple neurons are analyzed, the system MUST apply Bonferroni correction to ensure the family-wise error rate (FWER) ≤ 0.05. (See US-2)

## Assumptions

- The pre-existing electrophysiology datasets from OpenNeuro or Zenodo contain sufficient trial-level metadata linking specific reward magnitudes (e.g., 0.1μL, 0.5μL) to neural recordings.
- The anticipatory time window of -500ms to 0ms relative to reward delivery is appropriate for capturing reward expectation in songbirds, based on prior literature, subject to validation by FR-009.
- The available CPU-only CI runner (multi-core, sufficient RAM) is sufficient to process the dataset size and perform 1000 permutation iterations within the 6-hour job limit.
- The Negative Binomial GLM is an appropriate approximation for the spike count data distribution, subject to validation by FR-010.
- No GPU accelerators or heavy deep learning models are required; the analysis relies on classical statistical methods (scikit-learn/Statsmodels).
- The dataset contains sufficient variance in reward magnitude to estimate a slope.