# Feature Specification: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

**Feature Branch**: `001-llmxive-gam-symbolic-planner`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Geometric Action Model for Robot Policy Learning'"

## User Scenarios & Testing

### User Story 1 - Synthetic Topology-Shift Test Set Generation (Priority: P1)

**Researcher** needs to generate a synthetic dataset of manipulation tasks involving novel kinematic chains (e.g., variable hinge counts) and deformable materials (e.g., soft ropes, cloth) that are strictly absent from the original GAM training distribution, using a CPU-based physics simulator (PyBullet) to ensure reproducibility and zero-shot evaluation conditions.

**Why this priority**: Without a rigorously defined "topology-shift" test set, the core hypothesis (zero-shot generalization to unseen topologies) cannot be tested. This is the foundational data layer required for all subsequent model evaluation.

**Independent Test**: Can be fully tested by running the data generation script and verifying the output files contain valid physics simulation states for at least 50 distinct novel topologies, with a checksum validation confirming no overlap with the original GAM training set.

**Acceptance Scenarios**:
1. **Given** a configuration for a novel kinematic chain (e.g., 5-link hinge), **When** the generation script is executed in PyBullet, **Then** the system outputs a valid sequence of simulation states (latent inputs and ground-truth actions) without physics errors.
2. **Given** a request to generate a deformable material task (e.g., rope dragging), **When** the script runs, **Then** the resulting dataset includes vertex-level position data for the deformable object at every timestep, distinct from rigid-body data.
3. **Given** the generated test set, **When** a hash of the dataset metadata is compared against the original GAM training metadata, **Then** the system confirms zero overlap in object topology definitions.

---

### User Story 2 - Symbolic Latent Planner Execution (Priority: P2)

**Researcher** needs to execute the frozen Geometric Foundation Model (GFM) encoder/decoder to map 3D observations to latent space and back, while injecting a differentiable symbolic solver that enforces geometric constraints (rigid-body, soft-body) in physical 3D space (via decoded actions), ensuring the entire pipeline runs on a standard multi-core CPU without GPU acceleration. The system MUST verify that the symbolic logic is decoupled from decoder fidelity by isolating the solver's constraint satisfaction check from the decoder's reconstruction error.

**Why this priority**: This is the core experimental intervention (replacing the neural predictor with a symbolic solver). It validates the feasibility of the "symbolic-latent" approach and measures the primary metric of success (zero-shot generalization).

**Independent Test**: Can be fully tested by loading the frozen GFM weights, running the symbolic planner on a single test case from the P1 dataset, decoding the latent action to physical space, and verifying that the resulting physical action satisfies the geometric constraints in PyBullet without crashing.

**Acceptance Scenarios**:
1. **Given** a pre-processed observation from the test set, **When** the GFM encoder processes it, **Then** the system outputs a 3D latent vector within the expected dimensionality range.
2. **Given** the latent vector and task constraints, **When** the symbolic solver computes the next action in physical space (via decoded latent), **Then** the solver returns an action that strictly satisfies the defined rigid-body or soft-body constraints (e.g., no interpenetration, valid joint limits) as verified by the PyBullet physics engine.
3. **Given** the computed action, **When** the GFM decoder reconstructs the physical action, **Then** the system executes the action in the PyBullet simulator and records the resulting state without crashing or requiring GPU resources.

---

### User Story 3 - Comparative Statistical Analysis (Priority: P3)

**Researcher** needs to compare the task success rate and inference latency of the symbolic-latent approach against the baseline GAM (neural predictor) using statistical tests (Fisher's Exact Test for success rates and paired t-test for latency) to determine if the symbolic approach achieves zero-shot generalization with lower latency.

**Why this priority**: This provides the scientific conclusion. It quantifies the trade-off between generalization capability and computational efficiency, directly answering the research question.

**Independent Test**: Can be fully tested by running the analysis script on the collected results from P1 and P2, generating a report that includes p-values, confidence intervals, and effect sizes for both success rate and latency comparisons.

**Acceptance Scenarios**:
1. **Given** the binary success/failure outcomes for 50 trials of the symbolic approach and 50 trials of the baseline, **When** the Fisher's Exact Test is executed, **Then** the system outputs a p-value and a confidence interval for the difference in success rates.
2. **Given** the inference latency measurements (ms) for both approaches, **When** the paired t-test is executed, **Then** the system outputs the mean difference, p-value, and effect size (Cohen's d).
3. **Given** the analysis results, **When** the report is generated, **Then** it explicitly states whether the null hypothesis (no difference in generalization) is rejected at the α=0.05 significance level.

---

### Edge Cases

- **What happens when** the symbolic solver fails to find a valid action sequence due to infeasible constraints (e.g., a requested motion violates physics)?
  - *System handles*: The solver must return a specific "infeasible" flag, and the simulation step must be recorded as a failure (task not completed) rather than crashing the pipeline.
- **How does the system handle** a topology in the test set that is so complex the symbolic solver exceeds the A time-limited CI window will be established. The research question, method, and references remain unchanged as per the original planning document.?
  - *System handles*: The solver must implement a timeout mechanism (e.g., a predefined duration per step) and record the trial as a timeout failure, logging the specific topology complexity that caused it.
- **What happens when** the frozen GFM encoder produces latent representations that drift significantly from the training distribution due to the novel topology?
  - *System handles*: The system must detect latent drift (e.g., via Mahalanobis distance) and flag the trial for manual review, treating it as a potential "out-of-distribution" failure mode.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST generate a synthetic test set of at least 50 unique manipulation tasks involving novel kinematic chains and deformable materials using PyBullet, ensuring zero overlap with the original GAM training distribution (See US-1).
- **FR-002**: The system MUST load and freeze the Geometric Foundation Model (GFM) encoder and decoder weights from the original GAM implementation to preserve the 3D latent geometric representation (See US-2).
- **FR-003**: The system MUST replace the learned causal future predictor with a differentiable symbolic solver (implemented as a differentiable convex optimization layer, e.g., using DiffTaichi) that enforces rigid-body (non-penetration, joint limits) and soft-body constraints in physical 3D space via the GFM decoder output. The system MUST verify differentiability by ensuring gradients flow from the constraint violation loss, through the decoder, to the solver parameters (See US-2).
- **FR-004**: The system MUST execute the entire inference pipeline (encoding, solving, decoding, simulation) on a GitHub Actions 2-core x86_64 runner (Intel Xeon or equivalent) without requiring GPU, CUDA, or 8-bit quantization libraries (See US-2).
- **FR-005**: The system MUST record binary task success (manipulation completed vs. failed) and inference latency (ms per step) for each of the 50 randomized trials for both the symbolic approach and the baseline GAM (See US-3).
- **FR-006**: The system MUST apply Fisher's Exact Test to compare success rates (to handle low counts) and a paired t-test to compare inference latencies between the symbolic and baseline approaches. The system MUST report p-values, 95% confidence intervals, and effect sizes (Cohen's d) for both tests, using a significance threshold of α=0.05 (See US-3).

### Key Entities

- **Topology-Shift Test Set**: A collection of simulation environments and initial states featuring object topologies (kinematic chains, deformable meshes) not present in the original training data.
- **Symbolic Solver**: A constraint satisfaction module operating on decoded 3D states that outputs action sequences based on geometric priors rather than learned weights.
- **Latent Trajectory**: The sequence of 3D latent vectors generated by the frozen GFM encoder as it processes the simulation states.
- **Baseline GAM**: The original Geometric Action Model implementation with the learned neural predictor, used as the control condition for comparison.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The task success rate of the symbolic-latent approach on the novel topology test set is measured against the success rate of the baseline GAM. Success is defined as the manipulated object reaching the target zone (center within 5cm) without collision for a duration of approximately one second (See US-3).
- **SC-002**: The inference latency (ms per step) of the symbolic-latent approach is measured against the baseline GAM latency on the same hardware configuration (See US-3).
- **SC-003**: The statistical significance of the difference in success rates is measured against the null hypothesis of no difference using Fisher's Exact Test with a 95% confidence interval (See US-3).
- **SC-004**: The statistical significance of the difference in latency is measured against the null hypothesis of no difference using a paired t-test with a 95% confidence interval (See US-3).
- **SC-005**: The feasibility of the approach is measured against the constraint of completing all trials within a 6-hour CI time limit on a GitHub Actions 2-core x86_64 runner (See US-2).

## Assumptions

- **Assumption about data source**: The original GAM training dataset and weights are accessible and compatible with the current environment, and the PyBullet physics simulator can accurately model the required deformable materials and kinematic chains for the test set.
- **Assumption about computational limits**: The symbolic solver's complexity is such that it can solve the constraint satisfaction problem for a single timestep within <300 seconds on a Multi-core x86_64 CPU, ensuring the total -trial experiment fits within the 6-hour CI window (assuming ≤12 timesteps per trial).
- **Assumption about model freezing**: The frozen GFM encoder/decoder, trained on the original distribution, will produce valid latent representations for the novel topologies without requiring fine-tuning or domain adaptation, even if the latent distribution shifts slightly. The decoder is assumed to be the necessary interface for physical constraint validation, consistent with Constitution VI (Latent-Space Symbolic Fidelity) which mandates that physical constraints be resolved in 3D space, not the latent manifold.
- **Assumption about statistical power**: A sample size of a sufficient number of trials per condition is sufficient to detect a moderate effect size (Cohen's d ≈ moderate magnitude) in latency and a meaningful difference in success rates (e.g., an absolute difference) with α=0.05, acknowledging that power analysis for the exact effect size is deferred until preliminary data is available. Fisher's Exact Test is used for success rates to ensure validity under low-success-rate conditions.
- **Assumption about constraint definitions**: The geometric constraints (rigid-body, soft-body) required for the symbolic solver are mathematically formulated in physical 3D space (Euclidean coordinates) via the GFM decoder output, ensuring that the validation target (constraint satisfaction) is physically grounded and verifiable.