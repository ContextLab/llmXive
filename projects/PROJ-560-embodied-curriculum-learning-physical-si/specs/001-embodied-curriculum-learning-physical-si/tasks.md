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

- [X] T001a [P] Create code directories: `code/src/`, `code/tests/` at repository root (Constitution Principle III, FR-001)
- [X] T001b [P] Create data directories: `data/raw/`, `data/processed/`, `data/synthetic/`, `data/derivation_logs/` (Constitution Principle III, FR-001)
- [X] T001c [P] Create state directories: `state/projects/PROJ-560-embodied-curriculum-learning-physical-si/` (Constitution Principle III, FR-001)
- [X] T002a [P] Create `code/requirements.in` listing `pandas`, `scipy`, `statsmodels`, `numpy`, `pyyaml`, `pytest`, `black`, `ruff` as dependencies, one per line, no comments.
- [X] T002b [P] Resolve and pin exact versions for dependencies in `code/requirements.txt` using `pip-compile requirements.in` (or manual lookup) ensuring reproducibility.
- [X] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools in `code/` (create `ruff.toml` and `pyproject.toml` configurations).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes T014 (SyntheticDataGenerator)** to ensure data pipeline fallbacks are available.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `code/src/__init__.py` and basic logging configuration in `code/src/logging_config.py`
- [X] T006 [P] Create `DatasetRecord` dataclass in `code/src/models.py` with `pre_test_score`, `post_test_score`, `instruction_type`, `covariates` (static data structure only)
- [X] T007 [P] Create `AnalysisResult` and `SensitivitySweep` dataclasses in `code/src/models.py`
- [X] T008 [P] Implement CLI argument parser in `code/src/cli.py` supporting `--mode`, `--input`, `--sweep_thresholds`, and `--seed`. **Do NOT** include `--concept_definition` as it is out of scope per Spec and Plan.
- [X] T009 [P] Setup deterministic random seed management in `code/src/utils.py` for reproducibility (numpy, python)
- [X] T014 [P] [US1] Implement `SyntheticDataGenerator` class in `code/src/synthetic_gen.py` to generate datasets with configurable mean differences, sample sizes, and ground truths for statistical validation (FR-009). **Must include**:
 1. Accept parameters: `n`, `seed`, `mean_diff_embodied`, `mean_diff_static`.
 2. **Conditional Logic**: Accept a `mode` parameter.
 - If `mode=secondary_analysis`: **MUST NOT** generate `mapping_log`. Raise an error if attempted.
 - If `mode=synthetic`: Generate `mapping_log` file at `data/synthetic/mapping_log.json` with schema keys `physics_param`, `math_concept`, `mapping_rule`. The `physics_param` must be 'simulated_gain', `math_concept` must be 'mathematical_reasoning', and `mapping_rule` must describe the linear mapping used to generate the data, satisfying Constitution Principle VI (Simulation-Pedagogy Alignment).
 3. Ensure generation is deterministic based on `seed`.
 **Dependency**: T006 (Base Schema), T008 (CLI Args).
- [X] T046 [P] [US1] Update `code/src/synthetic_gen.py` (T014) to include a metadata field in the generated `mapping_log.json` that explicitly states the "Causal Mechanism" assumption: "Virtual manipulation is assumed to map to abstract principle understanding via [specific mapping rule]." This satisfies the request to articulate the causal mechanism, even if the mechanism is a hypothesis. **Dependency**: T014.

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

- [X] T012a [US1] Implement `load_public_dataset` in `code/src/data_loader.py` to read CSV/JSON, validate required columns (`pre_test_score`, `post_test_score`, `instruction_type`). **Logic**:
 1. Read input file.
 2. Validate presence of required columns.
 3. Return dataset if valid.
 **Output**: Dataset object.
 **Dependency**: T006 (DatasetRecord), T008 (CLI Args), T014 (SyntheticDataGenerator) for fallback context.
- [X] T012c [US1] Implement `handle_fallback_logic` in `code/src/data_loader.py` to:
 1. If `instruction_type` column is missing, invoke `SyntheticDataGenerator.generate(n, seed, mean_diff_embodied=10.0, mean_diff_static=5.0)` (T014) to create a labeled dataset for analysis.
 2. If generation fails, **MUST** exit with code 1 and **MUST** print to stderr: `Primary research question cannot be answered: missing instruction_type and synthetic generation failed`.
 3. Log error to `data/derivation_logs/skipped_records.log` in JSONL format with schema: `{"timestamp": "<ISO8601>", "reason": "synthetic_gen_failed", "dataset_source": "<url_or_path>"}` (FR-008).
 **Output**: `data/processed/validated_fallback.csv` (if successful) or exit code 1.
 **Dependency**: T014 (Phase 2) must be implemented first. T012a (load_public_dataset).
- [X] T013 [US1] Implement `calculate_gain_scores` in `code/src/data_loader.py` to compute `post - pre`, excluding rows with missing values and logging them to `data/derivation_logs/skipped_records.log` (FR-001).
- [X] T015 [US1] Implement CLI entry point logic in `code/src/cli.py` to switch between `--mode=secondary_analysis` and `--mode=synthetic` and write output to `data/processed/` or `data/synthetic/` (depends on T008, T014, T012a, T012c). **Dependency**: Phase 2 (Foundational) completion.
- [X] T017a [P] [US1] Configure logging handler in `code/src/logging_config.py` to write specifically to `data/derivation_logs/skipped_records.log` in JSONL format. **Dependency**: T005 (logging configuration).
- [X] T017b [P] [US1] Add log statements in `code/src/data_loader.py` for data loading events and missing pre-test scores, ensuring they write to the configured handler from T017a. **Dependency**: T017a.

---

## Phase 4: User Story 2 - Statistical Comparison and Inference (Priority: P2)

**Goal**: Perform independent samples t-tests as the primary statistical method (Spec FR-002) and ANCOVA as a secondary descriptive method (Plan Complexity Tracking). Frame results as associational.

**Independent Test**: The system can be tested by running the analysis script on a synthetic dataset where the "embodied" group has a known mean gain and the "static" group has a known mean gain., verifying that the output reports a t-statistic and p-value consistent with these inputs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Welch's t-test logic in `code/tests/test_stats_engine.py`
- [X] T019 [P] [US2] Unit test for Bonferroni correction logic in `code/tests/test_stats_engine.py`
- [X] T018b [P] [US2] Unit test for ANCOVA logic in `code/tests/test_stats_engine.py`

### Implementation for User Story 2

- [X] T020a [US2] Implement `run_t_test` in `code/src/stats_engine.py` to perform Student's or Welch's t-test on gain scores based on Levene's test result (FR-002). **This is the PRIMARY statistical method** as mandated by Spec FR-002.
- [X] T020b [US2] Implement `run_ancova` in `code/src/stats_engine.py` to perform ANCOVA with `pre_test_score` as covariate and `instruction_type` as factor, addressing regression to the mean (Plan Complexity Tracking). **This is for SECONDARY descriptive statistics only.**
- [X] T021 [US2] Implement `calculate_effect_size` (Cohen's d) and `confidence_interval` in `code/src/stats_engine.py` (FR-002).
- [X] T022 [US2] Implement `apply_bonferroni_correction` in `code/src/stats_engine.py` to adjust alpha based on number of concepts tested (FR-004).
- [X] T023 [US2] Implement `frame_inference` in `code/src/stats_engine.py` to explicitly label all findings as "associational" and include methodological caveats (FR-003).
- [X] T024 [US2] Implement `check_collinearity` in `code/src/stats_engine.py` to detect |r| > 0.8 between predictors and report diagnostics (FR-006).
- [X] T025 [US2] Implement `calculate_power` in `code/src/stats_engine.py` to compute achieved power and flag "underpowered" results if < 0.80 (FR-007).
- [X] T026a [US2] Implement `aggregate_stats_results` in `code/src/stats_engine.py` to combine t-test (primary), ANCOVA (secondary), effect sizes, power, and collinearity diagnostics into a single dictionary structure.
- [X] T026b [US2] Implement `write_partial_results` in `code/src/stats_engine.py` to write the aggregated dictionary from T026a to `data/processed/results_us2.json`. **Schema Keys**:
 - `t_statistic` (PRIMARY)
 - `p_value` (PRIMARY)
 - `ancova_f_statistic` (under `secondary_descriptive_stats`)
 - `ancova_p_value` (under `secondary_descriptive_stats`)
 - `effect_size_cohen_d`
 - `confidence_interval`
 - `inference_framing` (Must contain the full explanatory statement from FR-003: "Findings are associational; no causal inference is drawn due to observational nature of data.")
 - `power_analysis`
 - `collinearity_diagnostics`
 **Dependency**: T023, T026a. **Purpose**: Enables independent testing of US2 without requiring US3.

---

## Phase 5: User Story 3 - Sensitivity Analysis for Thresholds (Priority: P3)

**Goal**: Execute a sensitivity analysis sweeping inclusion thresholds to demonstrate robustness of the headline effect size.

**Independent Test**: The system can be tested by running the analysis with the `--sweep` flag on a dataset with N ≥ 30 and verifying that the output contains a table of effect sizes corresponding to each threshold value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for sensitivity sweep logic in `code/tests/test_sensitivity.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `run_sensitivity_sweep` in `code/src/sensitivity.py` to: (1) check total N; (2) if N < 30, return early with `insufficient_data` flag; (3) if N >= 30, iterate over the fixed set of thresholds **[0.01, 0.05, 0.10]** (linked to CLI argument `--sweep_thresholds` per FR-005), calculate effect sizes, aggregate results into `SensitivitySweep` objects, and append to the main JSON report (FR-005).
- [X] T030 [US3] Implement `check_robustness_warning` in `code/src/sensitivity.py` to flag `robustness_warning: true` in the output if the effect size drops below 0.2 (per SC-003) at any point in the sweep. **Dependency**: Must consume `SensitivitySweep` objects produced by T028.
- [X] T026c [US3] Implement `finalize_results` in `code/src/stats_engine.py` to merge `results_us2.json` (T026b) with sensitivity analysis results (T028, T030) into the final `data/processed/results.json`. **Schema Keys**:
 - `t_statistic` (PRIMARY)
 - `p_value` (PRIMARY)
 - `ancova_f_statistic` (under `secondary_descriptive_stats`)
 - `ancova_p_value` (under `secondary_descriptive_stats`)
 - `effect_size_cohen_d`
 - `confidence_interval`
 - `inference_framing` (Must contain exact string "associational" from T023, plus full explanatory statement)
 - `sensitivity_analysis` (Array of objects: `{"threshold_value": float, "n_participants_retained": int, "effect_size_cohen_d": float, "robustness_flag": bool}`)
 - `robustness_warning` (boolean)
 **Dependency**: T023, T026a, T026b, T028, T030.

---

## Phase 6: Scope Boundary & Documentation

**Purpose**: Address scope limitations and constitutional requirements without modifying core statistical logic.

**Note on Scope**: This phase addresses documentation and cleanup. Philosophical framing (training vs. teaching, abstract concept definitions) is **explicitly out of scope** for this MVP as per Spec Assumptions and Risks.

### Implementation for Scope Clarification

- [X] T037 [P] Documentation updates in `code/../quickstart.md` and `docs/`. Specifically update the "Running the Analysis" section to include an example of running with synthetic data (the fallback scenario) and the "Data Sources" section to explain the `instruction_type` requirement and fallback behavior. The documentation must clarify that if public data lacks `instruction_type`, synthetic data is used for pipeline validation only.
- [X] T038 [P] Code cleanup and refactoring to ensure type hinting and docstrings are complete. Run `ruff check --select=ANN code/src/` and ensure all files pass (exit code 0). Generate a report at `code/tests/ruff_report.txt` if any warnings exist, or record success. **Dependency**: T003 (ruff config).
- [X] T039 [P] Performance verification: Run `time python code/src/cli.py --mode=synthetic --n=10000` on a fresh runner (no caching) and verify exit time < 600s (10 minutes) **wall-clock time** on a 2-core CPU (SC-001).
 **Pass/Fail Criteria**:
 - Task **PASSES** if duration <= 600s AND `data/processed/perf_log.json` is written.
 - Task **FAILS** if duration > 600s OR `perf_log.json` is missing. If duration > 600s, write a warning to the log and mark task as FAILED in the CI step.
 Write the timing result to `data/processed/perf_log.json` with schema: `{ "timestamp": "<ISO8601>", "n_records": int, "duration_seconds": float }`.
 **Note**: The `--n=10000` parameter is mandatory for this benchmark to match the Plan's Performance Goals.
- [X] T040a [P] Add unit test `test_t_test_underpowered` in `code/tests/test_stats_engine.py` for N < 30 case.
- [X] T040b [P] Add unit test `test_load_missing_columns` in `code/tests/test_data_loader.py` for missing column handling.
- [X] T040c [P] Add unit test `test_collinearity_detection` in `code/tests/test_stats_engine.py` for |r| > 0.8 case.
- [X] T042 [P] Run `quickstart.md` validation to ensure end-to-end flow works. The test MUST pass using either a valid public dataset OR the synthetic data generator (if public data lacks `instruction_type`), as per the spec's Risk section. Execute: `pytest code/tests/test_e2e.py::test_quickstart_flow`.

---

## Phase 7: Research-Stage Review Resolution (Revisions)

**Purpose**: Address specific philosophical and definitional concerns raised by research-stage reviewers (Aristotle and Socrates) by updating documentation and metadata, without altering the core statistical engine's scope.

**Context**: Reviewers questioned the distinction between "training" vs. "teaching" (Aristotle) and the definition of "abstract concept" (Socrates). The statistical engine remains focused on *measurable gain scores* from *instruction types*, but the documentation must explicitly frame these limitations and definitions to satisfy the research validity requirements.

### Implementation for Review Resolution

- [X] T043 [P] Update `docs/research-framing.md` to explicitly distinguish between "Training" (habituation/motor skill acquisition via simulation) and "Teaching" (intellectual actualization/dialectic). The document must state that the current MVP measures *training effects* (gain scores) and explicitly disclaims claims about *teaching* (intellectual actualization) without further qualitative study. Cite Aristotle-simulated review.
- [X] T044 [P] Update `docs/research-framing.md` to define the "Body" in "Embodied" as the *simulation's internal physics engine* (virtual mechanics) rather than the student's physical interaction, acknowledging the limitation that this is an *image* of embodiment rather than direct physical interaction. Cite Aristotle-simulated review.
- [X] T045 [P] Update `docs/research-framing.md` to provide a strict operational definition of "Abstract Concept" for this study: "Mathematical reasoning tasks (e.g., algebra, geometry) where the correct answer is derived from logical rules rather than sensory observation." The document must acknowledge the Socratic critique that operational success does not guarantee conceptual understanding and state that the current metrics (gain scores) measure *performance* not *understanding*. Cite Socrates-simulated review.
- [X] T047 [P] Add a "Limitations" section to `data/processed/results.json` output (via T026c) that explicitly lists: (1) The study measures performance gains, not intellectual actualization; (2) The "body" is virtual, not physical; (3) "Abstract concept" is operationally defined as mathematical reasoning tasks. This ensures the output report carries the necessary philosophical caveats.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Sensitivity Analysis (Phase 5)**: Depends on Phase 4 (US2) completion to aggregate stats.
- **Review Resolution (Phase 7)**: Can be done in parallel with Phase 6 (Documentation) but must be completed before final publication of the research report.

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
- Phase 7 (Review Resolution) tasks can run in parallel with Phase 6 (Scope Boundary) as they are documentation/metadata focused.

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
 - Developer D: Documentation & Review Resolution (Phase 6 & 7)
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
- **Scope Boundary**: Philosophical/pedagogical framing (training vs. teaching, abstract concept definitions) is **explicitly out of scope** for the statistical engine's core logic and output report.
- **Plan Mismatch**: The plan.md Complexity Tracking table mandates ANCOVA as the primary method. The Spec mandates t-tests. **This tasks.md satisfies the Spec**: t-tests are PRIMARY (Spec FR-002), ANCOVA is SECONDARY (Plan). **T020a and T020b enforce this hierarchy.**
- **Synthetic Mode Validity**: The `--mode=synthetic` is valid for pipeline validation. The system does not reject `pedagogical_mode` values; it generates data as requested. Documentation must reflect that the tool is a statistical validator, not a pedagogical simulator.
- **Removed Tasks**: Phase 7 (T043-T049) and associated tasks have been **removed** as they attempted to implement unmeasurable philosophical concepts, violating the Spec's scope boundary and Single Source of Truth principle.
- **Rejected Tasks**: Tasks T002a, T016, T026 (old), and T038 (old) marked as "REJECTED" in input have been removed or updated (T026 split into T026a/T026b/T026c; T002a re-enabled).
- **Schema Conformance**: T026b and T026c now use exact keys from Spec `SensitivitySweep` entity and US-3 acceptance criteria: `threshold_value`, `n_participants_retained`.
- **Performance Benchmark**: T039 explicitly mandates `--n=10000` to align with Plan Performance Goals.
- **Review Resolution**: Phase 7 tasks (T043-T047) address the specific philosophical critiques from Aristotle and Socrates by updating documentation and metadata, ensuring the research output is philosophically robust without overstepping the statistical engine's scope.
- **US2 Independent Test**: T026b allows US2 to be tested independently by writing a partial report. T026c merges US3 results for the final report.
- **T046 Moved**: T046 (code metadata update) moved to Phase 2 to ensure downstream tasks (T012c) can access the updated generator logic.