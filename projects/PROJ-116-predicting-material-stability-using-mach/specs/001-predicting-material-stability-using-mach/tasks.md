---
description: "Task list for Predicting Material Stability using Machine Learning and DFT Calculations"
---

# Tasks: Predicting Material Stability using Machine Learning and DFT Calculations

**Input**: Design documents from `/specs/001-material-stability/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL – only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] T### [P?] [Story] description with file path`

- **[P]** – can run in parallel (different files, no dependencies)  
- **[Story]** – which user story this task belongs to (e.g., US1, US2, US3)  

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 [P] Create directory structure for `projects/PROJ-116-predicting-material-stability-using-mach/` (sub‑folders `data/raw`, `data/processed`, `data/models`, `code`, `code/utils`, `outputs`, `outputs/figures`, `outputs/logs`, `outputs/metrics`, `tests`, `state`).
- [x] T002 [P] Initialize a Git repository and create a top‑level `README.md` in the project root.
- [x] T003 Initialize a Python 3.11 project with pinned dependencies in `projects/PROJ-116-predicting-material-stability-using-mach/code/requirements.txt` (pymatgen, scikit‑learn, pandas, numpy, matplotlib, seaborn, requests, datasets, shap).
- [x] T004 [P] Configure linting/formatting tools (black, flake8, mypy) in the same directory.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that **must** be complete before any user story can start.

- [x] T005 [P] Create base data‑model classes `MaterialEntry` and `FeatureVector` in `projects/PROJ-116-predicting-material-stability-using-mach/code/data_models.py`.
- [x] T006 [P] Set up environment‑configuration management (data‑path constants, random‑seed handling) in `projects/PROJ-116-predicting-material-stability-using-mach/code/config.py`.
- [x] T007 [P] Implement logging infrastructure with file and console handlers in `projects/PROJ-116-predicting-material-stability-using-mach/code/utils/logging.py`.
- [x] T008 [P] Implement data‑validation utilities for missing bond‑length data and degenerate Voronoi cells in `projects/PROJ-116-predicting-material-stability-using-mach/code/utils/validation.py`.

**Checkpoint**: Foundational work complete – user‑story implementation may now begin.

---

## Phase 3: User Story 1 – Baseline Model Training & Evaluation (Priority P1) 🎯 MVP

**Goal**: Train a Gradient Boosting Regressor using only bulk Magpie descriptors and produce baseline metrics.

### Tests for User Story 1 (optional)

- [x] T009 [P] [US1] Unit test for Magpie feature extraction in `projects/PROJ-116-predicting-material-stability-using-mach/tests/unit/test_features.py`.
- [x] T010 [P] [US1] Integration test for the end‑to‑end baseline pipeline in `projects/PROJ-116-predicting-material-stability-using-mach/tests/integration/test_baseline.py`.

### Implementation for User Story 1

- [ ] T011 [US1] Implement data download & filtering in `projects/PROJ-116-predicting-material-stability-using-mach/code/download_data.py`.  
  • Fetch OQMD Li‑rich rock‑salt entries via the official Zenodo URL.  
  • Filter for fully relaxed DFT energies.  
  • Log a warning if the final sample count < 500 and proceed with whatever is available.  
  • Save raw CSV to `projects/PROJ-116-predicting-material-stability-using-mach/data/raw/oqmd_li_rocksalt.csv`.  
  • **Fail loudly** if the remote source cannot be reached (no synthetic fallback).
- [ ] T012 [US1] Implement bulk Magpie feature extraction in `projects/PROJ-116-predicting-material-stability-using-mach/code/feature_engineering.py`.  
  • Use `matminer` to compute Magpie descriptors only.  
  • Impute missing values with the column median **or** skip the feature for that entry, logging counts to `outputs/logs/imputation_log.txt`.  
  • Write the feature matrix to `projects/PROJ-116-predicting-material-stability-using-mach/data/processed/baseline_features.parquet`.
- [ ] T013 [US1] Implement baseline model training & hyper‑parameter tuning in `projects/PROJ-116-predicting-material-stability-using-mach/code/train_baseline.py`.  
  • Split data (train/val/test) respecting the spec split ratios.  
  • Tune `max_depth` and `n_estimators` on the validation set (early stopping).  
  • Persist the best model to `projects/PROJ-116-predicting-material-stability-using-mach/data/models/baseline_model.pkl`.  
  • Save tuning details (best params, validation scores) to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/baseline_tuning_results.json`.
- [ ] T014 [US1] Implement baseline evaluation in `projects/PROJ-116-predicting-material-stability-using-mach/code/evaluate.py`.  
  • Load the test split, generate predictions, compute MAE & RMSE.  
  • Write predictions + true values + metrics to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/baseline_results.csv`.
- [ ] T015 [US1] Add concise logging of dataset size, feature count, and training metrics to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/logs/baseline.log`.

**Checkpoint**: User Story 1 should now be fully functional and independently testable.

---

## Phase 4: User Story 2 – Local Coordination Feature Integration & Comparative Analysis (Priority P2)

**Goal**: Augment the dataset with Voronoi & bond‑length descriptors, train a second model, and quantify performance gains.

### Tests for User Story 2 (optional)

- [x] T016 [P] [US2] Unit test for Voronoi‑statistic and bond‑length histogram extraction in `projects/PROJ-116-predicting-material-stability-using-mach/tests/unit/test_voronoi_features.py`.
- [x] T017 [P] [US2] Integration test for augmented‑model training & comparison in `projects/PROJ-116-predicting-material-stability-using-mach/tests/integration/test_augmented.py`.

### Implementation for User Story 2

- [ ] T018 [US2] Extend `feature_engineering.py` to compute local coordination features using `pymatgen` (Voronoi coordination number, face area, solid angle; bond‑length histograms).  
  • Apply to the raw crystal structures from `data/raw/oqmd_li_rocksalt.csv`.  
  • Skip any entry where Voronoi tessellation fails or bond lengths are missing; log counts to `outputs/logs/voronoi_issues.log`.  
  • Append these columns to the existing Magpie matrix.
- [ ] T019 [US2] Persist the combined feature set to `projects/PROJ-116-predicting-material-stability-using-mach/data/processed/augmented_features.parquet`.
- [ ] T020 [US2] Implement augmented model training & tuning in `projects/PROJ-116-predicting-material-stability-using-mach/code/train_augmented.py`.  
  • Use the same train/val/test splits as the baseline.  
  • Save the model to `projects/PROJ-116-predicting-material-stability-using-mach/data/models/augmented_model.pkl`.  
  • Save tuning details to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/augmented_tuning_results.json`.
- [ ] T021 [US2] Extend `evaluate.py` to compute MAE, RMSE, and **R²** for the augmented model, then calculate deltas relative to the baseline.  
  • Output a JSON report `projects/PROJ-116-predicting-material-stability-using-mach/outputs/comparison_metrics.json` containing `mae_baseline`, `mae_augmented`, `mae_delta`, `r2_baseline`, `r2_augmented`, `r2_delta`.
- [ ] T022 [US2] Generate a feature‑importance plot (SHAP or permutation) that highlights the top 10 local coordination features.  
  • Save the figure to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/figures/feature_importance.png`.

**Checkpoint**: Both baseline and augmented pipelines should now run independently and produce the comparative report.

---

## Phase 5: User Story 3 – Metastable Phase Classification & Sensitivity Analysis (Priority P3)

**Goal**: Classify materials as stable/metastable, compute ROC/AUC, and assess robustness of the 0.05 eV/atom threshold.

### Tests for User Story 3 (optional)

- [x] T023 [P] [US3] Unit test for convex‑hull distance calculation using `pymatgen` in `projects/PROJ-116-predicting-material-stability-using-mach/tests/unit/test_hull_distance.py`.
- [x] T024 [P] [US3] Integration test for the full sensitivity‑analysis sweep in `projects/PROJ-116-predicting-material-stability-using-mach/tests/integration/test_sensitivity.py`.

### Implementation for User Story 3

- [ ] T025 [US3] Implement convex‑hull distance computation in `projects/PROJ-116-predicting-material-stability-using-mach/code/hull_distance.py`.  
  • Use `pymatgen.PhaseDiagram` on both predicted and DFT formation energies.  
  • If a composition lacks elemental reference energies, **exclude** it from classification metrics (but keep it for regression); log each exclusion to `outputs/logs/hull_exclusions.log`.  
  • Store all distances in `projects/PROJ-116-predicting-material-stability-using-mach/data/processed/hull_distances.parquet`.
- [ ] T026 [US3] Implement binary classification in `projects/PROJ-116-predicting-material-stability-using-mach/code/classify.py`.  
  • Label “stable” if distance ≤ 0.00 eV/atom, “metastable” if 0.00 < distance ≤ threshold (default 0.05).  
  • Save the label column alongside distances to `data/processed/classification.parquet`.
- [ ] T027 [US3] Extend `evaluate.py` to generate ROC curves and compute AUC‑ROC.  
  • Save the plot to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/figures/roc_curve.png`.  
  • Save the numeric AUC to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/metrics/roc_auc.json`.
- [ ] T028 [US3] Implement sensitivity‑analysis script `projects/PROJ-116-predicting-material-stability-using-mach/code/sensitivity_analysis.py`.  
  • Sweep thresholds `{0.04, 0.05, 0.06}` eV/atom.  
  • For each threshold compute Recall, Precision, F1, **variance_fp**, **variance_fn** (standard deviation across thresholds).  
  • If the filtered dataset contains < 500 samples, set `low_sample_flag = True`.  
  • Output a CSV `projects/PROJ-116-predicting-material-stability-using-mach/outputs/sensitivity_analysis.csv` with columns: `threshold, recall, precision, f1, variance_fp, variance_fn, low_sample_flag`.
- [ ] T029 [US3] Summarize variance metrics in `projects/PROJ-116-predicting-material-stability-using-mach/outputs/metrics/variance_summary.json`.
- [ ] T030 [US3] Generate a robustness report `projects/PROJ-116-predicting-material-stability-using-mach/outputs/robustness_report.md` that reads `variance_summary.json` and states whether the model’s metastability discrimination is **robust** (variance < 5 %) or **sensitive** to the threshold choice.
- [ ] T031 [US3] Add detailed logging of classification, ROC, and sensitivity steps to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/logs/classification.log`.

**Checkpoint**: All three user stories are now independently runnable and produce the required scientific artifacts.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Final quality‑of‑life improvements affecting the whole pipeline.

- [ ] T032 [P] Run a full‑pipeline benchmark (runtime, peak memory) on the CI runner; write results to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/performance_metrics.json`.  
  • Ensure total runtime ≤ 4 h and peak RAM ≤ 7 GB.
- [ ] T033 [P] Refactor `feature_engineering.py` for streaming‑style processing to keep RAM usage low.
- [ ] T034 [P] Add extra unit tests for edge cases (empty dataset, all missing bond lengths) under `projects/PROJ-116-predicting-material-stability-using-mach/tests/unit/`.
- [ ] T035 [P] Validate that `quickstart.md` correctly reproduces the end‑to‑end pipeline steps; update if discrepancies are found.

---
