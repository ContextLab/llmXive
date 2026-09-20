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
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, numpy, nltk, vaderSentiment, statsmodels, scikit-learn, pyyaml, hashlib, datasets, sentence-transformers, scikit-learn)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create data directory structure: `data/raw/`, `data/processed/`, `data/validation/`, `data/citations/`, `results/`
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
- [ ] T011 [P] [US1] Unit test for regex classification logic in `tests/unit/test_classification.py`
- [ ] T012 [P] [US1] Unit test for PII anonymization (SHA-256 hashing) in `tests/unit/test_anonymization.py`

### Implementation for User Story 1

- [X] T013 [US1] **SOURCE VERIFICATION & FETCH**: Implement `code/01_ingest.py` to verify and fetch data from the HuggingFace dataset `jplu/tf-reddit-comments-2020` using `datasets.load_dataset(..., streaming=True)`. **Logic**: Filter for subreddits r/AskReddit, r/science, r/relationships and date range -01-01 to 2023-12-31. **Constraint**: Must stream data to fit within RAM limits. **Abort**: If dataset is unavailable or missing `link_title`, abort with clear error. **Dependency**: None (First step).
- [X] T014 [US1] **CLASSIFICATION**: Implement `code/01_ingest.py` to classify threads as 'Prime' or 'Control' based on a simple regex match in the thread title (`link_title`): `/(thank|help|support|care)/i`. **Logic**: Use Python `re.search` with `re.IGNORECASE`. **CRITICAL**: Do NOT use NLTK tokenization or negation windows. **Dependency**: Must wait for T013 success.
- [X] T015 [US1] **ANONYMIZATION**: Implement `code/01_ingest.py` to hash `author` using SHA-256 and remove raw timestamps. **Logic**: Hash the username to create `user_id`. Calculate `user_tenure` as `created_utc - author_created_utc` (account age at comment time). If `author_created_utc` is missing, use a proxy with explicit limitation reporting. Strip raw `created_utc`. **CRITICAL**: The SHA-256 hash MUST be retained as the `user_id` column for downstream random effects (FR-003). **Dependency**: Must wait for T014 success.
- [X] T016 [US1] **VALIDATION & ABORT**: Implement `code/01_ingest.py` to validate the fetched data. **Logic**: Check that at least 4,000 comments are present per group (Prime/Control) and that at least 3 subreddits are represented. **ABORT**: If conditions are not met, abort the pipeline and log the counts. Do NOT save data if this fails. **Dependency**: Must wait for T015 success.
- [X] T017 [US1] **SAVE**: Implement `code/01_ingest.py` to save `data/processed/anonymized.csv` and `data/processed/raw_counts.json`. **Dependency**: Must wait for T016 success (validation passed).
- [ ] T018 [US1] Create `tests/integration/test_ingest_pipeline.py` to verify end-to-end data flow and abort conditions

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Prosocial Action Scoring and Validation (Priority: P2)

**Goal**: Compute prosocial action counts and VADER scores, and validate the measurement against human annotations (simulated for CI, real for study).

**Independent Test**: Run `code/02_score.py` on the anonymized dataset and verify `data/processed/scored.csv` contains `prosocial_keyword_count` and `vader_score` columns, and that `results/validation_report.json` confirms Cohen's Kappa is calculated against a validation sample (flagged as SIMULATED if mock data is used).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for `prosocial_keyword_count` lexicon logic in `tests/unit/test_lexicon.py`
- [ ] T020 [P] [US2] Unit test for VADER `neg_score` extraction and range validation in `tests/unit/test_vader.py`
- [ ] T021 [P] [US2] Unit test for stratified sampling logic in `tests/unit/test_sampling.py`

### Implementation for User Story 2

- [X] T022 [US2] **VADER SCORING**: Implement `code/02_score.py` to compute VADER sentiment scores and extract `neg_score` for all comments (FR-002). **Dependency**: Must use `data/processed/anonymized.csv` from T017.
- [X] T023 [US2] **PROSOCIAL COUNT**: Implement `code/02_score.py` to compute `prosocial_keyword_count` using a specific lexicon. **Logic**: Count occurrences of prosocial keywords. **CRITICAL**: Do NOT exclude the prime keywords ("thank", "help", "support", "care") from this count; they are the independent variable definition, not an exclusion for the dependent variable. **Dependency**: Must wait for T022 success.
- [X] T024 [US2] **STRATIFIED SAMPLING**: Implement `code/02_score.py` to perform stratified sampling for validation (N=200). **Logic**: Ensure ≥200 comments with ≥50 per stratum (Prime/Control). **Dependency**: Must wait for T023 success.
- [X] T025 [US2] **GENERATE SIMULATED GOLD STANDARD**: Implement `code/validation/generate_mock_gold.py` to create `data/validation/gold_standard_simulated.csv`. **Logic**: Generate a file with `comment_id`, `rater_1`, `rater_2`, `rater_3` columns using a deterministic rule: `np.random.seed(42)` and assign labels based on `vader_score` quartiles to simulate dual-blind human annotation for CI reproducibility. **CRITICAL**: This file is for CODE PATH VALIDATION ONLY. The final report MUST flag this as "SIMULATED VALIDATION". **Dependency**: Must run before T026.
- [X] T026 [US2] **EXTERNAL FILE VERIFICATION**: Implement `code/validation/run_validation.py` to accept `data/validation/gold_standard_simulated.csv` (if `gold_standard.csv` is missing) or `data/validation/gold_standard.csv`. Verify the file contains annotations from ≥3 distinct raters. **Logic**: If `gold_standard_simulated.csv` is used, log a "SIMULATED VALIDATION" warning. If `gold_standard.csv` is used, verify ≥3 raters. **ABORT LOGIC**: If `gold_standard.csv` is present but fails the rater check, abort. If only the mock file is present, proceed with a warning. **Dependency**: Must wait for T025 success.
- [X] T027 [US2] **VALIDATION LOGIC**: Implement `code/validation/run_validation.py` to load the gold standard file (real or simulated), compute Cohen's Kappa (SC-002) and Pearson r for `neg_score` (SC-008). **LOGIC**: If the file is the simulated file, compute Kappa but flag the result as "SIMULATED" in `results/validation_report.json`. **Dependency**: Must wait for T026 success.
- [X] T028 [US2] **SAVE SCORED DATA**: Implement `code/02_score.py` to save `data/processed/scored.csv` and `results/validation_report.json`. **Dependency**: Must wait for T024 (sampling) and T027 (validation) completion.
- [ ] T029 [US2] Implement `code/02_score.py`: Performance monitoring to ensure runtime ≤ 4 hours on CPU (FR-012)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4.5: Human Annotation Collection (Priority: P2 - Mandatory for Study)

**Goal**: Collect real human annotations to satisfy Constitution Principle VI and US2 acceptance criteria.

- [ ] T030 [US2] **HUMAN ANNOTATION COLLECTION**: Implement `code/validation/collect_human_annotations.py` to generate a recruitment script and data collection form (e.g., Google Forms, Qualtrics) for dual-blind human annotation of N=200 comments. **Logic**: Randomly sample 200 comments from `data/processed/scored.csv`. Distribute to ≥3 independent raters. Collect `comment_id` and binary prosocial labels. Save raw responses to `data/validation/gold_standard.csv`. **CRITICAL**: This task is MANDATORY for the final study. If T030 is not completed, the final result must be flagged as "SIMULATED ONLY" and cannot claim measurement validity. **Dependency**: Must wait for T024 success.
- [ ] T031 [US2] **UPDATE VALIDATION PIPELINE**: Update T026/T027 logic to prioritize `data/validation/gold_standard.csv` (from T030) over `gold_standard_simulated.csv`. If T030 is completed, the validation report MUST use the real data. **Dependency**: Must wait for T030 success.

**Checkpoint**: Human validation data is ready for final analysis

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform GLMM analysis, sensitivity checks, and generate visualizations to answer the research question.

**Independent Test**: Execute `code/03_analyze.py` on the scored dataset and verify `results/stats_report.json` contains p-values, coefficients, CIs, sensitivity results, and `results/boxplot.png` exists.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Unit test for GLMM formula construction and singular fit detection in `tests/unit/test_glmm.py`
- [ ] T033 [P] [US3] Unit test for sensitivity analysis bootstrap logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [X] T034 [US3] **FEATURE DERIVATION**: Implement `code/03_analyze.py` to derive `thread_length` (word count of `link_title`) and `user_tenure` (days since `author_created_utc`) from the `scored.csv` data. **Logic**: Calculate these features directly from the available columns. **Dependency**: Must use `data/processed/scored.csv` from T028.
- [X] T035 [US3] **FIT GLMM**: Implement `code/03_analyze.py` to fit a Generalized Linear Mixed Model (GLMM) with a Poisson or Negative Binomial link. **Formula**: `prosocial_keyword_count ~ thread_type + thread_length + user_tenure + (1|subreddit) + (1|user_id)`. **Logic**: Use `statsmodels` or `lme4` (via `rpy2` if necessary, but prefer `statsmodels` for Python). **Constraint**: Model MUST converge (convergence status == 'converged') AND the p-value for the `thread_type` fixed effect MUST be < 0.05 for the analysis to be considered successful. **Dependency**: Must wait for T034 success.
- [X] T036 [US3] **SINGULAR FIT CHECK**: Implement `code/03_analyze.py` to check for singular fit (variance ≤ 0.01) and fallback re-fit without `user_id` random effect if necessary (FR-003b).
- [X] T037 [US3] **SENSITIVITY ANALYSIS**: Implement `code/03_analyze.py` to perform sensitivity analysis with bootstrap resampling. **Logic**: Run bootstrap iterations to verify model stability. Check for convergence by verifying that the mean p-value estimate stabilizes. **Dependency**: Must wait for T035 success.
- [X] T038 [US3] **LEXICON SENSITIVITY**: Implement `code/03_analyze.py` to re-run GLMM including prime keywords as a covariate to test for lexical repetition bias.
- [X] T039 [US3] **VISUALIZATION**: Implement `code/03_analyze.py` to generate boxplot visualization comparing `prosocial_keyword_count` distributions (FR-006).
- [X] T040 [US3] **UNIFIED STATISTICAL REPORT**: Implement `code/03_analyze.py` to generate a single `results/stats_report.json` containing descriptive statistics (mean, median, SD), p-values, coefficients, CIs, sensitivity results, and validation metrics (FR-004, SC-001..SC-003). **CRITICAL**: Consolidate all statistics into one file to ensure a single source of truth.
- [ ] T041 [US3] Create `tests/integration/test_analysis_pipeline.py` to verify end-to-end analysis and report generation

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `specs/001-the-effect-of-priming-on-prosocial-behav/` including `quickstart.md` and `data-model.md`
- [ ] T043 Code cleanup and refactoring in `code/`
- [ ] T044 Performance optimization (vectorization) for VADER and lexicon scoring in `code/02_score.py`
- [ ] T045 [P] Additional unit tests for edge cases (e.g., empty subreddits, missing keys) in `tests/unit/`
- [ ] T046 Security hardening: Ensure no PII leakage in logs or error messages
- [ ] T047 Run `quickstart.md` validation to ensure reproducibility on a clean runner

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
Task: "Unit test for regex classification logic in tests/unit/test_classification.py"

# Launch all models/utilities for User Story 1 together:
Task: "Implement data checksumming utility in code/utils/checksum.py"
Task: "Configure environment variable management in code/config.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Start with T013 Source Verification, then T014 Data Fetching)
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
- **CPU Constraint**: All tasks must be feasible on a limited CPU configuration with standard RAM, no GPU. Avoid heavy ML models; use VADER and lexicons only. Data is streamed to fit RAM.
- **Data Integrity**: Never fabricate data. All tasks must use real data from the verified HuggingFace dataset `jplu/tf-reddit-comments-2020`. Mock data is only for code path validation (T025) and must be flagged as "SIMULATED".
- **GLMM**: T035 implements a GLMM (Poisson/NB) as per Plan, not a Gaussian LMM, to handle count data correctly.
- **Human Annotation**: T030 is the MANDATORY task for real human annotation. T025 generates a simulated file for CI code path validation. T026/T027 handle both real and simulated files, flagging the simulated results. Real human annotation is required for the final study if manual intervention is possible.
- **Precision**: T037 enforces a convergence check on the mean p-value estimate over the final iterations, with a hard stop if stability is not achieved.
- **Anonymization**: T015 must retain the hash as `user_id`.
- **Unified Reporting**: T040 consolidates all statistical outputs into a single `stats_report.json`.