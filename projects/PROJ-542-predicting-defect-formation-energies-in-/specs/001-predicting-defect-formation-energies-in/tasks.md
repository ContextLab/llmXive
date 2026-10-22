# Tasks: Predicting Defect Formation Energies in Perovskites with Machine Learning

**Inputs**: `spec.md`, `plan.md`, verifier rejection feedback, reviewer comments, existing project artifacts.

## Phase 1: Setup and first end‑to‑end analysis

- [X] T001 [US1] Document the runnable pipeline entry point and verify module wiring.
  *Files:* `quickstart.md`, `src/pipeline/run.py`, `src/data/download.py`, `src/data/featurize.py`.
  *Verification:* Unit test `code/tests/test_pipeline_entry.py` asserts that `src.pipeline.run` can be imported and that the function `run()` returns without raising; no end-to-end execution required here (deferred to T010).

- [ ] T012 [P] Create a pinned `requirements.txt` for the project.
  *File:* `code/requirements.txt`.
  *Contents:*
  ```
  python==3.11
  pymatgen==2024.6.10
  mp-api==0.33.0
  pandas==2.2.2
  numpy==1.26.4
  scikit-learn==1.5.0
  matplotlib==3.9.0
  seaborn==0.13.2
  pytest==8.2.2
  ```
  *Verification:* `pip install -r code/requirements.txt` succeeds in a fresh venv and all import statements used in the code resolve.

- [ ] T002 [US1] Implement the real data acquisition step: fetch perovskite oxygen‑vacancy defect formation energies from the Materials Project API via `mp_api`. <!-- FAILED-IN-EXECUTION: src/utils/checksum_all.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/utils/checksum_all.py exit=1; src/utils/checksum_all.py exit=1 -->
  *File:* `src/data/download.py`.
  *Requirements:* Abort with clear error if `MP_API_KEY` missing (`"Materials Project API key not provided"`). Abort with `"No data found for specified filters."` if the query returns zero records. No user‑provided CSV fallback.
  *Output:* `data/raw/materials_defects.csv`.
  *Verification:* Script exits 0, CSV is validated row‑wise against `contracts/raw_dataset.schema.yaml`, and the row count is ≥500 to satisfy SC-005.

- [ ] T003 [US1] Implement featurization with `pymatgen`.
  *File:* `src/data/featurize.py`.
  *Requirements:* Drop rows with undeterminable oxidation states (log count). Abort if any descriptor gaps remain after this filter (`"Descriptor gaps detected – see descriptor_gaps.log"`).
  *Outputs:* `data/processed/features.csv`, `data/processed/featurize.log`, `data/processed/descriptor_gaps.log`.
  *Verification:* Column set exactly 12 descriptor columns + `formation_energy`; no missing target values.

- [ ] T004 [US1] Perform dataset validation and power analysis.
  *File:* `src/data/validate.py`.
  *Requirements:* Raise `ValueError` if <50 rows (FR‑009). Compute statistical power to detect ΔRMSE = 0.1 eV with σ ≈ 0.3 eV, α = 0.05; flag if N < 210.
  *Output:* `data/processed/validation.log`.
  *Verification:* Log contains row count, power estimate, and appropriate warnings/errors.

- [ ] T005 [US1] Compute SHA‑256 checksums for raw and processed data artifacts. <!-- FAILED-IN-EXECUTION: src/utils/checksum_all.py exit=1 -->
  *File:* `src/utils/checksum.py`.
  *Outputs:* `data/checksums/raw_defects.sha256`, `data/checksums/features.sha256`.
  *Verification:* pytest `code/tests/test_checksums.py` recomputes and asserts equality.

- [ ] T006 [US1] Perform deterministic group‑aware train/test split.
  *File:* `src/models/split.py`.
  *Outputs:* `data/processed/train.csv`, `data/processed/test.csv`, `data/processed/split.log`.
  *Verification:* No composition appears in both splits; unit test asserts empty intersection.

- [ ] T007 [US2] Implement 5‑fold GroupKFold cross‑validation for Random Forest and Gradient Boosting.
  *File:* `src/models/train.py`.
  *Fixes:* Import `List` from `typing`; write CV metrics to `data/processed/cv_metrics.json` (schema‑valid subset).
  *Outputs:* `models/rf_cv.pkl`, `models/gb_cv.pkl`, `data/processed/cv_metrics.json`.
  *Verification:* `cv_metrics.json` conforms to the `cv_metrics` section of `contracts/model_performance.schema.yaml`.

- [ ] T008 [US3] Evaluate the selected model on the held‑out test set.
  *File:* `src/models/evaluate.py`.
  *Decision rule:* Fallback is triggered if mean RMSE > 0.5 eV OR R² < 0.70 (per FR-012).
  *Outputs:* `data/processed/performance_partial.json` (contains `test_metrics`, `bootstrap_ci`, `paired_ttest`).
  *Verification:* `performance_partial.json` validates against the corresponding sections (excluding `feature_importances`) of `contracts/model_performance.schema.yaml`.

- [ ] T009 [US3] Generate baseline feature‑importance ranking.
  *File:* `src/models/feature_importance.py`.
  *Requirements:* Extract importances from the selected model, write `figures/feature_importance.png`, and populate the final `data/processed/performance.json` by merging `performance_partial.json` with `feature_importances`.
  *Outputs:* `figures/feature_importance.png`, `data/processed/performance.json`.
  *Verification:* `performance.json` validates against the full `contracts/model_performance.schema.yaml`.

- [ ] T015 [US3] Implement structural‑descriptor augmentation (FR-012 Fallback).
  *File:* `src/data/augment_structural.py`.
  *Requirements:* Triggered if T008 decision rule indicates failure. Compute coordination numbers, average bond lengths, and crystal symmetry class via `pymatgen`.
  *Output:* `data/processed/features_augmented.csv` (Do NOT overwrite `features.csv`).
  *Verification:* `features_augmented.csv` contains the original 12 compositional descriptors plus the new structural descriptors; checksum recorded in `data/checksums/features_augmented.sha256`.

- [ ] T016 [US3] Execute fallback re‑run loop.
  *Requirements:* If T015 produced augmented features, re-execute the sequence T006 → T007 → T008 → T009 using `features_augmented.csv` as the input.
  *Outputs:* Updated `data/processed/train.csv`, `test.csv`, `cv_metrics.json`, `performance.json`, and `figures/`.
  *Verification:* Final `performance.json` reflects the metrics of the augmented model.

- [ ] T010 [US1] Assemble the reproducible Jupyter notebook and full contract test suite.
  *File:* `src/pipeline.ipynb`.
  *Tasks performed in notebook:* download → featurize → validate → split → train → evaluate → (fallback) → generate figures → write `runtime.log`.
  *Verification:* Running the notebook from a clean environment reproduces all artifacts, ends with "Pipeline completed successfully", and all pytest contract tests (`test_contracts.py`) pass. Runtime ≤ 1800 s.

- [ ] T011 [US1] Write methods/results markdown and paper‑stage handoff.
  *File:* `paper/methods_results.md`.
  *Contents:* Links to `data/processed/features.csv` (or `features_augmented.csv` if fallback used), `data/processed/performance.json`, figures, dataset size, MP IDs, and explicit statement of whether FR‑012 fallback was triggered.

- [ ] T013 [US1] Update the project state file with artifact hashes.
  *File:* `state/projects/PROJ-542-predicting-defect-formation-energies-in-.yaml`.
  *Action:* After each artifact creation (raw CSV, features, split, models, performance, figures, logs, checksums), compute SHA‑256 and write to `artifact_hashes` map with current `updated_at` timestamp.
  *Verification:* pytest `code/tests/test_state_updates.py` parses the YAML and confirms that every file listed under `artifact_hashes` exists and its hash matches the recorded value.

## Phase 2: Validation of contract mapping for feature matrix

- [ ] T014 [US1] Define a dedicated features schema and validate `features.csv`.
  *File:* `contracts/features.schema.yaml`.
  *Schema:* Requires the twelve descriptor columns (`A_radius`, `A_electronegativity`, … `X_valence_electrons`) and a numeric `formation_energy`; no additional properties.
  *Verification:* `code/tests/test_features_schema.py` validates `data/processed/features.csv` (or `features_augmented.csv` if present) against this schema.