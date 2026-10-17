# Data Model: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## 1. Entity Overview
| Entity | Key Attributes | Description |
|---|---|---|
| **StimulusImage** | `stimulus_id`, `file_path`, `salience_map_path`, `low_level_features` (luminance, contrast, edge_density), `status` | One of the moral‑scenario images. |
| **SalienceMapMetadata** | `stimulus_id`, `map_path`, `resolution` (height, width), `generation_method` (gbvs, deepgaze_ii, gbvs_fallback), `status` (success, fallback_used, failed), `excluded_reason` (nullable) | Metadata for each generated salience map; tracks generation method and fallback usage. |
| **FixationTrial** | `trial_id`, `participant_id`, `stimulus_id`, `roi_type`, `dwell_time_ms`, `first_fixation_prob`, `fixation_latency_ms` | One eye‑tracking event for a given ROI. |
| **AnalysisResult** | `model_id`, `fixed_effect_estimate`, `p_value`, `p_value_fdr_corrected`, `confidence_interval`, `sensitivity_analysis`, `disclaimer`, `power_status` | Output of the statistical analysis. |

## 2. Data Flow
1. **Raw** – `data/raw/ds003123/` (unchanged, manually placed).  
2. **Interim** –  
   - `data/interim/salience_maps/` (`.npy` per image).  
   - `data/interim/salience_metadata.json` (SalienceMapMetadata records for all images).  
   - `data/interim/masks/` (`.png` masks).  
   - `data/interim/fixations.csv` (parsed eye‑tracking).  
3. **Processed** –  
   - `data/processed/aligned_data.csv` (merged dataset).  
   - `data/processed/results.json` (final statistical output).

## 3. Schemas
### 3.1 Aligned Dataset Schema (`contracts/dataset.schema.yaml`)
| Column | Type | Description |
|---|---|---|
| `trial_id` | string | Unique identifier for the trial |
| `participant_id` | string | Participant identifier |
| `stimulus_id` | string | Stimulus image identifier |
| `roi_type` | string (enum) | `"face"`, `"weapon"`, or `"background"` |
| `dwell_time_ms` | number | Dwell time (ms) |
| `first_fixation_prob` | number (0‑1) | Probability of first fixation |
| `fixation_latency_ms` | number | Fixation latency (ms) |
| `salience_score` | number | Mean salience within ROI |
| `luminance` | number | Average luminance (diagnostic) |
| `contrast` | number | Average contrast (diagnostic) |
| `edge_density` | number | Edge density (diagnostic) |
| `moral_valence` | number or string | Moral valence (numeric sentiment score or binary moral/neutral) |
| `scene_complexity` | integer | Number of detected objects in scene |
| `excluded` | boolean | `True` if trial excluded from analysis |

**Required**: all columns above.

### 3.2 Analysis Results Schema (`contracts/output.schema.yaml`)
| Property | Type | Notes |
|---|---|---|
| `model_id` | string | Identifier for the model run |
| `fixed_effect_estimate` | number | Estimate for the salience predictor (post-orthogonalization if applied) |
| `p_value` | number (0‑1) | Raw p‑value |
| `p_value_fdr_corrected` | number (0‑1) | FDR‑adjusted p‑value |
| `confidence_interval` | array[2] of number | 95 % CI `[lower, upper]` |
| `sensitivity_analysis` | object | `model_a_estimate`, `model_b_estimate`, `stability_metric` |
| `collinearity_report` | object | `pre_orthogonalization_vif`, `post_orthogonalization_vif` (if applied) |
| `disclaimer` | string (const) | Must be `"correlational only"` |
| `power_status` | string (enum) | `"valid"` or `"invalid"` (result of power check) |

**Required**: all properties above.

### 3.3 Salience Map Metadata Schema (`contracts/salience.schema.yaml`)
| Property | Type | Details |
|---|---|---|
| `stimulus_id` | string | Image identifier |
| `map_path` | string | Path to `.npy` salience map |
| `resolution` | object (`height`: int ≥ 1, `width`: int ≥ 1) | Spatial resolution |
| `generation_method` | string (enum) | `"gbvs"`, `"deepgaze_ii"`, or `"gbvs_fallback"` |
| `status` | string (enum) | `"success"`, `"fallback_used"`, or `"failed"` |
| `excluded_reason` | string (nullable) | Reason for failure, if any |

All schemas are located in `contracts/` and are used by `final_validator.py` to enforce correctness of the pipeline outputs.
