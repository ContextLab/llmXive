# Tasks: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

**Input**: Design documents from `/specs/001-social-rejection-reward/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are REQUIRED for all User Stories to ensure validation logic is correct.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/raw/`, `data/interim/`, `data/processed/`, `tests/`)
- [X] T002 Initialize Python 3.11 project with `pandas`, `numpy`, `scipy`, `statsmodels`, `pyyaml`, `requests` in `code/requirements.txt`
- [ ] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` to manage paths, random seeds, and α thresholds ({0.01, 0.05, 0.1})
- [X] T005 [P] Implement `code/__init__.py` and basic logging infrastructure for memory usage tracking
- [X] T006 Create `code/data_model.py` defining `Dataset`, `PreprocessedRecord`, and `AnalysisResult` entities with `design_type` field

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Design Determination (Priority: P1) 🎯 MVP

**Goal**: Download and validate datasets. The system MUST first attempt to find a **Single-Cohort** dataset (both tasks in one file). If found, proceed with Mixed ANOVA. If NOT found (e.g., ds000208 lacks reward task), the system MUST proceed to a **Composite Dataset Strategy** (matching IDs across ds000208 and ds003392) to enable a Between-Subjects ANOVA. **Merging is forbidden for Within-Subjects, but required for Between-Subjects fallback.**

**Independent Test**: Execute ingestion script against a mock single-cohort file (pass) and a mock composite set (pass with design_type=Between-Subjects). Verify script halts with exit code 1 only if NO valid data source exists.

### Tests for User Story 1 (REQUIRED) ⚠️

- [ ] T010 [P] [US1] Contract test in `tests/test_ingest.py::test_schema_validates_single_cohort` to assert `exit_code == 0` when single-cohort data is found
- [ ] T011 [P] [US1] Integration test in `tests/test_ingest.py::test_download_and_validate_composite` to verify successful ingestion and design switching when single-cohort is missing

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/ingest.py` with `download_dataset(url)` function. **MUST include logic to verify the dataset contains BOTH Cyberball and Reward tasks.** If single-cohort found, set `design_type="Within-Subjects"`. If not, **DO NOT halt**; instead, flag for composite validation.
- [ ] T016 [US1] **Immediately after download**, generate `data/raw/checksums.json` to preserve raw data integrity (Constitution Principle III). This MUST occur before any validation logic.
- [X] T015 [US1] Add memory guard in `code/ingest.py` to monitor **runtime RAM usage** using `psutil`. **Halt execution with exit code if the process memory footprint exceeds a predefined threshold.**, explicitly distinguishing this from raw file size on disk (FR-001, Plan Clarification). This check must occur *before* full data loading.
- [X] T013 [US1] Implement `validate_schema(df)` in `code/ingest.py` to check for `Condition` (Cyberball), `Condition` (Reward), `Reaction Time`, `Mood`. **Exit code 1 if required variables are missing AND no fallback dataset is available.**
- [X] T014 [US1] Implement `verify_single_cohort(df)` in `code/ingest.py` to ensure Participant IDs are consistent within the SINGLE dataset. If consistent, set `design_type="Within-Subjects"`. If inconsistent or missing, proceed to T017.
- [X] T017 [US1] Implement `validate_composite_datasets(df_rejection, df_reward)` in `code/ingest.py`. **MUST match Participant IDs across distinct datasets (ds000208 vs ds003392).** If matching IDs exist, set `design_type="Between-Subjects"`. If no matching IDs, halt with "Data Unavailable" (exit code 1).
- [X] T019 [US1] Implement `log_design_switch()` in `code/ingest.py` to explicitly record the transition from "Single-Cohort attempt" to "Composite Fallback" in the execution log, ensuring traceability for the "associational" framing.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. The pipeline must support both Within-Subjects (if found) and Between-Subjects (fallback) paths.

---

## Phase 4: User Story 2 - Preprocessing and Feature Extraction (Priority: P2)

**Goal**: Clean behavioral data, normalize reaction times, extract summary features (mean RT, avg mood), and remove outliers using IQR per Condition group.

**Independent Test**: Run preprocessing on sample subset; verify output CSV structure, memory logs ≤ 7 GB, and correct IQR outlier flagging.

### Tests for User Story 2 (REQUIRED) ⚠️

- [X] T018 [P] [US2] Contract test in `tests/test_preprocess.py::test_outlier_detection_iqr` to assert correct flagging per Condition group
- [X] T019 [P] [US2] Integration test in `tests/test_preprocess.py::test_memory_usage_under_limit` to verify memory stays ≤ 7 GB

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/preprocess.py` with `clean_data(df)` function
- [X] T021 [US2] Implement `normalize_rt(df)` in `code/preprocess.py` to standardize reaction times <!-- SKIPPED: non-mapping output -->
- [X] T022 [US2] Implement `detect_outliers_iqr(df, group_col='Condition')` in `code/preprocess.py` to flag/cap outliers using a standard interquartile range multiplier per group (FR-002)
- [X] T023 [US2] Implement `extract_features(df)` in `code/preprocess.py` to compute `mean_rt` and `avg_mood` per participant/condition
- [X] T024 [US2] Save intermediate data to `data/interim/preprocessed_data.csv` with `design_type` tag

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Execute ANOVA (Mixed for single-cohort; One-Way for composite), apply FDR, generate sensitivity analysis, and export report. **If the design is Between-Subjects, explicitly drop the "modulation" claim and frame results as "associational group differences".**

**Independent Test**: Run analysis on preprocessed data; verify output report contains p-values, effect sizes, sensitivity tables, and correct test selection logic.

### Tests for User Story 3 (REQUIRED) ⚠️

- [ ] T025 [P] [US3] Contract test in `tests/test_analysis.py::test_anova_selection_logic` to assert correct ANOVA type selection
- [ ] T026 [P] [US3] Integration test in `tests/test_analysis.py::test_fdr_and_sensitivity` to verify FDR correction and sensitivity sweep

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/analysis.py` with `run_anova(df, design_type)` to select Mixed ANOVA (Within) or One-Way ANOVA (Between). **If design_type is Between-Subjects, explicitly drop the "modulation" claim and flag the inability to test it.**
- [ ] T028 [US3] Implement `apply_fdr(p_values)` in `code/analysis.py` using Benjamini-Hochberg method (FR-004)
- [ ] T029 [US3] Implement `sensitivity_sweep(df, alpha_set={0.01, 0.05, 0.1})` in `code/analysis.py` (FR-006)
- [ ] T030 [US3] Implement `generate_report_logic(results, design_type)` in `code/report.py`. **MUST enforce "associational" phrasing in Limitations when design_type is Between-Subjects.**
- [ ] T031 [US3] Add convergence warning logic for small N (N < 30) and report effect size confidence intervals
- [ ] T033 [US3] Implement `save_final_results(results, design_type)` in `code/report.py` to write `data/processed/final_results.json` ensuring the `p_fdr` column is present (SC-003) and `design_type` is recorded (FR-008).
- [ ] T034 [US3] Implement `verify_report_constraints()` in `tests/test_report.py` to assert that `reports/final_report.md` contains the exact phrase "associational" in Limitations and excludes "causal" in Results (FR-003).
- [ ] T032 [US3] Save final results to `data/processed/final_results.json` and `reports/final_report.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `README.md`
- [ ] T036 Code cleanup and refactoring in `code/`
- [ ] T037 Performance optimization to ensure total runtime ≤ 6 hours for N ≤ 500
- [ ] T038 [P] Additional unit tests in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data ingestion
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 preprocessed data

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
Task: "Contract test in tests/test_ingest.py::test_schema_validates_single_cohort"
Task: "Integration test in tests/test_ingest.py::test_download_and_validate_composite"

# Launch all models for User Story 1 together:
Task: "Implement code/ingest.py with download_dataset(url) function (verify single-cohort OR composite)"
Task: "Generate data/raw/checksums.json immediately after download"
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
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: The pipeline must support both Single-Cohort (Within-Subjects) and Composite (Between-Subjects) paths. Merging distinct studies is forbidden for Within-Subjects but required for the Between-Subjects fallback.