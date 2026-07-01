# Data Model: OPID: On-Policy Skill Distillation for Agentic Reinforcement Learning

## Overview

This document defines the data structures used during the OPID training and evaluation process. The model is designed to be lightweight, serializable, and compatible with CPU-only storage constraints.

## Core Entities

### 1. Trajectory Step
Represents a single interaction step in the ALFWorld environment.

```yaml
type: object
properties:
  step_id:
    type: integer
    description: "Unique identifier for the step within the episode."
  state:
    type: string
    description: "Text-based state description from the environment."
  action:
    type: string
    description: "The action taken by the agent."
  reward:
    type: number
    description: "Scalar reward received at this step."
  done:
    type: boolean
    description: "Whether the episode terminated."
  skill_type:
    type: string
    enum: ["episode", "step"]
    description: "Type of skill supervision applied (critical-first routing result)."
  log_prob_shift:
    type: number
    description: "Difference between current policy log-prob and skill policy log-prob."
  outcome_advantage:
    type: number
    description: "Advantage computed from the outcome reward."
  distillation_advantage:
    type: number
    description: "Advantage computed from the skill distillation signal."
  total_advantage:
    type: number
    description: "Weighted sum of outcome and distillation advantages."
required:
  - step_id
  - state
  - action
  - reward
  - done
  - skill_type
  - log_prob_shift
  - outcome_advantage
  - distillation_advantage
  - total_advantage
```

### 2. Episode Summary
Aggregated metrics for a completed episode.

```yaml
type: object
properties:
  episode_id:
    type: integer
    description: "Unique episode identifier."
  task_name:
    type: string
    description: "Name of the ALFWorld task (e.g., 'pick_and_place').".
  success:
    type: boolean
    description: "Whether the task was completed successfully."
  total_steps:
    type: integer
    description: "Number of steps taken."
  total_reward:
    type: number
    description: "Sum of rewards in the episode."
  skill_distribution:
    type: object
    properties:
      episode_skills:
        type: integer
      step_skills:
        type: integer
    description: "Count of steps using each skill type."
required:
  - episode_id
  - task_name
  - success
  - total_steps
  - total_reward
  - skill_distribution
```

### 3. Training Metrics
Aggregated metrics per training step (logged to `opid_metrics.csv`).

```yaml
type: object
properties:
  global_step:
    type: integer
    description: "Global optimization step count."
  loss:
    type: number
    description: "Total policy loss."
  learning_rate:
    type: number
    description: "Current learning rate."
  avg_log_prob_shift:
    type: number
    description: "Mean log_prob_shift across the batch."
  avg_outcome_advantage:
    type: number
    description: "Mean outcome advantage."
  avg_distillation_advantage:
    type: number
    description: "Mean distillation advantage."
  memory_usage_mb:
    type: number
    description: "Approximate RAM usage in MB."
required:
  - global_step
  - loss
  - learning_rate
  - avg_log_prob_shift
  - avg_outcome_advantage
  - avg_distillation_advantage
  - memory_usage_mb
```

## Data Flow

1.  **Generation**: `training.py` (StrictOnPolicyGenerator) generates `TrajectoryStep` objects in the ALFWorld environment.
2.  **Routing**: The `critical_first_routing` module assigns `skill_type` and calculates `log_prob_shift`.
3.  **Advantage Computation**: `outcome_advantage` and `distillation_advantage` are calculated.
4.  **Update & Discard**: A batch is sampled from the current trajectories to compute gradients. **Immediately after the gradient update, all trajectories from this batch are discarded.** No data is retained for future steps to preserve on-policy assumptions.
5.  **Logging**: `TrainingMetrics` are written to `opid_metrics.csv` every 10 steps.
6.  **Evaluation**: `EpisodeSummary` objects are generated after every 5 tasks and saved to `eval_results.json`.