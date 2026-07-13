# Data Model: llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

## Overview

This document defines the data structures used for the Virtual Tactile Estimator, the Adaptive Reward Scheduler, and the simulation results. The data model supports the CPU-only, zero-shot adaptation workflow.

## Entities

### 1. `SimulationStep`
Represents a single timestep in the physics simulation.
- **Purpose**: Captures the raw inputs required for the stiffness estimator.
- **Fields**:
  - `timestep_id`: `int` (Unique ID for the step).
  - `hand_joint_torques`: `List[float]` (Torque values for all hand joints).
  - `object_velocity`: `float` (Scalar magnitude of object linear velocity).
  - `object_position`: `List[float]` (x, y, z).
  - `object_mass`: `float` (Mass of the object, used for normalization).
  - `friction_coeff`: `float` (Ground truth friction for the current object).
  - `success`: `bool` (Whether the goal was reached at this step).

### 2. `StiffnessEstimate`
The output of the `VirtualTactileEstimator`.
- **Purpose**: The computed proxy $k_{est}$.
- **Fields**:
  - `timestep_id`: `int`
  - `k_est`: `float` (The computed stiffness proxy, clamped to [0.01, 100.0]).
  - `delta_tau_hand`: `float` (Filtered torque derivative).
  - `delta_v_object`: `float` (Velocity derivative).
  - `is_stiction`: `bool` (True if $|\Delta v| < \epsilon$).
  - `mass_normalized`: `bool` (True if mass normalization was applied).

### 3. `RewardConfig`
The dynamic reward weights for the PICA policy.
- **Purpose**: The output of the `AdaptiveRewardScheduler`.
- **Fields**:
  - `r_detach`: `float` (Detachment penalty weight).
  - `r_contact`: `float` (Contact maintenance weight).
  - `r_goal`: `float` (Goal achievement weight, constant).
  - `adjustment_factor`: `float` (The multiplier applied based on $k_{est}$ via sigmoid).
  - `transition_smoothness`: `float` (The $\alpha$ parameter used in the sigmoid).

### 4. `ExperimentResult`
Aggregated results for a single object evaluation.
- **Purpose**: Stores the outcome of the zero-shot test.
- **Fields**:
  - `object_id`: `str` (Unique ID for the novel object).
  - `friction_coeff`: `float` (Ground truth friction).
  - `policy_type`: `str` ("static" or "adaptive").
  - `mean_success_rate`: `float` (Average success rate across 50 trials).
  - `std_success_rate`: `float` (Standard deviation across 50 trials).
  - `avg_k_est`: `float` (Average stiffness estimate during successful runs).
  - `total_trials`: `int` (Number of trials executed, e.g., 50).

## Data Flow

1.  **Generation**: `generator.py` creates 30 objects, saving metadata to `data/generated/object_manifest.jsonl`.
2.  **Simulation Loop**:
    - Load object -> Initialize PyBullet.
    - For each of multiple trials:
      - Read `hand_joint_torques`, `object_velocity`, `object_mass`.
      - Compute `StiffnessEstimate` (apply filter, epsilon, clamp, mass normalization).
      - Compute `RewardConfig` based on `StiffnessEstimate` (sigmoid transition).
      - Execute policy step.
    - Record `ExperimentResult` (aggregated over 50 trials).
3.  **Analysis**: `analysis.py` aggregates `ExperimentResult` files and performs the paired t-test.

## Storage Format

- **Raw Data**: `data/raw/dragmesh_manifest.jsonl` (Downloaded from HuggingFace).
- **Generated Objects**: `data/generated/object_{id}.json` (Geometry + friction params + mass).
- **Logs**: `data/logs/{object_id}_{policy_type}.jsonl` (Per-step `SimulationStep` and `StiffnessEstimate`).
- **Results**: `data/results/experiment_summary.csv` (Aggregated `ExperimentResult`).