# Tasks: Predicting the Impact of Alloying on Creep Resistance via Public Data

**Input**: Design documents from `/specs/001-predicting-impact-of-alloying-on-creep-resistance/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project structure: Initialize repository with `src/`, `tests/`, `data/`, `docs/`, `config/` directories, `pyproject.toml`, and `.gitignore`.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, scikit-learn, pymatgen, shap, numpy, pyyaml, requests, tqdm, scipy, pytest)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `config/settings.yaml` with random seeds, paths, and API key placeholders
- [X] T005 [P] Create `config/synthetic_params.yaml` with Arrhenius/Power-law parameters and statistical targets
- [X] T006b [P] Create `contracts/dataset.schema.yaml` validating the processed CSV schema. **Content**: Define JSON Schema with required fields: `alloy_id` (string), `composition_str` (string), `temperature` (float), `stress` (float), `rupture_time` (float), `mixing_enthalpy` (float), `radius_mismatch` (float), `solid_solution_strengthening` (float). Include validation rules for non-null values and data types as per FR-001 and US-01.
- [X] T007 [P] Create `contracts/output.schema.yaml` for model reports. **Content**: Define JSON Schema for `R2_score` (float), `RMSE` (float), `CI_bounds` (object with lower/upper floats), `p_value` (float), `shap_top_5` (list of objects with feature name and value).
- [X] T008 [P] Implement `src/utils/logger.py` for structured logging
- [X] T009 [P] Implement `src/utils/hash.py` for artifact hashing and state updates (Constitution Principle V)
- [X] T010 [P] Implement `src/utils/validators.py` for schema validation and physics consistency checks

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download NIMS data (if available) or generate synthetic data, merge with thermodynamic descriptors, and output a clean, validated CSV.

**Independent Test**: Execute the pipeline script and verify:
1. Pre-flight checks confirm NIMS URL (if used) returns HTTP 200 and MP API key is valid.
2. If external sources fail, synthetic data is generated matching the schema.
3. Output CSV validates against `contracts/dataset.schema.yaml`.
4. Row counts and exclusion logs match specifications.

### Tests for User Story 1

- [X] T011 [P] [US1] Contract test for schema validation in `tests/contract/test_schema.py`
- [X] T012 [P] [US1] Unit test for composition string parsing and normalization in `tests/unit/test_parsing.py`
- [X] T013 [P] [US1] Unit test for thermodynamic calculation in `tests/unit/test_thermo.py`
- [X] T014 [P] [US1] Integration test for synthetic data generation and physics consistency check in `tests/contract/test_physics.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement `src/data/download.py`:
 - **Real Data Path**: Download NIMS Creep Data Center dataset with exponential backoff (limited retries).
 - **Pre-flight Check**: Verify NIMS URL returns HTTP 200 before attempting download.
 - Parse CSV, remove entries with missing `temperature`, `stress`, or `rupture_time`.
 - **Duplicate Handling**: Group by (alloy_id, temperature, stress) and average `rupture_time`; log count of averaged duplicates.
 - **Missing Value Filtering**: Log excluded entries and counts.
 - If NIMS is unreachable, raise a `RuntimeError` ONLY if `STRICT_MODE` is enabled; otherwise, signal the pipeline to use synthetic data.
- [X] T016 [US1] Implement `src/data/generate.py`: Synthetic data generation using Arrhenius/Power-law laws, signal injection, and statistical target validation (KS distance, mean/SD). **Mandatory**: If statistical targets (KS distance > 0.05 or mean/SD mismatch > 10%) are not met, the system MUST raise an error and halt execution immediately, preventing the pipeline from proceeding to modeling.
- [X] T017 [US1] Implement `src/data/preprocess.py`: Composition parsing (alphabetical sort, rounding, weight% to atomic%), and exclusion logic for missing thermodynamic data.
 - **Mandatory**: Calculate `solid_solution_strengthening` estimates based on elemental fractions (FR-003).
 - **Mandatory**: Embed logging for excluded entries (missing temperature/stress/rupture time AND missing thermodynamic data) directly within this script to ensure counts are generated during the pipeline run and available for the report.
- [X] T018 [US1] Implement `src/data/merge.py`: Join composition data with Materials Project thermodynamic properties (mixing enthalpy, radius mismatch, solid-solution strengthening) using `pymatgen`.
 - **Mandatory**: Implement exponential backoff for Materials Project API rate limits with a limited number of retries.
 - **Mandatory**: Log "unresolved thermodynamic data" for entries with 404, null, or timeout > 30s; exclude these from the final dataset for BOTH models.
- [X] T019 [US1] Implement `src/data/pipeline.py`: Orchestration script that selects real vs. synthetic path, runs preprocessing, validates schema, and logs exclusion counts.
 - **Mandatory**: Validate output CSV against `contracts/dataset.schema.yaml` (T006b).
 - **Mandatory**: Log the count of entries excluded due to missing thermodynamic data for both models.
 - **Mandatory**: Ensure the pipeline can run in `STRICT_MODE` (fail on real data source error) or default mode (fallback to synthetic).
 - **Mandatory**: Implement `STRICT_MODE` logic: If `STRICT_MODE` is true and real data source fails, raise `RuntimeError`.
- [X] T041 [US1] Add a `verify_data_integrity.py` script to `src/utils/` that performs a final sanity check on the processed dataset: verify that all `alloy_id` entries have unique normalized composition keys, confirm that no duplicate (alloy, temp, stress) rows exist in the final CSV, and validate that the sum of retained + excluded rows equals the raw input count (where applicable).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Model Training and Evaluation (Priority: P2)

**Goal**: Train Gradient Boosting models on thermodynamic vs. composition-only features using Nested CV and perform statistical significance testing.

**Independent Test**: Run training script and verify:
1. Two distinct GBR models trained on the **exact same subset** of data.
2. Nested CV uses stratification by temperature range (if N≥50) or Repeated 5-fold (if N<50).
3. **Statistical Test**: Permutation Test (primary) with Corrected Resampled t-test (reference/logging only) for 20 ≤ N < 100. Bootstrap 95% CI for N < 20. Sensitivity analysis on cutoffs is logged.
4. **Spec Compliance**: Permutation Test is implemented as the primary robust test, with t-test calculated for reference pending spec amendment.

### Tests for User Story 2

- [X] T021 [P] [US2] Unit test for Nested CV split generation (stratification logic) in `tests/unit/test_cv_splits.py`
- [X] T022 [P] [US2] Integration test for model training and intersection verification in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement `src/models/train.py`:
 - Load processed data.
 - Ensure both models train on the exact same intersection of valid rows.
 - Implement Nested CV: Outer loop (k-fold stratified by temp range OR Repeated m-fold), Inner loop (GridSearch).
 - Train Thermodynamic GBR (features: atomic fractions + mixing enthalpy + radius mismatch + solid_solution_strengthening).
 - Train Composition-Only GBR (features: atomic fractions only).
 - Assert that input DataFrames for both models have identical indices; raise error if they differ.
- [X] T024 [US2] Implement `src/models/evaluate.py`:
 - Calculate R² and RMSE for both models.
 - **Primary Test**: Implement **Permutation Test** (10,000 permutations) on the difference in CV scores as the robust primary test for 20 ≤ N < 100.
 - **Reference Test**: Implement **Corrected Resampled t-test (Nadeau & Bengio)** *only* for logging/reference purposes to satisfy the current spec FR-005, noting in the log that the Permutation Test is the primary result.
 - **Mandatory**: Implement **Bootstrap 95% Confidence Interval** for N < 20.
 - **Mandatory**: Perform sensitivity analysis sweeping cutoffs {0.01, 0.05, 0.1} specifically on the **Permutation Test p-value**.
 - Output results to logs: Permutation Test p-value (primary), t-test p-value (reference), Bootstrap CI bounds, and sensitivity analysis results.
 - **Note**: T024 consolidates the statistical testing logic. The Permutation Test is the primary result; the t-test is secondary.
- [X] T025 [US2] Implement `src/models/main_eval.py`: Orchestration script to run training, evaluation, and print the final comparison table (R² delta, CI, significance).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance Analysis and Reporting (Priority: P3)

**Goal**: Generate SHAP plots and reports to interpret model decisions and rank feature importance.

**Independent Test**: Run SHAP script and verify:
1. SHAP summary plot generated and saved as PNG.
2. Top features extracted and reported with direction of influence.

### Tests for User Story 3

- [X] T026 [P] [US3] Unit test for SHAP value extraction and formatting in `tests/unit/test_shap_utils.py`

### Implementation for User Story 3

- [X] T027 [US3] Implement `src/models/interpret.py`:
 - Load the trained Thermodynamic GBR model.
 - Compute SHAP values using `TreeExplainer`.
 - Generate and save SHAP summary plot (PNG) in `data/outputs/`.
 - Extract top features and calculate mean absolute SHAP values.
 - Determine direction of influence (positive/negative correlation) for top features.
- [X] T028 [US3] Implement `src/reports/generate_report.py`:
 - Compile final results: R² delta, statistical test results (Permutation primary, t-test reference), SHAP top 5 list.
 - Format report with text summary: "feature_name: +value" or "feature_name: positive correlation".
 - Save final report to `docs/reports/`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Update `README.md` with quickstart instructions and execution commands for CI measurement.
- [X] T030 [P] Add `.gitignore` and CI configuration (GitHub Actions) for CPU-only runner, including the workflow to run the full pipeline and log duration.
- [X] T031 [P] Create `tests/integration/test_runtime.py` script to run the full pipeline, capture execution time, and **log the specific duration value** to stdout and a log file as a measured outcome for SC-005. Also assert pipeline duration < 6h and log failure if exceeded.
- [X] T033 Verify all artifacts (CSVs, plots, reports) are hashed and state updated per `src/utils/hash.py`

---

## Phase 7: Review & Compliance (Revision Pass)

**Goal**: Address specific reviewer concerns regarding data integrity, API robustness, and specification alignment.

- [X] T038 [US2] Update `src/models/evaluate.py` (T024) to explicitly log the **sample size N** used for the statistical test selection (Bootstrap vs. Permutation) and the **stratification strategy** applied (Temp Range vs. Repeated 5-fold).

**Note**: T020, T032, T034, T035, T039, T040, and T042 have been removed as their functionality is covered by T015, T031, T019, T018, T023, T024, and T024 respectively.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review (Phase 7)**: Depends on completion of US1 and US2 implementation tasks

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on T019 (Pipeline) to provide the processed CSV.
- **User Story 3 (P3)**: Depends on T023 (Training) to provide the trained model.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for schema validation in tests/contract/test_schema.py"
Task: "Unit test for composition string parsing in tests/unit/test_parsing.py"

# Launch data modules in parallel:
Task: "Implement src/data/download.py"
Task: "Implement src/data/generate.py"
Task: "Implement src/data/preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Pipeline + Synthetic Data)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify schema, physics check, exclusion logs).
5. Deploy/demo if ready.

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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Interpretability)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All models MUST run on CPU-only CI (cores, limited RAM). No GPU/CUDA.
- **Critical Constraint**: Synthetic data MUST pass Physics Consistency Check (R² > 0.8) before proceeding to real data modeling.
- **Critical Constraint**: Both models MUST train on the exact same intersection of data to ensure fair comparison.
- **Critical Constraint**: Statistical tests MUST follow the research plan (Permutation Test primary) while logging the t-test for reference.
- **Note on Statistical Methodology**: The Permutation Test is the primary robust test. The Corrected Resampled t-test is implemented for reference/logging only to align with the current spec FR-005, pending a formal spec amendment.
- **Data Integrity**: The data loader must FAIL LOUDLY if `STRICT_MODE` is enabled and real sources are unreachable; synthetic fallback is the default behavior to ensure executability per FR-001/FR-008.