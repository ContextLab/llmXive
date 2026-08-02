# Feature Specification: llmXive Follow-up: Non-Neural Approximation of VLA Priors

**Feature Branch**: `001-non-neural-vla-approximation`  
**Created**: 2026-08-02  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Envir'"

## User Scenarios & Testing

### US-01 - Dataset Ingestion and Trajectory Clustering (Priority: P1)

The system must ingest the Qwen-VLA training dataset, extract a representative sample of text-action pairs, and cluster the action sequences into behavioral groups based on kinematic features (velocity, acceleration, joint angles).

**Why this priority**: This is the foundational data processing step. Without a valid, clustered dataset, no non-neural models can be fitted, and no trajectory generation is possible. It delivers the "data substrate" for the entire research pipeline.

**Independent Test**: Can be fully tested by verifying that the output of the clustering script contains up to 50 clusters, each with a minimum of 100 samples (if k > 1), and that the kinematic features are normalized and within valid physical bounds for the simulator.

**Acceptance Scenarios**:

1. **Given** the Qwen-VLA dataset is available on HuggingFace, **When** the ingestion script runs on a CPU-only runner, **Then** the system extracts all available valid (text, action) pairs without crashing or timing out.
2. **Given** the ingested action sequences, **When** K-means clustering (k=50) is applied to kinematic features, **Then** the system outputs up to 50 distinct cluster centers and assigns every sample to exactly one cluster.
3. **Given** a cluster, **When** the kinematic statistics (mean velocity, max acceleration) are calculated, **Then** the values are physically plausible (e.g., joint angles within mechanical limits) and do not contain NaNs or infinities.

---

### US-02 - Non-Neural Model Fitting and Inference (Priority: P2)

The system must fit lightweight probabilistic models (Decision Trees or Gaussian Mixture Models) to each cluster, mapping frozen BERT text embeddings to the cluster's action distribution, and implement a CPU-only inference engine that generates trajectories for new prompts.

**Why this priority**: This implements the core hypothesis: that VLA priors can be approximated by non-neural logic. It delivers the "distilled policy" which is the primary object of study.

**Independent Test**: Can be fully tested by feeding a held-out set of text prompts into the inference engine and verifying that the output is a valid trajectory array (correct shape, valid joint angles) generated within a fixed time budget (≤ 2 seconds per prompt) without GPU usage.

**Acceptance Scenarios**:

1. **Given** a cluster of action sequences and a frozen BERT encoder, **When** a Decision Tree regressor is trained to map embeddings to actions, **Then** the model achieves a held-out validation R² score of ≥ 0.6 for that cluster, and the conditional variance of actions within the cluster is statistically significant (p < 0.05) to ensure the text embedding is a valid predictor.
2. **Given** a new text instruction not seen during training, **When** the inference engine processes it, **Then** it returns a complete trajectory array of the expected length (e.g., a sufficient number of time steps) with no CUDA errors.
3. **Given** the inference engine, **When** it is run on a CPU-only GitHub Actions runner, **Then** the total memory usage remains below 7 GB and the execution time for 100 prompts is ≤ 10 minutes.

---

### US-03 - Simulation Evaluation and Statistical Comparison (Priority: P3)

The system must execute generated trajectories in a PyBullet simulation for Multiple test prompts per task type (grasp, navigate, place), measure success rates and collision counts, and perform paired t-tests against a random baseline and VLA proxy metrics.

**Why this priority**: This provides the empirical validation of the research question. It delivers the "truth" regarding the trade-off between complexity and fidelity.

**Independent Test**: Can be fully tested by running the simulation loop and verifying that the output CSV contains success/failure flags and collision counts for every test prompt, and that the statistical test returns a valid p-value.

**Acceptance Scenarios**:

1. **Given** 100 generated trajectories for "grasp" tasks, **When** they are executed in PyBullet, **Then** the system records a binary success/failure outcome and a collision count for each trajectory.
2. **Given** the success rates of the non-neural model, the random baseline, and the original Qwen-VLA proxy, **When** paired t-tests are performed on the same test prompts, **Then** the system outputs p-values and confidence intervals indicating statistical significance (or lack thereof).
3. **Given** the full evaluation results, **When** the report is generated, **Then** it explicitly states the trajectory fidelity percentage (e.g., "Non-neural model achieved ≥ 95% of the VLA proxy's trajectory characteristics") and the complexity reduction factor.

### Edge Cases

- What happens when the text embedding for a new prompt falls far outside the distribution of any cluster (e.g., OOD prompt)? The system must default to the nearest cluster but log a "low-confidence" flag.
- How does the system handle a physics simulation step where the trajectory violates hard kinematic constraints (e.g., joint limits exceeded)? The simulation must catch the error, record it as a "failure," and continue to the next prompt without crashing the runner.
- What happens if the Qwen-VLA dataset download fails or the mirror is unavailable? The system must fail fast with a clear error message and not proceed to training.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the Qwen-VLA dataset (text instructions and action sequences) from the specified HuggingFace repository, ensuring all required samples are present and valid. (See US-01)
- **FR-002**: System MUST cluster the ingested action sequences into up to 50 groups using K-means based on normalized kinematic features (velocity, acceleration, joint angles). (See US-01)
- **FR-002a**: System MUST validate the clustering by calculating the average silhouette score; if the score is < 0.25, the system MUST reduce the target cluster count (k) by [deferred] and re-run clustering until a valid configuration is found or k=1 is reached. If k=1 is reached and the score is still < 0.25, the system MUST proceed with k=1 and log a "degenerate clustering" warning. (See US-01)
- **FR-003**: System MUST train a lightweight probabilistic model (Decision Tree or GMM) for each valid cluster produced by FR-002/FR-002a, mapping frozen BERT text embeddings to the cluster's action distribution. (See US-02)
- **FR-004**: System MUST implement a CPU-only inference engine that selects the nearest cluster for a new prompt and samples a trajectory from the fitted model without using CUDA or GPU accelerators. (See US-02)
- **FR-005**: System MUST execute generated trajectories in a PyBullet simulation for 100 test prompts per task type (grasp, navigate, place) and record success rates and collision counts. (See US-03)
- **FR-006**: System MUST perform paired t-tests comparing the non-neural model's success rate against a random sampling baseline and the original Qwen-VLA proxy metrics on the same test prompts, and report the p-values. (See US-03)

### Key Entities

- **Trajectory**: A time-series array of joint angles and end-effector positions representing a robot's movement.
- **Cluster**: A group of similar trajectories identified by K-means, characterized by a centroid and a fitted probabilistic model.
- **Prompt**: A text instruction (e.g., "Pick up the red block") used to query the model.
- **Simulation Result**: A record containing the task type, success flag, collision count, and execution time for a single trajectory.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The trajectory fidelity of the non-neural model (percentage of VLA trajectory characteristics preserved) is measured against the actual trajectory outputs of the original Qwen-VLA model on the same held-out test set. (See US-03)
- **SC-002**: The task success rate of the non-neural model is measured against the success rate of a random sampling baseline in the PyBullet simulator. (See US-03)
- **SC-003**: The computational cost (memory usage and execution time) of the non-neural inference is measured against the constraints of a free-tier GitHub Actions runner (≤ 7 GB RAM, ≤ 6 hours total time). (See US-02)
- **SC-004**: The statistical significance of the performance difference between the non-neural model, the random baseline, and the VLA proxy is measured against a significance threshold of α = 0.05 using paired t-tests on the same test prompts. (See US-03)
- **SC-005**: The Clustering Coverage is measured against the total dataset size, ensuring ≥ 98% of the ingested samples are assigned to exactly one cluster. (See US-01)

## Assumptions

- The Qwen-VLA dataset available on HuggingFace contains the specific text-action pairs required for the subset and is accessible via a public mirror if the primary link is unstable.
- The PyBullet physics simulator can run deterministically on a CPU-only runner without requiring GPU acceleration for the specific robot models used in the "grasp," "navigate," and "place" tasks.
- The frozen BERT encoder (e.g., `bert-base-uncased`) is small enough to fit within the 7 GB RAM limit of the free-tier runner when combined with the clustering and simulation processes.
- The "Trajectory Fidelity" metric is defined as the percentage of kinematic features (velocity, acceleration profiles) within a small error margin of the original VLA's trajectory, as this provides a concrete, measurable threshold for the trade-off analysis.
- The random sampling baseline will generate trajectories by uniformly sampling from the joint angle space within the robot's mechanical limits, serving as a strict lower-bound reference.
- The dataset contains sufficient variance in action sequences to support clustering; if the data is uniform, FR-002a will reduce the cluster count to 1 and log a warning.