# Tasks: Embodied Curriculum Learning: Physical Simulation for Abstract Concept Teaching

**Input**: Design documents from `/specs/[###-feature]/`
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

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure: `code/src/`, `code/tests/`, `data/raw/`, `data/processed/`, `data/synthetic/`, `data/derivation_logs/`, `state/projects/PROJ-560-embodied-curriculum-learning-physical-si/`
- [ ] T002 Initialize Python 3.11 project with `pandas`, `scipy`, `statsmodels`, `numpy`, `pyyaml`, `json` dependencies in `code/requirements.txt` (pin exact versions)
- [ ] T003 [P] Configure linting (`ruff` or `flake8`) and formatting (`black`) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup directory structure for `data/raw`, `data/processed`, `data/synthetic`, `data/derivation_logs`
- [X] T005 [P] Implement `code/src/__init__.py` and basic logging configuration in `code/src/logging_config.py`
- [X] T006 [P] Create `DatasetRecord` dataclass in `code/src/models.py` with `pre_test_score`, `post_test_score`, `instruction_type`, `covariates` (static data structure only)
- [X] T007 Create `AnalysisResult` and `SensitivitySweep` dataclasses in `code/src/models.py`
- [X] T008 Implement CLI argument parser in `code/src/cli.py` supporting `--mode`, `--input`, `--sweep_thresholds`, and `--seed`
- [X] T009 Setup deterministic random seed management in `code/src/utils.py` for reproducibility (numpy, python)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Processing and Synthetic Data Generation (Priority: P1) 🎯 MVP

**Goal**: Provide a deterministic, CPU-tractable environment that loads public data or generates synthetic data for validation.

**Independent Test**: The system can be tested by either (a) loading a sample of the OpenML math reasoning dataset and outputting a processed CSV, or (b) invoking the synthetic data generator to create a labeled dataset, all without requiring external network calls or GPU resources.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for `DatasetRecord` validation in `code/tests/test_models.py`
- [X] T011 [P] [US1] Unit test for `SyntheticDataGenerator` output schema in `code/tests/test_synthetic_gen.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `load_public_dataset` in `code/src/data_loader.py` to read CSV/JSON, validate required columns (`pre_test_score`, `post_test_score`, `instruction_type`), and **automatically invoke** `SyntheticDataGenerator.generate()` if `instruction_type` is missing (FR-008). The fallback must be a hard-coded code path, not an error or manual trigger.
- [~] T013 [US1] Implement `calculate_gain_scores` in `code/src/data_loader.py` to compute `post - pre`, excluding rows with missing values and logging them to `data/derivation_logs/skipped_records.log` (FR-001).
- [X] T014 [US1] Implement `SyntheticDataGenerator` class in `code/src/synthetic_gen.py` to generate datasets with configurable mean differences, sample sizes, and ground truths for statistical validation (FR-009).
- [ ] T014.1 [US1] Implement `generate_mapping_log` in `code/src/synthetic_gen.py` to create `data/synthetic/mapping_log.json` (for Synthetic Mode only) documenting the causal chain: `Physics_Action` -> `Virtual_Object_State` -> `Abstract_Principle_Inference`, satisfying Constitution Principle VI. This must be executed as part of the synthetic generation flow.
- [X] T016 [US1] Add validation logic in `code/src/data_loader.py` to detect missing critical columns and **automatically invoke** `SyntheticDataGenerator.generate()` if `instruction_type` is missing in public data, ensuring the fallback is deterministic and requires no manual intervention (FR-008).
- [X] T015 [US1] Implement CLI entry point logic in `code/src/cli.py` to switch between `--mode=secondary_analysis` and `--mode=synthetic` and write output to `data/processed/` or `data/synthetic/` (depends on T008, T012, T014, T016).
- [~] T017 [US1] Add logging for data loading, skipped records, and synthetic generation parameters.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Comparison and Inference (Priority: P2)

**Goal**: Perform independent samples t-tests comparing mean gain scores, framing results as associational, and applying corrections.

**Independent Test**: The system can be tested by running the analysis script on a synthetic dataset where the "embodied" group has a known mean gain and the "static" group has a known mean gain., verifying that the output reports a t-statistic and p-value consistent with these inputs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Welch's t-test logic in `code/tests/test_stats_engine.py`
- [X] T019 [P] [US2] Unit test for Bonferroni correction logic in `code/tests/test_stats_engine.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `run_t_test` in `code/src/stats_engine.py` to perform Student's or Welch's t-test on gain scores based on Levene's test result (FR-002).
- [X] T021 [US2] Implement `calculate_effect_size` (Cohen's d) and `confidence_interval` in `code/src/stats_engine.py` (FR-002).
- [X] T022 [US2] Implement `apply_bonferroni_correction` in `code/src/stats_engine.py` to adjust alpha based on number of concepts tested (FR-004).
- [X] T023 [US2] Implement `frame_inference` in `code/src/stats_engine.py` to explicitly label all findings as "associational" and include methodological caveats (FR-003).
- [X] T024 [US2] Implement `check_collinearity` in `code/src/stats_engine.py` to detect |r| > 0.8 between predictors and report diagnostics (FR-006).
- [X] T025 [US2] Implement `calculate_power` in `code/src/stats_engine.py` to compute achieved power and flag "underpowered" results if < 0.80 (FR-007).
- [ ] T026 [US2] Aggregate all statistical results into an `AnalysisResult` object and write to JSON output in `data/processed/results.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis for Thresholds (Priority: P3)

**Goal**: Execute a sensitivity analysis sweeping inclusion thresholds to demonstrate robustness of the headline effect size.

**Independent Test**: The system can be tested by running the analysis with the `--sweep` flag on a dataset with N ≥ 30 and verifying that the output contains a table of effect sizes corresponding to each threshold value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for sensitivity sweep logic in `code/tests/test_sensitivity.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `run_sensitivity_sweep` in `code/src/sensitivity.py` to iterate over thresholds representing small, moderate, and large significance levels (FR-005).
- [~] T029 [US3] Implement logic to skip sweep and flag "insufficient data for robustness check" if N < 30 (FR-005).
- [X] T030 [US3] Implement `check_robustness_warning` in `code/src/sensitivity.py` to flag `robustness_warning: true` if effect size drops below a substantively meaningful threshold at any threshold (FR-005).
- [~] T031 [US3] Aggregate sweep results into `SensitivitySweep` objects and append to the main JSON report.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `quickstart.md` and `docs/` explaining the data processing, statistical methods, and the associational framing of results.
- [ ] T038 Code cleanup and refactoring to ensure type hinting and docstrings are complete.
- [ ] T039 [P] Performance verification: Run `code/src/cli.py` with N=10,000 synthetic records and verify exit time < 600s (10 minutes) **wall-clock time on a 2-core CPU, 7GB RAM** (SC-001).
- [ ] T040 [P] Additional unit tests for edge cases (N < 30, missing columns, collinearity).
- [ ] T041 Security hardening (ensure no arbitrary code execution in data loading).
- [ ] T042 Run `quickstart.md` validation to ensure end-to-end flow works.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data input
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 for data and base stats
- **Polish (Final Phase)**: Depends on all user stories being complete

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
Task: "Unit test for DatasetRecord validation in code/tests/test_models.py"
Task: "Unit test for SyntheticDataGenerator output schema in code/tests/test_synthetic_gen.py"

# Launch all models for User Story 1 together:
Task: "Implement load_public_dataset in code/src/data_loader.py"
Task: "Implement SyntheticDataGenerator class in code/src/synthetic_gen.py"
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
 - Developer A: User Story 1 (Data/Synthetic)
 - Developer B: User Story 2 (Stats/Inference)
 - Developer C: User Story 3 (Sensitivity)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All statistical tasks must run on CPU-only CI with a minimal core count and constrained memory allocation. No GPU, no 8-bit quantization, no large model training.
- **Data Integrity**: Never fabricate input data. Use real public datasets or synthetic data *only* for pipeline validation as per FR-009.
- **Constitution Principle VI**: The `mapping_log` is required ONLY for Synthetic Data Generation Mode to document the physics-to-math mapping. Secondary Analysis Mode is exempt.
- **FR-008 Compliance**: If `instruction_type` is missing in public data, the system MUST automatically invoke the Synthetic Data Generator. No manual intervention or error-only fallback is permitted.
- **Associational Framing**: All statistical findings MUST be framed as "associational" (FR-003). No causal claims (e.g., "teaching" vs "training") are permitted in the output.