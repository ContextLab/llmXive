# Data Model: Self-improving LLM: recursive architecture refinement and re‑training

## Overview

This document defines the data structures used to track the state of the recursive refinement pipeline. All data is persisted to `results/` and `data/` directories in JSON/YAML format to ensure reproducibility (Constitution Principle I).

## Core Entities

### 1. ModelCheckpoint

Represents a specific version of the model at a given cycle.

```json
{
  "cycle_number": 1,
  "base_model": "gpt2-124m",
  "modification_type": "add_layer",
  "modification_details": {
    "added_layers": 2,
    "added_params": 12000000
  },
  "pre_modification_params": 124000000,
  "post_modification_params": 136000000,
  "parameter_increase_pct": 9.68,
  "training_time_seconds": 3600,
  "flops_total": 1.2e12,
  "path_to_weights": "data/models/cycle_1_weights.bin",
  "seed": 42
}
```

### 2. PerformanceMetric

Represents the evaluation results for a single benchmark at a specific cycle.

```json
{
  "cycle_number": 1,
  "benchmark_name": "GSM8K",
  "accuracy": 0.234,
  "samples_evaluated": 100,
  "p_value_vs_baseline": 0.042,
  "is_significant": true,
  "bootstrapped_ci_lower": 0.220,
  "bootstrapped_ci_upper": 0.248
}
```

### 3. RefinementCycle

Aggregates all data for a single iteration of the pipeline.

```json
{
  "cycle_number": 1,
  "status": "success",
  "start_time": "2026-06-16T10:00:00Z",
  "end_time": "2026-06-16T11:45:00Z",
  "model_checkpoint": { ... },
  "evaluation_results": [
    { ... }, // PerformanceMetric for GSM8K
    { ... }, // PerformanceMetric for ARC
    { ... }  // PerformanceMetric for ECE
  ],
  "resource_usage": {
    "peak_ram_gb": 6.2,
    "total_flops": 1.2e12
  },
  "modification_proposal": "Add 2 transformer layers...",
  "modification_validation": "valid"
}
```

### 4. TrajectorySummary

The final aggregated output for the 3-cycle experiment (or single cycle if scaling study fails).

```json
{
  "experiment_id": "PROJ-561-001",
  "cycles_completed": 1,
  "trajectory": [
    { "cycle": 0, "gsm8k": 0.150, "arc": 0.300, "ece": 0.450 },
    { "cycle": 1, "gsm8k": 0.160, "arc": 0.310, "ece": 0.440 }
  ],
  "decay_model_fit": {
    "formula": "y = a * e^(-bx) + c",
    "params": { "a": 0.1, "b": 0.5, "c": 0.16 },
    "plateau_cycle": null,
    "degradation_cycle": null
  },
  "trade_off_metrics": {
    "cycle_1": { "perf_per_flop": 1.2e-10, "perf_per_hour": 0.15 }
  },
  "dataset_status": {
    "openwebtext": "loaded",
    "gsm8k": "loaded",
    "arc_challenge": "loaded",
    "wikitext2": "loaded"
  },
  "pipeline_status": "success"
}
```

**Note**: If any dataset fails to load, the `pipeline_status` is set to "failed_data", and the `trajectory` array contains only the baseline (cycle 0) or previous successful cycles. No synthetic data is recorded for any part of the experiment.

## Data Flow

1.  **Input**: `spec.md` (defines constraints), `constitution.md` (defines rules).
2.  **Download**: Datasets loaded to `data/raw/`. Checksums recorded.
    *   **Fail-Fast**: If OpenWebText, GSM8K, ARC, or Wikitext-2 fails to load, terminate immediately.
3.  **Cycle Loop**:
    *   Load `ModelCheckpoint` (or base).
    *   Generate `modification_proposal` (using training loss only).
    *   Validate modification (parameter count).
    *   Train -> Update `ModelCheckpoint`.
    *   Evaluate -> Generate `PerformanceMetric`.
    *   Store `RefinementCycle` in `results/logs/cycle_N.json`.
4.  **Output**: Aggregate all cycles into `results/trajectory.json`.