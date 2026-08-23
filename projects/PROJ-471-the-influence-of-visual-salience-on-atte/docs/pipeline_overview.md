# Pipeline Overview

This document describes the end-to-end data flow of the PROJ-471 pipeline.

## Phase 1: Ingestion (US1)
1. **Download**: `code/ingestion/download_data.py` fetches the dataset from Hugging Face.
2. **Salience Generation**: `code/ingestion/salience_gen.py` generates salience maps.
 - Primary: DeepGaze II (CPU mode).
 - Fallback: GBVS (if DeepGaze II fails).
3. **Validation**: `code/ingestion/completion_validator.py` checks that all images have maps and fallback frequency < 10%.
4. **Metadata**: `code/ingestion/metadata_writer.py` writes `data/processed/salience_maps/metadata.json`.

## Phase 2: Processing (US2)
1. **Segmentation**: `code/processing/segmentation.py` generates face masks using YOLOv8.
2. **Eye Tracking**: `code/processing/eye_tracking.py` parses raw eye-tracking data and calculates metrics (Dwell Time, Latency, etc.).
3. **Alignment**: `code/processing/alignment.py` merges salience scores with fixation metrics on `TrialID`.
4. **Output**: `data/processed/aligned_metrics.csv`.

## Phase 3: Analysis (US3)
1. **Power Analysis**: `code/analysis/lmm_power.py` estimates statistical power.
2. **VIF Check**: `code/analysis/vif_calc.py` verifies multicollinearity (confirms FR-009 exclusion).
3. **LMM Fitting**: `code/analysis/lmm_fit.py` fits Model A and Model B.
4. **FDR Correction**: `code/analysis/robustness.py` applies Benjamini-Hochberg correction.
5. **Sensitivity**: `code/analysis/plot_sensitivity.py` generates sensitivity plots.
6. **Results**: `code/analysis/write_final_results.py` writes `data/processed/results.json`.

## Artifacts
- **Input**: Raw eye-tracking data (OpenNeuro).
- **Intermediate**: Salience maps (`.npy`), Face masks (`.png`), Aligned metrics (`.csv`).
- **Output**: Final results (`.json`), Sensitivity plots (`.png`), Logs (`.log`).
