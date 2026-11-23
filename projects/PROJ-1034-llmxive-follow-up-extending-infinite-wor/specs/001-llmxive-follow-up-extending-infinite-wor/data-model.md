# Data Model: llmXive follow-up: extending "Infinite Worlds with Versatile Interactions"

## Overview

This document defines the data structures for the simulation engine, the metric recording system, and the parameter grid. The data model is designed to support streaming processing (to fit within 7GB RAM) and to ensure reproducibility via strict schema validation.

## Entities

### 1. SimulationRun

Represents a single execution of the world simulator.

- **Attributes**:
  - `run_id` (string): Unique identifier (UUID).
  - `config_id` (string): Hash of the parameter configuration.
  - `agent_type` (enum): "neural_baseline" | "ca_eco_director".
  - `parameters` (object): The specific CA parameters (if applicable).
  - `start_time` (timestamp): ISO 8601.
  - `end_time` (timestamp): ISO 8601.
  - `status` (enum): "completed" | "timeout" | "oom" | "error".
  - `seed` (integer): Random seed used for reproducibility.
  - `noise_seed` (integer): Specific noise seed for this run (for LMM random effect).

### 2. MetricRecord

A snapshot of the simulation state at a specific time-step.

- **Attributes**:
  - `run_id` (string): Foreign key to `SimulationRun`.
 - `time_step` (integer): The step number (0 to [deferred]).
  - `coherence_score` (float): Deviation from physics oracle (lower is better).
  - `diversity_score` (float): Event entropy (higher is better).
  - `step_latency_ms` (float): Time taken for this step in milliseconds.
  - `is_valid` (boolean): Whether the step passed physics constraints.
  - `event_entropy` (float): Entropy of the specific state transition (for rare event detection).

### 3. ParameterGrid

The defined set of values for the sweep.

- **Attributes**:
  - `grid_id` (string): Unique identifier.
  - `neighborhood_radius` (list of integers): Values to test.
  - `memory_depth` (list of integers): Values to test.
  - `non_linearity` (list of strings): Values to test (e.g., "linear", "quadratic").

### 4. PhysicsOracleOutput

Output from the Stochastic Physics Sandbox.

- **Attributes**:
  - `timestamp` (timestamp): ISO 8601.
  - `noise_vector` (list of float): Injected random force vectors.
  - `collision_events` (list of string): IDs of collision events.
  - `expected_mass` (float): Expected mass/energy after constraints.
  - `actual_mass` (float): Actual mass/energy after state transition.

## Data Flow

1.  **Generation**: `cli/run_simulation.py` iterates through `ParameterGrid` and noise seeds.
2.  **Simulation**: `src/sim/eco_director.py` generates `MetricRecord` objects in a streaming fashion.
3.  **Storage**: `MetricRecord` objects are appended to a Parquet file in `data/raw/` (streamed to avoid memory overflow).
4.  **Aggregation**: `src/analysis/lmm_runner.py` reads the Parquet file in chunks to compute LMM and RF metrics.
5.  **Validation**: `contracts/` schemas validate every `MetricRecord` and `PhysicsOracleOutput` before writing.

## Data Hygiene

- **Checksums**: Every file in `data/raw/` and `data/processed/` is checksummed (SHA-256).
- **Immutability**: Raw data is never modified. Derivations are written to new files (e.g., `metrics_lmm_results.parquet`).
- **PII**: No personally identifiable information is present in simulation logs.