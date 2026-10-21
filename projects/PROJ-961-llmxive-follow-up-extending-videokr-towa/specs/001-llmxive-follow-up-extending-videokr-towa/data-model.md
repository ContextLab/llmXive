# Data Model: Video Reasoning Threshold Analysis

## 1. Conceptual Model
The analysis revolves around three core entities:

| Entity | Description |
|--------|-------------|
| **QuestionRecord** | One QA pair from the dataset, enriched with `chain_length`, `chain_bin`, covariates, and binary correctness. |
| **KnowledgeGraph** | Static directed graph of entities/relations; read‑only for hop counting. |
| **ThresholdResult** | Outcome of the permutation change‑point test, LRT, and sensitivity sweep. |

## 2. Physical Schemas

### `data/processed/annotated_videokr.csv`
| Column | Type | Description |
|--------|------|-------------|
| `question_id` | string | Unique identifier from the raw dataset. |
| `question_text` | string | Natural‑language question. |
| `answer_text` | string | Ground‑truth answer. |
| `correctness` | boolean | Binary label indicating whether the model answer is correct. |
| `predicted_correctness` | number | Model prediction of correctness (probability, 0.0–1.0) written after the predictive‑model step (FR‑013). |
| `chain_length` | integer | Shortest‑path hop count (≥ 1) or `-1` if unresolvable. |
| `chain_bin` | string | `'1'`, `'2'`, or `'3+'` derived from `chain_length`. |
| `question_difficulty` | number | Float in [0, 1] from `difficulty_score`. |
| `video_length_seconds` | number | Video duration in seconds. |
| `answer_type` | string | `"multiple_choice"` or `"open_ended"` derived from answer format. |
| `status` | string | `"valid"`, `"disconnected"`, or `"mapping_failure"` (FR‑001). |

### `data/processed/chain_bins.csv`
| Column | Type | Description |
|--------|------|-------------|
| `question_id` | string | Links to `annotated_videokr.csv`. |
| `hop_bin` | string | `'1'`, `'2'`, or `'3+'`. |

### `data/processed/threshold_results.json`
```json
{
  "primary_threshold": 3,
  "results": [
    { "knot": 1, "p_value": [deferred], "effect_size": [deferred], "cliff_magnitude": [deferred], "is_significant": [deferred] },
    { "knot": 2, "p_value": [deferred], "effect_size": [deferred], "cliff_magnitude": [deferred], "is_significant": [deferred] },
    { "knot": 3, "p_value": [deferred], "effect_size": [deferred], "cliff_magnitude": [deferred], "is_significant": [deferred] },
    { "knot": 4, "p_value": [deferred], "effect_size": [deferred], "cliff_magnitude": [deferred], "is_significant": [deferred] },
    { "knot": 5, "p_value": [deferred], "effect_size": [deferred], "cliff_magnitude": [deferred], "is_significant": [deferred] }
  ],
  "robustness_status": "PASS",
  "bias_flag": false,
  "disconnection_rates": { "1": 0.01, "2": 0.02, "3+": 0.05 }
}
```

### `data/processed/sensitivity_analysis.json`
```json
{
  "binning_schemes": [
    { "scheme": "[1,2,3+]", "selected_knot": 3, "p_value": [deferred], "is_significant": true },
    { "scheme": "[1,2,3,4+]", "selected_knot": 4, "p_value": [deferred], "is_significant": false },
    { "scheme": "[1,2,3,4,5+]", "selected_knot": 5, "p_value": [deferred], "is_significant": true }
  ],
  "robustness_status": "PASS"
}
```

### `data/processed/model_lrt_results.json`
```json
{
  "baseline_loglik": [deferred],
  "extended_loglik": [deferred],
  "lrt_statistic": [deferred],
  "p_value": [deferred],
  "is_significant": [deferred],
  "conclusion": "Chain length adds predictive power"
}
```

### `data/processed/power_analysis.json`
```json
{
  "effect_size_h": 0.12,
  "alpha": 0.05,
  "adjusted_alpha": 0.01,
  "power": 0.8,
  "min_samples_per_bin": 50,
  "computed_n": 45,
  "rounded_n": 50
}
```

### Supporting Logs
- `runtime_log.json` – total wall‑clock seconds, `limit_exceeded` flag (SC‑004).  
- `memory_log.json` – peak RAM in GB, `limit_exceeded` flag (SC‑005).  
- `annotation_coverage.json` – counts of total, annotated, and unresolvable records (SC‑001).

## 3. Additional Output Artifacts
- `data/processed/accuracy_binned.png` – bar chart of per‑bin accuracy.  
- `data/processed/accuracy_binned.csv` – summary table (`chain_bin`, `accuracy`, `sample_size`).  
- `data/processed/accuracy_vs_hop_raw.png` – scatter plot with LOESS trend.  
- `data/processed/accuracy_vs_hop_raw.csv` – raw per‑sample (`chain_length`, `correctness`).  

## 4. Data Flow Diagram
1. **Raw Files** (`data/raw/`) → `download_data.py` (gate) → **Verified Presence**.  
2. **Annotation** (`annotate_graph.py`) → `annotated_videokr.csv` + `chain_bins.csv`.  
3. **Power Analysis** (`power_analysis.py`) → `power_analysis.json`.  
4. **Stratified Accuracy** (`stratify_accuracy.py`) → `accuracy_binned.*`.  
5. **Threshold Detection** (`detect_threshold.py`) → `threshold_results.json`.  
6. **Sensitivity & Covariate Sweep** (`sensitivity.py`) → `sensitivity_analysis.json`.  
7. **Predictive Modeling** (`model_lrt.py`) → `model_lrt_results.json` **and** inject `predicted_correctness` into `annotated_videokr.csv`.  
8. **Runtime & Memory Logging** (`main.py`, `memory_tracker.py`) → `runtime_log.json`, `memory_log.json`.  

## 5. Validation Rules
- **Schema Conformance**: All CSV/JSON outputs must validate against the schemas in `contracts/`.  
- **Completeness**: Every row in `annotated_videokr.csv` must have a non‑null `chain_length` **or** a `status` indicating failure.  
- **Integrity**: `chain_length` ≥ 1 for `status = "valid"`; `chain_bin` follows `'1'` / `'2'` / `'3+'`.  
- **Immutability**: Files under `data/raw/` are never overwritten; derived files have new filenames.  

---


