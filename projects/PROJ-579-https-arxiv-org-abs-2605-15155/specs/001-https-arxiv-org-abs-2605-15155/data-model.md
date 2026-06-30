# Data Model: SDAR Reproduction

## Overview

This document defines the data structures used in the SDAR reproduction pipeline. Since the project focuses on code execution and artifact generation rather than data processing, the data model is primarily concerned with:
1.  **Configuration**: Parameters controlling the training and evaluation runs.
2.  **Logs**: Structured outputs recording loss values, step counts, success rates, and **mechanism activation**.
3.  **Checkpoints**: Serialized model states.
4.  **Health Checks**: Outputs from the Phase 0 sanity check.
5.  **Environment State**: Internal state of the ALFWorld environment (handled by the library, not explicitly modeled here).

## Configuration Schema

The configuration for the reproduction run is defined by a set of hardcoded parameters to ensure reproducibility and CI feasibility.

| Parameter | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `num_steps` | `int` | `10` | Number of training steps to execute. |
| `batch_size` | `int` | `1` | Batch size for training. |
| `env` | `str` | `"alfworld"` | Target environment name. |
| `device` | `str` | `"cpu"` | Target device (CPU-only). |
| `num_tasks` | `int` | `5` | Number of evaluation tasks. |
| `task_timeout` | `int` | `60` | Maximum seconds per task. |
| `output_dir` | `str` | `"outputs/"` | Directory for logs and checkpoints. |

## Log Schema

Training and evaluation logs are stored in JSON format for easy parsing.

### Ray Health Check Log (`ray_health.json`)

```json
{
  "run_id": "string",
  "timestamp": "ISO8601",
  "status": "success",
  "details": {
    "ray_version": "string",
    "cpu_count": 2,
    "gpu_count": 0,
    "message": "Ray cluster healthy"
  }
}
```

### Training Log (`train_log.json`)

```json
{
  "run_id": "string",
  "start_time": "ISO8601",
  "end_time": "ISO8601",
  "config": {
    "num_steps": 10,
    "batch_size": 1,
    "device": "cpu"
  },
  "steps": [
    {
      "step": 0,
      "sdar_gate_loss": 0.123,
      "rl_loss": 0.456,
      "total_loss": 0.579,
      "gate_activation": true,
      "timestamp": "ISO8601"
    }
  ],
  "summary": {
    "final_avg_sdar_gate_loss": 0.123,
    "final_avg_rl_loss": 0.456,
    "gate_activation_rate": 0.8,
    "status": "completed"
  }
}
```

### Evaluation Log (`eval_log.json`)

```json
{
  "run_id": "string",
  "start_time": "ISO8601",
  "end_time": "ISO8601",
  "config": {
    "num_tasks": 5,
    "task_timeout": 60
  },
  "tasks": [
    {
      "task_id": 0,
      "task_type": "pick_and_place",
      "status": "success",
      "steps_taken": 12,
      "reward": 1.0,
      "error_message": null
    },
    {
      "task_id": 1,
      "task_type": "navigate",
      "status": "timeout",
      "steps_taken": 60,
      "reward": 0.0,
      "error_message": "Max steps exceeded"
    }
  ],
  "summary": {
    "total_tasks": 5,
    "successful_tasks": 3,
    "failed_tasks": 2,
    "success_rate": 0.6,
    "avg_steps": 25.0
  }
}
```

## Checkpoint Schema

Model checkpoints are serialized PyTorch states (`.pt` or `.safetensors`). The structure is internal to the model and not strictly defined here, but the file naming convention is:
- `step_{N}.pt` where `N` is the step number (e.g., `step_5.pt`).

## File Structure

```text
outputs/
├── health/
│   └── ray_health.json   # Ray sanity check output (Phase 0)
├── logs/
│   ├── train_log.json    # Training log (Phase 1)
│   └── eval_log.json     # Evaluation log (Phase 2)
└── checkpoints/
    └── step_5.pt         # Model checkpoint
```