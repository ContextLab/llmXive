# Feature Specification: llmXive follow-up: extending "OmniOpt: Taxonomy, Geometry, and Benchmarking of Modern Optimizers"

**Feature Branch**: `001-spectral-optimizer-prediction`  
**Created**: 2026-07-31  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'OmniOpt: Taxonomy, Geometry, and Benchmarking of Modern Optimizers'"

## User Scenarios & Testing

### User Story 1 - Proxy Data Preparation and Gradient Spectral Extraction (Priority: P1)

A researcher needs to generate a dataset of spectral signatures from initial gradient covariance matrices for diverse small-scale models to establish the baseline data required for prediction.

**Why this priority**: This is the foundational data acquisition step. Without extracting the spectral features (condition number, tail decay, etc.) from the proxy models, no predictive model can be trained or evaluated. It directly enables the core hypothesis testing.

**Independent Test**: The system can be tested by running the extraction pipeline on a single architecture (e.g., ResNet) on a subset of TinyImageNet and verifying that a valid JSON/CSV file containing the spectral feature vector and the model identifier is produced within a reasonable time limit on a CPU-only runner.

**Acceptance Scenarios**:

1. **Given** a small-scale model (10M–50M params) initialized with random weights and a proxy dataset (TinyImageNet/C4), **When** the system runs 100 steps of baseline SGD training and computes the gradient covariance matrix, **Then** the system MUST output a feature vector containing the spectral radius, condition number, and tail decay exponent (calculated via power-law fitting via Maximum Likelihood Estimation (MLE) on the top-50 eigenvalues) with no NaN or infinite values.
2. **Given** a batch size of 32 and a dataset of 1000 samples, **When** the system attempts to compute the eigenvalue decomposition of the gradient covariance matrix, **Then** the computation MUST complete within 15 minutes on a 2-core CPU runner, ensuring the full pipeline fits within the 6-hour budget.
3. **Given** a model architecture that fails to converge during the 100-step proxy run, **When** the spectral extraction is attempted, **Then** the system MUST log the failure and exclude the sample from the dataset rather than crashing the entire job.

---

### User Story 2 - Ground Truth Labeling and Dataset Construction (Priority: P2)

A researcher needs to map the extracted spectral signatures to the "optimal mechanism family" ground truth labels derived from the OmniOpt benchmark results to create a supervised learning dataset.

**Why this priority**: This step bridges the gap between the extracted features (input) and the research question's target (optimal optimizer family). It creates the labeled dataset necessary for training the predictor.

**Independent Test**: The system can be tested by loading the OmniOpt benchmark results (or the pre-computed lookup table) and merging them with the spectral feature dataset. The test passes if every spectral feature vector is successfully paired with a categorical label (e.g., "Adam", "SGD", "Lion") and the resulting dataset is validated for missing labels.

**Acceptance Scenarios**:

1. **Given** a spectral feature vector for a specific architecture (e.g., ResNet-18) and task (e.g., TinyImageNet), **When** the system queries the OmniOpt benchmark lookup table, **Then** the system MUST retrieve the corresponding "best-performing mechanism family" (defined by final validation loss after 100k steps of full training) and append it as a target label to the feature vector.
2. **Given** an architecture/task combination not present in the OmniOpt benchmark tables, **When** the system attempts to label the data, **Then** the system MUST flag the sample as "unlabeled" and exclude it from the training set, recording the exclusion in a log file.
3. **Given** the merged dataset of spectral features and labels, **When** the system performs a sanity check, **Then** the distribution of labels MUST have a Shannon entropy > 1.5 bits and a minimum class count of 3 samples per optimizer family to ensure the regression task is non-trivial.

---

### User Story 3 - Predictive Model Training and Validation (Priority: P3)

A researcher needs to train a lightweight classification model (Logistic Regression, Random Forest, or MLP) to predict the optimal optimizer family from spectral features and validate its performance using cross-validation.

**Why this priority**: This is the core analytical step that tests the hypothesis. It determines if the spectral signature is a valid predictor, directly answering the research question.

**Independent Test**: The system can be tested by training the predictor on [deferred] of the labeled dataset and evaluating it on the remaining [deferred] (or via k-fold cross-validation). The test passes if the model produces a prediction accuracy or F1 score and a confusion matrix (for categorical targets) without exceeding memory limits.

**Acceptance Scenarios**:

1. **Given** the labeled dataset of spectral features and optimal mechanism families, **When** the system trains a Logistic Regression, Random Forest, or small MLP using 5-fold cross-validation, **Then** the system MUST output a mean prediction accuracy and macro-averaged F1 score with a standard deviation across folds.
2. **Given** a hold-out set of architectures not seen during training, **When** the trained model predicts the optimal mechanism family, **Then** the system MUST report the generalization accuracy on this independent set.
3. **Given** the trained model, **When** a permutation test is performed to assess significance (using 10,000 permutations and shuffling labels to construct the null distribution), **Then** the system MUST report a p-value indicating whether the correlation between spectral features and mechanism performance is statistically significant (p < 0.05).

---

### Edge Cases

- What happens if the gradient covariance matrix is singular or nearly singular, making the condition number infinite? (System must handle numerical stability, e.g., via regularization).
- How does the system handle architectures where the OmniOpt benchmark does not report a clear "best" optimizer (e.g., ties)? (System must define a tie-breaking rule or exclude ambiguous cases).
- What if the proxy dataset (TinyImageNet) is too large to fit in available RAM when preprocessed? (System must implement on-the-fly loading or aggressive sampling).

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute the gradient covariance matrix from the first 100 steps of training on a proxy dataset for at least 20 diverse small-scale models (10M–50M params), using the same random seed and weight initialization protocol as the OmniOpt benchmark. (See US-1)
- **FR-002**: System MUST extract spectral features (spectral radius, condition number, tail decay exponent calculated via power-law fitting via Maximum Likelihood Estimation (MLE) on the leading eigenvalues) from the gradient covariance matrix with numerical stability (handling singular matrices). (See US-1)
- **FR-003**: System MUST map each spectral feature vector to a ground truth "optimal mechanism family" label using the OmniOpt benchmark results, where the label is defined by the optimizer achieving the lowest final validation loss after 100k steps of full training (independent of initial spectral features). (See US-2)
- **FR-004**: System MUST train a lightweight classification model (e.g., Logistic Regression, Random Forest, or MLP with softmax) to map spectral features to the optimal mechanism family using k-fold cross-validation. (See US-3)
- **FR-005**: System MUST perform a permutation test to assess the statistical significance of the correlation between spectral features and mechanism performance, using a sufficient number of permutations and shuffling labels to construct the null distribution. (See US-3)
- **FR-006**: System MUST enforce a hard runtime limit for the entire pipeline, failing gracefully if exceeded. (See US-1)

### Key Entities

- **SpectralFeatureVector**: A structured record containing the spectral radius, condition number, tail decay exponent, and model identifier.
- **OptimalMechanismLabel**: A categorical label representing the best-performing optimizer family (e.g., "Adam", "SGD", "Lion") for a specific architecture/task, determined by final validation loss after 100k steps.
- **PredictorModel**: The trained machine learning model (Logistic Regression, Random Forest, or MLP) that maps spectral features to mechanism labels.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Prediction accuracy (or macro-averaged F1 score) of the predictor model on the hold-out set is measured against the random guessing baseline (e.g., 1/K for K classes) with a required threshold of baseline + 5% to determine if the spectral signature provides meaningful signal. (See FR-004)
- **SC-002**: The p-value from the permutation test is measured against a conventional significance threshold to determine if the correlation is statistically significant. (See FR-005)
- **SC-003**: The total runtime of the full pipeline (data extraction + labeling + training) is measured against a predefined feasibility limit to ensure CPU feasibility. (See FR-006)
- **SC-004**: The memory usage peak during gradient covariance computation is measured against the available RAM limit to ensure the method fits the runner constraints. (See FR-006)
- **SC-005**: The number of successfully labeled samples is measured against the minimum of 20 diverse architectures, where 'diverse' is defined as covering at least 5 distinct optimizer families with no single family comprising > 50% of the sample set, to ensure dataset diversity. (See FR-003)

## Assumptions

- The OmniOpt benchmark results (or a subset thereof) are available as a static lookup table or can be re-run within a practical time limit for the specific architectures used in this study.
- The TinyImageNet and C corpus datasets are accessible via standard public repositories and can be downloaded or streamed within the 6-hour window.
- The "tail decay exponent" can be reliably estimated via power-law fitting on the eigenvalue spectrum of the gradient covariance matrix, even with a limited number of eigenvalues computed.
- The relationship between the initial gradient spectrum and optimal mechanism family is static and does not require dynamic training signals beyond the initial 100 steps.
- The 2-core CPU runner is sufficient for computing eigenvalue decompositions of matrices derived from models with up to 50M parameters on a sampled subset of the data.
- The "optimal mechanism family" is a deterministic outcome of the OmniOpt benchmark for each architecture/task, allowing for unambiguous labeling.