# Data Model: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## Overview

The data model captures every artifact produced by the pipeline, including the newly introduced pre‑registration, source‑identification, and representativeness artifacts, and the KS‑test result required for SC‑006.

## Entity Definitions

### 1. Pre‑Registration Manifest
* `registration_id`: UUID.
* `timestamp`: ISO‑8601 string.
* `primary_outcome`: string (e.g., `"tDCS motor performance percentage change"`).
* `hypothesis`: string.
* `analysis_plan`: list of planned steps (as strings).
* `registered_by`: string.

### 2. Verified Source Manifest
* `source_type`: Enum `["EEG", "tDCS"]`.
* `source_url`: string (verified URL).
* `checksum`: string (SHA‑256).
* `subject_count`: integer.
* `verification_status`: Enum `["available", "unavailable"]`.
* `notes`: optional string.

### 3. Raw Dataset Manifest (unchanged)
* `source_url`, `dataset_type`, `subject_count`, `checksum`, `ingestion_status` (as in `dataset.schema.yaml`).

### 4. Representativeness Summary (New)
* `demographics`: object (age_mean, age_sd, sex_ratio).
* `protocol_heterogeneity`: string (e.g., "High", "Low").
* `generalization_risk`: boolean.

### 5. EEG Epoch
* `subject_id`, `condition`, `channels`, `data` (2‑D array), `bad_channels`.

### 6. Feature Vector
* `subject_id`, `spectral_power` (delta‑gamma), `connectivity` (channel‑pair map), `tdcs_response`, `normality_flag`.

### 7. KS‑Test Result (new, for SC‑006)
* `statistic`: number.
* `p_value`: number.
* `interpretation`: string (e.g., `"null distribution uniform"`).

### 8. Analysis Result
* `mode`: Enum `["Primary", "Hypothesis_Unanswerable", "Underpowered", "Generalization_Unanswerable"]`.
* `reason`: string explaining the mode.
* `model_metrics`: object (may be `null` if not in Primary mode) – includes `adjusted_r2`, `permutation_p_value`, `fdr_corrected_p_values`, `ks_test_result`.
* `power_analysis`: object with `min_n_required`, `actual_n`, `status`.
* `sensitivity_table`: list of rows (`p_threshold`, `r_squared_threshold`, `significance`, `stability`).
* `manifest`: object mapping output metrics to input hashes and code block IDs (for Principle IV).

## Data Flow

1. **Pre‑registration** → `pre_registration.yaml`.
2. **Systematic Search** → logs candidate accession numbers.
3. **Source Identification** → `verified_eeg_source.json`, `verified_tdcs_source.json`.
4. **Ingestion Gate** → `Raw Dataset Manifest`.
5. **Representativeness Check** → `representativeness_summary.json`.
6. **Power & Feasibility Checks** → `power_analysis.json`.
7. **Preprocessing** → `EEG Epoch` files.
8. **Feature Extraction** → `Feature Vector` records.
9. **Modeling** (if Primary) → `model_metrics` (including KS test).
10. **Generalization Check** → secondary `model_metrics` (or log "Generalization Unanswerable").
11. **Manifest Generation** → `manifest.json` linking every output metric to its input hash and code block ID.

## Constraints

* No synthetic data generation.
* All data must stem from a single verified source unless the Generalization Check explicitly attempts a secondary independent paired dataset.
* Memory‑efficient chunking for large EEG files (≤7 GB RAM).
* All artifacts are immutable after creation; any transformation writes a new file with a documented derivation.