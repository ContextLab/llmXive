# Research: Robotic AI Sensory Fidelity Ablation Study

## Research Question
How does sensory representation fidelity (Raw RGB vs. Downsampled Depth vs. 2D Occupancy Grids) influence Reinforcement Learning sample efficiency and generalization in autonomous navigation, given CPU-only constraints?

## Dataset Strategy

The study relies on a simulated environment to generate ground-truth sensor data, as no single pre-existing dataset provides the synchronized RGB/Depth/LiDAR streams with randomized obstacle densities required for this specific ablation.

**Primary Source**: **CARLA Simulator** (Open Source Driving Simulator).
- **Role**: Generates the "ground truth" environment (map, obstacles, vehicle dynamics) and simulates sensor outputs (RGB, Depth, LiDAR) with configurable noise.
- **Justification**: CARLA allows for the precise control of obstacle density and sensor parameters required by User Story 1 (randomized seeds) and User Story 2 (consistent ground truth for ablation). It is the standard for autonomous navigation research.
- **Verification**: While CARLA itself is a simulator, the plan references the **KITTI Vision Benchmark Suite** for validating the coordinate transformation and calibration logic (FR-009) against real-world sensor data distributions where applicable.
- **Note on Verified Datasets**: The provided "Verified datasets" list contains MobileNetV2 weights and DQN training logs for unrelated tasks (mangoleaf, Pong, etc.). These are **not** used as the primary data source for the navigation simulation but may be referenced for pre-training weights if applicable (though the plan favors training from scratch to ensure fair ablation). No fabricated URLs are used.

**Data Generation Pipeline**:
1.  **Simulation**: Run CARLA with randomized obstacle placement (N=30 seeds). **Crucially, each seed represents a distinct environment realization (different map layout and obstacle density) to ensure statistical independence and avoid pseudoreplication.**
2.  **Sensor Capture**: Collect synchronized RGB, Depth, and LiDAR point clouds.
3.  **Preprocessing**: Apply the pipeline in `generate_modalities.py` to create:
    *   `Raw_RGB`: 84x84 normalized tensors.
    *   `Depth_Map`: Downsampled depth values.
    *   `Occupancy_Grid`: 2D binary grids (FR-001).
4.  **Calibration**: Validate extrinsic parameters using KITTI-derived transformation matrices (FR-009) in Phase 0.1.

## Methodology

### Experimental Design
- **Independent Variable**: Sensory Modality (3 levels: Raw RGB, Depth, Occupancy Grid).
- **Dependent Variables**:
 * Sample Efficiency: **Censored** "Steps to Best Performance" (or steps to [deferred] success if reached).
    *   Generalization: Success rate in novel, high-obstacle-density scenarios (SC-002).
    *   Inference Latency: ms per step on CPU (SC-002).
- **Control Variables**: Random seeds (distinct environment realizations), hyperparameters, environment physics, obstacle distribution logic.
- **Baselines**:
    1.  **Classical**: Pure Pursuit / Dijkstra (Theoretical ceiling).
    2.  **Stochastic**: Random Policy (Theoretical floor).

### Model Architecture
- **Agent**: Deep Q-Network (DQN).
- **Backbone**: MobileNetV2 (Pruned to <1M parameters to ensure CPU tractability).
- **Head**: Fully connected layers for Q-value estimation.
- **Optimization**: SGD or Adam (CPU-optimized).
- **Constraints**: No GPU, no quantization, default float32 precision.

### Statistical Analysis Plan
1.  **Data Collection**: Aggregate learning curves (success rate vs. steps) for all 30 seeds × 3 modalities.
2. **Censored Data Handling**: For runs that do not reach [deferred] success within the time limit:
    *   Define "Time-to-Convergence" as "Steps to Best Observed Performance".
    *   Flag these runs as `censored = true` in the data model.
    *   If >50% of runs are censored, consider survival analysis; otherwise, use the capped value in parametric/non-parametric tests.
3. **AUC Calculation**: Compute Area Under the Curve (AUC) using the trapezoidal rule over a **fixed step range (0 to [deferred] steps)** to ensure comparability across all runs, regardless of convergence status.
4.  **Hypothesis Testing**:
    *   **Primary Test**: **Welch's ANOVA** (robust to unequal variances) OR **Kruskal-Wallis** (if distributions are heavily skewed).
    *   **Post-hoc**: Games-Howell (for Welch's) or Dunn's test with Bonferroni correction (for Kruskal-Wallis).
    *   **Note**: The Shapiro-Wilk pre-test is **removed** to avoid inflating Type I error rates. The robust method is pre-specified.
5.  **Significance Threshold**: α = 0.05.
6.  **Framing**: All results reported as **associational** (FR-007), acknowledging the simulation context.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Addressed via Games-Howell or Dunn's test with correction to control Family-Wise Error Rate (FWER).
- **Sample Size/Power**: N=30 seeds per modality is chosen to provide sufficient power to detect a moderate effect size (Cohen's f ≥ 0.25) as per Assumption. **However, if the actual effect size is small (f < 0.15) or variance is high, the study may be underpowered.**
    *   **Contingency**: If the study is underpowered (p > 0.05), the report will explicitly state the observed effect size (Cohen's d) and 95% confidence intervals, rather than claiming "no effect".
- **Causal Inference**: The study is observational within a controlled simulation. Claims are limited to associations between input fidelity and learning dynamics. No causal claims regarding real-world performance are made.
- **Measurement Validity**: MobileNetV2 is a validated architecture for image classification; its adaptation to DQN is standard in RL literature. Occupancy grid generation is validated against ground-truth depth maps.
- **Metric Independence (Critical)**: The "success" metric (collision detection) is derived **exclusively from the simulated physics engine state** (ground truth), not from the processed sensor data (e.g., the occupancy grid). This prevents a tautological validation where the grid modality would appear "perfect" by definition.
- **Construct Validity (Generalization)**: Generalization is validated against *simulated* novel scenarios (high-density obstacles) generated within the same physics engine. While KITTI is used for geometric calibration, it is **not** used to validate generalization performance, acknowledging the simulation-to-reality gap as a limitation.

## Compute Feasibility Rationale

- **Hardware**: Multi-core CPU, sufficient RAM.
- **Strategy**:
    *   **Model**: MobileNetV2 is lightweight. Pruning ensures <1M parameters, reducing memory footprint and compute per step.
    *   **Data**: Simulation runs in real-time or faster; data is streamed, not fully loaded into RAM.
    *   **Time Limit**: Hard 6-hour cap (FR-003) ensures the job terminates gracefully.
    *   **Libraries**: `torch` (CPU build), `scikit-learn`, `numpy` are all CPU-native and fit within the 7GB RAM limit.
- **Risk Mitigation**:
    *   **Memory Pressure**: Exception handling in `sim_wrapper.py` catches crashes and logs state (Edge Case 1).
    *   **Timeout**: A timer thread in `train_and_analyze.py` forces checkpointing and exit at 6h (Edge Case 3).