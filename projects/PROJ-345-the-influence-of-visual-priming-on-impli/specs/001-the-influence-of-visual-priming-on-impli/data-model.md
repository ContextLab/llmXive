# Data Model: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## 1. Entity Overview

| Entity | Primary Attributes | Description |
|---|---|---|
| **Participant** | `participant_id` (string), optional `age`, `gender`, `education` | Unique subject; demographics may be missing. |
| **Trial** | `trial_id`, `participant_id`, `response_time`, `stimulus_id`, `prime_valence`, `stimulus_ambiguity`, `linkage_status`, `demographics_status` | One observation linking participant to stimulus under a prime condition. |
| **Stimulus** | `stimulus_id`, `type` (image/word), `prime_or_target`, valence, ambiguity | Stored separately in `data/primes/` and `data/targets/` (Constitution VI); merged only at modeling. |

## 2. Schemas

### 2.1 Processed Trial Schema (`data/processed/linked_trials.csv`)
| Column | Type | Constraints |
|---|---|---|
| `trial_id` | string | unique |
| `participant_id` | string | FK → Participant |
| `response_time` | number (ms) | > 0 |
| `prime_valence` | number | ∈ [-1.0, 1.0]; **retained as empty column in valence-only scope** |
| `stimulus_ambiguity` | number | ∈ [0.0, 1.0]; **retained as empty column if unavailable** |
| `stimulus_id` | string | FK → Stimulus |
| `linkage_status` | string | `linked` \| `missing_image` \| `missing_metadata` |
| `demographics_status` | string | `complete` \| `missing_age` \| `missing_gender` \| `missing_education` \| `missing_all` |

### 2.2 Metadata Mapping (`data/processed/metadata_mapping.csv`, produced by T004)
| Column | Type | Description |
|---|---|---|
| `stimulus_id` | string | Stimulus identifier |
| `type` | string | `image` \| `word` |
| `file_path_or_word` | string | Path under `data/primes/` / `data/targets/`, or the word string |
| `prime_or_target` | string | `prime` \| `target` |

### 2.3 Linkage Status Artifact (`state/linkage_status.json`)
```json
{
  "status": "PASS|WARN|HALT",
  "percentage": 0.0,
  "threshold": 95.0,
  "message": "string"
}
```

### 2.4 Analysis Scope Artifact (`state/analysis_scope.json`)
```json
{ "scope": "full|valence_only", "reason": "string" }
```

### 2.5 Model Convergence Metrics (`state/model_convergence_metrics.json`)
| Field | Type | Description |
|---|---|---|
| `convergence_rate` | number ∈ [0,1] | successful fits / attempts |
| `total_attempts` | integer ≥ 1 | optimizer tries |
| `successful_runs` | integer ≥ 0 | converged fits |
| `failed_runs` | integer ≥ 0 | failed fits |
| `optimizer_settings` | array of strings | each optimizer attempted |

### 2.6 Model Result Dict (in-memory + `state/model_results.json`)
Keys include all `MixedLM` fixed effects, `robust_se`, `p_values`, `fdr_corrected_p`, and the **exact framing keys** `caution_note` and `limitation_note` (literal strings defined in plan T010), plus `effect_sizes` (`cohens_d`, `partial_eta_squared`, each with bootstrap CI).

### 2.7 VIF Flag (`state/vif_flag.json`)
| Field | Type |
|---|---|
| `flagged` | boolean (any VIF > 5.0) |
| `vif_values` | object (predictor → number) |
| `claim_suppressed` | boolean |
| `message` | string |

### 2.8 Verified Sources (`data/verified_sources.json`) — authoritative URL registry
```json
{ "sources": [ { "name": "string", "url": "string", "format": "string" } ] }
```
If `research.md` and this file disagree, **this file is authoritative** for URL validation.

### 2.9 Sensitivity Analysis (`reports/sensitivity_analysis.csv`)
| Column | Type |
|---|---|
| `alpha_level` | number |
| `significant_tests` | integer |
| `total_tests` | integer |
| `conclusion` | string |

## 3. Data Flow

1. Ingest (hardcoded URL) → `data/raw/iat.parquet` (+ checksum)
2. Core-column validation → halt on `Data Gap: Schema Mismatch` (expected given §2 audit)
3. Metadata extraction → `data/primes/`, `data/targets/`, `metadata_mapping.csv`
4. Linkage metric + gate → `ingest_metrics.json`, `linkage_status.json`
5. Derivations → `ambiguity_scores.csv`, `valence_scores.csv`
6. Merge → `linked_trials.csv` (+ `analysis_scope.json`)
7. VIF pre-check → `vif_flag.json`
8. LME fit with optimizer fallback → `model_results.json`, `model_convergence_metrics.json`
9. FDR + framing + effect sizes → augmented results
10. Sensitivity sweep → `sensitivity_analysis.csv`
11. Plots + PDF (always produced; data-gap report if halted) → `final_report.pdf`
12. PII scan → `pii_scan.json`; contract validation via pytest

## 4. Constraints & Validation Rules

- Linkage `percentage` ≥ `threshold` (default 95.0, from `config.py`), else HALT.
- `prime_valence` ∈ [-1, 1]; `stimulus_ambiguity` ∈ [0, 1].
- PII scan: `participant_id` must not match email/phone/SSN/full-name regexes.
- VIF > 5.0 → `claim_suppressed: true`.
- Missing covariates → omitted from model, flagged, never imputed.
- Raw data immutable; all derivations write new files; SHA-256 checksums in `state/artifact_hashes.json`.
