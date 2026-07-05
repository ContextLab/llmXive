# Data Sources and Acquisition

This document details the external data sources used by the pipeline, including
acquisition methods, validation criteria, and fallback strategies.

## Primary Source: Sleep-EDF Dataset

- **Repository**: PhysioNet
- **Dataset ID**: `sleep-edf`
- **URL**: `
- **Access Method**: `mne.datasets.sleep_edf` or direct HTTP fetch via `code/download.py`
- **Required Variables**:
 - Resting-state EEG channels (Fpz-Cz, Pz-Oz)
 - Paired pre- and post-fatigue subjective ratings (if available)
- **Validation**:
 - Checksum verification of downloaded files.
 - Presence of required metadata fields.
 - Minimum N ≥ 30 participants with complete data.

## Fallback Source: SHHS Dataset

- **Repository**: National Sleep Research Resource (NSRR)
- **Dataset ID**: `shhs`
- **Access Method**: Download via NSRR portal or `code/download.py` fallback logic
- **Usage Condition**: Only used if Sleep-EDF lacks required variables or yields N < 30.
- **Validation**: Same as Sleep-EDF; if both sources fail N ≥ 30 check, the pipeline
 halts with exit code 1 and generates `validation_report.json`.

## Data Storage Structure

- **Raw Data**: `data/raw/`
 - Unmodified downloaded files (e.g., `.edf`, `.gdf`).
- **Processed Data**: `data/processed/`
 - Filtered, artifact-rejected epochs and extracted features.
- **Analysis Data**: `data/analysis/`
 - Correlation matrices, sensitivity tables, and final metrics.

## Data Privacy and Compliance

- All data is anonymized at the source (PhysioNet/NSRR).
- No PII (Personally Identifiable Information) is stored or processed.
- PII scan implemented in `code/security.py` (Task T028).
