# Tasks: Embodied Curriculum Learning: Physical Simulation for Abstract Concept Teaching

**Input**: Design documents from `/specs/[###-feature]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [ ] T001a [P] Create code directories: `code/src/`, `code/tests/` at repository root (Constitution Principle III, FR-001)
- [ ] T001b [P] Create data directories: `data/raw/`, `data/processed/`, `data/synthetic/`, `data/derivation_logs/` (Constitution Principle III, FR-001)
- [ ] T001c [P] Create state directories: `state/projects/PROJ-560-embodied-curriculum-learning-physical-si/` (Constitution Principle III, FR-001)
- [ ] T002a [P] Create `requirements.in` in `code/` listing `pandas`, `scipy`, `statsmodels`, `numpy`, `pyyaml`, `pytest`, `black`, `ruff` as dependencies (no versions).
- [ ] T002b [P] Resolve and pin exact versions for dependencies in `code/requirements.txt` using `pip-compile requirements.in` (or manual lookup) ensuring reproducibility.
- [ ] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools in `code/` (create `ruff.toml` and `pyproject.toml` configurations).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes T014 (SyntheticDataGenerator)** to ensure data pipeline fallbacks are available.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement `code/src/__init__.py` and basic logging configuration in `code/src/logging_config.py`
- [ ] T006 [P] Create `DatasetRecord` dataclass in `code/src/models.py` with `pre_test_score`, `post_test_score`, `instruction_type`, `covariates` (static data structure only)
- [ ] T007 [P] Create `AnalysisResult` and `SensitivitySweep` dataclasses in `code/src/models.py`
- [ ] T008 [P] Implement CLI argument parser in `code/src/cli.py` supporting `--mode`, `--input`, `--sweep_thresholds`, and `--seed`. **Do NOT** include `--concept_definition` as it is out of scope per Spec and Plan.
- [ ] T009 [P] Setup deterministic random seed management in `code/src/utils.py` for reproducibility (numpy, python)
- [ ] T014 [P] [US1] Implement `SyntheticDataGenerator` class in `code/src/synthetic_gen.py` to generate datasets with configurable mean differences, sample sizes, and ground truths for statistical validation (FR-009). **Must include**: 
  1. Accept parameters: `n`, `seed`, `mean_diff_embodied`, `mean_diff_static`.
  2. **Conditional Logic**: Check CLI flag `--mode`. 
     - If `--mode=secondary_analysis`: **MUST NOT** generate `mapping_log`. Raise an error if attempted.
     - If `--mode=synthetic`: Generate `mapping_log` file at `data/synthetic/mapping_log.json` with schema keys `physics_param`, `math_concept`, `mapping_rule` to satisfy Constitution Principle VI (Simulation-Pedagogy Alignment).
  3. Ensure generation is deterministic based on `seed`.
  **Dependency**: T006 (Base Schema), T008 (CLI Args).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Processing and Synthetic Data Generation (Priority: P1) 🎯 MVP

**Goal**: Provide a deterministic, CPU-tractable environment that loads public data or generates synthetic data for validation.

**Independent Test**: The system can be tested by either (a) loading a sample of the OpenML math reasoning dataset and outputting a processed CSV, or (b) invoking the synthetic data generator to create a labeled dataset, all without requiring external network calls or GPU resources.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for `DatasetRecord` validation in `code/tests/test_models.py`
- [ ] T011 [P] [US1] Unit test for `SyntheticDataGenerator` output schema in `code/tests/test_synthetic_gen.py`

### Implementation for User Story 1

- [ ] T012a [US1] Implement `load_public_dataset` in `code/src/data_loader.py` to read CSV/JSON, validate required columns (`pre_test_score`, `post_test_score`, `instruction_type`). **Logic**: 
  1. Attempt to load public data.
  2. If `instruction_type` column is missing, invoke `SyntheticDataGenerator.generate(n, seed, mean_diff_embodied, mean_diff_static)` (T014) to create a labeled dataset for validation.
  3. If generation fails, **MUST** exit with code 1 and **MUST** print to stderr: `Primary research question cannot be answered: missing instruction_type and synthetic generation failed`. Log error to `data/derivation_logs/skipped_records.log` in JSONL format with schema: `{"timestamp": "<ISO8601>", "error_code": "FALLBACK_FAILED", "reason": "synthetic_gen_failed", "dataset_source": "<url_or_path>"}` (FR-008). 
  **Output**: `data/processed/validated_fallback.csv` and `data/derivation_logs/skipped_records.log`. 
  **Dependency**: T014 (Phase 2) must be implemented first.
- [ ] T012b [US1] Implement `handle_synthetic_fallback_failure` in `code/src/data_loader.py` to explicitly format and log the "clear error message" and ensure `sys.exit(1)` is called if synthetic generation fails, satisfying FR-008's requirement to report primary data availability risk before failing.
- [ ] T013 [US1] Implement `calculate_gain_scores` in `code/src/data_loader.py` to compute `post - pre`, excluding rows with missing values and logging them to `data/derivation_logs/skipped_records.log` (FR-001).
- [ ] T015 [US1] Implement CLI entry point logic in `code/src/cli.py` to switch between `--mode=secondary_analysis` and `--mode=synthetic` and write output to `data/processed/` or `data/synthetic/` (depends on T008, T014, T012a, T012b). **Dependency**: Phase 2 (Foundational) completion.
- [ ] T017a [US1] Configure logging handler in `code/src/logging_config.py` to write specifically to `data/derivation_logs/skipped_records.log` in JSONL format.
- [ ] T017b [US1] Add log statements in `code/src/data_loader.py` for data loading events and missing pre-test scores, ensuring they write to the configured handler from T017a.

---

## Phase 4: User Story 2 - Statistical Comparison and Inference (Priority: P2)

**Goal**: Perform ANCOVA as the primary inference method to address regression to the mean (Plan), and independent samples t-tests as secondary descriptive stats (Spec FR-002). Frame results as associational.

**Methodological Priority**: The Plan's 'Complexity Tracking' mandates ANCOVA as the primary method to address regression to the mean. The Spec FR-002 mandates t-tests. This implementation satisfies both: ANCOVA is the primary inference engine (Plan), t-tests are secondary descriptive stats (Spec).

**Independent Test**: The system can be tested by running the analysis script on a synthetic dataset where the "embodied" group has a known mean gain and the "static" group has a known mean gain., verifying that the output reports an ANCOVA F-statistic and p-value consistent with these inputs, alongside t-test results.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for Welch's t-test logic in `code/tests/test_stats_engine.py`
- [ ] T019 [P] [US2] Unit test for Bonferroni correction logic in `code/tests/test_stats_engine.py`
- [ ] T018b [P] [US2] Unit test for ANCOVA logic in `code/tests/test_stats_engine.py`

### Implementation for User Story 2

- [ ] T020b [US2] Implement `run_ancova` in `code/src/stats_engine.py` to perform ANCOVA with `pre_test_score` as covariate and `instruction_type` as factor, addressing regression to the mean (Plan Complexity Tracking). **This is the PRIMARY inference method.**
- [ ] T020a [US2] Implement `run_t_test` in `code/src/stats_engine.py` to perform Student's or Welch's t-test on gain scores based on Levene's test result (FR-002). **This is for SECONDARY descriptive statistics only.**
- [ ] T021 [US2] Implement `calculate_effect_size` (Cohen's d) and `confidence_interval` in `code/src/stats_engine.py` (FR-002).
- [ ] T022 [US2] Implement `apply_bonferroni_correction` in `code/src/stats_engine.py` to adjust alpha based on number of concepts tested (FR-004).
- [ ] T023 [US2] Implement `frame_inference` in `code/src/stats_engine.py` to explicitly label all findings as "associational" and include methodological caveats (FR-003).
- [ ] T024 [US2] Implement `check_collinearity` in `code/src/stats_engine.py` to detect |r| > 0.8 between predictors and report diagnostics (FR-006).
- [ ] T025 [US2] Implement `calculate_power` in `code/src/stats_engine.py` to compute achieved power and flag "underpowered" results if < 0.80 (FR-007).
- [ ] T026a [US2] Implement `aggregate_stats_results` in `code/src/stats_engine.py` to combine ANCOVA (primary), t-test (secondary), effect sizes, power, and collinearity diagnostics into a single dictionary structure.
- [ ] T026b [US2] Implement `write_analysis_results` in `code/src/stats_engine.py` to write the aggregated dictionary to `data/processed/results.json`. **Schema Keys**: 
  - `ancova_f_statistic` (PRIMARY)
  - `ancova_p_value` (PRIMARY)
  - `t_statistic` (under `secondary_descriptive_stats`)
  - `p_value` (under `secondary_descriptive_stats`)
  - `effect_size_cohen_d`
  - `confidence_interval`
  - `inference_framing` (Must contain exact string "associational" from T023)
  - `sensitivity_analysis` (Array of objects: `{"threshold": float, "n_participants": int, "effect_size_cohen_d": float, "robustness_flag": bool}`)
  **Dependency**: T023, T026a.

---

## Phase 5: User Story 3 - Sensitivity Analysis for Thresholds (Priority: P3)

**Goal**: Execute a sensitivity analysis sweeping inclusion thresholds to demonstrate robustness of the headline effect size.

**Independent Test**: The system can be tested by running the analysis with the `--sweep` flag on a dataset with N ≥ 30 and verifying that the output contains a table of effect sizes corresponding to each threshold value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for sensitivity sweep logic in `code/tests/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `run_sensitivity_sweep` in `code/src/sensitivity.py` to: (1) check total N; (2) if N < 30, return early with `insufficient_data` flag; (3) if N >= 30, iterate over the fixed set of thresholds **[0.01, 0.05, 0.10]**, calculate effect sizes, aggregate results into `SensitivitySweep` objects, and append to the main JSON report (FR-005).
- [ ] T030 [US3] Implement `check_robustness_warning` in `code/src/sensitivity.py` to flag `robustness_warning: true` in the output if the effect size drops below a negligible threshold at any point in the sweep (SC-003). **Dependency**: Must consume `SensitivitySweep` objects produced by T028.

---

## Phase 6: Scope Boundary & Documentation

**Purpose**: Address scope limitations and constitutional requirements without modifying core statistical logic.

**Note on Scope**: This phase addresses documentation and cleanup. Philosophical framing (training vs. teaching, abstract concept definitions) is **explicitly out of scope** for this MVP as per Spec Assumptions and Risks.

### Implementation for Scope Clarification

- [ ] T037 [P] Documentation updates in `code/../quickstart.md` and `docs/`. Specifically update the "Running the Analysis" section to include an example of running with synthetic data (the fallback scenario) and the "Data Sources" section to explain the `instruction_type` requirement and fallback behavior. The documentation must clarify that if public data lacks `instruction_type`, synthetic data is used for pipeline validation only.
- [ ] T038 [P] Code cleanup and refactoring to ensure type hinting and docstrings are complete. Run `ruff check --select=ANN` using the configuration from T003 and fix all errors.
- [ ] T039 [P] Performance verification: Run `code/src/cli.py` with `--mode=synthetic --n=10000` on a fresh runner (no caching) and verify exit time < 600s (10 minutes) **wall-clock time** on a 2-core CPU (SC-001). 
  **Pass/Fail Criteria**: 
  - Task **PASSES** if duration <= 600s AND `data/processed/perf_log.json` is written.
  - Task **FAILS** if duration > 600s OR `perf_log.json` is missing. If duration > 600s, write a warning to the log and mark task as FAILED in the CI step.
  Write the timing result to `data/processed/perf_log.json` with schema: `{ "timestamp": "<ISO8601>", "n_records": int, "duration_seconds": float }`.
- [ ] T040a [P] Add unit test `test_t_test_underpowered` in `code/tests/test_stats_engine.py` for N < 30 case.
- [ ] T040b [P] Add unit test `test_load_missing_columns` in `code/tests/test_data_loader.py` for missing column handling.
- [ ] T040c [P] Add unit test `test_collinearity_detection` in `code/tests/test_stats_engine.py` for |r| > 0.8 case.
- [ ] T042 [P] Run `quickstart.md` validation to ensure end-to-end flow works. The test MUST pass using either a valid public dataset OR the synthetic data generator (if public data lacks `instruction_type`), as per the spec's Risk section.

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (T014 is now in Phase 2)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data input
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 for data and base stats

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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for DatasetRecord validation in code/tests/test_models.py"
Task: "Unit test for SyntheticDataGenerator output schema in code/tests/test_synthetic_gen.py"

# Launch all models for User Story 1 together:
Task: "Implement load_public_dataset in code/src/data_loader.py" (Note: T014 must be done first, but T014 is in Phase 2)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes T014)
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
- **Constitution Principle VI**: The `mapping_log` is required for Synthetic Data Generation Mode to document the physics-to-math mapping. Secondary Analysis Mode is exempt. **T014 implements this conditional logic.**
- **FR-008 Compliance**: If `instruction_type` is missing in public data, the system MUST automatically invoke the Synthetic Data Generator. If generation fails, the system MUST exit with code 1 and log a clear error message: "Primary research question cannot be answered: missing instruction_type and synthetic generation failed".
- **Associational Framing**: All statistical findings MUST be framed as "associational" (FR-003). No causal claims (e.g., "teaching" vs "training") are permitted in the output without explicit qualification.
- **Scope Boundary**: Philosophical/pedagogical framing (training vs. teaching, abstract concept definitions) is **explicitly out of scope** for the statistical engine. The 'Associational Framing' is handled by T023.
- **Plan Mismatch**: The plan.md Complexity Tracking table mandates ANCOVA as the primary method. The Spec mandates t-tests. **This tasks.md satisfies both**: ANCOVA is primary (Plan), t-tests are secondary (Spec). **T026b enforces this hierarchy.**
- **Synthetic Mode Validity**: The `--mode=synthetic` is valid for pipeline validation. The system does not reject `pedagogical_mode` values; it generates data as requested. Documentation must reflect that the tool is a statistical validator, not a pedagogical simulator.
- **Removed Tasks**: Phase 7 (T050-T057) and associated tasks have been **removed** as they attempted to implement unmeasurable philosophical concepts, violating the Spec's scope boundary.
- **Rejected Tasks**: Tasks T002a, T016, T026 (old), and T038 (old) marked as "REJECTED" in input have been removed or updated (T026 split into T026a/T026b; T002a re-enabled).
- **New Phase 2**: T014 moved to Phase 2 to resolve ordering and dependency blocks.