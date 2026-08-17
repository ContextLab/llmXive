# Feature Specification: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

**Feature Branch**: `001-llmxive-entanglement-analysis`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Beyond Scalar Rewards by Internalizing Reasoning into Score Distributions'"

## User Scenarios & Testing

### User Story 1 - Dataset Ingestion and Ground-Truth Alignment (Priority: P1)

As a researcher, I need to ingest the Z-Reward evaluation dataset (prompts, generated images, human annotations) and the pre-computed inference outputs (logits and score distributions) for the teacher and student models, so that I can establish a reliable ground truth for dimensional fidelity loss without manual data collection.

**Why this priority**: Without verified access to the specific teacher outputs and independent human annotations, the core hypothesis regarding "information loss" cannot be tested. This is the foundational data layer for all subsequent analysis.

**Independent Test**: A script can be run to load the dataset, verify the presence of all four rubric dimensions (Alignment, Realism, Aesthetics, Plausibility) in both teacher outputs and human annotations, and output a summary of sample counts and missing data flags.

**Acceptance Scenarios**:
1. **Given** the Z-Reward dataset files are available in the repository, **When** the ingestion script executes, **Then** it successfully loads the teacher score distributions and human annotations into memory with a matching sample count.
2. **Given** a sample where human annotations are missing for a specific dimension, **When** the ingestion script processes it, **Then** it flags the sample as "excluded from fidelity calculation" and logs the specific missing dimension.
3. **Given** the dataset contains student scalar outputs, **When** the ingestion script runs, **Then** it aligns the student's scalar output with the teacher's distribution and human annotations for the same sample, ensuring the 'primary quality dimension' is identified solely by a fixed schema rule (static mapping from prompt metadata), independent of model scores.

---

### User Story 2 - Entanglement Quantification and Feature Engineering (Priority: P2)

As a researcher, I need to calculate the statistical "entanglement score" (variance across dimensions, entropy, skewness, kurtosis) for each sample based on the teacher's multi-dimensional score distribution, AND compute the covariance matrix and dominant eigenvalue across the entire batch of samples, so that I can quantify the structural complexity of the teacher's output.

**Why this priority**: This step transforms raw model outputs into the independent variables required for the predictive model. It operationalizes the "structural entanglement" concept from the research question, distinguishing between per-sample variability and batch-level correlation structure.

**Independent Test**: A script can be run on a fixed subset of samples to compute the variance, entropy, skewness, kurtosis for each sample, and the covariance matrix/eigenvalue for the batch, verifying that the mathematical operations produce finite, non-NaN values.

**Acceptance Scenarios**:
1. **Given** a batch of teacher score distributions for the four rubric dimensions, **When** the feature engineering module runs, **Then** it outputs a JSON record containing the calculated variance, entropy, skewness, kurtosis for each sample, AND the covariance matrix and dominant eigenvalue for the entire batch.
2. **Given** a distribution where all scores are identical (zero variance), **When** the module runs, **Then** it handles the zero-variance case gracefully (e.g., by setting entropy to 0 and variance to 0) without crashing.

---

### User Story 3 - Predictive Modeling and Validation (Priority: P3)

As a researcher, I need to train a CPU-based Random Forest regressor to predict the "dimensional fidelity loss" (MAE against human annotations) using the teacher's statistical features, AND perform a simple correlation test (Pearson/Spearman) between the entanglement score and fidelity loss, so that I can determine if structural entanglement correlates with information loss.

**Why this priority**: This is the core experimental validation. It tests the hypothesis that high variance predicts high error. It delivers the final research result (R² score, correlation coefficient, and error metrics).

**Independent Test**: A script can be run to train the model on a stratified random split ([deferred] train, [deferred] validation) of the data and evaluate it using 5-fold cross-validation, outputting the R² score and Mean Absolute Error. The test passes if the model trains successfully on a CPU-only environment and produces a non-NaN R² score.

**Acceptance Scenarios**:
1. **Given** the engineered features and the target fidelity loss values, **When** the training script executes with 5-fold cross-validation, **Then** it outputs the mean R² score and standard deviation across the folds.
2. **Given** the model is trained, **When** the validation step completes, **Then** the system outputs the correlation coefficient (R²), p-value (via permutation test), AND the result of a simple Pearson/Spearman correlation test between the entanglement features and fidelity loss.

---

### Edge Cases

- **What happens when** the teacher's output distribution has zero variance (constant scores) across all dimensions? (Handled by setting variance/entropy to zero).
- **How does the system handle** samples where the human annotation is missing for the specific "primary quality attribute" dimension required for the fidelity calculation? (Excluded from the target variable calculation; logged).
- **What happens when** the dataset size exceeds the available RAM (7 GB) on the free-tier runner? (The ingestion script must implement chunked loading or sampling to ensure the Random Forest fits in memory).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST ingest the Z-Reward evaluation dataset and pre-computed inference outputs (logits/scores) for both the teacher and student models of varying scales, ensuring alignment between teacher outputs, student scalar outputs, and human annotations for the same sample. (See US-1)
- **FR-002**: The system MUST calculate the variance across multiple dimensions, entropy, skewness, and kurtosis for the teacher's score distribution for EACH sample. Additionally, the system MUST compute the covariance matrix across the 4 dimensions for the ENTIRE dataset (or defined batch window) and derive the dominant eigenvalue from this matrix. (See US-2)
- **FR-003**: The system MUST compute the "dimensional fidelity loss" as the Mean Absolute Error (MAE) between the student model's scalar output and the independent human-annotated score for the primary quality dimension. The primary quality dimension MUST be determined solely by prompt metadata or a fixed schema rule, independent of model scores. (See US-1, US-3)
- **FR-004**: The system MUST train a Random Forest regressor using the statistical features as predictors and the fidelity loss as the target, employing k-fold cross-validation. (See US-3)
- **FR-005**: The system MUST report the R² score, Mean Absolute Error, and p-value (via permutation test) of the predictive model to quantify the relationship between teacher variance and student information loss. (See US-3)
- **FR-006**: The system MUST explicitly exclude samples with missing human annotations for the target dimension from the training set to avoid circular validation or imputation bias. (See US-1)
- **FR-007**: The system MUST output and store the computed covariance matrix and dominant eigenvalue as a core deliverable for reproducibility and verification of the 'structural entanglement' claim. (See US-2, Constitution Principle VI)

### Key Entities

- **Sample**: A single data point consisting of a prompt, generated image, teacher score distribution, student score, and human annotations.
- **Entanglement Features**: A vector of statistical descriptors (variance, entropy, eigenvalues) derived from the teacher's output.
- **Fidelity Loss**: A scalar value representing the error magnitude between the student's output and human ground truth.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation strength (R²) between teacher entanglement features and student fidelity loss is measured and reported. The system MUST output the R² score and the p-value (via permutation test). The correlation must be explicitly tested for a *positive* direction (higher variance -> higher loss) to confirm the hypothesis. (See FR-005)
- **SC-002**: The predictive accuracy (MAE) of the Random Forest model is measured and reported against a null baseline (predicting the mean loss). The system MUST output the p-value of the paired t-test comparing the model's MAE against the null baseline. (See FR-005)
- **SC-003**: The computational feasibility is measured against the constraint of running the full analysis (ingestion, feature engineering, training) within 6 hours on the specified CI runner. (See FR-004)
- **SC-004**: The independence of the target variable is verified by the system outputting a trace log or data lineage report showing the source of the target variable for each sample (prompt metadata/fixed schema), confirming it does not rely on model scores. (See FR-003)
- **SC-005**: The validity of the dataset-variable fit is confirmed by the ingestion script outputting a count of samples where all four dimensions have non-null, finite numeric values, and this count must be > 0. (See FR-001)

## Assumptions

- The Z-Reward evaluation dataset and the specific inference outputs (logits/scores) for the large-scale teacher and smaller student models are available in the public repository or a specified archive accessible by the GitHub Actions runner.
- The human annotations provided in the dataset are independent of the teacher model's internal reasoning chains, satisfying the requirement for non-circular validation.
- The dataset size (number of samples) is sufficiently small (or can be sampled) to fit within the RAM limit of the free-tier GitHub Actions runner when loaded into a Pandas DataFrame.
- The Random Forest implementation (via `scikit-learn`) is computationally efficient enough to train on the available CPU cores within the CI runner's resource budget.
- The four rubric dimensions (Alignment, Realism, Aesthetics, Plausibility) are consistently defined and labeled across both the teacher outputs and human annotations.
- The "primary quality attribute" for each sample can be deterministically identified from the dataset metadata to correctly calculate the fidelity loss, independent of model scores.