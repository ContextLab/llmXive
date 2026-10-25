# Data Model: Video Reasoning Threshold Analysis

## 1. Conceptual Model
Three core entities drive the analysis:

| Entity | Description |
|--------|-------------|
| **QuestionRecord** | A single QA pair enriched with hop count, bin label, covariates, and binary correctness. |
| **KnowledgeGraph** | Static directed graph of entities/relations used for deterministic hop counting. |
| **ThresholdResult** | Outcome of the permutation change‑point test, LRT, and sensitivity sweep. |

## 2. Physical Schemas

### `data/processed/annotated_videokr.csv`
| Column | Type | Description |
|--------|------|-------------|
| `question_id` | string | Unique identifier. |
| `question_text` | string | Natural‑language question. |
| `answer_text` | string | Ground‑truth answer. |
| `correctness` | boolean | 1 = correct, 0 = incorrect (observed from TVQA). |
| `predicted_correctness` | number | Model‑predicted probability (0.0–1.0). |
| `chain_length` | integer | Shortest‑path hops between query and answer entities; -1 indicates unresolvable. |
| `chain_bin` | string | `'1'`, `'2'`, or `'3+'`. |
| `question_difficulty` | number | Difficulty score (0–1), computed from question length. |
| `video_length_seconds` | number | Video duration in seconds. |
| `answer_type` | string | `"multiple_choice"` or `"open_ended"`. |
| `status` | string | `"annotated"` (successful linking), `"disconnected"` (no path), or `"mapping_failure"` (entity not found). |
| `hop_bin` | string | Duplicate of `chain_bin` for backward compatibility (may be omitted in downstream scripts). |

*All columns conform to `contracts/annotated_questions.schema.yaml`.*

### `data/processed/chain_bins.csv`
| Column | Type | Description |
|--------|------|-------------|
| `question_id` | string | Links to `annotated_videokr.csv`. |
| `hop_bin` | string | `'1'`, `'2'`, or `'3+'`. |

### `data/processed/threshold_results.json`
```json
{
  "primary_threshold": "to be defined based on exploratory analysis",
  "results": [
    { "knot": 1, "p_value": [deferred], "effect_size": [deferred], "cliff_magnitude": [deferred], "is_significant": [deferred] },
    { "knot": 2, "p_value": [deferred], "effect_size": [deferred], "cliff_magnitude": [deferred], "is_significant": [deferred] },
    { "knot": 3, "p_value": [deferred], "effect_size": [deferred], "cliff_magnitude": [deferred], "is_significant": [deferred] },
    { "knot": 4, "p_value": [deferred], "effect_size": [deferred], "cliff_magnitude": [deferred], "is_significant": [deferred] },
    { "knot": 5, "p_value": [deferred], "effect_size": [deferred], "cliff_magnitude": [deferred], "is_significant": [deferred] }
  ],
  "robustness_status": "PASS",
  "bias_flag": false,
  "disconnection_rates": { "1": 0.01, "2": 0.02, "3+": 0.03 }
}
```

### `data/processed/sensitivity_analysis.json`
```json
{
  "binning_schemes": [
    { "scheme": "S1 (1,2,3+)", "selected_knot": 3, "p_value": [deferred], "is_significant": true },
    { "scheme": "S2 (1,2,3,4+)", "selected_knot": 4, "p_value": [deferred], "is_significant": false },
    { "scheme": "S3 (1,2,3,4,5+)", "selected_knot": 5, "p_value": [deferred], "is_significant": true }
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

### `data/processed/confound_adjusted_lrt.json`
```json
{
  "baseline_loglik_cov": [deferred],
  "extended_loglik_cov": [deferred],
  "lrt_statistic_cov": [deferred],
  "p_value_cov": [deferred],
  "is_significant_cov": [deferred],
  "conclusion_cov": "Hop count remains significant after adjusting for difficulty, video length, and answer type"
}
```

### `data/processed/power_analysis.json`
```json
{
  "effect_size_h": "small",
  "alpha": "a conventional significance level",
  "adjusted_alpha": "a modest significance level",
  "power": "high",
  "min_samples_per_bin": 100,
  "computed_n": "a suitable sample size determined by the analysis",
  "rounded_n": "a sufficiently large number"
}
```

## 3. Additional Output Artifacts
- `accuracy_binned.png` – bar chart of per‑bin accuracy.  
- `accuracy_binned.csv` – table (`chain_bin`, `accuracy`, `sample_size`).  
- `accuracy_vs_hop_raw.png` – scatter plot with LOESS trend.  
- `accuracy_vs_hop_raw.csv` – raw (`chain_length`, `correctness`).  

## 4. Data Flow Diagram
1. **Data Download** (`download_tvqa.py`, `download_conceptnet.py`) → `data/raw/`.  
2. **Annotation** (`annotate_graph.py`) → `annotated_videokr.csv` + `chain_bins.csv`.  
3. **Power Analysis** (`power_analysis.py`) → `power_analysis.json` and validates bin adequacy.  
4. **Stratified Accuracy** (`stratify_accuracy.py`) → `accuracy_binned.*`.  
5. **Threshold Detection** (`detect_threshold.py`) → `threshold_results.json`.  
6. **Sensitivity & Covariate Sweep** (`sensitivity.py`) → `sensitivity_analysis.json`.  
7. **Predictive Modeling** (`model_lrt.py`) → `model_lrt_results.json`, `confound_adjusted_lrt.json`, and inject `predicted_correctness` into `annotated_videokr.csv`.  
8. **Runtime & Memory Logging** (`main.py`, `memory_tracker.py`) → `runtime_log.json`, `memory_log.json`.  

## 5. Validation Rules
- **Schema Conformance**: All CSV/JSON files must validate against the schemas in `contracts/`.  
- **Completeness**: Every row in `annotated_videokr.csv` must have a non‑null `chain_length` **or** a `status` indicating failure.  
- **Integrity**: `chain_length` ≥ 1 for `status="annotated"`; `chain_bin` must be `'1'`, `'2'`, or `'3+'`.  
- **Immutability**: Files under `data/raw/` are never overwritten; derived files receive new filenames.  
