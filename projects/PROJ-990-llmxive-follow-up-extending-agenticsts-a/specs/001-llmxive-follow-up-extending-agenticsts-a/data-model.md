# Data Model: llmXive follow-up: extending "AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents"

## Overview

This document defines the data structures used throughout the implementation of the dynamic memory policy feature. It ensures data hygiene (Constitution Principle III) and serves as the schema for validation contracts.

## Entity Definitions

### 1. Game Trajectory
A complete record of a single game run, containing per-turn state metrics and the final outcome.

- **Source**: `data/raw/` (immutable logs).
- **Derived Fields**: `move_entropy`, `layer_utility_proxy`.
- **Key Fields**:
  - `trajectory_id`: Unique identifier.
  - `turns`: List of turn objects.
  - `outcome`: Binary (1=Win, 0=Loss).

### 2. Turn State
A single decision point within a trajectory.

- **Fields**:
  - `turn_number`: Integer.
  - `health_ratio`: Float (0.0 - 1.0).
  - `enemy_threat_level`: Float.
  - `deck_size`: Integer.
  - `legal_moves`: List of strings.
  - `move_entropy`: Float (calculated).
  - `retrieved_layers`: List of layer IDs (static logs).

### 3. Memory Layer
A typed category of stored information.

- **Fields**:
  - `layer_id`: Unique identifier.
  - `layer_type`: String (e.g., "Inventory", "Enemy State").
  - `token_cost`: Integer.
  - `utility_score`: Float (predicted or ground-truth).

### 4. Simulation Result
The output of a single run (Dynamic, Static, or Random).

- **Fields**:
  - `trajectory_id`: Reference.
  - `condition`: String ("dynamic", "static", "random").
  - `total_tokens`: Integer.
  - `outcome`: Binary (1/0).
  - `layers_used`: List of layer IDs.

### 5. Statistical Result
Aggregated metrics and test statistics.

- **Fields**:
  - `test_name`: String (e.g., "McNemar", "Paired T-Test").
  - `condition_a`: String.
  - `condition_b`: String.
  - `statistic`: Float.
  - `p_value`: Float.
  - `p_value_corrected`: Float (Bonferroni).
  - `effect_size`: Float.

## Data Flow

1. **Ingestion**: Raw logs → `parser.py` → `data/processed/training_data.csv`.
2. **Training**: `classifier.py` → `data/processed/model.pkl` + `data/processed/metrics.json`.
3. **Simulation**: `simulator.py` → `data/processed/results.csv`.
4. **Analysis**: `stats.py` → `data/processed/statistical_results.json`.
5. **Reporting**: `paper/` reads from `data/processed/`.

## Validation Rules

- **Health Ratio**: Must be in [0.0, 1.0].
- **Entropy**: Must be ≥ 0.0. If calculated value is NaN, default to 0.0 (or trigger fallback).
- **Token Count**: Must be > 0.
- **Outcome**: Must be 0 or 1.
- **Correlation**: Proxy validation correlation must be ≥ 0.7 (warning if lower).
