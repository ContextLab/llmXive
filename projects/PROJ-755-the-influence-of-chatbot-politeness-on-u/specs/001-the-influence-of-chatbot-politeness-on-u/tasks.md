# Tasks: The Influence of Chatbot Politeness on User-Perceived Quality

**Input**: Design documents from `/specs/001-chatbot-politeness-trust/`
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

- [ ] T001 Create project structure per implementation plan (`data/raw`, `data/processed`, `code`, `tests`, `docs`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (transformers, datasets, statsmodels, pandas, scikit-learn, numpy, pyyaml, tqdm, rpy2, textstat, evalue)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T004 Setup CI workflow (GitHub Actions) to install R-base, R packages (lme4, ordinal), and Python dependencies
- [ ] T005 Create `.gitignore` to exclude `data/raw/*` (except.gitkeep), `data/processed/*`, `__pycache__`, and model caches
- [X] T006 [P] Implement `code/utils/pii_scanner.py` for PII scanning (regex for email, phone, SSN patterns)
- [X] T007 [P] Implement `code/utils/data_integrity.py` for checksumming and data integrity checks
- [ ] T008 [P] Create `contracts/dataset.schema.yaml` defining Dialogue, Utterance, and User entities

**Checkpoint**: Setup ready - Foundational phase can now begin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and validation that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. These tasks verify the data exists and meets schema requirements.

- [ ] T009 [P] Create `contracts/output.schema.yaml` defining CLMM results structure
- [~] T010 [P] Setup environment configuration management (`.env` template for HF_TOKEN if needed)
- [~] T011 [P] [US1] Implement `code/utils/schema_validator.py` to validate dataset schemas against `contracts/dataset.schema.yaml`
- [~] T012 [P] [US1/US3] **VERIFICATION GATE**: Validate presence of `quality_rating`, `user_id`, `age`, and `gender` fields in the merged dataset.
 - *Logic*:
 1. Check `quality_rating` and `user_id`: If missing, **halt pipeline** and log critical error (US-1/US-2 blocked).
 2. Check `age` and `gender`: If missing, **do not halt**. Generate `data/raw/validation_report.json` with `status: partial` and `missing_fields: ['age', 'gender']`. Proceed to US-1 and US-2.
 3. If `age`/`gender` missing, log that US-3 (subgroup analysis) will be skipped per FR-006.
 - *Deliverable*: `data/raw/validation_report.json` (if partial) or `data/raw/validation_report.json` with `status: full`.
 - *Note*: This task MUST run before any download or scoring logic to prevent wasted effort.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Politeness Scoring (Priority: P1) 🎯 MVP

**Goal**: Download **Persona-Chat** and **EmpatheticDialogues** datasets (mandatory per FR-001), filter for completeness, and compute mean politeness scores per conversation using `jfiedler/politeness-bert` on CPU. Use the secondary HCI protocol only if the primary datasets lack required fields.

**Independent Test**: Run `code/01_download_and_score.py` on a sample of dialogues; verify `data/processed/scored_dialogues.parquet` exists with `politeness_score` and `quality_rating` columns, and that excluded dialogues are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [X] T014 [P] [US1] Unit test for politeness scoring logic (batched inference) in `tests/unit/test_scoring.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/01_download_and_score.py` to fetch **Persona-Chat** (HF ID: `lhoestq/personachat`) and **EmpatheticDialogues** (HF ID: `empathetic_dialogues`) as **mandatory primary inputs** per FR-001.
 - *Logic*:
 1. Download Persona-Chat and EmpatheticDialogues first.
 2. Verify presence of `quality_rating`, `user_id`, `dialogue_id`.
 3. If either primary dataset lacks `quality_rating`, attempt to fetch **HCI_P2** as a fallback source.
 4. If all sources lack `quality_rating`, abort with critical error.
 - *Deliverable*: Raw data stored in `data/raw/` with checksums.
- [~] T016 [US1] Implement merging logic to combine all three datasets into a unified DataFrame, preserving `user_id`, `dialogue_id`, `quality_rating`, `age`, `gender`.
- [~] T017 [US1] Implement filtering logic to exclude dialogues missing `quality_rating` or chatbot utterances (log counts).
- [~] T018 [US1] Implement batched inference using `jfiedler/politeness-bert` (CPU-only, `torch.no_grad()`, max_memory management) to score utterances.
 - *Error Handling*: Implement try-except for `ModelLoadingError` and `MemoryError`, log specific error codes, and fallback to `batch_size=1`.
- [~] T019 [US1] Implement aggregation logic to compute `mean_politeness_score` per dialogue and z-score standardization.
- [ ] T020 [US1] Save processed data to `data/processed/scored_dialogues.parquet` and raw logs to `data/raw/exclusions.log`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cumulative Link Mixed-Effects Analysis (Priority: P2)

**Goal**: Fit a CLMM testing the association between politeness and quality ratings, controlling for length and user random effects, with multiple-comparison correction.

**Independent Test**: Run `code/02_fit_clmm.py` on `scored_dialogues.parquet`; verify `data/processed/clmm_results.csv` contains coefficients, p-values, and that convergence warnings are logged if fallback occurs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for VIF calculation and collinearity check in `tests/unit/test_collinearity.py`
- [ ] T022 [P] [US2] Integration test for CLMM execution and result schema validation in `tests/integration/test_clmm.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/02_fit_clmm.py` to load `scored_dialogues.parquet`
- [ ] T024 [US2] Implement VIF check for `politeness` and `conversation_length`; log warning and drop variable if VIF ≥ 5.
- [ ] T025 [US2] Implement CLMM fitting via `rpy2` (formula: `quality_rating ~ politeness + conversation_length + (1|user_id)`) with `lme4`.
- [ ] T026 [US2] **Convergence Tracking & Fallback**: Calculate and log the **CLMM convergence rate** (number of converged models / total attempts).
 - *Success Condition*: If convergence ≥ 95%, proceed.
 - *Failure Condition*: If convergence < 95%, **generate `data/processed/convergence_failure_report.csv`** detailing the failure, **halt** the primary CLMM path, and **trigger fallback** to fixed-effects ordinal regression (log diagnostic).
 - *Note*: Fallback models do not count as "converged CLMM" for SC-003; the report documents the deviation.
- [ ] T027 [US2] Implement Benjamini-Hochberg correction for p-values across fixed effects.
- [ ] T028 [US2] Save results to `data/processed/clmm_results.csv` with coefficients, SEs, p-values, CI, and convergence metrics.
- [ ] T029 [US2] Implement sensitivity analysis sweep (p < 0.01, 0.05, 0.10) and **explicitly report the range of variation** in headline significance rates across these thresholds.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Subgroup Analysis (Priority: P3)

**Goal**: Validate findings with an **open-source lexicon-based classifier** (`textstat`/`politeness` per Plan Phase 0 Step 4) and conduct subgroup analyses by age/gender (n ≥ 30 guard).

**Independent Test**: Run `code/03_robustness_analysis.py`; verify `data/processed/robustness_results.csv` exists, correlation (r ≥ 0.80) is calculated, and subgroup exclusions are logged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for lexicon-based scoring logic in `tests/unit/test_lexicon_scoring.py`
- [ ] T031 [P] [US3] Integration test for subgroup filtering logic (n ≥ 30) in `tests/integration/test_subgroup.py`

### Implementation for User Story 3

- [ ] T032 [US3] **Robustness Classifier**: Implement `code/03_robustness_analysis.py` to re-score dialogues using **`textstat` (Bing/Afinn)** or **`politeness` package** as the primary alternative classifier, adhering to FR-005 and Plan constraints.
 - *Logic*: Use `textstat` as the primary fallback; log if proprietary LIWC-2015 was requested but unavailable.
 - *Dependency*: Requires T012 (Demographic Verification) to have passed (or reported partial status).
- [ ] T033 [US3] Re-fit CLMM on lexicon scores and compute **Pearson correlation of per-dialogue predicted quality scores** between the primary model and the robustness model.
 - *Metric*: Calculate `correlation_r` between `primary_model.predicted_quality` and `robust_model.predicted_quality`.
 - *Output*: Save `correlation_r` to `data/processed/robustness_results.csv` column `correlation_r`.
 - *Target*: Verify r ≥ 0.80 per SC-004.
- [ ] T034 [US3] **Subgroup Analysis**: Split data by age/gender.
 - *Dependency*: Requires T012 (Demographic Verification) to have reported `status: full` or `partial` with available fields.
 - *Logic*: Exclude groups with n < 30, log exclusions. Fit separate CLMMs for valid subgroups and test interaction terms.
- [ ] T035 [US3] Apply multiplicity correction for subgroup tests.
- [ ] T036 [US3] Calculate E-values for robustness to unmeasured confounding (implement VanderWeele formula or use EValue R package logic via rpy2).
- [ ] T037 [US3] Save all robustness results to `data/processed/robustness_results.csv`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` (README, quickstart.md, data-model.md)
- [ ] T039 Code cleanup and refactoring (remove debug prints, ensure type hints)
- [ ] T040 Performance optimization: verify memory usage < 7GB during peak BERT inference
- [ ] T041 [P] Additional unit tests for edge cases (empty dialogues, NaN handling) in `tests/unit/`
- [ ] T042 Run `quickstart.md` validation to ensure full pipeline executes on CI within 6 hours

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS** all user stories. Includes T012 (Demographic Verification) which gates US3.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (`scored_dialogues.parquet`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US1 and US2 for comparison. **Explicitly depends on T012 passing (or partial status with available fields).**

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
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Unit test for politeness scoring logic in tests/unit/test_scoring.py"

# Launch all models for User Story 1 together:
Task: "Implement code/01_download_and_score.py to fetch Persona-Chat and EmpatheticDialogues"
Task: "Implement filtering logic to exclude dialogues missing quality_rating"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes T012 verification)
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
 - Developer C: User Story 3 (Only if T012 passes or partial status available)
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
- **Constraint**: All BERT inference must be CPU-only (no CUDA); use batch processing to stay under available RAM limits.
- **Constraint**: Dataset source MUST include Persona-Chat and EmpatheticDialogues as per FR-001.
- **Constraint**: Subgroup analysis (US3) is strictly gated by T012 (Demographic Verification).