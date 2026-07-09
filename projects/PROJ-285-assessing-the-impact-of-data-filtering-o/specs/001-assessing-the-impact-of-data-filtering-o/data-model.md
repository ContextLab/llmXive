# Data Model: Assessing the Impact of Data Filtering on Gravitational Lens Detection Rates

## Overview
This document defines the data structures, schemas, and relationships used in the project. All data artifacts are stored in `data/` and processed by scripts in `code/`.

## Entities

### 1. LensCandidate
Represents a potential gravitational lens object from the input catalog (SLFC).
*   **Source**: `data/raw/slfc_dataset.parquet`.
*   **Attributes**:
    *   `id`: Unique identifier (string/int).
    *   `SNR`: Signal-to-Noise Ratio (float).
    *   `morphology_score`: Morphology classification score (float, 0.0-1.0).
    *   `RA`: Right Ascension (float, degrees).
    *   `Dec`: Declination (float, degrees).
    *   `is_lens`: Boolean ground truth label (True/False).

### 2. ThresholdMetric
Represents the result of applying a specific threshold pair.
*   **Source**: `data/processed/detection_matrix.csv`.
*   **Attributes**:
    *   `snr_threshold`: The SNR cutoff used (float).
    *   `morph_threshold`: The morphology cutoff used (float).
    *   `detection_count`: Total candidates passing thresholds (int).
    *   `tp_count`: True Positives (int).
    *   `fp_count`: False Positives (int).
    *   `purity_score`: `tp / (tp + fp)` (float, or NaN).
    *   `recovery_rate`: Fraction of true lenses detected (float).
    *   `bootstrap_ci_lower`: Lower bound of 95% CI for recovery rate.
    *   `bootstrap_ci_upper`: Upper bound of 95% CI for recovery rate.
    *   `fdr_adjusted_p`: Benjamini-Yekutieli adjusted p-value.
    *   `clm_coefficient`: Coefficient from Cumulative Link Model.

### 3. SensitivitySweepResult
Represents the result of the sensitivity analysis.
*   **Source**: `data/processed/sensitivity_sweep.csv`.
*   **Attributes**:
    *   `base_snr_threshold`: The base SNR threshold (float).
    *   `offset`: The offset applied (e.g., +0.5, -1.0) (float).
    *   `fp_rate`: False Positive Rate at this offset (float).
    *   `fp_variation`: Change in FP rate relative to base (float).

### 4. InjectionRecoveryReport
Represents the validation of the injection/recovery methodology.
*   **Source**: `data/processed/injection_recovery_report.json`.
*   **Attributes**:
    *   `recovery_rate`: Fraction of true lenses recovered at base threshold.
    *   `threshold_met`: Boolean (True if recovery_rate >= 0.95).
    *   `total_lenses`: Total number of true lenses in the dataset.
    *   `recovered_lenses`: Number of lenses detected.

## Data Flow

1.  **Ingestion**: `data_loader.py` reads SLFC data and outputs `data/raw/slfc_dataset.parquet` and `data/raw/injection_ground_truth.csv`.
2.  **Filtering**: `filter_engine.py` iterates the grid, outputs `data/processed/detection_matrix.csv`.
3.  **Validation**: `validation.py` matches coordinates, calculates purity, updates `detection_matrix.csv`.
4.  **Analysis**: `stats_analysis.py` performs CLM and Bootstrap on lens population, adds `recovery_rate` and `fdr_adjusted_p`.
5.  **Sensitivity**: `stats_analysis.py` runs the sweep, outputs `data/processed/sensitivity_sweep.csv`.
6.  **Recovery Report**: `validation.py` generates `data/processed/injection_recovery_report.json`.
7.  **Visualization**: `visualization.py` reads processed CSVs, generates `.png` plots.

## Constraints & Invariants

*   **Coordinate Tolerance**: All matching must use ≤ 1.0 arcsec (FR-003).
*   **Grid Completeness**: All possible combinations must be present in `detection_matrix.csv`. (Constitution Principle VII).
*   **Memory**: No single DataFrame exceeds a manageable size threshold..
*   **Reproducibility**: All random seeds must be set to a fixed integer (e.g., 42) in `config.py`.
*   **Ground Truth**: `is_lens` label is the single source of truth for TP/FP.
