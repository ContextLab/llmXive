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

- [ ] T002 [P] Initialize Python 3.11 project with dependencies in `requirements.txt` (pandas>=2.0.0, numpy>=1.24.0, scikit-learn>=1.3.0, scipy>=1.11.0, statsmodels>=0.14.0, opencv-python-headless>=4.8.0, scikit-image>=0.21.0, requests>=2.31.0, huggingface_hub>=0.16.0, pytest>=7.0.0, networkx>=3.0). **Note**: `pandas-phy` and `ete3` excluded to align with Plan's Primary Dependencies list.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools.
- [X] T004 [P] Implement `code/config.py` with paths, random seeds (42), and hyperparameters.
- [X] T005 [P] Setup logging infrastructure in `code/__init__.py`.
- [X] T006 [P] Create base data models/entities in `code/models.py` referencing `data-model.md` schema: `RootImage` {id: str, path: str, species: str}, `RSAMetrics` {depth: float, branching_density: float, surface_area: float}, `PhysioTrait` {species: str, conductance: float, photosynthesis: float, survival_rate: float?}. Include validation rules.
- [ ] T007 [P] Create base data validation schema checks in `contracts/` (dataset.schema.yaml, output.schema.yaml).
- [ ] T008 [P] Implement `code/power_analysis.py`: Calculate required sample size (N) using `statsmodels.stats.power.FTestPower` with explicit parameters: {{claim:c_bcec7d3b}}. **Logic**: Fetch species list from NPPN/MGB3 and TRY. If overlap N < 55, **HALT** with critical error "Insufficient species for power analysis (N < 55)". **Deliverable**: `state/power_analysis_report.yaml`. <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract and Aggregate Root System Architecture Metrics (Priority: P1) 🎯 MVP

**Goal**: Convert raw root images from the NPPN Plant Phenome Pipeline into quantitative architectural metrics (depth, branching density, surface area) to enable downstream statistical analysis.

**Independent Test**: The pipeline can be tested by running the image analysis module on a small, fixed set of known root images and verifying that the output CSV contains non-null, positive numerical values for all defined RSA traits.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download_images.py`: Fetch root images from `nppn/root-phenotyping` (HuggingFace ID: `nppn/root-phenotyping`) via `huggingface_hub`. **Logic**: Attempt download. If download fails (exception `RepositoryNotFoundError` or `LocalEntryNotFoundError` or empty directory), **HALT** with critical error "No real NPPN root images found. Pipeline cannot proceed." Do NOT fallback to other datasets. Ensure CPU-optimized, no GPU. Output: `data/raw/nppn_images/`.
- [ ] T013 [US1] Implement `code/preprocess_images.py`: Extract RSA traits using OpenCV/scikit-image on CPU. **Algorithm**: `skeletonize` (8-connectivity) for depth/branching; `find_contours` for surface area. Branching density = (branch_points - endpoints) / total_length. [UNRESOLVED-CLAIM: c_69fe03ff — status=not_enough_info] **Includes**: Error logging for corrupted images (skipping them gracefully) and validation logic to ensure no null values and positive numerical values for all traits in output.
- [ ] T015 [US1] [D:T013] Generate `data/derived/rsametrics.csv` with columns: species_id, depth, branching_density, surface_area. **Includes**: Validation to ensure no null values and positive numerical values for all traits (logic merged into T013).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests depend on implementation. Write them first, but they run after code exists.

- [ ] T016 [P] [US1] [D:T012,T013] Unit test in `tests/unit/test_image_processing.py`: Implement `test_load_image_handles_corrupted_file_returns_error` (asserts specific error message) and `test_skeletonize_returns_valid_branch_points` (asserts branch_points > 0).
- [ ] T017 [P] [US1] [D:T012,T013] Integration test in `tests/integration/test_image_pipeline.py`: Implement `test_full_pipeline_generates_non_null_csv` (asserts output CSV has a consistent number of rows with no nulls and positive values) on sample data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlate RSA Metrics with Drought Physiology (Priority: P2)

**Goal**: Statistically validate whether deeper or more branched root systems associate with higher stomatal conductance and photosynthetic rates under water stress using the aggregated data.

**⚠️ DEPENDENCY**: This phase depends on the completion of Phase 3 (T015) to ensure `rsametrics.csv` exists before merging.

**Independent Test**: The analysis can be tested by running the regression module on a synthetic dataset with a known positive correlation between a "depth" variable and a "conductance" variable, verifying that the calculated correlation coefficient matches the expected value within an acceptable margin of error.

### Implementation for User Story 2

- [ ] T020 [US2] [D:T001a, D:T015] Implement `code/download_traits.py` to fetch physiological trait data from TRY database. **Logic**: Use the `trydata` Python package to query traits (stomatal_conductance, photosynthesis) for the species list derived from `rsametrics.csv`. Handle authentication via environment variable `TRY_API_KEY`. If no overlap, handle via T021 logic.
- [X] T021 [US2] [D:T015, D:T020] Implement `code/merge_data.py` to merge `rsametrics.csv` with physiological data. **Logic**: Handle missing species via listwise deletion. **Constraint**: If sample size < 55, **HALT** with critical error "Insufficient species after merge (N < 55)". Do NOT implement mean imputation for species count. **Note**: This deviates from Spec Assumptions (which allow mean imputation) per the Plan's decision to enforce stricter data hygiene; this deviation is intentional.
- [X] T022 [US2] Implement `code/analysis.py` function `perform_pca()` to transform RSA traits for collinearity handling (VIF > 5 check included).
- [X] T023a [US2] [D:T022] Implement `code/models.py` functions `fit_ols()`, `fit_ridge()`, `fit_lasso()` to predict stomatal conductance/photosynthesis. **Specs**: R² metric, **5-fold GroupKFold (groups=species_name) ** to prevent phylogenetic leakage, alpha search [a range of values].
- [X] T023c [US2] [D:T022] Implement `code/models.py` function `fit_random_forest()` to predict stomatal conductance/photosynthesis using Random Forest Regression. **Specs**: R² metric, **5-fold GroupKFold (groups=species_name) ** to prevent phylogenetic leakage, n_estimators=100, max_depth=None, regularization via min_samples_leaf.
- [ ] T024a [US2] [D:T022] Implement `code/fetch_phylogeny.py`: Fetch phylogenetic tree from Open Tree of Life API. **Logic**: If fetch fails, **HALT immediately** with critical error "Phylogenetic tree fetch failed. PVR fallback is impossible without a tree. FR-010 violation." **Output**: `data/derived/phylogenetic_tree.newick`. **Note**: No 'equivalent' fallback is implemented per the Plan's decision to strictly enforce the tree requirement.
- [~] T024b [US2] [D:T024a] Implement `code/models.py` function `fit_pgl()` to perform Phylogenetic Generalized Least Squares (PGLS). **Logic**: Use `statsmodels` to fit model: `conductance ~ depth + surface_area + (phylogenetic_structure)`. Input: `data/derived/phylogenetic_tree.newick`.
- [X] T025 [US2] Implement multiple-comparison correction (Bonferroni/FDR) in `code/analysis.py` for hypothesis testing.
- [ ] T026 [US2] Generate `data/derived/model_results.csv` with coefficients, p-values, R², and adjusted p-values.
- [~] T026b [US2] [D:T022, D:T026] Implement report framing logic in `code/generate_report.py`: If VIF > 5 is detected (from T022), explicitly suppress independent effect claims for correlated variables in the generated report. Output: `state/vif_compliance_check.yaml` (record of VIF status and suppression action).
- [X] T026c [US2] [D:T026, D:T022] Implement logic in `code/generate_report.py` to explicitly **suppress** any claims of independent effects for predictors with VIF > 5 in the final report text.
- [X] T027 [US2] Implement `code/analysis.py` function `detect_tolerance_proxies()` to check for and ingest 'independent tolerance proxies' (e.g., survival rate) if available, as required by FR-009. Generate explicit framing text in `data/derived/report_framing.md` (predicting 'physiological state'). **Deliverable**: `state/proxy_detection.yaml` (boolean `has_proxy`).
- [ ] T030 [US2] [D:T022, D:T026] Verify that if VIF > 5 is detected, the system refrains from claiming independent effects for definitionally related variables (assertion in T022/T026c). Output: `state/vif_compliance_check.yaml` (updated with final verification status).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test in `tests/unit/test_model_fitting.py`: Implement `test_spearman_correlation_matches_known_value` (asserts correlation within 5% of synthetic target).
- [ ] T019 [P] [US2] Integration test in `tests/integration/test_model_pipeline.py`: Implement `test_pgl_fits_with_phylogenetic_structure` (asserts PGLS converges and phylogenetic signal lambda > 0).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Predictive Robustness via Sensitivity Analysis (Priority: P3)

**Goal**: Confirm that the predictive thresholds used in the classification model are not arbitrary. **Note**: As per spec, the classification model (FR-007/008) is REQUIRED to enable the sensitivity analysis. This phase implements the classification model and the threshold sweep.

**Independent Test**: The sensitivity module can be tested by running the model with a primary threshold and then {{claim:c_73727cab}}, verifying that the output includes a plot or table showing how the false-positive/false-negative rates change.

### Implementation for User Story 3

- [ ] T027b [US3] [D:T015, D:T022, D:T027] Implement `code/models.py` function `fit_rf_classification()` to predict the binary drought tolerance class (high/low). **Logic**:
 1. Check `state/proxy_detection.yaml` for `has_proxy` flag (from T027).
 2. **If `has_proxy` is True**: Binarize the *proxy* variable using median split. Train Random Forest Classification model. **Specs**: F1-score metric, **5-fold GroupKFold (groups=species_name) **, n_estimators=100. Output: `data/derived/classification_model.pkl`.
 3. **If `has_proxy` is False**: **SKIP** model training entirely. Do NOT binarize primary physiological metrics. This avoids circular classification. **Deliverable**: Flag `classification_skipped=True` in `state/proxy_detection.yaml` and generate `data/derived/classification_status.md` stating "Classification skipped: No independent tolerance proxy found. Sensitivity analysis will report N/A."
- [ ] T028 [US3] [D:T023a, D:T023c, D:T027, D:T027b] Implement `code/analysis.py` function `run_sensitivity_analysis()`. **Logic**:
 1. **If `has_proxy` is True**: {{claim:c_2ad237e4}} Calculate and report variation in accuracy, precision, recall, F1, **False Positive Rate, and False Negative Rate**.
 2. **If `has_proxy` is False**: **SKIP** threshold sweep. Generate `results/sensitivity_sweep_results.csv` with a single row indicating "N/A" and a justification: "Classification model not built due to lack of independent tolerance proxy (Plan: No Circular Classification). Sensitivity analysis not applicable."
 3. **Output**: `data/derived/sensitivity_sweep_results.csv` and `results/figures/sensitivity_curve.png` (if applicable).
- [ ] T029 [US3] [D:T028] Generate sensitivity report in `data/derived/sensitivity_report.md` including threshold justification and impact analysis. Ensure the report explicitly states the threshold used and the robustness of the results, or the N/A justification if no proxy was found.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T037 [US3] [D:T028] Unit test in `tests/unit/test_sensitivity.py`: Implement `test_sensitivity_sweep_generates_valid_range` (asserts output covers full alpha range or threshold range).
- [ ] T038 [US3] [D:T028] Integration test in `tests/integration/test_sensitivity.py`: Implement `test_sensitivity_report_contains_expected_metrics` (asserts report contains threshold variation data or N/A justification).

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `README.md` and `docs/`.
- [ ] T033 Code cleanup and refactoring.
- [ ] T034 [P] [D:T012,T013] Profile and optimize image loading to use generators; ensure memory usage <7GB RAM and full pipeline runs within 6 hours on 2 CPU/7GB RAM. **Logic**: Measure total pipeline runtime and log against 6h limit. **Deliverable**: Generate `docs/memory_profile.md` with peak usage <7GB and `state/runtime_profile.yaml` with total runtime. **Input Load**: Run on a representative set of images for profiling.
- [ ] T035 [P] Additional unit tests for data hygiene and checksums in `tests/unit/`.
- [ ] T036 Run `quickstart.md` validation.

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
- **Spec Gaps Addressed**: Tasks use NPPN (no fallback), PGLS (strict tree requirement), and Classification (mandatory median-split on primary metrics if no proxy). Documentation tasks confirm these implementations.

### Project Structure Note

To resolve file collision concerns, the following file split is mandated:
- `code/download_images.py` (T012)
- `code/download_traits.py` (T020)
- `code/preprocess_images.py` (T013)
- `code/merge_data.py` (T021)
- `code/models.py` (T022, T023a, T023c, T024b, T027b) - Contains functions `perform_pca`, `fit_ols`, `fit_ridge`, `fit_lasso`, `fit_random_forest`, `fit_pgl`, `fit_rf_classification`
- `code/analysis.py` (T022, T025, T027, T028) - Contains functions `perform_pca`, `multiple_comparison_correction`, `run_sensitivity_analysis`, `detect_tolerance_proxies`
- `code/fetch_phylogeny.py` (T024a) - Contains functions `fetch_tree`, `construct_pvr_covariance`