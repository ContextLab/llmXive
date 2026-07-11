# Tasks: The Impact of Visual Attention Allocation on Recall of Emotionally Valenced Stories

**Input**: Design documents from `/specs/001-visual-attention-recall/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

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
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `output/`, `tests/`). **Verification**: `tree code/` matches plan.md structure. **Add**: Create `scripts/run_pipeline.sh` which checks if `data/processed/validation_status.txt` contains "HALT" before running Phase 4/5.
- [X] T002 Initialize Python 3.11 project with `pandas`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml` dependencies in `requirements.txt`. **Verification**: `pip install -r requirements.txt` returns 0.
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools in `pyproject.toml`. **Verification**: `black --check code/` returns 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup random seed configuration and global logging in `code/utils/config.py` and `code/utils/logger.py`. **Deliverable**: `config.py` exports `RANDOM_SEED=42`.
- [X] T005 [P] Create base directory structure for `data/raw/`, `data/processed/`, `data/eye-tracking/`, `data/valence/`, `output/plots/`, `output/results/`. **Verification**: `ls -R data/` shows all dirs.
- [X] T006 [P] Implement data checksumming utility in `code/utils/data_integrity.py` (Constitution III). **Deliverable**: Function `compute_checksum(file_path)` returns MD5 hash.
- [X] T007 Create data model classes for `EyeTrackingRecord`, `RecallScore`, `AnalysisResult` in `code/models/data_models.py`. **Deliverable**: Pydantic models with validated fields.
- [X] T008 Setup environment variable management for paths and thresholds in `code/utils/config.py`. **Deliverable**: `config.py` loads `.env` for `DATA_PATH`, `OUTPUT_PATH`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Variable Validation (Priority: P1) 🎯 MVP

**Goal**: Load public eye-tracking datasets and validate required variables and data quality metrics before analysis.

**Independent Test**: Can be fully tested by running the ingestion script against a sample dataset file and verifying the output log confirms all required columns exist AND data quality metrics pass.

**TDD Workflow Note**: Write tests (T018-T019) FIRST, ensure they FAIL, then implement (T012-T017).

### Implementation for User Story 1

- [X] T012 [P] [US1] Create `load_data.py` in `code/ingestion/` to load CSV/EDF files without GPU (FR-001). **Deliverable**: Script loads data, returns DataFrame. **Exit**: 0 on success, 1 on file not found.
- [X] T013 [US1] Implement `validate_data.py` in `code/ingestion/` to check for fixation duration, saccade amplitude, **gaze distribution**, **recall accuracy**, valence label (FR-002). **Deliverable**: Validates column existence, logs missing columns.
- [ ] T014 [US1] Add data quality checks for ≤5% track loss and calibrated eye-tracker status in `code/ingestion/validate_data.py` (Constitution VI). **Deliverable**: Writes `data/eye-tracking/quality_report.md`. **Action**: **HALT** (exit 1) if track loss > 5% or uncalibrated.
- [ ] T015 [US1] Implement valence annotation validation for standardized rating scale and storage in `data/valence/` in `code/ingestion/validate_data.py` (Constitution VII). **Constraint**: Use human-rated metadata only; if unavailable, halt with `DATA_BLOCKER` per `plan.md`. **Deliverable**: Writes `valence_categories_count` to `data/eye-tracking/quality_report.md`.
- [ ] T016 [US1] Add logic to halt processing and log error if dataset is incompatible (missing variables). **Deliverable**: Exit code 1, log `DATA_BLOCKER: Missing required variables`.
- [ ] T017 [US1] Add logging for data ingestion success rate and quality metrics (SC-001). **Deliverable**: If count of available public datasets == 0, log `DATA_BLOCKER: No verified datasets found` and exit 1. Do NOT calculate percentage. If count > 0, log `Ingestion Success Rate: X%`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [P] [US1] Contract test for schema validation in `tests/contract/test_data_schema.py::test_schema_validates_required_columns`.
- [~] T019 [P] [US1] Integration test for data loading failure on missing columns in `tests/integration/test_ingestion_failures.py::test_missing_columns_halts`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. **Note: If no verified dataset exists, this task will halt execution as per plan.md.**

---

## Phase 4: User Story 2 - Statistical Analysis and Association Modeling (Priority: P2)

**ORCHESTRATION GUARD**: These tasks are **CONDITIONAL**. If Phase 3 (US1) halts with `DATA_BLOCKER`, **DO NOT RUN** these tasks. The pipeline script `scripts/run_pipeline.sh` must check for this condition and skip Phase 4.

**Goal**: Compute Linear Mixed-Effects Models (LMM) between attentional metrics and recall accuracy, applying multiple-comparison corrections.

**⚠️ CONDITIONAL EXECUTION**: These tasks are **SKIPPED** if Phase 3 (US1) reports a data blocker (exit code 1).

**Independent Test**: Can be fully tested by running the analysis module on pre-processed data and verifying the output includes LMM coefficients with corrected p-values.

### Implementation for User Story 2

- [~] T020 [P] [US2] **CONDITIONAL: SKIP IF US1 HALTS** Create `lmm_model.py` in `code/analysis/` to compute LMM using `statsmodels` mixedlm (FR-003). **Deliverable**: `output/results/lmm_summary.csv` with columns `metric`, `valence`, `coef`, `p_raw`.
- [~] T021 [US2] **CONDITIONAL: SKIP IF US1 HALTS** Implement logic to model attention metrics vs. recall accuracy for each valence category (multiple metrics × multiple categories). **Deliverable**: Loop over combinations, store results.
- [~] T022 [US2] **CONDITIONAL: SKIP IF US1 HALTS** Create `correction.py` in `code/analysis/` to apply Bonferroni correction across all 9 metric-category combinations (FR-004). **Deliverable**: `output/results/correction_results.json` with `p_corrected`.
- [~] T023 [US2] **CONDITIONAL: SKIP IF US1 HALTS** Implement sensitivity analysis in `code/analysis/sensitivity.py` to sweep p-values across {0.01, 0.05, 0.1} and report rate variations (FR-006). **Deliverable**: `output/results/sensitivity_analysis.json`. **Note**: Do NOT use learning rates; this is a statistical threshold sweep.
- [~] T024 [US2] **CONDITIONAL: SKIP IF US1 HALTS** Add explicit "associational" labeling to all output results to prohibit causal language (FR-005). **Deliverable**: Append `association_label: "associational"` to all result objects.
- [~] T025 [US2] **CONDITIONAL: SKIP IF US1 HALTS** Add error handling for missing recall scores per participant-passages (Edge Case). **Deliverable**: Log warning, skip missing rows, continue.
- [~] T026 [US2] **CONDITIONAL: SKIP IF US1 HALTS** Implement memory-efficient data loading (chunking/sampling) to ensure <7 GB RAM usage (SC-004). **Deliverable**: Use `pd.read_csv(chunksize=...)` or `sample(n=...)`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T032 [P] [US2] Contract test for LMM output schema in `tests/contract/test_lmm_output.py::test_lmm_output_schema`.
- [~] T033 [P] [US2] Integration test for associational labeling in `tests/integration/test_associational_labeling.py::test_associational_labeling_present`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (provided valid data exists).

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**ORCHESTRATION GUARD**: These tasks are **CONDITIONAL**. If Phase 3 (US1) halts or Phase 4 (US2) fails, **DO NOT RUN** these tasks.

**Goal**: Generate visualizations of attentional metric distributions by valence, scatter plots, and a summary report.

**⚠️ DEPENDENCY**: Requires Phase 4 (US2) completion and valid results.

**Independent Test**: Can be fully tested by checking that plot files are generated in the output directory and contain labeled axes matching the defined metrics.

### Implementation for User Story 3

- [~] T039 [P] [US3] **CONDITIONAL: SKIP IF US1/US2 HALT** Create `visualize.py` in `code/reporting/` using `matplotlib`/`seaborn`. **Deliverable**: Script generates plots.
- [~] T040 [US3] **CONDITIONAL: SKIP IF US1/US2 HALT** Implement scatter plots of Attention Metric vs. Recall Accuracy for each valence category (FR-007). **Deliverable**: `output/plots/scatter_{valence}.png` for each valence.
- [~] T041 [US3] **CONDITIONAL: SKIP IF US1/US2 HALT** Implement distribution histograms for each attention metric by valence category (FR-007). **Deliverable**: `output/plots/hist_{metric}_{valence}.png`.
- [~] T042 [US3] **CONDITIONAL: SKIP IF US1/US2 HALT** Ensure all plots have labeled axes and are saved to `output/plots/` (SC-005). **Deliverable**: Axes labeled "Attention Metric", "Recall Accuracy".
- [~] T043 [US3] **CONDITIONAL: SKIP IF US1/US2 HALT** Create `generate_report.py` in `code/reporting/` to compile LMM coefficients, corrected p-values, and associational disclaimer (FR-005). **Deliverable**: `output/results/final_report.md`.
- [~] T044 [US3] **CONDITIONAL: SKIP IF US1/US2 HALT** Add logic to verify plot completeness. **Deliverable**: Read `valence_categories_count` from `data/eye-tracking/quality_report.md` (generated by T015) to determine `expected_count`. Assert `len(glob('output/plots/*.png')) >= expected_count * 2`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T034 [P] [US3] Contract test for plot file existence and labels in `tests/contract/test_visualization.py::test_plot_files_exist_and_labeled`.
- [~] T035 [P] [US3] Integration test for report generation completeness in `tests/integration/test_report.py::test_report_completeness`.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T045 [P] Documentation updates in `docs/` including data acquisition limitations.
- [~] T046 Code cleanup and refactoring for memory efficiency.
- [~] T047 Performance optimization to ensure total pipeline <6h runtime (FR-008).
- [~] T048 [P] Additional unit tests for edge cases (missing data, sensitivity analysis stability) in `tests/unit/`. <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
  in "<unicode string>", line 2, column 13:
        contents: |
                ^) -->
- [ ] T049 Run `quickstart.md` validation and verify data gap documentation.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (Phase 3)**: Can start after Foundational. **CRITICAL**: If data validation fails, US2 and US3 cannot execute.
 - **User Story 2 (Phase 4)**: **CONDITIONAL** on Phase 3 success. If Phase 3 halts, Phase 4 is SKIPPED.
 - **User Story 3 (Phase 5)**: **DEPENDENT** on Phase 4 success. Requires valid results from US2.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

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
Task: "Contract test for schema validation in tests/contract/test_data_schema.py::test_schema_validates_required_columns"
Task: "Integration test for data loading failure on missing columns in tests/integration/test_ingestion_failures.py::test_missing_columns_halts"

# Launch all models for User Story 1 together:
Task: "Create load_data.py in code/ingestion/"
Task: "Create validate_data.py in code/ingestion/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently. **Verify if a verified dataset exists.**
5. If no dataset: Document blocker and halt. If dataset exists: Proceed to US2.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **Validate Data Availability** → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Ingestion & Validation)
 - Developer B: User Story 2 (Statistical Analysis) - *Can prepare code but may wait on data*
 - Developer C: User Story 3 (Visualization) - *Can prepare code but may wait on results*
3. Stories complete and integrate independently once data is confirmed.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- **STOP** if `validate_data.py` reports missing variables (per plan.md "HALT with documented data gap").
- **ORCHESTRATION**: Phase 4 and Phase 5 are **SKIPPED** if Phase 3 fails. Use `scripts/run_pipeline.sh` to enforce this.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.
- **Data Constraint**: All tasks assume CPU-only execution. No GPU/CUDA, no 8-bit quantization, no deep learning. Use `statsmodels` LMM.
- **Data Integrity**: No synthetic or fake data is permitted. All analysis must use real data from verified sources. If no verified source exists, the pipeline halts.