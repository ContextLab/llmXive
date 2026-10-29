# Tasks: Evaluating the Impact of Code Generation on Code Review Quality Using LLMs

**Input**: Design documents from `/specs/001-evaluating-llm-code-review-impact/`  
**Prerequisites**: `plan.md`, `spec.md`, `data-model.md`, `contracts/`

## Phase 1 – Setup and first end‑to‑end analysis

### User Story 1 – Data Acquisition and LLM Classification (US-1)

- [~] T001 Create a root‑level `requirements.txt` (path: `requirements.txt`) listing `requests`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `statsmodels`, `pytest`, `pydantic`. Record the installation log at `logs/requirements_install.log`.
  – **Verification**: `pip install -r requirements.txt` on a clean runner finishes without error; the log contains the success message and is committed.

- [X] T002 Implement a checksum utility `code/utils/checksum.py` exposing `sha256_file(path: str) -> str`. Add a unit test `tests/unit/test_checksum.py`.  
  – **Verification**: `pytest tests/unit/test_checksum.py` exits with code 0 and the test asserts the correct SHA‑256 of a known file.

- [~] T003 Implement the GitHub fetch script `code/data/fetch_github.py` with function `fetch_batch(repo: str, limit: int, batch_size: int = 50, max_retries: int = 3)`. The script must:
  1. Paginate through the GitHub REST API in batches of **50 PRs**,
  2. Apply exponential back‑off on HTTP 429/5xx (max 3 retries),
  3. Write each raw JSON payload to `data/raw/<repo>_prs.jsonl`,
  4. Write a SHA‑256 checksum file `data/raw/<repo>_checksums.txt`,
  5. After each repo, count rows labelled `llm`; if fewer than 10, automatically continue with the next repository defined in `code/utils/config.py` until a total of ≤ 200 PRs is collected.  
  – **Verification**: After running `python -m code.data.fetch_github`, the `data/raw/` directory contains JSONL files respecting the batch size, total PR records ≤ 200, and at least 10 rows are labelled `llm` (or the fallback list is exhausted). All checksum files exist and match the data files.

- [ ] T004 Verify Python 3.11 project setup and package installation **using the `requirements.txt` created by T001**.   <!-- FAILED-IN-EXECUTION: code/setup_verification.py exit=1 -->
  – **Verification**: The command `python -c "import importlib; importlib.import_module('requests')"` runs without ImportError after installing from `requirements.txt`; the verification log is stored at `logs/setup_verification.log`.

- [ ] T005 Implement the secondary entropy detector `code/data/entropy_detector.py`:
  * Reads a PR diff (plain‑text),
  * Tokenises the diff (whitespace split),
  * Computes Shannon entropy of the token distribution,
  * Normalises to a 0‑1 score (`entropy_score`),
  * Exposes `compute_entropy(diff_text: str) -> float`.  
  Add a unit test `tests/unit/test_entropy_detector.py` that checks higher entropy for a noisy diff versus a clean diff.  
  – **Verification**: Unit test passes; the detector can be imported and returns a float between 0 and 1.

- [ ] T006 Implement the primary classification script `code/data/classify_prs.py` that:
  * Reads all `data/raw/*.jsonl`,
  * Detects known LLM‑bot usernames (`copilot-bot`, `github-copilot`) and commit‑message markers,
  * Calls `entropy_detector.compute_entropy` on each diff,
  * Assigns `source_type` (`llm` or `human`),
  * Computes `confidence_score` (1.0 for exact bot match, otherwise 0.5‑0.9 based on pattern strength; if `< 0.6` label as `human` and set `flagged_for_audit=True`),
  * Writes `data/processed/prs_labeled.csv` containing **all columns required by `pr_schema`** (including `entropy_score`, `confidence_score`, `flagged_for_audit`).  
  – **Verification**: The CSV validates against `specs/001-evaluating-llm-code-review-impact/contracts/pr_schema.schema.yaml`. All `source_type` values are either `llm` or `human`.

### User Story 2 – Metric Extraction and Statistical Comparison (US-2)

- [ ] T008 Compute code‑complexity metrics `code/analysis/complexity.py`:
  * Reads `prs_labeled.csv`,
  * For each PR attempts to fetch the full source files via the GitHub API using the `diff_url` metadata,
  * If the full source can be retrieved, builds a control‑flow graph with `networkx` from the AST and calculates cyclomatic complexity (`complexity_score`) and lines‑of‑code (`loc`),
  * If memory usage exceeds **6 GB** or source retrieval fails, falls back to a simpler metric calculated from the diff: `complexity_score = added_lines + removed_lines` and `loc = added_lines + removed_lines`,
  * Writes `data/processed/complexity_scores.csv` and merges the two new columns back into `data/processed/prs_labeled_complex.csv`.  
  – **Verification**: Output file exists, contains one row per PR, numeric fields are ≥ 0, and a spot‑check on a trivially simple PR yields `complexity_score == 1` when full analysis succeeds; fallback produces non‑negative scores when it is used.

- [ ] T009 Extract review metrics and temporal covariates `code/data/extract_metrics.py`: <!-- FAILED-IN-EXECUTION: code/data/extract_metrics.py exit=1 -->
  * Joins `prs_labeled_complex.csv` with the raw JSON data,
  * Calculates `comment_count` (from `comments_count`),
  * Calculates `time_to_merge_minutes` (`merged_at - created_at` in minutes; rows with `merged_at` = null are logged and omitted),
  * Derives `review_cycles` as `max(1, comment_count // 2)`,
  * Extracts `hour_of_day` and `day_of_week` from `created_at`,
  * Computes **defect density** as `defect_count / loc`, where `defect_count` is derived from linked issue labels `bug` or PR “fixes #” patterns,
  * Writes the fully populated dataset `data/processed/prs_metrics.csv` that **conforms exactly** to the `pr_schema` plus an additional column `defect_density`.  
  – **Verification**: Schema validation passes for the original fields; a separate validation step confirms `defect_density` is a non‑negative float.

- [ ] T010 Perform the primary statistical analysis `code/analysis/statistical_tests.py`:
  * For each metric (`comment_count`, `time_to_merge_minutes`, `defect_density`) runs:
    - Shapiro‑Wilk normality test per group,
    - Independent two‑sample **t‑test** (unequal variance) and computes Cohen’s d,
    - Mann‑Whitney U test (primary) and computes rank‑biserial correlation,
  * Assembles results into `data/processed/results.json` matching `statistical_result.schema.yaml`.  
  – **Verification**: JSON file exists, contains all required fields for each metric, and passes schema validation.

- [ ] T011 Conduct a sensitivity analysis `code/analysis/sensitivity_analysis.py`:
  * Redefine the LLM cohort using **only** `entropy_score > 0.7`,
  * Re‑run the statistical tests from T010 on this alternative cohort,
  * Output `data/processed/sensitivity_results.json` adhering to the same schema.  
  – **Verification**: File exists and validates against `statistical_result.schema.yaml`.

- [ ] T012 Compute correlation between code complexity and review metrics `code/analysis/correlation.py`:
  * Reads `prs_metrics.csv`,
  * Calculates Pearson’s r (and p‑value) for `complexity_score` vs. each of `comment_count`, `time_to_merge_minutes`, `review_cycles`, `defect_density`,
  * Writes `data/processed/complexity_correlation.json` with keys `metric`, `pearson_r`, `p_value`.  
  – **Verification**: JSON contains five entries, each with numeric `pearson_r` and `p_value`.

### User Story 3 – Complexity Scoring and Visualization (US-3)

- [ ] T013 Run the manual audit pipeline `code/audit/manual_validation.py`:
  * Determines required sample size via `calculate_sample_size(N_llm, min_threshold=10, scaling_factor=0.1)`,
  * Randomly (seeded) selects a stratified subset of LLM‑labelled PRs,
  * Emits `data/audit/audit_input.jsonl` containing diff snippets and the checklist columns,
  * Accepts a user‑supplied `--answers-file` (or interactive prompts) and writes `data/audit/audit_log.jsonl`,
  * Computes the classification error rate and writes `data/audit/error_rate.json` (`{"error_rate": <float>}`),
  * Generates a gating file `data/processed/gate_status.json` with `"status"` set to `"passed"` if `error_rate ≤ 0.05`, `"exploratory"` if `N_llm < 10`, or `"blocked"` otherwise.  
  – **Verification**: After providing an answers file, `error_rate.json` contains a numeric value ≤ 0.05 and `gate_status.json` reflects `"passed"`.

- [ ] T014 Produce visualisations `code/analysis/visualizations.py`:
  * Reads `prs_metrics.csv`,
  * Generates side‑by‑side boxplots for `comment_count`, `time_to_merge_minutes`, and `defect_density` split by `source_type`,
  * Generates histograms for the same metrics,
  * Saves PDFs `reports/figures/boxplots.pdf` and `reports/figures/histograms.pdf` (each > 50 KB, contain ≥ 2 vector paths).  
  – **Verification**: Integration test opens each PDF and confirms the expected subplot titles are present.

- [ ] T015 Assemble the final report `code/analysis/generate_report_narrative.py`:
  * Loads `results.json`, `sensitivity_results.json`, `complexity_correlation.json`, and `gate_status.json`,
  * Calls the narrative synthesis helper (`code/analysis/narrative_synthesis.py`) to produce markdown sections for Discussion and Limitations,
  * Inserts quantitative tables and the two figure PDFs into `docs/report_template.md`,
  * Renders the markdown + figures into a single PDF `reports/final_report.pdf` (using `pandoc` or a simple markdown‑to‑PDF renderer).  
  – **Verification**: The final PDF exists, contains the sections *Executive Summary*, *Methodology*, *Results*, *Discussion*, *Limitations*, and embeds the two figure pages. If `gate_status.json` is `"blocked"` the script aborts with a clear error; if `"exploratory"` it adds a note about limited statistical power.

- [ ] T016 Document the reproducible workflow in `quickstart.md`:
  * List the exact command sequence to run the full pipeline from a fresh clone (steps T001‑T015),
  * Include any required environment variables (e.g., `GITHUB_TOKEN`),
  * Verify that a CI job which deletes `data/` and `reports/` then follows the listed commands reproduces **all** artefacts without error.  
  – **Verification**: CI run passes all assertions; `quickstart.md` is up‑to‑date.

## Phase 2 – Complete the study and validate its evidence

(Tasks T001‑T016 together satisfy FR‑001 through FR‑008, SC‑001 through SC‑004, and the statistical requirements. Their ordering respects data flow: fetching → checksum → entropy detection → classification → complexity → metric extraction → statistical testing → sensitivity → correlation → audit → gating → visualisation → report assembly.)

## Phase 3 – Reproducible results and paper handoff

(Execution of T016 demonstrates that a clean clone can reproduce every required artefact, fulfilling the reproducibility mandate. The final PDF `reports/final_report.pdf` constitutes the handoff to the downstream paper pipeline.)