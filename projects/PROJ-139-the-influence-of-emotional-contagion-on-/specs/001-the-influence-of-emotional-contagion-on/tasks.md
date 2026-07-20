# Tasks: The Influence of Emotional Contagion on Collective Decision-Making in Online Forums

**Input**: Design documents from `/specs/001-emotional-contagion-decisions/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must wait for dependencies)
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
- [X] T008 [S] [US1] Implement `code/data/download.py` to fetch data:
 **Primary**: Pushshift API.
 **Fallback 1**: Reddit Official API (OAuth).
 **Fallback 2**: Verified HuggingFace archives.
 The script MUST implement the full fallback chain: if the primary fails, automatically attempt the next, and log the `origin_type` (API vs. archive) for every thread. **Constraint**: If all sources fail, raise a `RuntimeError` with a clear message indicating the data source failure. Do NOT generate synthetic data.
 **Output**: Write raw data to `data/raw/reddit_threads.jsonl`.
 **Verification**: Assert that the final dataset contains ≥2 subreddits and ≥1 Stack Exchange site. Log counts and `origin_type` distribution.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Sentiment Tool Validation (Sequential to T008 in Phase 2)

**Purpose**: Validate VADER sentiment tool against human annotations (Constitution Principle VII). Runs sequentially after T008 to ensure data availability.

- [ ] T007a [S] [US2] Implement Annotation Protocol:
 **Dependency**: T008 (Data Download).
 1. **Protocol Definition**: Create `docs/annotation_protocol.md` defining the protocol for human annotation (e.g., 5-point Likert scale, instructions for annotators).
 2. **Sample Selection**: Create `code/data/sampling.py` to select a representative subset of comments from the dataset downloaded in T008. **Constraint**: If human annotations are unavailable, the script MUST attempt to load a public sentiment corpus (e.g., from HuggingFace datasets). **Stratification Logic**: 
    - Calculate quartiles for `thread_length` and `sentiment` (using VADER on raw text as a proxy for sentiment distribution) to create a 2x2 stratification grid.
    - Select a stratified random sample to ensure representation across all grid cells.
    - **Fallback**: If the dataset is too small to form a valid grid (e.g., < 50 threads) OR if no public corpus is available, generate a validation report with `status: unvalidated` and `reason: insufficient_data_or_corpus`. Do NOT raise an error.
    - **Constraint**: If the dataset size is < 50 AND no public corpus is found, generate `data/processed/vader_validation_report.json` with `status: unvalidated` and exit successfully.
 3. **Storage**: Store raw annotations (if available) in `data/raw/annotations.json`. This file MUST be checksummed.
 **Output**: `docs/annotation_protocol.md`, `data/processed/vader_validation_report.json` (if unvalidated).
 **Dependency**: Runs sequentially after T008. **T013 can proceed if T007a completes (even if status is unvalidated), but a warning flag will be set.**

- [ ] T007b [S] [US2] **Depends on T007a**: Implement Sentiment Validation Pipeline:
 **Dependency**: T008 (Data Download), T007a (Protocol).
 1. **Validation Execution**: Run VADER against the human annotations or public corpus. **Constraint**: If annotations/corpus are not available, the script MUST generate a report with `status: unvalidated` and exit successfully. No pre-validated corpus fallback is permitted if neither exists.
 2. **Reliability**: Calculate inter-rater reliability (Cohen's Kappa). If Kappa < 0.6, generate `data/processed/vader_validation_report.json` with `status: failed`, `kappa: <value>`, and exit successfully. Do NOT raise a RuntimeError.
 3. **Storage**: Generate `data/processed/vader_validation_report.json` containing the Kappa value, sample size, and source (human/public).
 4. **Justification**: Compute bootstrapped confidence intervals for Kappa to justify subset validity. Output `data/processed/validation_justification.json`.
 **Output**: `data/processed/vader_validation_report.json`, `data/processed/validation_justification.json`.
 **Dependency**: Runs sequentially after T007a. **T013 can proceed if T007b completes (even if status is failed/unvalidated), but a warning flag will be set.**

---

## Phase 3: User Story 1 - Data Collection, Ground Truth, and Extraction (Priority: P1) 🎯 MVP

**Goal**: Download data, classify ground truth availability, and extract threads.

**Independent Test**: Can be fully tested by running the data extraction script against a sample of threads from r/AskScience and verifying that each thread has a sufficient number of seed posts extracted with valid timestamps and author IDs, and that the total dataset spans ≥2 subreddits and ≥1 site.

### Implementation for User Story 1

- [X] T019 [S] [US1] Implement `code/data/validation.py` to validate ground-truth availability (FR-009).
 **Logic**: 
 1. For Stack Exchange threads: Classify as 'valid' if an 'accepted_answer_id' exists.
 2. For Reddit threads: Classify as 'valid_no_gt' (valid for dataset inclusion, but no ground truth for external validation) as per Assumption 2.
 **Constraint**: Do NOT exclude Reddit threads from the dataset; include them with the 'valid_no_gt' flag to satisfy FR-001 (≥2 subreddits).
 **Action**: Classify threads into three states: 'valid' (has GT), 'valid_no_gt' (Reddit), 'invalid' (excluded). Log the count and percentage of each.
 **Output**: Write `data/processed/valid_threads.csv` (only 'valid' threads) and `data/processed/all_threads_classified.csv` (all threads with classification).
- [X] T019b [S] [US1] **Depends on T019**: Implement logic in `code/data/validation.py` to check if valid threads < 30%.
 **Source**: Read total thread count from `data/raw/reddit_threads.jsonl` and valid thread count from `data/processed/valid_threads.csv`.
 **Action**: Calculate `valid_thread_percentage = (count(valid) / count(total)) * 100`.
 **Constraint**: If `valid_thread_percentage < 30`, **DO NOT raise a RuntimeError**. Instead, generate `data/processed/validity_status.json` with `sc_006_compliance: false`, `valid_thread_percentage` (float), `threshold` (30), `status: fail`. The pipeline MUST continue. If `valid_thread_percentage >= 30`, generate `data/processed/validity_status.json` with `sc_006_compliance: true`, `status: pass`.
 **Output**: Generate `data/processed/validity_status.json` with `valid_thread_percentage` (float), `threshold` (30), `status` (pass/fail), `sc_006_compliance` (boolean).
 **Note**: This task produces the SC-006 compliance report and does not block downstream tasks.
- [X] T019a [S] [US1] **Depends on T019**: Implement `code/data/validation.py` to **compute the external validation score** (accuracy of consensus vs. ground truth) for valid threads.
 **Logic**: Calculate accuracy of consensus (majority vote) against ground truth for valid threads.
 **Output**: Append `external_validation_score` to `data/processed/valid_threads.csv`.
 **Constraint**: This task runs only on the 'valid' subset identified in T019.
- [X] T010 [S] [US1] Implement exclusion logic in `code/data/extract.py`: Flag threads with <3 top-level posts with reason code `SEED_INSUFFICIENT`.
 **Requirement**: Log the `origin_type` (from T008) alongside the reason code for reproducibility.
 **Output**: Write exclusion log to `data/processed/exclusions_seed.log` with columns [thread_id, reason_code, origin_type].
- [X] T009 [S] [US1] **Depends on T010, T019**: Implement `code/data/extract.py` to identify threads with decision points and extract the first N=3 top-level posts as seed posts from the *filtered* dataset (valid threads + valid_no_gt threads, after seed count filtering).
 **Input**: Read from `data/processed/all_threads_classified.csv` (after T010 filtering).
 **Output**: Write `data/processed/threads_with_seeds.csv`.
- [X] T011 [S] [US1] Implement validation logic in `code/data/extract.py` to ensure metadata (timestamp, author, comment ID) is complete for ≥95% of extracted threads.
- [X] T012 [S] [US1] **Depends on T009, T010, T011**: Create unit tests in `code/tests/test_extract.py`: Implement specific functions `test_extract_seed_posts`, `test_flag_insufficient_seeds`, and `test_metadata_completeness`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Ground truth and seed extraction are complete.

---

## Phase 4: User Story 2 - Sentiment Analysis and Contagion Index Computation (Priority: P2)

**Goal**: Apply VADER sentiment analysis and compute the emotional contagion index.

**Independent Test**: Can be fully tested by running sentiment analysis on a fixed test corpus of Reddit comments and verifying that VADER compound scores fall within the standard normalized range. and the contagion index computation returns a valid correlation coefficient for threads with ≥5 replies.

### Implementation for User Story 2

- [X] T013 [S] [US2] **Depends on T008, T010, T007b**: Implement `code/data/sentiment.py` to apply VADER (NLTK) and compute compound sentiment scores on a bounded scale for each post in the *full* dataset (valid + valid_no_gt).
 **Constraint**: This task runs on the FULL dataset. **Dependency on T007b ensures validation ran (even if unvalidated/failed).**
- [X] T016 [S] [US2] Implement exclusion logic in `code/data/metrics.py`: Flag threads with <5 replies as insufficient for contagion analysis.
 **Output**: Log the count of excluded threads to `data/processed/exclusion_counts.json`.
- [X] T015 [S] [US2] **Depends on T016, T010, T013, T019**: Implement `code/data/metrics.py` to compute the emotional contagion index.
 **Input**: Use the *filtered* dataset (valid + valid_no_gt threads, seed posts extracted, reply count ≥5). Read valid thread list from `data/processed/all_threads_classified.csv`. **Filter**: Select threads where `is_valid=True` OR `is_valid_no_gt=True` AND `reply_count >= 5`.
 **Logic**: **Exclude threads with <5 replies** (handled by T016). Calculate the **change in sentiment (delta)** of subsequent replies over the first 20 comments OR the total available replies (whichever is smaller). **Delta is defined as the slope of the linear regression of sentiment score vs. reply position (1 to min(20, available_replies))**. Compute the Pearson correlation between the seed-post sentiment and this **delta**.
 **Note**: The regression slope (delta) represents the "change in sentiment" required by Spec FR-004.
 **Output**: Append results to `data/processed/thread_metrics.csv` with columns [thread_id, contagion_index, reply_count].
 **Constraint**: Exclude threads with <5 replies (handled by T016) and threads excluded in T010 (use `filtered_thread_ids.csv` from T010/T019 as input list).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Decision Quality Metrics and Statistical Modeling (Priority: P3)

**Goal**: Compute decision quality metrics, fit GLMMs, and perform sensitivity analysis.

**Independent Test**: Can be tested by running the statistical modeling pipeline on a sample dataset of threads and verifying that GLMMs converge, p-values are computed, and multiple-comparison correction is applied when ≥3 tests are run.

### Implementation for User Story 3

- [X] T018 [S] [US3] Implement `code/data/metrics.py` to compute decision quality metrics: (a) agreement proportion, (b) Shannon entropy for diversity, (c) external validation score (read from T019a output), and (d) efficiency metrics (time-to-decision, thread length).
 **Input**: Read external validation score from `data/processed/valid_threads.csv` generated by T019a.
- [X] T020 [S] [US3] **Depends on T019a, T015**: Implement `code/data/modeling.py` to fit Generalized Linear Mixed Models (GLMM) with **thread-level random intercepts**. Use **beta regression** for bounded outcomes (agreement proportion), **Gamma distribution with log link** for time-to-decision outcomes, and appropriate link functions for count outcomes. **Include the external validation score as a predictor** in the model where applicable. **Random intercept: Subreddit** (Corrected from 'Thread ID' to match Spec FR-006 and Plan Thread entity).
- [X] T021 [S] [US3] Implement significance testing in `code/data/modeling.py`: Wald tests (α=0.05) for contagion coefficients.
- [X] T022 [S] [US3] Implement multiple-comparison correction in `code/data/modeling.py`: Apply Bonferroni or Benjamini-Hochberg FDR when ≥3 hypothesis tests are run (FR-007).
- [X] T023 [S] [US3] **Depends on T019a, T015, T019, T019b**: Implement sensitivity analysis in `code/data/modeling.py`:
 **Sweep**: Agreement cutoff across **{0.5, 0.6, 0.7}** and entropy threshold across **{0.2, 0.4, 0.6}**.
 **Metric**: Compute the **Pearson correlation between contagion_index and (1) agreement_proportion, (2) Shannon entropy, and (3) external validation score** for each sweep.
 **Requirement**: For valid threads, **compute and report False Positive and False Negative rates** of Consensus vs. Ground Truth for *each* threshold sweep. 
 **Consensus Logic**: Consensus=1 if upvotes > downvotes; Consensus=0 if downvotes > upvotes; Inconclusive if equal. FP/FN rates are calculated only on threads with a definitive consensus (exclude Inconclusive).
 **Input**: Read valid thread list from `data/processed/valid_threads.csv`. **Filter**: Use threads where `is_valid=True`. If T019b reports `sc_006_compliance: false`, FP/FN columns must be filled with `null` and a warning logged.
 **Output**: Write `data/processed/sensitivity_analysis.csv` with columns: `agreement_cutoff` (float), `entropy_threshold` (float), `correlation_agreement` (float), `correlation_entropy` (float), `correlation_validation` (float), `false_positive_rate` (float/null), `false_negative_rate` (float/null), `grid_coverage` (boolean), `trend_summary` (text).
 **Requirement**: Generate a summary report (text and CSV) explicitly describing the **trend** of the primary contagion-vs-quality correlation across the swept thresholds (e.g., "Correlation decreases as agreement cutoff increases"). The `trend_summary` column in the CSV must contain this description for the primary metric.
 **Requirement**: Ensure the output covers the full x3 cross-product grid (9 rows) and sets `grid_coverage: true` only if all 9 rows are present.
- [X] T024 [S] [US3] **Depends on T019a, T015**: Implement correlation analysis in `code/data/modeling.py`: Compute the correlation between the **external validation score** and the contagion index/decision quality metrics.
 **Input**: Read external validation score from `data/processed/valid_threads.csv` (T019a) and contagion index from `data/processed/thread_metrics.csv` (T015).
 **Output**: Output results to `data/processed/external_validation_correlation.csv`.
- [X] T024a [P] [US3] Create integration tests in `code/tests/test_modeling.py` to verify GLMM convergence and correction application.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5.5: Performance Verification (Removed - Consolidated)

**Note**: Task T025a has been removed and consolidated into Phase 6 (T025) to avoid redundancy and incorrect dependencies.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T025 [S] Run full pipeline on N=500 threads and verify completion within 6 hours on CPU-only runner (SC-005).
 **Requirement**: Implement a runtime check that **raises an error** or flags a `status: failure` if the total runtime exceeds 6 hours.
 **Output**: Generate `state/performance_log.json` containing `total_runtime_seconds` (int), `thread_count` (int), `status` (string: "success" or "failure"), and `resource_check` (object: {cpu: bool, ram_gb: float, disk_gb: float}).
 **Constraint**: This task runs AFTER T023 (Sensitivity Analysis) to verify the full pipeline performance.
- [X] T026 [S] Generate final report in `docs/paper.md` including SC-006 pass/fail status, ground truth percentage, model results, **and the correlation analysis between external validation score and decision quality (from T024)**.
- [X] T027 [S] Record all artifact checksums: Update `state/projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml` with a map of file paths to SHA-256 hashes.
- [ ] T028 [S] Verify reproducibility by re-running pipeline and matching checksums.
- [ ] T029 [S] [US3] **Review Fix**: Create/Overwrite `docs/quickstart.md` with execution instructions for the full pipeline.
 **Dependency**: T030, T031, T032.
 **Deliverable**: `docs/quickstart.md` MUST contain:
 1. **Prerequisites**: Python 3.11, dependencies.
 2. **Install Command**: `pip install -r code/requirements.txt`.
 3. **Run Command**: `python code/analysis/run_pipeline.py --threads`.
 4. **Output Description**: List expected artifacts in `data/processed/` and `state/`.
 **Verification**: Ensure the file exists and contains all listed sections.
- [ ] T030 [S] [US3] **Review Fix**: Implement collinearity diagnostics (Variance Inflation Factor) for predictors **(sentiment, thread length, time-to-decision, external_validation_score)** in `code/data/modeling.py` as required by **Assumption 7**. Output VIF scores to `data/processed/collinearity_diagnostics.json`.
 **JSON Schema**: `{"vif_scores": {"sentiment": float, "thread_length": float, "time_to_decision": float, "external_validation_score": float}, "threshold": 5, "flagged": boolean}`.
 **Threshold Logic**: VIF > 5 is strict greater than. If any predictor has VIF > 5, set `flagged: true` and frame joint relationships descriptively in the final report.
- [ ] T031 [S] **Review Fix**: Ensure `code/data/download.py` implements a strict "fail-loud" policy for data fetching: **Remove** any `try/except` blocks that fall back to `generate_synthetic_*()` or mock data. If the primary Pushshift API, Reddit API, and HuggingFace archives all fail, the script MUST raise a `RuntimeError` with a clear message indicating the data source failure, ensuring the execution stage can re-try with a verified real source rather than proceeding with fabricated data.
 **Implementation**: Modify `download.py` to catch all API exceptions, attempt fallbacks, and if all fail, `raise RuntimeError("All data sources failed. No synthetic data generated.")`.
- [ ] T032 [S] **Review Fix**: Update `code/data/metrics.py` to explicitly state the **streaming/sampling rule** in comments and logs: specify the exact split used, chunking strategy (if any), and the number of rows processed. If a sample is taken due to dataset size, the code MUST log the sample size and a statement of its representativeness limitation, ensuring no "toy" or "synthetic" data is used as a silent fallback.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Phase 2.5 (Validation)**: Runs sequentially after T008 (Data Download) in Phase 2.
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