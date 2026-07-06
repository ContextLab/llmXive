# Data Model: Dream-State Learning: Implementing REM-like Consolidation in Language Models

## Overview

This document defines the data structures, schemas, and flow for the Dream-State Learning experiment. The data model supports the oscillatory training cycle, the generation of pseudo-samples (masked real data), and the statistical evaluation of results.

## Core Entities

### 1. TrainingStep
Represents a single iteration in the training loop.
-   `step_id`: Integer (0 to N).
-   `phase`: Enum ("wake", "dream").
-   `loss`: Float (Cross-Entropy or MLM loss).
-   `gradient_norm`: Float.
-   `timestamp`: ISO 8601 string.
-   `memory_rss_mb`: Integer (Peak RSS at this step).
-   `reconstruction_difficulty`: Float (Average entropy of the masked input tokens, used for Quality Control).

### 2. PseudoSample
Generated during the "dream" phase (now a masked real sample).
-   `original_input`: String (The real text to be reconstructed).
-   `masked_input`: String (Input with tokens replaced by `[MASK]`).
-   `generated_output`: String (Model's reconstruction).
-   `reconstruction_loss`: Float.
-   `entropy_bits`: Float (Average entropy of generated tokens, used for QC).

### 3. EvaluationResult
Result of a single run on a held-out task.
-   `run_id`: UUID (Unique identifier for the seed/run).
-   `seed`: Integer.
-   `dataset`: String (e.g., "GLUE-AX").
-   `accuracy`: Float.
-   `baseline_accuracy`: Float (from the paired baseline run).
-   `effect_size`: Float (Cohen's d).
-   `p_value`: Float (from Wilcoxon signed-rank test).
-   `is_significant`: Boolean.
-   `reconstruction_difficulty_avg`: Float (Average difficulty during training, for QC).

### 4. ExperimentConfig
The configuration for a specific run.
-   `model_name`: String.
-   `wake_dream_ratio`: Integer (4:1).
-   `dream_temperature`: Float.
-   `total_steps`: Integer.
-   `warmup_steps`: Integer (Default 20).
-   `seed`: Integer.

## Data Flow

1.  **Ingestion**: Raw GLUE/SuperGLUE data is downloaded to `data/raw/` and cached.
2.  **Preprocessing**: Data is tokenized and split into `train` (for wake/dream) and `test` (for evaluation).
3.  **Training Loop**:
    -   `TrainingStep` records are appended to a log file (`data/logs/training_log.jsonl`).
    -   `PseudoSample` data is transient (in-memory) but aggregated statistics (avg entropy, reconstruction difficulty) are logged.
4.  **Evaluation**:
    -   Model is loaded from `data/checkpoints/`.
    -   `EvaluationResult` is computed and written to `data/results/experiment_results.json`.
5.  **Analysis**: `EvaluationResult` entries are aggregated to compute the final Wilcoxon test statistics and correlation analysis.

## Storage Schema

### Checkpoints
-   Location: `data/checkpoints/{run_id}/model.pt`
-   Format: PyTorch `.pt` file (state_dict).
-   Metadata: Includes `step_id`, `loss`, and `seed` in the filename or accompanying `meta.json`.

### Logs
-   Location: `data/logs/training_log.jsonl`
-   Format: JSON Lines (one object per line).
-   Schema: Matches `TrainingStep` entity.

### Results
-   Location: `data/results/experiment_results.json`
-   Format: JSON Array.
-   Schema: Array of `EvaluationResult` objects.

## Constraints & Validations

-   **Memory**: `memory_rss_mb` must not exceed 6500 (6.5 GB).
-   **Entropy**: `entropy_bits` for a `PseudoSample` must be > 0.5 (if < 0.5, the sample is discarded).
-   **Consistency**: `total_steps` in `ExperimentConfig` must equal the sum of `wake` and `dream` steps in `TrainingStep` logs.
-   **Reproducibility**: `seed` must be identical for the experimental and baseline runs being compared.
-   **Quality Control**: `reconstruction_difficulty` must be logged for every dream step to enable correlation analysis with final accuracy.
