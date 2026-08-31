# Feature Specification: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

**Feature Branch**: `001-predict-residual-stress-fatigue`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "To what extent does residual stress mediate the relationship between manufacturing process parameters and fatigue life across different material classes, and how much predictive value does stress‑mediated estimation add beyond direct process‑to‑fatigue modeling?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The researcher downloads public fatigue datasets (NIST, UCI, OpenML), parses CSV/JSON files, standardizes units, and handles missing values via median imputation to create a unified analysis-ready dataset containing process parameters, residual stress (measured or estimated), and fatigue life outcomes.

**Why this priority**: This is the foundational step; without a clean, unified dataset, no modeling or mediation analysis can occur. It delivers immediate value by transforming raw, heterogeneous public data into a structured format ready for investigation.

**Independent Test**: The pipeline can be fully tested by running the ingestion script against a small, synthetic test set containing known missing values and unit inconsistencies, verifying that the output CSV contains imputed values and standardized units.

**Acceptance Scenarios**:

1. **Given** a raw CSV with mixed units (MPa and psi) and missing residual stress values, **When** the ingestion script runs, **Then** the output CSV contains all stress values in MPa and missing entries filled with the column median.
2. **Given** a JSON dataset from OpenML with nested feature structures, **When** the parser processes it, **Then** the output is a flat CSV with columns for material composition, process parameters, and fatigue life cycles.
3. **Given** a dataset where residual stress is missing for [deferred] of rows, **When** the script calculates the estimated proxy using the formula `σ_res ≈ k·heat_input·cooling_rate`, **Then** the proxy values are appended to the dataset with a flag indicating they are derived.

---

### User Story 2 - Baseline and Stress-Mediated Model Training (Priority: P2)

The researcher trains baseline regression models (Process Parameters Only) and stress-mediated models (Process + Residual Stress) using Random Forest, Gradient Boosting, and a shallow neural network on a CPU-only environment, performing 5-fold cross-validation to select hyperparameters.

**Why this priority**: This implements the core comparative analysis to answer the research question regarding predictive value. It delivers the primary scientific result: the comparison of model performance with and without stress features.

**Independent Test**: The training script can be tested independently by running it on a fixed subset of data with a fixed random seed, verifying that the model with stress features produces a lower Mean Absolute Percentage Error (MAPE) on the validation fold than the baseline model.

**Acceptance Scenarios**:

1. **Given** the prepared dataset split into [deferred] training and [deferred] testing, **When** the Random Forest model is trained on feature set A (process only) and feature set B (process + stress), **Then** the cross-validation log reports the MAPE and R² for both models.
2. **Given** a dataset containing only CPU-compatible features, **When** the shallow neural network (1 hidden layer, ≤500 epochs) is trained with early stopping, **Then** the training completes within 60 minutes on a standard 2-core runner without GPU errors.
3. **Given** a hyperparameter grid of 10 combinations, **When** the grid search executes, **Then** the system selects the combination with the lowest validation error and saves the model weights.

---

### User Story 3 - Mediation Analysis and Statistical Reporting (Priority: P3)

The researcher performs bootstrap mediation analysis (10,000 resamples) to quantify the indirect effect of process parameters on fatigue life via residual stress, calculates the proportion mediated, and generates a report comparing model performance across material classes (steels vs. aluminum).

**Why this priority**: This addresses the specific "mediation" aspect of the research question, providing the statistical evidence for the mechanistic link. It is the final analytical step that synthesizes the modeling results into scientific conclusions.

**Independent Test**: The analysis script can be tested by running it on a toy dataset where the mediation effect is known, verifying that the bootstrap confidence intervals correctly capture the true indirect effect and that the proportion mediated matches the theoretical expectation.

**Acceptance Scenarios**:

1. **Given** the trained models and the full dataset, **When** the bootstrap mediation analysis runs with 10,000 resamples, **Then** the output includes the indirect effect estimate, 95% confidence intervals, and the proportion of variance mediated.
2. **Given** separate subsets for steels and aluminum alloys, **When** the cross-material evaluation runs, **Then** the report quantifies the performance drop (MAPE increase) when training on one material and testing on the other.
3. **Given** the paired absolute errors from Model A and Model B on the test set, **When** a paired t-test is performed, **Then** the output reports the p-value and determines if the improvement is statistically significant (p < 0.05).

---

### Edge Cases

- What happens when a public dataset lacks residual stress measurements entirely? The system must rely solely on the estimated proxy and flag the analysis as "proxy-dependent" in the final report.
- How does the system handle datasets with fewer than 50 samples? The system must raise a warning that statistical power is insufficient for reliable mediation analysis and may skip the bootstrap step.
- What if the estimated residual stress proxy results in negative values (physically impossible)? The system must clamp negative proxy values to a small positive epsilon (e.g., 0.01 MPa) and log the adjustment.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST ingest data from NIST, UCI, and OpenML repositories, parsing CSV and JSON formats into a unified schema with columns for material type, process parameters, residual stress, and fatigue life cycles (See US-1).
- **FR-002**: The system MUST impute missing numeric values using the median of the respective column and standardize all stress units to MPa (See US-1).
- **FR-003**: The system MUST calculate an estimated residual stress proxy using the formula `σ_res ≈ k·heat_input·cooling_rate` when measured values are absent, and flag these entries as derived (See US-1).
- **FR-004**: The system MUST train baseline (process-only) and stress-mediated (process + stress) regression models using Random Forest, Gradient Boosting, and a shallow neural network with a maximum of 500 epochs (See US-2).
- **FR-005**: The system MUST perform 5-fold cross-validation for model selection and reserve [deferred] of the data as a held-out test set (See US-2).
- **FR-006**: The system MUST execute bootstrap mediation analysis with 10,000 resamples to estimate the indirect effect of process parameters on fatigue life via residual stress (See US-3).
- **FR-007**: The system MUST report the proportion of variance mediated and 95% confidence intervals for the indirect effect (See US-3).
- **FR-008**: The system MUST compare model performance (MAPE, R²) between feature set A and feature set B using paired t-tests on absolute errors (See US-3).
- **FR-009**: The system MUST stratify analysis by material class (e.g., steels, aluminum) to evaluate cross-material generalization (See US-3).
- **FR-010**: The system MUST fix random seeds for data splits, model initialization, and bootstrap resampling to ensure reproducibility (See US-2, US-3).

### Key Entities

- **DatasetRecord**: A single observation containing material composition, manufacturing process parameters, residual stress (measured or estimated), and fatigue life cycles.
- **ModelRun**: An instance of a trained regression model with associated hyperparameters, training metrics (MAPE, R²), and feature set configuration.
- **MediationResult**: A statistical object containing the direct effect, indirect effect, proportion mediated, and confidence intervals derived from bootstrap resampling.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of variance in fatigue life mediated by residual stress is measured against the total variance explained by the full model (See US-3).
- **SC-002**: The Mean Absolute Percentage Error (MAPE) of the stress-mediated model is measured against the MAPE of the baseline (process-only) model to determine the predictive value added (See US-2).
- **SC-003**: The statistical significance of the mediation effect is measured against the 95% confidence interval generated by the bootstrap analysis (See US-3).
- **SC-004**: The performance drop in cross-material evaluation is measured against the within-material performance baseline to assess generalization capability (See US-3).
- **SC-005**: The computational feasibility is measured against the GitHub Actions free-tier limits (≤6 hours runtime, ≤7 GB RAM) for the entire training and analysis pipeline (See US-2).

## Assumptions

- Public datasets (NIST, UCI, OpenML) contain sufficient samples (≥50) with at least one of: measured residual stress or the necessary process parameters to compute the proxy.
- The empirical correlation `σ_res ≈ k·heat_input·cooling_rate` is a valid approximation for the specific manufacturing processes represented in the datasets.
- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM) is sufficient to train shallow neural networks and perform 10,000 bootstrap resamples on the available dataset size.
- The datasets are primarily observational; therefore, all findings regarding the "mediation" effect are framed as associational, not causal, unless the dataset explicitly includes randomization.
- The variable "residual stress" in the datasets is either directly measured or can be reasonably estimated; if a dataset lacks both, it will be excluded from the stress-mediated analysis.
- The material classes (e.g., steels, aluminum) are clearly labeled in the metadata, allowing for valid stratification.
