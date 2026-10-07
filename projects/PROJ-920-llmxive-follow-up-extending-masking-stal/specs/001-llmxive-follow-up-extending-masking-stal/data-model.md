# Data Model: llmXive follow-up: extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

## Overview

This document defines the data structures for the synthetic trajectory generation and agent simulation pipeline.

## Trajectory Schema

A trajectory is a JSON object representing a single search session.

### Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `trajectory_id` | string | Unique identifier (e.g., "traj_001") |
| `turns` | array | List of turn objects |
| `critical_evidence_turn` | integer | Index of the turn containing critical evidence (0-based) |
| `density_level` | string | "low", "medium", or "high" |
| `target_entropy` | float | Target entropy per token for the critical evidence block |
| `actual_entropy` | float | Calculated entropy per token (validated) |
| `technical_token_ratio` | float | Ratio of technical tokens in the critical evidence block |
| `final_density` | float | Calculated density: `0.6 * entropy + 0.4 * tech_ratio` |

### Turn Object

| Field | Type | Description |
| :--- | :--- | :--- |
| `turn_index` | integer | 0-based index of the turn |
| `text` | string | Content of the turn |
| `is_critical` | boolean | True if this turn contains critical evidence |
| `entropy_per_token` | float | Entropy of this turn's text |

## Simulation Log Schema

A CSV file containing the results of the agent simulation.

**Source of Truth**: `data/logs/simulation_results.csv`

### Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `trajectory_id` | string | ID of the trajectory |
| `density` | float | Final density of the critical evidence |
| `horizon` | integer | Retention horizon used in this simulation run |
| `evidence_age` | integer | Age of the evidence (current_turn - evidence_turn) |
| `success` | integer | 1 if success, 0 if failure |
| `retrieval_prob` | float | Probability of retrieval (always 0.9 in this design) |

## File Paths

- `data/raw/trajectories.json`: Generated trajectories.
- `data/logs/simulation_results.csv`: Simulation logs.
- `results/regime_map.png`: 3D surface plot.

## Data Hygiene

- **Checksums**: SHA-256 checksums for `trajectories.json` and `simulation_results.csv` will be recorded in the project state file `state/projects/PROJ-920-llmxive-follow-up-extending-masking-stal.yaml`.
- **Immutability**: Raw data files are never modified. Derived files (logs, plots) are new files.
- **PII**: No PII is generated (synthetic data).