# Feature Specification: Kairos: A Native World Model Stack for Physical AI

**Feature Branch**: `001-kairos-world-model-stack`  
**Created**: 2026-06-30  
**Status**: Draft  
**Input**: User description: "Kairos: A Native World Model Stack for Physical AI - How does the integration of hybrid multi-scale temporal memory mechanisms within a native world model stack influence the long-horizon planning fidelity and sample efficiency of embodied agents operating in open-world, safety-critical environments?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline World Model Training & Evaluation (Priority: P1)

**User Journey**: The researcher downloads a specific [deferred] stratified subset of the UNION of the Open X-Embodiment dataset and BridgeData V2, configures a MuJoCo simulation environment with a Franka Panda robot arm, and trains a baseline Transformer-based world model to predict future states. The system then evaluates this model on held-out test trajectories to establish a performance baseline for long-horizon success rate and prediction error.

**Why this priority**: This establishes the control condition against which the proposed "Kairos" memory architecture must be compared. Without a valid, reproducible baseline, no comparative claim regarding the hybrid memory mechanism can be made.

**Independent Test**: Can be fully tested by executing the training pipeline on the baseline model, verifying convergence, and generating a report of Success Rate, MSE, and Physics Consistency Score on the test set.

**Acceptance Scenarios**:

1. **Given** a downloaded [deferred] stratified subset of the union of Open X-Embodiment and BridgeData V2, **When** the baseline Transformer model is trained for 50 epochs on a CPU-only runner, **Then** the model must produce a valid checkpoint and report a Mean Squared Error (MSE) on the held-out test set of 500 trajectories that is strictly less than 0.15.
2. **Given** the trained baseline model, **When** it is evaluated on a multi-step "pick and place" task with obstacles in MuJoCo, **Then** the system must record a "Long-Horizon Success Rate" (percentage of tasks completed within N steps) and log the peak RAM usage to ensure it remains strictly less than 7 GB.
3. **Given** the evaluation results, **When** the statistical analysis script runs, **Then** it must output a descriptive statistic (mean, standard deviation) for the success rate across 5 random seeds, formatted for downstream comparison.

---

### User Story 2 - Hybrid Multi-Scale Memory Implementation & Ablation (Priority: P2)

**User Journey**: The researcher implements the "Hybrid Multi-Scale Temporal Memory" module (using open-source equivalents like GatedDeltaNet) and integrates it into the world model stack. The system trains this new architecture under identical hardware constraints and compares its planning fidelity and sample efficiency against the baseline.

**Why this priority**: This directly addresses the core research question by testing the specific architectural variable (hybrid memory) against the baseline. It is the primary experimental intervention.

**Independent Test**: Can be fully tested by training the memory-augmented model, running the same evaluation suite as the baseline, and generating a side-by-side comparison of success rates, MSE, and Physics Consistency Score.

**Acceptance Scenarios**:

1. **Given** the baseline training pipeline, **When** the Hybrid Multi-Scale Temporal Memory module is injected to train on the same [deferred] stratified subset of the combined dataset, **Then** the system must successfully train the model within 6 hours on a 2-core CPU runner without OOM errors AND achieve a final training loss strictly less than 0.10.
2. **Given** the trained memory-augmented model, **When** it is evaluated on the same 500 held-out test trajectories, **Then** the system must calculate the Long-Horizon Success Rate, Prediction Error (MSE), and Physics Consistency Score (PCS) using the exact same metrics as the baseline, and verify that MSE ≤ 90% of baseline MSE and PCS improvement ≥ 5%.
3. **Given** both baseline and memory-augmented results, **When** the Wilcoxon signed-rank test is executed across 5 random seeds, **Then** the system must output the p-value and effect size, and PASS if p < 0.05 AND effect size ≥ 0.2.

---

### User Story 3 - Resource Efficiency & Sparsity Analysis (Priority: P3)

**User Journey**: The researcher analyzes the computational overhead of the memory module, specifically testing if sparsity constraints can mitigate latency and memory usage to meet "simulation feasibility" claims on consumer hardware.

**Why this priority**: The idea explicitly hypothesizes that computational overhead may negate real-time claims. This story validates the feasibility of the architecture under strict resource constraints, a critical factor for Physical AI deployment.

**Independent Test**: Can be fully tested by running the memory-augmented model with varying sparsity constraints and logging inference latency and peak memory usage.

**Acceptance Scenarios**:

1. **Given** the trained memory-augmented model, **When** inference is run on a single test trajectory with sparsity constraints enabled, **Then** the system must log the 95th percentile (p95) inference latency over ≥ 1,000 steps and verify it remains strictly less than 200ms (simulating simulation feasibility for slow-motion control).
2. **Given** the resource logs, **When** the peak RAM usage is analyzed, **Then** the system must confirm that usage never exceeds 7 GB for the largest tested configuration.
3. **Given** the latency data, **When** the sensitivity analysis is run, **Then** the system must report how the inconsistency rate (failed predictions) varies across sparsity levels (e.g., 0.1, 0.5, 0.9).

---

### Edge Cases

- What happens when the downloaded dataset subset is corrupted or incomplete? (System must detect missing files and exit with a clear error code before training starts).
- How does the system handle simulation instability (e.g., robot falling through the floor in MuJoCo) during long-horizon tasks? (The evaluation script must catch simulation exceptions, log the failure as a "task failure," and continue to the next trajectory without crashing the entire batch).
- How does the system handle the case where the Wilcoxon signed-rank test assumptions (e.g., symmetric distribution of differences or sufficient sample size) are violated? (The system must fall back to a bootstrap confidence interval on the success rate difference and report the result).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and preprocess a specific [deferred] stratified subset of the UNION of the Open X-Embodiment dataset and BridgeData V2 via HuggingFace Datasets. (See US-1)
- **FR-002**: System MUST instantiate a MuJoCo physics environment with a Franka Emika Panda robot arm configured for multi-step "pick and place" tasks with obstacles. (See US-1)
- **FR-003**: System MUST implement a baseline Transformer-based dynamics model capable of predicting future states from current observations and actions. (See US-1)
- **FR-004**: System MUST implement a Hybrid Multi-Scale Temporal Memory module (using GatedDeltaNet or equivalent) that can be swapped into the baseline architecture. (See US-2)
- **FR-005**: System MUST evaluate both models on a held-out test set of 500 trajectories, calculating "Long-Horizon Success Rate", "Prediction Error" (MSE), and "Physics Consistency Score" (PCS). PCS is defined as the percentage of trajectories with zero conservation-of-momentum violations or collision errors. (See US-2)
- **FR-006**: System MUST perform a Wilcoxon signed-rank test across 5 random seeds to determine statistical significance of performance differences. (See US-2)
- **FR-007**: System MUST log peak RAM usage and inference latency per step to verify compliance with 7 GB RAM and 2-CPU constraints. (See US-3)
- **FR-008**: System MUST allow configuration of sparsity constraints to test their impact on latency and prediction error. (See US-3)

### Key Entities

- **Trajectory**: A sequence of states, actions, and rewards from the simulation environment, used for training and evaluation.
- **World Model**: A neural network architecture (Baseline or Memory-Augmented) that predicts future states given current state and action.
- **Simulation Environment**: The MuJoCo instance hosting the Franka Panda robot and obstacles.
- **Performance Metric**: Quantitative measures including Success Rate (binary task completion), Prediction Error (MSE), Physics Consistency Score (PCS, 0-100%), and Inference Latency (ms).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Long-Horizon Success Rate of the memory-augmented model is measured against the baseline model's success rate. Success is defined as: Memory-augmented success rate ≥ Baseline success rate + 5 percentage points, with p < 0.05. (See US-2)
- **SC-002**: Prediction Error (MSE) and Physics Consistency Score (PCS) of the memory-augmented model are measured against the baseline. Success is defined as: MSE ≤ 90% of baseline MSE AND PCS improvement ≥ 5 percentage points. (See US-2)
- **SC-003**: Inference latency per step is measured against a strict 200ms threshold (p95 over 1,000 steps) to evaluate the feasibility of "simulation feasibility" (≤ 5Hz loop) on consumer hardware. (See US-3)
- **SC-004**: Peak RAM usage is measured against the free-tier CI runner constraints to ensure the model fits within the allocated resource limits. (See US-3)
- **SC-005**: Statistical significance (p-value) of the performance difference is measured against the 0.05 threshold to determine if the observed improvements are non-random. (See US-2)
- **SC-006**: Sensitivity of the success rate to sparsity constraints is measured across a range of sparsity levels to validate the trade-off between efficiency and accuracy. (See US-3)

## Assumptions

- The Open X-Embodiment dataset (subset: robotics manipulation) and BridgeData V2 are available via HuggingFace Datasets and do not require authentication that blocks automated CI runners.
- MuJoCo physics engine can run deterministically on a CPU-only environment with a standard Franka Emika Panda robot model available in the simulation library.
- The "Hybrid Multi-Scale Temporal Memory" can be approximated using open-source implementations like GatedDeltaNet without proprietary layers, ensuring reproducibility.
- A stratified subset of the combined Open X-Embodiment and BridgeData V2 datasets is sufficient to train a small-scale world model that exhibits the general trends of the full dataset within the 6-hour compute limit.
- The "Long-Horizon Success Rate" metric is well-defined as "task completion within N steps" where N is a fixed constant (e.g., 50 steps) defined in the simulation configuration.
- The simulation environment (MuJoCo) is stable enough that the majority of trajectories do not result in catastrophic physics errors (e.g., exploding velocities) that would invalidate the test set.
- The free-tier GitHub Actions runner (standard CPU, limited RAM) provides sufficient compute for training small Transformer and GatedDeltaNet variants on the sampled dataset.
- The Open X-Embodiment dataset is strictly scoped to physical robotics manipulation tasks (e.g., pick-and-place, navigation) and does not contain psychological state variables such as 'anxiety' or 'rumination'. Consequently, the research question is explicitly bounded to physical simulation success metrics (success rate, prediction error, latency) only. Any future expansion to psychological modeling is out of scope for this specification and requires a separate data source and ethical review. (See US-1, US-2)
- The "real-time" claim is interpreted as "simulation feasibility" (strictly less than 200ms per step, i.e., ≥ 5Hz control loop) for the purpose of this simulation-based feasibility study, acknowledging that physical robot latency (typically > 100Hz) may differ.
- **Physics Consistency Score (PCS)**: PCS is defined numerically as the percentage of trajectories in the test set that contain zero violations of conservation of momentum or collision integrity checks. A score of [deferred] indicates perfect physical consistency.