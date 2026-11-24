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
| `predicted_correctness` | number (0‑1) | Model‑predicted probability of correctness. |
| `chain_length` | integer (≥ -1) | Shortest‑path hops; -1 indicates unresolvable. |
| `chain_bin` | string (`'1'`, `'2'`, `'3+'`) | Binned hop count. |
| `question_difficulty` | number (0‑1) | Difficulty proxy (normalized question length). |
| `video_length_seconds` | number (≥ 0) | Video duration. |
| `answer_type` | string (`"multiple_choice"` or `"open_ended"`) | Answer format. |
| `status` | string (`"annotated"`, `"disconnected"`, `"mapping_failure"`) | Linking outcome. |
| `hop_bin` | string | Duplicate of `chain_bin` for backward compatibility. |

### `data/processed/chain_bins.csv`
| Column | Type | Description |
|--------|------|-------------|
| `question_id` | string | Links to `annotated_videokr.csv`. |
| `hop_bin` | string (`'1'`, `'2'`, `'3+'`) | Binned hop count. |

### `data/processed/threshold_results.json`
```json
{
  "primary_threshold": null,
  "results": [
    { "knot": 1, "p_value": null, "effect_size": null, "cliff_magnitude": null, "is_significant": null },
    { "knot": 2, "p_value": null, "effect_size": null, "cliff_magnitude": null, "is_significant": null },
    { "knot": 3, "p_value": null, "effect_size": null, "cliff_magnitude": null, "is_significant": null },
    { "knot": 4, "p_value": null, "effect_size": null, "cliff_magnitude": null, "is_significant": null },
    { "knot": 5, "p_value": null, "effect_size": null, "cliff_magnitude": null, "is_significant": null }
  ],
  "robustness_status": "PASS",
  "bias_flag": false,
  "disconnection_rates": { "1": 0.0, "2": 0.0, "3+": 0.0 }
}
```

### `data/processed/sensitivity_analysis.json`
```json
{
  "binning_schemes": [
    { "scheme": "S1 (1,2,3+)", "selected_knot": null, "p_value": null, "is_significant": null },
    { "scheme": "S2 (1,2,3,4+)", "selected_knot": null, "p_value": null, "is_significant": null },
    { "scheme": "S3 (1,2,3,4,5+)", "selected_knot": null, "p_value": null, "is_significant": null }
  ],
  "robustness_status": "PASS"
}
```

### `data/processed/model_lrt_results.json`
```json
{
  "baseline_loglik": null,
  "extended_loglik": null,
  "lrt_statistic": null,
  "p_value": null,
  "is_significant": null,
  "conclusion": null
}
```

### `data/processed/confound_adjusted_lrt.json`
```json
{
  "baseline_loglik_cov": null,
  "extended_loglik_cov": null,
  "lrt_statistic_cov": null,
  "p_value_cov": null,
  "is_significant_cov": null,
  "conclusion_cov": null
}
```

### `data/processed/power_analysis.json`
```json
{
  "effect_size_h": "0.12",
  "alpha": 0.05,
  "adjusted_alpha": 0.01,
  "power": 0.80,
  "min_samples_per_bin": 100,
  "computed_n": 92,
  "rounded_n": 100
}
```

## 3. Additional Output Artifacts
- `accuracy_binned.png` – bar chart of per‑bin accuracy.  
- `accuracy_binned.csv` – (`chain_bin`, `accuracy`, `sample_size`).  
- `accuracy_vs_hop_raw.png` – scatter plot with LOESS trend.  
- `accuracy_vs_hop_raw.csv` – (`chain_length`, `correctness`).  

## 4. Data Flow Diagram
1. **Data Download** → `data/raw/`.  
2. **Annotation** → `annotated_videokr.csv` + `chain_bins.csv`.  
3. **Power Analysis** → `power_analysis.json`.  
4. **Stratified Accuracy** → `accuracy_binned.*`.  
5. **Threshold Detection** → `threshold_results.json`.  
6. **Sensitivity & Covariate Sweep** → `sensitivity_analysis.json`.  
7. **Predictive Modeling** → `model_lrt_results.json`, `confound_adjusted_lrt.json`, and injection of `predicted_correctness`.  
8. **Runtime & Memory Logging** → `runtime_log.json`, `memory_log.json`.  

## 5. Validation Rules
- All CSV/JSON files must validate against schemas in `contracts/`.  
- Every row in `annotated_videokr.csv` must have a non‑null `chain_length` **or** a `status` indicating failure.  
- `chain_length` ≥ 1 for `status="annotated"`; `chain_bin` must be `'1'`, `'2'`, or `'3+'`.  
- Raw files under `data/raw/` are immutable; derived files receive new filenames.
