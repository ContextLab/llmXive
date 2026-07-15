# Data Model: llmXive follow-up: extending "LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation"

## 1. Entities

### 1.1 VideoClip
A short-duration video segment from the Kinetics-400 dataset (or UCF101 fallback).
- **Attributes**:
  - `clip_id`: Unique identifier (string).
  - `source`: Original dataset source (string: "kinetics-400" or "ucf101").
  - `duration`: Duration in seconds (float).
  - `frames`: List of frame tensors (float32).
  - `label`: Action label from dataset (string, optional).
  - `has_synthetic_discontinuity`: Boolean (for validation set).

### 1.2 ExperimentRun
A single execution instance of the simulation and evaluation pipeline.
- **Attributes**:
  - `run_id`: Unique identifier (string).
  - `bit_width`: Simulated bit-width (int: 2, 3, 4, 5, 6).
  - `seed`: Random seed (int).
  - `model_params`: Number of parameters in the student model (int).
  - `theoretical_memory_gb`: Calculated memory footprint (float).
  - `runtime_memory_gb`: Measured peak RSS memory (float, for SC-005).
  - `consistency_score`: Mean temporal coherence score (float).
  - `convergence_status`: Status of training (e.g., "converged", "collapsed", "timeout").
  - `noise_kl_divergence`: KL-divergence of quantization emulation noise (float).
  - `timestamp`: Execution timestamp (datetime).

### 1.3 ConsistencyScore
The metric derived from the frozen evaluator.
- **Attributes**:
  - `run_id`: Reference to ExperimentRun (string).
  - `clip_id`: Reference to VideoClip (string).
  - `frame_similarity`: Cosine similarity between consecutive frames (float).
  - `aggregated_score`: Mean similarity for the clip (float).
  - `ground_truth_label`: Boolean (for synthetic validation).

## 2. Data Flow

1. **Ingestion**: `data/loader.py` streams clips from Kinetics-400 (or UCF101).
2. **Simulation**: `simulation/training_loop.py` generates video outputs for each `ExperimentRun`.
3. **Evaluation**: `evaluation/clip_evaluator.py` scores each generated clip.
4. **Aggregation**: `analysis/aggregation.py` compiles results into a master CSV.
5. **Analysis**: `analysis/visualization.py` generates plots and statistical tests.

## 3. Storage

- **Raw Data**: Streamed from HuggingFace (not stored locally).
- **Derived Data**:
  - `data/derived/clips_{seed}_{bit_width}.csv`: List of processed clips.
  - `data/derived/results.csv`: Aggregated experiment results.
  - `data/derived/figures/`: Generated plots.
- **Checkpoints**: Model checkpoints are stored temporarily and deleted after evaluation to save disk space.

## 4. Constraints

- **Memory**: Total memory usage must not exceed a predefined system threshold.
- **Disk**: Total disk usage must not exceed a predefined storage threshold.
- **Time**: Total execution time must not exceed a practical limit suitable for iterative experimentation.
- **Data Integrity**: No raw data modification. All derived data must be checksummed.
