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
- [X] T007 [P] Setup pytest environment with CPU-only constraints: Create `code/tests/conftest.py` and `pytest.ini` to enforce random seed pinning (e.g., `addopts = --random-seed=42`) and CPU-only execution flags.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Sentiment Tool Validation (Parallel to US1)

**Purpose**: Validate VADER sentiment tool against human annotations (Constitution Principle VII). Runs in parallel to US1 data extraction to avoid blocking.

- [ ] T007 [S] [US2-Parallel] Implement Sentiment Validation Pipeline:
 1. **Sampling**: Create `code/data/sampling.py` to select a representative subset of comments from the dataset downloaded in T008. **Constraint**: If manual annotation is not feasible, the script MUST generate a mock annotation file at `data/raw/annotations.json` with a schema of `{"comment_id": "str", "label": "neutral"}` for all sampled comments. Do not fall back to synthetic data generation for the *pipeline* data, only for the *validation* labels if human annotators are unavailable.
 2. **Protocol**: Define annotation protocol in `docs/annotation_protocol.md` requiring at least 2 independent annotators (or mock logic) to label each sample.
 3. **Storage**: Store raw annotations in `data/raw/annotations.json`. This file MUST be checksummed.
 4. **Reliability**: Calculate inter-rater reliability (Cohen's Kappa) and generate `data/processed/vader_validation_report.json`. If Kappa is missing or < 0.6, log a warning but DO NOT halt the pipeline.
 5. **Justification**: Compute bootstrapped confidence intervals for Kappa to justify subset validity. Output `data/processed/validation_justification.json`.
 **Output**: `data/processed/vader_validation_report.json`, `data/processed/validation_justification.json`.
 **Dependency**: Runs in parallel to T008/T010; does NOT block T013.

---

## Phase 3: User Story 1 - Data Collection, Ground Truth, and Extraction (Priority: P1) 🎯 MVP

**Goal**: Download data, classify ground truth availability, and extract threads.

**Independent Test**: Can be fully tested by running the data extraction script against a sample of threads from r/AskScience and verifying that each thread has a sufficient number of seed posts extracted with valid timestamps and author IDs, and that the total dataset spans ≥2 subreddits and ≥1 site.

### Implementation for User Story 1

- [ ] T008 [S] [US1] Implement `code/data/download.py` to fetch data:
 **Primary**: Pushshift API (`).
 **Fallback 1**: Reddit Official API (OAuth).
 **Fallback 2**: Verified HuggingFace archives (e.g., `pushshift/reddit`, `stackexchange/questions`).
 The script MUST implement the full fallback chain: if the primary fails, automatically attempt the next, and log the `origin_type` (API vs. archive) for every thread.
 **Output**: Write raw data to `data/raw/reddit_threads.jsonl`.
 **Verification**: Assert that the final dataset contains ≥2 subreddits and ≥1 Stack Exchange site. Log counts and `origin_type` distribution.
- [ ] T019 [S] [US1] Implement `code/data/validation.py` to validate ground-truth availability (FR-009).
 **Logic**: For Stack Exchange threads, classify as 'valid' if an 'accepted_answer_id' exists. For Reddit threads, classify as 'valid' if a 'best_answer' heuristic (e.g., highest upvoted reply with specific keywords) is detected.
 **Action**: Classify threads as 'valid' or 'excluded'. Log the count and percentage of valid threads.
 **Output**: Write `data/processed/valid_threads.csv` (only valid threads) and `data/processed/exclusions_ground_truth.log`.
- [ ] T019b [S] [US1] **Depends on T019**: Implement logic in `code/data/validation.py` to check if valid threads < 30%.
 **Source**: Use the 'Solved'/'Accepted Answer' logic defined in T019.
 **Action**: If valid threads < 30%, flag the *predictive accuracy analysis* as invalid and generate a formal **validity status report** at `data/processed/validity_status.json` with keys `valid_thread_percentage`, `threshold` (30), `status` (pass/fail). If valid threads ≥ 30%, generate `validity_status.json` with `status: pass`.
- [ ] T019a [S] [US1] **Depends on T019**: Implement `code/data/validation.py` to **compute the external validation score** (accuracy of consensus vs. ground truth) for valid threads.
 **Output**: Append `external_validation_score` to `data/processed/valid_threads.csv`.
- [ ] T010 [S] [US1] Implement exclusion logic in `code/data/extract.py`: Flag threads with <3 top-level posts with reason code `SEED_INSUFFICIENT`.
 **Requirement**: Log the `origin_type` (from T008) alongside the reason code for reproducibility.
 **Output**: Write exclusion log to `data/processed/exclusions_seed.log` with columns [thread_id, reason_code, origin_type].
- [ ] T009 [S] [US1] **Depends on T010, T019**: Implement `code/data/extract.py` to identify threads with decision points and extract the first N=3 top-level posts as seed posts from the *filtered* dataset (valid threads only).
 **Output**: Write `data/processed/threads_with_seeds.csv`.
- [ ] T011 [S] [US1] Implement validation logic in `code/data/extract.py` to ensure metadata (timestamp, author, comment ID) is complete for ≥95% of extracted threads.
- [ ] T012 [P] [US1] Create unit tests in `code/tests/test_extract.py`: Implement specific functions `test_extract_seed_posts`, `test_flag_insufficient_seeds`, and `test_metadata_completeness`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Ground truth and seed extraction are complete.

---

## Phase 4: User Story 2 - Sentiment Analysis and Contagion Index Computation (Priority: P2)

**Goal**: Apply VADER sentiment analysis and compute the emotional contagion index.

**Independent Test**: Can be fully tested by running sentiment analysis on a fixed test corpus of Reddit comments and verifying that VADER compound scores fall within the standard normalized range. and the contagion index computation returns a valid correlation coefficient for threads with ≥5 replies.

### Implementation for User Story 2

- [ ] T013 [S] [US2] **Depends on T019, T019a**: Implement `code/data/sentiment.py` to apply VADER (NLTK) and compute compound sentiment scores on a bounded scale [-1.0, 1.0] for each post in the *valid* dataset.
 **Constraint**: This task runs on the FULL valid dataset. The validation report (T007) is a quality gate but does NOT block execution. If T007 validation failed, log a warning but proceed.
- [ ] T016 [S] [US2] Implement exclusion logic in `code/data/metrics.py`: Flag threads with <5 replies as insufficient for contagion analysis.
 **Output**: Log the count of excluded threads to `data/processed/exclusion_counts.json`.
- [ ] T015 [S] [US2] **Depends on T016, T010, T013**: Implement `code/data/metrics.py` to compute the emotional contagion index.
 **Input**: Use the *filtered* dataset (valid threads, seed posts extracted, reply count ≥5).
 **Logic**: Calculate the **change in sentiment (delta)** of subsequent replies over the first 20 comments. Compute the Pearson correlation between the seed-post sentiment and this **delta**.
 **Output**: Append results to `data/processed/thread_metrics.csv` with columns [thread_id, contagion_index, reply_count].
 **Constraint**: Exclude threads with <5 replies (handled by T016) and threads excluded in T010 (use `filtered_thread_ids.csv` from T010/T019 as input list).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Decision Quality Metrics and Statistical Modeling (Priority: P3)

**Goal**: Compute decision quality metrics, fit GLMMs, and perform sensitivity analysis.

**Independent Test**: Can be tested by running the statistical modeling pipeline on a sample dataset of threads and verifying that GLMMs converge, p-values are computed, and multiple-comparison correction is applied when ≥3 tests are run.

### Implementation for User Story 3

- [ ] T018 [S] [US3] Implement `code/data/metrics.py` to compute decision quality metrics: (a) agreement proportion, (b) Shannon entropy for diversity, (c) external validation score (already in T019a, ensure consistency), and (d) efficiency metrics (time-to-decision, thread length).
- [ ] T020 [S] [US3] Implement `code/data/modeling.py` to fit Generalized Linear Mixed Models (GLMM) with thread-level random intercepts. Use **beta regression** for bounded outcomes (agreement proportion), **Gamma distribution with log link** for time-to-decision outcomes, and appropriate link functions for count outcomes. **Include the external validation score as a predictor** in the model where applicable.
- [ ] T021 [S] [US3] Implement significance testing in `code/data/modeling.py`: Wald tests (α=0.05) for contagion coefficients.
- [ ] T022 [S] [US3] Implement multiple-comparison correction in `code/data/modeling.py`: Apply Bonferroni or Benjamini-Hochberg FDR when ≥3 hypothesis tests are run (FR-007).
- [ ] T023 [S] [US3] Implement sensitivity analysis in `code/data/modeling.py`:
 **Sweep**: Agreement cutoff across **{0.5, 0.6, 0.7}** and entropy threshold across **{0.2, 0.4, 0.6}**.
 **Metric**: Compute the **Pearson correlation between contagion_index and agreement_proportion** for each sweep.
 **Requirement**: For valid threads, **compute and report False Positive and False Negative rates** of Consensus vs. Ground Truth for *each* threshold sweep.
 **Output**: Write `data/processed/sensitivity_analysis.csv` with columns: `agreement_cutoff` (float), `entropy_threshold` (float), `correlation_coefficient` (float, Pearson), `false_positive_rate` (float), `false_negative_rate` (float).
- [ ] T024 [S] [US3] **Depends on T019a**: Implement correlation analysis in `code/data/modeling.py`: Compute the correlation between the **external validation score** and the contagion index/decision quality metrics. Output results to `data/processed/external_validation_correlation.csv`.
- [ ] T024a [P] [US3] Create integration tests in `code/tests/test_modeling.py` to verify GLMM convergence and correction application.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T025 [S] Run full pipeline on N=500 threads and verify completion within 6 hours on CPU-only runner (SC-005).
 **Requirement**: Implement a runtime check that **raises an error** or flags a `status: failure` if the total runtime exceeds 6 hours.
 **Output**: Generate `state/performance_log.json` containing `total_runtime_seconds`, `thread_count`, and `status: success/failure`.
- [ ] T026 [S] Generate final report in `docs/paper.md` including SC-006 pass/fail status, ground truth percentage, model results, **and the correlation analysis between external validation score and decision quality (from T024)**.
- [ ] T027 [S] Record all artifact checksums: Update `state/projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml` with a map of file paths to SHA-256 hashes.
- [ ] T028 [S] Verify reproducibility by re-running pipeline and matching checksums.
- [ ] T029 [S] Update `quickstart.md` with execution instructions for the full pipeline.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Phase 2.5 (Validation)**: Can run in parallel with Phase 3 (US1) once Foundational is complete.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data extraction (T019, T010, T009)
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
- Once Foundational phase completes, Phase 2.5 and Phase 3 (US1) can start in parallel
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py to fetch data from Pushshift API"
Task: "Implement code/data/validation.py to classify ground truth"
Task: "Create unit tests in code/tests/test_extract.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data + Ground Truth)
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
 - Developer A: User Story 1 (Data + Ground Truth)
 - Developer B: Phase 2.5 (Sentiment Validation)
 - Developer C: User Story 2 (Sentiment + Contagion)
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