# Tasks: Evaluating the Impact of Code Generation on Code Review Time

**Inputs**: `spec.md`, `plan.md`, contracts, and any existing artifacts.  
All tasks are expressed as canonical checklist items; unchecked boxes indicate work that still needs to be performed. Verification steps are described in indented lines beneath each task.

---

## Phase 1 – Setup, Data Acquisition, and First End‑to‑End Run  

| Goal | Produce a runnable pipeline on a small real repository and generate the core input artefacts required for matching and analysis. |
|------|-----------------------------------------------------------------------------------------------------------------------------------|

- [X] T001 [US‑1] **Create project skeleton & lock dependencies** – `requirements.txt`, `docs/quickstart.md`, `code/` package layout.  
  *Create the directory layout shown in `plan.md` (`code/`, `data/`, `tests/`, `docs/`). Add a `requirements.txt` that pins exact versions of all packages (pandas, pyarrow, datasets, scikit‑learn, statsmodels, scipy, radon, transformers, torch, sentence‑transformers, matplotlib, seaborn, tenacity, requests, ruff). Commit the skeleton and ensure `pip install -r requirements.txt` succeeds in a fresh venv.*  
  - **Verification**: `requirements.txt` exists with the listed versions; `docs/quickstart.md` contains a “Run‑the‑pipeline” command; a fresh `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt` finishes without errors.

- [ ] T002 [US‑1] **Data acquisition – stream PR metadata via GitHub REST API** – `code/data_acquisition.py`, `data/raw/<owner>_<repo>.parquet`
  *Implement `code/data_acquisition.py` to stream PR metadata (creation time, merge time, review comments, CI duration, file changes) for **three** verified GitHub repositories that satisfy ≥ 1 000 stars and ≥ 100 PRs. Use the GitHub REST API with exponential backoff (via `tenacity`) to respect rate limits. Store each repository’s PR parquet file under `data/raw/<owner>_<repo>.parquet` and cache commit messages in `data/raw/commit_messages.parquet`.*  
  - **Verification**: Each `<owner>_<repo>.parquet` file exists, conforms to `pull_request.schema.yaml`, and contains > 0 rows; `commit_messages.parquet` exists with columns `pr_id` and `commit_message`; no unhandled 403 errors appear in the logs.

- [ ] T003 [US‑1] **Prompt engineering** – `code/prompt_engineering.py`, `data/processed/intent_prompts.parquet`  
  *Implement `code/prompt_engineering.py` that reads `data/raw/commit_messages.parquet`, derives a natural‑language prompt for each PR (e.g., “Write a medium‑complexity change that implements …”), and writes `data/processed/intent_prompts.parquet` containing `pr_id`, `prompt`, and a `complexity_indicator` field.*  
  - **Verification**: `intent_prompts.parquet` exists; a random sample shows non‑empty `prompt` strings and a valid `complexity_indicator` (simple / moderate / complex); all `pr_id`s match those in the raw PR files.

- [ ] T004 [US‑4] **Synthetic code generation (both cohorts)** – `code/synthetic_generation.py`, `data/synthetic/context_based.parquet`, `data/synthetic/prompt_based.parquet`  
  *Using the CPU‑tractable **CodeLlama‑7B‑4bit‑GGUF** model, generate two LLM cohorts:*  
  1. **Context‑based** – feed the original code snippet together with its prompt.  
  2. **Prompt‑only** – feed only the NL prompt derived in T003.  
  *Generate at least 100 snippets per cohort for the pilot run. Write the results to the parquet files above. Enforce ≤ 30 s per snippet and record a syntax‑validity rate ≥ 0.95 (AST parse success) in `data/synthetic/validation.json`.*  
  - **Verification**: Both parquet files exist; all `generation_time_sec` ≤ 30; `validation.json` reports `syntax_validity_rate` ≥ 0.95; model version and generation parameters are present for every row.

- [ ] T005 [US‑1] **Feature extraction & covariate configuration** – `code/feature_extraction.py`, `data/processed/merged_features.parquet`, `data/processed/covariate_config.json`  
  *Implement `code/feature_extraction.py` to compute for **all** PRs (human, context‑based, prompt‑based):*  
  - LOC and cyclomatic complexity via `radon` → `file_size_loc`, `complexity_score`.  
  - CI build duration → `ci_build_time`.  
  - Repository activity level → `repo_activity_level`.  
  - Semantic similarity to the repository‑level centroid using `sentence‑transformers/all‑MiniLM‑L6‑v2` (embed each snippet, compute centroid, then cosine similarity).  
  *Merge the features into `data/processed/merged_features.parquet` (conforms to `dataset.schema.yaml`). Write `data/processed/covariate_config.json` listing the exact five matching covariates in order.*  
  - **Verification**: `merged_features.parquet` contains all required columns with correct types; `semantic_similarity` values lie in [‑1, 1]; `covariate_config.json` is valid JSON and lists exactly `["file_size_loc","complexity_score","repo_activity_level","ci_build_time","semantic_similarity"]`.

- [ ] T006 [US‑4] **Real review‑timestamp collection (evaluation repository)** – `code/evaluate_repo.py`, `code/timestamp_collection.py`, `data/processed/merged_features_with_timestamps.parquet`  
  *Create a dedicated sandbox evaluation repository (if not existing). For each LLM‑generated snippet (both cohorts), open a pull request in this repo, invite a pre‑registered reviewer panel, and record the actual `review_effort_duration` (time from first reviewer comment to merge). Log any PR that fails to receive a review within 48 h and exclude it from the primary analysis. Enrich the merged features table with real timestamps and write the result to `merged_features_with_timestamps.parquet`.*  
  - **Verification**: All LLM rows have non‑null `created_at`, `first_comment_at`, `review_effort_duration`, and `total_review_duration`; a summary `timestamp_collection_report.json` shows ≥ 80 % of LLM PRs received a review; the parquet file conforms to `dataset.schema.yaml`.

- [ ] T007 [US‑1] **End‑to‑end sanity test on a tiny repository** – `docs/quickstart.md`, pipeline entry point (`code/main.py`)  
  *Run the full pipeline on a small public repo (e.g., `octocat/Hello-World`) using the command documented in `docs/quickstart.md`. The run must complete within 30 minutes and produce at least one row in `data/processed/merged_features_with_timestamps.parquet`.*  
  - **Verification**: CI log shows successful execution; the output parquet contains ≥ 1 row; all intermediate artefacts (intent prompts, synthetic cohorts, merged features, timestamps) are present.

- [ ] T014 [US‑1] **Runtime measurement & instrumentation** – `code/runtime.py`, `data/processed/runtime_report.json`  
  *Instrument the pipeline (via `code/runtime.py`) to record start/end timestamps for each major stage (data acquisition, prompt engineering, synthetic generation, feature extraction, timestamp collection, matching, analysis, sensitivity, visualization, report generation). The instrumentation is integrated at the entry point of the pipeline so that all subsequent tasks automatically emit timing data.*  
  - **Verification**: After a full pipeline run, `runtime_report.json` exists, contains a `stage_times` mapping for every stage, and `total_seconds` ≤ 21 600 (6 h). Running `python -m code.runtime --verify` exits with status 0.

---

## Phase 2 – Full Study: Matching, Analysis, and Reporting  

| Goal | Pair LLM‑generated commits with human commits, run statistical tests, assess robustness, and produce the final research report. |
|------|------------------------------------------------------------------------------------------------------------------------------|

- [ ] T009 [US‑2] **Propensity‑score matching & covariate‑balance report** – `code/matching.py`, `data/processed/matched_pairs.parquet`, `data/processed/covariate_balance.json`  
  *Load `merged_features_with_timestamps.parquet` and the five covariates from `covariate_config.json`. Fit a logistic‑regression propensity model, perform 1‑to‑1 nearest‑neighbor matching with caliper = 0.05, and output the matched pairs. If any standardized mean difference (SMD) ≥ 0.1, automatically retry up to three times adding interaction terms; abort with a clear error if balance is not achieved.*  
  - **Verification**: `matched_pairs.parquet` exists with ≥ 1 pair; `covariate_balance.json` reports all SMD < 0.1; the script exits with status 0.

- [ ] T010 [US‑2] **Statistical analysis of the primary outcome** – `code/analysis.py`, `data/processed/analysis_results.json`  
  *Load `matched_pairs.parquet` and extract `review_effort_duration` for human vs. LLM entries. Run a Shapiro‑Wilk test on the paired differences; select a paired t‑test if p > 0.05, otherwise Mann‑Whitney U. Compute the p‑value, appropriate effect size (Cohen’s d or rank‑biserial), and a boolean `passed` flag (p < 0.05). **Additionally, verify that the mean LLM `review_effort_duration` is at least 10 % greater than the human mean and that the effect size meets or exceeds 0.2; if either condition is not satisfied, mark `passed` as false and raise a failure.** Write the results conforming to `test_result.schema.yaml`.*  
  - **Verification**: `analysis_results.json` exists, validates against `test_result.schema.yaml`, includes `test_name`, `p_value`, `effect_size`, `passed`, and the task fails if the 10 % increase or effect‑size threshold is not met.

- [ ] T011 [US‑3] **Sensitivity analysis across repository‑star quartiles** – `code/sensitivity.py`, `data/processed/sensitivity_summary.json`  
  *Split the dataset into four quartiles based on `repo_activity_level`, repeat matching (using T009 logic) and statistical testing (using T010 logic) within each quartile. Aggregate the results into a JSON file with keys `quartile_results` (list of four `test_result` objects) and `consistent` (true if ≥ 80 % of quartiles have `passed` = true).*  
  - **Verification**: `sensitivity_summary.json` exists; `quartile_results` has exactly four entries each valid per `test_result.schema.yaml`; `consistent` correctly reflects the 80 % rule.

- [ ] T012 [US‑3] **Visualization of review‑time distributions** – `code/visualization.py`, `data/figures/review_time_box.png`, `data/figures/review_time_cdf.png`  
  *Generate a box plot and a cumulative distribution function (CDF) plot comparing `review_effort_duration` for human vs. LLM (both cohorts). Save the figures as PNGs with at least 100 DPI, include axis labels (“review_effort_duration (seconds)”), and a legend.*  
  - **Verification**: Both PNG files exist, are non‑empty, open without error, and contain the required labels and legend.

- [ ] T013 [US‑3] **Report generation (HTML + PDF)** – `code/report_generator.py`, `data/reports/analysis_report.html`, `data/reports/analysis_report.pdf`  
  *Create a Jinja2 template `docs/templates/report_template.j2` with placeholders for test name, p‑value, effect size, pass/fail flag, quartile results, and base‑64‑encoded images. Implement `code/report_generator.py` to render the HTML report, then convert it to PDF (e.g., via `weasyprint`).*  
  - **Verification**: `analysis_report.html` and `analysis_report.pdf` exist; the PDF is > 10 KB and renders the figures and statistics correctly; the template file contains all listed placeholders.

- [ ] T015 [US‑1] **Documentation & code cleanup** – `docs/quickstart.md`, `data/processed/cleanup_report.txt`  
  *Populate `docs/quickstart.md` with step‑by‑step instructions (environment creation, dependency installation, pipeline command, expected outputs). Run `ruff` linting on the entire `code/` directory, add type hints where missing, remove dead code, and write a summary `cleanup_report.txt` stating “0 errors, 0 warnings”.*  
  - **Verification**: `quickstart.md` exists and the commands run cleanly on a fresh runner; `cleanup_report.txt` shows zero linting issues; `ruff` passes without warnings.

---  

### Dependency & Execution Order Summary  

1. **Phase 1**: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T014.  
2. **Phase 2**: T009 → T010 → T011 → T012 → T013 → T015.  

All downstream tasks depend only on the artefacts produced by their predecessors, respecting data‑flow constraints and the scientific methodology outlined in the specification.  

---  

*End of `tasks.md`.*  