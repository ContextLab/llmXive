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
  "percentage": "number (0‑100)",
  "threshold": "number (default 95.0, from code/config.py)",
  "message": "string"
}
```

### 2.4 Analysis Scope (`state/analysis_scope.json`)
```json
{
  "scope": "full|valence_only",
  "reason": "string"
}
```

### 2.5 Model Convergence Metrics (`state/model_convergence_metrics.json`)
| Field | Type | Description |
|-------|------|-------------|
| `convergence_rate` | number ∈ [0, 1] | successful fits / attempts |
| `total_attempts` | integer ≥ 1 | number of optimizer tries |
| `successful_runs` | integer ≥ 0 | converged fits |
| `failed_runs` | integer ≥ 0 | failed fits |
| `optimizer_settings` | array of strings | attempted optimizers (`lbfgs`, `bfgs`, `powell`) |

### 2.6 Model Results (`state/model_results.json`)
```json
{
  "fixed_effects": {
    "prime_valence": {"coef": "number", "se": "number", "p_raw": "number", "p_fdr": "number"},
    "stimulus_ambiguity": {"coef": "number", "se": "number", "p_raw": "number", "p_fdr": "number"},
    "interaction": {"coef": "number", "se": "number", "p_raw": "number", "p_fdr": "number"}
  },
  "random_effects": {"participant_intercept_variance": "number", "participant_valence_slope_variance": "number"},
  "robust_se": true,
  "caution_note": "string",
  "limitation_note": "string",
  "effect_sizes": {
    "cohens_d": {"estimate": "number", "ci_lower": "number", "ci_upper": "number"},
    "partial_eta_squared": {"estimate": "number", "ci_lower": "number", "ci_upper": "number"}
  }
}
```
*Random‑effects now include `participant_valence_slope_variance` to reflect the added random slope (methodology‑a4a36c).*

### 2.7 VIF Flag (`state/vif_flag.json`)
| Field | Type |
|-------|------|
| `flagged` | boolean |
| `vif_values` | object (predictor → number) |
| `claim_suppressed` | boolean |
| `message` | string |

### 2.8 Derived Scores Validation (`state/score_validation.json`)
```json
{
  "prime_valence_validation": {"pearson_r": "number", "ci_lower": "number", "ci_upper": "number"},
  "ambiguity_validation": {"pearson_r": "number", "ci_lower": "number", "ci_upper": "number"},
  "validation_passed": "boolean"
}
```
*Provides external validation metrics for the derived predictors (addresses methodology‑c1f3b31e & scientific_soundness‑0f39757b).*

### 2.9 Power Check (`state/power_check.json`)
```json
{
  "required_n": "integer",
  "observed_n": "integer",
  "power_achieved": "boolean",
  "message": "string"
}
```
*Result of the power‑analysis checkpoint (methodology‑e9a77e04).*

### 2.10 Confound Check (`state/confound_check.json`)
```json
{
  "trial_order_autocorrelation": "number",
  "stimulus_repetition_rate": "number",
  "stimulus_icc": "number",
  "confound_severe": "boolean",
  "message": "string"
}
```
*Outputs from the confounding diagnostics (methodology‑e281f6e1).*

### 2.11 Verified Sources Registry (`data/verified_sources.json`)
```json
{
  "sources": [
    {"name": "OpenIAT", "url": "https://huggingface.co/datasets/openai/open_iat/resolve/main/iat.parquet", "format": "parquet"}
  ]
}
```
*If the research.md and this file disagree, this file is authoritative (Task T002).*

### 2.12 Ingest Metrics (`data/processed/ingest_metrics.json`)
```json
{
  "total_trials": "integer",
  "linked_trials": "integer",
  "missing_image_trials": "integer",
  "missing_metadata_trials": "integer",
  "linkage_percentage": "number (0‑100)"
}
```

### 2.13 Sensitivity Analysis (`reports/sensitivity_analysis.csv`)
| Column | Type |
|--------|------|
| `alpha_level` | number |
| `significant_tests` | integer |
| `total_tests` | integer |
| `conclusion` | string |

## 3. Data Flow
1. **Ingest** → `data/raw/iat.parquet` (+ checksum).  
2. **Validate** → halt if core columns missing (Task T004).  
3. **Metadata Extraction** → `metadata_mapping.csv`.  
4. **Linkage Metric** → `ingest_metrics.json`, `linkage_status.json`.  
5. **Derive Ambiguity / Valence** → `ambiguity_scores.csv`, `valence_scores.csv`.  
6. **Merge** → `linked_trials.csv` + `analysis_scope.json`.  
7. **VIF** → `vif_flag.json`.  
8. **Derived Scores Validation** → `score_validation.json`.  
9. **Power Check** → `power_check.json`.  
10. **Confound Check** → `confound_check.json`.  
11. **LME Fit** → `model_results.json`, `model_convergence_metrics.json`.  
12. **FDR** → `fdr_results.json`.  
13. **Framing** → adds `caution_note` & `limitation_note`.  
14. **Sensitivity** → `sensitivity_analysis.csv`.  
15. **Report** → `final_report.pdf` (full or data‑gap).  
16. **PII Scan** → `pii_scan.json`.  
17. **Contract Validation** → `pytest -m contract` validates all JSON/YAML artifacts against schemas in `contracts/`.  

## 4. Constraints & Validation Rules
- **Linkage**: `% linked ≥ config.LINKAGE_THRESHOLD` (default 95 %). Otherwise `HALT`.  
- **Valence** ∈ [-1, 1]; **Ambiguity** ∈ [0, 1]; nulls allowed only in *valence‑only* scope.  
- **PII**: `participant_id` must not match email/phone/SSN regexes.  
- **VIF** > 5.0 → `claim_suppressed: true`.  
- **Missing covariates** → omitted from model, flagged, never imputed.  
- **Derived Score Validation**: Pearson r ≥ 0.6 required for `validation_passed:true`; otherwise a caution flag is set.  
- **Power**: `observed_n` ≥ `required_n` required for `power_achieved:true`; otherwise analysis halts with a data‑gap note.  
- **Confounds**: `stimulus_icc` > 0.3 or `trial_order_autocorrelation` > 0.3 triggers `confound_severe:true` and halts the pipeline.  
- **Raw data immutable**; all derivations create new files with SHA‑256 hashes recorded.  
- **No synthetic stand‑ins**; all files are derived from the verified OpenIAT dataset.

---

