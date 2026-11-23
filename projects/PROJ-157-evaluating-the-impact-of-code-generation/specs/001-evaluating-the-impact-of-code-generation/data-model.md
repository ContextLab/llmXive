# Data Model: Evaluating the Impact of Code Generation Models on Code Security

## Overview
The pipeline manipulates three core entities, each persisted as newline‑delimited JSON (`*.jsonl`) files under `data/`. Schemas are defined in `contracts/` and validated by the test suite.

## Entities

| Entity | Description | Primary File(s) | Key Fields |
|--------|-------------|-----------------|------------|
| **ProblemPair** | One programming challenge together with the human reference solution and LLM‑generated variants for each model. | `data/raw/problem_pairs_v{hash}.jsonl` | `problem_id` (str), `human_code` (str), `llm_code` (mapping model → str), `generation_timestamp` (ISO‑8601) |
| **FuzzResult** | Outcome of a fuzzing run for a single compiled binary. | `data/results/fuzz_results_v{hash}.jsonl` | `binary_id` (str), `model` (str, e.g., `human`, `codellama`, `starcoder`), `crash_count` (int, security‑relevant only), `unique_stack_traces` (list‑of‑str), `severity_scores` (list‑of‑int, 1‑4), `execution_status` (enum: `success`, `timeout`, `compile_fail`) |
| **StatisticalSummary** | Aggregated test statistics for a model comparison. | `data/analysis/stat_summary_v{hash}.jsonl` | `model` (str), `test_method` (str), `p_value` (float), `effect_size` (float), `corrected_alpha` (float), `conclusion_text` (str) |

## Schema Files

* `contracts/problem_pair.schema.yaml` – validates each line of the ProblemPair file.  
* `contracts/fuzz_result.schema.yaml` – validates each line of the FuzzResult file.  

Both schemas enforce:
* Presence of required fields.  
* Correct data types (string, integer, list).  
* Enumerated values for `execution_status`.  
* Non‑negative integers for counts and severity scores.  

All schema files are version‑controlled and referenced by the CI test harness.

---


