# Data Model: Predicting Reaction Mechanisms from Spectroscopic Data with Machine Learning

## Overview

This document defines the data structures used throughout the pipeline. All data artifacts are derived from raw spectroscopic files and transformed into standardized formats for modeling.

## Entities

### 1. Raw Spectral Record
The raw input from Hugging Face datasets.
- **Fields**:
  - `id`: Unique identifier (string).
  - `spectrum_type`: "IR" or "NMR" (string).
  - `raw_data`: List of floats (intensity values).
  - `x_axis`: List of floats (wavenumbers or ppm).
  - `mechanism_label`: String (SN1, SN2, E1) or `null`.
  - `provenance`: String (source of the label, e.g., "kinetic_study", "inferred_structure") or `null`.
  - `source_url`: String (original dataset URL).
  - `source_id`: String (Derived: `provenance` if present, else `source_url`). Used for Source-Stratified CV.

### 2. Spectral Fingerprint (Processed)
The standardized 512-bin vector used for modeling (256 IR + 256 NMR).
- **Fields**:
  - `id`: Unique identifier (string).
  - `fingerprint`: List[float] (length 512).
  - `mechanism_label`: String (SN1, SN2, E1).
  - `source_id`: String (Used for stratification).
  - `class_distribution`: Dict (counts of each class in the dataset, for reference).
  - `is_valid`: Boolean (true if no NaNs and provenance is valid or pivot is active).

### 3. Model Output
The results of the training and evaluation phase.
- **Fields**:
  - `model_type`: String ("RandomForest" or "XGBoost").
  - `mean_accuracy`: Float.
  - `std_accuracy`: Float.
  - `f1_scores`: Dict (key: class, value: float).
  - `feature_importance`: List[Tuple] (list of (bin_index, importance_score)).
  - `permutation_p_value`: Float.
  - `is_significant`: Boolean (p < 0.05).
  - `top_features`: List[Dict] (top 10 bins with mapped frequency ranges).
  - `stability_cv`: Float (Coefficient of Variation of importance scores across folds).
  - `structure_confound_metric`: Float (Correlation between spectral importance and structure-only importance).
  - `match_rate`: Float (Percentage of top-10 bins matching literature modes within ±10 cm-1).

## Data Flow

1.  **Ingestion**: `Raw Spectral Record` -> Filter (valid label, valid provenance OR pivot active) -> `Filtered Raw Record`.
2.  **Preprocessing**: `Filtered Raw Record` -> Binning (4000-400 cm-1 or 0-12 ppm) -> `Spectral Fingerprint`.
3.  **Modeling**: `Spectral Fingerprint` (X, y, source_id) -> `Model Output`.
4.  **Analysis**: `Model Output` -> `Final Report`.

## Constraints

-   **Fingerprint Length**: Exactly 512 bins (256 IR + 256 NMR).
-   **Label Domain**: Strictly {SN1, SN2, E1}.
-   **Missing Data**: No NaN values allowed in the `fingerprint` or `mechanism_label`.
-   **Provenance**: Only records with `provenance` indicating "kinetic" or "validated" are included in the "Kinetic" set. If absent, records are included only in the "Structure-Verified" pivot set.