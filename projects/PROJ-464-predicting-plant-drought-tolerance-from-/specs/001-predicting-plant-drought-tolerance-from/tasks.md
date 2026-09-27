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

- [X] T001a [P] Create project directories: `data/raw/`, `data/derived/`, `code/`, `tests/`, `docs/`, `state/`, `contracts/`, `results/`.
- [X] T001b [P] Initialize `README.md` and `requirements.txt` (empty).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Initialize Python 3.11 project with dependencies in `requirements.txt` (pandas>=2.0.0, numpy>=1.24.0, scikit-learn>=1.3.0, scipy>=1.11.0, statsmodels>=0.14.0, opencv-python-headless>=4.8.0, scikit-image>=0.21.0, requests>=2.31.0, huggingface_hub>=0.16.0, pytest>=7.0.0, networkx>=3.0, caper>=1.0.0, ete3>=3.1.0). **Note**: `pandas-phy` and `ete3` added for PGLS/PVR support.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools.
- [X] T004 [P] Implement `code/config.py` with paths, random seeds (42), and hyperparameters.
- [X] T005 [P] Setup logging infrastructure in `code/__init__.py`.
- [X] T006 [P] Create base data models/entities in `code/models.py` referencing `data-model.md` schema: `RootImage` {id: str, path: str, species: str}, `RSAMetrics` {depth: float, branching_density: float, surface_area: float}, `PhysioTrait` {species: str, conductance: float, photosynthesis: float, survival_rate: float?}. Include validation rules.
- [X] T007 [P] [D:T001a, D:T002] Create base data validation schema checks in `contracts/`. **Deliverables**:
 1. `contracts/dataset.schema.yaml`: Validates merged data structure (FR-001, FR-002). Fields: `species_id` (str), `depth` (float, >0), `branching_density` (float, >0), `surface_area` (float, >0), `conductance` (float), `photosynthesis` (float).
 2. `contracts/rsametrics.schema.yaml`: Validates extracted traits (FR-002, SC-001). Fields: `species_id` (str), `depth` (float, >0), `branching_density` (float, >0), `surface_area` (float, >0).
 3. `contracts/merged_data.schema.yaml`: Validates joined data and PCA/PVR fields (FR-003, FR-010). Fields: `species_id` (str), `depth` (float), `branching_density` (float), `surface_area` (float), `conductance` (float), `photosynthesis` (float), `pca_depth` (float), `pca_branching` (float), `pca_surface` (float).
 4. `contracts/model_results.schema.yaml`: Validates model outputs, VIF, and sensitivity (FR-004, FR-005, FR-006). Fields: `model_type` (str), `predictor` (str), `coefficient` (float), `p_value` (float), `r2` (float), `adj_p_value` (float), `vif` (float).
 5. `contracts/output.schema.yaml`: Validates final report framing (FR-009). Fields: `framing` (str: 'associational' or 'causal'), `threshold_justification` (str).
 6. `contracts/results.schema.yaml`: Validates sensitivity sweep details (FR-005, SC-003). Fields: `threshold` (float), `accuracy` (float), `precision` (float), `recall` (float), `f1` (float), `fpr` (float), `fnr` (float).
 **Logic**: Define JSON schemas for each artifact. Ensure T015, T021, and T026 validate against these schemas. **Verification**: Ensure `tests/contract/` suite is configured to validate all generated artifacts against these schemas.
- [X] T008 [P] Implement `code/power_analysis.py`: Calculate required sample size (N) using `statsmodels.stats.power.FTestPower`. **Parameters**: Cohen's f2=0.15 (medium effect), alpha=0.05, power=0.80, k=3 predictors. **Logic**: Fetch species list from NPPN/MGB3 and TRY. If overlap N < 55, **HALT** with critical error "Insufficient species for power analysis (N < 55)". **Deliverable**: `state/power_analysis_report.yaml`.
- [X] T024a [US2] [D:T008] Implement `code/fetch_phylogeny.py`: Fetch phylogenetic tree from Open Tree of Life API. **Logic**: 
 1. Attempt fetch via `open_tree_of_life` API. 
 2. If fetch fails, **HALT** with critical error "Phylogenetic tree fetch failed. PVR fallback is impossible without a tree. FR-010 violation." (Per Plan: No fallback allowed). 
  **Output**: `data/derived/phylogenetic_tree.newick`. **Note**: Implements strict HALT to ensure FR-010 compliance.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract and Aggregate Root System Architecture Metrics (Priority: P1) 🎯 MVP

**Goal**: Convert raw root images from the NPPN Plant Phenome Pipeline into quantitative architectural metrics (depth, branching density, surface area) to enable downstream statistical analysis.

**Independent Test**: The pipeline can be tested by running the image analysis module on a small, fixed set of known root images and verifying that the output CSV contains non-null, positive numerical values for all defined RSA traits.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download_images.py`: Fetch root images from `nppn/root-phenotyping` (HuggingFace ID: `nppn/root-phenotyping`) via `huggingface_hub`. **Logic**: Attempt download. If download fails (exception `RepositoryNotFoundError` or `LocalEntryNotFoundError` or empty directory), **HALT** with critical error "No real NPPN root images found. Pipeline cannot proceed." Do NOT fallback to other datasets. Ensure CPU-optimized, no GPU. Output: `data/raw/nppn_images/`.
- [X] T013 [US1] [D:T012] Implement `code/preprocess_images.py`: Extract RSA traits using OpenCV/scikit-image on CPU. **Algorithm**: 
  - `skeletonize` (8-connectivity) for depth/branching. 
  - `find_contours` for surface area. 
  - Branching density = (branch_points - endpoints) / total_length. 
  - **Includes**: Error logging for corrupted images (skipping them gracefully) and validation logic to ensure no null values and positive numerical values for all traits in output.
- [X] T015 [US1] [D:T013] Generate `data/derived/rsametrics.csv`. **Schema**: Columns `species_id` (str), `depth` (float, >0), `branching_density` (float, >0), `surface_area` (float, >0). **Logic**: Run T013 on all images. Validate output against `contracts/rsametrics.schema.yaml`. If validation fails, log error and halt. **Deliverable**: Validated CSV file.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests depend on implementation. Write them first, but they run after code exists.

- [X] T016 [P] [US1] [D:T012,T013] Unit test in `tests/unit/test_image_processing.py`: Implement `test_load_image_handles_corrupted_file_returns_error` (asserts specific error message) and `test_skeletonize_returns_valid_branch_points` (asserts branch_points > 0).
- [X] T017 [P] [US1] [D:T012,T013] Integration test in `tests/integration/test_image_pipeline.py`: Implement `test_full_pipeline_generates_non_null_csv` (asserts output CSV has a consistent number of rows with no nulls and positive values) on sample data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlate RSA Metrics with Drought Physiology (Priority: P2)

**Goal**: Statistically validate whether deeper or more branched root systems associate with higher stomatal conductance and photosynthetic rates under water stress using the aggregated data.

**⚠️ DEPENDENCY**: This phase depends on the completion of Phase 3 (T015) to ensure `rsametrics.csv` exists before merging.

**Independent Test**: The analysis can be tested by running the regression module on a synthetic dataset with a known positive correlation between a "depth" variable and a "conductance" variable, verifying that the calculated correlation coefficient matches the expected value within an acceptable margin of error.

### Implementation for User Story 2

- [X] T020 [US2] [D:T008] Implement `code/download_traits.py` to fetch physiological trait data from TRY database. **Logic**: Use the `trydata` Python package to query traits (stomatal_conductance, photosynthesis) for the species list derived from `rsametrics.csv`. Handle authentication via environment variable `TRY_API_KEY`. If no overlap, handle via T021 logic. **Note**: Dependency on T015 removed to allow parallel execution.
- [X] T021 [US2] [D:T015, D:T020] Implement `code/merge_data.py` to merge `rsametrics.csv` with physiological data. **Logic**: Handle missing species via listwise deletion. **Constraint**: If sample size < 55, **HALT** with critical error "Insufficient species after merge (N < 55)". **Note**: This deviates from Spec Assumptions (which allow mean imputation) per the Plan's decision to enforce stricter data hygiene; this deviation is intentional and documented. **Deliverable**: `data/derived/merged_data.csv`.
- [X] T022 [US2] [D:T021] Implement `code/analysis.py` function `perform_pca()` to transform RSA traits for collinearity handling (VIF > 5 check included). **Logic**: Calculate VIF. If VIF > 5 for any predictor, flag. Perform PCA on RSA traits. **Deliverable**: `data/derived/pca_results.csv`, `state/vif_report.yaml`.
- [X] T023a [US2] [D:T021] Implement `code/models.py` functions `fit_ols()`, `fit_ridge()`, `fit_lasso()` to predict stomatal conductance/photosynthesis. **Specs**: 
  - R² metric. 
  - **5-fold GroupKFold (groups=species_name)** to prevent phylogenetic leakage. 
  - Alpha search: GridSearchCV across log-spaced values spanning a range from a lower bound to an upper bound. 
  - Regularization via alpha parameter (only for Ridge/Lasso; OLS has no alpha).
- [X] T023c [US2] [D:T021] Implement `code/models.py` function `fit_random_forest()` to predict stomatal conductance/photosynthesis using Random Forest Regression. **Specs**: 
  - R² metric. 
  - **5-fold GroupKFold (groups=species_name)** to prevent phylogenetic leakage. 
  - n_estimators=100, max_depth=None, regularization via min_samples_leaf.
- [X] T024b [US2] [D:T024a, D:T021] Implement `code/models.py` function `fit_pgl()` to perform Phylogenetic Generalized Least Squares (PGLS). **Logic**: 
  - Construct `comparative.data` object using `caper.comparative.data(phy=phylogenetic_tree, data=merged_data, labels='species_id')`.
  - Fit model: `pgls(formula='conductance ~ depth + surface_area', data=cd_object)`.
  - **Deliverable**: `data/derived/pgls_results.csv`.
- [X] T025 [US2] [D:T023a, D:T023c, D:T022] Implement multiple-comparison correction (Bonferroni/FDR) in `code/analysis.py` for hypothesis testing. **Logic**: Apply correction to p-values from T023a, T023c, T022. **Verification**: Ensure adjusted p-values are recorded in `model_results.csv`.
- [X] T026 [US2] [D:T022, D:T023a, D:T023c, D:T025] Generate `data/derived/model_results.csv`. **Schema**: Columns `model_type` (str), `predictor` (str), `coefficient` (float), `p_value` (float), `r2` (float), `adj_p_value` (float). **Logic**: Aggregate results from T023a, T023c, T025. If T024b succeeded, include PGLS results; otherwise, mark as 'N/A'. Apply adjusted p-values from T025. **Deliverable**: Validated CSV file.
- [X] T026b [US2] [D:T022, D:T026] Implement report framing logic in `code/generate_report.py`: If VIF > 5 is detected (from T022), explicitly suppress independent effect claims for correlated variables in the generated report. Output: `state/vif_compliance_check.yaml` (record of VIF status and suppression action).
- [X] T026c [US2] [D:T022, D:T026] Implement logic in `code/generate_report.py` to explicitly **suppress** any claims of independent effects for predictors with VIF > 5 in the final report text.
- [X] T027 [US2] [D:T021] Implement `code/analysis.py` function `detect_tolerance_proxies()` to check for and ingest 'independent tolerance proxies' (e.g., survival rate) if available, as required by FR-009. Generate explicit framing text in `data/derived/report_framing.md` (predicting 'physiological state'). **Deliverable**: `state/proxy_detection.yaml` (boolean `has_proxy`).
- [X] T030 [US2] [D:T022, D:T026] Verify that if VIF > 5 is detected, the system refrains from claiming independent effects for definitionally related variables (assertion in T022/T026c). Output: `state/vif_compliance_check.yaml` (updated with final verification status).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test in `tests/unit/test_model_fitting.py`: Implement `test_spearman_correlation_matches_known_value` (asserts correlation within 5% of synthetic target).
- [X] T019 [P] [US2] Integration test in `tests/integration/test_model_pipeline.py`: Implement `test_pgl_fits_with_phylogenetic_structure` (asserts PGLS converges and phylogenetic signal lambda > 0).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Predictive Robustness via Sensitivity Analysis (Priority: P3)

**Goal**: Confirm that the predictive thresholds used in the classification model are not arbitrary. **Note**: As per spec, the classification model (FR-007/008) is REQUIRED to enable the sensitivity analysis. This phase implements the classification model and the threshold sweep.

**Independent Test**: The sensitivity module can be tested by running the model with a primary threshold and then verifying that the output includes a plot or table showing how the false-positive/false-negative rates change.

### Implementation for User Story 3

- [X] T027b [US3] [D:T015, D:T022, D:T027] Implement `code/models.py` function `fit_rf_classification()` to predict the binary drought tolerance class (high/low). **Logic**:
 1. Check `state/proxy_detection.yaml` for `has_proxy` flag (from T027).
 2. **If `has_proxy` is True**: Binarize the *proxy* variable using median split (threshold = median(proxy_value)). Train Random Forest Classification model. **Specs**: F1-score metric, **5-fold GroupKFold (groups=species_name) **, n_estimators=100. Output: `data/derived/classification_model.pkl`.
 3. **If `has_proxy` is False**: **SKIP** model training. Output: `state/classification_status.yaml` with status 'N/A' and justification "No independent tolerance proxy found; classification skipped per Plan 'No Circular Classification' rule." **Note**: This ensures FR-007 and FR-008 compliance by NOT binarizing the target variable.
 4. **Tie-breaking**: Use `np.searchsorted` to handle ties in the median split deterministically.
- [X] T028 [US3] [D:T027, D:T027b] Implement `code/analysis.py` function `run_sensitivity_analysis()`. **Logic**:
 1. **If `has_proxy` is False**: Output `results/sensitivity_sweep_results.csv` with status 'N/A' and justification "Classification skipped; sensitivity analysis not applicable."
 2. **If `has_proxy` is True**: Sweep predicted probability threshold across the full range (from the minimum to the maximum, using a fine-grained step). Calculate and report variation in accuracy, precision, recall, F1, **False Positive Rate, and False Negative Rate** for each step. Ensure at least ±0.05 sweep around the baseline (optimal F1 or 0.5) is explicitly reported.
 3. **Output**: `data/derived/sensitivity_sweep_results.csv` and `results/figures/sensitivity_curve.png` (if applicable).
- [X] T029 [US3] [D:T028] Generate sensitivity report in `data/derived/sensitivity_report.md` including threshold justification and impact analysis. Ensure the report explicitly states the threshold used and the robustness of the results, or the N/A justification if no proxy was found.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T037 [US3] [D:T028] Unit test in `tests/unit/test_sensitivity.py`: Implement `test_sensitivity_sweep_generates_valid_range` (asserts output covers full alpha range or threshold range).
- [X] T038 [US3] [D:T028] Integration test in `tests/integration/test_sensitivity.py`: Implement `test_sensitivity_report_contains_expected_metrics` (asserts report contains threshold variation data or N/A justification).

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032a [P] Update `README.md` with Installation, Usage, and Results sections. **Logic**: Add detailed installation instructions, usage examples, and results interpretation to satisfy Constitution Principles I and IV.
- [X] T032b [P] Update `docs/` with API documentation and quickstart guide. **Logic**: Generate API docs from docstrings and create `quickstart.md` to satisfy Constitution Principles I and IV.
- [X] T033 [P] Code cleanup and refactoring.
- [X] T034a [P] [D:T012,T013] Profile memory usage of image loading pipeline. **Deliverable**: `docs/memory_profile.md` with peak usage <7GB.
- [X] T034b [P] [D:T012,T013] Profile total pipeline runtime. **Deliverable**: `state/runtime_profile.yaml` with total runtime. **Logic**: Verify total runtime <= 6h.
- [X] T034c [P] Optimize image loading to use generators if profiling shows memory issues.
- [X] T035 [P] Additional unit tests for data hygiene and checksums in `tests/unit/`.
- [X] T036 [P] Run `quickstart.md` validation.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

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
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for image loading and error handling in tests/unit/test_image_processing.py"
Task: "Integration test for full image-to-CSV pipeline on sample data in tests/integration/test_image_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download_images.py to fetch NPPN root images"
Task: "Implement code/preprocess_images.py to extract RSA traits"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

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
- `code/models.py` (T022, T023a, T023c, T024b, T027b) - Contains functions `perform_pca`, `fit_ols`, `fit_ridge`, `fit_lasso`, `fit_random_forest`, `fit_pgl`, `fit_rf_classification`
- `code/analysis.py` (T022, T025, T027, T028) - Contains functions `perform_pca`, `multiple_comparison_correction`, `run_sensitivity_analysis`, `detect_tolerance_proxies`
- `code/fetch_phylogeny.py` (T024a) - Contains functions `fetch_tree`, `construct_pvr_covariance`