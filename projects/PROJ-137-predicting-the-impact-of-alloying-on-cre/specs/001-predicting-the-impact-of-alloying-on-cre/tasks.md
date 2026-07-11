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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `docs/`, `config/`) <!-- ATOMIZE: requested -->
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, scikit-learn, pymatgen, shap, numpy, pyyaml, requests, tqdm, scipy, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `config/settings.yaml` with random seeds, paths, and API key placeholders
- [ ] T005 [P] Create `config/synthetic_params.yaml` with Arrhenius/Power-law parameters and statistical targets
- [ ] T006a [P] Create `docs/data-model.md` defining `AlloySample`, `ThermodynamicDescriptor`, `ModelPerformance` entities with detailed schema descriptions, explicitly referencing `contracts/dataset.schema.yaml` for alignment
- [~] T006b Create `contracts/dataset.schema.yaml` validating the processed CSV schema (alloy_id, composition_str, temperature, stress, rupture_time, mixing_enthalpy, radius_mismatch)
- [~] T007 [P] Create `contracts/output.schema.yaml` for model reports
- [~] T008 [P] Implement `src/utils/logger.py` for structured logging
- [~] T009 [P] Implement `src/utils/hash.py` for artifact hashing and state updates (Constitution Principle V)
- [~] T010 [P] Implement `src/utils/validators.py` for schema validation and physics consistency checks

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

- [~] T011 [P] [US1] Contract test for schema validation in `tests/contract/test_schema.py`
- [~] T012 [P] [US1] Unit test for composition string parsing and normalization in `tests/unit/test_parsing.py`
- [~] T013 [P] [US1] Unit test for thermodynamic calculation in `tests/unit/test_thermo.py`
- [~] T014 [P] [US1] Integration test for synthetic data generation and physics consistency check in `tests/contract/test_physics.py`

### Implementation for User Story 1

- [~] T015 [US1] Implement `src/data/download.py`: NIMS fetch with exponential backoff, duplicate handling (averaging rupture times), and missing value filtering.
- [~] T016 [US1] Implement `src/data/generate.py`: Synthetic data generation using Arrhenius/Power-law laws, signal injection, and statistical target validation (KS distance, mean/SD). **Mandatory**: If statistical targets (KS distance > 0.05 or mean/SD mismatch > 10%) are not met, the system MUST raise an error and halt execution immediately, preventing the pipeline from proceeding to modeling.
- [~] T017 [US1] Implement `src/data/preprocess.py`: Composition parsing (alphabetical sort, rounding, weight% to atomic%), and exclusion logic for missing thermodynamic data. **Mandatory**: Embed logging for excluded entries (missing temperature/stress/rupture time AND missing thermodynamic data) directly within this script to ensure counts are generated during the pipeline run and available for the report.
- [~] T018 [US1] Implement `src/data/merge.py`: Join composition data with Materials Project thermodynamic properties (mixing enthalpy, radius mismatch) using `pymatgen`.
- [~] T019 [US1] Implement `src/data/pipeline.py`: Orchestration script that selects real vs. synthetic path, runs preprocessing, validates schema, and logs exclusion counts. **Mandatory**: Embed logging for excluded entries (missing temperature/stress/rupture time AND missing thermodynamic data) directly within this script to ensure counts are generated during the pipeline run and available for the report.
- [~] T020 REMOVED (Merged into T019)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Model Training and Evaluation (Priority: P2)

**Goal**: Train Gradient Boosting models on thermodynamic vs. composition-only features using Nested CV and perform statistical significance testing.

**Independent Test**: Run training script and verify:
1. Two distinct GBR models trained on the **exact same subset** of data.
2. Nested CV uses stratification by temperature range (if N≥50) or Repeated 5-fold (if N<50).
3. **Statistical Test**: Permutation Test (10,000 permutations) is performed for 20 ≤ N < 100; Bootstrap 95% CI for N < 20. Sensitivity analysis on cutoffs is logged.

### Tests for User Story 2

- [~] T021 [P] [US2] Unit test for Nested CV split generation (stratification logic) in `tests/unit/test_cv_splits.py`
- [~] T022 [P] [US2] Integration test for model training and intersection verification in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [~] T023 [US2] Implement `src/models/train.py`:
 - Load processed data.
 - Ensure both models train on the exact same intersection of valid rows.
 - Implement Nested CV: Outer loop (k-fold stratified by temp range OR Repeated m-fold), Inner loop (GridSearch).
 - Train Thermodynamic GBR (features: atomic fractions + mixing enthalpy + radius mismatch).
 - Train Composition-Only GBR (features: atomic fractions only).
- [~] T024 [US2] Implement `src/models/evaluate.py`:
 - Calculate R² and RMSE for both models.
 - **Mandatory**: Implement **Permutation Test** (10,000 permutations) on the difference in CV scores for 20 ≤ N < 100, as per research.md and plan.md (Section 3.3). This test is robust to the dependency structure of Nested CV and deterministic feature expansion.
 - **Mandatory**: Implement **Bootstrap 95% Confidence Interval** for N < 20.
 - **Mandatory**: Perform sensitivity analysis sweeping cutoffs {0.01, 0.05, 0.1} specifically on the **Permutation Test p-value**.
 - Output results to logs: Permutation Test p-value, Bootstrap CI bounds, and sensitivity analysis results.
 - **Note**: This task implements the Permutation Test as mandated by the research plan and plan.md. The spec FR-005 (mandating Corrected Resampled t-test) is flagged for a kickback due to its potential scientific invalidity in this context.
- [ ] T025 [US2] Implement `src/models/main_eval.py`: Orchestration script to run training, evaluation, and print the final comparison table (R² delta, CI, significance).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance Analysis and Reporting (Priority: P3)

**Goal**: Generate SHAP plots and reports to interpret model decisions and rank feature importance.

**Independent Test**: Run SHAP script and verify:
1. SHAP summary plot generated and saved as PNG.
2. Top features extracted and reported with direction of influence.

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for SHAP value extraction and formatting in `tests/unit/test_shap_utils.py`

### Implementation for User Story 3

- [ ] T027 [US3] Implement `src/models/interpret.py`:
 - Load the trained Thermodynamic GBR model.
 - Compute SHAP values using `TreeExplainer`.
 - Generate and save SHAP summary plot (PNG) in `data/outputs/`.
 - Extract top features and calculate mean absolute SHAP values.
 - Determine direction of influence (positive/negative correlation) for top features.
- [ ] T028 [US3] Implement `src/reports/generate_report.py`:
 - Compile final results: R² delta, statistical test results, SHAP top 5 list.
 - Format report with text summary: "feature_name: +value" or "feature_name: positive correlation".
 - Save final report to `docs/reports/`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Update `README.md` with quickstart instructions and execution commands
- [ ] T030 [P] Add `.gitignore` and CI configuration (GitHub Actions) for CPU-only runner
- [ ] T031 [P] Create `tests/integration/test_runtime.py` script to run the full pipeline, capture execution time, and **log the specific duration value** to stdout and a log file as a measured outcome for SC-005. Also assert pipeline duration < 6h and log failure if exceeded.
- [ ] T032 [P] Create `src/utils/runtime_logger.py` to ensure the total execution time is explicitly logged to standard output and a dedicated log file (`logs/runtime.log`) as a measured outcome for SC-005. This task ensures the artifact (the logged time value) is produced for the report, distinct from the pass/fail assertion in T031.
- [ ] T033 Verify all artifacts (CSVs, plots, reports) are hashed and state updated per `src/utils/hash.py`

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
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
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
- **Critical Constraint**: All models MUST run on CPU-only CI (cores, 7GB RAM). No GPU/CUDA.
- **Critical Constraint**: Synthetic data MUST pass Physics Consistency Check (R² > 0.8) before proceeding to real data modeling.
- **Critical Constraint**: Both models MUST train on the exact same intersection of data to ensure fair comparison.
- **Critical Constraint**: Statistical tests MUST follow the research plan (Permutation Test for 20 ≤ N < 100, Bootstrap for N < 20). The spec FR-005 (Corrected Resampled t-test) is flagged for a kickback.
- **Note on Statistical Methodology**: The research plan (research.md:3.3) and plan.md (Section 3.3) explicitly mandate the Permutation Test due to dependency violations in Nested CV. The spec FR-005 (Corrected Resampled t-test) is flagged for a kickback. This task list implements the scientifically robust Permutation Test.