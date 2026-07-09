# Data Model: Astrocyte-Inspired Meta-Learning

## 1. Overview

This document defines the data structures for the Astrocyte Meta-Learning project. It covers the input datasets, the internal state of the training loop, and the output metrics. All data is stored in `data/` (raw) and `results/` (processed).

## 2. Input Data

### 2.1. Datasets
- **Omniglot**: `torchvision.datasets.Omniglot`
  - Structure: `images/` directory with subfolders for each character class.
  - Format: PNG images, 28x28 pixels.
  - Labels: Integers (0 to N_classes).
- **Mini-ImageNet**: `torchvision.datasets.ImageFolder`
  - Structure: `train/`, `val/`, `test/` directories with subfolders for classes.
  - Format: PNG images, 84x84 pixels (resized from 224x224).
  - Labels: Integers (0 to 100).

### 2.2. Configuration (`config.yaml`)
- **Seeds**: List of integers for reproducibility.
- **Hyperparameters**: Learning rate, inner-loop steps, ODE parameters ($\tau, \alpha, \beta, \lambda$).
- **Dataset**: Path to cached data.

## 3. Internal State

### 3.1. Training Episode State
- **Task ID**: Integer identifier for the current task in the TIL sequence.
- **Support Set**: List of (image, label) tuples.
- **Query Set**: List of (image, label) tuples.
- **Model Weights**: Current parameters $\theta$.
- **Astrocyte State**:
  - `Ca_t`: Current calcium concentration (float).
  - `h_t`: Homeostatic factor (float).
  - `history_buffer`: Running average of past task activations. **CRITICAL**: This buffer explicitly excludes the activation signal from Task N-1 (the Stability target) to prevent circular validation. It uses tasks N-2, N-3, etc., or internal loss signals.

### 3.2. Metric Vector
- **Plasticity**: Float (accuracy on current task after $k$ steps).
- **Stability**: Float (accuracy on previous task N-1 after current training). **Note**: This metric is derived from a held-out query set for N-1, which is NOT used in the history buffer for $h_t$.
- **Loss**: Float (MAML loss on query set).

## 4. Output Schema

### 4.1. Results File (`results/episode_{seed}_{task}.json`)
- **Structure**: JSON object containing metrics for a single episode.
- **Fields**:
  - `seed`: Integer.
  - `task_id`: Integer.
  - `plasticity_score`: Float.
  - `stability_score`: Float.
  - `loss`: Float.
  - `h_t`: Float.
  - `Ca_t`: Float.

### 4.2. Aggregated Results (`results/aggregated_{seed}.json`)
- **Structure**: JSON object containing summary statistics for a seed.
- **Fields**:
  - `seed`: Integer.
  - `mean_plasticity`: Float.
  - `mean_stability`: Float.
  - `std_plasticity`: Float.
  - `std_stability`: Float.
  - `total_episodes`: Integer.

### 4.3. Statistical Test Results (`results/stats_test.json`)
- **Structure**: JSON object containing Permutation Test results.
- **Fields**:
  - `test_name`: String ("Permutation Test").
  - `observed_distance`: Float (Euclidean distance between mean vectors).
  - `p_value`: Float.
  - `verdict`: String ("Significant", "Not Significant", "Inconclusive").
  - `reason`: String (if inconclusive, e.g., "insufficient_power").
  - `confidence_interval`: List of floats or null.
  - `power`: Float (estimated).
  - `permutations`: Integer.
  - `baseline_mean`: List [Stability, Plasticity].
  - `astrocyte_mean`: List [Stability, Plasticity].

## 5. Data Flow

1. **Load**: `data_loader.py` fetches Omniglot/Mini-ImageNet from `data/`.
2. **Train**: `train_loop.py` iterates through tasks, updating model weights and astrocyte state. **Crucially, the history buffer for $h_t$ excludes N-1.**
3. **Log**: Metrics are written to `results/` after each episode.
4. **Aggregate**: `stats.py` reads all episode logs, computes mean/std, and runs the Permutation Test.
5. **Report**: Final JSON report is generated.