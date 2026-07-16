# Data Model: llmXive follow-up: extending "Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution"

## Overview

This document defines the data structures used in the experiment: failure trajectories, ground-truth state transitions, retrieval relevance scores, and statistical results. All data is stored in `data/` with checksums; raw data is immutable; derived data is versioned.

## Core Entities

### Failure Trajectory

A sequence of agent actions in ALFWorld ending in failure.

**Fields**:
- `trajectory_id`: Unique string identifier (UUID v4).
- `task_id`: ALFWorld task identifier (e.g., `pick_and_place_simple-1`).
- `failure_step`: Integer step number where failure occurred.
- `action_log`: List of strings (agent actions up to failure).
- `failure_description`: Human-readable failure summary (e.g., "failed to pick up object X after Y steps").
- `ground_truth_root_cause`: **String representing the raw simulator state transition log** (e.g., `STATE: [object] not found`), independent of agent text.
- `condition`: Enum: "baseline", "degraded", "intervention".
- `retrieval_relevance_score`: Float (0.0–1.0).
- `task_completed`: Boolean (true if re-executed task succeeded).
- `timestamp`: ISO 8601 timestamp of generation.
- `seed`: Integer random seed used for generation.

**Source**: `src/sim/trajectory_generator.py` → `data/raw/trajectories.jsonl`.

### Ground-Truth State Transition

Simulator log entry linking failure to root cause.

**Fields**:
- `state_id`: Unique state identifier.
- `task_id`: ALFWorld task identifier.
- `transition_type`: String (e.g., "object_not_found", "action_invalid").
- `description`: **Raw simulator state transition string** (e.g., `STATE: [object] not found`).
- `is_failure`: Boolean (true if transition led to failure).

**Source**: ALFWorld simulator logs → `data/raw/state_transitions.jsonl`.

### Frozen Task Bank

Human-annotated task definitions for retrieval.

**Fields**:
- `task_id`: ALFWorld task identifier.
- `root_cause_template`: String template for matching failure descriptions.
- `human_annotation`: Text description of ground-truth root cause.
- `priority`: Integer (for ambiguous cases).

**Source**: `data/raw/task_bank.json`.

### Statistical Results

Aggregated metrics for each condition.

**Fields**:
- `condition`: Enum: "baseline", "degraded", "intervention".
- `n`: Integer sample size (500).
- `mean_retrieval_score`: Float.
- `std_retrieval_score`: Float.
- `task_completion_rate`: Float (0.0–1.0).
- `normality_p_value`: Float (Shapiro-Wilk p-value).
- `test_used`: String ("t-test" or "mann-whitney-u").
- `p_value`: Float (statistical test p-value).
- `effect_size`: Float (Cohen's d or rank-biserial correlation).

**Source**: `src/analysis/statistical_tests.py` → `data/derived/stats.csv`.

## Data Flow

1. **Generation**: `trajectory_generator.py` (3 independent runs) → `data/raw/trajectories.jsonl`.
2. **Validation**: `validation.py` → filters invalid trajectories; logs excluded cases.
3. **Condition Processing**: `degraded.py`, `intervention.py` → adds `condition` field (Note: Conditions are generation parameters, not post-processing).
4. **Retrieval Scoring**: `relevance_scorer.py` → calculates score by matching *retrieved task* to *raw simulator log* (ground-truth).
5. **Re-execution**: `sim/alfworld_runner.py` → adds `task_completed`.
6. **Aggregation**: `statistical_tests.py` → `data/derived/stats.csv`.

## Storage & Hygiene

- **Raw Data**: `data/raw/` (immutable; checksummed).
- **Derived Data**: `data/derived/` (versioned; checksummed).
- **Checkpoints**: `state/...yaml` records artifact hashes.
- **No PII**: All data is synthetic or simulator-generated; no personally identifiable information.