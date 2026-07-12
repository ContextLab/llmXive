# Data Model: Robotic AI Sensory Fidelity Ablation Study

## Overview

This document defines the data structures, schemas, and transformations used in the ablation study. All data is versioned and checksummed.

## Key Entities

### 1. SensorModality
Enumeration of input types.
- **Values**: `RGB`, `DEPTH`, `OCCUPANCY_GRID`
- **Parameters**:
    - `RGB`: Shape (3, 84, 84), dtype float32, range [0, 1].
    - `DEPTH`: Shape (1, 84, 84), dtype float32, range [0, max_distance].
    - `OCCUPANCY_GRID`: Shape (1, 84, 84), dtype bool/int8, binary (0=free, 1=occupied).

### 2. TrainingRun
Record of a single DQN training session.
- **Fields**:
    - `run_id`: UUID.
    - `modality`: SensorModality.
    - `seed`: int.
    - `hyperparameters`: dict (lr, gamma, epsilon, etc.).
    - `total_steps`: int.
    - `wall_clock_time`: float (seconds).
    - `peak_ram_gb`: float.
    - `checkpoint_path`: str (relative).
    - `status`: "completed" | "time_limited" | "crashed".

### 3. NavigationResult
Record of a single episode outcome.
- **Fields**:
    - `episode_id`: int.
    - `run_id`: UUID (foreign key to TrainingRun).
    - `success`: bool.
    - `path_length`: float (meters).
    - `collision_count`: int.
    - `inference_latency_ms`: float.
    - `optimal_path_length`: float (from Dijkstra baseline).
    - `path_optimality_ratio`: float (agent path / optimal path).

### 4. LearningCurve
Time-series record of performance.
- **Fields**:
    - `run_id`: UUID.
    - `step`: int.
    - `success_rate`: float (rolling window).
    - `reward`: float.
    - `epsilon`: float.
    - `is_converged`: bool (True if success_rate >= 0.9 sustained over 10 episodes).
    - `steps_to_best`: int (Steps at which max success_rate was observed, used for censored data).

## Data Flow

1.  **Input**: Raw sensor data from CARLA (simulated).
2.  **Transformation**: `generate_modalities.py` converts raw data to `SensorModality` tensors.
    - *Validation*: Check shapes and value ranges.
3.  **Processing**: `dqn_agent.py` consumes tensors and updates `TrainingRun` state.
4.  **Output**: `NavigationResult` and `LearningCurve` records written to CSV/JSON.
5.  **Analysis**: `stats.py` aggregates `LearningCurve` data to compute AUC (over fixed range) and handle censored `steps_to_best`.

## Data Hygiene

- **Checksums**: All generated data files in `data/` and `results/` are checksummed (SHA-256).
- **Immutability**: Raw simulated data is never modified. Derived modalities are written to new files.
- **PII**: No PII involved (simulated environment).