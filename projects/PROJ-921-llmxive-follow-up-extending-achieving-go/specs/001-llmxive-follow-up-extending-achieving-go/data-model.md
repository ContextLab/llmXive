# Data Model: llmXive follow-up: extending "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified S"

## Overview

This document defines the data structures used throughout the research pipeline. All data is stored in JSONL (JSON Lines) format for streaming compatibility and processed into Pandas DataFrames for analysis.

## Core Entities

### 1. Prompt
Represents a single input problem statement.

| Field | Type | Description |
| :--- | :--- | :--- |
| `prompt_id` | string | Unique identifier (e.g., `imo_001`, `scienceqa_001`) |
| `text` | string | The full text of the problem/prompt (converted to open-ended for ScienceQA) |
| `source` | string | Dataset origin (e.g., `Nemotron-IMO-Bench`, `ScienceQA`) |
| `domain` | string | Category (e.g., `math`, `general_science`) |
| `is_ill_structured` | boolean | True if from ScienceQA (converted), False if Olympiad |

### 2. Response
Represents a model's generated output.

| Field | Type | Description |
| :--- | :--- | :--- |
| `response_id` | string | Unique identifier |
| `prompt_id` | string | Foreign key to Prompt |
| `model_name` | string | `SU-01` or `Baseline` |
| `text` | string | Generated text |
| `generation_params` | object | JSON: `{temperature, max_tokens, seed}` |
| `truncated` | boolean | True if generation hit token limit |
| `status` | string | `success`, `failure`, `truncated`, `incomplete` |

### 3. Score
Represents the evaluation of a Response by the proxy model.

| Field | Type | Description |
| :--- | :--- | :--- |
| `score_id` | string | Unique identifier |
| `response_id` | string | Foreign key to Response |
| `novelty` | integer | Score 1-5 |
| `feasibility` | integer | Score 1-5 |
| `consistency` | integer | Score 1-5 |
| `entropy` | float | Mean entropy of logits (for ambiguity check) |
| `is_low_confidence` | boolean | True if variance > 1.5 or entropy > 2.0 |
| `raw_output` | string | Full JSON string from proxy model (for audit) |
| `rationale` | string | Raw text rationale from the proxy model (for audit) |

### 4. OlympiadResult
Binary correctness for deterministic problems.

| Field | Type | Description |
| :--- | :--- | :--- |
| `prompt_id` | string | Foreign key to Prompt |
| `model_name` | string | `SU-01` or `Baseline` |
| `is_correct` | boolean | 1 if answer matches ground truth, 0 otherwise |
| `ground_truth` | string | The correct answer (for reference) |

### 5. GoldStandard
Human-rated responses for validation.

| Field | Type | Description |
| :--- | :--- | :--- |
| `response_id` | string | Unique identifier |
| `human_novelty` | integer | Human score 1-5 |
| `human_feasibility` | integer | Human score 1-5 |
| `human_consistency` | integer | Human score 1-5 |
| `proxy_novelty` | integer | Proxy model score |
| `proxy_feasibility` | integer | Proxy model score |
| `proxy_consistency` | integer | Proxy model score |

### 6. LMEResult
Results from the Linear Mixed Effects model.

| Field | Type | Description |
| :--- | :--- | :--- |
| `fixed_effect_model_type` | float | Coefficient for Model Type |
| `fixed_effect_domain` | float | Coefficient for Domain |
| `interaction_effect` | float | Coefficient for Model_Type * Domain |
| `interaction_p_value` | float | P-value for interaction effect |
| `random_effect_variance` | float | Variance of random intercept (Prompt) |

## Data Flow

1.  **Ingestion**: Raw datasets (JSONL/Parquet) → `Prompt` entities.
2.  **Inference**: `Prompt` + Model → `Response` entities (JSONL).
3.  **Scoring**: `Response` → Proxy Model → `Score` entities (JSONL).
4.  **Validation**: `Score` + `GoldStandard` → Correlation metrics.
5.  **Analysis**: `OlympiadResult` + `Score` + `Prompt` → LME model → `LMEResult`.

## File Layout

```text
data/
├── raw/
│   ├── imo_bench.jsonl          # Downloaded from verified URL
│   ├── scienceqa_raw.parquet    # Downloaded from verified URL
│   └── gold_standard.jsonl      # Curated N=50 set
├── processed/
│   ├── unified_prompts.jsonl    # Merged Prompt entities (converted ScienceQA)
│   ├── su01_responses.jsonl     # Responses from SU-01
│   ├── baseline_responses.jsonl # Responses from Baseline
│   ├── su01_scores.jsonl        # Scores for SU-01
│   ├── baseline_scores.jsonl    # Scores for Baseline
│   ├── olympiad_results.jsonl   # Binary correctness
│   └── lme_results.json         # Final statistical output
└── audit/
    ├── truncation_log.jsonl     # Failed generations
    ├── ambiguity_log.jsonl      # Low-confidence scores
    └── audit_log.jsonl          # Comprehensive audit log (FR-007)
```


## projects/PROJ-921-llmxive-follow-up-extending-achieving-go/specs/001-llmxive-follow-up-extending-achieving-go/quickstart.md