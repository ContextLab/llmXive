# Data Model: Evaluating the Predictive Power of Machine Learning for Identifying Novel High‑Entropy Alloy Compositions

## Overview
All pipeline artifacts are CSV files, enabling straightforward loading with `pandas`. Schemas are provided in the `contracts/` folder and are validated by the test suite.

## Entity Definitions

| Entity | Filename | Description |
|---|---|---|
| **TrainingSet** | `data/processed/heas_train.csv` | Filtered HEA compositions with ground‑truth thermodynamic properties. |
| **HoldoutKnown** | `data/processed/holdout_known.csv` | Subset of known compositions excluded from training (manifold extrapolation test). |
| **TrueNovel** | `data/processed/true_novel.csv` | Candidate compositions absent from the Local Proxy Index and geometrically distant from the training centroid. |
| **FeatureEngineered** | `data/processed/heas_train_features.csv` | Training set augmented with weighted mean/variance descriptors. |
| **NovelPredictions** | `data/processed/true_novel_predictions.csv` | Model predictions, ensemble variance, and hull distance for each novel candidate. |
| **Report** | `data/results/report.csv` | Final table of top‑100 novel candidates plus aggregated metrics and statistical test results. |

## Schema Summaries (full JSON‑Schema definitions live in `contracts/`)

* **TrainingSet** – `composition_id` (string), `elements` (string), `n_elements` (int ≥ 5), `formation_energy` (float), `mixing_enthalpy` (float), `source` (enum {aflow, mp}).  
* **FeatureEngineered** – adds `mean_atomic_radius`, `var_atomic_radius`, `mean_electronegativity`, `var_electronegativity`, `mean_VEC`, `var_VEC`, `mean_melting_point`, `var_melting_point`, `target_energy`.  
* **NovelCandidate** – `composition_id`, `elements`, `predicted_energy`, `prediction_variance`, `distance_from_hull`, `rank`.  
* **Metrics** – generic schema for any scalar metric (`metric_name`, `value`, optional `p_value`, `test_type`, `dataset`).  

## Data Flow
1. **Ingestion** → `heas_train.csv`.  
2. **Index Building** → Local Proxy Index (in‑memory).  
3. **Hold‑out / Novel Generation** → `holdout_known.csv`, `true_novel.csv`.  
4. **Descriptor Calc** → `heas_train_features.csv`.  
5. **Model Training** → model pickle files (`models/`).  
6. **Prediction** → `true_novel_predictions.csv`.  
7. **Statistical Evaluation** → JSON metric files (`data/results/`).  
8. **Report Assembly** → `report.csv`.

---
