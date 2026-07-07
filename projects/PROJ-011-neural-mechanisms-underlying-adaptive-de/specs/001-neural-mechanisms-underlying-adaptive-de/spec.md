# Feature Specification: Neural Mechanisms Underlying Adaptive Decision-Making in Response to Social Feedback

**Feature Branch**: `001-neural-mechanisms-adaptive-decision`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Neural Mechanisms Underlying Adaptive Decision-Making in Response to Social Feedback"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The research team must be able to ingest raw fMRI data and behavioral logs from a sufficient cohort of participants, preprocess them using standard pipelines, and extract time-series data from specific Regions of Interest (ROIs) to prepare for analysis.

**Why this priority**: Without clean, preprocessed data and extracted BOLD signals from the dorsolateral prefrontal cortex (dlPFC), ventral striatum, and anterior cingulate cortex (ACC), no statistical modeling or hypothesis testing can occur. This is the foundational step for the entire study.

**Independent Test**: The pipeline can be validated by running it on a small subset of dummy or sample data and verifying that output files contain the expected ROI time-series matrices and behavioral matrices with no missing values or motion artifacts exceeding the threshold.

**Acceptance Scenarios**:

1. **Given** raw fMRI NIfTI files and behavioral CSV logs for a participant, **When** the preprocessing script is executed, **Then** the output includes motion-corrected, normalized, and smoothed fMRI data, and a behavioral matrix aligned to trial events.
2. **Given** a participant's preprocessed fMRI data, **When** the ROI extraction module runs, **Then** it outputs a time-series matrix for dlPFC, ventral striatum, and ACC with dimensions matching the number of timepoints.
3. **Given** a dataset where motion correction fails for >10% of volumes, **When** the quality control check runs, **Then** the participant is flagged for exclusion, and a log entry is generated.

---

### User Story 2 - Computational Modeling of Belief Updating (Priority: P2)

The system must implement a computational model (e.g., hierarchical Bayesian) to estimate individual-level belief updating rates based on the magnitude of social feedback discrepancy, generating parameters that quantify how much social information overrides private beliefs.

**Why this priority**: This transforms raw behavioral choices into interpretable cognitive parameters. It bridges the gap between observed behavior and the theoretical mechanism of "adaptive decision-making," allowing for correlation with neural data.

**Independent Test**: The model can be tested by feeding it synthetic data generated from a *different* generative process with noise characteristics distinct from the fitting model, verifying that the posterior estimates converge to the ground truth within a defined error margin.

**Acceptance Scenarios**:

1. **Given** a participant's sequence of choices and social feedback ratings, **When** the belief-updating model is fitted, **Then** it outputs a posterior distribution for the belief-updating rate (alpha) and the precision of social feedback.
2. **Given** a dataset where social feedback contradicts prior beliefs, **When** the model runs, **Then** the estimated updating rate is significantly higher than in trials where feedback aligns with beliefs.
3. **Given** the hierarchical structure, **When** the model runs, **Then** it produces both individual-level estimates and a group-level hyperparameter distribution without diverging.
4. **Given** held-out real behavioral data not used in training, **When** the model predicts choices, **Then** it achieves an accuracy ≥ 60% (See US-2, Constitution Principle VII).

---

### User Story 3 - Neural-Behavioral Correlation and Hypothesis Testing (Priority: P3)

The system must perform General Linear Model (GLM) analysis to identify neural signatures of feedback discrepancy and correlate these activation patterns with the computational updating parameters derived in Story 2.

**Why this priority**: This directly addresses the research question by linking the neural mechanism (BOLD signal) to the computational mechanism (updating rate). It validates the core hypothesis that specific brain regions encode the discrepancy between private and social information.

**Independent Test**: The analysis can be tested on simulated data where the correlation between a specific ROI and the updating parameter is known, verifying that the statistical test correctly identifies the significant association.

**Acceptance Scenarios**:

1. **Given** the ROI time-series and the individual updating parameters, **When** the correlation analysis is performed, **Then** the system computes and reports the correlation coefficient and p-value (See US-3).
2. **Given** the full voxel-wise data, **When** the permutation testing with FDR correction is applied, **Then** the resulting statistical map highlights clusters in the ventral striatum and ACC associated with social feedback magnitude.
3. **Given** a null hypothesis where no relationship exists, **When** the analysis is run, **Then** the false discovery rate remains controlled at the specified threshold (e.g., 5%).

---

### Edge Cases

- If a participant's motion exceeds the safety threshold (>3mm translation), then the system must exclude the participant from the final analysis and log the reason.
- If participants exhibit no behavioral adaptation (updating rate ≈ 0), then the model must converge without crashing, and these participants should be flagged for sensitivity analysis to ensure they do not skew group-level estimates.
- If the computational model fails to converge for a specific participant, then the system must log the failure, attempt a restart with different initializers (up to 3 times), and if it fails, exclude that participant's behavioral data from the correlation step.
- If the sensitivity analysis is required, then the system must execute the sweep and report stability metrics (See FR-006).

## Requirements

### Functional Requirements

- **FR-001**: System MUST preprocess fMRI data (motion correction, normalization, smoothing) and extract BOLD signals from dlPFC, ventral striatum, and ACC for all valid participants (See US-1).
- **FR-002**: System MUST implement a hierarchical Bayesian model to estimate individual belief-updating rates (alpha) based on the discrepancy between private beliefs and social feedback (See US-2).
- **FR-003**: System MUST perform General Linear Model (GLM) analysis to test for activation differences in ROIs between social feedback conditions, specifically modeling parametric modulation by feedback discrepancy (See US-3).
- **FR-004**: System MUST apply permutation testing with False Discovery Rate (FDR) correction for multiple comparisons across voxels and regions to control family-wise error (See US-3).
- **FR-005**: System MUST compute partial correlation between the extracted neural activation (discrepancy encoding) and the computational updating parameters, controlling for the input discrepancy signal (See US-3).
- **FR-006**: System MUST implement a sensitivity analysis sweeping the belief-updating threshold/cutoff over a set of values (e.g., {0.01, 0.05, 0.1}) to verify robustness of the headline correlation rates, and report the stability of the correlation coefficient (change < 0.05) across the sweep (See US-2).

### Key Entities

- **Participant**: A healthy adult subject with demographic data and scan metadata.
- **Trial**: A single decision event containing private belief, choice, social feedback, and timestamp.
- **ROI-Data**: Extracted time-series data for a specific brain region (dlPFC, ventral striatum, ACC).
- **Updating-Parameter**: The computational estimate (alpha) representing the weight given to social feedback.
- **Neural-Signature**: The statistical map or beta-value representing the encoding of feedback discrepancy.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The rate of participant exclusion due to motion artifacts is measured against the pre-defined threshold of 10% of volumes exceeding 3mm translation (See FR-001).
- **SC-002**: The convergence rate of the hierarchical Bayesian model is measured against the requirement that the model converges for ≥ 90% of N_valid, where N_valid is the count of participants passing motion QC (See FR-002).
- **SC-003**: The partial correlation coefficient (controlling for input discrepancy) between neural activation and updating parameters is measured against the target of r ≥ 0.3 (See FR-005).
- **SC-004**: The family-wise error rate in the voxel-wise analysis is measured against the FDR-corrected threshold of q < 0.05 (See FR-004).
- **SC-005**: The robustness of the belief-updating effect is measured by the stability of the correlation coefficient across the sensitivity sweep of the cutoff threshold (See FR-006).

## Assumptions

- The dataset (fMRI + behavioral) contains all necessary variables: private belief ratings, social feedback ratings, choice data, and the specific coordinates for the ROIs (dlPFC, ventral striatum, ACC).
- The study design is observational; therefore, all findings regarding the relationship between neural activity and behavior will be framed as **associational** rather than causal.
- The analysis will run on a CPU-only environment (GitHub Actions free tier) using `numpy`, `scipy`, `scikit-learn`, and `pymc` (or equivalent CPU-optimized Bayesian library); no GPU acceleration or 8-bit quantization will be used.
- The sample size of [deferred] participants is sufficient to achieve the target power for the primary correlation analysis, assuming an effect size of r ≥ 0.3.
- The computational model (hierarchical Bayesian) will be implemented using a CPU-tractable approximation (e.g., Variational Inference or MCMC with a limited number of samples) to ensure execution within the CI time limit.
- The social feedback provided in the task is treated as an exogenous variable; no endogenous modeling of the "peer" generating the feedback is included in this scope.