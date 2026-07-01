# Data Model: A Matter of TASTE: Improving Coverage and Difficulty of Agent Benchmarks

## 1. Overview
This document defines the data structures used in the TASTE pipeline. All data is persisted as JSON files in the `artifacts/` directory. The schema definitions in `contracts/` serve as the source of truth for validation.

## 2. Core Entities

### 2.1 ToolSequence
An ordered list of tool invocations representing the ground-truth solution.
- **Attributes**:
    - `tools`: List of `ToolInvocation` objects.
    - `length`: Integer (number of steps).
    - `entropy_score`: Float (calculated during Stage 1).

### 2.2 ToolInvocation
A single step in the sequence.
- **Attributes**:
    - `name`: String (e.g., "search_flights").
    - `parameters`: Dictionary of key-value pairs.

### 2.3 Task
The primary output unit.
- **Attributes**:
    - `id`: Unique String (UUID).
    - `scenario`: Natural language string describing the user goal.
    - `action_sequence`: The `ToolSequence` that solves the scenario.
    - `validation_status`: Enum (`valid`, `invalid`, `pending`).
    - `validation_reason`: String (if invalid).
    - `domain`: String (e.g., "airline").
    - `difficulty_score`: Float (Consensus failure rate from Multi-Heuristic Ensemble).

### 2.4 DomainConfig
Configuration for a specific domain.
- **Attributes**:
    - `name`: String.
    - `tools`: List of `ToolDefinition`.
    - `constraints`: List of rules (e.g., "max 5 steps").
    - `validator_module`: String (path to validator).

### 2.5 ValidationReport
Aggregated metrics from the pipeline.
- **Attributes**:
    - `total_tasks`: Integer.
    - `valid_count`: Integer.
    - `validity_rate`: Float (0.0-1.0).
    - `tool_coverage`: Dictionary (tool_name -> count).
    - `unique_combinations`: Integer.
    - `entropy_avg`: Float.
    - `heuristic_complexity_gap`: Float (Difference in failure rates between TASTE and Baseline).
    - `p_value`: Float (Result of Permutation Test).
    - `effect_size_cohen_d`: Float (Magnitude of the difficulty drop).
    - `proxy_correlation`: Float (Correlation with known LLM failures, if applicable).
    - `baseline_type`: String ("real" or "synthetic").

## 3. Schema Definitions
The following schemas are defined in `contracts/` and used for validation:
- `task.schema.yaml`: Validates the `tasks.json` output.
- `domain_config.schema.yaml`: Validates `tool_spec.json`.
- `validation_report.schema.yaml`: Validates `reports/validation_report.json`.

## 4. Data Flow
1. **Input**: `pre_seed.json`, `tool_spec.json` → **Stage 1**: `ngram_checkpoint.json`.
2. **Stage 1 Output**: `ngram_checkpoint.json` → **Stage 2**: `medoids.json`.
3. **Stage 2 Output**: `medoids.json` → **Stage 3**: `tasks_raw.json`.
4. **Validation**: `tasks_raw.json` + `airline.py` → `tasks.json` (filtered).
5. **Evaluation**: `tasks.json` + `ensemble_agent` + `baseline` → `validation_report.json`.
