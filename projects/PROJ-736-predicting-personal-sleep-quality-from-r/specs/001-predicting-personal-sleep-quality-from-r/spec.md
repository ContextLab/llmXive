# Feature Specification: Predicting Personal Sleep Quality from Resting‑State fMRI Connectivity

**Feature Branch**: `[001-predict-sleep-quality]`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Predicting Personal Sleep Quality from Resting‑State fMRI Connectivity"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – End‑to‑end Data Pipeline (Priority: P1)

A researcher wants to obtain preprocessed whole‑brain functional connectivity vectors for every HCP participant who completed the Sleep questionnaire.

**Why this priority**: Without reliable input data the rest of the workflow cannot be executed; this is the foundational slice of value.

**Independent Test**: Run the data‑pipeline script on the HCP 1200‑subject release (restricted to subjects with Sleep questionnaire data) and verify that the expected `.npy` files are produced.

**Acceptance Scenarios**:

1. **Given** the raw minimally preprocessed HCP rs‑fMRI files and a list of subject IDs with valid Sleep questionnaire responses, **When** the pipeline is executed, **Then** it outputs (a) nuisance‑regressed, band‑pass‑filtered time series for the Schaefer cortical atlas + subcortical ROIs, and (b) Fisher‑z‑transformed upper‑triangular connectivity vectors for each subject.  
2. **Given** a subject whose rs‑fMRI contains > 0.3 mm framewise displacement, **When** the pipeline runs, **Then** that subject is excluded and logged, while all other eligible subjects are processed.

### User Story 2 – Predictive Modeling & Statistical Validation (Priority: P2)

A researcher wants to train an elastic‑net regression model on the connectivity features, evaluate its out‑of‑sample predictive performance for Sleep Score, and assess statistical significance.

**Why this priority**: The core scientific claim rests on whether rs‑fMRI can predict sleep quality; this story delivers that evidence.

**Independent Test**: Execute the modeling script on the feature matrix produced by US‑1 and confirm that the script returns performance metrics, permutation‑test p‑value, and bootstrap confidence intervals.

**Acceptance Scenarios**:

1. **Given** the feature matrix (≤ 5 k dimensions) and corresponding Sleep Scores, **When** nested 5‑fold outer/inner cross‑validation with elastic‑net hyper‑parameter tuning is run, **Then** the script outputs (a) Pearson r, (b) out‑of‑sample R², (c) an empirical p‑value from 1 000 label‑permutations, and (d) a Bootstrap confidence interval for R².  
2. **Given** the same data, **When** the variance‑threshold is varied across {0.005, 0.01, 0.02} and the PCA variance‑retention across {0.95, 0.90, 0.85}, **Then** the resulting R² values are recorded for a sensitivity analysis.

### User Story 3 – Interpretation & Visualization (Priority: P3)

A researcher wants to identify which brain connections drive the prediction and visualise them on a cortical surface.

**Why this priority**: Interpretability is essential for neuroscientific insight and for communicating results to the community.

**Independent Test**: Run the feature‑importance script on the trained model from US‑2 and verify that a brain‑surface plot is generated without errors.

**Acceptance Scenarios**:

1. **Given** the fitted elastic‑net model with non‑zero coefficients, **When** the importance‑extraction script is executed, **Then** it maps each non‑zero coefficient back to its corresponding edge and graph‑theoretic metric, and produces a brain‑surface image highlighting the top N most predictive connections (where N is a configurable parameter).
2. **Given** a failed mapping (e.g., coefficient refers to a dropped edge), **When** the script runs, **Then** it logs a warning and continues, producing a plot for the remaining valid edges.

### Edge Cases

- What happens when a subject’s Sleep Score is missing or marked as “N/A”?  
- How does the system handle a scenario where variance‑thresholding removes **all** edges (e.g., because variance < 0.01 across subjects)?  
- How does the workflow behave if total runtime exceeds the maximum allowed duration for GitHub‑Actions. (e.g., due to an unusually large subset of subjects)? 

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest raw minimally preprocessed HCP rs‑fMRI files and output nuisance‑regressed, band‑pass‑filtered (low‑frequency to 0.1 Hz) time series for the Schaefer‑200 cortical atlas plus subcortical ROIs. *(See US‑1)*
- **FR-002**: System MUST compute pairwise Pearson correlation matrices for each subject, apply Fisher‑z transformation, and store the upper‑triangular elements as a flat feature vector. *(See US‑1)*
- **FR-003**: System MUST perform variance‑thresholding, retaining only edges whose across‑subject variance exceeds a configurable threshold parameter (default 0.01) (justified by the need to reduce dimensionality in high-dimensional neuroimaging data prior to regularization) and subsequently apply PCA retaining a configurable percentage of variance (implementation-time selection), guaranteeing a final feature dimensionality **< 5 000**. *(See US‑1)*
- **FR-004**: System MUST implement a nested k‑fold outer / k‑fold inner cross‑validation loop that tunes elastic‑net mixing (α) and regularisation (λ) using scikit‑learn’s `ElasticNetCV`. *(See US‑2)*
- **FR-005**: System MUST compute out‑of‑sample Pearson r and coefficient of determination (R²) for each outer fold and aggregate them across folds. *(See US‑2)*
- **FR-006**: System MUST generate an empirical null distribution for Pearson r by performing **1 000** label‑permutations (shuffling Sleep Scores) and compute a family‑wise‑error‑corrected p‑value, including the entire nested CV pipeline (inner-loop tuning and variance-thresholding) re-run for each permutation. *(See US-2; addresses multiplicity)*
- **FR-007**: System MUST conduct **1 000** bootstrap resamples of the outer‑fold predictions to obtain a 95 % confidence interval for the aggregated R². *(See US‑2)*
- **FR-008**: System MUST extract all non‑zero elastic‑net coefficients, map them back to their corresponding brain edges and graph‑theoretic metrics, and produce a brain‑surface visualization (e.g., using Nilearn’s `plot_connectome`). *(See US‑3)*
- **FR-009**: System MUST enforce CPU‑only execution, limit peak RAM consumption to **≤ 6 GB**, and abort with a clear error if total wall‑clock time exceeds **5 hours** on an ubuntu-latest runner on GitHub Actions (justified by GitHub Actions free-tier limits). *(See US-1, US-2)*
- **FR-010**: System MUST log each processing stage (data ingestion, preprocessing, feature engineering, modeling, validation, visualization) to a structured JSON file to guarantee reproducibility. *(See US-1, US-2, US-3)*

### Key Entities

- **Subject**: Represents a single HCP participant; key attributes – `subject_id`, `sleep_score`, `connectivity_vector`.  
- **FeatureMatrix**: The matrix of all subjects’ retained connectivity features after variance‑thresholding and PCA.  
- **Model**: Elastic‑net regression object with trained coefficients and hyper‑parameters.  
- **ResultReport**: JSON document containing performance metrics, permutation p‑value, bootstrap CI, and paths to visualisation files.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ≥ 80 % of subjects with a valid Sleep Score are successfully processed through the pipeline, producing a connectivity vector. *(See US‑1)*
- **SC-002**: The aggregated out‑of‑sample Pearson r is correctly computed and reported, and the permutation‑test p‑value is statistically significant (p < 0.05, family‑wise‑error corrected) if the null hypothesis is rejected, indicating a statistically significant associational relationship. *(See US‑2)*
- **SC-003**: Sensitivity analysis across variance‑threshold values {0.005, 0.01, 0.02} and PCA variance‑retention levels {0.95, 0.90, 0.85} is performed and reports the R² values for each threshold combination to enable robustness assessment. *(See US‑2)*
- **SC-004**: The visualization step produces a brain‑surface plot file (`.png` or `.svg`) without errors for **≥ 95 %** of runs, and the plot includes at least the top 50 most predictive connections (or all if fewer than 50). *(See US‑3)*
- **SC-005**: The entire end‑to‑end workflow completes within **5 hours** and uses **≤ 6 GB** RAM on an ubuntu-latest runner on GitHub Actions (justified by GitHub Actions free-tier limits). *(See US-1, US-2)*
- **SC-006**: All logs and the final `ResultReport.json` are reproducibly generated and can be re‑run to obtain identical numerical results (modulo stochastic seeds). *(FR‑010)*

## Assumptions

- The Human Connectome Project 1200‑subject release **contains** Sleep questionnaire items (specifically within the `hcp_1200/behavioral` directory, file `sleep.csv`), which are used to derive a composite Sleep Score for the selected subset of participants. The HCP Subjects Release does not contain the Pittsburgh Sleep Quality Index (PSQI); the Sleep Score is derived from available sleep duration and quality items as a proxy. See HCP Data Dictionary and Behavioral Data Release Notes.
- The variance‑threshold of **0.01** is a community‑standard heuristic for discarding near‑constant functional connections; the chosen PCA retention is configurable and balances dimensionality reduction with information preservation.
- A permutation count of **1 000** provides adequate power for estimating an empirical null distribution while staying within the CPU‑only compute budget.  
- The sample size (≈ 200–300 subjects with Sleep Score) is assumed to yield enough statistical power to detect an R² of at least 0.05; a formal power analysis will be performed later (deferred).  
- All software dependencies (Python 3.11, `nibabel`, `nilearn`, `scikit‑learn`, `networkx`, `pandas`, `numpy`) run efficiently on a single‑CPU runner without GPU acceleration.  
- Docker containerisation will be used to guarantee environment reproducibility; the container image size will stay < 2 GB to satisfy GitHub Actions storage limits.  