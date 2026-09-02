# Data Model: llmXive follow-up: extending "DOPD: Dual On-policy Distillation"

## Overview

This document defines the data structures for the discrete MDP simulation, training logs, and statistical analysis results. All data is generated procedurally; no external datasets are used.

## Entity Definitions

### 1. MDP Transition Record
Represents a single step in the environment.
- **`state_id`**: Integer, unique identifier for the step.
- **`seed`**: Integer, the random seed for this episode.
- **`full_state_vector`**: List of integers (grid encoding).
- **`student_observation`**: List of integers (observable grid only).
- **`privileged_variable`**: Integer or String (hidden state $H$, e.g., "safe_door_A").
- **`action_space`**: Integer (size of action space).
- **`reward`**: Float (immediate reward).
- **`next_state_vector`**: List of integers.
- **`transition_function`**: String (e.g., "action_2").
- **`teacher_action`**: Integer (optimal action given $H$).
- **`student_action`**: Integer (action taken by Student).
- **`teacher_advantage_gap`**: Float (computed by Teacher).
- **`distillation_weight`**: Float (lambda passed to Student).

### 2. Training Log Entry
Recorded at every training step.
- **`step`**: Integer.
- **`seed`**: Integer.
- **`regime`**: Enum (`uniform`, `dopd`, `randomized_weight`).
- **`advantage_gap`**: Float (calculated $Q_{teacher} - V_{baseline}$).
- **`weight_lambda`**: Float (dynamic weight used).
- **`loss`**: Float (distillation loss).
- **`student_entropy`**: Float (policy entropy).
- **`action`**: Integer.

### 3. Experiment Result (Per Seed)
Aggregated metrics for one seed.
- **`seed`**: Integer.
- **`regime`**: Enum.
- **`accuracy_unmasked`**: Float (0.0 to 1.0).
- **`accuracy_masked`**: Float (0.0 to 1.0).
- **`performance_drop`**: Float.
- **`convergence_steps`**: Integer (steps to reach stable policy).
- **`mean_entropy`**: Float.

## File Formats

### Raw Data
- **Location**: `data/raw/transitions_seed_{seed}.json`
- **Format**: JSON Lines (one record per line) for streaming efficiency.

### Processed Data
- **Location**: `data/processed/results_{regime}.csv`
- **Format**: CSV with headers: `seed, regime, accuracy_unmasked, accuracy_masked, performance_drop, convergence_steps`.

### Statistical Report
- **Location**: `data/processed/statistical_summary.json`
- **Format**: JSON containing p-value, effect size, and exploratory status.

## Constraints

- **Grid Size**: Max 10x10 (enforced in `privileged_grid.py`).
- **Seeds**: Training seeds (0-49), Evaluation seeds (50-99), Baseline seeds (1000-1099) must be distinct sets.
- **Data Hygiene**: Raw data files are never modified; analysis scripts read from them and write to `processed/`.
