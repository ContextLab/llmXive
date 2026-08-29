# Data Model: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

## Overview

This document defines the schema and structure of the data artifacts generated and consumed by the project. All data is stored in CSV or Parquet format under `data/processed/`.

## Entity Definitions

### 1. TrainingSet (`heas_train.csv`)
The primary dataset used for model training. Contains known HEA compositions with ground-truth thermodynamic properties and calculated descriptors.

| Column Name | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `composition_id` | string | Unique hash of the elemental composition (e.g., "Al0.2Co0.2Cr0.2Fe0.2Ni0.2") | Derived |
| `elements` | string | Comma-separated list of elements (e.g., "Al,Co,Cr,Fe,Ni") | Derived |
| `n_elements` | int | Number of unique elements in the system | Derived |
| `formation_energy` | float | Ground truth formation energy (eV/atom) | AFLOW (Verified) |
| `mixing_enthalpy` | float | Ground truth mixing enthalpy (kJ/mol) | AFLOW (Verified) |
| `atomic_radius_mean` | float | Weighted mean atomic radius | `pymatgen` |
| `atomic_radius_var` | float | Weighted variance atomic radius | `pymatgen` |
| `electronegativity_mean` | float | Weighted mean electronegativity | `pymatgen` |
| `electronegativity_var` | float | Weighted variance electronegativity | `pymatgen` |
| `vec_mean` | float | Weighted mean Valence Electron Count | `pymatgen` |
| `vec_var` | float | Weighted variance Valence Electron Count | `pymatgen` |
| `melting_point_mean` | float | Weighted mean melting point | `pymatgen` |
| `melting_point_var` | float | Weighted variance melting point | `pymatgen` |

### 2. HoldoutKnown (`holdout_known.csv`)
A subset of the source data that was excluded from the TrainingSet but exists in the source API. Used to measure extrapolation error.

| Column Name | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `composition_id` | string | Unique hash | Derived |
| `elements` | string | Comma-separated list | Derived |
| `formation_energy` | float | Ground truth (from source) | AFLOW (Verified) |
| `mixing_enthalpy` | float | Ground truth (from source) | AFLOW (Verified) |
| `atomic_radius_mean` | float | Weighted mean | `pymatgen` |
| ... | ... | (Same descriptor columns as TrainingSet) | `pymatgen` |
| `prediction_energy` | float | Model prediction | Model Output |
| `prediction_enthalpy` | float | Model prediction | Model Output |
| `error_energy` | float | `formation_energy` - `prediction_energy` | Derived |
| `error_enthalpy` | float | `mixing_enthalpy` - `prediction_enthalpy` | Derived |

### 3. TrueNovel (`true_novel.csv`)
Programmatically generated compositions not found in the source API index. Used for uncertainty analysis.

| Column Name | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `composition_id` | string | Unique hash | Derived |
| `elements` | string | Comma-separated list | Derived |
| `atomic_radius_mean` | float | Weighted mean | `pymatgen` |
| ... | ... | (Same descriptor columns as TrainingSet) | `pymatgen` |
| `prediction_energy` | float | Model prediction | Model Output |
| `prediction_enthalpy` | float | Model prediction | Model Output |
| `prediction_var_energy` | float | Ensemble variance for energy | Model Output |
| `prediction_var_enthalpy` | float | Ensemble variance for enthalpy | Model Output |
| `distance_from_hull` | float | Distance from training convex hull | Derived |
| `reliability_rank` | int | Rank by lowest variance | Derived |

### 4. PerformanceMetrics (`metrics_summary.csv`)
Aggregated statistics for the final report.

| Column Name | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `metric_name` | string | e.g., "interpolation_R2", "extrapolation_R2" | Derived |
| `value` | float | The measured value | Derived |
| `p_value` | float | p-value from statistical test (if applicable) | Derived |
| `test_type` | string | e.g., "permutation", "spearman" | Derived |
| `dataset` | string | e.g., "train", "holdout", "novel" | Derived |

## Data Flow

1.  **Ingestion**: Raw Parquet (AFLOW) $\to$ Filtered CSV (`heas_train.csv` + `holdout_known.csv`).
2.  **Engineering**: CSV $\to$ CSV with descriptor columns (all sets).
3.  **Training**: `heas_train.csv` $\to$ Model Artifacts (`.pkl`).
4.  **Evaluation**: Models + `holdout_known.csv` $\to$ `holdout_known.csv` (with predictions).
5.  **Novel Gen**: Random Combinations $\to$ Query Index $\to$ `true_novel.csv` (filtered).
6.  **Novel Eval**: Models + `true_novel.csv` $\to$ `true_novel.csv` (with variance/distance).
7.  **Reporting**: All CSVs $\to$ `metrics_summary.csv`.
