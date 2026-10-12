# Data Model: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## 1. Entity Overview
| Entity | Primary Attributes | Description |
|--------|-------------------|-------------|
| **Participant** | `participant_id` (string), optional `age`, `gender`, `education` | Unique subject; demographics may be missing. |
| **Trial** | `trial_id`, `participant_id`, `response_time`, `stimulus_id`, `prime_valence`, `stimulus_ambiguity`, `linkage_status`, `demographics_status` | One observation linking a participant to a stimulus under a prime condition. |
| **Stimulus** | `stimulus_id`, `type` (image/word), `prime_or_target`, `valence`, `ambiguity` | Stored separately in `data/primes/` and `data/targets/`; merged only for modeling. |

## 2. Schemas
### 2.1 Processed Trial (`data/processed/linked_trials.csv`)
| Column | Type | Constraints |
|--------|------|-------------|
| `trial_id` | string | unique |
| `participant_id` | string | FK → Participant |
| `response_time` | number (ms) | > 0 |
| `prime_valence` | number | null | ∈ [-1.0, 1.0]; null retained in *valence‑only* scope |
| `stimulus_ambiguity` | number | null | ∈ [0.0, 1.0]; null retained in *valence‑only* scope |
| `stimulus_id` | string | FK → Stimulus |
| `linkage_status` | string | `linked` | `missing_image` | `missing_metadata` |
| `demographics_status` | string | `complete` | `missing_age` | `missing_gender` | `missing_education` | `missing_all` |

### 2.2 Metadata Mapping (`data/processed/metadata_mapping.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `stimulus_id` | string | Identifier |
| `type` | string | `image` | `word` |
| `file_path_or_word` | string | Path under `data/primes/` or `data/targets/`, or the word token |
| `prime_or_target` | string | `prime` | `target` |

### 2.3 Linkage Status (`state/linkage_status.json`)
```json
{
  "status": "PASS|WARN|HALT",
  "percentage": 0.0,
  "threshold": 95.0,
  "message": "string"
}
```

### 2.4 Analysis Scope (`state/analysis_scope.json`)
```json
{ "scope": "full|valence_only", "reason": "string" }
```

### 2.5 Model Convergence Metrics (`state/model_convergence_metrics.json`)
| Field | Type | Description |
|-------|------|-------------|
| `convergence_rate` | number ∈ [0, 1] | successful fits / attempts |
| `total_attempts` | integer ≥ 1 | number of optimizer tries |
| `successful_runs` | integer ≥ 0 | converged fits |
| `failed_runs` | integer ≥ 0 | failed fits |
| `optimizer_settings` | array of strings | attempted optimizers (e.g., `lbfgs`, `bfgs`, `powell`) |

### 2.6 Model Results (`state/model_results.json`)
```json
{
  "fixed_effects": {
    "prime_valence": {"coef": "number", "se": "number", "p_raw": "number", "p_fdr": "number"},
    "stimulus_ambiguity": {"coef": "number", "se": "number", "p_raw": "number", "p_fdr": "number"},
    "interaction": {"coef": "number", "se": "number", "p_raw": "number", "p_fdr": "number"}
  },
  "random_effects": {"participant_intercept_variance": "number"},
  "robust_se": "boolean",
  "caution_note": "string",
  "limitation_note": "string",
  "effect_sizes": {
    "cohens_d": {"estimate": "number", "ci_lower": "number", "ci_upper": "number"},
    "partial_eta_squared": {"estimate": "number", "ci_lower": "number", "ci_upper": "number"}
  }
}
```
*Keys `caution_note` and `limitation_note` are required by FR‑003 and are defined in `contracts/model_results.schema.yaml`.*

### 2.7 VIF Flag (`state/vif_flag.json`)
| Field | Type |
|-------|------|
| `flagged` | boolean |
| `vif_values` | object (predictor → number) |
| `claim_suppressed` | boolean |
| `message` | string |

### 2.8 Verified Sources Registry (`data/verified_sources.json`)
```json
{
  "sources": [
    { "name": "string", "url": "string", "format": "string" }
  ]
}
```
*If `research.md` and this file disagree, **this file is authoritative** (Task T015).*

### 2.9 Ingest Metrics (`data/processed/ingest_metrics.json`)
```json
{
  "total_trials": "integer",
  "linked_trials": "integer",
  "missing_image_trials": "integer",
  "missing_metadata_trials": "integer",
  "linkage_percentage": "number"
}
```

### 2.10 Sensitivity Analysis (`reports/sensitivity_analysis.csv`)
| Column | Type |
|--------|------|
| `alpha_level` | number |
| `significant_tests` | integer |
| `total_tests` | integer |
| `conclusion` | string |

## 3. Data Flow
1. **Ingest** → `data/raw/iat.parquet` (+ checksum).  
2. **Validate** → halt if core columns missing (Task T003).  
3. **Metadata Extraction** → `metadata_mapping.csv`.  
4. **Linkage Metric** → `ingest_metrics.json`, `linkage_status.json`.  
5. **Derive Ambiguity / Valence** → respective CSVs.  
6. **Merge** → `linked_trials.csv` + `analysis_scope.json`.  
7. **VIF** → `vif_flag.json`.  
8. **LME Fit** → `model_results.json`, `model_convergence_metrics.json`.  
9. **FDR** → `fdr_results.json`.  
10. **Framing** → adds `caution_note` & `limitation_note`.  
11. **Sensitivity** → `sensitivity_analysis.csv`.  
12. **Report** → `final_report.pdf` (full or data‑gap).  
13. **PII Scan** → `pii_scan.json`.  
14. **Contract Validation** → `pytest -m contract`.

## 4. Constraints & Validation Rules
- **Linkage**: `% linked ≥ config.LINKAGE_THRESHOLD` (default 95 %). Otherwise `HALT`.  
- **Valence** ∈ [-1, 1]; **Ambiguity** ∈ [0, 1]; nulls allowed only in *valence‑only* scope.  
- **PII**: `participant_id` must not match email/phone/SSN regexes.  
- **VIF** > 5.0 → `claim_suppressed: true`.  
- **Missing covariates** → omitted from model, flagged, never imputed.  
- **Raw data immutable**; all derivations create new files with SHA‑256 hashes recorded.  

---
