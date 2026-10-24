# Data Model: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

## Core Entities

| Entity | Key Fields | Description |
|--------|------------|-------------|
| **EEGDataset** | `dataset_id` (str), `raw_file_hash` (str), `subjects` (list[str]) | Metadata for the downloaded BIDS dataset. |
| **Subject** | `subject_id` (str), `is_excluded` (bool), `exclusion_reason` (str, opt), `artifact_rejection_rate` (float) | QC information per participant. |
| **Epoch** | `epoch_id` (str), `subject_id` (str), `condition_label` (enum: simple/complex), `stimulus_type` (enum: standard/deviant), `signal_data` (ndarray), `time_window` ([-0.2,0.5]), `baseline_corrected` (bool) | Individual trial segment. |
| **MMNMetric** | `metric_id` (str), `subject_id` (str), `electrode` (str), `condition_label` (enum), `amplitude_diff` (float), `latency_diff` (float), `snr_ratio` (float), `signal_validity` (bool), `t_statistic` (float, opt), `p_value_fdr` (float, opt), `cohen_d` (float, opt), `practical_significance` (bool, opt), `topographic_correlation` (float, opt), `validation_type` (enum: consistency_simple/validity_complex), `significant` (bool, opt), `covariates` (object, opt) | Aggregated per‑subject, per‑electrode result. |

## Transformations

1. **Download → Raw BIDS** (`download.py`): produces `EEGDataset` with checksum.  
2. **Raw → Processed Epochs** (`preprocess.py`): creates `Epoch` objects, stores as `.fif`.  
3. **Epochs → MMNMetric** (`analysis.py`): computes amplitudes, latencies, SNR, topographic correlations; writes `results/metrics.csv`.  
4. **Group Statistics** (`analysis.py`): aggregates across subjects, runs paired t‑tests, writes `results/stats.json`.  

## Constraints (derived from FRs)

* **Temporal Window**: All epochs must be exactly –200 ms → 500 ms.  
* **Baseline Correction**: `baseline_corrected` must be `True`.  
* **Signal Validity**: `signal_validity` must be `True` for any metric reported as “detected MMN”.  
* **Condition Independence**: `condition_label` comes directly from `events.tsv`; never inferred from `stimulus_type`.  
* **Topographic Validation**: `validation_type` distinguishes consistency vs. validity checks, preventing circularity.  
* **Covariate Recording**: When covariates are extracted, they are stored in the optional `covariates` field for downstream mixed‑effects modelling.  

---===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-250-neural-correlates-of-temporal-prediction/specs/001-neural-correlates-of-temporal-prediction/contracts/dataset.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "EEG Dataset Metadata Schema"
description: "Schema for validating per‑subject metadata required for MMN analysis."
type: object
properties:
  subject_id:
    type: string
    description: "Unique subject identifier (e.g., 'sub-01')."
  condition_label:
    type: string
    enum:
      - "simple"
      - "complex"
    description: "Experimental condition extracted from events.tsv."
  stimulus_type:
    type: string
    enum:
      - "standard"
      - "deviant"
    description: "Stimulus classification."
  is_valid:
    type: boolean
    description: "True if the subject passed QC (artifact rejection < 50%)."
  artifact_rejection_rate:
    type: number
    minimum: 0
    maximum: 100
    description: "Percentage of epochs rejected due to artifacts."
required:
  - subject_id
  - condition_label
  - stimulus_type
  - is_valid
  - artifact_rejection_rate
additionalProperties: false