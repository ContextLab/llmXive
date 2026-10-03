# Tasks: Assessing Uncertainty Quantification Techniques for Machine‑Predicted Material Properties

**Input**: Design documents from `/specs/001-assessing-uncertainty-quantification/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be independently completable and testable.

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001b [P] Create initial empty files: `code/requirements.txt`, `code/config.yaml`, `README.md`.
- [X] T001 [P] Document the deviation from Spec FR-001 (Materials Project) to Plan's OQMD source in `docs/data_source_rationale.md` to satisfy reproducibility principles while using an executable dataset.
- [X] T002 Initialize Python project with pinned dependencies in `requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` and `.black.toml` configuration files in the repository root to enforce style standards. **Dependency**: None.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [X] T004 [P] Implement `code/config.yaml` with the following exact keys and values: `seed` (int, default 42), `split_ratio` (list [0.8, 0.1, 0.1]), `split_type` (string, MUST be "stratified"), `timeout_hours` (float, 5.0), `screening_recall_target` (float, default 0.8), `robustness_seeds` (list [42, 43, 44]), `robustness_cv_threshold` (float, 0.1), and `screening_precision_gain_threshold` (float, 0.05). Define exact keys: `seed`, `split_ratio`, `split_type`, `timeout_hours`, `screening_recall_target`, `robustness_seeds`, `robustness_cv_threshold`, `screening_precision_gain_threshold`. File path: `code/config.yaml`.
- [X] T005 [US1] **Data Download & Validation**: Implement `code/data/download.py` to fetch the **OQMD** Formation Energy dataset via HuggingFace (`datasets.load_dataset("materials-toolkits/oqmd", streaming=False)`). **Requirement**: Implement retry logic with exponential backoff (up to 3 attempts) for network failures. **Materialization Requirement**: Explicitly call `dataset.to_parquet('data/raw/oqmd.parquet')` to materialize the stream. **Checksum Requirement**: Calculate SHA-256 hash of `data/raw/oqmd.parquet` and record it in `data/checksums.json` with schema: `{"filename": "oqmd.parquet", "sha256": "<hash_string>"}`. **Schema Requirement**: Explicitly extract columns: `formation_energy`, `bulk_modulus`, `band_gap`, `element_fractions`, and structural descriptors if present. **Validation**: Parse columns to identify structural features. If missing, log to `data/validation_report.json`, proceed with compositional features, and set `structural_features_available=false` in config. If present, extract `radius` and `packing_fraction`. Output artifact: `data/raw/oqmd.parquet`. **Dependency**: None.
- [ ] T006a [US1] Implement `code/data/preprocess.py` (Split & Binning): Read `code/config.yaml` for `split_type` and `seed`. Apply a **stratified random split** (train/validation/test) based on the target variable (**formation_energy**) using **10 quantile bins**. **Output**: Explicitly generate `data/processed/raw_train.csv`, `data/processed/raw_val.csv`, `data/processed/raw_test.csv`. **Requirement**: The output CSVs MUST include a new column `target_bin`. **Dependency**: T005.
- [ ] T006b [US1] **PCA & Exclusion**: Read `data/processed/raw_train.csv` from T006a. Fit PCA on **training set only** to reduce features to **20 principal components**. Transform train/val/test sets using the fitted PCA. **Exclusion**: Exclude rows with missing critical features. **Output**: Generate `data/processed/features_train_20pca.csv`, `data/processed/features_val_20pca.csv`, `data/processed/features_test_20pca.csv` and `data/validation_report.json` with schema `{"excluded_count": int, "missing_columns": [str]}`. **Artifact Serialization**: Save the PCA transformer object as `data/processed/pca_transformer.pkl`. **Dependency**: T006a.
- [X] T009 [P] **Contract Definitions**: Create `specs/001-assess-uncertainty-quantification/contracts/` directory. Generate `dataset.schema.yaml`, `uq_prediction.schema.yaml`, and `calibration_metric.schema.yaml` files defining the SSoT for `MaterialSample`, `UQPrediction`, and `CalibrationMetric` respectively. **Dependency**: None.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Model Training and UQ Application (Priority: P1) 🎯 MVP

**Goal**: Train a baseline FFNN and apply three UQ techniques (Deep Ensembles, MC Dropout, Sparse GP) to generate predictions and variance estimates on CPU.

**Independent Test**: The system ingests the dataset, trains the baseline, runs UQ inference, and outputs a CSV with (prediction, lower_bound, upper_bound, variance) without GPU errors within 5 hours.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for `code/data/preprocess.py` PCA and missing data exclusion in `tests/unit/test_preprocess.py`
- [X] T011 [P] [US1] Contract test for output schema in `tests/contract/test_schemas.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/models/baseline_nn.py`: Define the architecture for a 2 hidden layer FFNN with ≤10k params and a heteroscedastic output head. **Verification**: Include a function to calculate total parameters and assert `total_params <= 10000`. **Output**: Save the architecture definition/class to `results/models/baseline_nn_arch.pt` and a log entry confirming the parameter count. **Dependency**: T006b.
- [ ] T013 [P] [US1] **Deep Ensemble Training**: Implement `code/models/deep_ensemble.py`. **Execute the training loop** to train **exactly 5** independently initialized copies of the baseline model (T012). **Logic**: Iterate 5 times with seeds `[42, 43, 44, 45, 46]`, training a new model instance each time. **Hyperparameters**: Use **100 epochs**, **learning rate 0.001**, **batch size 64**, and **MSE loss with heteroscedastic head**. **Output**: Save models to `results/models/ensemble/` with unique filenames `ensemble_seed_<seed>.pt`. **Verification**: Ensure all 5 files exist and are non-empty before task completion. **Dependency**: T012, T006b.
- [ ] T014 [P] [US1] **MC Dropout Inference**: Implement `code/models/mc_dropout.py`. Enable dropout (p=0.2), run **30 stochastic forward passes** per sample on the **test set** with `model.train()` enabled. **Output**: Save inference results (predictions and variances) to `results/uq_predictions_mc_dropout.csv` AND save the trained MC Dropout model state dict (seed 42) to `results/models/mc_dropout/mc_dropout_seed_42.pt`. **Dependency**: T006b, T012.
- [ ] T015 [P] [US1] **Sparse GP Fitting & Saving**: Implement `code/models/sparse_gp.py`. **Verification**: Check existence of `data/processed/features_test_20pca.csv` and `data/processed/pca_transformer.pkl` before execution. Fail loudly if missing. **Do not re-fit PCA**. **Fitting**: Load **PCA-reduced features** from `data/processed/features_train_20pca.csv` (T006b) and the transformer from T006b. Fit Sparse GP with **500 inducing points** and **RBF kernel** using GPyTorch (CPU mode). **Saving**: Save the fitted GP model to `results/models/sparse_gp_model.pt`. **Dependency**: T006b.
- [ ] T016a [US1] Implement `code/models/run_single_seed.py`: A reusable runner script that performs **model training and UQ inference** for **one specific seed**. **Constraint**: This script MUST **NOT** perform data download or preprocessing. It must load pre-processed artifacts from `data/processed/` (generated by T006) and train/infer only. **Execution**: **Load** model weights from `results/models/ensemble/ensemble_seed_<seed>.pt` (T013), `results/models/mc_dropout/mc_dropout_seed_<seed>.pt` (T014), and `results/models/sparse_gp_model.pt` (T015). **Logic**: **Iterate** over the seed list `[42, 43, 44, 45, 46]`, loading the corresponding model artifacts for each seed. **Inference**: Run inference, **calculate bounds from variance** using **Gaussian assumption (mean ± z*std)** for **[deferred] (z=0.674)** and **[deferred] (z=1.645)** intervals, and write CSV. Output artifact: `results/uq_predictions_seed_<seed>.csv` with the **exact** following columns in order: `sample_id` (int), `method` (str), `prediction` (float64), `variance` (float64), `lower_50` (float64), `upper_50` (float64), `lower_90` (float64), `upper_90` (float64). **Dependency**: T006b, T012, T013, T014, T015.
- [ ] T016b [US1] Implement `code/main.py` orchestrator to chain data load -> train -> UQ inference. **Global Timeout**: Enforce a hard timeout for the **entire pipeline** (T016a runs + T026 tasks). **Wait Logic**: Explicitly trigger and wait for the completion of T013, T014, and T015 (models) before T016a starts. **Merge**: Explicitly depend on and merge outputs from T016a runs into `results/uq_predictions_base.csv`. **Dependency**: T006b, T012, T013, T014, T015, T016a.
- [X] T017a [P] [US1] Configure logging format in `code/utils/logging_config.py` to output to `logs/pipeline.log` with timestamps and metric keys.
- [X] T017b [P] [US1] Implement metric recording logic in `code/utils/logging_config.py` to write `epoch_time` and `total_training_time` to `logs/pipeline.log`.
- [X] T018 [US1] Verify `results/uq_predictions_base.csv` generation and schema compliance. **Dependency**: T016b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Calibration and Reliability Evaluation (Priority: P2)

**Goal**: Evaluate calibration (ECE, Interval Score) and rank methods based on uncertainty accuracy.

**Independent Test**: Calculate ECE and Interval Score for specified confidence intervals, generate reliability diagrams, and rank methods by ECE.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for ECE calculation logic in `tests/unit/test_uq_metrics.py`
- [ ] T020 [P] [US2] Unit test for Interval Score and Sharpness calculation in `tests/unit/test_uq_metrics.py`

### Implementation for User Story 2

- [ ] T025a [P] [US2] **Seed Orchestrator**: Implement `code/run_seeds.py`. **Logic**: Iterate over a fixed list of seeds `[42, 43, 44]`. For each seed, **invoke `code/models/run_single_seed.py`** (T016a) with the specific seed argument. **Constraint**: This script MUST **NOT** call T005 (Download) or T006 (Preprocess). It must rely entirely on the **single frozen dataset** artifacts in `data/processed/` generated by T006. **Robustness**: If a seed fails (e.g., GP timeout), log a warning and **continue** to the next seed. **Output**: Generate `results/uq_predictions_seed_<seed>.csv` for each *successful* seed and **aggregate them into a single intermediate file `results/uq_predictions_aggregated.csv`**. **Dependency**: T016a, T006b.
- [ ] T022 [P] [US2] **Decomposition**: Implement the calculation logic in `code/uq/metrics.py` to separate aleatoric and epistemic uncertainty: **Epistemic variance = variance of predictions across ensemble members for a single sample**, **Aleatoric variance = mean of predicted variances**. **Condition**: If method is Sparse GP, set `aleatoric` and `epistemic` to `null` and `total` to `variance`. **Execution**: This task MUST **read the aggregated file `results/uq_predictions_aggregated.csv`** (from T025a), and **apply the decomposition** to produce **`results/uq_predictions_decomposed.csv`** (a new file with new columns). **Output**: `results/uq_predictions_decomposed.csv` with columns: `sample_id`, `method`, `prediction`, `variance`, `lower_50`, `upper_50`, `lower_90`, `upper_90`, `aleatoric`, `epistemic`, `total`, `uncertainty_type`. **Dependency**: T025a, T021.
- [ ] T022c [US2] **REQUIRED**: Implement a verification script in `code/uq/validate_uq.py` that explicitly asserts the aleatoric/epistemic decomposition logic is correctly applied to the *Deep Ensemble* and *MC-Dropout* outputs specifically, validating that **epistemic variance is non-negative** and **consistent with model variance (correlation > 0.9)**. Output artifact: `logs/uq_validation.log`. **Dependency**: T022.
- [ ] T021 [P] [US2] Implement `code/uq/metrics.py`: ECE (quantile binning), Interval Score, Sharpness.
- [ ] T024 [US2] Compute final metrics and save to `results/calibration_report.csv`. **Schema**: `method` (str), `ece` (float), `interval_score` (float), `sharpness` (float), `coverage_50` (float), `coverage_90` (float). **Dependency**: T022.
- [X] T024a [US2] **REQUIRED**: Implement the logic to aggregate ECE scores by seed into `results/ece_scores_by_seed.json`. **Input**: `results/calibration_report.csv` (T024). **Output**: `results/ece_scores_by_seed.json` with schema `{"42": {"ece": float}, "43": {"ece": float}, "44": {"ece": float}}`. **Dependency**: T024.
- [X] T025 [US2] Implement ranking logic to identify best-performing method based on ECE and Interval Score. **Dependency**: T024.
- [ ] T025b [US2] **REQUIRED**: Implement the **Coefficient of Variation (CV)** calculation logic for ECE scores across **exactly 3 seeds** defined in `code/config.yaml` key `robustness_seeds`. **Input**: `results/ece_scores_by_seed.json` (T024a). **Output**: `results/robustness_report.json` containing: `cv` (float, calculated as **std(ECE)/mean(ECE)**, or null if mean=0), `pass` (boolean, **true if CV ≤ `robustness_cv_threshold` (from config) AND cv is not null AND exactly 3 seeds succeeded**, else false), `seeds_used` (array of integers representing the **successfully completed** seeds. If fewer than 3 seeds succeed, `seeds_used` is `[]`). **Gate**: If `pass` is false, the pipeline MUST log a clear warning indicating robustness failure but **MUST NOT exit with error code 1** (per SC-004 reporting requirement). **Error Handling**: If < 3 seeds succeed, set `cv=null` and `pass=false`. **Dependency**: T025a, T024a.
- [ ] T026 [US2] **REQUIRED**: Implement the **Robustness Gate** in `code/main.py`. **Logic**: After T025b completes, `main.py` must load `results/robustness_report.json`. If the `pass` field is `false`, `main.py` MUST **log a clear error message**: "Robustness Gate Failed: CV > `robustness_cv_threshold` or insufficient seeds (requires 3)". **Dependency**: T025b.
- [X] T023 [US2] Generate reliability diagrams (PDF/PNG) for each method in `results/reliability_diagrams/`. **Dependency**: T024. **Requirement**: Ensure `results/reliability_diagrams/` directory exists and files are named `reliability_<method>.png`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Downstream Screening Case Study (Priority: P3)

**Goal**: Demonstrate practical utility by comparing UQ-based screening vs point-prediction screening for perovskite stability.

**Independent Test**: Filter candidates using narrow confidence intervals; verify precision improvement over point-prediction baseline at fixed recall.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Integration test for screening logic in `tests/integration/test_screening.py`

### Implementation for User Story 3

- [ ] T028a [US3] **REQUIRED**: Implement `code/uq/screening.py` (Threshold Calculation): Calculate the specific formation energy threshold required to achieve the **target recall** defined in `code/config.yaml` (key: `screening_recall_target`) from the test set distribution. **Fallback**: If `screening_recall_target` is `[DEFERRED]` or missing, default to **0.8**. **Output**: `results/screening_threshold.json` with schema `{"recall_target": float, "threshold_value": float}`. **Dependency**: T022.
- [ ] T028b [US3] **REQUIRED**: Implement `code/uq/screening.py`: Point-prediction baseline screening logic for comparison. **Baseline Logic**: Rank candidates by mean prediction value and filter by the **threshold calculated in T028a** to ensure fixed recall. **Dependency**: T022, T028a. Output artifact: `results/screening_baseline.csv`.
- [ ] T028c [US3] **REQUIRED**: Implement `code/uq/screening.py`: Random selection baseline logic. **Logic**: Shuffle the candidate list randomly and select the top-N items corresponding to the target recall count. **Output**: `results/screening_random.csv`. **Dependency**: T028a.
- [ ] T028d [US3] **REQUIRED**: Implement `code/uq/screening.py`: **Narrow confidence interval filtering** as required by FR-007 and US-3. **Input**: `results/uq_predictions_decomposed.csv` (T022) and `results/screening_threshold.json` (T028a). **Logic**: Select candidates where the width of the confidence interval (upper_90 - lower_90) is below a dynamically calculated threshold to ensure high confidence. **Dependency**: T022, T028a, T028b, T028c. Output artifact: `results/screening_candidates.csv`.
- [ ] T028e [US3] **REQUIRED**: Implement fallback logic in `code/uq/screening.py`: If the Sparse GP model fails to load or produce predictions, **exclude** GP results from the screening process and **re-calculate rankings and thresholds** using the remaining methods (Deep Ensemble/MC-Dropout), logging a warning. **Dependency**: T028a, T028b, T028c, T028d. Output artifact: `results/screening_final_candidates.csv`.
- [X] T029 [US3] Calculate precision/recall curves for both UQ (consumes output of T028e) and baseline methods (T028b, T028c). **MUST** explicitly compare the filtered set from T028e against the baselines. **Output**: `results/selection_decisions.csv` containing binary flags (`selected_uq`, `selected_baseline`, `selected_random`) for each candidate to enable McNemar's test. **Dependency**: T028e, T028b, T028c.
- [ ] T029b [US3] **REQUIRED**: Perform **McNemar's test** to validate statistical significance of precision gain, using the binary classification matrix from T029. **Comparison Target**: Explicitly compare the UQ method against the **random selection baseline (T028c)** as required by FR-007. **Input**: `results/selection_decisions.csv`. **Output**: `results/screening_significance.json` containing p-value, test statistic, and test method ("McNemar"). **Fallback Logic**: If McNemar's test is inconclusive (p-value >= 0.05) or sample size is too small, **explicitly check** if the UQ method's precision is at least **`screening_precision_gain_threshold` (from config, default 0.05) absolute percentage point increase** higher than the random baseline. If the specified threshold is met, record success; otherwise, record failure. **Dependency**: T029.
- [ ] T030 [US3] Generate `results/screening_results.csv` with selection metrics and comparison p-values. **Dependency**: T029b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T033a [P] Update `README.md` with project overview and usage instructions.
- [ ] T033b [P] Update `docs/api.md` with usage examples for `screening.py`.
- [X] T034a [P] Run `ruff check code/` to identify unused imports and linting errors.
- [X] T034b [P] Run `black code/` to enforce formatting standards.
- [X] T035 Verify `results/` artifacts against `code/contracts/` schemas
- [X] T036 [P] Run `tests/unit/` and `tests/contract/` suites to ensure all pass
- [X] T037 [P] Implement `code/utils/runtime_logger.py` to measure and record the total wall-clock time of the pipeline in `results/runtime_report.json` to satisfy SC-002. **Dependency**: T016b.

---