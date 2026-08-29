# Data Model: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## Entities

### AudioClip
- **audio_id**: str (unique identifier)
- **source_dataset**: str (e.g., "ami", "librispeech")
- **speaker_id**: str (if available)
- **duration_sec**: float
- **sample_rate**: int
- **checksum**: str (SHA‑256 of raw audio)
- **simulated_rt60**: float (Synthetic reverberation time generated via pyroomacoustics)
- **simulated_room_volume**: float (Synthetic room volume generated via pyroomacoustics)

### DistortionVector
- **vector_id**: str (unique identifier)
- **snr_db**: float (Signal‑to‑noise ratio in dB)
- **rt60_sec**: float (Reverberation time in seconds)
- **distortion_type**: str ("reverberation+noise")
- **intensity_level**: int (1‑54, based on grid position)
- **simulated_room_volume**: float (Synthetic room volume for stratification)

### StressCurve
- **curve_id**: str (unique identifier)
- **audio_id**: str (FK to AudioClip)
- **model_id**: str (e.g., "whisper‑tiny")
- **vector_id**: str (FK to DistortionVector)
- **ss_score**: float (Semantic Similarity Score, 0‑1)
- **wer**: float (Word Error Rate)
- **hypothesis**: str (ASR output)
- **reference_transcript**: str
- **timestamp**: datetime

### CollapseIntensity
- **collapse_id**: str (unique identifier)
- **audio_id**: str (FK to AudioClip)
- **model_id**: str (FK to ASR model)
- **collapse_intensity**: float or string ("None") – distortion intensity at collapse
- **collapse_type**: str (enum: "threshold_crossing", "inflection_point", "none", "total_failure", "noise_floor")
- **ss_at_collapse**: float (0‑1)
- **wer_at_collapse**: float
- **baseline_wer**: float (WER on clean audio)
- **normalized_inflection_coord**: float or null – relative position of the inflection point in the normalized SNR/RT60 space (0‑1). Null if no inflection detected.  
- **sigmoid_slope**: float – slope of the fitted sigmoid at the inflection point (null if undefined).  

### CriticalInteractionVector
- **vector_id**: str (unique identifier)
- **model_id**: str (FK to ASR model)
- **snr_coeff**: float
- **rt60_coeff**: float
- **snr_sq_coeff**: float
- **rt60_sq_coeff**: float
- **interaction_coeff**: float (SNR × RT60)
- **r2_score**: float
- **mae**: float
- **p_value_interaction**: float (FDR‑corrected)
- **shap_interaction_strength**: float

## Relationships

- **AudioClip** → **StressCurve** (1:N)  
- **DistortionVector** → **StressCurve** (1:N)  
- **StressCurve** → **CollapseIntensity** (1:1)  
- **CollapseIntensity** → **CriticalInteractionVector** (N:1, aggregated by model_id)

## Data Flow

1. **Raw Data**: Download from verified Hugging Face datasets (AMI test, LibriSpeech test.clean).
2. **Stratification**: Generate synthetic RIRs via `pyroomacoustics` to create `simulated_rt60` and `simulated_room_volume`; assign each clip to a stratum.
3. **Distortion**: Generate scenarios per clip (synthetic).
4. **Inference**: Run ASR models; store hypotheses.
5. **Metrics**: Compute SSS (MiniLM v2) and WER.
6. **Collapse Detection**: Apply FR‑021 algorithm with smoothing and **morphology check**; if noise floor, set `collapse_type: 'noise_floor'`. If no inflection, set `normalized_inflection_coord` and `sigmoid_slope` to null. Empty hypothesis before step 1 → `collapse_type` "total_failure".
7. **Regression**: Train hierarchical model on `normalized_inflection_coord` and `sigmoid_slope` (targets) using predictors from `DistortionVector` and model architecture features.
8. **Validation**: SHAP analysis, sensitivity sweeps.
9. **Output**: Store all derived entities in `data/derived/` as Parquet files, each validated against its contract.

## Constraints

- **Checksums**: All raw files checksummed; derivations written to new files (Constitution III).
- **No PII**: No personal data in any artifact.
- **Immutable Raw Data**: Raw audio never modified; distortions produce new files.
- **Streaming**: Large datasets processed in batches to stay within 7 GB RAM.
- **Audit Trail**: All metric values logged with timestamps; hashes recorded in `state.yaml`.
- **Synthetic Vectors**: `snr_db` and `rt60_sec` are generated internally; not sourced externally.