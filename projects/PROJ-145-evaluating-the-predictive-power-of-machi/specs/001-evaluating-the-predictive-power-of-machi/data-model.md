# Data Model: Evaluating Uncertainty Calibration and Extrapolation Error of Machine Learning for High‑Entropy Alloy Compositions

## Overview
All pipeline artifacts are CSV files (or JSON for scalar metrics) to simplify loading with `pandas`. Full JSON‑Schema definitions reside in `contracts/`.

## Entity Definitions

| Entity | Filename | Description |
|---|---|---|
| **TrainingSet** | `data/processed/heas_train.csv` | Filtered HEA compositions with ground‑truth thermodynamic properties. |
| **HoldoutKnown** | `data/processed/holdout_known.csv` | Known compositions excluded from training (used for extrapolation error). |
| **TrueNovel** | `data/processed/true_novel.csv` | Candidate compositions absent from the local hash index and distant from the training centroid. |
| **FeatureEngineered** | `data/processed/heas_train_features.csv` | Training set augmented with weighted mean/variance descriptors (FR‑003). |
| **NovelPredictions** | `data/processed/true_novel_predictions.csv` | Model predictions, ensemble variance, and convex‑hull distance for each novel candidate. |
| **Report** | `data/results/report.csv` | Final ranked table (top segment) plus aggregated metrics and statistical test results. |
| **Metrics** | `data/results/holdout_metrics.csv`, `data/results/novel_stats.json` | Scalar performance metrics and statistical test outcomes. |

## Schema Summaries (full definitions in `contracts/`)

* **heas_train.schema.yaml** – columns: `composition_id` (string), `elements` (string), `n_elements` (int ≥ 5), `formation_energy` (float), `mixing_enthalpy` (float), `source` (enum {aflow, mp}).  
* **heas_train_features.schema.yaml** – adds weighted descriptor columns (`mean_atomic_radius`, `var_atomic_radius`, …, `target_energy`). Variance fields are clamped to a minimum of 1e‑6.  
* **novel_candidates.schema.yaml** – columns: `composition_id`, `elements`, `predicted_energy`, `prediction_variance` (≥ 0), `distance_from_hull` (≥ 0), `rank` (int).  
* **metrics.schema.yaml** – generic metric record: `metric_name` (string), `value` (number), optional `p_value` (0‑1), `test_type` (enum), `dataset` (enum).  

## Data Flow
1. **Ingestion** → `heas_train.csv`.  
2. **Index Building** → in‑memory hash set.  
3. **Hold‑out / Novel Generation** → `holdout_known.csv`, `true_novel.csv`.  
4. **Descriptor Calculation** → `heas_train_features.csv`.  
5. **Model Training** → `models/rf_model.pkl`, `models/gb_model.pkl`.  
6. **Prediction** → `true_novel_predictions.csv`.  
7. **Statistical Evaluation** → metric JSON files.  
8. **Report Assembly** → `report.csv`.

## Validation Steps
After each artifact is written, the pipeline **validates the file against its corresponding JSON‑Schema** (e.g., `heas_train.csv` → `contracts/heas_train.schema.yaml`). Validation failures abort the run, ensuring strict adherence to the contracts and satisfying spec‑coverage requirement 27727f48.
