# Data Model: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

## 1. Entity Relationship Overview

The data model consists of three primary input datasets derived from the source API, two intermediate feature datasets, and one output prediction dataset.

1.  **Source Data**: Raw thermodynamic data from `hmao/all_apis_for_multiapi`.
2.  **Training Set (`heas_train.csv`)**: Filtered 5+ element systems used for model training.
3.  **Hold-out Known (`holdout_known.csv`)**: 5+ element systems present in source but excluded from training.
4.  **True Novel (`true_novel.csv`)**: Synthetic 5-element compositions not found in source (database novelty).
5.  **Feature Data**: All three sets augmented with `pymatgen` descriptors.
6.  **Predictions**: Model outputs with uncertainty metrics.

## 2. Schema Definitions

### 2.1. Source Data (Raw)
*Derived from `hmao/all_apis_for_multiapi`.*
-   `composition`: String (e.g., "Fe0.2Co0.2Ni0.2Cr0.2Mn0.2")
-   `formation_energy_per_atom`: Float (eV/atom)
-   `mixing_enthalpy`: Float (eV/atom) - *Optional, may be derived or null*
-   `elements`: List of Strings (e.g., ["Fe", "Co", "Ni", "Cr", "Mn"])
-   `element_fractions`: List of Floats

### 2.2. Feature-Engineered Data (Train/Holdout/Novel)
*Common schema for all three sets after `feature_engineering.py`.*

| Column Name | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `composition_id` | String | Unique hash of composition string | Generated |
| `composition` | String | Original composition string | Raw |
| `num_elements` | Integer | Count of unique elements | Filtered |
| `formation_energy` | Float | Target variable (eV/atom) | Raw |
| `mixing_enthalpy` | Float | Target variable (eV/atom) | Raw/Null |
| `mean_atomic_radius` | Float | Weighted mean of atomic radii | `pymatgen` |
| `var_atomic_radius` | Float | Weighted variance of atomic radii | `pymatgen` |
| `mean_electronegativity` | Float | Weighted mean of electronegativity | `pymatgen` |
| `var_electronegativity` | Float | Weighted variance of electronegativity | `pymatgen` |
| `mean_VEC` | Float | Weighted mean of Valence Electron Count | `pymatgen` |
| `var_VEC` | Float | Weighted variance of VEC | `pymatgen` |
| `mean_melting_point` | Float | Weighted mean of melting points | `pymatgen` |
| `var_melting_point` | Float | Weighted variance of melting points | `pymatgen` |
| `distance_to_hull` | Float | Distance from training convex hull **in descriptor feature space** | Calculated |

**Note on `distance_to_hull`**: This metric is calculated in the space of the compositional descriptors (radius, VEC, etc.), not in thermodynamic space. It represents the geometric distance of a new composition from the training data distribution in feature space.

### 2.3. Predictions Output
*Output of `evaluate.py`.*

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `composition_id` | String | Unique hash |
| `composition` | String | Composition string |
| `target_energy` | Float | Ground truth (if available, else `NaN`) |
| `pred_energy` | Float | Predicted formation energy |
| `pred_std` | Float | Ensemble standard deviation (uncertainty metric) |
| `distance_to_hull` | Float | Distance from training convex hull (in descriptor space) |
| `is_novel` | Boolean | True if "True Novel" set |

## 3. Data Flow

1. **Ingestion**: Load raw data -> Filter `num_elements >= 5` -> Split into `Train` ([deferred]), `Holdout` ([deferred]).
2.  **Novel Generation**: Enumerate random 5-element combos -> Check against `Train` + `Holdout` (and `hmao/all_apis_for_multiapi` index) -> Save as `True Novel`.
3.  **Feature Engineering**: Apply `pymatgen` calculations to all three sets.
4.  **Training**: Fit RF/GB on `Train`.
5.  **Evaluation**: Predict on `Holdout` (calculate error) and `True Novel` (calculate uncertainty).
6.  **Report**: Aggregate metrics, run t-tests, Spearman correlations.

## 4. Constraints & Validation

-   **Clamping**: All variance features clamped to minimum $1e-6$ to prevent division by zero.
-   **Uniqueness**: `composition_id` must be unique across all sets.
-   **Completeness**: No `NaN` in target variables for training/holdout sets.
-   **Consistency**: `distance_to_hull` calculated relative to the `Train` set convex hull in descriptor space.
-   **Novelty Definition**: "True Novel" is defined as "absent from `hmao/all_apis_for_multiapi`", not "absent from physical reality".