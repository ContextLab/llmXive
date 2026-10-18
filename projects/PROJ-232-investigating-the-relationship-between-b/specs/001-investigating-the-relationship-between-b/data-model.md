# Data Model: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Overview
Defines the input dataset schema (what the validation gate requires), the network‑metrics entity, the analysis‑output schema, and the Data‑Gap Report produced when required variables are absent.

**Note**: The schemas below are provisional pending a specification amendment that provides an open dataset containing paired resting‑state fMRI and MER scores (required for FR‑001, FR‑002, FR‑003). Until such a dataset is available, the pipeline will stop after the validation gate.

## Entity Definitions

### 1. Subject (required input row)
| Field | Type | Description | Constraints |
|---|---|---|---|
| `subject_id` | `str` | Unique participant ID | required, unique |
| `age` | `int` | Age in years | `0 < age < 120` |
| `sex` | `str` | `"M"` or `"F"` | enum |
| `fd_mean` | `float` | Mean framewise displacement (mm) | `>= 0`; rows with `fd_mean > 0.5` are excluded |
| `mer_score` | `float` | Music Emotion Rating total score | required for analysis; `>= 0` |
| `fc_upper_tri` | `array[number]` | Upper‑triangular FC values (including diagonal) | length = 20100 (200 × 201 / 2) |

### 2. ConnectivityMatrix
| Field | Type | Constraints |
|---|---|---|
| `subject_id` | `str` | FK to Subject |
| `matrix` | `list[list[float]]` | 200 × 200, symmetric, diagonal = 1.0, values ∈ [−1, 1] |
| `atlas` | `str` | `"Schaefer200"` |

### 3. NetworkMetrics
| Field | Type | Constraints |
|---|---|---|
| `subject_id` | `str` | FK |
| `global_efficiency` | `float` | `> 0` |
| `modularity` | `float` | `0 < value < 1` |
| `participation_coeff` | `float` | `0 ≤ value ≤ 1` |
| `dmn_efficiency` | `float` | `> 0` |
| `salience_efficiency` | `float` | `> 0` |
| `visual_efficiency` | `float` | `> 0` |
| `edge_strengths` | `array[float]` | Flattened upper‑triangular edge vector **after absolute‑value transformation and 10 % top‑edge thresholding** |
| `pca_components` | `array[float]` | Principal component scores derived from `edge_strengths` (explaining ≥ 80 % variance). |

### 4. AnalysisResult (output row)
| Field | Type | Constraints |
|---|---|---|
| `metric_name` | `str` | required |
| `correlation_r` | `float` | `[-1, 1]` |
| `p_value` | `float` | `[0, 1]` |
| `p_value_fdr` | `float` | `[0, 1]` |
| `significant` | `bool` | `p_value_fdr < 0.05` |
| `sample_size` | `int` | `> 0` |
| `power_achieved` | `float` | `[0, 1]` |

### 5. DataGapReport (produced when validation fails)
| Field | Type | Description |
|---|---|---|
| `missing_variables` | `array[str]` | Required variables absent from all sources |
| `per_file_columns` | `map[str, array[str]]` | Actual columns found in each downloaded file |
| `gate_passed` | `bool`` | `false` when required variables are missing |
| `timestamp` | `str` | ISO‑8601 run time |

## Data Flow
1. `download.py` → raw files + `data/checksums.json`
2. `validate.py` → `reports/data_gap_report.json` (halts) **or** validated subject table
3. `graph_metrics.py` → `results/network_metrics.csv`
4. `stats.py` → `results/analysis_results.csv`
5. `visualize.py` → `figures/`

## Validation Rules
- Matrix symmetry, diagonal = 1.0, and value range checks (unit‑tested).  
- Listwise exclusion of subjects with any missing required field; motion exclusion at `fd_mean > 0.5`.  
- VIF > 5 → predictor removal, logged.  
- Edge‑strength vectors are transformed to absolute values and thresholded before PCA.  
- No synthetic data may enter `data/`; test fixtures live under `tests/fixtures/` and are never emitted as results.

--- 

## Notes
- The PCA‑reduced components (`pca_components`) are the only edge‑derived predictors used in the Ridge regression (Task 2.2).  
- The Data‑Gap Report schema is defined in `contracts/data_gap_report.schema.yaml`.

--- 

## Future Work
The schemas are designed to accommodate the full dataset once it becomes available. Should the specification be revised to accept pre‑computed connectivity matrices only, the `fc_upper_tri` field can remain while the raw‑fMRI‑dependent steps (FR‑002, FR‑003) would be omitted.
