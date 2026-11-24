# Feature Specification: llmXive follow-up: extending "In-Context World Modeling for Robotic Control"

**Feature Branch**: `001-auto-icwm-latent-dynamics`  
**Created**: 2026-07-30  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'In-Context World Modeling for Robotic Control'"

## User Scenarios & Testing

### User Story 1 - Automated Latent Statistic Extraction (Priority: P1) (See US-1)

The researcher needs to process raw interaction clips (state-action-observation tuples) from the ICWM dataset to generate a structured table of statistical descriptors (variance, autocorrelation, spectral density) for each clip. This is the foundational step; without these features, no mapping to hyperparameters can be learned.

**Why this priority**: This is the data ingestion and feature engineering layer. If the system cannot reliably extract the statistical properties of the latent trajectories, the entire hypothesis regarding "latent complexity" cannot be tested. It is the prerequisite for all downstream modeling.

**Independent Test**: Can be fully tested by running the extraction pipeline on a small, fixed subset of interaction clips and verifying that the output CSV contains the required columns (clip_id, variance, autocorr_lag1, spectral_density) with non‑null, finite numerical values.

**Acceptance Scenarios**:

1. **Given** a directory of valid interaction clip files from the ICWM simulation dataset, **When** the extraction script is executed, **Then** a structured dataset is generated containing statistical descriptors for every clip.
2. **Given** a clip with high-variance latent trajectories, **When** the statistics are computed, **Then** the variance metric is > 2x the variance of a low-variance clip from a stable configuration.

---

### User Story 2 - Hyperparameter Mapping Model Training (Priority: P2) (See US-2)

The researcher needs to train a lightweight regressor (MLP or linear) that maps the extracted statistical descriptors to the optimal inference hyperparameters (sampling temperature $\tau$, context window $k$) determined via grid search on the training set only.

**Why this priority**: This implements the core hypothesis: that latent statistics predict optimal inference strategy. It transforms the descriptive statistics from Story 1 into a predictive capability. Without this, the system cannot "auto-calibrate."

**Independent Test**: Can be fully tested by training the model on [deferred] of the training data and evaluating the Mean Squared Error (MSE) on the held-out [deferred] test set, ensuring the error is at least 10% lower than a naive baseline (predicting the global mean temperature for all inputs).

**Acceptance Scenarios**:

1. **Given** a trained regressor model and a set of novel configuration descriptors, **When** the model predicts hyperparameters, **Then** the predicted values are within the valid operational range (e.g., $0.1 \le \tau \le 2.0$, $1 \le k \le 64$).
2. **Given** a configuration with high latent instability, **When** the model predicts, **Then** the output suggests a higher sampling temperature or longer context window compared to a stable configuration.

---

### User Story 3 - Zero-Shot Calibration Validation (Priority: P3) (See US-3)

The researcher needs to execute the full "Auto-ICWM" pipeline on novel robotic configurations (where no grid search was performed) to verify that the model‑predicted hyperparameters yield a higher success rate than fixed‑parameter baselines.

**Why this priority**: This is the final validation of the research question. It demonstrates the practical utility of the method in the target environment (novel configurations) and quantifies the improvement over static approaches.

**Independent Test**: Can be fully tested by running the validation protocol on the test set (novel configurations), executing **five** episodes per clip for both the Auto‑ICWM pipeline and the fixed baseline ($\tau\!=\!1.0$, $k\!=\!32$), computing a per‑clip success **rate** (successful episodes / 5), and then performing a paired **t‑test** on these rates. The test passes only if the p‑value < 0.05 and the mean rate improvement is ≥ 5 % absolute.

**Acceptance Scenarios**:

1. **Given** a novel robotic configuration not seen during training, **When** the Auto‑ICWM pipeline predicts and applies hyperparameters across five episodes, **Then** the per‑clip success rate is recorded and compared against the fixed‑baseline success rate.
2. **Given** the results of the validation runs, **When** the statistical analysis is performed, **Then** the paired t‑test yields $p < 0.05$ and the average success‑rate gain ≥ 5 % absolute.

### Edge Cases

- **Near‑zero variance**: Generate a clip where all latent embeddings are constant (e.g., by feeding a static observation sequence). The descriptor extractor must detect variance ≈ 0 without division‑by‑zero in spectral density and still output a low‑complexity hyper‑parameter prediction.
- **Encoder failure**: Create an out‑of‑distribution observation (e.g., random noise image) that causes the ICWM encoder to raise an exception. The pipeline must catch the exception, log the clip ID to `logs/encoder_failures.txt`, and skip the clip for both labeling and training.
- **Hyper‑parameter ties**: When grid‑search yields identical performance for multiple $(\tau,k)$ pairs, apply a deterministic tie‑breaker: select the pair with the **lowest** temperature; if temperatures are equal, select the **smallest** context window.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST extract statistical descriptors (variance, autocorrelation, spectral density) from latent token sequences generated by the pre‑trained ICWM encoder for every input interaction clip. (See US-1)
- **FR-002**: The system MUST perform an independent grid search over sampling temperature ($\tau$) and context window length ($k$) for each **training** configuration to establish ground‑truth optimal hyperparameters. No grid search is performed for **test** (novel) configurations. The search space is limited to $\tau \in \{0.5, 1.0, 1.5\}$ and $k \in \{16, 32, 64\}$ (6 combos). (See US-2)
- **FR-003**: The system MUST train a lightweight, CPU‑tractable regressor (e.g., MLP or linear regression) using the statistical descriptors as inputs and the grid‑searched hyperparameters (from the training set only) as targets. (See US-2)
- **FR-004**: The system MUST execute the validation protocol on novel configurations, applying the predicted hyperparameters to the VLA policy and recording the task success rate. (See US-3)
- **FR-005**: The system MUST perform a statistical significance test (paired t‑test) comparing the Auto‑ICWM success‑rate distribution against a fixed‑parameter baseline. (See US-3)
- **FR-006**: The system MUST enforce a computational budget of **≤ 4 hours** on a 2‑core, 7 GB RAM runner, ensuring no GPU dependencies are invoked. (See US-1, US-2, US-3)
- **FR-007**: The system MUST compute an independent “task complexity” metric defined as the **number of distinct sub‑goals** listed in the environment’s `task_metadata.yaml` file for each configuration, to validate the hypothesis that latent variance correlates with complexity, independent of VLA success rate. (See US-2, US-3)
- **FR-008**: The system MUST compute the Pearson correlation between latent **variance** and the **ground‑truth optimal temperature** (from grid search) while controlling for task complexity, to assess predictive power without circularity. (See US-2, US-3)

### Key Entities

- **Interaction Clip**: A sequence of state-action-observation tuples representing a single task‑agnostic interaction in the simulation.
- **Latent Descriptor**: A vector of statistical properties (variance, autocorrelation, etc.) derived from the latent embeddings of an Interaction Clip.
- **Hyperparameter Label**: The optimal pair of ($\tau$, $k$) values determined by grid search (on training set only) that minimizes task failure for a specific configuration.
- **Auto-ICWM Model**: The trained regressor that maps Latent Descriptors to Hyperparameter Labels.
- **Task Complexity**: An independent metric representing the number of distinct sub‑goals in the simulation environment, used to validate the latent variance hypothesis.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between latent variance and the independent “task complexity” metric must be > 0.5 with $p < 0.05$. (See US-2, US-3)
- **SC-002**: The success rate of the Auto‑ICWM pipeline on novel configurations must be at least **[deferred] absolute** higher than the success rate of a fixed‑parameter baseline ($\tau\!=\!1.0$, $k\!=\!32$), with $p < 0.05$. (See US-3)
- **SC-003**: The statistical significance of the performance improvement is measured using a **paired t‑test** on per‑clip success‑rate vectors (α = 0.05). (See US-3)
- **SC-004**: Total runtime of the full pipeline (extraction, training, validation) is measured as **wall‑clock time** using Python’s `time.time()` wrapper and logged in the CI run summary; it must not exceed the 4‑hour limit. (See US-1, US-2, US-3)
- **SC-005**: Memory footprint of the model training and inference process is measured as **peak RSS** (Resident Set Size) via the `psutil` library and must stay ≤ 7 GB. (See US-2, US-3)
- **SC-006**: The regressor's MSE on the held‑out test set must be at least 10 % lower than the naive baseline (predicting the global mean temperature). (See US-2)

## Assumptions

- The public simulation dataset (e.g., Franka Emika or Fetch) contains sufficient task‑agnostic interaction clips to support both training and testing of the regressor model.
- The pre‑trained ICWM encoder provided in the reference repository is compatible with the local CPU‑only environment and does not require CUDA‑specific kernels.
- The grid search for optimal hyperparameters is restricted to the discrete set $\tau \in \{0.5, 1.0, 1.5\}$, $k \in \{16, 32, 64\}$ (6 combos) and **5 episodes per combo**; this yields $200 \times 6 \times 5 = 6{,}000$ episodes, which empirical profiling shows completes within **[deferred]** on the specified runner.
- The relationship between latent statistics and optimal hyperparameters is approximable by a simple non‑linear model (MLP) without requiring deep transformer architectures or large‑scale pre‑training.
- The “novel configurations” in the test set are distinct enough from the training set to validate zero‑shot generalization but share the same underlying dynamics distribution.
- The “task complexity” metric (sub‑goal count) is available in `task_metadata.yaml` for each configuration and accurately reflects the structural difficulty of the simulation environment, independent of the VLA policy's performance.
