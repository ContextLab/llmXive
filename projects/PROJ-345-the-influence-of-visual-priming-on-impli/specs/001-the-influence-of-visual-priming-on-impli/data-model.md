# Data Model: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## 1. Entity Overview
| Entity | Primary Attributes | Description |
|---|---|---|
| **Participant** | `participant_id` (string), optional `age`, `gender`, `education` | Unique subject identifier; demographics may be missing. |
| **Trial** | `trial_id`, `participant_id`, `response_time`, `stimulus_id`, `prime_valence`, `stimulus_ambiguity`, `linkage_status`, `demographics_status` | One observation linking a participant to a stimulus under a prime condition. |
| **Stimulus** | `stimulus_id`, `type` (image/word), `prime_valence` (derived or human‑rated), `ambiguity` (derived or human‑rated) | Stored separately in `data/primes/` and `data/targets/` per Constitution Principle VI. |

## 2. Schemas

### 2.1 Processed Trial Schema (`data/processed/linked_trials.csv`)
| Column | Type | Constraints |
|---|---|---|
| `trial_id` | string | unique |
| `participant_id` | string | foreign key → Participant |
| `response_time` | number (ms) | > 0 |
| `prime_valence` | number | range `[-1.0, 1.0]` |
| `stimulus_ambiguity` | number | range `[0.0, 1.0]` |
| `stimulus_id` | string | foreign key → Stimulus |
| `linkage_status` | string | enum: `linked`, `missing_image`, `missing_metadata` |
| `demographics_status` | string | enum: `complete`, `missing_age`, `missing_gender`, `missing_education`, `missing_all` |

### 2.2 Linkage Status Artifact (`state/linkage_status.json`)
```json
{
  "status": "PASS|WARN|HALT",
  "percentage": 0.0,
  "threshold": 95.0,
  "message": "string"
}
```

### 2.3 Model Convergence Metrics (`state/model_convergence_metrics.json`)
| Field | Type | Description |
|---|---|---|
| `convergence_rate` | number ∈[0,1] | Successful fits / total attempts |
| `total_attempts` | integer ≥1 | Number of optimizer tries |
| `successful_runs` | integer ≥0 | Fits that converged |
| `failed_runs` | integer ≥0 | Fits that failed |
| `optimizer_settings` | array of strings | Descriptions of each optimizer tried |

### 2.4 VIF Flag Artifact (`state/vif_flag.json`)
| Field | Type | Description |
|---|---|---|
| `flagged` | boolean | True if any VIF > 5.0 |
| `vif_values` | object (predictor → number) | Raw VIFs |
| `claim_suppressed` | boolean | If true, the report omits independent‑effect language |
| `message` | string | Human‑readable explanation |

### 2.5 Sensitivity Analysis (`reports/sensitivity_analysis.csv`)
| Column | Type | Description |
|---|---|---|
| `alpha_level` | number | Tested significance threshold |
| `significant_interactions` | integer | Count of interaction terms passing FDR |
| `total_tests` | integer | Number of fixed‑effect tests |
| `fdr_corrected_p_values` | string (JSON list) | List of corrected p‑values |
| `conclusion` | string | `"Significant"`, `"Non‑Significant"`, or `"Borderline"` |

## 3. Data Flow Diagram
1. **Ingest** → `data/raw/iat.parquet` (T002)  
2. **Validate Columns** (T003) → abort if schema mismatch.  
3. **Extract Stimulus Metadata** (T004) → `data/primes/`, `data/targets/`.  
4. **Linkage Metric** (T005) → `state/linkage_status.json`.  
5. **Threshold Definition** (T006) → `config/analysis_params.json`.  
6. **Linkage Gate** (T007) → may halt.  
7. **Derive Ambiguity / Valence** (T008‑T009) → add columns to `linked_trials.csv`.  
8. **Merge & Finalize** (T010) → `data/processed/linked_trials.csv`.  
9. **Demographics Flag** (T012) → `state/demographics_status.json`.  
10. **VIF Check** (T013) → `state/vif_flag.json`.  
11. **LME Fit** (T014) → `state/model_results.pkl`.  
12. **Diagnostics / Convergence** (T015‑T016) → `state/model_convergence_metrics.json`.  
13. **FDR & Framing** (T017‑T018) → augment result dict.  
14. **Sensitivity Analysis** (T019) → `reports/sensitivity_analysis.csv`.  
15. **Plot & PDF Generation** (T020‑T021) → `reports/final_report.pdf`.  

All intermediate artifacts are validated against the JSON/YAML schemas in `contracts/`.

## 4. Constraints & Validation Rules
- **Linkage Threshold**: `percentage` ≥ `threshold` (default 95 %). If not, `status` = `HALT`.  
- **Valence Range**: `prime_valence` ∈ [-1, 1].  
- **Ambiguity Range**: `stimulus_ambiguity` ∈ [0, 1].  
- **PII Scan**: `participant_id` must not match email, phone, SSN, or full name regexes.  
- **VIF Flag**: If `flagged` = true, `claim_suppressed` = true and the PDF includes a warning.  
- **Demographics Status**: Missing covariates lead to omission from the model (see §3.1 of `research.md`).  

---
