# Feature Specification: llmXive follow-up: extending "In-Context World Modeling for Robotic Control"

**Feature Branch**: `001-auto-icwm-latent-dynamics`  
**Created**: 2026-07-30  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'In-Context World Modeling for Robotic Control'"

## User Scenarios & Testing

### User Story 1 - Automated Latent Statistic Extraction (Priority: P1)

The researcher needs to process raw interaction clips (state-action-observation tuples) from the ICWM dataset to generate a structured table of statistical descriptors (variance, autocorrelation, spectral density) for each clip. This is the foundational step; without these features, no mapping to hyperparameters can be learned.

**Why this priority**: This is the data ingestion and feature engineering layer. If the system cannot reliably extract the statistical properties of the latent trajectories, the entire hypothesis regarding "latent complexity" cannot be tested. It is the prerequisite for all downstream modeling.

**Independent Test**: Can be fully tested by running the extraction pipeline on a small, fixed subset of 50 interaction clips and verifying that the output CSV contains the required columns (clip_id, variance, autocorr_lag1, spectral_density) with non-null, finite numerical values.

**Acceptance Scenarios**:

1. **Given** a directory of valid interaction clip files from the ICWM simulation dataset, **When** the extraction script is executed, **Then** a structured dataset is generated containing statistical descriptors for every clip.
2. **Given** a clip with high-variance latent trajectories, **When** the statistics are computed, **Then** the variance metric is significantly higher than that of a low-variance clip from a stable configuration.

---

### User Story 2 - Hyperparameter Mapping Model Training (Priority: P2)

The researcher needs to train a lightweight regressor (MLP or linear) that maps the extracted statistical descriptors to the optimal inference hyperparameters (sampling temperature $\tau$, context window $k$) determined via grid search.

**Why this priority**: This implements the core hypothesis: that latent statistics predict optimal inference strategy. It transforms the descriptive statistics from Story 1 into a predictive capability. Without this, the system cannot "auto-calibrate."

**Independent Test**: Can be fully tested by training the model on [deferred] of the data and evaluating the Mean Squared Error (MSE) on the held-out [deferred] test set, ensuring the error is lower than a naive baseline (e.g., predicting the global mean temperature for all inputs).

**Acceptance Scenarios**:

1. **Given** a trained regressor model and a set of novel configuration descriptors, **When** the model predicts hyperparameters, **Then** the predicted values are within the valid operational range (e.g., $0.1 \le \tau \le 2.0$, $1 \le k \le 64$).
2. **Given** a configuration with high latent instability, **When** the model predicts, **Then** the output suggests a higher sampling temperature or longer context window compared to a stable configuration.

---

### User Story 3 - Zero-Shot Calibration Validation (Priority: P3)

The researcher needs to execute the full "Auto-ICWM" pipeline on novel robotic configurations to verify that the model-predicted hyperparameters yield a higher success rate than fixed-parameter baselines.

**Why this priority**: This is the final validation of the research question. It demonstrates the practical utility of the method in the target environment (novel configurations) and quantifies the improvement over static approaches.

**Independent Test**: Can be fully tested by running the validation protocol on the test set, comparing the success rate of "Auto-ICWM" against a fixed $\tau=1.0, k=32$ baseline, and performing a statistical significance test (paired t-test or Wilcoxon).

**Acceptance Scenarios**:

1. **Given** a novel robotic configuration not seen during training, **When** the Auto-ICWM pipeline predicts and applies hyperparameters, **Then** the task success rate is recorded and compared against the fixed-baseline success rate.
2. **Given** the results of the validation runs, **When** the statistical analysis is performed, **Then** the p-value is calculated to determine if the improvement is statistically significant ($p < 0.05$).

### Edge Cases

- What happens when a latent trajectory has near-zero variance (indicating a static state)? The system must handle this without division-by-zero errors in spectral density calculations and still produce a valid (low-complexity) hyperparameter prediction.
- How does the system handle clips where the pre-trained ICWM encoder fails to generate embeddings (e.g., out-of-distribution input)? The pipeline must log the failure and exclude the clip from the training set rather than crashing.
- What if the grid search for optimal hyperparameters yields multiple equally optimal solutions (ties)? The system must consistently select one (e.g., the lowest temperature) to ensure deterministic labeling for the regressor.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST extract statistical descriptors (variance, autocorrelation, spectral density) from latent token sequences generated by the pre-trained ICWM encoder for every input interaction clip. (See US-1)
- **FR-002**: The system MUST perform an independent grid search over sampling temperature ($\tau$) and context window length ($k$) for each configuration to establish ground-truth optimal hyperparameters. (See US-2)
- **FR-003**: The system MUST train a lightweight, CPU-tractable regressor (e.g., MLP or linear regression) using the statistical descriptors as inputs and the grid-searched hyperparameters as targets. (See US-2)
- **FR-004**: The system MUST execute the validation protocol on novel configurations, applying the predicted hyperparameters to the VLA policy and recording the task success rate. (See US-3)
- **FR-005**: The system MUST perform a statistical significance test (paired t-test or Wilcoxon signed-rank) comparing the Auto-ICWM success rates against a fixed-parameter baseline. (See US-3)
- **FR-006**: The system MUST enforce a computational budget of ≤6 hours on a 2-core, 7GB RAM runner, ensuring no GPU dependencies are invoked. (See US-1, US-2, US-3)

### Key Entities

- **Interaction Clip**: A sequence of state-action-observation tuples representing a single task-agnostic interaction in the simulation.
- **Latent Descriptor**: A vector of statistical properties (variance, autocorrelation, etc.) derived from the latent embeddings of an Interaction Clip.
- **Hyperparameter Label**: The optimal pair of ($\tau$, $k$) values determined by grid search that minimizes task failure for a specific configuration.
- **Auto-ICWM Model**: The trained regressor that maps Latent Descriptors to Hyperparameter Labels.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between latent variance and the required sampling temperature is measured against the hypothesis that higher variance necessitates higher temperature. (See US-2)
- **SC-002**: The success rate of the Auto-ICWM pipeline on novel configurations is measured against the success rate of a fixed-parameter baseline (e.g., $\tau=1.0, k=32$). (See US-3)
- **SC-003**: The statistical significance of the performance improvement is measured against the standard threshold of $p < 0.05$ using a paired t-test or Wilcoxon test. (See US-3)
- **SC-004**: The total computational runtime of the full pipeline (extraction, training, validation) is measured against the 6-hour limit of the GitHub Actions free-tier runner. (See US-1, US-2, US-3)
- **SC-005**: The memory footprint of the model training and inference process is measured against the 7GB RAM limit of the CI runner. (See US-2, US-3)

## Assumptions

- The public simulation dataset (e.g., Franka Emika or Fetch) contains sufficient task-agnostic interaction clips to support both training ([deferred]) and testing ([deferred]) of the regressor model.
- The pre-trained ICWM encoder provided in the reference repository is compatible with the local CPU-only environment and does not require CUDA-specific kernels.
- The grid search for optimal hyperparameters is restricted to a manageable discrete set (e.g., $\tau \in \{0.5, 1.0, 1.5, 2.0\}$, $k \in \{16, 32, 64\}$) to ensure the labeling step completes within the 6-hour compute budget.
- The relationship between latent statistics and optimal hyperparameters is approximable by a simple non-linear model (MLP) without requiring deep transformer architectures or large-scale pre-training.
- The "novel configurations" in the test set are distinct enough from the training set to validate zero-shot generalization but share the same underlying dynamics distribution.
