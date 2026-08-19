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
- [X] T002 Initialize Python project with requirements.txt (pandas, nltk, scikit-learn, statsmodels, pyyaml, requests, scipy, langdetect, datasets)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup initial data contracts in code/contracts/ (thread.schema.yaml, sentiment.schema.yaml, result.schema.yaml) based on Plan.md initial draft.
- [X] T019c [S] [US1] **Update Data Contracts to Match Spec FR-006**: Modify `code/contracts/thread.schema.yaml` to explicitly define `random_intercept: thread_id` to align with Spec FR-006, overriding the Plan.md suggestion of 'Subreddit'. Document the override in the schema file comments. Validate that it matches Spec FR-006 requirements.
 **Dependency**: T004.
 **Output**: Updated `code/contracts/thread.schema.yaml`.
- [X] T005 [P] Implement logging infrastructure and artifact hashing in state/
- [X] T006 Create base configuration management for API keys and dataset paths
- [X] T007 [P] Setup pytest environment with CPU-only constraints: Create `code/tests/conftest.py` and `pytest.ini` to enforce random seed pinning (e.g., `addopts = --random-seed=42`) and CPU-only execution flags.

---

## Phase 2.5: Data Acquisition & Streaming (Split for Sequential Execution)

**Purpose**: Implement streaming logic first, then fetch data.

- [X] T081 [S] **Implement Streaming Logic**: Modify `code/data/download.py` and `code/data/extract.py` to use `datasets.load_dataset(..., streaming=True)` or equivalent chunked iteration logic. Ensure the code processes the full real dataset in chunks rather than loading it entirely into RAM, adhering to the available RAM constraint.
 **Constraint**:
 1. **Primary**: Use `streaming=True` with `datasets` library.
 2. **Fail-Loud**: If memory usage exceeds **6GB** during streaming (monitored via `psutil`), the pipeline MUST raise a `RuntimeError` with a clear message indicating the failure. **Do NOT** use `itertools.islice` or any sampling fallback.
 3. Do NOT use synthetic data.
 **Output**: Updated `code/data/download.py` and `code/data/extract.py`.

- [X] T008 [S] [US1] **Fetch & Validate Data**: Implement `code/data/download.py` to fetch data:
 **Primary**: Pushshift API (verified endpoint: ` with query params `subreddit=AskScience,AskHistorians,etc&size=1000&sort=desc`).
 **Fallback 1**: Reddit Official API (OAuth).
 **Fallback 2**: Internet Archive/Common Crawl (generic reference per Spec Assumption 1).
 **Internal Sequence**:
 1. Fetch data and write to `data/raw/reddit_threads.jsonl`.
 2. Write `origin_type` log (`data/processed/download_attempts.log`) for every thread.
 3. Verify that the `origin_type` log is present and accurate by reading the raw file content.
 **Constraint**:
 1. Do NOT use HuggingFace archives as a fallback unless explicitly added to the spec.
 2. If all sources fail, raise a `RuntimeError` with a clear message indicating the data source failure.
 3. Do NOT generate synthetic data.
 **Output**: Write raw data to `data/raw/reddit_threads.jsonl` and `data/processed/download_attempts.log`.

- [X] T008c [S] [US1] **Record Checksums**: Compute a cryptographic checksum of `data/raw/reddit_threads.jsonl` and record it in `state/projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml` under `artifact_hashes`.

---

## Phase 2.5: Sentiment Tool Validation (Independent of Data Download)

**Purpose**: Validate VADER sentiment tool against human annotations (Constitution Principle VII). Runs independently of data download to ensure tool readiness.

- [X] T007a-1 [P] [US2] **Standard Test: VADER Sanity Check**.
 **Dependency**: None.
 **Logic**: Run VADER against the built-in NLTK VADER test suite (bundled with the library) to ensure scores fall within the standard normalized range.
 **Output**: `data/processed/vader_sanity_check.json` containing `status` (pass/fail), `min_score`, `max_score`.

- [X] T007a-2 [S] [US2] **Human-Annotated Corpus Validation**.
 **Dependency**: T007a-1.
 **Logic**:
 1. **Fetch Corpus**: Download the `cardiffnlp/twitter-sentiment-2018` from HuggingFace (split: 'train').
 2. **Verification**: Compute Cohen's Kappa between VADER scores and human annotations on the sample. [UNRESOLVED-CLAIM: c_612f7427 — status=not_enough_info]
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
 **Dependency**: T008.
 **Action**: Implement `code/data/sentiment.py` to integrate `langdetect` library. Process each comment in `data/raw/reddit_threads.jsonl`. Filter out comments where the detected language is not 'en'.
 **Justification**: {{claim:c_3c912d3b}} (Wikidata Q37573478, https://www.wikidata.org/wiki/Q37573478) Filtering is an implementation optimization authorized by Assumption 6 (CPU feasibility) and does not constitute scope reduction. [UNRESOLVED-CLAIM: c_74e8428b — status=not_enough_info]
 **Input**: `data/raw/reddit_threads.jsonl`.
 **Output**: Write filtered data to `data/raw/reddit_threads_english.jsonl` and log excluded thread IDs to `data/processed/lang_filter.log`.
 **Constraint**: This task runs BEFORE T009 (Extraction) to ensure only English content is processed.

---

## Phase 3: User Story 1 - Data Collection, Ground Truth, and Extraction (Priority: P1) 🎯 MVP

**Goal**: Download data, classify ground truth availability, and extract threads.

**Independent Test**: Can be fully tested by running the data extraction script against a sample of threads from r/AskScience and verifying that each thread has a sufficient number of seed posts extracted with valid timestamps and author IDs, and that the total dataset spans ≥2 subreddits and ≥1 site.

### Implementation for User Story 1

- [ ] T010 [S] [US1] **Generate Exclusion Log**: Implement `code/data/extract.py` to identify threads with <3 top-level posts and write them to `data/processed/exclusions_seed.log`.
 **Dependency**: T008.
 **Input**: Read RAW data from `data/raw/reddit_threads.jsonl`.
 **Logic**: Filter threads with <3 top-level posts. Log `thread_id` and reason code `SEED_INSUFFICIENT`.
 **Output**: Write `data/processed/exclusions_seed.log`.

- [X] T009 [S] [US1] **Depends on T008, T010, T071**: Implement `code/data/extract.py` to identify threads with decision points and extract the first N=3 top-level posts as seed posts from the *filtered* dataset (threads that passed the seed count filter).
 **Dependency**: T008, T010, T071.
 **Input**: Read input from `data/raw/reddit_threads_english.jsonl` (output of T071). Apply the exclusion filter defined by T010 by reading `data/processed/exclusions_seed.log` to identify threads to skip. **Merge the exclusion list with the filtered dataset to ensure correct filtering.**
 **Action**: Compute `reply_count` for each thread and include it in the output.
 **Output**: Write `data/processed/threads_with_seeds.csv`.

- [X] T019 [S] [US1] **Depends on T009, T010, T071**: Implement `code/data/validation.py` to validate ground-truth availability (FR-009).
 **Dependency**: T009, T010, T071.
 **Logic**:
 1. For Stack Exchange threads: Classify as 'valid' if an 'accepted_answer_id' exists.
 2. For Reddit threads: Classify as 'valid_no_gt' (valid for dataset inclusion, but no ground truth for external validation) as per Assumption 2.
 **Constraint**: Do NOT exclude Reddit threads from the dataset; include them with the 'valid_no_gt' flag to satisfy FR-001 (≥2 subreddits).
 **Output**: Write `data/processed/valid_threads.csv` (only 'valid' threads) and `data/processed/all_threads_classified.csv` (all threads with classification).

- [X] T019a [S] [US1] **Depends on T009, T019, T010, T071**: Implement `code/data/validation.py` to **compute the external validation score** (accuracy of consensus vs. ground truth) for valid threads.
 **Dependency**: T009, T019, T010, T071.
 **Logic**: Calculate accuracy of consensus (majority vote) against ground truth for valid threads. [UNRESOLVED-CLAIM: c_79abec4a — status=not_enough_info]
 **Consensus Definition**: For Stack Exchange, consensus is the 'accepted_answer_id'. For Reddit, set `external_validation_score` to `null` and log the reason as 'No External Ground Truth'.
 **Input**: Merge data from T009 (seed posts) and T019 (ground truth classification). Iterate over ALL threads in `data/processed/all_threads_classified.csv`.
 **Output**: Append `external_validation_score` to `data/processed/valid_threads.csv` (for valid threads) and `data/processed/all_threads_classified.csv` (for all threads, setting null for 'valid_no_gt').
 **Constraint**: This task runs on the full classified dataset, explicitly handling 'valid_no_gt' threads by setting their score to null.

- [X] T019b [S] [US1] **Depends on T009, T019, T019a, T010, T071**: Implement `code/data/validation.py` to check if valid threads < 30% of the **ANALYZABLE DATASET**.
 **Dependency**: T009, T019, T019a, T010, T071.
 **Source**: Read `total_analyzable_count` DIRECTLY from `data/processed/threads_with_seeds.csv` (output of T009, **after** T071 and T010 filtering) to ensure the denominator represents the true analyzable dataset. Read `valid_thread_count` from `data/processed/all_threads_classified.csv` (T019 output).
 **Logic**: Calculate `valid_thread_percentage = (count(valid) / count(total_analyzable_threads)) * 100`.
 **Constraint**: Generate `data/processed/ground_truth_stats.json` first containing `analyzable_dataset_count`, `valid_dataset_count`, and `valid_thread_percentage`. THEN check if `valid_thread_percentage < 30`. If <30, log a warning indicating that the study validity threshold (SC-006) is not met, set `status: warning`, and DO NOT raise a RuntimeError. The pipeline MUST continue to allow downstream analysis and reporting. **CRITICAL**: Generate `data/processed/sc_006_compliance_report.json` with a definitive `status: pass` or `status: fail` and the calculated percentage. This artifact serves as the mandatory evidence for the study's validity check.
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
 **Dependency**: T071, T007b.
 **Constraint**: This task runs on the English-filtered dataset (output of T071). Dependency on T007b ensures validation ran (and passed or logged a warning).

- [X] T087 [S] [US2] **Refine Contagion Delta Calculation**: Implement a robust linear regression routine in `code/data/metrics.py` that explicitly handles the "slope of sentiment vs. position" definition. Ensure the regression uses the *first 20* replies for the primary set and *all available* replies for the secondary set, as defined in T015b. Add a unit test `test_contagion_delta_calculation` in `code/tests/test_metrics.py` to verify the slope calculation against a known synthetic dataset.
 **Rationale**: Clarifies the mathematical definition of "delta" to prevent implementation ambiguity.
 **Dependency**: T013.

- [X] T015a [S] [US2] **Depends on T013, T019, T010, T071**: Implement `code/data/metrics.py` to compute the emotional contagion index (Part 1: Filtering).
 **Dependency**: T013, T019, T010, T071.
 **Input**: Use the *filtered* dataset (valid + valid_no_gt threads, seed posts extracted). **Join `threads_with_seeds.csv` (T009) with `all_threads_classified.csv` (T019) to filter based on ground truth status.**
 **Logic**:
 1. **Filter**: Select threads where `reply_count >= 5`.
 2. **Primary Set**: Select threads with `reply_count >= 20` for the fixed-window contagion index calculation (as per Plan and Spec).
 3. **Secondary Set**: Select threads with `5 <= reply_count < 20` for the 'available replies' calculation.
 4. **Exclusion**: Log the count of threads excluded due to `reply_count < 5` with reason code `REPLY_COUNT_INSUFFICIENT`.
 **Constraint**: Strictly exclude threads with <5 replies from all contagion analysis. Include threads with 5-19 replies in the Secondary Set.

- [X] T015b [S] [US2] **Depends on T015a, T087**: Implement `code/data/metrics.py` to compute the emotional contagion index (Part 2: Calculation) **AND Confidence Intervals**.
 **Dependency**: T015a, T087.
 **Logic**:
 1. **Performance Guardrail**: Estimate runtime based on thread count. If estimated runtime > 5 hours, reduce bootstrap resamples from 1000 to 500 **before** execution.
 2. **Primary Set (>=20)**: For threads with `reply_count >= 20`, calculate the **change in sentiment (delta)** of subsequent replies over the **initial set of comments**. **Delta is defined as the slope of the linear regression of sentiment score vs. reply position across the initial range of replies.**. Compute the Pearson correlation between the seed-post sentiment and this **delta**.
 3. **Secondary Set (5-19)**: For threads with `5 <= reply_count < 20`, calculate the **change in sentiment (delta)** over the **available replies** (1 to N, where N = reply_count). Compute the Pearson correlation between the seed-post sentiment and this **delta**.
 4. **Confidence Intervals**: For each thread, compute confidence intervals for the Pearson correlation using bootstrapping with **method=percentile**, **resamples=1000**, and **seed=42**.
 **Constraint**: Threads with <5 replies are excluded (handled by T015a). **Do NOT use a variable window** for the Primary Set, but use the **available window** for the Secondary Set.
 **Output**: Append results to `data/processed/thread_metrics.csv` with columns [thread_id, contagion_index, reply_count_used, window_type, confidence_interval_low, confidence_interval_high].

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Decision Quality Metrics and Statistical Modeling (Priority: P3)

**Goal**: Compute decision quality metrics, fit GLMMs, and perform sensitivity analysis.

**Independent Test**: Can be tested by running the statistical modeling pipeline on a sample dataset of threads and verifying that GLMMs converge, p-values are computed, and multiple-comparison correction is applied when ≥3 tests are run.

### Implementation for User Story 3

- [X] T018 [S] [US3] Implement `code/data/metrics.py` to compute decision quality metrics: (a) agreement proportion, (b) Shannon entropy for diversity, (c) external validation score (read from T019a output), and (d) efficiency metrics (time-to-decision, thread length).
 **Dependency**: T019a.
 **Input**: Read external validation score from `data/processed/valid_threads.csv`.

- [X] T030 [S] [US3] **Collinearity Diagnostics**: Implement `code/data/modeling.py` to compute Variance Inflation Factor (VIF) for predictors (sentiment, thread length, time-to-decision, external_validation_score).
 **Requirement**: Compute VIF scores and output them to `data/processed/collinearity_diagnostics.json`.
 **Dependency**: T019a, T015b.

- [X] T091 [S] [US3] **Collinearity Threshold Alert**: In `code/data/modeling.py`, if any VIF score (from T030) exceeds 5.0, log a warning with the specific predictor names and recommend excluding the most collinear variable from the final model.
 **Dependency**: T030.

- [X] T088 [S] [US3] **Implement Beta Regression Link Function Validation**: In `code/data/modeling.py`, add a pre-check for the beta regression model to ensure the response variable (agreement proportion) strictly lies within (0, 1). If values are exactly 0 or 1, apply a standard transformation (e.g., `y' = y * (n-1) + 0.5) / n`) to avoid logit/link function errors. Log these transformations.
 **Rationale**: Beta regression requires bounded (0,1) data; real-world proportions may hit boundaries, causing model failure.
 **Dependency**: T018.

- [X] T089 [S] [US3] **Add Model Convergence Timeout**: In `code/data/modeling.py`, wrap GLMM fitting in a timeout mechanism (e.g., using `signal` or `concurrent.futures`) with a 5-minute limit per thread. If a model fails to converge within the timeout, log the thread ID as `MODEL_TIMEOUT` and skip it, rather than hanging the entire pipeline.
 **Rationale**: Prevents the pipeline from stalling on a single non-converging thread, ensuring the 6-hour runtime constraint (SC-005) is met.
 **Dependency**: T018.

- [X] T020 [S] [US3] **Depends on T019a, T015b, T030, T088, T089**: Implement `code/data/modeling.py` to fit Generalized Linear Mixed Models (GLMM) with **thread-level random intercepts**. Use **beta regression** for bounded outcomes (agreement proportion). For time-to-decision (continuous duration), **select an appropriate distribution (e.g., Gamma or Log-Normal) based on residual diagnostics (AIC/BIC)** and use the corresponding link function. **Include the external validation score as a predictor** in the model where applicable.
 **Dependency**: T019a, T015b, T030, T088, T089.
 **Constraint**:
 1. **Override Plan.md**: Use **Random intercept: Thread ID** (not Subreddit) to match Spec FR-006, overriding the initial plan suggestion for 'Subreddit'. Document this override with a comment referencing Spec FR-006.
 2. **Convergence Check**: Explicitly check for GLMM convergence warnings. Wrap model fitting in a try/except block catching `statsmodels.tools.sm_exceptions.ConvergenceWarning` and `RuntimeError`. If a model fails to converge, log the thread ID, the specific error, and exclude it from the final results set with a reason code `MODEL_NON_CONVERGENCE`. Do not force convergence or remove constraints to make the test pass.
 **Input**: Join `valid_threads.csv` and `thread_metrics.csv` on `thread_id`.
 **Output**: Model outputs and diagnostic information will be stored as files in the data/processed directory.

- [X] T021 [S] [US3] Implement significance testing in `code/data/modeling.py`: Wald tests (α=0.05) for contagion coefficients.

- [X] T022 [S] [US3] Implement multiple-comparison correction in `code/data/modeling.py`: Apply Bonferroni or Benjamini-Hochberg FDR when ≥3 hypothesis tests are run (FR-007).

- [X] T023a [S] [US3] **Split Task 1**: Implement FP/FN Calculation in `code/data/metrics.py`.
 **Dependency**: T019a.
 **Input**: Read `data/processed/valid_threads.csv` (T019a).
 **Logic**: Calculate and report False Positive and False Negative rates of Consensus vs. Ground Truth for valid threads.
 **Output**: Intermediate FP/FN data.

- [X] T023b [S] [US3] **Split Task 2**: Implement Correlation Analysis in `code/data/metrics.py`.
 **Dependency**: T019a, T015b.
 **Input**: Read `data/processed/valid_threads.csv` and `data/processed/thread_metrics.csv`.
 **Logic**: Compute the Pearson correlation between contagion index and (1) agreement proportion, (2) Shannon entropy, and (3) external validation score for each sweep (agreement cutoff **{0.5, 0.6, 0.7}** and entropy threshold **{0.2, 0.4, 0.6}**).
 **Constraint**: Generate a **FULL grid report**. Iterate over the full Cartesian product of thresholds: Agreement x Entropy. If no data exists for a combination, **explicitly write a row** to `sensitivity_analysis.csv` with the threshold values and a `status` field set to "No data" or similar, rather than omitting the row. Partial results are not permitted.
 **Output**: Write `data/processed/sensitivity_analysis.csv`.

- [X] T023c [S] [US3] **Split Task 3**: Generate Trend Summary in `code/data/modeling.py`.
 **Dependency**: T023b.
 **Input**: Read `data/processed/sensitivity_analysis.csv`.
 **Logic**: Generate a deterministic `trend_summary` text description for the primary metric (contagion vs. agreement).
 **Output**: Append `trend_summary` to `data/processed/sensitivity_analysis.csv`.

- [X] T024 [S] [US3] **Depends on T019a, T015b**: Implement correlation analysis in `code/data/modeling.py`: Compute the correlation between the external validation score and the contagion index/decision quality metrics.
 **Dependency**: T019a, T015b.
 **Input**: Read external validation score from `data/processed/valid_threads.csv` and contagion index from `data/processed/thread_metrics.csv`.
 **Output**: Output results to `data/processed/external_validation_correlation.csv`.

- [X] T024a [P] [US3] Create integration tests in `code/tests/test_modeling.py` to verify GLMM convergence and correction application.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [S] **Review Fix**: Ensure `code/data/download.py` implements a strict "fail-loud" policy for data fetching: Remove any `try/except` blocks that fall back to `generate_synthetic_*()` or mock data.
 **Logic**: If the primary Pushshift API, Reddit API, and Internet Archive/Common Crawl all fail, raise a RuntimeError with a clear message indicating the exact failure point.

- [X] T032 [S] **Review Fix**: Update `code/data/metrics.py` to explicitly state the streaming/sampling rule in comments and logs: specify the exact split used, chunking strategy (if any), and the number of rows processed.

- [X] T041 [S] **Review Fix**: Generate Sampling Strategy Log.
 **Action**: Create `data/processed/sampling_strategy_log.json` documenting the exact sampling rules (if any) used for dataset subsets, including the random seed, sample size, and representativeness limitations.

- [X] T042 [S] **Review Fix**: Generate Fail-Loud Verification Log.
 **Action**: Create `data/processed/fail_loud_verification_log.json` documenting the results of simulated failure condition triggers (e.g., using `unittest.mock` to simulate API 500 errors) to confirm that `RuntimeError` is raised and the pipeline halts as expected.

- [X] T025 [S] **Review Fix**: Run full pipeline on up to N=500 threads and verify completion within 6 hours on CPU-only runner (SC-005).
 **Requirement**: Implement a runtime check that raises an error or flags a `status: failure` if the total runtime exceeds a predefined maximum duration threshold.

- [X] T086 [S] [US3] **Add Power Analysis Documentation**: Create `docs/paper.md` section "Power Analysis" to explicitly state the sample size (N=500 threads) and acknowledge the limitation if N < 100 threads (Assumption 5). Include a calculation or reference for the statistical power of the GLMM given the sample size and expected effect sizes. [UNRESOLVED-CLAIM: c_f034e8b4 — status=not_enough_info]
 **Dependency**: T019a, T015b.
 **Output**: Updated `docs/paper.md`.

- [X] T026 [S] **Review Fix**: Generate final report in `docs/paper.md` including SC-006 pass/fail status, ground truth percentage, model results, and the correlation analysis between external validation score and decision quality.
 **Dependency**: T086, T023c, T020.

- [X] T029 [S] **Review Fix**: Create/Overwrite `docs/quickstart.md` with execution instructions for the full pipeline.

- [X] T033 [S] **Review Fix**: Generate Sampling Strategy Log.
 **Action**: Document streaming rules in comments and logs.

- [X] T034 [S] **Review Fix**: Ensure `docs/paper.md` includes a "Data Availability" section with a direct link to the `data/raw/reddit_threads.jsonl` checksum and the `state/artifact_hashes` map, ensuring full reproducibility.

- [X] T035 [S] **Review Fix**: Verify that the VADER sentiment analysis in T013 correctly handles multi-lingual content, as the dataset may contain non-English threads.

- [X] T036 [S] **Review Fix**: Ensure the final report (T026) includes a "Limitations" subsection specifically addressing the potential bias introduced by the exclusion of threads with <5 replies.

- [X] T092 [S] [Polish] **Generate Reproducibility Manifest**: Create a script `code/scripts/generate_manifest.py` that aggregates all checksums from `state/`, the `requirements.txt` hash, and the git commit hash into a single `reproducibility_manifest.json`. Run this as the final step of the pipeline.
 **Rationale**: Ensures a single, verifiable artifact for the entire research run, satisfying Principle V (Versioning Discipline).

---

## Phase 9: Final Review & Revision (Pending)

**Purpose**: Address any remaining concerns from the analysis phase or manual review.

- [X] T078 [S] **Review Fix**: Add confidence interval stability checks to tests.
 **Action**: Implement tests to verify that confidence intervals are stable with varying bootstrap resamples.

- [X] T079 [S] **Review Fix**: Update data contracts for new fields.
 **Action**: Add definitions for `thread_count`, `ground_truth_status`, and `convergence_status` to the schema.

- [X] T080 [S] **Review Fix**: Finalize memory profiling documentation.
 **Action**: Include detailed memory usage estimates in `docs/quickstart.md`.

- [X] T082 [S] **Review Fix**: Strengthen data source verification.
 **Action**: Update `code/data/download.py` to strictly enforce the use of verified real data sources.
 **Mechanism**: Check for environment variable `VERIFIED_DATA_SOURCE` or config key `verified_data_recipe`. If present, the code MUST adopt that exact package/recipe and remove any hand-rolled URLs or guessed IDs. Ensure no fallback to synthetic data exists.

- [X] T083 [S] **Review Fix**: Validate Ground Truth Threshold Logic.
 **Action**: Review T019b logic to ensure the 30% threshold check (SC-006) is applied against the *analyzable dataset* count (post-filtering), not the raw count. Ensure the pipeline continues with a warning if the threshold is not met, rather than failing, as per the spec requirement to report the failure rather than pivot.

- [X] T094 [S] **Amend Plan.md**: Update `projects/PROJ-139-the-influence-of-emotional-contagion-on-/specs/001-emotional-contagion-decisions/plan.md` to formally change the random intercept specification from 'Subreddit' to 'Thread ID' in Phase 3, aligning the plan with Spec FR-006 and the implementation in T020.
 **Dependency**: T019c.
 **Rationale**: Resolves the direct contradiction between Plan.md and Spec FR-006.

---

## Phase 10: Analysis-Driven Revisions (Mode B Resolution)

**Purpose**: Tasks generated to resolve specific findings from `/speckit.analyze` that were not addressed in the initial plan or required clarification.

(No tasks remaining in this phase; all fixes have been integrated into earlier phases.)
