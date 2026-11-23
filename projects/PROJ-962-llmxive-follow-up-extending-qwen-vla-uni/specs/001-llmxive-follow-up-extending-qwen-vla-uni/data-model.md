# Data Model: Non-Neural Approximation of VLA Priors

## Overview

This document defines the data structures, schemas, and flow for the `001-non-neural-vla-approximation` feature. It ensures that all data artifacts are validated against strict contracts before being used in training or evaluation.

## Data Flow

1.  **Raw Ingestion**: `file-000.parquet` (HuggingFace) $\rightarrow$ `data/raw/vla_episodes.parquet`
2.  **Feature Extraction**: Raw actions $\rightarrow$ `data/processed/kinematic_features.csv` (Statistical summaries: Mean/Max/Variance of velocity, acceleration, angles)
3.  **Clustering**: Features $\rightarrow$ `data/processed/cluster_assignments.csv` (Cluster ID, Silhouette Score)
4.  **Embedding Generation**: Text $\rightarrow$ `data/processed/bert_embeddings.npy`
5.  **Model Training**: (Embeddings, Cluster Actions) $\rightarrow$ `data/models/cluster_*.pkl`
6.  **Simulation Output**: Trajectories $\rightarrow$ `data/results/simulation_results.csv`

## Schema Definitions

### 1. Raw Dataset Schema (`contracts/dataset.schema.yaml`)
Defines the expected structure of the ingested Qwen-VLA parquet file.

### 2. Trajectory Schema (`contracts/trajectory.schema.yaml`)
Defines the structure of a single robot trajectory (time-series of joint states).

### 3. Simulation Result Schema (`contracts/simulation_result.schema.yaml`)
Defines the output of the PyBullet evaluation.

### 4. Model Schema (`contracts/model.schema.yaml`)
Defines the structure of the serialized per-cluster model artifacts (Decision Tree or GMM).

## Entity Definitions

- **Trajectory**: A list of time steps, where each step is a dictionary of joint angles and end-effector position.
- **Cluster**: A grouping of trajectories sharing similar kinematic profiles (based on statistical features).
- **Prompt**: A text string instruction.
- **Simulation Result**: A record of a single execution attempt.
