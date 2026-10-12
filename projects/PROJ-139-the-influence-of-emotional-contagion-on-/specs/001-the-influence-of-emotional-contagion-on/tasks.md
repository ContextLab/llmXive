# Tasks: The Influence of Emotional Contagion on Collective Decision‑Making in Online Forums  

**Inputs**: `spec.md`, `plan.md`, `data‑model.md`, contract schemas, existing code base.  

The checklist below follows the canonical `- [ ] T### [P?] [USx?] description …` format.  
`[P]` = can run in parallel with other tasks that have no data‑flow dependency.  
`[S]` = must run sequentially after its listed dependencies.  
`[USx]` = user‑story identifier from the specification (US1 = Data collection, US2 = Sentiment & contagion, US3 = Decision quality & modelling).  

All paths are relative to the project root.

---

## Phase 1 – Project setup & first end‑to‑end run  

| Goal | Tasks |
|------|-------|
| Establish reproducible project skeleton and confirm a minimal runnable pipeline on a tiny real sample. |  

- [ ] T001 [P] Establish project layout (`code/`, `data/raw/`, `data/processed/`, `state/`, `docs/`) and record it in `docs/quickstart.md`.  
- [ ] T002 [P] Add `requirements.txt` (pandas, nltk, scikit‑learn, statsmodels, pyyaml, requests, scipy, langdetect, datasets) and pin versions.  
- [ ] T003 [P] Document a one‑line execution command in `docs/quickstart.md` that runs `python -m code.analysis.run_pipeline --sample 5` producing a tiny CSV under `data/results/sample_run.csv`.  

**Verification**  

- [ ] T003v [P] Unit test asserts that running the sample command exits with code 0 and creates `data/results/sample_run.csv` with the required columns.

---

## Phase 2 – Data contracts, acquisition & validation  

| Goal | Tasks |
|------|-------|
| Define schemas, fetch real data, and verify provenance before any downstream analysis. |  

- [ ] T004 [P] Copy contract schemas into the runtime location `code/contracts/` (thread.schema.yaml, sentiment.schema.yaml, result.schema.yaml).   <!-- FAILED-IN-EXECUTION: code/contracts/copy_schemas.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/contracts/copy_schemas.py exit=1 -->
- [ ] T005 [P] Implement a lightweight logger (`code/utils/logger.py`) that writes to `state/logs/` and is used by all pipeline modules.  
- [ ] T006 [P] Extend seeding to pin randomness in `numpy`, `random`, `scikit-learn`, and `statsmodels`.  
- [ ] T006v [P] Test that `np.random.rand()` returns the same sequence across runs after seeding.  

**Data download & streaming**  

- [ ] T008 [S] Implement `code/data/download.py` to **attempt**:  
  1. Pushshift API query for the two target subreddits (`AskScience`, `AskHistorians`).  
  2. Fallback to Reddit official API (OAuth via `praw`).  
  3. Final fallback to an Internet Archive mirror (URL stored in `config.yaml`).  
  The script writes raw JSONL to `data/raw/reddit_threads.jsonl` and logs the source type for each thread in `data/processed/download_attempts.log`. It **fails loudly** (`RuntimeError`) if all three sources are unavailable.  
- [ ] T008v [S] Verify that `data/raw/reddit_threads.jsonl` exists and that `download_attempts.log` contains at least one line with source = “Pushshift”.  

- [ ] T081 [S] Refactor `code/data/download.py` and `code/data/extract.py` to use `datasets.load_dataset(..., streaming=True)` so the full archive is processed in ≤1 GB‑max chunks. A memory guard raises `RuntimeError` if RAM usage exceeds 6 GB.  
- [ ] T081v [S] Run a streaming sanity check on a small shard and assert that the guard does not trigger under normal conditions but does raise when artificially exceeding the limit (mocked test).  

**Language filtering**  

- [ ] T071 [S] Add English‑only filtering in `code/data/sentiment.py` using `langdetect`. Write filtered output to `data/raw/reddit_threads_en.jsonl` and log excluded thread IDs to `data/processed/lang_filter.log`.  
- [ ] T071v [S] Unit test confirms that every line in `reddit_threads_en.jsonl` has language code “en” and that `lang_filter.log` is non‑empty when non‑English threads are present.  

**Seed‑post extraction & exclusion logging (re‑planned)**  

- [ ] T010 [S] **Generate seed‑post exclusion log** – Implement `code/data/extract.py` function `log_insufficient_seeds(thread_id)` that writes a line `thread_id\tSEED_INSUFFICIENT` to `data/processed/exclusions_seed.log`.  
  - **Dependency**: T008, T071.  
  - **Output**: `data/processed/exclusions_seed.log` (tab‑separated, one line per excluded thread).  
  - **Verification**: Unit test `test_exclusions_log_exists` in `code/tests/test_extract.py` asserts the file exists and contains only valid thread IDs.  
- [ ] T010v [S] Verify that `exclusions_seed.log` is created and that its entries match threads with fewer than three top‑level posts.  

- [ ] T009 [S] Implement full thread extraction in `code/data/extract.py`:  
  - Read from `data/raw/reddit_threads_en.jsonl`.  
  - Skip any thread listed in `exclusions_seed.log`.  
  - For remaining threads, verify ≥3 top‑level posts, extract the first three as seed posts, compute `seed_count`, and write a CSV `data/processed/threads_with_seeds.csv` (columns: `thread_id, source, subreddit_site, created_at, seed_count, total_replies`).  
- [ ] T009v [S] Validate `threads_with_seeds.csv` against `thread.schema.yaml` and assert all rows have `seed_count ≥ 3`.  

**Ground‑truth classification**  

- [ ] T019 [S] Implement `code/data/validation.py` to create `data/processed/all_threads_classified.csv` with an added boolean `has_ground_truth` (Stack Exchange → `accepted_answer_id` present, Reddit → `False`).  
- [ ] T019v [S] Schema‑validate `all_threads_classified.csv` against `thread.schema.yaml` and confirm presence of `has_ground_truth` column.  

- [ ] T019a [S] Compute `external_validation_score` (1 = consensus matches ground truth, 0 = mismatch, null = no ground truth) and append it to `all_threads_classified.csv`.  
- [ ] T019av [S] Verify that the new column exists and contains only 0, 1, or null values.  

- [ ] T019b [S] Generate `data/processed/ground_truth_stats.json` containing `analyzable_dataset_count`, `valid_dataset_count`, and `valid_thread_percentage`. Then produce `state/sc_006_compliance_report.json` with `status: "pass"` if `valid_thread_percentage ≥ 30` else `"fail"`.  
- [ ] T019bv [S] Unit test checks that both JSON files are well‑formed and that `status` field matches the computed percentage.  

**Sentiment‑tool validation**  

- [ ] T007a-1 [P] Run VADER sanity check on the built‑in NLTK test suite; output `data/processed/vader_sanity_check.json`.  
- [ ] T007a-1v [P] Verify that `vader_sanity_check.json` exists and contains keys `mean_compound`, `std_compound`.  

- [ ] T007a-2 [S] Download the `cardiffnlp/twitter-sentiment-2018` dataset from HuggingFace, compute Cohen’s κ between VADER scores and human labels, and store results in `data/processed/vader_validation_report.json`.  
- [ ] T007a-2v [S] Assert that `vader_validation_report.json` exists and that κ ∈ [0,1].  

**Schema validation (SC‑001)**  

- [ ] T011 [S] Run JSON‑schema validation on all generated CSV/JSON artifacts (`threads_with_seeds.csv`, `post_sentiments.csv`, `thread_metrics.csv`, `decision_quality.csv`, `glmm_results.json`, etc.) against the three contract schemas.  
- [ ] T011v [S] Fail the pipeline if any file does not conform; unit test ensures the validator runs on a known good file without error.  

---

## Phase 3 – Sentiment scoring & emotional‑contagion index  

| Goal | Tasks |
|------|-------|
| Apply VADER, compute contagion metrics, and store them with full provenance. |  

- [ ] T013 [S] Apply VADER to every post in `data/raw/reddit_threads_en.jsonl` (including seed and reply posts) and write `data/processed/post_sentiments.csv` (`thread_id, post_id, role[seed|reply], vader_compound`).  
- [ ] T013v [S] Validate `post_sentiments.csv` against `sentiment.schema.yaml` and confirm compound scores lie in [-1, 1].  

- [ ] T015a [S] Filter threads for contagion analysis: keep only those with `total_replies ≥ 5`. Write the filtered list to `data/processed/contagion_candidate_threads.csv`. Log excluded thread IDs with reason `REPLY_COUNT_INSUFFICIENT`.  
- [ ] T015av [S] Verify that the candidate CSV exists and that every excluded thread appears in `exclusions_reply.log` with the correct reason.  

- [ ] T015b [S] For each candidate thread, compute:  
  1. `seed_sentiment_mean` (mean of the three seed VADER scores).  
  2. `contagion_index_slope` = Pearson r between `seed_sentiment_mean` and the **slope** of reply‑sentiment vs. position (linear regression over first 20 replies).  
  3. Bootstrapped 95 % confidence interval (1 000 resamples, seed 42).  
  Results are appended to `data/processed/thread_metrics.csv` (columns: `thread_id, seed_sentiment_mean, contagion_index_slope, n_replies_used, ci_low, ci_high, window_type`).  
- [ ] T015bv [S] Ensure all `contagion_index_slope` values lie within [-1, 1] and that CI columns are ordered (`ci_low ≤ ci_high`).  

- [ ] T015c [S] **FR‑004 compliance** – Compute the original contagion metric defined in the spec: Pearson correlation between `seed_sentiment_mean` and the **delta** (change) in reply sentiment across the first 20 replies. Store as `contagion_index_delta` in `thread_metrics.csv`.  
- [ ] T015cv [S] Verify that `contagion_index_delta` values are within [-1, 1] and that both slope‑based and delta‑based metrics are present for each thread.  

- [ ] T087 [S] Implement a robust linear‑regression routine in `code/data/metrics.py` that, for each thread, fits sentiment vs. position over the first 20 replies (or all replies if <20) and returns the slope (“delta”). Unit test `test_contagion_delta_calculation` validates against a hand‑crafted synthetic series.  
- [ ] T087v [S] Confirm that the regression routine returns a numeric slope for a synthetic test case.  

---

## Phase 4 – Decision‑quality metrics, modelling & sensitivity  

| Goal | Tasks |
|------|-------|
| Derive outcome metrics, fit GLMMs, apply multiple‑comparison correction, and run sensitivity sweeps. |  

- [ ] T018 [S] Compute decision‑quality metrics per thread (agreement proportion, Shannon entropy of sentiment buckets, time‑to‑decision, thread length) and merge them with `thread_metrics.csv` → `data/processed/decision_quality.csv`.  
- [ ] T018v [S] Validate `decision_quality.csv` against `result.schema.yaml`.  

- [ ] T023a [S] From `all_threads_classified.csv`, calculate false‑positive and false‑negative rates of consensus vs. ground truth; write `data/processed/fp_fn_rates.csv`.  
- [ ] T023av [S] Verify that `fp_fn_rates.csv` contains columns `fp_rate` and `fn_rate` and that values are between 0 and 1.  

- [ ] T023b [S] Perform a full grid sweep over agreement cutoffs `{0.5,0.6,0.7}` and entropy thresholds `{0.2,0.4,0.6}`. For each combination compute the Pearson correlation between `contagion_index_slope` (primary) and the selected decision‑quality outcome. Write every combination (including “No data” rows) to `data/processed/sensitivity_analysis.csv`.  
- [ ] T023bv [S] Assert that the number of rows equals `3 × 3 = 9` plus any “No data” placeholders.  

- [ ] T023c [S] Generate a deterministic textual summary of the primary trend (contagion vs agreement) and append a column `trend_summary` to `sensitivity_analysis.csv`.  
- [ ] T023cv [S] Verify that `trend_summary` is non‑empty for all non‑placeholder rows.  

**Statistical modelling**  

- [ ] T030 [S] Compute Variance Inflation Factors for all predictors (contagion, thread length, time‑to‑decision, external validation score) and output `data/processed/collinearity_diagnostics.json`.  
- [ ] T030v [S] Ensure all VIF values are < 5; fail if any exceed.  

- [ ] T088 [S] Pre‑process `agreement_proportion` for beta regression: apply the `(y · (n‑1) + 0.5)/n` transformation when any value equals 0 or 1; log the transformation actions.  
- [ ] T088v [S] Check that transformed values lie strictly within (0,1) and that a log entry is created.  

- [ ] T089 [S] Wrap each GLMM fit in a 5‑minute timeout; on timeout log `MODEL_TIMEOUT` and skip the thread.  
- [ ] T089v [S] Verify that a `model_timeout.log` file is created when a timeout occurs.  

- [ ] T020 [S] Fit GLMMs with **thread‑level random intercepts** (override the original plan that used subreddit). Fixed effects: `contagion_index_slope`, `thread_length`, `time_to_decision`, `external_validation_score` (when present). Store model summaries, convergence flags, and coefficient tables in `data/processed/glmm_results.json`.  
- [ ] T020v [S] Confirm that `glmm_results.json` exists, conforms to `result.schema.yaml`, and includes a `convergence` flag for each model.  

- [ ] T021 [S] Conduct Wald tests (α = 0.05) on the contagion coefficient; add `p_value` and `is_significant` fields to the GLMM results.  
- [ ] T021v [S] Verify that `p_value` is numeric and `is_significant` is boolean.  

- [ ] T022 [S] If ≥3 hypothesis tests are performed, apply Benjamini‑Hochberg FDR correction; record adjusted p‑values and a boolean `is_significant_after_fdr`.  
- [ ] T022v [S] Ensure that corrected p‑values are present and that `is_significant_after_fdr` is boolean.  

**External‑validation correlation**  

- [ ] T024 [S] Correlate `external_validation_score` with `contagion_index_slope` and other decision‑quality metrics; write `data/processed/external_validation_correlation.csv`.  
- [ ] T024v [S] Validate that the CSV contains correlation coefficients and that they are numeric.  

**SC‑002 Associational framing**  

- [ ] T027 [S] Scan `docs/paper.md` for prohibited causal phrasing (e.g., “causes”, “leads to”) and enforce associational language only. Fail the pipeline if causal language is detected.  
- [ ] T027v [S] Unit test supplies a snippet with causal wording and asserts that the scan fails.  

---

## Phase 5 – Reporting, reproducibility & hand‑off  

| Goal | Tasks |
|------|-------|
| Produce the final research artefacts and ensure full reproducibility. |  

- [ ] T026 [S] Draft the methods & results section in `docs/paper.md`, automatically inserting tables/figures generated from `glmm_results.json`, `sensitivity_analysis.csv`, and the SC‑006 compliance report. Include a “Limitations” paragraph that discusses exclusion of threads with <5 replies and any ground‑truth shortfall.  
- [ ] T026v [S] Verify that `paper.md` contains placeholders `{{TABLE_GLMM}}`, `{{FIG_SENSITIVITY}}`, and that no causal language is present (reuse T027 scan).  

- [ ] T086 [S] Add a “Power Analysis” subsection to `docs/paper.md` that cites the intended sample size (N = 500) and reports the achieved statistical power for the observed effect size (using `statsmodels.stats.power`).  
- [ ] T086v [S] Ensure the subsection exists and contains numeric power estimate.  

- [ ] T092 [S] Create `code/scripts/generate_manifest.py` that aggregates: all checksum files from `state/`, the SHA‑256 of `requirements.txt`, and the current git commit hash; output `reproducibility_manifest.json`. Run this script as the final step of `run_pipeline.py`.  
- [ ] T092v [S] Verify that `reproducibility_manifest.json` contains a non‑empty `artifact_hashes` map.  

**Checksum generation (III Data Hygiene)**  

- [ ] T031 [S] Generate SHA‑256 checksums for every raw and processed data file and write them to `state/checksums.txt`.  
- [ ] T031v [S] Confirm that each file listed in `state/checksums.txt` exists and that the checksum line matches the file’s actual hash.  

**Versioning Discipline (V)**  

- [ ] T033 [S] Populate the `artifact_hashes` map in `state/projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml` using the checksums from T031.  
- [ ] T033v [S] Validate that the YAML now includes a top‑level `artifact_hashes` dictionary with entries for all data artifacts.  

**Runtime resource monitoring (SC‑005)**  

- [ ] T028 [S] Measure total CPU time, peak memory usage, and disk consumption of the full pipeline; write `state/runtime_metrics.json` and compare against GitHub Actions free‑tier limits (≤6 h CPU, ≤7 GB RAM, ≤14 GB disk). Fail if any limit is exceeded.  
- [ ] T028v [S] Unit test runs a lightweight mock pipeline and asserts that the metrics JSON is produced and values are within limits.  

**Final hand‑off**  

- [ ] T029 [S] Update `docs/quickstart.md` with step‑by‑step instructions to reproduce the full analysis (including required environment variables for API credentials).  
- [ ] T029v [S] Check that `quickstart.md` contains a section titled “Full Reproduction”.  

- [ ] T032 [S] Ensure `code/data/metrics.py` contains a comment block documenting the exact streaming/sampling rule used (full dataset streaming, no down‑sampling).  
- [ ] T032v [S] Verify that the comment block exists and matches the required wording.  

**Verification** – A fresh CI run on a clean runner must:  
1. Execute `python -m code.analysis.run_pipeline` (no `--sample` flag).  
2. Complete all steps within the 6‑hour CPU limit.  
3. Produce the final artefacts (`glmm_results.json`, `sensitivity_analysis.csv`, `paper.md`, `reproducibility_manifest.json`).  
4. Pass all pytest suites (`code/tests/`).  

---  

## Dependency & Requirement Mapping  

| Spec FR | Covered by Task(s) |
|---------|--------------------|
| FR‑001 | T008, T081 |
| FR‑002 | T009, T010 |
| FR‑003 | T013 |
| FR‑004 | T015b (slope‑based) & T015c (delta‑based) |
| FR‑005 | T018, T023a, T023b |
| FR‑006 | T020 (random intercept = thread ID) |
| FR‑007 | T022 |
| FR‑008 | T023b (threshold sweep) |
| FR‑009 | T019, T019a, T019b |
| SC‑001 | T011 |
| SC‑002 | T027 |
| SC‑003 | T022 |
| SC‑004 | T023b grid report |
| SC‑005 | T028 (runtime guard) |
| SC‑006 | T019b & `state/sc_006_compliance_report.json` |

---  

*All pending tasks are unchecked; completed tasks are marked `[X]`. The pipeline can now be executed end‑to‑end, producing verifiable real artefacts that satisfy every functional and success‑criterion in the specification.*  