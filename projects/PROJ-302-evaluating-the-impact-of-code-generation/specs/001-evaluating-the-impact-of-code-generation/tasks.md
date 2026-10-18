# Tasks: Evaluating the Impact of Code Generation on Code Review Time

**Inputs**: `spec.md`, `plan.md`, contracts, and any existing artifacts.  
All tasks are expressed as canonical checklist items; unchecked boxes indicate work that still needs to be performed. Verification steps are described in indented lines beneath each task.

---

## Phase 1 – Setup, Data Acquisition, and First End‑to‑End Run  

| Goal | Produce a runnable pipeline on a small real repository and generate the core input artefacts required for matching and analysis. |
|------|-----------------------------------------------------------------------------------------------------------------------------------|

- [ ] T001 [US‑1] **Create project skeleton & lock dependencies**   <!-- FAILED-IN-EXECUTION: code/verify_setup.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/verify_setup.py exit=1 -->
  *Create the directory layout shown in `plan.md` (`code/`, `data/`, `tests/`, `docs/`). Add a `requirements.txt` that pins exact versions of all packages (e.g., pandas, pyarrow, datasets, scikit‑learn, statsmodels, scipy, radon, transformers, torch, matplotlib, seaborn, tenacity, requests, codecarbon). Commit the skeleton and ensure `pip install -r requirements.txt` succeeds in a fresh venv.*  
  - **Verification**: `requirements.txt` exists with the listed versions; `docs/quickstart.md` contains a “Run‑the‑pipeline” command; a fresh `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt` finishes without errors.

- [ ] T014 [US‑1] **Runtime measurement & instrumentation (early)**  
  *Instrument the pipeline (via `code/runtime.py`) to record start/end timestamps for each major stage (data acquisition, prompt engineering, synthetic generation, feature extraction, timestamp simulation, matching, analysis, sensitivity, visualization, report generation). This instrumentation is integrated at the entry point of the pipeline so that all subsequent tasks automatically emit timing data.*  
  - **Verification**: After a full pipeline run, `data/processed/runtime_report.json` exists, contains a `stage_times` mapping for every stage, and `total_seconds` ≤ 21 600. Running `python -m code.verification` exits with status 0.

- [ ] T002 [US‑1] **Data acquisition – stream PR metadata via GitHub REST API**   <!-- FAILED-IN-EXECUTION: code/data_acquisition.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_acquisition.py exit=1 -->
  *Implement `code/data_acquisition.py` to stream PR metadata (creation time, merge time, review comments, CI duration, file changes) for three verified GitHub repositories that satisfy ≥ 1 000 stars and ≥ 100 PRs. Use the GitHub **REST** API with exponential backoff (via `tenacity`) to respect rate limits. Store each repository’s PR parquet file under `data/raw/<owner>_<repo>.parquet` and cache commit messages in `data/raw/commit_messages.parquet`.*  
  - **Verification**: Each `<owner>_<repo>.parquet` file exists, conforms to `pull_request.schema.yaml`, and contains > 0 rows; `commit_messages.parquet` exists with columns `pr_id` and `commit_message`; rate‑limit handling is logged and no unhandled 403 errors occur.

- [ ] T003 [US‑1] **Prompt engineering**  
  *Implement `code/prompt_engineering.py` that reads `data/raw/commit_messages.parquet`, derives a natural‑language prompt for each PR (e.g., “Write a *medium‑complexity* code change with a *12‑word* description: …”), and writes `data/processed/intent_prompts.parquet` containing `pr_id`, `prompt`, and `complexity_indicator`.*  
  - **Verification**: `intent_prompts.parquet` exists; a random sample shows non‑empty `prompt` strings and a valid `complexity_indicator` (simple / moderate / complex); all `pr_id`s match those in the raw PR files.

- [ ] T004 [US‑4] **Synthetic code generation (both cohorts, no pre‑stratification)**  
  *Using the CPU‑tractable **CodeLlama‑7B‑4bit‑GGUF** model, generate two LLM cohorts:*  
  1. **Context‑based** – feed the original code snippet together with its prompt.  
  2. **Prompt‑only** – feed only the NL prompt derived in T003.  
  *Generate at least 100 snippets per cohort for the pilot run (stratification by repository activity will be handled later during matching). Write the results to:*  
  - `data/synthetic/context_based.parquet` (columns: `pr_id`, `code_content`, `generation_source='llm‑context'`, `generation_time_sec`, `model_version`, `generation_params`).  
  - `data/synthetic/prompt_based.parquet` (columns: `pr_id`, `code_content`, `generation_source='llm‑prompt'`, `generation_time_sec`, `model_version`, `generation_params`).  
  *Enforce ≤ 30 s per snippet and record a syntax‑validity rate ≥ 0.95 (AST parse success) in `data/synthetic/validation.json`.*  
  - **Verification**: Both parquet files exist; all `generation_time_sec` ≤ 30; `validation.json` reports `syntax_validity_rate` ≥ 0.95; model version and parameters are present for every row.

- [ ] T005 [US‑1] **Feature extraction & covariate configuration**  
  *Implement `code/feature_extraction.py` to compute for **all** PRs (human, context‑based, prompt‑based):*  
  - LOC and cyclomatic complexity via `radon` → `file_size_loc`, `complexity_score`.  
  - CI build duration → `ci_build_time`.  
  - Repository activity level → `repo_activity_level`.  
  - **Semantic similarity** to the repository‑level centroid using `microsoft/codebert-base` (embed each human snippet per repo, compute centroid, then cosine‑similarity for every snippet).  
  *Merge the features into `data/processed/merged_features.parquet` (conforms to `dataset.schema.yaml`). Write `data/processed/covariate_config.json` listing the exact five matching covariates in order:* `["file_size_loc","complexity_score","repo_activity_level","ci_build_time","semantic_similarity"]`.  
  - **Verification**: `merged_features.parquet` contains all required columns with correct types; `semantic_similarity` values lie in [‑1, 1]; `covariate_config.json` is valid JSON and lists exactly the five covariates.

- [ ] T006 [US‑1] **Synthetic review‑timestamp simulation (using human PRs for KDE)**  
  *For each LLM‑generated PR (both cohorts), simulate realistic timestamps:*  
  1. **Create synthetic `created_at`** by sampling from the distribution of human PR `created_at` values conditioned on the five covariates.  
  2. **Build a KDE of `review_effort_duration`** using the full set of human PRs (available before matching).  
  3. Sample a `review_effort_duration` for each LLM PR, set `first_comment_at = merge_at - sampled_duration`, and compute `total_review_duration = merge_at - created_at`.  
  4. Write the enriched dataset to `data/processed/merged_features_with_timestamps.parquet` (extends the file from T005).  
  - **Verification**: All LLM rows have non‑null `created_at`, `review_effort_duration`, and `total_review_duration`; sampled values fall within the observed human range; a summary report `data/processed/timestamp_simulation_report.json` shows ≥ 95 % successful samples.

- [ ] T007 [US‑1] **End‑to‑end sanity test on a tiny repository**  
  *Run the full pipeline on a small public repo (e.g., `octocat/Hello-World`) using the command documented in `docs/quickstart.md`. The run must complete within 30 minutes and produce at least one row in `data/processed/merged_features_with_timestamps.parquet`.*  
  - **Verification**: CI log shows successful execution; the output parquet contains ≥ 1 row; all intermediate artefacts (intent prompts, synthetic cohorts, merged features, timestamps) are present.

---

## Phase 2 – Full Study: Matching, Analysis, and Reporting  

| Goal | Pair LLM‑generated commits with human commits, run statistical tests, assess robustness, and produce the final research report. |
|------|------------------------------------------------------------------------------------------------------------------------------|

- [ ] T008 [US‑2] **Pre‑study power analysis**  
  *Implement `code/power_analysis.py` to compute the required number of matched pairs for detecting an effect size = 0.3 with α = 0.05 and power = 0.8. Read `covariate_config.json` to confirm the five covariates are present. Output `data/processed/power_analysis.json` with fields:* `effect_size`, `alpha`, `power`, `minimum_pairs_required`, `current_pairs`, `sufficient`, and a recommendation if more data are needed.  
  - **Verification**: `power_analysis.json` exists, is valid JSON, and the `sufficient` flag correctly reflects whether the current dataset meets the required sample size.

- [ ] T009 [US‑2] **Propensity‑score matching & covariate‑balance report**  
  *Implement `code/matching.py` to:*  
  1. Load `merged_features_with_timestamps.parquet` and the five covariates from `covariate_config.json`.  
  2. Fit a logistic regression to estimate propensity scores.  
  3. Perform 1‑to‑1 nearest‑neighbor matching with caliper = 0.05.  
  4. Output `data/processed/matched_pairs.parquet` (conforms to `matched_pair.schema.yaml`) and `data/processed/covariate_balance.json` containing standardized mean differences (SMD) for each covariate.  
  5. If any SMD ≥ 0.1, automatically retry up to three times adding interaction terms; abort with a clear error if balance is not achieved.  
  - **Verification**: `matched_pairs.parquet` exists with ≥ 1 pair; `covariate_balance.json` reports all SMD < 0.1; the script exits with status 0.

- [ ] T010 [US‑2] **Statistical analysis of the primary outcome**  
  *Implement `code/statistical_test.py` to:*  
  1. Load `matched_pairs.parquet` and extract `review_effort_duration` for human vs. LLM entries.  
  2. Run a Shapiro‑Wilk test on the paired differences; select a paired t‑test if p > 0.05, otherwise Mann‑Whitney U.  
  3. Compute the p‑value, appropriate effect size (Cohen’s d or rank‑biserial), and a boolean `passed` flag (p < 0.05).  
  4. Write `data/processed/analysis_results.json` conforming to `test_result.schema.yaml`.  
  - **Verification**: `analysis_results.json` exists and validates against `test_result.schema.yaml`; the JSON includes `test_name`, `p_value`, `effect_size`, and `passed`.

- [ ] T011 [US‑3] **Sensitivity analysis across repository‑star quartiles**  
  *Implement `code/sensitivity.py` to split the dataset into four quartiles based on `repo_activity_level`, repeat matching (using T009 logic) and statistical testing (using T010 logic) within each quartile, and aggregate the results into `data/processed/sensitivity_summary.json` with keys `quartile_results` (list of four `test_result` objects) and `consistent` (true if ≥ 80 % of quartiles have `passed` = true).*  
  - **Verification**: `sensitivity_summary.json` exists; `quartile_results` has exactly four entries each valid per `test_result.schema.yaml`; `consistent` correctly reflects the 80 % rule.

- [ ] T012 [US‑3] **Visualization of review‑time distributions**  
  *Implement `code/visualization.py` to generate:*  
  - A box plot saved as `data/figures/review_time_box.png`.  
  - A cumulative distribution function (CDF) plot saved as `data/figures/review_time_cdf.png`.  
  *Both plots must display human vs. LLM (both cohorts) side‑by‑side, include axis labels (“review_effort_duration (seconds)”), a legend, and be at least 100 DPI.*  
  - **Verification**: Both PNG files exist, are non‑empty, open without error, and contain the required labels and legend.

- [ ] T013 [US‑3] **Report generation (HTML + PDF)**  
  *Create a Jinja2 template `docs/templates/report_template.j2` with placeholders for test name, p‑value, effect size, pass/fail flag, quartile results, and base‑64‑encoded images.*  
  *Implement `code/report_generator.py` to:*  
  1. Load `analysis_results.json`, `sensitivity_summary.json`, and the two PNGs.  
  2. Render the HTML report to `data/reports/analysis_report.html`.  
  3. Convert the HTML to PDF (e.g., via `weasyprint`) and save to `data/reports/analysis_report.pdf`.  
  - **Verification**: `analysis_report.html` and `analysis_report.pdf` exist; the PDF is > 10 KB and renders the figures and statistics correctly; the template file contains all listed placeholders.

- [ ] T015 [US‑1] **Documentation: quickstart & code‑cleanup**  
  *Populate `docs/quickstart.md` with step‑by‑step instructions (environment creation, dependency installation, pipeline command, expected outputs).*  
  *Run `ruff` linting on the entire `code/` directory, add type hints where missing, remove dead code, and write a summary `data/processed/cleanup_report.txt` stating “0 errors, 0 warnings”.*  
  - **Verification**: `quickstart.md` exists and the commands run cleanly on a fresh runner; `cleanup_report.txt` shows zero linting issues; `ruff` passes without warnings.

---

### Dependency & Execution Order Summary  

1. **Phase 1**: T001 → T014 → T002 → T003 → T004 → T005 → T006 → T007.  
2. **Phase 2**: T008 → T009 → T010 → T011 → T012 → T013 → T015.  

All downstream tasks depend only on the artefacts produced by their predecessors, respecting data‑flow constraints and the scientific methodology outlined in the specification.  

---  

*End of `tasks.md`.*  