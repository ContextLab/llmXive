# Data Model: Non-Neural Approximation of VLA Priors

## Overview

This document defines the data schemas and transformation pipelines for the `001-non-neural-vla-approximation` feature. All data artifacts are stored under `data/` and must be checksummed.

## Entity Definitions

### 1. Raw Trajectory (Ingested)
The raw data structure extracted from the HuggingFace parquet source.
*   **Source**: `data/raw/hy_embodied.parquet`
*   **Fields**:
    *   `instruction`: String (Text prompt)
    *   `actions`: List of Floats (Joint angles/EE positions over time)
    *   `task_type`: String (e.g., "grasp", "navigate")
    *   `episode_id`: String (Unique identifier)

### 2. Kinematic Features (Processed)
Derived features used for clustering.
*   **Source**: `data/processed/kinematic_features.feather`
*   **Fields**:
    *   `episode_id`: String (FK to Raw)
    *   `mean_velocity`: Float
    *   `max_acceleration`: Float
    *   `joint_angle_std`: Float
    *   `cluster_id`: Integer (Assigned by K-Means)

### 3. Cluster Model (Trained)
Serialized model for each cluster.
*   **Source**: `data/models/cluster_{id}.pkl`
*   **Fields**:
    *   `cluster_id`: Integer
    *   `model_type`: String ("DecisionTree" or "GMM")
    *   `embedding_dim`: Integer
    *   `hyperparameters`: JSON (Model config)
    *   `centroid_embedding`: List of Floats

### 4. Simulation Result (Evaluation)
Output from the PyBullet execution.
*   **Source**: `data/results/simulation_logs.csv`
*   **Fields**:
    *   `prompt_id`: String
    *   `task_type`: String
    *   `model_used`: String ("NonNeural", "Random", "VLA_Proxy")
    *   `success`: Boolean
    *   `collision_count`: Integer
    *   `execution_time_ms`: Float
    *   `fidelity_score`: Float (0.0 - 1.0)

## Transformation Pipeline

1.  **Ingest**: `01_ingest.py`
    *   Input: HF Parquet URL
    *   Output: `data/raw/hy_embodied.parquet` (Checksummed)
    *   Logic: Validate schema, handle missing values, save raw.

2.  **Feature Engineering**: `02_cluster.py` (Part 1)
    *   Input: `data/raw/hy_embodied.parquet`
    *   Output: `data/processed/kinematic_features.feather`
    *   Logic: Calculate velocity/acceleration, normalize, K-Means.

3.  **Model Training**: `03_train.py`
    *   Input: `data/processed/kinematic_features.feather`, Frozen BERT
    *   Output: `data/models/cluster_{id}.pkl`
    *   Logic: Embed text, split train/test, fit model per cluster.

4.  **Simulation**: `05_simulate.py`
    *   Input: `data/models/*.pkl`, Test Prompts
    *   Output: `data/results/simulation_logs.csv`
    *   Logic: Generate trajectory, run PyBullet, record metrics.

## Data Constraints

*   **Immutability**: Files in `data/raw/` are never modified.
*   **Checksums**: All files in `data/raw/` and `data/results/` must have a corresponding `.sha256` file.
*   **PII**: No personally identifiable information allowed. Text prompts are sanitized if necessary.
