# Data Model: Self-improving LLM: recursive architecture refinement and re‑training

## Overview

This document defines the data structures, schemas, and flow for the recursive refinement pipeline. All data artifacts are versioned and checksummed.

## Core Entities

### 1. ModelCheckpoint
Represents a trained model instance at a specific cycle.
- **cycle_number**: Integer (0, 1, 2, 3)
- **parameter_count**: Integer (total parameters)
- **architecture_modification**: String (JSON or description of the change)
- **training_time**: Float (seconds)
- **flops**: Float (total FLOPs for training)
- **checkpoint_path**: String (relative path to saved weights)

### 2. PerformanceMetric
Represents evaluation results for a specific cycle and benchmark.
- **cycle_number**: Integer
- **benchmark_name**: Enum ["Wikitext-2"]
- **ppl**: Float (Perplexity)
- **p_value_vs_predecessor**: Float (p-value from bootstrap test, null for Cycle 0)
- **sample_size**: Integer (number of samples used)

### 3. RefinementCycle
Aggregates all data for one iteration of the pipeline.
- **cycle_number**: Integer
- **pre_modification_params**: Integer
- **post_modification_params**: Integer
- **training_duration**: Float
- **evaluation_results**: List[PerformanceMetric]
- **success_status**: Boolean (true if training and evaluation completed)
- **failure_reason**: String (if success_status is false)
- **modification_proposal**: String (raw proposal from model)
- **oracle_validation**: Boolean (result of external check)

### 4. Trajectory
Aggregated results for the entire experiment.
- **cycles**: List[RefinementCycle]
- **trend_direction**: Enum ["improving", "declining", "flat", "inconclusive"]
- **cost_effectiveness**: List[Object] (ppl_per_flop, ppl_per_hour)

## Data Flow Diagram (Conceptual)

1.  **Input**: `config.py` (hyperparameters), `data/raw/` (datasets).
2.  **Processing**:
    -   `pipeline/loader.py`: Loads model and datasets.
    -   `pipeline/generator.py`: Generates modification proposal.
    -   `pipeline/validator.py`: Validates proposal.
    -   `pipeline/trainer.py`: Trains model, logs FLOPs/time.
    -   `pipeline/evaluator.py`: Evaluates on benchmarks.
    -   `pipeline/stats.py`: Computes bootstrap p-values and trend direction.
3.  **Output**:
    -   `results/trajectory.json`: Aggregated results.
    -   `results/logs/cycle_N.log`: Detailed logs per cycle.
    -   `data/processed/`: Checksummed dataset subsets.

## Contracts

The following contracts define the expected format of output files.

### `results/trajectory.json` Schema
- **Type**: Object
- **Properties**:
    - `cycles`: Array of `RefinementCycle` objects.
    - `trend_direction`: Object with `slope` (N/A), `trend_direction`.
    - `cost_effectiveness`: Array of objects with `ppl_per_flop`, `ppl_per_hour`.

### `results/logs/cycle_N.log` Schema
- **Type**: JSON Lines (one JSON object per line)
- **Properties**:
    - `timestamp`: ISO 8601 string.
    - `cycle`: Integer.
    - `event`: String (e.g., "proposal", "validation", "training_start", "training_end", "evaluation").
    - `data`: Object (context-specific data).