# Tasks: The Influence of Emotional Contagion on Collective Decision-Making in Online Forums

**Input**: Design documents from `/specs/001-emotional-contagion-decisions/`
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

- [X] T001 Create project structure per implementation plan (code/, data/raw, data/processed, state/, docs/)
- [X] T002 Initialize Python 3.11 project with requirements.txt (pandas, nltk, scikit-learn, statsmodels, pyyaml, requests, scipy)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data contracts in code/contracts/ (thread.schema.yaml, sentiment.schema.yaml, result.schema.yaml)
- [X] T005 [P] Implement logging infrastructure and artifact hashing in state/
- [X] T006 Create base configuration management for API keys and dataset paths
- [ ] T007 [P] Setup pytest environment with CPU-only constraints: Create `code/tests/conftest.py` and `pytest.ini` to enforce random seed pinning (e.g., `addopts = --random-seed=42`) and CPU-only execution flags.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection and Thread Extraction (Priority: P1) 🎯 MVP

**Goal**: Download Reddit/Stack Exchange data and extract threads with seed posts.

**Independent Test**: Can be fully tested by running the data extraction script against a sample of threads from r/AskScience and verifying that each thread has a sufficient number of seed posts extracted with valid timestamps and author IDs, and that the total dataset spans ≥2 subreddits and ≥1 site.

### Implementation for User Story 1

- [ ] T008 [P] [US1] Implement `code/data/download.py` to fetch data: **Primary**: Pushshift API (if reachable). **Fallback 1**: Reddit Official API. **Fallback 2**: Verified HuggingFace archives or Internet Archive dumps. The script MUST implement the full fallback chain: if the primary fails, automatically attempt the next, and log the origin type used. Do not skip Pushshift; attempt it first as per Spec FR-001.
- [ ] T009 [P] [US1] Implement `code/data/extract.py` to identify threads with decision points and extract the first N=3 top-level posts as seed posts.
- [ ] T010 [US1] Implement exclusion logic in `code/data/extract.py`: Flag threads with <3 top-level posts with reason code `SEED_INSUFFICIENT` and log to `data/processed/exclusions.log`.
- [ ] T011 [US1] Implement validation logic in `code/data/extract.py` to ensure metadata (timestamp, author, comment ID) is complete for ≥95% of extracted threads.
- [ ] T012 [P] [US1] Create unit tests in `code/tests/test_extract.py`: Implement specific functions `test_extract_seed_posts` (asserts a small set of posts extracted), `test_flag_insufficient_seeds` (asserts exclusion logic), and `test_metadata_completeness` (asserts a high-confidence threshold).
- [ ] T007a [S] [US1] **Depends on T008**: Generate human-annotated corpus sample: Create a script to sample a representative subset of comments from the dataset downloaded in T008. Implement an inter-annotator agreement protocol requiring **at least 2 independent annotators** to label each sample with sentiment. Store raw annotations in `data/raw/annotations.json`. If manual annotation is not feasible, use a pre-defined gold-standard subset from a verified source. This task is sequential [S] and cannot run until T008 completes.
- [ ] T007b [S] [US1] **Depends on T007a**: Calculate inter-rater reliability and generate validation report: Implement a script to compute Cohen's Kappa on the corpus generated in T007a. The output MUST be a JSON report at `data/processed/vader_validation_report.json` containing the Kappa value and summary statistics. **Constraint**: The corpus is considered INVALID for downstream use if Kappa is not calculated or if the report is missing. This task MUST complete before T014.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Sentiment Analysis and Contagion Index Computation (Priority: P2)

**Goal**: Apply VADER sentiment analysis and compute the emotional contagion index.

**Independent Test**: Can be fully tested by running sentiment analysis on a fixed test corpus of Reddit comments and verifying that VADER compound scores fall within the standard normalized range. and the contagion index computation returns a valid correlation coefficient for threads with ≥5 replies.

### Implementation for User Story 2

- [X] T013 [P] [US2] Implement `code/data/sentiment.py` to apply VADER (NLTK) and compute compound sentiment scores on a bounded scale for each post.
- [~] T014 [US2] **Depends on T007b**: Implement VADER validation in `code/data/sentiment.py`: Run against the human-annotated corpus from T007a. **Verify** that the report from T007b (`data/processed/vader_validation_report.json`) exists and contains the required Kappa statistics. Store the final validation confirmation in the same report.
- [X] T015 [US2] Implement `code/data/metrics.py` to compute the emotional contagion index: Calculate the **slope** of the reply sentiment trajectory (linear regression of sentiment vs. position) for an initial segment of comments. Compute the Pearson correlation between the seed-post sentiment and this **slope**. **Exclude** threads with <5 replies from this analysis and log them. (Note: This aligns with the Plan's 'Technical Context' definition of the index).
- [X] T016 [US2] Implement exclusion logic in `code/data/metrics.py`: Flag threads with <5 replies as insufficient for contagion analysis and exclude from primary set.
- [X] T017 [P] [US2] Create unit tests in `code/tests/test_sentiment.py` to verify VADER scores and contagion index calculation. <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Decision Quality Metrics and Statistical Modeling (Priority: P3)

**Goal**: Compute decision quality metrics, fit GLMMs, and perform sensitivity analysis.

**Independent Test**: Can be tested by running the statistical modeling pipeline on a sample dataset of threads and verifying that GLMMs converge, p-values are computed, and multiple-comparison correction is applied when ≥3 tests are run.

### Implementation for User Story 3

- [X] T018 [P] [US3] Implement `code/data/metrics.py` to compute decision quality metrics: (a) agreement proportion, (b) Shannon entropy for diversity, (c) external validation score (ground truth), and (d) efficiency metrics (time-to-decision, thread length).
- [~] T019 [US3] Implement `code/data/validation.py` to validate ground-truth availability (FR-009), classify threads as 'valid' or 'excluded', and log the count/percentage of valid threads. Output the classified dataset to `data/processed/valid_threads.csv`.
- [X] T019a [US3] Implement `code/data/validation.py` to **compute the external validation score** (e.g., accuracy of consensus vs. ground truth) for valid threads. <!-- FAILED: unspecified -->
- [~] T019b [US3] Implement logic in `code/data/validation.py` to check if valid threads < 30%. If so, flag the study as failing SC-006 and generate a formal **failure report** in `data/processed/validity_failure_report.json` detailing the percentage and the reason for failure. This is a valid research outcome, not a project stop.
- [X] T020 [US3] Implement `code/data/modeling.py` to fit Generalized Linear Mixed Models (GLMM) with thread-level random intercepts. Use **beta regression** for bounded outcomes (agreement proportion), **Gamma distribution with log link** for time-to-decision outcomes, and appropriate link functions for count outcomes.
- [X] T021 [US3] Implement significance testing in `code/data/modeling.py`: Wald tests (α=0.05) for contagion coefficients.
- [X] T022 [US3] Implement multiple-comparison correction in `code/data/modeling.py`: Apply Bonferroni or Benjamini-Hochberg FDR when ≥3 hypothesis tests are run (FR-007).
- [~] T023 [US3] Implement sensitivity analysis in `code/data/modeling.py`: Sweep agreement cutoff across **representative values** and entropy threshold across **representative values**. Output results to `data/processed/sensitivity_analysis.csv` with columns: `agreement_cutoff`, `entropy_threshold`, `correlation_coefficient`.
- [X] T023a [US3] Implement FP/FN calculation in `code/data/modeling.py`: For valid threads, compute False Positive and False Negative rates of Consensus vs. Ground Truth **for each sensitivity threshold** defined in T023. Append these rates to the `sensitivity_analysis.csv` output.
- [X] T024 [P] [US3] Create integration tests in `code/tests/test_modeling.py` to verify GLMM convergence and correction application.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T025 [P] Run full pipeline on N=500 threads and verify completion within 6 hours on CPU-only runner (SC-005). <!-- ATOMIZE: requested -->
- [X] T026 [P] Generate final report in `docs/paper.md` including SC-006 pass/fail status, ground truth percentage, and model results.
- [~] T027 [P] Record all artifact checksums in `state/projects/PROJ-139-...yaml` under `artifact_hashes`.
- [ ] T028 [P] Verify reproducibility by re-running pipeline and matching checksums.
- [ ] T029 [P] Update `quickstart.md` with execution instructions for the full pipeline.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data extraction
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 metrics

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
# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py to fetch data from Pushshift API"
Task: "Implement code/data/extract.py to identify threads and extract seed posts"
Task: "Create unit tests in code/tests/test_extract.py"
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
- [S] tasks = sequential, depend on previous task completion
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence