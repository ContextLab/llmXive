# Data Model: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

## Overview
This document defines the data schemas for the HEA predictive power study. All data is stored in CSV format for portability and interoperability with `pandas` and `scikit-learn`.

## Entity Definitions

### 1. TrainingSet (`heas_train.csv`)
The core dataset of known HEA compositions with thermodynamic properties.
*   **Source**: Filtered `dataset_thermalcond_aflow` and `all_apis_for_multiapi`.
*   **Filter**: 5+ distinct elements.
*   **Usage**: Model training and feature engineering baseline.

### 2. HoldoutKnown (`holdout_known.csv`)
Compositions present in the source API but excluded from the training set.
*   **Purpose**: Measure extrapolation error relative to the training manifold (Manifold Extrapolation).
*   **Ground Truth**: Available (from API).

### 3. TrueNovel (`true_novel.csv`)
Compositions that return "Not Found" on query to the **Local Proxy Index** (derived from static datasets).
*   **Purpose**: Measure uncertainty calibration in unexplored chemical spaces.
*   **Ground Truth**: **Unavailable** (Analysis limited to uncertainty metrics).

### 4. FeatureEngineering (`heas_train_features.csv`)
The training set augmented with calculated descriptors.
*   **Descriptors**: Weighted mean/variance of Atomic Radius, Electronegativity, VEC, Melting Point.

## Schema Definitions

### TrainingSet Schema
| Column | Type | Description |
| :--- | :--- | :--- |
| `composition_id` | string | Unique hash of the composition string (e.g., "Al20Cr20...") |
| `elements` | string | Comma-separated list of elements (e.g., "Al,Cr,Fe,Mn,Ni") |
| `n_elements` | int | Count of distinct elements (must be ≥ 5) |
| `formation_energy` | float | Formation energy per atom (eV/atom) |
| `mixing_enthalpy` | float | Mixing enthalpy (eV/atom) |
| `source` | string | "aflow" or "mp" |

### FeatureEngineered Schema
| Column | Type | Description |
| :--- | :--- | :--- |
| `composition_id` | string | Unique hash |
| `elements` | string | Comma-separated list |
| `mean_atomic_radius` | float | Weighted mean of atomic radii |
| `var_atomic_radius` | float | Weighted variance (clamped to 1e-6) |
| `mean_electronegativity` | float | Weighted mean electronegativity |
| `var_electronegativity` | float | Weighted variance (clamped to 1e-6) |
| `mean_VEC` | float | Weighted mean Valence Electron Count |
| `var_VEC` | float | Weighted variance (clamped to 1e-6) |
| `mean_melting_point` | float | Weighted mean melting point (K) |
| `var_melting_point` | float | Weighted variance (clamped to 1e-6) |
| `target_energy` | float | Ground truth formation energy |

### NovelCandidate Schema
| Column | Type | Description |
| :--- | :--- | :--- |
| `composition_id` | string | Unique hash |
| `elements` | string | Comma-separated list |
| `predicted_energy` | float | Model prediction |
| `prediction_variance` | float | Ensemble variance (uncertainty metric) |
| `distance_from_hull` | float | Distance from training convex hull |
| `rank` | int | Rank by lowest uncertainty |

## Data Flow
1.  **Ingestion**: Raw Parquet → `heas_train.csv` (filtered).
2.  **Generation**: `heas_train.csv` + API Query → `holdout_known.csv`, `true_novel.csv`.
3.  **Engineering**: `heas_train.csv` + `pymatgen` → `heas_train_features.csv`.
4.  **Prediction**: `heas_train_features.csv` (train) → Model → `holdout_known`/`true_novel` (predict) → `results/report.csv`.
