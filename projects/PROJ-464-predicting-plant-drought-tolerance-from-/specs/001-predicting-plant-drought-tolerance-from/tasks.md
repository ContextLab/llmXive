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

- [ ] T001 Create project structure per implementation plan: explicitly create directories `data/raw/`, `data/derived/`, `code/`, `tests/`, `docs/`, `state/`, `contracts/` and initialize `README.md`, `requirements.txt`.
- [ ] T047 [P] Update `spec.md` SC-005 to reflect the actual deliverable scope (representative dataset of images, e.g., [deferred]) or formally mark as 'Not Applicable' with justification to align spec with implementation constraints BEFORE execution begins.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Initialize Python 3.11 project with dependencies in `requirements.txt` (pandas>=2.0.0, numpy>=1.24.0, scikit-learn>=1.3.0, scipy>=1.11.0, statsmodels>=0.14.0, opencv-python-headless>=4.8.0, scikit-image>=0.21.0, requests>=2.31.0, huggingface_hub>=0.16.0, pytest>=7.0.0).
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools.
- [ ] T005 [P] Implement `code/config.py` with paths, random seeds (42), and hyperparameters.
- [ ] T006 [P] Setup logging infrastructure in `code/__init__.py`.
- [ ] T007 [P] Create base data models/entities in `code/models.py` referencing `data-model.md` schema: `RootImage` {id: str, path: str, species: str}, `RSAMetrics` {depth: float, branching_density: float, surface_area: float}, `PhysioTrait` {species: str, conductance: float, photosynthesis: float, survival_rate: float?}. Include validation rules.
- [ ] T008 [P] Create base data validation schema checks in `contracts/` (dataset.schema.yaml, output.schema.yaml).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract and Aggregate Root System Architecture Metrics (Priority: P1) 🎯 MVP

**Goal**: Convert raw root images from the NPPN Plant Phenome Pipeline (or verified fallback) into quantitative architectural metrics (depth, branching density, surface area) to enable downstream statistical analysis.

**Independent Test**: The pipeline can be tested by running the image analysis module on a small, fixed set of known root images and verifying that the output CSV contains non-null, positive numerical values for all defined RSA traits.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/download_images.py`: Fetch root images from `nppn/root-phenotyping` (HuggingFace ID: `nppn/root-phenotyping`) via `huggingface_hub`. **Logic**: Attempt NPPN first. If download fails (exception or empty), fallback to `mgb3/root-images` (HuggingFace ID: `mgb3/root-images`) and log the fallback. Ensure CPU-optimized, no GPU.
- [ ] T012b [US1] [D:T012] Log specific "NPPN Unavailable" exception to `state/exceptions.yaml` if T012's NPPN attempt *actually* failed (check return code/exception flag in T012), formally documenting the deviation from FR-001.
- [ ] T013 [US1] Implement `code/preprocess_images.py`: Extract RSA traits using OpenCV/scikit-image on CPU. **Algorithm**: `skeletonize` (8-connectivity) for depth/branching; `find_contours` for surface area. Branching density = (branch_points - endpoints) / total_length. **Includes**: Error logging for corrupted images (skipping them gracefully) and validation logic to ensure no null values and positive numerical values for all traits in output.
- [ ] T015 [US1] Generate `data/derived/rsametrics.csv` with columns: species_id, depth, branching_density, surface_area. **Includes**: Validation to ensure no null values and positive numerical values for all traits (logic merged into T013).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests depend on implementation. Write them first, but they run after code exists.

- [ ] T016 [P] [US1] [D:T012,T013] Unit test in `tests/unit/test_image_processing.py`: Implement `test_load_image_handles_corrupted_file_returns_error` (asserts specific error message) and `test_skeletonize_returns_valid_branch_points` (asserts branch_points > 0).
- [ ] T017 [P] [US1] [D:T012,T013] Integration test in `tests/integration/test_image_pipeline.py`: Implement `test_full_pipeline_generates_non_null_csv` (asserts output CSV has 10 rows, no nulls, positive values) on sample data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlate RSA Metrics with Drought Physiology (Priority: P2)

**Goal**: Statistically validate whether deeper or more branched root systems associate with higher stomatal conductance and photosynthetic rates under water stress using the aggregated data.

**⚠️ DEPENDENCY**: This phase depends on the completion of Phase 3 (T015) to ensure `rsametrics.csv` exists before merging.

**Independent Test**: The analysis can be tested by running the regression module on a synthetic dataset with a known positive correlation between a "depth" variable and a "conductance" variable, verifying that the calculated correlation coefficient matches the expected value within a 5% margin of error.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/download_traits.py` to fetch physiological trait data from TRY database (or verified subset).
- [ ] T021 [US2] [D:T015, D:T020] Implement `code/merge_data.py` to merge `rsametrics.csv` with physiological data, handling missing species via listwise deletion.
- [ ] T022 [US2] Implement `code/analysis.py` function `perform_pca()` to transform RSA traits for collinearity handling (VIF > 5 check included).
- [ ] T023 [US2] Implement `code/models.py` functions `fit_ols()`, `fit_ridge()`, `fit_lasso()` to predict stomatal conductance/photosynthesis. **Specs**: R² metric, 5-fold stratified CV by species, alpha search [0.01, 0.1, 1.0, 10.0]. (Merged OLS, Ridge, Lasso).
- [ ] T024 [US2] Implement `code/models.py` function `fit_lmm()` using `statsmodels` with formula 'conductance ~ depth + (1|species)' and solver 'bfgs' (substitute for PGLS).
- [ ] T024b [US2] [D:T024] Implement statistical equivalence test (simulation-based) in `code/analysis.py` to verify LMM is a valid substitute for PGLS for the specific species non-independence constraints (FR-010).
- [ ] T025 [US2] Implement multiple-comparison correction (Bonferroni/FDR) in `code/analysis.py` for hypothesis testing.
- [ ] T026 [US2] Generate `data/derived/model_results.csv` with coefficients, p-values, R², and adjusted p-values.
- [ ] T027 [US2] Implement `code/analysis.py` function `detect_tolerance_proxies()` to check for and ingest 'independent tolerance proxies' (e.g., survival rate) if available, as required by FR-009. Generate explicit framing text in `data/derived/report_framing.md` (predicting 'physiological state').

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test in `tests/unit/test_model_fitting.py`: Implement `test_spearman_correlation_matches_known_value` (asserts correlation within 5% of synthetic target).
- [ ] T019 [P] [US2] Integration test in `tests/integration/test_model_pipeline.py`: Implement `test_lmm_fits_with_species_random_effects` (asserts LMM converges and random effect variance > 0).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Predictive Robustness via Sensitivity Analysis (Priority: P3)

**Goal**: Confirm that the predictive thresholds used in the classification model are not arbitrary. **Note**: As per plan, the classification model (FR-007/008) is excluded. This phase implements sensitivity analysis for the regression model stability and documents the N/A condition for classification thresholds.

**Independent Test**: The sensitivity module can be tested by running the model with a primary threshold and then sweeping that threshold across a defined range (e.g., ±0.05), verifying that the output includes a plot or table showing how the false-positive/false-negative rates change.

### Implementation for User Story 3

- [ ] T028 [US3] [D:T023] Implement `code/analysis.py` function `run_regression_sensitivity()` to sweep regularization **alpha** linearly across a broad range [0.001, 100.0] with a fine step size and report variation in R²/error rates; if classification is not used, output "N/A" with justification.
- [ ] T029 [US3] [D:T028] Add logic to detect if classification is used; if only regression is performed (per plan), explicitly write "Sensitivity: N/A (Regression only)" to `data/derived/sensitivity_report.md`.
- [ ] T030 [US3] [D:T029] Generate sensitivity report in `data/derived/sensitivity_report.md` including threshold justification and impact analysis.
- [ ] T031 [US3] Verify that if VIF > 5 is detected, the system refrains from claiming independent effects for definitionally related variables.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T037 [US3] [D:T028] Unit test in `tests/unit/test_sensitivity.py`: Implement `test_sensitivity_sweep_generates_valid_range` (asserts output covers full alpha range).
- [ ] T038 [US3] [D:T028] Integration test in `tests/integration/test_sensitivity.py`: Implement `test_sensitivity_report_contains_expected_metrics` (asserts report contains N/A justification).

---

## Additional Documentation Tasks for Spec Gaps & Constraints

- [ ] T042 [US3] Document the exclusion of FR-007/FR-008 (binarization/classification) in `docs/spec_gaps.md` and justify the regression-only approach.
- [ ] T043 [US3] Document the substitution of PGLS (FR-010) with LMM in `docs/spec_gaps.md` due to lack of phylogenetic tree.
- [ ] T044 [US3] Update `docs/success_criteria.md` to reflect the image limit (MGB3, images) and document deviation from original SC-005 (now updated in T047).
- [ ] T045 [US3] Generate explicit framing text in `docs/report_framing.md` as required by FR-009 (predicting 'physiological state').
- [ ] T046b [US3] Formally process the rejection of FR-007/008 via a Change Request entry in `state/change_requests.yaml`, documenting the scientific rationale for excluding classification (circular validation).
- [ ] T047 [US3] (Moved to Phase 1) Update `spec.md` SC-005 to reflect the actual deliverable scope (a representative dataset of images) or formally mark as 'Not Applicable' with justification.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `README.md` and `docs/`.
- [ ] T033 Code cleanup and refactoring.
- [ ] T034 [P] [D:T012,T013] Profile and optimize image loading to use generators; ensure memory usage <7GB RAM and full pipeline runs within 6 hours on 2 CPU/7GB RAM. **Deliverable**: Generate `docs/memory_profile.md` with peak usage <7GB.
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
Task: "Implement code/download_images.py to fetch NPPN/MGB3 root images"
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
- **Spec Gaps Addressed**: Tasks use NPPN (with MGB3 fallback), LMM (with equivalence test), and Regression (with formal rejection of Classification) per plan.md constraints. Documentation tasks (T042-T047) explicitly record these deviations and formalize the change requests.

### Project Structure Note

To resolve file collision concerns, the following file split is mandated:
- `code/download_images.py` (T012)
- `code/download_traits.py` (T020)
- `code/preprocess_images.py` (T013)
- `code/merge_data.py` (T021)
- `code/models.py` (T022, T023, T024) - Contains functions `perform_pca`, `fit_ols`, `fit_ridge`, `fit_lasso`, `fit_lmm`
- `code/analysis.py` (T022, T024b, T025, T027, T028) - Contains functions `perform_pca`, `multiple_comparison_correction`, `run_regression_sensitivity`, `test_lmm_equivalence`, `detect_tolerance_proxies`