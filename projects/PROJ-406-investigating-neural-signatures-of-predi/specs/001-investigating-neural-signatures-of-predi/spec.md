# Feature Specification: Investigating Neural Signatures of Predictive Processing in Visual Illusions

**Feature Branch**: `001-predictive-coding-cross-illusion`  
**Created**: 2026-07-21  
**Status**: Draft  
**Input**: User description: "Investigating Neural Signatures of Predictive Processing in Visual Illusions - Do individual differences in precision-weighting parameters estimated from a predictive-coding model fitted to a training illusion task predict individual susceptibility to a novel, held-out visual illusion?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

The research pipeline must successfully ingest, clean, and structure the raw behavioral data from two distinct public datasets (Müller-Lyer training set and Ponzo test set) to prepare them for model fitting and analysis. This is the foundational step; without valid data, no modeling can occur.

**Why this priority**: Data availability and quality are the primary constraints. If the datasets cannot be loaded or lack the necessary variables (e.g., individual trial responses, stimulus parameters), the entire study is impossible. This is the "MVP" of the research pipeline.

**Independent Test**: The system can be tested by running the data ingestion script against the raw dataset files and verifying that a clean, tabular dataframe is produced with the correct columns (Subject ID, Stimulus Type, Response, Ground Truth) and no missing values in critical fields.

**Acceptance Scenarios**:

1. **Given** raw CSV files for the Müller-Lyer and Ponzo datasets are present in the input directory, **When** the ingestion script is executed, **Then** two clean pandas DataFrames are generated with [deferred] of required columns populated and no duplicate Subject IDs within a single dataset.
2. **Given** a dataset file contains a column with missing values for the "Response" variable, **When** the ingestion script runs, **Then** the script flags the specific rows for exclusion and logs a warning count, ensuring the downstream model only receives valid data.
3. **Given** the dataset metadata indicates a different number of trials per subject, **When** the script processes the data, **Then** it correctly aligns the data by Subject ID and calculates summary statistics (mean response, standard deviation) for each subject without crashing.

---

### User Story 2 - Model Fitting and Parameter Extraction (Priority: P2)

The system must fit a hierarchical predictive-coding model to the training (Müller-Lyer) dataset to estimate individual precision-weighting parameters for each subject, ensuring the model converges and parameters are within valid bounds.

**Why this priority**: This is the core computational engine. It transforms raw behavioral data into the specific predictor variable (precision-weighting) required by the research question. The validity of the entire study hinges on the accuracy and stability of these parameter estimates.

**Independent Test**: The system can be tested by running the model fitting routine on the training data and verifying that the optimization algorithm converges (e.g., log-likelihood improves, no NaN values) and that the extracted parameters fall within a theoretically plausible range (e.g., precision > 0).

**Acceptance Scenarios**:

1. **Given** the cleaned Müller-Lyer dataset and the predictive-coding model definition, **When** the Maximum Likelihood Estimation (MLE) routine runs, **Then** the optimization converges within 1000 iterations and produces a unique set of precision-weighting parameters for every subject with no NaN or Inf values.
2. **Given** a subject with inconsistent or noisy response data, **When** the model fits, **Then** the parameter estimate for that subject is bounded within a pre-defined valid range (e.g., [0.01, 10.0]) to prevent extreme outliers from skewing the correlation analysis.
3. **Given** the model fitting process, **When** the routine completes, **Then** it outputs a summary statistic (e.g., AIC/BIC or final log-likelihood) for each subject to allow for later diagnostic checks on model fit quality.

---

### User Story 3 - Cross-Illusion Prediction and Validation (Priority: P3)

The system must correlate the extracted precision-weighting parameters from the training set with the susceptibility scores from the held-out (Ponzo) test set, performing bootstrap resampling and control analyses to validate the findings.

**Why this priority**: This addresses the primary research question. It validates whether the computational mechanism is a stable trait. While critical for the scientific conclusion, it depends entirely on the success of US-1 and US-2.

**Independent Test**: The system can be tested by executing the correlation analysis script on the extracted parameters and test scores, verifying that a correlation coefficient, p-value, and 95% confidence interval are generated, and that the bootstrap resampling produces a stable distribution.

**Acceptance Scenarios**:

1. **Given** the precision-weighting parameters (predictor) and Ponzo susceptibility scores (outcome), **When** the Pearson correlation analysis runs, **Then** the system outputs a correlation coefficient (r), p-value, and 95% confidence interval derived from 1000 bootstrap iterations.
2. **Given** the primary correlation result, **When** the control analysis (shuffled subject IDs) runs, **Then** the distribution of correlation coefficients from the shuffled data centers around zero, confirming the original result is not due to chance.
3. **Given** the analysis pipeline, **When** the diagnostic plots are generated, **Then** the system produces a scatter plot of predicted vs. observed susceptibility and a histogram of the bootstrap distribution, saved as PNG files in the output directory.

### Edge Cases

- What happens if the public dataset (OpenNeuro) is temporarily unavailable or the download link is broken? (System should fail gracefully with a clear error message suggesting manual download).
- How does the system handle subjects who have data in the training set but no corresponding data in the test set (or vice versa)? (Subjects with incomplete pairs must be excluded from the cross-illusion analysis).
- What if the model fitting fails to converge for a specific subject due to noisy data? (The system must exclude that subject from the correlation analysis and log the failure).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the Müller-Lyer and Ponzo behavioral datasets from the specified public repository, ensuring all subject IDs match across the two datasets for paired analysis (See US-1).
- **FR-002**: System MUST implement a hierarchical predictive-coding model using only CPU-tractable numerical libraries (NumPy/SciPy) to estimate individual precision-weighting parameters via Maximum Likelihood Estimation (See US-2).
- **FR-003**: System MUST enforce parameter bounds during optimization to ensure precision-weighting estimates remain within a theoretically valid range (e.g., > 0) and prevent numerical instability (See US-2).
- **FR-004**: System MUST perform a Pearson correlation analysis between the training-derived precision parameters and the test-set susceptibility scores, calculating the correlation coefficient and p-value (See US-3).
- **FR-005**: System MUST execute a bootstrap resampling procedure with ≥ 1000 iterations to generate 95% confidence intervals for the correlation coefficient (See US-3).
- **FR-006**: System MUST perform a control analysis by shuffling subject IDs between the training and test sets 1000 times to establish a null distribution and verify the robustness of the primary finding (See US-3).
- **FR-007**: System MUST generate diagnostic plots including model fit residuals, the primary scatter plot, and the bootstrap distribution histogram, saving them as static image files (See US-3).

### Key Entities

- **Subject**: Represents an individual participant in the study, identified by a unique ID, containing behavioral responses for both the training and test illusions.
- **PrecisionParameter**: A scalar value derived from the model fit representing the individual's precision-weighting (reliability assigned to sensory evidence vs. prior).
- **SusceptibilityScore**: A scalar value calculated from the test dataset representing the magnitude of the illusion effect (deviation from veridical length) for a specific subject.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between precision parameters and susceptibility scores is measured against the null distribution generated by the shuffled subject ID control analysis (See US-3, FR-006).
- **SC-002**: The stability of the correlation result is measured against the 95% confidence interval derived from 1000 bootstrap resampling iterations (See US-3, FR-005).
- **SC-003**: The computational feasibility of the analysis is measured against the constraint of completing the full pipeline (download, fit, analyze, plot) within 6 hours on a standard 2-core CPU runner with ≤ 7 GB RAM (See Assumptions).
- **SC-004**: The validity of the model fit is measured against the convergence criteria of the optimization algorithm (no NaN/Inf values, successful log-likelihood improvement) for ≥ 90% of subjects (See US-2, FR-002).
- **SC-005**: The methodological rigor regarding multiple comparisons is measured by the inclusion of the family-wise error correction or explicit acknowledgement of the single-test nature of the primary hypothesis (See Methodological Soundness).

## Assumptions

- **Dataset Availability**: Publicly available datasets for the Müller-Lyer and Ponzo illusions exist on OpenNeuro or similar repositories and contain the necessary raw trial-level data (stimulus parameters, subject responses) to calculate susceptibility scores and fit the model.
- **Computational Constraints**: The total dataset size (raw and processed) will fit within the 7 GB RAM and 14 GB disk limits of the GitHub Actions free-tier runner; if necessary, data will be sampled or processed in chunks.
- **Model Tractability**: The hierarchical predictive-coding model can be implemented and fitted using standard CPU-based numerical optimization (e.g., `scipy.optimize`) without requiring GPU acceleration or large language model inference.
- **Inference Framing**: The study is observational; therefore, any observed correlation will be framed as associational evidence for a shared mechanism, not as causal proof of a trait, unless the dataset includes a randomized manipulation of precision (which is not assumed here).
- **Variable Fit**: The chosen datasets contain the specific variables required (stimulus length, perceived length, trial ID) to calculate the susceptibility metric and fit the precision-weighting parameter. [NEEDS CLARIFICATION: Does the specific OpenNeuro dataset ds00XXXX contain trial-level response data for both illusions, or only summary statistics?]
- **Threshold Justification**: The decision threshold for excluding non-converging subjects is set at [deferred] of total subjects; if more subjects fail to converge, the model specification will be re-evaluated.
- **Sensitivity Analysis**: A sensitivity analysis will be performed by sweeping the parameter bounds (e.g., [0.1, 1.0], [0.5, 5.0]) to ensure the correlation result is robust to the specific choice of optimization constraints.
