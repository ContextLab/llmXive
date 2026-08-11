# Data Model: Self-improving LLM: recursive architecture refinement and re‑training

## Overview

This document defines the data structures, schemas, and file formats used throughout the project. All data flows are validated against `contracts/` schemas.

## Entity Definitions

### 1. ModelCheckpoint
Represents a saved state of the model after a cycle.
- `cycle_number`: int (0, 1, 2, 3)
- `parameter_count`: int (total trainable params)
- `architecture_modification`: str (description of change, e.g., "hidden_size + 64")
- `training_time_seconds`: float
- `flops`: float (total FLOPs for the epoch)
- `status`: str ("success", "failed", "early_terminated")

### 2. PerformanceMetric
Represents evaluation results for a specific benchmark.
- `cycle_number`: int
- `benchmark_name`: str ("GSM8K", "ARC-Challenge", "BoolQ")
- `accuracy_or_ECE`: float (accuracy for GSM8K/ARC, ECE for BoolQ)
- `p_value_vs_baseline`: float (or null for Cycle 0)
- `sample_size`: int

### 3. RefinementCycle
Aggregates data for a single iteration.
- `cycle_number`: int
- `pre_modification_params`: int
- `post_modification_params`: int
- `training_duration_seconds`: float
- `evaluation_results`: list[PerformanceMetric]
- `success_status`: str
- `log_file_path`: str

## File Formats

### `results/trajectory.json`
A JSON array containing one object per completed cycle (including failed ones with null metrics).
```json
[
  {
    "cycle_number": 0,
    "parameter_count": 117000000,
    "gsm8k_accuracy": 0.123,
    "arc_accuracy": 0.345,
    "ece_boolq": 0.056,
    "flops": 1.23e15,
    "training_time_seconds": 7200.5
  },
  ...
]
```

### `results/logs/cycle_N.log`
A JSON Lines (`.jsonl`) file where each line is a structured log event.
```json
{"timestamp": "2026-06-26T10:00:00Z", "level": "INFO", "event": "cycle_start", "cycle": 1}
{"timestamp": "2026-06-26T10:05:00Z", "level": "INFO", "event": "proposal_received", "modification": "add_layer"}
{"timestamp": "2026-06-26T10:10:00Z", "level": "INFO", "event": "training_complete", "duration": 3600}
```

### `data/checksums.json`
A JSON object mapping dataset filenames to SHA256 hashes.
```json
{
  "openwebtext/train-00000-of-00080.parquet": "abc123...",
  "gsm8k/test-00000-of-00001.parquet": "def456..."
}
```

## Data Flow Diagram (Conceptual)

1.  **Ingest**: `utils/data_loader.py` -> Stream -> `data/processed/` (sampled)
2.  **Process**: `pipeline/trainer.py` -> `results/logs/cycle_N.log`
3.  **Evaluate**: `pipeline/evaluator.py` -> `results/trajectory.json`
4.  **Validate**: `contracts/` schemas verify all outputs before finalization.
