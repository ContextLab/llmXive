# Data Model: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

## Overview
The data model defines all entities that flow from raw acquisition to final results, ensuring traceability and compliance with the constitution’s “Single Source of Truth” principle.

## Entities

### 1. Participant
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `id` | string | Unique identifier (e.g., `sub-001`). | Primary key, non‑null. |
| `heat_pain_threshold` | number | Heat‑pain threshold in °C. | Non‑null, > 0. |
| `age` | integer | Age in years. | Optional. |
| `gender` | string | Gender (categorical). | Optional. |
| `valid_eeg_minutes` | number | Minutes of clean EEG after ICA. | Must be ≥ 4.0 for inclusion. |
| `exclusion_reason` | string | Reason for exclusion (e.g., “< 4 min post‑ICA”). | Null if included. |

### 2. DataChunk
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `chunk_id` | integer | Unique chunk identifier. | Primary key. |
| `participant_id` | string | FK → Participant.id. | Non‑null. |
| `data_path` | string | Path to memory‑mapped EEG segment. | Non‑null. |
| `start_time` | number | Start time (s) of chunk. | Non‑null. |
| `end_time` | number | End time (s) of chunk. | Non‑null, `end_time > start_time`. |
| `status` | string | Enum {`loaded`, `processed`, `excluded`}. | Non‑null. |

*The **DataChunk** entity is used in Phase 1 preprocessing to stream raw EEG files in ≤ 2 GB batches, satisfying the memory constraints of the CI runner.*

### 3. MicrostateFeature
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `participant_id` | string | FK → Participant.id. | Non‑null. |
| `feature_name` | string | One of the canonical names (see schema). | Enum, non‑null. |
| `value` | number | Feature value (normalized). | Non‑null, no NaNs. |
| `standard_error` | number | Standard error (if computed). | Optional, ≥ 0. |

### 4. ModelResult
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `run_id` | string | UUID for the model run. | Primary key. |
| `pearson_r` | number | Correlation between predictions & true thresholds. | Non‑null, –1 ≤ ≤ 1. |
| `p_value` | number | Empirical p‑value from global permutation test. | 0 ≤ ≤ 1. |
| `mae` | number | Mean Absolute Error. | Non‑null, ≥ 0. |
| `ci_lower` | number | Lower bound of 95 % bootstrap CI for r. | Non‑null. |
| `ci_upper` | number | Upper bound of 95 % bootstrap CI for r. | Non‑null, ≥ ci_lower. |
| `n_permutations` | integer | Number of permutations performed. | ≥ 1000 (or 500 if runtime limited). |
| `n_bootstrap` | integer | Number of bootstrap resamples. | ≥ 200. |

### 5. DiagnosticReport
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `feature_name` | string | FK → MicrostateFeature.feature_name. | Non‑null. |
| `coefficient` | number | Elastic Net coefficient. | Non‑null. |
| `importance_score` | number | Permutation importance. | Non‑null. |
| `p_value_raw` | number | Raw p‑value from permutation importance. | 0 ≤ ≤ 1. |
| `p_value_fdr` | number | FDR‑adjusted p‑value. | 0 ≤ ≤ 1. |
| `vif` | number | Variance Inflation Factor. | ≥ 1. |
| `is_significant` | boolean | `p_value_fdr < 0.05`. | Derived. |
| `is_collinear` | boolean | `vif > 10`. | Derived. |

## Data Flow
1. **Raw ingestion** → `Participant` + `DataChunk` (EEG files).  
2. **Preprocessing** → `MicrostateFeature` (30 per participant).  
3. **Feature matrix** (`data/processed/feature_matrix.csv`) derived from `MicrostateFeature` + `heat_pain_threshold` + covariates (`age`, `gender`, `valid_eeg_minutes`).  
4. **Modeling** → `ModelResult` (`artifacts/model_results.json`).  
5. **Diagnostics** → `DiagnosticReport` (`artifacts/diagnostics.csv`) + `sensitivity_report.md`.  

## Validation Rules
- No NaNs in `feature_matrix.csv`.  
- Every `MicrostateFeature.participant_id` exists in `Participant`.  
- Participants with `valid_eeg_minutes < 4.0` are excluded before feature extraction.  
- `heat_pain_threshold` must lie within physiological bounds (35 °C – 55 °C).  
- All output files must conform to their respective JSON/YAML schemas in `contracts/`.  
