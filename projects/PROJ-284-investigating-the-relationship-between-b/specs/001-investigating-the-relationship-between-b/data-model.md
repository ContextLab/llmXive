# Data Model: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Sensorimotor Performance

## Overview

This document defines the data structures, schemas, and file formats used in the project. It ensures the "Single Source of Truth" principle by strictly defining how data flows from raw acquisition to final analysis.

## Entity Definitions

### 1. Subject
Represents a single participant in the HCP dataset.
- **Attributes**:
  - `subject_id`: Unique string identifier (e.g., "100307").
  - `age`: Integer.
  - `sex`: String ("M", "F").
  - `motor_score`: Float (Motor Task Performance composite score - measure of motor execution).
  - `fd_mean`: Float (Mean Framewise Displacement).
  - `tsnr_mean`: Float (Mean tSNR).
  - `quality_pass`: Boolean (True if tSNR ≥ 50 and FD < 0.5mm).

### 2. ConnectivityMatrix
A symmetric 400x400 matrix representing functional connectivity.
- **Format**: `numpy.ndarray` (float32) or `pandas.DataFrame`.
- **Shape**: (400, 400).
- **Properties**: Symmetric, diagonal = 0 (or 1 if self-correlation kept, but typically 0 for graph metrics).

### 3. NetworkMetric
A scalar value derived from a connectivity matrix.
- **Attributes**:
  - `subject_id`: String.
  - `metric_name`: String ("modularity", "participation_coeff", "within_module_degree").
  - `value`: Float.
  - `atlas`: String ("Schaefer_400").

### 4. CorrelationResult
The output of the statistical analysis.
- **Attributes**:
  - `metric_name`: String.
  - `correlation_coefficient`: Float (r).
  - `p_value`: Float (uncorrected).
  - `p_value_corrected`: Float (q, FDR).
  - `significant`: Boolean (q < 0.05).
  - `covariate_controlled`: Boolean (True if FD was controlled).

## File Formats

### Raw Data (`data/raw/`)
- **Behavioral**: `behavioral_metadata.json` (from HCP verified source).
- **fMRI**: `sub-<ID>_rest.nii.gz` (NIfTI-1 format).
- **Checksums**: `data/raw/checksums.txt` (SHA-256 hashes).

### Processed Data (`data/processed/`)
- **Preprocessed fMRI**: `sub-<ID>_preproc.nii.gz` (Minimal Preprocessed, no re-processing).
- **Motion Parameters**: `sub-<ID>_fd.csv` (FD per volume).

### Analysis Data (`data/analysis/`)
- **Connectivity Matrices**: `sub-<ID>_connectivity.npy` (NumPy binary).
- **Metrics Table**: `metrics_summary.csv` (Columns: subject_id, modularity, participation, within_module, motor_score, fd_mean).
- **PCA Loadings**: `pca_loadings.csv` (T023a) - Loadings for exactly 2 components.
- **PCA Factor Scores**: `factor_scores.csv` (T023a) - 2 factor scores per subject.
- **Full Metrics**: `full_metrics.csv` (T023b) - Merged metrics + PCA scores.
- **Correlation Results**: `correlation_results.csv` (Columns: metric, r, p, q, significant).
- **Power Analysis**: `power_analysis.json`.

## Data Flow Diagram

1. **Download**: `fetch_hcp_data.py` → `data/raw/behavioral_metadata.json`, `data/raw/sub-*/rest.nii.gz`.
2. **Preprocess**: `run_preprocessing.py` → `data/processed/sub-*/preproc.nii.gz`, `data/processed/sub-*/fd.csv`.
3. **QC**: Filter subjects based on tSNR/FD → `data/analysis/subjects_included.csv`.
4. **Connectivity**: `compute_connectivity.py` → `data/analysis/sub-*/connectivity.npy`.
5. **Metrics**: `extract_metrics.py` → `data/analysis/metrics_summary.csv`.
6. **PCA**: `run_pca_on_metrics.py` → `data/analysis/pca_loadings.csv`, `data/analysis/factor_scores.csv`.
7. **Merge**: `correlations.py` → `data/analysis/full_metrics.csv`.
8. **Correlation**: `correlations.py` → `data/analysis/correlation_results.csv`.
9. **Viz/Report**: `plot_scatter.py`, `report_generator.py` → `reports/summary.md`.
