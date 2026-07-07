# Tasks: The Relationship Between Personality Traits and Response to Personalized AI Feedback

**Input**: Design documents from `/specs/001-personality-ai-feedback/`
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

- [ ] T001 [P] Create directory structure at repository root: `projects/PROJ-292-the-relationship-between-personality-tra/{code,data,results}` with subdirectories `data/raw`, `data/processed`, `results/plots`, `results/stats`
- [ ] T002 [P] Create `code/__init__.py`, `data/.gitkeep`, `results/.gitkeep`
- [ ] T003 [P] Initialize `requirements.txt` with pinned dependencies: `pandas`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `pytest`, `pyyaml`, `requests`, `numpy`, `openml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement utility module `code/utils.py` containing: (1) deterministic seeding function (`set_seed(seed)`), (2) checksum generation function (`generate_sha256(filepath)`), and (3) error handling wrapper for dataset fetches (`fetch_with_retry(url, max_retries=3)`).
- [ ] T005 [P] Create base configuration loader `code/config.py` to load environment variables and default seeds.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Validation (Priority: P1) 🎯 MVP

**Prerequisites**: `data-model.md` must be finalized before writing contract tests.

**Goal**: Attempt to download public datasets (IPIP-50 + AI feedback response) from OpenML; if the specific 'feedback' columns are missing (as expected), generate synthetic data with explicit 'Simulation-Based' flags, merge them, and validate sample size.

**Independent Test**: The pipeline runs end-to-end, attempting the download, detecting missing schema, generating synthetic data if needed, merging by ID, and outputting `data/processed/analysis_data.csv` with valid columns and N ≥ 50. The output metadata must explicitly flag if synthetic data was used.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/data_ingestion.py` to: (1) Fetch 'Big Five Personality Traits' from OpenML (real), (2) Attempt to fetch 'Human Feedback Response' data from OpenML; (3) If 'feedback' columns (receptivity, anxiety, intention) are missing, generate synthetic data with schema `participant_id`, `receptivity_score`, `anxiety_level`, `behavioral_intention`, and write to `data/raw/synthetic_responses.csv` with a metadata flag `source: synthetic`; (4) Write real personality data to `data/raw/iPIP50.csv`.
- [ ] T012 [US1] Implement merge logic in `code/data_ingestion.py` to align `data/raw/iPIP50.csv` and `data/raw/synthetic_responses.csv` (or real feedback if found) by `participant_id`, handling missing values via mean imputation or excluding rows where missingness > 10%, outputting `data/processed/analysis_data.csv`.
- [ ] T013 [US1] Implement validation logic in `code/data_ingestion.py` to explicitly validate `data/processed/analysis_data.csv`: check sample size N ≥ 50; if N < 50, exit with code 1 and write a detailed warning message including the count to `data/validation_log.txt`.
- [ ] T014 [US1] Implement checksum generation for `data/raw/*.csv` and `data/processed/analysis_data.csv` using SHA-256, writing results to `data/checksums.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Correlation Computation (Priority: P2)

**Goal**: Compute correlation matrices, multiple regression, and apply Benjamini-Hochberg correction to determine relationships between traits and feedback responses.

**Independent Test**: The analysis script processes `analysis_data.csv` and outputs `results/stats/stats.json` with correlations, p-values, regression coefficients, and BH-corrected significance flags.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Contract test for statistical output schema in `tests/contract/test_stats_schema.py`
- [ ] T017 [P] [US2] Unit test for Benjamini-Hochberg implementation in `tests/unit/test_bh_correction.py`

### Implementation for User Story 2

- [ ] T018 [US2] Implement Pearson correlation computation for all traits vs multiple outcomes (multiple pairs) in `code/analysis.py`, outputting coefficients and p-values.
- [ ] T019 [US2] Enumerate the full set of hypothesis tests across the traits and outcomes and write to `results/stats/test_set_definition.json` as a JSON list of pairs before correction.
- [ ] T020 [US2] Implement Benjamini-Hochberg correction in `code/analysis.py` using the set defined in T019, outputting adjusted p-values.
- [ ] T021 [US2] Implement calculation of Pearson correlation coefficient (r) effect sizes for all pairs of variables under investigation and write to `results/stats/correlation_effects.json`.
- [ ] T022 [US2] Implement multiple linear regression with interaction terms for feedback type in `code/analysis.py`, calculating R² for all models.
- [ ] T023 [US2] Write statistical results (correlations, regression coefficients, R², BH-corrected p-values) to `results/stats/stats.json` with full metadata including `source_type: synthetic` if applicable.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-quality visualizations (heatmaps, regression plots) and a final summary report with sensitivity analysis.

**Independent Test**: The reporting script consumes `results/stats/stats.json` and generates `results/report.md` with multiple plots and a sensitivity table.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for report content in `tests/contract/test_report_schema.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement correlation heatmap generation with significance stars in `code/visualization.py` using `results/stats/stats.json`.
- [ ] T026 [US3] Implement scatter plot with regression line for strongest predictor-outcome pair in `code/visualization.py`.
- [ ] T027 [US3] Implement sensitivity analysis table for alpha across representative significance levels in `code/report.py`.
- [ ] T028 [US3] Implement Markdown/PDF report generation including all plots and tables to `results/report.md` and `results/report.pdf`.
- [ ] T029 [US3] Ensure all plots have clear axis labels, legends, and no GPU acceleration in `code/visualization.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T031 [P] Run `quickstart.md` validation to ensure full pipeline execution
- [ ] T032 [P] Update `research.md` to explicitly state the distinction between the static correlational study and the data source reality (synthetic vs real).
- [ ] T039 [P] Implement Drift Analysis report generation in `code/report.py` to output a dedicated file `results/drift_analysis.md` containing a section header "## Drift Analysis" with stability metrics (specifically coefficient stability across bootstrap resamples), ensuring the output is verifiable at the specified path.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 results output

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
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"

# Launch all models for User Story 1 together:
Task: "Implement data_ingestion.py to fetch/generate data..."
Task: "Implement merge logic..."
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
- **CRITICAL**: All data generation tasks MUST use real or explicitly labeled synthetic data; never fabricate results. The "Simulation-Based" label must be prominent in all reports derived from synthetic data.
- **Scope Note**: This project is strictly a "Simulation-Based" study on synthetic data (fallback) to validate the pipeline. No empirical claims about human-AI interaction are made.
- **Data Reality**: The pipeline attempts to fetch real OpenML data for personality traits. If the required 'feedback' columns are missing (as expected), it generates synthetic data and explicitly flags the result.