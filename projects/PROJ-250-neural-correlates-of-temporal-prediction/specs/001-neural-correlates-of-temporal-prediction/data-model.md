# Data Model: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

## Core Entities

| Entity | Key Fields | Description |
|--------|------------|-------------|
| **EEGDataset** | `dataset_id` (str), `raw_file_hash` (str), `subjects` (list[str]) | Metadata for the downloaded BIDS dataset. |
| **Subject** | `subject_id` (str), `is_excluded` (bool), `exclusion_reason` (str, opt), `artifact_rejection_rate` (float) | QC information per participant. |
| **Epoch** | `epoch_id` (str), `subject_id` (str), `condition_label` (enum: simple/complex), `stimulus_type` (enum: standard/deviant), `signal_data` (ndarray), `time_window` ([-0.2,0.5]), `baseline_corrected` (bool) | Individual trial segment. |
| **MMNMetric** | `metric_id` (str), `subject_id` (str), `electrode` (str), `condition_label` (enum), `amplitude_diff` (float), `latency_diff` (float), `snr_ratio` (float), `signal_validity` (bool), `t_statistic` (float, opt), `p_value_fdr` (float, opt), `cohen_d` (float, opt), `practical_significance` (bool, opt), `topographic_correlation` (float, opt), `validation_type` (enum: consistency_simple/validity_complex), `significant` (bool, opt), `covariates` (object, opt), `window_start` (float), `window_end` (float), `benchmark_reference` (string) | Aggregated per‑subject, per‑electrode result. |

## Transformations

1. **Download → Raw BIDS** (`download.py`) → creates `EEGDataset` with checksum.  
2. **Raw → Processed Epochs** (`preprocess.py`) → generates `Epoch` objects saved as `.fif`.  
3. **Epochs → MMNMetric** (`analysis.py`) → computes amplitudes, latencies, SNR, topographic correlations; writes `results/metrics.csv`.  
4. **Group Statistics** (`analysis.py`) → aggregates across subjects, runs paired t‑tests; writes `results/stats.json`.  

## Constraints (derived from FRs)

* **Temporal Window**: All epochs must begin at a pre‑stimulus interval and extend to a post‑stimulus interval of sufficient duration to capture the relevant neural response.  
* **Baseline Correction**: `baseline_corrected` must be `True`.  
* **Signal Validity**: `signal_validity` must be `True` for any reported MMN.  
* **Condition Independence**: `condition_label` is taken directly from `events.tsv`; never inferred.  
* **Topographic Validation**: `validation_type` distinguishes consistency (simple) vs. validity (complex) checks, avoiding circularity.  
* **Covariate Recording**: When present, covariates are stored in the optional `covariates` field for downstream mixed‑effects modelling.  

---



