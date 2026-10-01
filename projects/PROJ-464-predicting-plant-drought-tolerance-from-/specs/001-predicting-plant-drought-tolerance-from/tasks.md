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
  4. `contracts/model_results.schema.yaml`: Validates model outputs, VIF, and sensitivity (FR-004, FR-005, FR-006). Fields: `model_type` (str), `predictor` (str), `coefficient` (float), `p_value` (float), `r2` (float), `adj_p_value` (float), `vif` (float).
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

- [X] T023a [US2] [D:T021] Implement `code/models.py` functions `fit_ols()`, `fit_ridge()`, `fit_lasso()` to predict stomatal conductance/photosynthesis. **Specs**:
  - R² metric.
  - **GroupKFold cross-validation (groups=species_name) with a multi-fold strategy.** to prevent phylogenetic leakage.
  - Alpha search: GridSearchCV across log-spaced values spanning a range from `np.logspace(, 3, 10)`.
  - Regularization via alpha parameter (only for Ridge/Lasso; OLS has no alpha).
  - **Output**: Generate `data/derived/regression_results.csv`.

- [X] T023c [US2] [D:T021] Implement `code/models.py` function `fit_random_forest()` to predict stomatal conductance/photosynthesis using Random Forest Regression. **Specs**:
  - R² metric.
  - **5-fold GroupKFold (groups=species_name)** to prevent phylogenetic leakage.
  - n_estimators=100, max_depth=None, regularization via min_samples_leaf.
  - Use `sklearn.ensemble.RandomForestRegressor`.
  - **Output**: Generate `data/derived/rf_regression_results.csv`.

- [X] T024a [US2] [D:T021] Implement `code/fetch_phylogeny.py`: Fetch phylogenetic tree from Open Tree of Life API. **Logic**:
 1. Attempt fetch via `open_tree_of_life` API.
 2. If fetch fails, **HALT** with critical error "Phylogenetic tree fetch failed. PVR fallback is impossible without a tree. FR-010 violation."
  **Output**: `data/derived/phylogenetic_tree.newick`. **Note**: Implements strict HALT to ensure FR-010 compliance.

- [X] T024b [US2] [D:T024a, D:T021] Implement `code/models.py` function `fit_pgl()` to perform Phylogenetic Generalized Least Squares (PGLS). **Logic**:
  - Construct `comparative.data` object using `caper.comparative.data(phy=phylogenetic_tree, data=merged_data, labels='species_id')`.
  - Fit model: `pgls(formula='conductance ~ depth + surface_area', data=cd_object)`.
  - **Deliverable**: Generate `data/derived/pgls_results.csv`.

- [X] T025 [US2] [D:T023a, T023c, T024b] Implement multiple-comparison correction (Bonferroni/FDR) in `code/analysis.py` for hypothesis testing. **Logic**: Apply correction to p-values from Ta, T023c, T024b using `statsmodels.stats.multitest.multipletests(..., method="fdr_bh")`. **Verification**: Ensure adjusted p-values are recorded in `model_results.csv`.

- [X] T026 [US2] [D:T022, T023a, T023c, T025] Generate `data/derived/model_results.csv`. **Schema**: Columns `model_type` (str), `predictor` (str), `coefficient` (float), `p_value` (float), `r2` (float), `adj_p_value` (float), `vif` (float). **Logic**: Aggregate results from T023a, T023c, and T024b using `pd.concat` and `groupby`. If a source is missing (e.g., T024b failed), insert `NaN` or 'N/A' for that model type. Apply adjusted p-values from T025 to the aggregated results. **Deliverable**: Validated CSV file.

- [X] T026b [US2] [D:T022, T026] Implement report framing logic in `code/generate_report.py`: If VIF > 5 is detected, explicitly suppress independent effect claims for correlated variables in the generated report. Output: `state/vif_compliance_check.yaml` (record of VIF status and suppression action). **Logic**: Output `state/vif_compliance_check.yaml` in YAML format.

- [X] T027 [US2] [D:T021] Implement `code/analysis.py` function `detect_tolerance_proxies()` to check for and ingest 'independent tolerance proxies' (e.g., survival rate) if available, as required by FR-009. Generate explicit framing text in `data/derived/report_framing.md` (predicting 'physiological state'). **Logic**: Check for columns `survival_rate`, `biomass_stress`. **Deliverable**: `state/proxy_detection.yaml` (boolean `has_proxy`).

- [X] T027c [US3] [D:T021] Implement `code/models.py` function `binarize_target()` to binarize the proxy variable using median split. **Logic**: Use `df['proxy'] > df['proxy'].median()`. **Deliverable**: `data/derived/binary_target.csv`.

- [X] T027b [US3] [D:T015, D:T021, D:T022, D:T027, D:T027c] Implement `code/models.py` function `fit_rf_classification()` to predict the binary drought tolerance class (high/low). **Logic**:
 1. Use the binarized target from T027c (`data/derived/binary_target.csv`).
 2. Train Random Forest Classification model. **Specs**: F1-score metric, **5-fold GroupKFold (groups=species_name)**, n_estimators=100.
 3. **Conditional**: Per Plan override of FR-007/FR-008: Classification is conditional on independent proxy existence. If `has_proxy` is False, generate `state/classification_status.yaml` with status "SKIPPED". If `has_proxy` is True, generate `data/derived/classification_model.pkl`.
 4. **Output**: Generate `data/derived/classification_model.pkl` OR `state/classification_status.yaml`.

- [X] T028 [US3] [D:T027b, D:T027c] Implement `code/analysis.py` function `run_sensitivity_analysis()`. **Logic**:
 1. Sweep predicted probability threshold across the full range (to 1.0) using `np.arange(0.0, 1.0, 0.01)`.
 2. Calculate and report variation in accuracy, precision, recall, F1, **False Positive Rate, and False Negative Rate** for each step.
 3. **Explicitly isolate and report** the metrics for the ±0.05 deviation window around the baseline (optimal F1 or 0.5).
 4. **Conditional**: Per Plan override: Sensitivity analysis is conditional on classification execution. If classification was skipped, output 'N/A' with justification.
 5. **Output**: `data/derived/sensitivity_sweep_results.csv` and `results/figures/sensitivity_curve.png` (if applicable).
 6. **Output**: `results/sensitivity_fpr_fnr.csv`.

- [X] T029 [US3] [D:T028] Generate sensitivity report in `data/derived/sensitivity_report.md` including threshold justification and impact analysis. **Logic**: Use `templates/sensitivity_report.md` template. Ensure the report explicitly states the threshold used and the robustness of the results.

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

- [X] T034a [P] [D:T012,T013] Profile memory usage of image loading pipeline. **Logic**: Use `memory_profiler`. **Deliverable**: `docs/memory_profile.md` with peak usage <7GB.

- [X] T034b [P] [D:T012,T013] Profile total pipeline runtime. **Logic**: Use `cProfile`. **Deliverable**: `state/runtime_profile.yaml` with total runtime. **Logic**: Verify total runtime <= 6h.

- [X] T034c [P] Optimize image loading to use generators if profiling shows memory issues. **Logic**: Use Python generators (`yield`) for image loading.

- [X] T035 [P] Additional unit tests for data hygiene and checksums in `tests/unit/`. **Logic**: Add `test_data_checksums`, `test_no_pii`.

- [X] T036 [P] Run `quickstart.md` validation. **Logic**: Run `python -m pytest tests/contract/`.

---

## Phase R: Revision & Review Resolution

**Purpose**: Address specific review concerns regarding data integrity, streaming, and error handling.

- [ ] T039 [US1] [D:T012] Refactor `code/download_images.py` to implement **streaming** for large NPPN datasets. **Logic**:
 1. Use `huggingface_hub` streaming API to list repository files.
 2. Implement a generator that downloads and processes images in chunks (e.g., a manageable batch size) to ensure memory usage remains within acceptable limits.
 3. **Constraint**: Do NOT download the entire repository to local disk if it exceeds a significant storage threshold; process and discard raw images immediately after RSA extraction.
 4. **Verification**: Run `code/profile_memory.py` to generate the profile. Ensure `state/memory_profile.md` confirms peak memory < 7GB during full dataset processing.

- [ ] T040 [US1] [D:T012] Update `code/download_images.py` to strictly **FAIL LOUDLY** on fetch errors. **Logic**:
 1. Remove any `try/except` blocks that catch `RepositoryNotFoundError` or `HTTPError` and fall back to synthetic data.
 2. Ensure the script raises a `RuntimeError` with the exact message "No real NPPN root images found. Pipeline cannot proceed." if the fetch fails.
 3. **Verification**: Add unit test `test_download_fails_loudly` in `tests/unit/test_download.py` asserting `RuntimeError: No real NPPN root images found. Pipeline cannot proceed."

- [ ] T041 [US2] [D:T020] Refactor `code/download_traits.py` to use **streaming** or chunked processing for large TRY datasets. **Logic**:
 1. If the TRY dataset is too large for a single fetch, implement chunked fetching or use the `trydata` streaming API.
 2. Accumulate results in `data/raw/try_traits.csv` incrementally.
 3. **Verification**: Ensure `state/memory_profile.md` confirms peak memory < 7GB during trait ingestion.

- [ ] T042 [US2] [D:T015] Update `code/merge_data.py` to handle **species-level stratification** explicitly. **Logic**:
 1. Ensure that the merge operation preserves species IDs.
 2. Add a check to verify that the merged dataset does not contain duplicate species entries that could bias the GroupKFold.
 3. **Verification**: Add unit test in `tests/unit/test_merge.py` asserting unique species IDs in the merged output.

- [ ] T043 [US2] [D:T022] Enhance `code/analysis.py` to report **VIF scores** for all predictors, not just flagging those > 5. **Logic**:
 1. Calculate VIF for every predictor in the model.
 2. Log the full VIF table to `state/vif_report.yaml` in YAML format.
 3. **Verification**: Ensure `state/vif_report.yaml` contains a complete table of VIF scores for all predictors.

- [ ] T044 [US3] [D:T024b] Update `code/models.py` to ensure **GroupKFold** is correctly applied in `fit_rf_classification`. **Logic**:
 1. Verify that `groups=species_name` is passed to the `GroupKFold` splitter.
 2. Add a check to ensure that no species appears in both training and test sets within a fold.
 3. **Verification**: Add unit test in `tests/unit/test_models.py` asserting that GroupKFold prevents species leakage.

- [ ] T045 [US3] [D:T028] Refine `code/analysis.py` to ensure sensitivity analysis covers the full range of thresholds. **Logic**:
 1. Implement a sweep across the full range of the parameter with a fine step size.
 2. Ensure the output includes FPR and FNR for each step.
 3. **Verification**: Add unit test in `tests/unit/test_sensitivity.py` asserting that the output covers the full threshold range.

---

## Phase N+1: Revision & Review Resolution

**Purpose**: Address specific reviewer concerns from prior research-stage reviews regarding data integrity and pipeline robustness.

- [ ] T040 [US2] [D:T021] Implement robust data streaming for large TRY/NPPN subsets in `code/download_traits.py` and `code/download_images.py`. **Logic**: If dataset size exceeds 14GB disk or 7GB RAM, switch to `datasets.load_dataset(..., streaming=True)` or chunked processing. **Constraint**: Do NOT fall back to synthetic data; if streaming fails, HALT with "Real data stream failed; cannot proceed."
- [ ] T041 [US2] [D:T040] Add explicit power analysis validation in `code/merge_data.py` to ensure the *streamed* sample size meets N >= 55. **Logic**: If N < 55 after streaming/sampling, HALT with "Insufficient real data for power analysis (N < 55) even after streaming."
- [ ] T042 [US1] [D:T012] Add checksum verification for all downloaded NPPN images in `code/download_images.py`. **Logic**: If `data/raw/nppn_checksums.json` does not exist, generate it from the initial download. Compare SHA256 of downloaded files against manifest. If mismatch, HALT with "Data integrity check failed for NPPN images."
- [ ] T043 [US3] [D:T027b] Add explicit "No Circular Classification" assertion in `code/models.py` for `fit_rf_classification`. **Logic**: Assert that the target variable for binarization is NOT the same as the dependent variable in the regression models (e.g., `conductance`). If `has_proxy` is False, ensure the code path strictly skips binarization of `conductance`.
- [ ] T044 [US2] [D:T024a] Add retry logic with exponential backoff for Open Tree of Life API fetch in `code/fetch_phylogeny.py`. **Logic**: Retry up to 3 times with 5s, 10s, 20s delays. If all fail, HALT with "Phylogenetic tree fetch failed after retries."
- [ ] T045 [US2] [D:T022] Add VIF visualization in `results/figures/vif_heatmap.png`. **Logic**: Generate a heatmap of VIF scores for all predictors to explicitly demonstrate collinearity handling in the final report.
- [ ] T046 [US3] [D:T028] Add sensitivity analysis plot in `results/figures/sensitivity_curve.png`. **Logic**: Plot FPR/FNR vs. Threshold to visually demonstrate robustness of the classification threshold.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase R)**: Depends on completion of relevant User Story phases

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data (merged dataset)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 results (model outputs)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Notes

- [P] tasks = different files, no dependencies
- [D:ID] tasks = depends on completion of task ID
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Spec Gaps Addressed**: Tasks use NPPN (no fallback), PGLS (strict tree requirement with fallback), and Classification (mandatory median-split on primary metrics if no proxy). Documentation tasks confirm these implementations.

### Project Structure Note

To resolve file collision concerns, the following file split is mandated:
- `code/download_images.py` (T012)
- `code/download_traits.py` (T020)
- `code/preprocess_images.py` (T013)
- `code/merge_data.py` (T021)
- `code/models.py` (T022, T023a, T023c, T024b, T027b, T027c) - Contains functions `perform_pca`, `fit_ols`, `fit_ridge`, `fit_lasso`, `fit_random_forest`, `fit_pgl`, `fit_rf_classification`, `binarize_target`
- `code/analysis.py` (T022, T025, T027, T028) - Contains functions `perform_pca`, `multiple_comparison_correction`, `run_sensitivity_analysis`, `detect_tolerance_proxies`
- `code/fetch_phylogeny.py` (T024a) - Contains functions `fetch_tree`, `construct_pvr_covariance`