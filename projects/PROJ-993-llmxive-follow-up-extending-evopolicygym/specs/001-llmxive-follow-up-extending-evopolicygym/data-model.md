# Data Model: llmXive follow-up

## 1. Overview

This document defines the data artifacts produced by the `001-llmxive-counterfactual-extension` feature. All data is stored in `data/` and validated against schemas in `contracts/`.

## 2. Data Artifacts

### 2.1. Environment Discovery Log
- **File**: `data/discovered_envs.json`
- **Purpose**: Records the list of environments successfully loaded and their shift configurations. **This is the source of truth for the environment count.**
- **Fields**: `env_id` (str), `base_name` (str), `shift_step` (int), `shift_type` (str).

### 2.2. Sensitivity Report
- **File**: `data/sensitivity_report.csv`
- **Purpose**: Records the results of the static agent test on dynamic environments to validate the shift impact.
- **Fields**: `env_id`, `pre_shift_score`, `post_shift_score`, `drop_percent`, `p_value`, `is_significant`.
- **Schema**: Validated against `contracts/sensitivity_report.schema.yaml` (pre-generated in Phase 0).

### 2.3. Evolution Results
- **File**: `data/evolution_results.csv`
- **Purpose**: Final metrics for each evolved policy.
- **Fields**: `run_id`, `seed`, `condition` (baseline/counterfactual), `generalization_score`, `complexity`, `branch_count`, `generation_errors`.

### 2.4. Fallback Log
- **File**: `data/fallbacks.log`
- **Purpose**: Tracks LLM failures and fallback usage for SC-004.
- **Fields**: `run_id`, `event_type` (timeout, validation_fail, exceeds_token_limit), `rule_id`, `timestamp`.

## 3. Data Flow

1. **Discovery**: `environments/registry.py` loads envs -> `data/discovered_envs.json`.
2. **Validation**: `agents/static_agent.py` runs on dynamic envs -> `data/sensitivity_report.csv`.
3. **Evolution**: `agents/evolutionary_harness.py` runs evolution -> `data/evolution_results.csv`.
4. **Explanation**: `explanation/generator.py` logs failures -> `data/fallbacks.log`.
5. **Analysis**: `analysis/statistical_test.py` reads CSVs -> Final report.

## 4. Integrity Constraints

- **Checksums**: All CSV/JSON files are checksummed (SHA-256) and recorded in `state/...yaml`.
- **Immutability**: Raw data files are never modified in place. Derivations create new files.
- **Schema Validation**: Every CSV/JSON file is validated against its corresponding `contracts/*.schema.yaml` before use.
- **Schema Generation**: Schemas (e.g., `contracts/sensitivity_report.schema.yaml`) are generated in Phase 0 (Research) as static artifacts, independent of the data generation, to resolve the dependency deadlock.