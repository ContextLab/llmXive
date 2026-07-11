# Feature Specification: Robotic AI Sensory Fidelity Ablation Study

**Feature Branch**: `001-sensory-fidelity-ablation`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "Investigation into how sensory representation fidelity (raw pixels vs. occupancy grids) influences RL sample efficiency and generalization in autonomous navigation, constrained to CPU-only execution."

## User Scenarios & Testing

### User Story 1 - Baseline Environment & Classical Planner Execution (Priority: P1)

The system MUST establish a reproducible simulation environment and execute a classical non-learning baseline (Pure Pursuit/Dijkstra) to define the performance ceiling for navigation tasks. This is the foundation; without a known "good" path and collision rate, RL performance cannot be evaluated.

**Why this priority**: This is the control condition. If the classical planner fails to navigate the test track or the environment setup is unstable, no RL results are meaningful. It validates the simulation wrapper and sensor noise injection.

**Independent Test**: Can be fully tested by running the `run_baseline.py` script, verifying that the vehicle completes the course without collision, and logging the path length and inference latency.

**Acceptance Scenarios**:

1. **Given** a configured CARLA simulation environment with randomized obstacle density, **When** the Pure Pursuit controller is executed, **Then** the vehicle completes the course with a success rate ≥ 95% and logs path optimality ratio ≤ 1.1.
2. **Given** the same environment, **When** the Dijkstra planner is executed, **Then** it generates a collision-free path with the shortest possible length (optimality ratio = 1.0) within 500ms.

---

### User Story 2 - Sensory Modality Data Pipeline & Preprocessing (Priority: P2)

The system MUST implement a data pipeline that ingests raw sensor data (RGB, Depth, LiDAR) and transforms them into the three distinct input modalities: (1) Raw RGB images, (2) Downsampled depth maps, and (3) 2D occupancy grids. This enables the ablation study by ensuring the only variable changing is the input representation.

**Why this priority**: This is the core experimental variable. Without consistent, correct generation of these three modalities from the same ground truth, the comparison of sample efficiency is invalid.

**Independent Test**: Can be fully tested by running the `generate_modalities.py` script on a fixed set of 100 frames, verifying that the output shapes match specifications (e.g., occupancy grid is 64x64 binary matrix), and that the occupancy grid correctly represents obstacles present in the raw depth map.

**Acceptance Scenarios**:

1. **Given** a raw LiDAR point cloud and camera image pair, **When** the preprocessing pipeline runs, **Then** it outputs a multi-dimensional occupancy grid where occupied cells correspond to obstacles within the vehicle's 10m radius, with no false positives in free space.
2. **Given** a raw RGB image, **When** the pipeline processes it, **Then** it outputs a normalized tensor of shape (C, 84, 84) suitable for the MobileNetV2 backbone, where C represents the number of input channels., preserving aspect ratio via center-cropping.

---

### User Story 3 - DRL Training & Statistical Analysis (Priority: P3)

The system MUST train lightweight DQN agents (MobileNetV backbone) for each sensory modality under a 6-hour CPU limit, then perform statistical analysis (ANOVA + Tukey's HSD) to determine if differences in sample efficiency and success rates are significant.

**Why this priority**: This delivers the research answer. It synthesizes the data from US-1 and US-2 into a conclusion about the "sweet spot" of information density.

**Independent Test**: Can be fully tested by executing `train_and_analyze.py`, which must complete within 6 hours on a 2-core runner, produce a CSV of training curves, and output a JSON report stating whether the difference between "Raw RGB" and "Occupancy Grid" success rates is statistically significant (p < 0.05).

**Acceptance Scenarios**:

1. **Given** the three sensory modalities and a 2-core CPU environment, **When** the DQN agent trains for [deferred] episodes, **Then** the total wall-clock time does not exceed a practical threshold for routine analysis, and peak RAM usage remains below 7 GB.
2. **Given** the final success rates for all three modalities, **When** the statistical analysis runs, **Then** it reports a p-value for the ANOVA test and, if significant, the specific pairwise differences from Tukey's HSD, explicitly labeling findings as associational.

---

### Edge Cases

- **What happens when** the simulation crashes due to memory pressure during high-obstacle-density curriculum steps? The system MUST catch the exception, log the current episode count, and attempt to resume from the last checkpoint rather than failing the entire job.
- **How does the system handle** a scenario where the occupancy grid generation fails for a specific frame (e.g., LiDAR dropout)? The system MUST substitute a "safe" empty grid for that single frame and log the event, ensuring the training loop does not break, but the episode is marked as "noisy" for later exclusion if necessary.
- **What happens when** the CPU runner cannot complete [deferred] episodes in 6 hours? The system MUST stop training at the 6-hour mark, record the current step count, and proceed to evaluation with the partially trained model, clearly marking the result as "time-limited" in the final report.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate three distinct input modalities (Raw RGB, Downsampled Depth, 2D Occupancy Grid) from the same ground-truth sensor data to enable ablation, ensuring spatial alignment across modalities (See US-2).
- **FR-002**: System MUST implement a lightweight DQN agent using a MobileNetV2 backbone pruned to <1M parameters to ensure CPU tractability, avoiding any CUDA-dependent operations (See US-3).
- **FR-003**: System MUST enforce a hard 6-hour wall-clock time limit on the training process, stopping execution and saving the checkpoint if the limit is reached (See US-3).
- **FR-004**: System MUST implement a classical baseline (Pure Pursuit/Dijkstra) that operates on the same simulated environment and sensor noise profiles as the RL agents to provide a performance ceiling (See US-1).
- **FR-005**: System MUST perform a one-way ANOVA followed by Tukey's HSD post-hoc test on the final success rates and inference latencies across the three modalities to determine statistical significance (See US-3).
- **FR-006**: System MUST log peak RAM usage and CPU utilization at regular intervals during training to verify adherence to the 7 GB RAM and 2-core constraints (See US-3).
- **FR-007**: System MUST frame all comparative findings as associational relationships between sensory fidelity and learning dynamics, explicitly avoiding causal language unless randomization is proven (See US-3).

### Key Entities

- **SensorModality**: An enumeration of the input types (RGB, Depth, OccupancyGrid) with associated preprocessing parameters.
- **TrainingRun**: A record of a specific DQN training session, containing hyperparameters, total steps, wall-clock time, and peak resource usage.
- **NavigationResult**: A record of a single episode outcome, including success (boolean), path length, collision count, and inference latency.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: Sample efficiency (episodes to reach a target success rate) is measured across the three sensory modalities to determine the "sweet spot" of information density (See FR-002, US-3).
- **SC-002**: Inference latency (ms per step) is measured on the CPU-only runner for each modality to verify embedded feasibility, compared against the 6-hour training constraint (See FR-003, US-3).
- **SC-003**: Statistical significance of performance differences is measured via p-values from Tukey's HSD tests, ensuring findings are not due to random variance (See FR-005, US-3).
- **SC-004**: Path optimality ratio (agent path length vs. shortest path) is measured against the classical baseline to assess navigation quality (See FR-004, US-1).
- **SC-005**: Resource compliance is measured by verifying peak RAM usage remains below 7 GB and total training time does not exceed 6 hours (See FR-003, FR-006).

## Assumptions

- **Assumption about data source**: The KITTI Vision Benchmark Suite and CARLA simulator provide sufficient ground-truth data to generate accurate occupancy grids and depth maps without requiring external LiDAR calibration data.
- **Assumption about computational limits**: A 2-core CPU runner with 7 GB RAM is sufficient to train a pruned MobileNetV2 DQN (under 1M parameters) for a representative number of training episodes. if the dataset is sampled appropriately (e.g., at a standard resolution) and no GPU-specific libraries (like `bitsandbytes`) are invoked.
- **Assumption about methodology**: The relationship between sensory fidelity and sample efficiency is non-linear and can be detected via one-way ANOVA with a a large sample size of episodes per modality, assuming the effect size is moderate (Cohen's f ≥ 0.25).
- **Assumption about statistical framing**: Since the study uses simulation with randomized obstacle generation but no random assignment to "treatment" groups in a real-world sense, all conclusions regarding the impact of sensory fidelity will be framed as associational, not causal.
- **Assumption about threshold justification**: The decision cutoff for "success" (collision-free completion) is binary and community-standard; however, the sensitivity of the occupancy grid generation threshold (e.g., point density required to mark a cell as occupied) will be swept over {0.1, 0.5, 0.9} to ensure robustness, as no single standard exists for this specific synthetic pipeline.
