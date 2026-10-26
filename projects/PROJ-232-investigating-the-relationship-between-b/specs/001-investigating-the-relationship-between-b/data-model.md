# Data Model: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Overview
Defines the input dataset schema, derived network‑metric entities, analysis‑output schema, and the Data‑Gap Report schema used when required variables are missing. All schemas are expressed as JSON‑Schema drafts and are enforced by the contract tests.

## Entity Definitions

### 1. Subject (required input row)
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `subject_id` | `string` | Unique participant identifier | required, unique |
| `age` | `integer` | Age in years | `0 < age < 120` |
| `sex` | `string` | `"M"` or `"F"` | enum |
| `fd_mean` | `number` | Mean framewise displacement (mm) | `≥ 0`; rows with `fd_mean > 0.5` are excluded |
| `mer_score` | `number` | Music Emotion Rating total score (behavioral outcome). **Note:** The MER instrument used in the external datasets has not been independently validated for musical‑emotion perception; this constitutes a limitation of the current analysis. | `≥ 0` |
| `fc_upper_tri` | `array[number]` | Upper‑triangular elements (including diagonal) of the 200 × 200 functional connectivity matrix | length = 20100 (`200 × 201 / 2`) |

### 2. ConnectivityMatrix
| Field | Type | Constraints |
|-------|------|-------------|
| `subject_id` | `string` | FK to Subject |
| `matrix` | `list[list[number]]` | 200 × 200, symmetric, diagonal = 1.0, values ∈ [−1, 1] |
| `atlas` | `string` | `"Schaefer200"` |

### 3. NetworkMetrics
| Field | Type | Constraints |
|-------|------|-------------|
| `subject_id` | `string` | FK |
| `global_efficiency` | `number` | `> 0` |
| `modularity` | `number` | `0 < value < 1` |
| `participation_coeff` | `number` | `0 ≤ value ≤ 1` |
| `dmn_efficiency` | `number` | `> 0` |
| `salience_efficiency` | `number` | `> 0` |
| `visual_efficiency` | `number` | `> 0` |
| `edge_strengths` | `array[number]` | Flattened upper‑triangular edge vector after absolute‑value transformation and 10 % top‑edge thresholding |
| `pca_components` | `array[number]` | Principal component scores derived from `edge_strengths` (explaining ≥ 80 % variance) |

### 4. AnalysisResult (output row)
| Field | Type | Constraints |
|-------|------|-------------|
| `metric_name` | `string` | e.g., `"global_efficiency"` |
| `correlation_r` | `number` | `[-1, 1]` |
| `p_value` | `number` | `[0, 1]` |
| `p_value_fdr` | `number` | `[0, 1]` |
| `significant` | `boolean` | `True if p_value_fdr < 0.05` |
| `sample_size` | `integer` | `> 0` |
| `power_achieved` | `number` | `[0, 1]` |
| `required_N` | `integer` | Minimum sample size needed for r ≥ 0.20, power ≥ 0.80, α = 0.05 |
| `actual_N` | `integer` | Number of subjects used in the analysis |

### 5. DataGapReport (produced when validation fails)
| Field | Type | Description |
|-------|------|-------------|
| `gate_passed` | `boolean` | `false` when required variables are missing from all sources |
| `missing_variables` | `array[string]` | List of required variables absent from **all** downloaded files |
| `per_file_columns` | `object` (map of filename → `array[string]`) | Actual column names found in each file |
| `timestamp` | `string` | ISO‑8601 timestamp of the validation run |
| `matched_proportion` | `number` | Proportion of HCP subjects successfully matched to MER scores (0 – 1) |
| `match_confidence_scores` | `object` (map of subject_id → `number`) | Confidence score (0‑1) based on age + sex agreement |
| `metric_completion_proportion` | `number` | Proportion of matched subjects with all required network metrics computed (0 – 1) |

## Data Flow
1. `download.py` → raw files + `data/checksums.json`  
2. `validate.py` → `reports/data_gap_report.json` (halts) **or** validated subject table (`results/validated_subjects.parquet`)  
3. `graph_metrics.py` → `results/network_metrics.csv` (validated against `network_metrics.schema.yaml` if present)  
4. `stats.py` → `results/analysis_results.csv`  
5. `visualize.py` → `figures/` (scatter, bar charts)  

## Validation Rules
- **Matrix integrity**: symmetry, diagonal = 1.0, values ∈ [−1, 1].  
- **Listwise exclusion** of any subject missing a required field; motion exclusion at `fd_mean > 0.5`.  
- **VIF screening**: predictors with VIF > 5 are dropped; logged.  
- **Edge‑weight handling**: absolute values → top 10 % threshold → PCA (≥ 80 % variance).  
- **No synthetic data** may be written to `data/`; test fixtures reside under `tests/fixtures/` only.
- **Conditional Success Criteria**: SC‑006 (matched proportion) and SC‑007 (metric‑completion proportion) are evaluated **only when a compliant dataset is available**. If the validation gate fails, these criteria are not required and are omitted from the final report.

## Future Work
If the specification is revised to accept pre‑computed connectivity matrices only, the `fc_upper_tri` field remains, while FR‑002/FR‑003 (raw‑fMRI‑dependent steps) are omitted. The schemas are already compatible with that scenario.  

---



