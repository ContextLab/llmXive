# Tasks: The Effect of Priming on Prosocial Behavior in Online Communities

**Input**: Design documents from `/specs/001-the-effect-of-priming-on-prosocial-behav/`
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, numpy, nltk, vaderSentiment, statsmodels, scikit-learn, pyyaml, hashlib, datasets)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create data directory structure: `data/raw/`, `data/processed/`, `data/validation/`, `results/`
- [X] T005 [P] Implement data checksumming utility in `code/utils/checksum.py` to verify raw data integrity
- [X] T006 Create schema validation utilities in `code/utils/schema_validator.py` for `dataset.schema.yaml`, `scored.schema.yaml`, and `output.schema.yaml`
- [X] T007 [P] Configure environment variable management for `TARGET_N` and data source paths in `code/config.py`
- [X] T008 Implement logging infrastructure in `code/utils/logger.py` to capture "Negation Exclusions" and abort conditions
- [X] T009 [P] Setup pytest configuration and test directory structure (`tests/unit/`, `tests/integration/`, `tests/contract/`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Classification, and Anonymization (Priority: P1) 🎯 MVP

**Goal**: Retrieve, filter, classify, and anonymize Reddit comments to establish the independent variable (thread type) and ensure PII compliance.

**Independent Test**: Execute `code/01_ingest.py` against a small, known test subset and verify the output DataFrame contains exactly two distinct groups ("Prime", "Control") with at least 4,000 comments each (or aborts correctly), and that no plaintext usernames or timestamps exist in the output.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [ ] T011 [P] [US1] Unit test for negation-aware keyword classification logic in `tests/unit/test_classification.py`
- [ ] T012 [P] [US1] Unit test for PII anonymization (SHA-256 hash ing) in `tests/unit/test_anonymization.py`

### Implementation for User Story 1

- [~] T013 [US1] **PRE-COLLECTION POWER ANALYSIS**: Implement `code/00_power_analysis.py` to perform pre-data-collection power analysis (FR-013) assuming d=0.15, α=0.05. **Logic**: Check for existing pilot data; if present, use actual ICC to calculate power; if absent, use a conservative theoretical ICC estimate with a **mandatory log entry citing the specific prior study or theoretical justification** for this value. If power < 80%, the script MUST abort and log a requirement for **researcher approval** before proceeding. This task MUST run BEFORE T014. **CRITICAL**: This is a pre-fetch gate; if it fails, no data fetching occurs.
- [~] T014 [US1] Implement `code/01_ingest.py`: Source verification for `pushshift/reddit` (FR-014) and presence check for multiple target subreddits (r/AskReddit, r/relationships, r/socialscience, r/psychology, r/dataisbeautiful). **Dependency**: Must wait for T013 success.
- [~] T015 [US1] Implement `code/01_ingest.py`: Data fetching logic with `TARGET_N = 10,000` limit and abort logic if dataset exhausted or group counts < 4,000 (FR-001, FR-001a). **Dependency**: Must wait for T014 success.
- [~] T016 [US1] Implement `code/01_ingest.py`: Classification logic using NLTK `word_tokenize` and -token negation window (FR-002, FR-002a); log "Negation Exclusions".
- [~] T015b [US1] **Feasibility Check for Optional Feature**: Check CPU feasibility for FR-002c (confidence score). If a lightweight lexical confidence model can be run within time limits, implement logic; otherwise, explicitly defer this feature in code comments and log "FR-002c Deferred". This task does not implement the full feature, only determines feasibility.
- [~] T016a [US1] Implement `code/01_ingest.py`: Anonymization logic (SHA hash of username). **CRITICAL**: The SHA-256 hash MUST be **retained and explicitly mapped as the `user_id` column** for downstream LMM random effects (FR-009, SC-009). Strip raw timestamps only after computing `thread_age` (FR-009).
- [ ] T017 [US1] Implement `code/01_ingest.py`: Save `data/processed/anonymized.csv` and `data/processed/raw_counts.json`.
- [ ] T018 [US1] Implement `code/01_ingest.py`: Post-fetch validation to ensure at least 4,000 comments per group and ≥3 subreddits remain; abort if conditions not met (FR-001, Edge Cases).
- [ ] T019 [US1] Create `tests/integration/test_ingest_pipeline.py` to verify end-to-end data flow and abort conditions

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Prosocial Action Scoring and Validation (Priority: P2)

**Goal**: Compute prosocial action counts and VADER scores, and validate the measurement against human annotations.

**Independent Test**: Run `code/02_score.py` on the anonymized dataset and verify `data/processed/scored.csv` contains `prosocial_action_count` and `neg_score` columns, and that `results/validation_report.json` confirms Cohen's Kappa ≥ 0.7 against `data/validation/gold_standard.csv`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for `prosocial_action_count` lexicon logic (excluding prime keywords) in `tests/unit/test_lexicon.py`
- [ ] T021 [P] [US2] Unit test for VADER `neg_score` extraction and range validation in `tests/unit/test_vader.py`
- [ ] T022 [P] [US2] Unit test for stratified sampling logic (FR-010, FR-010a) in `tests/unit/test_sampling.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/02_score.py`: VADER sentiment scoring and `neg_score` extraction for all comments (FR-003, SC-008)
- [ ] T024 [US2] Implement `code/02_score.py`: `prosocial_action_count` computation using secondary lexicon (FR-003b), excluding "help", "support", "charity" and equivalents
- [ ] T025 [US2] Implement `code/02_score.py`: Stratified sampling logic for validation (FR-010, FR-010a) to ensure ≥200 comments with ≥50 per stratum. **Logic**: Implement thematic categories (Social Science: r/socialscience, r/psychology; General: all others). If a stratum is insufficient, merge within category, then merge across thread_type, then draw from global pool.
- [ ] T026a [US2] Create `code/validation/protocol.md` defining "prosocial action" and "negative sentiment" for human raters (FR-011). This task generates the instructions only.
- [ ] T026b [US2] **EXTERNAL FILE VERIFICATION**: Implement `code/validation/run_validation.py` to **accept an externally supplied** `gold_standard.csv`. Verify the file contains annotations from **≥3 distinct raters** (validated via `rater_id` column). **Abort** if the file does not meet this criterion (FR-011a). This task does not recruit raters; it verifies the external artifact.
- [ ] T027 [US2] Implement `code/validation/run_validation.py`: Logic to load `gold_standard.csv`, compute Cohen's Kappa (SC-006) and Pearson r for `neg_score` (SC-008). **ABORT LOGIC**: If Cohen's Kappa < 0.7, the script MUST abort the pipeline and log insufficiency per SC-006.
- [ ] T028 [US2] Implement `code/02_score.py`: Performance monitoring to ensure runtime ≤ 4 hours on CPU (FR-012)
- [ ] T029 [US2] Save `data/processed/scored.csv` and `results/validation_report.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform LMM analysis, sensitivity checks, and generate visualizations to answer the research question.

**Independent Test**: Execute `code/03_analyze.py` on the scored dataset and verify `results/stats_report.json` contains p-values, coefficients, CIs, sensitivity results, and `results/boxplot.png` exists.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for LMM formula construction and singular fit detection in `tests/unit/test_lmm.py`
- [ ] T031 [P] [US3] Unit test for sensitivity analysis bootstrap logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement `code/03_analyze.py`: Load `data/processed/scored.csv` and prepare data for LMM
- [ ] T033 [US3] Implement `code/03_analyze.py`: Fit Linear Mixed-Effects Model (LMM) with formula `prosocial_action_count ~ thread_type + thread_age + comment_count + (1|thread_id) + (1|user_id)` (FR-005). **Dependency**: `user_id` must be the SHA-256 hash from T016a.
- [ ] T034 [US3] Implement `code/03_analyze.py`: Singular fit check (variance ≤ 0.01) and fallback re-fit without `user_id` random effect (FR-005b)
- [ ] T035 [US3] Implement `code/03_analyze.py`: Sensitivity analysis with bootstrap resampling. **Convergence Logic**: Run bootstrap iterations (target a sufficient number to ensure stable estimation) and check for convergence by verifying that the **mean p-value estimate** stabilizes (standard deviation of the mean over the last 100 iterations < 0.001). If not converged after [deferred], log a warning but proceed with the results. Also perform control variable drops and alternative random effects (FR-005a).
- [ ] T036 [US3] Implement `code/03_analyze.py`: Lexicon sensitivity check (re-run LMM including prime keywords) to test for lexical repetition bias
- [ ] T037 [US3] Implement `code/03_analyze.py`: Generate boxplot visualization comparing `prosocial_action_count` distributions (FR-006)
- [ ] T038a [US3] Implement `code/03_analyze.py`: Generate `results/descriptive_stats.json` containing mean, median, and SD for `prosocial_action_count` by group (FR-004). **This must be a separate file from the main report.**
- [ ] T038b [US3] Implement `code/03_analyze.py`: Generate `results/stats_report.json` with p-values, coefficients, CIs, sensitivity results, and validation metrics (FR-004, SC-001..SC-003)
- [ ] T039 [US3] Create `tests/integration/test_analysis_pipeline.py` to verify end-to-end analysis and report generation

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `specs/001-the-effect-of-priming-on-prosocial-behav/` including `quickstart.md` and `data-model.md`
- [ ] T041 Code cleanup and refactoring in `code/`
- [ ] T042 Performance optimization (vectorization) for VADER and lexicon scoring in `code/02_score.py`
- [ ] T043 [P] Additional unit tests for edge cases (e.g., empty subreddits, missing keys) in `tests/unit/`
- [ ] T044 Security hardening: Ensure no PII leakage in logs or error messages
- [ ] T045 Run `quickstart.md` validation to ensure reproducibility on a clean runner

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`anonymized.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (`scored.csv`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before analysis endpoints
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
Task: "Unit test for negation-aware keyword classification logic in tests/unit/test_classification.py"

# Launch all models/utilities for User Story 1 together:
Task: "Implement data checksumming utility in code/utils/checksum.py"
Task: "Configure environment variable management in code/config.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Start with T013 Power Analysis)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify group counts, anonymization)
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
 - Developer A: User Story 1 (Ingestion)
 - Developer B: User Story 2 (Scoring/Validation)
 - Developer C: User Story 3 (Analysis)
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
- **CPU Constraint**: All tasks must be feasible on a limited CPU configuration with standard RAM, no GPU. Avoid heavy ML models; use VADER and lexicons only.
- **Data Integrity**: Never fabricate data. All tasks must use real data from `pushshift/reddit` or verified fallbacks.
- **Power Analysis**: T013 MUST run before any data fetching. It uses theoretical ICC if pilot data is absent, with a mandatory log of the rationale.
- **Human Annotation**: T026a generates the protocol. T026b verifies an external file. T027 computes Kappa and aborts if < 0.7.
- **Precision**: T035 enforces a convergence check on the mean p-value estimate over the final iterations.
- **Anonymization**: T016a must retain the hash as `user_id`.