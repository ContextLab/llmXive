# Data Model: llmXive follow-up: extending "Macaron-A2UI: A Model for Generative UI in Personal Agents"

## 1. Overview

This document defines the data structures used for ingestion, simulation, and analysis. All data is stored in CSV/JSON formats under `data/` and validated against schemas in `contracts/`.

## 2. Core Entities

### 2.1 InteractionTurn
Represents a single user-agent exchange.
- **Source**: `data/raw/macaron_a2ui.csv` (ingested from Hugging Face)
- **Fields**:
  - `turn_id`: Unique identifier (string).
  - `query`: User input text (string).
  - `ground_truth_intent`: Original intent label (string).
  - `complexity_score`: Derived or annotated score (float/int).
  - `is_annotated`: Boolean (True if manually labeled).
  - `annotated_intent`: "High-Confidence" or "Ambiguous" (string, nullable).

### 2.2 RoutingDecision
Records the outcome of the router for a specific turn.
- **Source**: `data/simulation/decisions.csv`
- **Fields**:
  - `turn_id`: Foreign key to `InteractionTurn`.
  - `router_confidence`: Probability score (float, 0.0-1.0).
  - `chosen_path`: "Generative" or "Deterministic" (string).
  - `intent_category`: "High-Confidence" or "Ambiguous" (string).

### 2.3 SimulationRun
Aggregates metrics for a specific configuration.
- **Source**: `data/simulation/results.csv`
- **Fields**:
  - `run_id`: Unique identifier (string).
  - `turn_id`: Foreign key to `InteractionTurn`.
  - `latency_step`: Injected latency in ms (int: 0, 100, 200, 500, 1000).
  - `ui_density`: Number of UI elements (int: 1, 3, 5, 10).
  - `generation_time`: Simulated generation time in ms (float).
  - `total_latency`: `generation_time` + `latency_step` (float).
  - `patience_threshold`: User's patience limit in ms (float).
  - `abandoned`: Boolean (True if `total_latency` > `patience_threshold`).
  - `alignment_score`: Calculated score (float). **Formula**: `0.5 * intent_match + 0.5 * ui_completeness`.
  - `ui_completeness`: Boolean (True if UI rendered successfully).
  - `intent_match`: Boolean (True if output matches intent).

## 3. Data Flow

1.  **Ingestion**: `data/raw/macaron_a2ui.csv` (from Hugging Face) -> `data/processed/annotated_turns.csv`.
    - **Manual Step**: `code/data/ingest.py --annotate` launches a CLI loop to label 200 unique samples.
2.  **Training**: `annotated_turns.csv` -> `models/router.pth` (DistilBERT weights).
3.  **Simulation**:
    - Input: `annotated_turns.csv`, `router.pth`, `config.yaml`.
    - Process: Loop over turns, apply router, inject latency, generate UI (DistilGPT2 or rule-based), calculate patience.
    - Output: `data/simulation/results.csv`.
4.  **Analysis**: `results.csv` -> `data/analysis/pareto_data.json`, `data/analysis/stats_report.json`.

## 4. Constraints & Validation

- **Missing Data**: No missing values allowed in `query`, `intent`, `latency_step`, `ui_density`.
- **Ranges**:
  - `latency_step`: {0, 100, 200, 500, 1000}.
  - `ui_density`: {1, 3, 5, 10}.
  - `router_confidence`: [0.0, 1.0].
  - `alignment_score`: [0.0, 1.0].
- **Consistency**: `total_latency` must equal `generation_time` + `latency_step` (within ±10ms tolerance).
- **Abandonment**: If `abandoned` is True, `alignment_score` must be 0.0.
