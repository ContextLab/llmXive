# Tasks: The Impact of Parasocial Relationships with AI Companions on Loneliness  

**Input**: `spec.md`, `plan.md`, `research.md`, `data‑model.md`, contract schemas.  

The list follows the canonical `- [ ] T### [P?] [USx?] description …` format.  
Tasks are ordered by scientific data‑flow; tasks that can run in parallel are marked **[P]**.

---

## Phase 0 – Project scaffolding  

- [ ] T001 [P] Create the required project directory tree and verify its existence.  
  - **Paths created**: `src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `docs/`, `contracts/`, `config/`.  
  - **Verification**: Run `tree -L 2 .` (or equivalent) and store the output in `docs/directory_structure.txt`; the file must list all nine top‑level folders.

- [ ] T002 Add the three contract schema files required by the specification and validate them.  
  - **Files**:  
    - `contracts/unified_dataset.schema.yaml` (matches *MatchedUsersDataset*).  
    - `contracts/model_output.schema.yaml` (matches *ModelResult*).  
    - `contracts/weekly_aggregates.schema.yaml` (matches *WeeklyAggregatesDataset*).  
  - **Verification**: Write a small script `src/utils/validate_schema.py` that loads each YAML with `jsonschema.validate` against a dummy instance; the script must exit with code 0 and produce `logs/schema_validation.log` confirming success.  
  - **Dependency**: Runs after T001 (now explicitly dependent).

- [ ] T020 [P] Set a global random seed (42) for all stochastic steps and record it in `config/random_seed.yaml`.  
  - **Verification**: Script `src/utils/set_seed.py` writes the seed file and asserts that `numpy`, `random`, and `torch` (if present) are seeded; downstream scripts import this utility.

- [ ] T018 [P] Compute SHA‑256 checksums for every raw and derived data artifact created throughout the pipeline and store them in `data/artifact_manifest.yaml`.  
  - **Verification**: `src/utils/checksum.py` generates the manifest; a subsequent verification step compares current file hashes to the manifest and fails if any mismatch is detected.

---

## Phase 1 – Data ingestion & user matching  

- [ ] T003 [P] Implement `src/ingest/download_loneliness.py` to fetch the **Reddit Loneliness Longitudinal Dataset** from its Zenodo DOI, validate required columns (`username_hash`, `UCLA_Loneliness_Score`, `timestamp`, `baseline_text`, `age`, `gender`), enforce ≥ 6 months of non‑null scores per user, and write `data/raw/loneliness_dataset.parquet`.  
  - **Verification**: Unit test `tests/unit/test_download_loneliness.py` asserts the parquet contains ≥ 600 rows, all required columns, and that each user has ≥ 6 distinct months with non‑null loneliness scores.

- [ ] T004 [P] Implement `src/ingest/fetch_pushshift.py` to retrieve AI‑companion interaction logs from the Pushshift API for subreddits `r/Replika`, `r/characterAI`, and `r/AICompanions`.  
  - **Requirements**:  
    1. Use the earliest and latest survey timestamps (from `loneliness_dataset.parquet`) to define the exact calendar window (strictly preceding each survey).  
    2. Apply exponential back‑off (max 5 retries, 30 s timeout) via `src/utils/retry_policy.py`.  
    3. Respect the API rate‑limit (≤ 100 req/min) using `src/utils/rate_limit_handler.py`.  
    4. **Exact query parameters**: `size=500`, and explicit `before`/`after` timestamps derived from the window.  
  - **Output**: `data/raw/pushshift_logs.parquet`.  
  - **Verification**: Integration test `tests/integration/test_fetch_pushshift.py` checks that the file exists, contains ≥ 1 M rows, that all timestamps lie inside the defined window, and that the request URLs contain `size=500` with correct `before`/`after` parameters.

- [ ] T016 [P] Verify that the Pushshift API calls made by `fetch_pushshift.py` conform to the required parameters (`size=500`, proper `before`/`after`).  
  - **Verification**: `src/validation/validate_pushshift_params.py` intercepts the request log, parses query strings, and aborts with “Pushshift Parameter Mismatch” if any deviation is found.

- [ ] T005 [P] Implement `src/match/user_match.py` to:  
  1. Load `loneliness_dataset.parquet` and `pushshift_logs.parquet`.  
  2. Hash raw Reddit usernames with SHA‑256 (UTF‑8, no salt) **in memory only**; never write the raw names to disk or logs.  
  3. Perform an inner join on the hashed IDs, dropping unmatched users.  
  4. **Exclude** any user whose `baseline_text` field is missing or empty (fulfilling FR‑009).  
  5. Write the anonymised, matched dataset to `data/processed/matched_users.parquet`.  
  - **Verification**: `tests/unit/test_user_match.py` asserts that the output file contains a `user_id` column matching the 64‑character hex pattern, that the match rate is ≥ 80 % of the original loneliness cohort, and that no record has a null `baseline_text`.

- [ ] T019 [P] Verify deterministic matching: ensure the hashing step is fully deterministic and that no random sampling occurs.  
  - **Verification**: `src/validation/verify_deterministic_match.py` runs the matching twice on the same inputs and asserts identical outputs; any divergence fails the pipeline.

- [ ] T006 [P] Validate the match result and perform a power check.  
  - **Steps**:  
    1. `src/validation/validate_match.py` reads `matched_users.parquet`, computes `match_rate` and total matched users `N`.  
    2. If `match_rate < 0.80` **or** `N < 600`, abort with a *“Power Insufficient”* error.  
    3. Additionally, verify that **each retained user has ≥ 6 distinct calendar months** of non‑null loneliness scores; abort with “Insufficient Longitudinal Depth” if any user fails.  
    4. `src/validation/power_analysis.py` (called by the same script) computes the detectable effect size given `N` and a target power = 0.80; if the detectable Cohen’s d > 0.8, write a warning in `data/validation/power_analysis_report.yaml`.  
  - **Outputs**: `data/validation/match_report.yaml`, `data/validation/power_analysis_report.yaml`.  
  - **Verification**: The two YAML files must exist and contain the keys `match_rate`, `total_users`, `matched_users`, `status` (pass/fail), `detectable_d`, and `longitudinal_depth_pass`.

---

## Phase 2 – Feature engineering  

- [ ] T007 [P] Implement `src/ingest/download_ecar_lexicon.py` to download the **ECAR Lexicon** from its public repository, validate the `keyword`, `anxiety_weight`, `avoidance_weight` columns against an expected schema, and store it as `data/lexicons/ecar_lexicon.csv`.  
  - **Verification**: Unit test `tests/unit/test_download_ecar_lexicon.py` confirms the file exists, contains ≥ 500 rows, and passes schema validation; if validation fails the script aborts with “Lexicon Missing”.

- [ ] T008 [P] Implement `src/features/usage_metrics.py` to aggregate weekly AI‑companion usage per matched user:  
  - Compute `usage_frequency` (count of interactions) and `session_duration` (minutes between first and last timestamp of consecutive activities, capped at 24 h per session).  
  - Write `data/processed/usage_metrics.parquet`.  
  - **Verification**: `tests/unit/test_usage_metrics.py` checks that each user‑week record has non‑negative integers and that the sum of `session_duration` does not exceed 24 h per session.

- [ ] T009 [P] Implement `src/features/attachment_proxy.py` to:  
  1. Load the ECAR lexicon and the baseline‑window config (`config/baseline_window_config.yaml`, `baseline_days_preceding = 30`).  
  2. Identify each user’s baseline posts (within 30 days before their first survey timestamp).  
  3. Count anxiety and avoidance keywords, normalize by total baseline tokens to produce `attachment_anxiety_score` and `attachment_avoidance_score` (range 0‑1).  
  4. Exclude any user lacking baseline text or for whom the lexicon scan fails (FR‑004b).  
  - **Output**: `data/processed/attachment_scores.parquet`.  
  - **Verification**: `tests/unit/test_attachment_proxy.py` validates that all retained users have scores in the 0‑1 range and that the excluded‑user count matches expectations from a manually curated small set.

- [ ] T015 [P] Validate attachment‑proxy extraction accuracy against a manually annotated validation set of 20 users. Compute Cohen’s κ; abort with “Attachment Proxy Validation Failed” if κ < 0.8.  
  - **Verification**: `src/validation/validate_attachment_proxy.py` outputs `data/validation/attachment_proxy_kappa.yaml` containing the κ value and pass/fail flag.

- [ ] T017 [P] Perform proxy‑construct validation (usage metrics vs. Parasocial Interaction Scale) on a 30‑user subset. Compute Pearson r; abort with “Proxy Validation Failed” if r < 0.6 (p < 0.05).  
  - **Verification**: `src/validation/validate_proxy_construct.py` writes `data/validation/proxy_construct_report.yaml` with r, p‑value, and pass/fail status.

- [ ] T010 [P] Implement `src/features/integrate_features.py` to merge `matched_users.parquet`, `usage_metrics.parquet`, and `attachment_scores.parquet` into a single longitudinal dataset `data/processed/unified_dataset.parquet`.  
  - **Verification**: Run `src/utils/data_validation.py` against `contracts/unified_dataset.schema.yaml`; the script must produce `logs/unified_dataset_validation.log` with “validation passed”.

---

## Phase 3 – Modeling pipeline  

- [ ] T011 [P] Implement the full modeling pipeline (primary, baseline, bootstrap, subgroup) in `src/modeling/`.  
  - **Sub‑steps** (executed sequentially inside the script `run_modeling.py`):  
    1. Fit an intercept‑only baseline mixed‑effects model (random intercept for `User`).  
    2. Fit the primary linear mixed‑effects model with lagged predictors, fixed effects `UsageFrequency`, `SessionDuration`, `AttachmentAnxietyScore`, `AttachmentAvoidanceScore`, plus covariates (`Age`, `Gender`, `OverallRedditActivity`, `BaselineMentalHealthScore`, `SES_Index`). Random intercepts and random slopes for `UsageFrequency` by `User`.  
    3. Perform **1 000** cluster bootstrap iterations (seed = 42) at the user level to obtain 95 % confidence intervals; apply Holm‑Bonferroni correction to p‑values.  
    4. If the dataset contains ≥ 80 users aged ≥ 60, re‑fit the model on this subgroup and store a separate summary.  
  - **Outputs**:  
    - `data/results/baseline_model_summary.json`  
    - `data/results/model_fit_summary.json` (conforms to `contracts/model_output.schema.yaml`)  
    - `data/results/bootstrap_ci.json`  
    - `data/results/subgroup_analysis_60plus.json` (if applicable)  
  - **Verification**: `tests/integration/test_modeling_pipeline.py` checks that all four JSON files exist, that `model_fit_summary.json` reports `"convergence_status": "converged"`, and that each fixed‑effect CI contains the point estimate.

---

## Phase 4 – Robustness validation & reporting  

- [ ] T012 [P] Implement `src/validation/validate_success.py` to compute the study‑level success metrics:  
  - Marginal R² gain (≥ 0.05) compared to baseline (SC‑002).  
  - Confidence‑interval stability (effect CIs not crossing zero for at least one predictor) (SC‑003).  
  - Total runtime (must be ≤ 6 h) (SC‑004).  
  - Produce `data/results/robustness_report.csv` with columns `metric_name,value,threshold,passed,timestamp`.  
  - **Verification**: The CSV must contain rows for `marginal_r2_gain`, `ci_stability`, `runtime_hours` and all `passed` fields are `true` for a successful run.

- [ ] T013 [P] Generate the final results package:  
  - Convert `model_fit_summary.json` to `data/results/model_results.csv` (columns: `parameter,estimate,std_error,p_value,ci_lower,ci_upper`).  
  - Render an HTML report `data/results/report.html` using a Jinja2 template that embeds the results table, robustness metrics, and a brief methods summary.  
  - **Verification**: Opening `report.html` in a headless browser must display the table and show no missing values.

- [ ] T021 [P] Enforce Single Source of Truth: verify that all manuscript figures, tables, and statistics reference the canonical dataset `data/processed/unified_dataset.parquet`.  
  - **Verification**: `src/validation/verify_sst.py` parses the generated report and any downstream figure scripts, confirming that each numeric value originates from the unified dataset; fails with “SST Violation” if any discrepancy is found.

- [ ] T014 [P] Write project documentation.  
  - `docs/README.md` – overview, installation, data sources, and high‑level workflow.  
  - `docs/quickstart.md` – step‑by‑step commands to run the entire pipeline from raw data to `report.html`.  
  - **Verification**: `tests/integration/test_quickstart.py` runs the commands listed in `quickstart.md` on a tiny sampled dataset (first 100 users) and asserts that `report.html` is produced without errors.

---

## Dependencies & execution order  

| Task | Depends on |
|------|------------|
| T001 | – |
| T002 | T001 |
| T020 | T001 |
| T018 | T001 |
| T003 | T001 |
| T004 | T001, T003 |
| T016 | T004 |
| T005 | T003, T004 |
| T019 | T005 |
| T006 | T005 |
| T007 | T001 |
| T008 | T005 |
| T009 | T005, T007 |
| T015 | T009 |
| T017 | T008 |
| T010 | T005, T008, T009 |
| T011 | T010 |
| T012 | T011 |
| T021 | T012 |
| T013 | T012 |
| T014 | T013 |
| T018 | (already listed) |
| T020 | (already listed) |

Tasks marked **[P]** can be executed in parallel when their dependencies are satisfied.  

---  

*All tasks are expressed as unchecked (`- [ ]`) unless the artifact has already been verified as present and passing its associated test, in which case the box is checked (`- [X]`).*  