# Data Model: Video Reasoning Threshold Analysis

## 1. Conceptual Model
The analysis revolves around three core entities:

| Entity | Description |
|--------|-------------|
| **QuestionRecord** | One QA pair from VideoKR‑SFT, enriched with `chain_length`, `chain_bin`, and correctness. |
| **KnowledgeGraph** | Static directed graph of entities/relations; used read‑only for hop counting. |
| **ThresholdResult** | Outcome of the permutation change‑point test and sensitivity sweep. |

## 2. Physical Schemas

### `data/processed/annotated_videokr.csv`
| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Unique identifier from the raw dataset. |
| `question` | string | Natural‑language question text. |
| `answer` | string | Ground‑truth answer text. |
| `correctness` | boolean | Whether the model’s prediction was correct (1 = correct). |
| `chain_length` | integer | Shortest‑path hop count (≥ 1) or `-1` if unresolvable. |
| `chain_bin` | string | `'1'`, `'2'`, or `'3+'` (derived from `chain_length`). |
| `status` | string | `"valid"`, `"disconnected"`, or `"mapping_failure"` (see FR‑001). |

### `data/processed/threshold_results.json`
```json
{
  "primary_threshold": "a low threshold indicating minimal occurrence",
  "results": [
    {
      "knot": 2,
      "p_value": [deferred],
      "effect_size": [deferred],
      "cliff_magnitude": [deferred],
      "is_significant": [deferred]
    },
    {
      "knot": 3,
      "p_value": [deferred],
      "effect_size": [deferred],
      "cliff_magnitude": [deferred],
      "is_significant": [deferred]
    },
    {
      "knot": 4,
      "p_value": [deferred],
      "effect_size": [deferred],
      "cliff_magnitude": [deferred],
      "is_significant": [deferred]
    }
  ],
  "robustness_status": "PASS",
  "bias_flag": false,
  "disconnection_rates": {
    "1": 0.01,
    "2": 0.02,
    "3+": a modest positive value
  }
}
```

### Supporting Logs
- `runtime_log.json` – total wall‑clock time, `limit_exceeded` flag (SC‑004).  
- `memory_log.json` – peak RAM usage, `limit_exceeded` flag (SC‑005).  
- `annotation_coverage.json` – counts of total, annotated, and unresolvable records (SC‑001).

## 3. Data Flow Diagram
1. **Raw Files** (`data/raw/`) → `download_data.py` (gate) → **Verified Presence**.  
2. **Ingestion** (`annotate_graph.py`) → `annotated_videokr.csv`.  
3. **Analysis** (`stratify_accuracy.py`, `detect_threshold.py`, `sensitivity.py`) → accuracy plots, `threshold_results.json`.  
4. **Reporting** (`main.py`) → logs, final JSON artifacts.

## 4. Validation Rules
- **Schema Conformance**: All CSV/JSON outputs must validate against the schemas in `contracts/`.  
- **Completeness**: Every row must have a non‑null `chain_length` **or** a `status` indicating failure.  
- **Integrity**: `chain_length` ≥ 1 for `status = "valid"`; `chain_bin` matches the rule `'1'` / `'2'` / `'3+'`.  
- **Immutability**: Files under `data/raw/` are never overwritten; derived files are new.

---
