# Tasks: The Influence of Simulated Social Status on Risk-Taking Behavior

**Input**: Design documents from `/specs/001-simulated-status-risk/`
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

- [X] T001a [P] Create `data/` directory structure (`data/raw/`, `data/processed/`) with `.gitkeep` files to ensure tracking.
- [X] T001b [P] Create `code/` directory structure (`code/__init__.py`, `code/config.py`) with `.gitkeep` files.
- [X] T001c [P] Create `tests/` and `docs/` directory structures with `.gitkeep` files.
- [X] T002a [P] Create `code/requirements.txt` listing specific dependencies: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `ruff`, `black`.
- [X] T002b [P] Pin versions in `code/requirements.txt` for all dependencies listed in T002a to ensure deterministic environments.
- [X] T003a [P] Create `.pre-commit-config.yaml` configuring ruff and black hooks.
- [ ] T003b [P] Create `.gitignore` excluding `__pycache__`, `*.pyc`, `.env`, and `data/raw/*.csv` (checksummed only).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T004 [P] Create `data/checksums.json` with initial structure `{"files": {}}` to satisfy Constitution Principle III.
- [~] T005 [P] Implement `code/logger.py` with a standard logging configuration (JSON format, file output) and create `code/config.py` with empty placeholders.
- [~] T006 [P] Create `code/models.py` explicitly defining `Participant`, `Condition`, and `ModelResult` entities as Pydantic or dataclass models.
- [~] T007 [P] Setup pytest framework in `tests/` with `conftest.py` and `tests/contract/` directory.
- [~] T008 [P] Implement `code/utils.py` for common helpers (seeding, file I/O, checksum calculation).
- [~] T010a [P] [US1] Read effect sizes (Cohen's d) and citations from `research.md` and define them as constants in `code/config.py` for simulation parameters.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Synthesis and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset based on meta-analytic effect sizes and preprocess it for analysis, ensuring correct categorical factor integrity.

**Independent Test**: Verify that the output CSV contains required columns (`status_level`, `observed_behavior`, `risk_taking_score`, `participant_id`), that the data structure is correctly tagged, and that the random seed produces deterministic results.

### Implementation for User Story 1

- [~] T010b [P] [US1] Implement `code/generate_data.py`: Synthetic data generator using parameters from T010a, ensuring N=800 and between-subjects design.
- [~] T011 [US1] Implement `code/generate_data.py`: Add a validation function that raises a `ValueError` with the message "Error: status_level has no variance. Experimental condition integrity violated." if the generated data lacks variance, and exit with code 1.
- [~] T012 [US1] Implement `code/preprocess.py`: Load raw synthetic data, map `status_level` and `observed_behavior` to categorical factors (High/Low, Risky/Conservative).
- [~] T012b [US1] Implement `code/preprocess.py`: Implement the specific binning strategy (e.g., High vs Low/Medium) for input data with >2 levels, OR implement logic to flag ambiguity for manual review as required by FR-002.
- [~] T012c [US1] Implement `code/preprocess.py`: Create a "meta-analysis stub" function that logs a clear decision record explaining why FR-001(b) was discarded in favor of simulation, satisfying the 'OR' requirement.
- [~] T012d [US1] Implement `code/config.py`: Create a `decision_record.json` file explicitly documenting the exclusion of the FR-001(b) meta-analysis path due to the Plan's constraint against external API calls and the unavailability of a single public dataset with the required factorial design.
- [~] T012e [US1] Implement `code/generate_data.py`: Add a validation check to ensure the generated dataset strictly adheres to the "between-subjects" design (one observation per `participant_id`) as mandated by the Plan's decision to use a Fixed-Effects model.
- [~] T013 [US1] Implement `code/preprocess.py`: Handle missing values (imputation or exclusion) and report the final N used for analysis.
- [~] T014a [US1] Implement `code/preprocess.py`: Detect outcome variable type (binary vs. continuous) based on data distribution.
- [~] T014b [US1] Implement `code/preprocess.py`: Implement the logic to switch the regression family (binomial vs. gaussian) or flag for manual review based on T014a's detection, satisfying FR-003.
- [~] T015 [P] [US1] Write `tests/contract/test_data_schema.py` to validate output CSV columns and data types against `data-model.md`.
- [~] T016 [P] [US1] Write `tests/unit/test_data_generation.py` to verify deterministic output given a fixed seed.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Adaptive Mixed-Effects Regression Analysis (Priority: P1)

**Goal**: Fit a Mixed-Effects model (if within-subjects) or Fixed-Effects model (if between-subjects) to test the interaction, automatically detecting data structure and calculating VIF.

**Independent Test**: Run the model on the synthetic dataset with a known interaction effect and verify the estimated coefficient matches the injected parameter within the 95% CI, and that the p-value is correctly calculated against the null.

### Implementation for User Story 2

- [~] T020a [US2] Implement `code/analysis.py`: Validate data structure (between vs within) based on `participant_id` repetition and write the result to `data/processed/structure_config.json` with schema `{"type": "between|within", "n_subjects": int}`.
- [~] T020b [US2] Implement `code/analysis.py`: Consume `family_type` flag from T014b and configure the regression family (Binomial vs Gaussian) for the model.
- [~] T021a [US2] **Must run after T020a**: Implement `code/analysis.py`: Function `fit_mixed_effects` that fits a Mixed-Effects model using `statsmodels` with formula `risk_taking ~ status_level * observed_behavior + (1|participant_id)` IF `structure_config` is 'within-subjects'.
- [~] T021b [US2] **Must run after T020a**: Implement `code/analysis.py`: Function `fit_fixed_effects` that fits a Fixed-Effects model (OLS/GLM) using `statsmodels` with formula `risk_taking ~ status_level * observed_behavior` IF `structure_config` is 'between-subjects'.
- [ ] T021c [US2] **Must run after T014b**: Implement `code/analysis.py`: Logic to select between `fit_mixed_effects` and `fit_fixed_effects` based on `structure_config` and `family_type`, ensuring adaptive behavior per FR-003.
- [ ] T022 [US2] Implement `code/analysis.py`: Calculate Variance Inflation Factors (VIF) for all predictors and flag if > 5.0.
- [ ] T023 [US2] Implement `code/analysis.py`: Extract fixed effects coefficients, standard errors, and p-values for the interaction term.
- [ ] T023b [US2] Implement `code/analysis.py`: Explicitly calculate and report p-values for the interaction term against the null hypothesis (coefficient = 0) to satisfy SC-001 (p < 0.05).
- [ ] T024 [US2] Implement `code/analysis.py`: Add fallback logic to use asymptotic standard errors if bootstrap resampling fails (memory constraints).
- [ ] T025 [P] [US2] Write `tests/contract/test_model_output.py` to validate model output schema (coefficients, p-values, VIF) against `contracts/model_output.schema.yaml`.
- [ ] T026 [P] [US2] Write `tests/unit/test_analysis.py` to verify parameter recovery (estimated vs. injected effect size) and correct family selection.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Reporting (Priority: P2)

**Goal**: Conduct sensitivity analyses on outlier thresholds, perform post-hoc comparisons with Bonferroni correction, and generate reproducible reports with forest plots.

**Independent Test**: Manually alter the outlier threshold in config and verify the report explicitly lists the change in the headline effect size and p-value.

### Implementation for User Story 3

- [ ] T030 [US3] **Must run after T023**: Implement `code/analysis.py`: Sensitivity analysis module to sweep outlier exclusion threshold over a range of standard deviations, explicitly calculating deviations relative to the *cell mean* within each of the experimental conditions (High/Risky, High/Conservative, Low/Risky, Low/Conservative).
- [ ] T031 [US3] Implement `code/analysis.py`: Perform post-hoc pairwise comparisons with Bonferroni correction for all condition combinations, executing this logic UNCONDITIONALLY regardless of the primary interaction significance (per FR-006).
- [ ] T032 [P] [US3] Implement `code/report.py`: Generate forest plot of condition means with 95% Confidence Intervals using `matplotlib/seaborn`.
- [ ] T033 [US3] Implement `code/report.py`: Generate PDF/HTML summary containing model coefficients, VIF table, sensitivity sweep results, and forest plot, saving to `reports/analysis_report.html`.
- [ ] T034 [P] [US3] Write `tests/unit/test_sensitivity.py` to verify that changing the threshold in config updates the sensitivity table.
- [ ] T035 [P] [US3] Write `tests/contract/test_report_schema.py` to validate the generated report structure against `contracts/model_output.schema.yaml`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] Update `quickstart.md` with specific execution steps and dependencies
- [ ] T040b [P] Add comprehensive docstrings to `code/generate_data.py`, `code/analysis.py`, and `code/report.py`
- [ ] T041 Code cleanup and refactoring
- [ ] T042 Performance optimization across all scripts (ensure < 6h runtime)
- [ ] T043 [P] Additional unit tests in `tests/unit/`
- [ ] T044 Run `quickstart.md` validation to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T014 flag, T020a structure)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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
Task: "Contract test for data schema in tests/contract/test_data_schema.py"
Task: "Unit test for data generation in tests/unit/test_data_generation.py"

# Launch all models for User Story 1 together:
Task: "Create data generator in code/generate_data.py"
Task: "Create preprocessor in code/preprocess.py"
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
 - Developer A: User Story 1 (Data Generation/Preprocessing)
 - Developer B: User Story 2 (Analysis/Modeling)
 - Developer C: User Story 3 (Sensitivity/Reporting)
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