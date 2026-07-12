# Feature Specification: Robotic AI Sensory Fidelity Ablation Study

**Feature Branch**: `001-sensory-fidelity-ablation`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "Investigation into how sensory representation fidelity (raw pixels vs. occupancy grids) influences RL sample efficiency and generalization in autonomous navigation, constrained to CPU-only execution."

## User Scenarios & Testing

### User Story 1 - Baseline Environment & Classical/Stochastic Planner Execution (Priority: P1)

The system MUST establish a reproducible simulation environment and execute two baselines: (1) a classical non-learning baseline (Pure Pursuit/Dijkstra) to define the theoretical performance ceiling, and (2) a stochastic baseline (random policy) to provide a realistic floor for sample efficiency comparison. This is the foundation; without known bounds, RL performance cannot be evaluated.

**Why this priority**: This is the control condition. If the baselines fail to navigate the test track or the environment setup is unstable, no RL results are meaningful. It validates the simulation wrapper and sensor noise injection.

**Independent Test**: Can be fully tested by running the `run_baselines.py` script, verifying that the classical planner completes ≥ 80% of episodes, the stochastic baseline completes ≤ 10% of episodes, and logs path optimality ratios.

**Acceptance Scenarios**:

1. **Given** a configured CARLA simulation environment with randomized obstacle density across N=30 randomized seeds, **When** the Pure Pursuit controller is executed, **Then** the vehicle completes ≥ 80% of episodes, and the average path optimality ratio is recorded as a reference target (not a pass/fail gate) for RL agents.
2. **Given** the same environment, **When** the Dijkstra planner is executed on a -core CPU runner with x64 map resolution, **Then** it generates a collision-free path with the shortest possible length (optimality ratio = 1.0) within 500ms, serving as the theoretical upper bound.

---

### User Story 2 - Sensory Modality Data Pipeline & Preprocessing (Priority: P2)

The system MUST implement a data pipeline that ingests raw sensor data (RGB, Depth, LiDAR) and transforms them into the three distinct input modalities: (1) Raw RGB images (defined as x84 normalized tensors), (2) Downsampled depth maps, and (3) 2D occupancy grids. This enables the ablation study by ensuring the only variable changing is the input representation.

**Why this priority**: This is the core experimental variable. Without consistent, correct generation of these three modalities from the same ground truth, the comparison of sample efficiency is invalid.

**Independent Test**: Can be fully tested by running the `generate_modalities.py` script on a fixed set of A set of frames will be utilized to address the research question., verifying that the output shapes match specifications (e.g., occupancy grid is a binary matrix of appropriate resolution), and that the occupancy grid correctly represents obstacles present in the raw depth map.

**Acceptance Scenarios**:

1. **Given** a raw LiDAR point cloud and camera image pair, **When** the preprocessing pipeline runs, **Then** it outputs a multi-dimensional occupancy grid where occupied cells correspond to obstacles within the vehicle's m radius, with a false positive rate in free space ≤ 1% (accounting for sensor noise floor).
2. **Given** a raw RGB image, **When** the pipeline processes it, **Then** it outputs a normalized tensor of shape (C, H, W) suitable for the MobileNetV2 backbone, where C represents the number of input channels, preserving aspect ratio via center-cropping.

---

### User Story 3 - DRL Training & Statistical Analysis (Priority: P3)

The system MUST train lightweight DQN agents (MobileNet backbone) for each sensory modality under a A fixed computational time budget will be imposed on the analysis. The research question remains: [Research Question]. The method remains: [Method]. References: [References]., then perform statistical analysis (learning curve analysis + ANOVA/Kruskal-Wallis) to determine if differences in sample efficiency and success rates are significant.

**Why this priority**: This delivers the research answer. It synthesizes the data from US-1 and US-2 into a conclusion about the "sweet spot" of information density.

**Independent Test**: Can be fully tested by executing `train_and_analyze.py`, which must complete within 6 hours on a 2-core runner, produce a CSV of training curves, and output a JSON report stating whether the difference between "Raw RGB" and "Occupancy Grid" sample efficiency (AUC) is statistically significant (p < 0.05).

**Acceptance Scenarios**:

1. **Given** the three sensory modalities and a 2-core CPU environment, **When** the DQN agent trains, **Then** the total wall-clock time does not exceed the specified wall-clock time limit, and peak RAM usage remains below a low memory threshold.
2. **Given** the final learning curves for all three modalities, **When** the statistical analysis runs, **Then** it reports the Area Under the Curve (AUC) for success rates, time-to-convergence, and a p-value from the appropriate statistical test (ANOVA or Kruskal-Wallis), explicitly labeling findings as associational.

---

### Edge Cases

- **What happens when** the simulation crashes due to memory pressure during high-obstacle-density curriculum steps? The system MUST catch the exception, log the current episode count, and attempt to resume from the last checkpoint rather than failing the entire job.
- **How does the system handle** a scenario where the occupancy grid generation fails for a specific frame (e.g., LiDAR dropout)? The system MUST substitute a "safe" empty grid for that single frame and log the event, ensuring the training loop does not break, but the episode is marked as "noisy" for later exclusion if necessary.
- **What happens when** the CPU runner cannot complete the planned episodes in 6 hours? The system MUST stop training at the 6-hour mark, record the current step count, and proceed to evaluation with the partially trained model, clearly marking the result as "time-limited" in the final report.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate three distinct input modalities (Raw RGB defined as 84x84, Downsampled Depth, 2D Occupancy Grid) from the same ground-truth sensor data to enable ablation, ensuring spatial alignment across modalities (See US-2).
- **FR-002**: System MUST implement a lightweight DQN agent using a MobileNetV2 backbone pruned to <1M parameters to ensure CPU tractability, avoiding any CUDA-dependent operations (See US-3).
- **FR-003**: System MUST enforce a hard wall-clock time limit on the training process., stopping execution and saving the checkpoint if the limit is reached (See US-3).
- **FR-004**: System MUST implement a classical baseline (Pure Pursuit/Dijkstra) that operates on the same simulated environment and sensor noise profiles as the RL agents to provide a theoretical performance ceiling (See US-1).
- **FR-005**: System MUST perform a statistical analysis on the learning curves (Area Under the Curve - AUC and time-to-convergence) using One-way ANOVA or, if normality is violated (Shapiro-Wilk p < 0.05), Kruskal-Wallis test, followed by appropriate post-hoc tests (Tukey's HSD or Dunn's test) to determine statistical significance (See US-3).
- **FR-006**: System MUST log peak RAM usage and CPU utilization at regular intervals during training to verify adherence to the 7 GB RAM and 2-core constraints (See US-3).
- **FR-007**: System MUST frame all comparative findings as associational relationships between sensory fidelity and learning dynamics, explicitly avoiding causal language unless randomization is proven (See US-3).
- **FR-008**: System MUST perform a sensitivity analysis on the occupancy grid generation threshold, sweeping over a range of values (e.g., a spectrum spanning from low to high) to ensure robustness, with specific values determined in the implementation plan (See Assumptions).
- **FR-009**: System MUST perform explicit extrinsic calibration and coordinate transformation validation between sensor modalities (KITTI/CARLA) before data generation to prevent systematic bias (See Assumptions).

### Key Entities

- **SensorModality**: An enumeration of the input types (RGB, Depth, OccupancyGrid) with associated preprocessing parameters.
- **TrainingRun**: A record of a specific DQN training session, containing hyperparameters, total steps, wall-clock time, and peak resource usage.
- **NavigationResult**: A record of a single episode outcome, including success (boolean), path length, collision count, and inference latency.
- **LearningCurve**: A time-series record of success rates or rewards per episode, used for AUC calculation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: Sample efficiency (episodes to reach a target success rate) is measured across the three sensory modalities to determine the "sweet spot" of information density. Target success rate is defined as ≥ 90% success sustained over 10 consecutive episodes (See FR-002, US-3).
- **SC-002**: Inference latency (ms per step) is measured on the CPU-only runner for each modality to verify embedded feasibility, compared against the real-time constraint of ≤ 33ms per step (Hz control) (See FR-003, US-3).
- **SC-003**: Statistical significance of performance differences is measured via p-values from the appropriate post-hoc tests (Tukey's HSD or Dunn's), ensuring findings are not due to random variance (See FR-005, US-3).
- **SC-004**: Path optimality ratio (agent path length vs. shortest path) is measured against the classical baseline to assess navigation quality (See FR-004, US-1).
- **SC-005**: Resource compliance is measured by verifying peak RAM usage remains within acceptable operational limits and Total training time is constrained to be within a practical, single-session duration. (See FR-003, FR-006).
- **SC-006**: Learning curve robustness is measured by the stability of the Area Under the Curve (AUC) metric across different random seeds (See FR-005).

## Assumptions

- **Assumption about data source**: The KITTI Vision Benchmark Suite and CARLA simulator provide sufficient ground-truth data to generate accurate occupancy grids and depth maps, provided that explicit extrinsic calibration and coordinate transformation validation (as mandated by FR-009) are performed to align the sensor frames.
- **Assumption about computational limits**: A 2-core CPU runner with 7 GB RAM is sufficient to train a pruned MobileNetV2 DQN (under 1M parameters) for a representative number of training episodes, assuming the dataset is sampled appropriately (e.g., at a standard resolution) and no GPU-specific libraries (like `bitsandbytes`) are invoked.
- **Assumption about methodology**: The relationship between sensory fidelity and sample efficiency is non-linear and can be detected via analysis of learning curves (AUC). A moderate effect size (Cohen's f ≥ 0.25) is *expected* for sample size planning, but the study's validity depends on running the statistical test, not on achieving this specific effect size.
- **Assumption about statistical framing**: Since the study uses simulation with randomized obstacle generation but no random assignment to "treatment" groups in a real-world sense, all conclusions regarding the impact of sensory fidelity will be framed as associational, not causal.
- **Assumption about threshold justification**: The decision cutoff for "success" (collision-free completion) is binary and community-standard. A sensitivity analysis will be performed on the occupancy grid generation threshold (as mandated by FR-008) to ensure robustness, with specific sweep values to be determined in the implementation plan based on preliminary data.