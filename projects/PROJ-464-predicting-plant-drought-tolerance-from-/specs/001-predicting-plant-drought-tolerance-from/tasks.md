# Tasks: Predicting Plant Drought Tolerance from RSA Data

**Input**: Design documents from `/specs/001-predicting-plant-drought-tolerance-from/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [D:Dep] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[D:ID]**: Depends on completion of task ID (e.g., [D:T015])
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, spec alignment, and basic structure

- [X] T001a [P] Create project directories: `data/raw/`, `data/derived/`, `code/`, `tests/`, `docs/`, `state/`, `contracts/`, `results/`. **Logic**: Run `mkdir -p data/raw data/derived code tests docs state contracts results`. **Deliverable**: Directory structure created.

- [X] T001b [P] Initialize `README.md` and `requirements.txt` (empty).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Initialize Python 3.11 project with dependencies in `requirements.txt` (pandas>=2.0.0, numpy>=1.24.0, scikit-learn>=1.3.0, scipy>=1.11.0, statsmodels>=0.14.0, opencv-python-headless>=4.8.0, scikit-image>=0.21.0, requests>=2.31.0, huggingface_hub>=0.16.0, pytest>=7.0.0, networkx>=3.0, caper>=1.0.0, power>=1.0). **Logic**: Run `pip install -r requirements.txt`. **Note**: `pandas-phy` and `ete3` added for PGLS/PVR support. **Deliverable**: `requirements.txt` populated.

- [X] T003 [P] Configure linting (ruff) and formatting (black) tools. **Logic**: Create `ruff.toml` and `pyproject.toml` with black config. **Deliverable**: Config files created.

- [X] T004 [P] Implement `code/config.py` with paths, random seeds (42), and hyperparameters. **Logic**: Include `DATA_PATH`, `SEED`, `HYPERPARAMS` keys. **Deliverable**: `code/config.py`.

- [X] T005 [P] Setup logging infrastructure in `code/__init__.py`. **Logic**: Configure logging to output to `state/pipeline.log` with JSON format and `INFO` level. **Deliverable**: Logging configured.

- [X] T006 [P] Create base data models/entities in `code/models.py` referencing `data-model.md` schema: `RootImage` {id: str, path: str, species: str}, `RSAMetrics` {depth: float, branching_density: float, surface_area: float}, `PhysioTrait` {species: str, conductance: float, photosynthesis: float, survival_rate: float?}. **Logic**: Include validation rules: `depth > 0`, `species_id not null`. **Deliverable**: `code/models.py`.

- [X] T007 Create base data validation schema checks in `contracts/`. **Logic**: Define JSON Schema Draft 7 format for each artifact. **Deliverables**:
 1. `contracts/dataset.schema.yaml`: Validates merged data structure (FR-001, FR-002). Fields: `species_id` (str), `depth` (float, >0), `branching_density` (float, >0), `surface_area` (float, >0), `conductance` (float), `photosynthesis` (float), `pca_depth` (float), `pca_branching_density` (float), `pca_surface_area` (float).
 2. `contracts/rsametrics.schema.yaml`: Validates extracted traits (FR-002, SC-001). Fields: `species_id` (str), `depth` (float, >0), `branching_density` (float, >0), `surface_area` (float, >0).
 3. `contracts/merged_data.schema.yaml`: Validates joined data and PCA/PVR fields (FR-003, FR-010). Fields: `species_id` (str), `depth` (float), `branching_density` (float), `surface_area` (float), `conductance` (float), `photosynthesis` (float), `pca_1` (float), `pca_2` (float), `pca_3` (float).
 4. `contracts/model_results.schema.yaml`: Validates model outputs, VIF, and sensitivity (FR-004, FR-005, FR-006). Fields: `model_type` (str), `predictor` (str), `coefficient` (float), `p_value` (float), `r2` (float), `adj_p_value` (float), `vif` (float), `lambda` (float).
 5. `contracts/output.schema.yaml`: Validates final report framing (FR-009). Fields: `framing` (str: 'associational' or 'causal'), `threshold_justification` (str).
 6. `contracts/results.schema.yaml`: Validates sensitivity sweep details (FR-005, SC-003). Fields: `threshold` (float), `accuracy` (float), `precision` (float), `recall` (float), `f1` (float), `fpr` (float), `fnr` (float).
 **Verification**: Ensure `tests/contract/` suite is configured to validate all generated artifacts against these schemas.

- [X] T008 [P] Implement `code/power_analysis.py`: Calculate required sample size (N) using `statsmodels.stats.power.FTestPower.solve_power`. **Parameters**: Cohen's f2=0.15 (medium effect), alpha=0.05, power=0.80, k=3 predictors. **Logic**: Fetch species list from `data/raw/nppn.parquet` and `data/raw/try_traits.csv`. If overlap N < 55, **HALT** with critical error "Insufficient species for power analysis (N < 55)". **Deliverable**: `state/power_analysis_report.yaml`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract and Aggregate Root System Architecture Metrics (Priority: P1) 🎯 MVP

**Goal**: Convert raw root images from the NPPN Plant Phenome Pipeline into quantitative architectural metrics (depth, branching density, surface area) to enable downstream statistical analysis.

**Independent Test**: The pipeline can be tested by running the image analysis module on a small, fixed set of known root images and verifying that the output CSV contains non-null, positive numerical values for all defined RSA traits.

### Implementation for User Story 1

- [X] T012 [US1] [D:T008] Implement `code/download_images.py`: Fetch root images from `nppn/root-phenotyping` (HuggingFace ID: `nppn/root-phenotyping`) via `huggingface_hub`. **Logic**: Use `huggingface_hub.snapshot_download` with `allow_patterns` for images. Attempt download. If download fails (exception `RepositoryNotFoundError` or `LocalEntryNotFoundError` or empty directory), **HALT** with critical error "No real NPPN root images found. Pipeline cannot proceed." Do NOT fallback to other datasets. Ensure CPU-optimized, no GPU. **Output**: `data/raw/nppn_images/`.

- [X] T013 [US1] [D:T012] Implement `code/preprocess_images.py`: Extract RSA traits using OpenCV/scikit-image on CPU. **Algorithm**:
 - `skimage.morphology.skeletonize` (8-connectivity) for depth/branching.
 - `cv2.findContours` for surface area.
 - Branching density = (branch_points - endpoints) / total_length.
 - **Includes**: Error logging for corrupted images (skipping them gracefully) and validation logic to ensure no null values and positive numerical values for all traits in output. The exclusion rate (percentage of successfully processed images) is calculated and logged. **Logic**: Calculate the exclusion rate (percentage of successfully processed images) and log it to `state/image_processing_stats.yaml`.
 - **Output**: Generate `data/derived/rsametrics.csv`.

- [X] T015 [US1] [D:T013] Validate `data/derived/rsametrics.csv`. **Schema**: Columns `species_id` (str), `depth` (float, >0), `branching_density` (float, >0), `surface_area` (float, >0). **Logic**: Run T013 on all images. Validate output against `contracts/rsametrics.schema.yaml` using `jsonschema`. If validation fails, log error and halt. **Deliverable**: Validated CSV file.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US1] [D:T012,T013] Unit test in `tests/unit/test_image_processing.py`: Implement `test_load_image_handles_corrupted_file_returns_error` (asserts specific error message) and `test_skeletonize_returns_valid_branch_points` (asserts branch_points > 0).
- [X] T017 [P] [US1] [D:T012,T013] Integration test in `tests/integration/test_image_pipeline.py`: Implement `test_full_pipeline_generates_non_null_csv` (asserts output CSV has a consistent number of rows with no nulls and positive values) on sample data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlate RSA Metrics with Drought Physiology (Priority: P2)

**Goal**: Statistically validate whether deeper or more branched root systems associate with higher stomatal conductance and photosynthetic rates under water stress using the aggregated data.

**⚠️ DEPENDENCY**: This phase depends on the completion of Phase 3 (T015) to ensure `rsametrics.csv` exists before merging.

**Independent Test**: The analysis can be tested by running the regression module on a synthetic dataset with a known positive correlation between a "depth" variable and a "conductance" variable, verifying that the calculated correlation coefficient matches the expected value within an acceptable margin of error.

### Implementation for User Story 2

- [X] T020 [US2] [D:T015] Implement `code/download_traits.py` to fetch physiological trait data from TRY database. **Logic**: Use the `trydata` Python package to query traits (stomatal_conductance, photosynthesis) for the species list derived from `rsametrics.csv` using `trydata.query(species_list, traits=[...])`. Handle authentication via environment variable `TRY_API_KEY`. If no overlap, handle via T021 logic. **Output**: `data/raw/try_traits.csv`.

- [X] T021 [US2] [D:T015, D:T020] Implement `code/merge_data.py` to merge `rsametrics.csv` with physiological data. **Logic**: Handle missing species via listwise deletion using `df.dropna()`. **Constraint**: If sample size < 55, **HALT** with critical error "Insufficient species after merge (N < 55)". **Note**: This is a power analysis requirement, not a spec deviation. **Deliverable**: `data/derived/merged_data.csv`.

- [X] T022 [US2] [D:T021] Implement `code/analysis.py` function `perform_pca()` to transform RSA traits for collinearity handling (VIF > 5 check included). **Logic**: Calculate VIF using `statsmodels.stats.outliers_influence.variance_inflation_factor`. If VIF > 5 for any predictor, flag. Perform PCA on RSA traits. **Deliverable**: `data/derived/pca_results.csv`, `state/vif_report.yaml`.

- [X] T024a [US2] [D:T021] Implement `code/fetch_phylogeny.py`: Fetch phylogenetic tree from Open Tree of Life API. **Logic**:
 1. Attempt fetch via `open_tree_of_life` API.
 2. If fetch fails, **HALT** with critical error "Phylogenetic tree fetch failed. PVR fallback is impossible without a tree. FR-010 violation."
 **Output**: `data/derived/phylogenetic_tree.newick`. **Note**: Implements strict HALT to ensure FR-010 compliance.

- [X] T023a [US2] [D:T021, D:T022, D:T024a] Implement `code/models.py` functions `fit_ols()`, `fit_ridge()`, `fit_lasso()`, AND `fit_pgl()` to predict stomatal conductance/photosynthesis. **Specs**:
 - **PGLS (FR-010)**: MUST implement Phylogenetic Generalized Least Squares using the fetched tree. **Output**: `data/derived/pgls_results.csv`. **Verification**: Ensure `pgls_results.csv` exists and contains columns `model_type` (='PGLS'), `predictor`, `coefficient`, `p_value`, `r2`, `lambda`.
 - R² metric for OLS/Ridge/Lasso.
 - **GroupKFold cross-validation (groups=species_name) with a multi-fold strategy.** to prevent phylogenetic leakage.
 - Alpha search: GridSearchCV across log-spaced values spanning a broad range (only for Ridge/Lasso). **Logic**: GridSearchCV runs ONLY after T021 and T024a confirm valid data and tree presence.
 - Regularization via alpha parameter (only for Ridge/Lasso; OLS has no alpha).
 - **Output**: Generate `data/derived/regression_results.csv` (for OLS/Ridge/Lasso) AND `data/derived/pgls_results.csv` (for PGLS).
 - **Verification**: Ensure `data/derived/regression_results.csv` exists and contains columns `model_type`, `predictor`, `coefficient`, `p_value`, `r2`, `adj_p_value`.

- [X] T023c [US2] [D:T021, D:T022, D:T024a] Implement `code/models.py` function `fit_random_forest()` to predict stomatal conductance/photosynthesis using Random Forest Regression. **Specs**:
 - R² metric.
 - **5-fold GroupKFold (groups=species_name)** to prevent phylogenetic leakage.
 - n_estimators=100, max_depth=None, regularization via min_samples_leaf.
 - Use `sklearn.ensemble.RandomForestRegressor`.
 - **Output**: Generate `data/derived/rf_regression_results.csv`.

- [X] T025 [US2] [D:T023a, T023c] Implement multiple-comparison correction (Bonferroni/FDR) in `code/analysis.py` for hypothesis testing. **Logic**: Apply correction to p-values from T023a, T023c using `statsmodels.stats.multitest.multipletests(..., method="fdr_bh")`. **Verification**: Ensure adjusted p-values are recorded in `model_results.csv`.

- [X] T026 [US2] [D:T022, T023a, T023c, D:T024a] Generate `data/derived/model_results.csv`. **Schema**: Columns `model_type` (str), `predictor` (str), `coefficient` (float), `p_value` (float), `r2` (float), `adj_p_value` (float), `vif` (float), `lambda` (float). **Logic**: Aggregate results from T023a (OLS/Ridge/Lasso/PGLS) and T023c using `pd.concat` and `groupby`. **Edge Case**: If PGLS results are missing (should not happen due to T024a HALT), insert string "N/A" for columns `model_type`, `lambda`, `p_value`. **Verification**: Ensure `model_results.csv` exists and contains "N/A" strings if data is missing, or valid floats otherwise. **Deliverable**: Validated CSV file.

- [X] T026b [US2] [D:T026] **MANDATORY**: Validate PGLS Results. **Logic**: Check if `data/derived/pgls_results.csv` exists and is non-empty. If missing, **HALT** with "PGLS results missing. Cannot proceed to report generation. FR-010 violation." **Deliverable**: `state/pgls_validation.yaml`.

- [X] T026c [US2] [D:T022, T026] Implement report framing logic in `code/generate_report.py`: If VIF > 5 is detected, explicitly suppress independent effect claims for correlated variables in the generated report. Output: `state/vif_compliance_check.yaml` (record of VIF status and suppression action). **Logic**: Output `state/vif_compliance_check.yaml` in YAML format.

- [X] T027 [US2] [D:T021] Implement `code/analysis.py` function `detect_tolerance_proxies()` to check for and ingest 'independent tolerance proxies' (e.g., survival rate) if available, as required by FR-009. Generate explicit framing text in `data/derived/report_framing.md` (predicting 'physiological state'). **Logic**: Check for columns `survival_rate`, `biomass_stress`. **Deliverable**: `state/proxy_detection.yaml` (boolean `has_proxy`).

- [X] T027c [US3] [D:T021, D:T027] Implement `code/models.py` function `binarize_target()` to binarize the target variable. **Logic**: 
 1. Check `state/proxy_detection.yaml` for `has_proxy`.
 2. **If False (No Proxy)**: **MANDATORY**: Binarize the *physiological metrics* (stomatal conductance/photosynthesis) using median split to create a binary target. **DO NOT** skip this step. Generate `data/derived/binary_physio_target.csv` with columns `species_id`, `conductance_bin`, `photosynthesis_bin`. **Deliverable**: `data/derived/binary_physio_target.csv`.
 3. **If True (Proxy Exists)**: Use `df['proxy'] > df['proxy'].median()` to binarize the *proxy* variable. **Deliverable**: `data/derived/binary_target.csv`.
 **Deliverable**: `data/derived/binary_physio_target.csv` (if no proxy) OR `data/derived/binary_target.csv` (if proxy exists).

- [X] T027b [US3] [D:T027, D:T027c, D:T021, D:T022] Implement conditional classification logic in `code/models.py` function `fit_rf_classification()` to predict the binary drought tolerance class (high/low). **Logic**:
 1. Check `state/proxy_detection.yaml` for `has_proxy`.
 2. **If False**: Use `data/derived/binary_physio_target.csv` as the target. **Deliverable**: `data/derived/classification_model.pkl`.
 3. **If True**: Use `data/derived/binary_target.csv` as the target. **Deliverable**: `data/derived/classification_model.pkl`.
 4. **Specs**: F1-score metric, **5-fold GroupKFold (groups=species_name)**, n_estimators=100.
 5. **Output**: Generate `data/derived/classification_model.pkl`.

- [X] T027d [US3] [D:T027] **MANDATORY**: Generate Sensitivity N/A Justification. **Logic**:
 1. Check `state/proxy_detection.yaml` for `has_proxy`.
 2. **If False**: Generate `results/sensitivity_na_justification.md` with text: "Sensitivity analysis skipped: No independent tolerance proxy found. Classification model not trained. Binarization of physiological metrics was performed as per FR-007, but classification was skipped to avoid circularity. See T027c for justification." **Deliverable**: `results/sensitivity_na_justification.md`.
 3. **If True**: Generate `results/sensitivity_na_justification.md` with text: "Sensitivity analysis performed. See sensitivity sweep results."
 **Verification**: Ensure `results/sensitivity_na_justification.md` exists in all cases.

- [X] T028 [US3] [D:T027b, D:T027d] Implement `code/analysis.py` function `run_sensitivity_analysis()`. **Logic**:
 1. Check `state/classification_status.yaml`. If status is "SKIPPED", output 'N/A' with justification in `results/sensitivity_sweep_results.csv` and exit.
 2. **If classification exists**: Sweep predicted probability threshold across the full range (0.0 to 1.0) using `np.arange(0.0, 1.0, 0.01)`.
 3. Calculate and report variation in accuracy, precision, recall, F1, **False Positive Rate, and False Negative Rate** for each step.
 4. **Explicitly isolate and report** the metrics for the ±0.05 deviation window around the baseline (optimal F1 or 0.5).
 5. **Output**: `data/derived/sensitivity_sweep_results.csv` and `results/figures/sensitivity_curve.png` (if applicable).
 6. **Output**: `results/sensitivity_fpr_fnr.csv`.

- [X] T028a [US3] [D:T027b, D:T028] **MANDATORY**: Generate Sensitivity N/A Justification. **Logic**:
 1. Check `state/classification_status.yaml`.
 2. **If status == 'SKIPPED' OR if T027b/T028 were not executed due to missing proxy**: Generate `results/sensitivity_na_justification.md` with text: "Sensitivity analysis skipped: No independent tolerance proxy found. Classification model not trained. Binarization of physiological metrics was performed as per FR-007, but classification was skipped to avoid circularity. See T027c for justification." **Deliverable**: `results/sensitivity_na_justification.md`.
 3. **If status != 'SKIPPED'**: Generate `results/sensitivity_na_justification.md` with text: "Sensitivity analysis performed. See sensitivity sweep results."
 **Verification**: Ensure `results/sensitivity_na_justification.md` exists in all cases.

- [X] T029 [US3] [D:T028, T028a, D:T026b] Generate sensitivity report in `data/derived/sensitivity_report.md` including threshold justification and impact analysis. **Logic**: Use `templates/sensitivity_report.md` template. Ensure the report explicitly states the threshold used and the robustness of the results. **Conditional**: If `results/sensitivity_na_justification.md` exists, include its content in the report. **Deliverable**: `data/derived/sensitivity_report.md`.

- [ ] T045 [US2] [D:T022] Generate VIF visualization in `results/figures/vif_heatmap.png`. **Logic**: Read VIF scores from `state/vif_report.yaml`. Use `seaborn.heatmap` with `cmap='viridis'` to plot the correlation matrix and VIF scores. **Deliverable**: `results/figures/vif_heatmap.png` (Required for SC-004).

- [ ] T046 [US3] [D:T028, T028a] Generate sensitivity analysis plot in `results/figures/sensitivity_curve.png`. **Logic**: 
 1. Check `state/classification_status.yaml`.
 2. **If status == 'SKIPPED'**: Read `results/sensitivity_na_justification.md` and generate a placeholder plot or skip. **Deliverable**: `results/figures/sensitivity_curve.png` (placeholder or N/A).
 3. **If status != 'SKIPPED'**: Read columns `threshold`, `FPR`, `FNR` from `results/sensitivity_fpr_fnr.csv`. Plot using `matplotlib` with threshold on X-axis and FPR/FNR on Y-axis. **Deliverable**: `results/figures/sensitivity_curve.png` (Required for SC-003).

- [X] T047 [US2] [D:T023a] Implement PGLS robustness check via leave-one-out cross-validation (LOOCV) on the phylogenetic tree. **Logic**: Iteratively remove one species from the tree and re-run PGLS. Aggregate results into `results/pgls_loocv_summary.csv` with columns `species_removed`, `coefficient_mean`, `coefficient_std`. **Deliverable**: `results/pgls_loocv_summary.csv`.

- [X] T048 [US3] [D:T027] Add a "No Proxy" fallback report section. **Logic**: If `has_proxy` is False, generate a specific section in `results/reports/final_report.md` titled "Classification Skipped: No Independent Proxy Found". Explicitly state the classification model was skipped, explain the scientific reasoning (avoiding circularity), and frame the results purely as associational predictions of physiological state. **Deliverable**: Updated `results/reports/final_report.md`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T037 [US3] [D:T028] Unit test in `tests/unit/test_sensitivity.py`: Implement `test_sensitivity_sweep_generates_valid_range` (asserts output covers full alpha range).
- [X] T038 [US3] [D:T028] Integration test in `tests/integration/test_sensitivity.py`: Implement `test_sensitivity_report_contains_expected_metrics` (asserts report contains threshold variation data).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Predictive Robustness via Sensitivity Analysis (Priority: P3)

**Goal**: Confirm that the predictive thresholds used in the classification model are not arbitrary. **Note**: As per spec, the classification model (FR-007/008) is REQUIRED to enable the sensitivity analysis. This phase implements the classification model and the threshold sweep.

**Independent Test**: The sensitivity module can be tested by running the model with a primary threshold and then verifying that the output includes a plot or table showing how the false-positive/false-negative rates change.

*Note: Implementation tasks for US3 (T027b, T028, T029) are located in Phase 4 to maintain correct dependency ordering.*

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032a [P] Update `README.md` with Installation, Usage, and Results sections. **Logic**: Add detailed installation instructions, usage examples, and results interpretation to satisfy Constitution Principles I and IV. **Sections**: Installation, Usage, Results.

- [X] T032b [P] Update `docs/` with API documentation and quickstart guide. **Logic**: Use `pdoc` to generate API docs from docstrings and create `quickstart.md` to satisfy Constitution Principles I and IV.

- [X] T033 [P] Code cleanup and refactoring. **Logic**: Remove unused imports, fix linting errors using ruff/black.

- [ ] T034a [P] [D:T012,T013] Profile memory usage of image loading pipeline. **Logic**: Use `memory_profiler`. **Deliverable**: `docs/memory_profile.md` with peak usage <7GB.

- [ ] T034b [P] [D:T012,T013] Profile total pipeline runtime. **Logic**: Use `cProfile`. **Deliverable**: `state/runtime_profile.yaml` with total runtime. **Logic**: Verify total runtime <= 6h.

- [ ] T034c [P] Optimize image loading to use generators if profiling shows memory issues. **Logic**: Use Python generators (`yield`) for image loading.

- [X] T035 [P] Additional unit tests for data hygiene and checksums in `tests/unit/`. **Logic**: Add `test_data_checksums`, `test_no_pii`.

- [X] T036 [P] Run `quickstart.md` validation. **Logic**: Run `python -m pytest tests/contract/`.

---

## Phase R: Revision & Review Resolution

**Purpose**: Address specific review concerns regarding data integrity, streaming, and error handling.

- [ ] T039a [US1] [D:T012] Refactor `code/download_images.py` to implement **streaming** for large NPPN datasets. **Logic**:
 1. Use `huggingface_hub` streaming API to list repository files.
 2. Implement a generator that downloads and processes images in chunks (e.g., a manageable batch size) to ensure memory usage remains within acceptable limits.
 3. **Constraint**: Do NOT download the entire repository to local disk if it exceeds a significant storage threshold; process and discard raw images immediately after RSA extraction.
 4. **Verification**: Run `code/profile_memory.py` to generate the profile. Ensure `state/memory_profile.md` confirms peak memory < 7GB during full dataset processing.

- [ ] T039b [US1] [D:T039a] Verify memory profile of image loading pipeline. **Logic**: Run `code/profile_memory.py` and generate `state/memory_profile.md`. Ensure peak memory < 7GB. **Deliverable**: `state/memory_profile.md`.

- [ ] T040 [US1] [D:T012] Update `code/download_images.py` to strictly **FAIL LOUDLY** on fetch errors. **Logic**:
 1. Remove any `try/except` blocks that catch `RepositoryNotFoundError` or `HTTPError` and fall back to synthetic data.
 2. Ensure the script raises a `RuntimeError` with the exact message "No real NPPN root images found. Pipeline cannot proceed." if the fetch fails.
 3. **Verification**: Add unit test `test_download_fails_loudly` in `tests/unit/test_download.py` asserting `RuntimeError: No real NPPN root images found. Pipeline cannot proceed."

- [ ] T042 [US2] [D:T015] Update `code/merge_data.py` to handle **species-level stratification** explicitly. **Logic**:
 1. Ensure that the merge operation preserves species IDs.
 2. Add a check to verify that the merged dataset does not contain duplicate species entries that could bias the GroupKFold.
 3. **Verification**: Add unit test in `tests/unit/test_merge.py` asserting unique species IDs in the merged output.

- [ ] T043 [US2] [D:T022] Enhance `code/analysis.py` to report **VIF scores** for all predictors, not just flagging those > 5. **Logic**:
 1. Calculate VIF for every predictor in the model.
 2. Log the full VIF table to `state/vif_report.yaml` in YAML format.
 3. **Verification**: Ensure `state/vif_report.yaml` contains a complete table of VIF scores for all predictors.

- [ ] T044 [US3] [D:T023a] Update `code/models.py` to ensure **GroupKFold** is correctly applied in `fit_rf_classification`. **Logic**:
 1. Verify that `groups=species_name` is passed to the `GroupKFold` splitter.
 2. Add a check to ensure that no species appears in both training and test sets within a fold.
 3. **Verification**: Add unit test in `tests/unit/test_models.py` asserting that GroupKFold prevents species leakage.

- [ ] T045 [US3] [D:T028] Refine `code/analysis.py` to ensure sensitivity analysis covers the full range of thresholds. **Logic**:
 1. Implement a sweep across the full range of the parameter with a fine step size.
 2. Ensure the output includes FPR and FNR for each step.
 3. **Verification**: Add unit test in `tests/unit/test_sensitivity.py` asserting that the output covers the full threshold range.

- [ ] T051 [US1] [D:T012] Add checksum verification for all downloaded NPPN images in `code/download_images.py`. **Logic**:
 1. If `data/raw/nppn_checksums.json` does not exist, compute SHA256 of all files in `data/raw/nppn_images/` and write to JSON.
 2. If `data/raw/nppn_checksums.json` exists, compare SHA256 of downloaded files against manifest.
 3. If mismatch, **HALT** with "Data integrity check failed: checksum mismatch".
 4. **Deliverable**: `data/raw/nppn_checksums.json`.

- [X] T052 [US3] [D:T027b] Add explicit "No Circular Classification" assertion in `code/models.py` for `fit_rf_classification`. **Logic**: Assert that the target variable for binarization is NOT the same as the dependent variable in the regression models (e.g., `conductance`). If `has_proxy` is False, ensure the code path strictly skips binarization of `conductance`.

- [X] T053 [US2] [D:T024a] Add retry logic with exponential backoff for Open Tree of Life API fetch in `code/fetch_phylogeny.py`. **Logic**: Retry up to 3 times with 5s, 10s, 20s delays. If all fail, HALT with "Phylogenetic tree fetch failed after retries."

- [ ] T054 [US2] [D:T022] **MANDATORY**: Implement VIF Compliance Check. **Logic**: Ensure `state/vif_compliance_check.yaml` is generated and validated. If VIF > 5, ensure report suppression logic is active. **Deliverable**: `state/vif_compliance_check.yaml`.

- [ ] T055 [US3] [D:T028] **MANDATORY**: Implement Sensitivity Plot Generation. **Logic**: Ensure `results/figures/sensitivity_curve.png` is generated with FPR/FNR curves. **Deliverable**: `results/figures/sensitivity_curve.png`.

---

## Phase Z: Final Verification & Handoff

**Purpose**: Final validation of all constraints before marking the project complete.

- [ ] T059 [P] [US1, US2, US3] Run end-end pipeline on a small subset of images to verify all dependencies, streaming logic, and error handling paths function correctly. **Logic**: Execute `python code/pipeline.py --subset 50`. Verify `state/pipeline.log` shows no synthetic fallbacks and all critical checks passed. **Deliverable**: `state/e2e_validation_report.yaml`.

- [ ] T060 [P] [US1, US2, US3] Verify all generated artifacts against their respective JSON schemas in `contracts/`. **Logic**: Run `python tests/contract/test_all_schemas.py`. Ensure [deferred] pass rate. **Deliverable**: Updated `state/artifact_hashes.yaml` with new validation timestamp.

- [ ] T061 [P] [US1, US2, US3] Final check: Ensure no `try/except` blocks in data loading code paths silently swallow errors or fallback to synthetic data. **Logic**: Manual code review or static analysis scan for `try/except` in `code/download*.py` and `code/merge*.py`. **Deliverable**: `state/code_review_checklist.yaml`.

- [ ] T062 [P] [US1, US2, US3] Confirm that if `has_proxy` is False, the report explicitly states "Classification Skipped" and does not attempt to binarize physiological metrics. **Logic**: Run pipeline with a mock dataset lacking a proxy. Verify `results/reports/final_report.md` contains the correct framing. **Deliverable**: Updated `results/reports/final_report.md` (mock run).