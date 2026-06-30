# Data Model: DragMesh-2 Reproduction

## Overview

This document defines the data structures used for configuration, simulation state, evaluation metrics, and the specific "work-energy" traces required for validation. All data is stored locally as JSON, YAML, or CSV files.

## Configuration Schema

The training and evaluation configurations are stored in YAML files.

**File**: `configs/train_config_gla_pica.yaml` (Reference)
**Structure**:
```yaml
agent:
  type: "PICA"
  hidden_sizes: [256, 256]
  learning_rate: 0.0003
  gamma: 0.99
  gae_lambda: 0.95
  batch_size: 64
  epochs: 10  # Reduced for CI
  total_timesteps: 50000  # Reduced for CI

env:
  object_name: "drawer_01"  # Single object
  damping_range: [0.1, 10.0]  # For robustness test (Domain Randomization)
  max_steps: 500
  physics_engine: "mujoco"
  cpu_only: true

logging:
  work_energy_trace: true
  checkpoint_interval_seconds: 300
```

## Simulation State & Logs

### Interaction Episode Log
Stores the trajectory of a single episode.
**File**: `logs/episodes/{episode_id}.json`
**Schema**:
- `episode_id`: string (UUID)
- `start_time`: string (ISO8601)
- `damping_value`: float
- `success`: boolean
- `steps`: list of step objects
  - `t`: float
  - `state`: object (position, velocity of hand and object)
  - `action`: array (float)
  - `reward`: float
  - `forces`: object (normal, friction, gravity, total)
  - `reset_reason`: string (optional, if reset occurred)

### Work-Energy Trace
Specific log for the Feynman reviewer's request.
**File**: `logs/work_energy/{episode_id}.csv`
**Columns**:
- `t`: float (timestamp)
- `F_normal_mag`: float (magnitude of normal force)
- `F_friction_mag`: float (magnitude of friction force)
- `F_gravity_mag`: float (magnitude of gravity force)
- `v_finger`: string (JSON array of x,y,z velocity)
- `v_object`: string (JSON array of x,y,z velocity)
- `damping_torque`: float (joint damping torque)
- `work_finger`: float (cumulative work done by finger)
- `delta_ke`: float (change in kinetic energy since last step)
- `delta_pe`: float (change in potential energy since last step)
- `work_dissipation`: float (work lost to friction and damping)
- `energy_balance_error`: float (work_finger - (delta_ke + delta_pe + work_dissipation))

## Evaluation Results

### Robustness Summary
**File**: `results/robustness_summary.csv`
**Columns**:
- `damping_value`: float
- `method`: string ("PICA" or "Baseline")
- `success_rate`: float (0.0 - 1.0)
- `mean_reward`: float
- `std_reward`: float
- `n_episodes`: int
- `ci_lower`: float ([deferred] Wilson score lower bound)
- `ci_upper`: float ([deferred] Wilson score upper bound)

### Artifact Manifest
**File**: `results/manifest.json`
**Structure**:
- `artifacts`: list of objects
  - `type`: string ("checkpoint", "log", "plot", "trace")
  - `path`: string (relative path)
  - `checksum`: string (SHA256)

## Contracts (Schemas)

The following schemas are defined in the `contracts/` directory to ensure data integrity.