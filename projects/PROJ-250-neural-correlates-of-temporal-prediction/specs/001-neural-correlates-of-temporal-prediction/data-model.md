# Data Model: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis  

## Core Entities  

| Entity | Key Fields | Description |
|--------|------------|-------------|
| **EEGDataset** | `dataset_id` (str), `raw_file_hash` (str), `subjects` (list[str]) | Metadata for the downloaded BIDS dataset. |
| **Subject** | `subject_id` (str), `is_excluded` (bool), `exclusion_reason` (str, opt), `artifact_rejection_rate` (float) | QC information per participant. |
| **Epoch** | `epoch_id` (str), `subject_id` (str), `condition_label` (enum: simple/complex), `stimulus_type` (enum: standard/deviant), `signal_data` (ndarray), `time_window` ([-0.2,0.5]), `baseline_corrected` (bool) | Individual trial segment. |
| **MMNMetric** | `metric_id` (str), `subject_id` (str), `electrode` (str), `condition_label` (enum), `amplitude_diff` (float), `latency_diff` (float), `snr_ratio` (float), `signal_validity` (bool), `t_statistic` (float, opt), `p_value_fdr` (float, opt), `cohen_d` (float, opt), `practical_significance` (bool, opt), `topographic_correlation` (float, opt), `validation_type` (enum: consistency_simple/validity_complex), `significant` (bool, opt), `window_start` (float), `window_end` (float), `benchmark_reference` (string) | Per‑subject, per‑electrode MMN results, including topographic consistency/validity checks. |
| **GroupStats** | `test_name` (str), `t_statistic` (float), `p_value_raw` (float), `p_value_fdr` (float), `cohen_d` (float), `effect_size_benchmark` (float), `practical_significance` (bool), `topographic_consistency_r` (float), `topographic_validity_r` (float) | Aggregated statistics for the cohort. |
| **Covariate** (optional) | `name` (str), `values` (list[float]) | Stimulus‑level variables (e.g., deviant probability, ISI) that can be included in mixed‑effects modelling. |

## Transformations  

1. **Download → EEGDataset** (`download.py`) → creates `EEGDataset` record, stores SHA‑256 checksums.  
2. **Raw → Epoch** (`preprocess.py`) → generates `Epoch` objects saved as `.fif`; populates `Subject` entries with QC flags.  
3. **Epochs → MMNMetric** (`analysis.py`) → computes amplitudes, latencies, SNR, topographic correlations; writes `results/metrics.csv`.  
4. **Group Statistics** (`analysis.py`) → runs paired t‑tests, FDR, effect‑size benchmark; writes `results/stats.json`.  
5. **Optional Covariate Modelling** (`analysis.py`) → fits mixed‑effects model using `Covariate` data when present.  

## Constraints (derived from FRs)  

* **Temporal Window**: All epochs must span –200 ms → 500 ms.  
* **Baseline Correction**: `baseline_corrected` must be `True`.  
* **Signal Validity**: `signal_validity` must be `True` for any metric that proceeds to group analysis (SNR ≥ 3).  
* **Condition Independence**: `condition_label` is taken directly from `events.tsv`; never inferred.  
* **Topographic Validation**: `validation_type` distinguishes consistency (simple) vs. validity (complex) checks, avoiding circularity.  
* **Covariate Availability**: If stimulus‑level covariates exist, they are stored in `Covariate` entities and used in the mixed‑effects model; otherwise the field is omitted.  
* **Artifact Handling**: Subjects with > 50 % rejected epochs are marked `is_excluded = True` and omitted from group‑level analyses.  
* **Missing Channels**: Interpolated channels are reflected in the `Epoch` data; original missing‑channel count must be ≤ 10 % to permit interpolation.  

These entities are referenced explicitly in the **Implementation Phases** of `plan.md` to ensure full alignment between the plan and the data model.  

---

