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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (code/, data/raw, data/processed, state/, docs/)
- [X] T002 Initialize Python project with requirements.txt (pandas, nltk, scikit-learn, statsmodels, pyyaml, requests, scipy, langdetect)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup initial data contracts in code/contracts/ (thread.schema.yaml, sentiment.schema.yaml, result.schema.yaml) based on Plan.md initial draft.
- [X] T005 [P] Implement logging infrastructure and artifact hashing in state/
- [X] T006 Create base configuration management for API keys and dataset paths
- [X] T007 [P] Setup pytest environment with CPU-only constraints: Create `code/tests/conftest.py` and `pytest.ini` to enforce random seed pinning (e.g., `addopts = --random-seed=42`) and CPU-only execution flags.

- [X] T019c [S] [US1] **Update Data Contracts**: Update `code/contracts/thread.schema.yaml` to explicitly define `random_intercept: thread_id` to align with Spec FR-006, overriding the Plan.md suggestion of 'Subreddit'. Document the override in the schema file comments. Validate that it matches Spec FR-006 requirements.
 **Dependency**: T004.
 **Output**: Updated `code/contracts/thread.schema.yaml` and `state/schema_validation_log.json`.
 **Constraint**: This task MUST run before T020 (GLMM Fitting) to ensure the correct schema is used.

---

## Phase 2.5: Data Acquisition (Split for Sequential Execution)

**Purpose**: Implement the data download fallback chain in atomic steps.

- [X] T008a [S] [US1] **Fetch Data**: Implement `code/data/download.py` to fetch data:
 **Primary**: Pushshift API (verified endpoint as per Spec Assumption 1).
 **Fallback 1**: Reddit Official API (OAuth).
 **Fallback 2**: Internet Archive/Common Crawl (generic reference per Spec Assumption 1).
 **Constraint**: 
 1. Do NOT use HuggingFace archives as a fallback unless explicitly added to the spec. 
 2. If all sources fail, raise a `RuntimeError` with a clear message indicating the data source failure. 
 3. Do NOT generate synthetic data.
 **Output**: Write raw data to `data/raw/reddit_threads.jsonl`.

- [X] T008b [S] [US1] **Validate Fallbacks**: Implement `code/data/download.py` to log the `origin_type` (API vs. archive) for every thread and verify the fallback chain logic.
 **Input**: Read `data/raw/reddit_threads.jsonl` (the raw file output from T008a).
 **Logic**: Verify that the `origin_type` logging implemented in T008a is present and accurate for all records by reading the raw file content.
 **Output**: Write `data/processed/download_attempts.log` with `{"timestamp": "...", "endpoint": "...", "status_code":..., "success": true/false}` for each attempt.

- [X] T008c [S] [US1] **Record Checksums**: Compute a cryptographic checksum of `data/raw/reddit_threads.jsonl` and record it in `state/projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml` under `artifact_hashes`.

---

## Phase 2.5: Sentiment Tool Validation (Independent of Data Download)

**Purpose**: Validate VADER sentiment tool against human annotations (Constitution Principle VII). Runs independently of data download to ensure tool readiness.

- [X] T007a-1 [S] [US2] **Standard Test: VADER Sanity Check**.
 **Dependency**: None.
 **Logic**: Run VADER against the built-in NLTK VADER test suite (bundled with the library) to ensure scores fall within the standard normalized range.
 **Output**: `data/processed/vader_sanity_check.json` containing `status` (pass/fail), `min_score`, `max_score`.

- [X] T007a-2 [S] [US2] **Human-Annotated Corpus Validation**.
 **Dependency**: T007a-1.
 **Logic**:
 1. **Fetch Corpus**: Download the `cardiffnlp/twitter-sentiment-2018` from HuggingFace.
 2. **Verification**: Compute Cohen's Kappa between VADER scores and human annotations on the sample.
 **Constraint**: 
 1. If the external dataset is unavailable, raise a RuntimeError with a clear message. 
 2. Do NOT use hardcoded sentences or synthetic annotations. 
 3. This task requires a statistically valid corpus.
 **Data Hygiene**: Compute SHA-256 checksum of the sample used for verification and record it in `state/`.
 **Output**: `data/processed/vader_verification_log.json` containing `status` (pass/fail), `sample_size`, `cohen_kappa`, `annotation_source`.

- [X] T007b [S] [US2] Depends on T007a-2: Implement Sentiment Validation Pipeline.
 **Dependency**: T007a-2.
 **Logic**:
 1. **Validation Execution**: Confirm VADER is installed and functional on the test corpus.
 2. **Storage**: Generate `data/processed/vader_validation_report.json` containing the verification status and sample details.
 3. **Audit**: Ensure the raw annotations file (if any) is checksummed and recorded in `state/`.
 **Output**: `data/processed/vader_validation_report.json`.

---

## Phase 2.5: Language Detection (Pre-Sentiment Filtering)

**Purpose**: Filter non-English content before sentiment analysis to ensure VADER accuracy.

- [X] T071 [S] [US1] **Language Detection and Filtering**.
 **Dependency**: T008a, T007b.
 **Action**: Implement `code/data/sentiment.py` to integrate `langdetect` library. Process each comment in `data/raw/reddit_threads.jsonl`. Filter out comments where the detected language is not 'en'.
 **Input**: `data/raw/reddit_threads.jsonl`.
 **Output**: Write filtered data to `data/raw/reddit_threads_english.jsonl` and log excluded thread IDs to `data/processed/lang_filter.log`.
 **Constraint**: This task runs BEFORE T013 (Sentiment Analysis) to ensure only English content is processed.

---

## Phase 3: User Story 1 - Data Collection, Ground Truth, and Extraction (Priority: P1) 🎯 MVP

**Goal**: Download data, classify ground truth availability, and extract threads.

**Independent Test**: Can be fully tested by running the data extraction script against a sample of threads from r/AskScience and verifying that each thread has a sufficient number of seed posts extracted with valid timestamps and author IDs, and that the total dataset spans ≥2 subreddits and ≥1 site.

### Implementation for User Story 1

- [X] T010 [S] [US1] **Generate Exclusion Log**: Implement `code/data/extract.py` to identify threads with <3 top-level posts and write them to `data/processed/exclusions_seed.log`.
 **Input**: Read RAW data from `data/raw/reddit_threads_english.jsonl`.
 **Logic**: Filter threads with <3 top-level posts. Log `thread_id` and reason code `SEED_INSUFFICIENT`.
 **Output**: Write `data/processed/exclusions_seed.log`.

- [X] T009 [S] [US1] **Depends on T008a, T010, T071**: Implement `code/data/extract.py` to identify threads with decision points and extract the first N=3 top-level posts as seed posts from the *filtered* dataset (threads that passed the seed count filter).
 **Input**: Read RAW data from `data/raw/reddit_threads_english.jsonl`. Apply the exclusion filter defined by T010 by reading `data/processed/exclusions_seed.log` to identify threads to skip.
 **Action**: Compute `reply_count` for each thread and include it in the output.
 **Output**: Write `data/processed/threads_with_seeds.csv`.

- [X] T019 [S] [US1] **Depends on T009, T010, T071**: Implement `code/data/validation.py` to validate ground-truth availability (FR-009).
 **Logic**:
 1. For Stack Exchange threads: Classify as 'valid' if an 'accepted_answer_id' exists.
 2. For Reddit threads: Classify as 'valid_no_gt' (valid for dataset inclusion, but no ground truth for external validation) as per Assumption 2.
 **Constraint**: Do NOT exclude Reddit threads from the dataset; include them with the 'valid_no_gt' flag to satisfy FR-001 (≥2 subreddits).
 **Output**: Write `data/processed/valid_threads.csv` (only 'valid' threads) and `data/processed/all_threads_classified.csv` (all threads with classification).

- [X] T019a [S] [US1] **Depends on T009, T019, T010, T071**: Implement `code/data/validation.py` to **compute the external validation score** (accuracy of consensus vs. ground truth) for valid threads.
 **Logic**: Calculate accuracy of consensus (majority vote) against ground truth for valid threads.
 **Consensus Definition**: For Stack Exchange, consensus is the 'accepted_answer_id'. For Reddit, set `external_validation_score` to `null` and log the reason as 'No External Ground Truth'.
 **Input**: Merge data from T009 (seed posts) and T019 (ground truth classification). Iterate over ALL threads in `data/processed/all_threads_classified.csv`.
 **Output**: Append `external_validation_score` to `data/processed/valid_threads.csv` (for valid threads) and `data/processed/all_threads_classified.csv` (for all threads, setting null for 'valid_no_gt').
 **Constraint**: This task runs on the full classified dataset, explicitly handling 'valid_no_gt' threads by setting their score to null.

- [X] T019b [S] [US1] **Depends on T009, T019, T010, T071**: Implement `code/data/validation.py` to check if valid threads < 30% of the **TOTAL RAW DATASET**.
 **Source**: Read `total_thread_count` DIRECTLY from `data/raw/reddit_threads.jsonl` (output of T008a, **before** T071 or T010 filtering) to ensure the denominator represents the true total dataset. Read `valid_thread_count` from `data/processed/all_threads_classified.csv` (T019 output).
 **Logic**: Calculate `valid_thread_percentage = (count(valid) / count(total_raw_threads)) * 100`.
 **Constraint**: Generate `data/processed/ground_truth_stats.json` first containing `total_dataset_count`, `valid_dataset_count`, and `valid_thread_percentage`. THEN check if `valid_thread_percentage < 30`. If <30, log a warning indicating that the study validity threshold (SC-006) is not met, set `status: warning`, and DO NOT raise a RuntimeError. The pipeline MUST continue to allow downstream analysis and reporting.
 **Output**: Generate `state/sc_006_compliance_report.json` (conditional on threshold) and `data/processed/ground_truth_stats.json`.

- [X] T011 [S] [US1] Implement validation logic in `code/data/extract.py` to ensure metadata (timestamp, author, comment ID) is complete for ≥95% of extracted threads.

- [X] T012 [S] [US1] Create unit tests in `code/tests/test_extract.py`: Implement specific functions `test_extract_seed_posts`, `test_flag_insufficient_seeds`, and `test_metadata_completeness`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Ground truth and seed extraction are complete.

---

## Phase 3: User Story 2 - Sentiment Analysis and Contagion Index Computation (Priority: P2)

**Goal**: Apply VADER sentiment analysis and compute the emotional contagion index.

**Independent Test**: Can be fully tested by running sentiment analysis on a fixed test corpus of Reddit comments and verifying that VADER scores fall within the standard normalized range. and the contagion index computation returns a valid correlation coefficient for threads with ≥20 replies.

### Implementation for User Story 2

- [X] T013 [S] [US2] **Depends on T071, T007b**: Implement `code/data/sentiment.py` to apply VADER (NLTK) and compute compound sentiment scores on a bounded scale for each post in the *English-filtered* dataset (valid + valid_no_gt).
 **Constraint**: This task runs on the English-filtered dataset (output of T071). Dependency on T007b ensures validation ran (and passed or logged a warning).

- [X] T015a [S] [US2] **Depends on T013, T019, T010, T071**: Implement `code/data/metrics.py` to compute the emotional contagion index (Part 1: Filtering).
 **Input**: Use the *filtered* dataset (valid + valid_no_gt threads, seed posts extracted). Read valid thread list from `data/processed/threads_with_seeds.csv`.
 **Logic**:
 1. **Filter**: Select threads where `reply_count >= 5`.
 2. **Primary Set**: Select threads with `reply_count >= 20` for the fixed-window contagion index calculation (as per Plan and Spec).
 3. **Secondary Set**: Select threads with `5 <= reply_count < 20` for the 'available replies' calculation.
 4. **Exclusion**: Log the count of threads excluded due to `reply_count < 5` with reason code `REPLY_COUNT_INSUFFICIENT`.
 **Constraint**: Strictly exclude threads with <5 replies from all contagion analysis. Include threads with 5-19 replies in the Secondary Set.

- [X] T015b [S] [US2] **Depends on T015a**: Implement `code/data/metrics.py` to compute the emotional contagion index (Part 2: Calculation) **AND Confidence Intervals**.
 **Logic**:
 1. **Performance Guardrail**: Estimate runtime based on thread count. If estimated runtime > 5 hours, reduce bootstrap resamples from 1000 to 500 **before** execution.
 2. **Primary Set (>=20)**: For threads with `reply_count >= 20`, calculate the **change in sentiment (delta)** of subsequent replies over the **initial set of comments**. **Delta is defined as the slope of the linear regression of sentiment score vs. reply position (1 to 20)**. Compute the Pearson correlation between the seed-post sentiment and this **delta**.
 3. **Secondary Set (5-19)**: For threads with `5 <= reply_count < 20`, calculate the **change in sentiment (delta)** over the **available replies** (1 to N, where N = reply_count). Compute the Pearson correlation between the seed-post sentiment and this **delta**.
 4. **Confidence Intervals**: For each thread, compute confidence intervals for the Pearson correlation using bootstrapping (a sufficient number of resamples determined by guardrail criteria).
 **Constraint**: Threads with <5 replies are excluded (handled by T015a). **Do NOT use a variable window** for the Primary Set, but use the **available window** for the Secondary Set.
 **Output**: Append results to `data/processed/thread_metrics.csv` with columns [thread_id, contagion_index, reply_count_used, window_type, confidence_interval_low, confidence_interval_high].

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Decision Quality Metrics and Statistical Modeling (Priority: P3)

**Goal**: Compute decision quality metrics, fit GLMMs, and perform sensitivity analysis.

**Independent Test**: Can be tested by running the statistical modeling pipeline on a sample dataset of threads and verifying that GLMMs converge, p-values are computed, and multiple-comparison correction is applied when ≥3 tests are run.

### Implementation for User Story 3

- [X] T018 [S] [US3] Implement `code/data/metrics.py` to compute decision quality metrics: (a) agreement proportion, (b) Shannon entropy for diversity, (c) external validation score (read from T019a output), and (d) efficiency metrics (time-to-decision, thread length).
 **Input**: Read external validation score from `data/processed/valid_threads.csv`.

- [X] T020 [S] [US3] **Depends on T019a, T015b, T019c**: Implement `code/data/modeling.py` to fit Generalized Linear Mixed Models (GLMM) with **thread-level random intercepts**. Use **beta regression** for bounded outcomes (agreement proportion). For time-to-decision (continuous duration), **select an appropriate distribution (e.g., Gamma or Log-Normal) based on residual diagnostics (AIC/BIC)** and use the corresponding link function. **Include the external validation score as a predictor** in the model where applicable.
 **Constraint**: 
 1. **Override Plan.md**: Use **Random intercept: Thread ID** (not Subreddit) to match Spec FR-006, overriding the initial plan suggestion for 'Subreddit'. Document this override with a comment referencing Spec FR-006.
 2. Note: This change requires a formal amendment to the Plan.md to align the technical approach with the Spec.
 **Input**: Join `valid_threads.csv` and `thread_metrics.csv` on `thread_id`.
 **Output**: Model outputs and diagnostic information will be stored as files in the data/processed directory.

- [X] T021 [S] [US3] Implement significance testing in `code/data/modeling.py`: Wald tests (α=0.05) for contagion coefficients.

- [X] T022 [S] [US3] Implement multiple-comparison correction in `code/data/modeling.py`: Apply Bonferroni or Benjamini-Hochberg FDR when ≥3 hypothesis tests are run (FR-007).

- [X] T023a [S] [US3] **Split Task 1**: Implement FP/FN Calculation in `code/data/metrics.py`.
 **Input**: Read `data/processed/valid_threads.csv` (T019a).
 **Logic**: Calculate and report False Positive and False Negative rates of Consensus vs. Ground Truth for valid threads.
 **Output**: Intermediate FP/FN data.

- [X] T023b [S] [US3] **Split Task 2**: Implement Correlation Analysis in `code/data/metrics.py`.
 **Input**: Read `data/processed/valid_threads.csv` and `data/processed/thread_metrics.csv`.
 **Logic**: Compute the Pearson correlation between contagion index and () agreement proportion, (2) Shannon entropy, and (3) external validation score for each sweep (agreement cutoff [0.5, 0.6, 0.7] and entropy threshold {0.2, 0.4, 0.6}).
 **Constraint**: Generate a **FULL grid report**. If cells are empty, the task must report the specific missing combinations rather than logging a warning and continuing. Partial results are not permitted.
 **Output**: Write `data/processed/sensitivity_analysis.csv`.

- [X] T023c [S] [US3] **Split Task 3**: Generate Trend Summary in `code/data/modeling.py`.
 **Input**: Read `data/processed/sensitivity_analysis.csv`.
 **Logic**: Generate a deterministic `trend_summary` text description for the primary metric (contagion vs. agreement).
 **Output**: Append `trend_summary` to `data/processed/sensitivity_analysis.csv`.

- [X] T024 [S] [US3] **Depends on T019a, T015b**: Implement correlation analysis in `code/data/modeling.py`: Compute the correlation between the external validation score and the contagion index/decision quality metrics.
 **Input**: Read external validation score from `data/processed/valid_threads.csv` and contagion index from `data/processed/thread_metrics.csv`.
 **Output**: Output results to `data/processed/external_validation_correlation.csv`.

- [X] T024a [P] [US3] Create integration tests in `code/tests/test_modeling.py` to verify GLMM convergence and correction application.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030 [S] **Review Fix**: Implement collinearity diagnostics (Variance Inflation Factor) for predictors (sentiment, thread length, time-to-decision, external_validation_score) in `code/data/modeling.py`.
 **Requirement**: Compute VIF scores and output them to `data/processed/collinearity_diagnostics.json`

- [X] T031 [S] **Review Fix**: Ensure `code/data/download.py` implements a strict "fail-loud" policy for data fetching: Remove any `try/except` blocks that fall back to `generate_synthetic_*()` or mock data.
 **Logic**: If the primary Pushshift API, Reddit API, and Internet Archive/Common Crawl all fail, raise a RuntimeError with a clear message indicating the exact failure point.

- [X] T032 [S] **Review Fix**: Update `code/data/metrics.py` to explicitly state the streaming/sampling rule in comments and logs: specify the exact split used, chunking strategy (if any), and the number of rows processed.

- [X] T041 [S] **Review Fix**: Generate Sampling Strategy Log.
 **Action**: Create `data/processed/sampling_strategy_log.json` documenting the exact sampling rules (if any) used for dataset subsets, including the random seed, sample size, and representativeness limitations.

- [X] T042 [S] **Review Fix**: Generate Fail-Loud Verification Log.
 **Action**: Create `data/processed/fail_loud_verification_log.json` documenting the results of simulated failure condition triggers (e.g., using `unittest.mock` to simulate API 500 errors) to confirm that `RuntimeError` is raised and the pipeline halts as expected.

- [X] T025 [S] **Review Fix**: Run full pipeline on up to N=500 threads and verify completion within 6 hours on CPU-only runner (SC-005).
 **Requirement**: Implement a runtime check that raises an error or flags a `status: failure` if the total runtime exceeds a predefined maximum duration threshold.

- [X] T026 [S] **Review Fix**: Generate final report in `docs/paper.md` including SC-006 pass/fail status, ground truth percentage, model results, and the correlation analysis between external validation score and decision quality.

- [X] T029 [S] **Review Fix**: Create/Overwrite `docs/quickstart.md` with execution instructions for the full pipeline.

- [X] T033 [S] **Review Fix**: Generate Sampling Strategy Log.
 **Action**: Document streaming rules in comments and logs.

- [X] T034 [S] **Review Fix**: Ensure `docs/paper.md` includes a "Data Availability" section with a direct link to the `data/raw/reddit_threads.jsonl` checksum and the `state/artifact_hashes` map, ensuring full reproducibility.

- [X] T035 [S] **Review Fix**: Verify that the VADER sentiment analysis in T013 correctly handles multi-lingual content, as the dataset may contain non-English threads.

- [X] T036 [S] **Review Fix**: Ensure the final report (T026) includes a "Limitations" subsection specifically addressing the potential bias introduced by the exclusion of threads with <5 replies.

---

## Phase 9: Final Review & Revision (Pending)

**Purpose**: Address any remaining concerns from the analysis phase or manual review.

- [X] T078 [S] **Review Fix**: Add confidence interval stability checks to tests.
 **Action**: Implement tests to verify that confidence intervals are stable with varying bootstrap resamples.

- [X] T079 [S] **Review Fix**: Update data contracts for new fields.
 **Action**: Add definitions for `thread_count`, `ground_truth_status`, and `convergence_status` to the schema.

- [X] T080 [S] **Review Fix**: Finalize memory profiling documentation.
 **Action**: Include detailed memory usage estimates in `docs/quickstart.md`.