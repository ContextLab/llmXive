# Data Model: Dynamic Socio-Cognitive State Injection

## Overview

This document defines the data structures used for the `001-dynamic-state-injection` feature, ensuring data hygiene (Constitution Principle III) and providing schema contracts for validation.

## Entity Definitions

### 1. ConflictTrajectory
Represents a single generated conflict scenario.

- **trajectory_id**: Unique string (UUID).
- **dialogue**: List of turns (speaker, text).
- **metadata**:
  - `emotional_reactivity`: Float (0.0–10.0).
  - `cultural_identity`: List of strings (e.g., `["Western","Eastern"]`).
  - `conflict_type`: String (e.g., `"resource"`).
- **ideal_resolution**: String (ground‑truth resolution).

### 2. SocioCognitiveState
The inferred state from the classifier.

- **label**: String (`escalating`, `cultural-friction`, `neutral`, `de-escalating`).
- **confidence**: Float (0.0–1.0).
- **trigger**: String (e.g., `"sentiment_spike"`).

### 3. ExperimentRun
One execution of an LLM on a trajectory under a specific condition.

- **trajectory_id**: Reference to `ConflictTrajectory`.
- **llm_id**: String (model name).
- **condition**: Enum (`static`, `adapter`).
- **prompt**: String (full system prompt used for the turn).
- **output**: String (LLM response).
- **metrics**:
  - `consensus_gap_score`: Float (0.0–1.0).
  - `inference_time_ms`: Integer.

### 4. StatisticalReport
Aggregated results for a single LLM.

- **llm_id**: String.
- **comparison**:
  - `mean_diff`: Float (Adapter − Static).
  - `p_value`: Float.
  - `is_significant`: Boolean.
  - `effect_size`: Float.
  - `test_type`: String (`t-test` or `wilcoxon`).
- **correction_applied**: Boolean.

## Data Flow

1. **Raw Generation**: `code/data/generator.py` creates `data/processed/trajectories.jsonl`.
2. **State Annotation**: Heuristic rules annotate each turn with a `SocioCognitiveState`; these labels form the training set for the classifier.
3. **Classifier Training**: `code/models/classifier.py` outputs `data/models/classifier.pkl`.
4. **Experiment Logs**: `data/processed/experiments/{llm_id}.jsonl`.
5. **Statistical Summary**: `data/results/statistical_summary.json`.

## Storage & Hygiene

- **Checksums**: SHA‑256 recorded for all raw and processed files.
- **Immutability**: Raw generated trajectories are never overwritten; derivations write new files.
- **PII**: All participant identifiers are synthetic; no personal data stored.
