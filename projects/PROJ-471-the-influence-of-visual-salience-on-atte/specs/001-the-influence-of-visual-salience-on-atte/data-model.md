# Data Model: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## 1. Entities

| Entity | Key attributes | Description |
|---|---|---|
| **StimulusImage** | `stimulus_id`, `file_path`, `salience_map_path`, `low_level_features` (luminance, contrast, edge_density), `status` | One moral-scenario image. |
| **SalienceMapMetadata** | `stimulus_id`, `map_path`, `resolution{height,width}`, `generation_method` (spectral_residual \| center_surround), `status` (success \| fallback_used \| failed), `excluded_reason` (nullable) | Per-image salience record. |
| **FixationTrial** | `trial_id`, `participant_id`, `stimulus_id`, `roi_type`, `dwell_time_ms`, `first_fixation_prob`, `fixation_latency_ms` | One gaze event per ROI. |
| **AnalysisResult** | `model_id`, `fixed_effect_estimate`, `p_value`, `p_value_fdr_corrected`, `confidence_interval`, `sensitivity_analysis`, `collinearity_report`, `power_status`, `disclaimer` | Statistical output. |

## 2. Data flow

1. **Raw** — `data/raw/ds003123/` (unchanged) + `data/raw/checksums.json` (SHA-256 per file; must be non-empty).
2. **Interim** — `salience_maps/*.npy`, `salience_metadata.json`, `masks/*.png`, `mask_metadata.csv`, `fixations.csv`.
3. **Processed** — `aligned_data.csv`, `results.json`.

## 3. Schemas

### 3.1 Aligned dataset (`contracts/dataset.schema.yaml`)
Columns: `trial_id` (string), `participant_id` (string), `stimulus_id` (string), `roi_type` (enum: face/weapon/background), `dwell_time_ms` (number), `first_fixation_prob` (number 0–1), `fixation_latency_ms` (number), `salience_score` (number), `luminance`, `contrast`, `edge_density` (numbers), `scene_complexity` (integer ≥ 0), `excluded` (boolean). All required. (Rows are validated as objects; the validator iterates CSV rows.)

### 3.2 Analysis results (`contracts/output.schema.yaml`)
Properties (all required): `model_id` (string), `fixed_effect_estimate` (number), `p_value` (0–1), `p_value_fdr_corrected` (0–1), `confidence_interval` ([lower, upper]), `sensitivity_analysis` {`model_a_estimate`, `model_b_estimate`, `stability_metric`}, `collinearity_report` {`pre_orthogonalization_vif`, `post_orthogonalization_vif`}, `power_status` (valid \| invalid), `disclaimer` (const "correlational only").

### 3.3 Salience metadata (`contracts/salience.schema.yaml`)
Properties (all required): `stimulus_id`, `map_path`, `resolution{height≥1, width≥1}`, `generation_method` (enum: spectral_residual, center_surround), `status` (enum: success, fallback_used, failed), `excluded_reason` (string or null).
