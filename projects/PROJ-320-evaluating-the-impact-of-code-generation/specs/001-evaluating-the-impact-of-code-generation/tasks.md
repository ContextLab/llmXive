# Tasks: Evaluating the Impact of Code Generation on Code Review Quality Using LLMs

**Input**: Design documents from `/specs/001-evaluating-llm-code-review-impact/`  
**Prerequisites**: `plan.md`, `spec.md`, `data-model.md`, `contracts/`

## Phase 1 – Setup and first end‑to‑end analysis

| Goal | Run an executable driver on a small real input set and produce the first validated artefacts. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] T002 Establish the Python 3.11 project with a `requirements.txt` that pins `requests`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `statsmodels`, `pytest`, `pydantic`.  
  – **Verification**: `pip install -r requirements.txt` succeeds on a fresh runner; `requirements.txt` is present at the repo root.

- [X] T004 Create `code/utils/seeds.py` that defines a deterministic RNG seed (`SEED = 42`) and a helper `set_seed()` used by all stochastic scripts.  
  – **Verification**: Importing `set_seed` sets `numpy` and `random` seeds without error.

- [X] T005 Create `code/utils/config.py` containing the prioritized repository list (`["psf/requests", "microsoft/vscode", "numpy/numpy"]`), API limits, and classification thresholds (`LLM_CONFIDENCE = 0.6`).  
  – **Verification**: `from code.utils.config import REPOS` returns the expected list.

- [ ] T008 Add `code/utils/checksum.py` with `sha256_file(path)` used by the fetch script.   <!-- FAILED-IN-EXECUTION: tests/unit/test_checksum.py exit=1 -->
  – **Verification**: Unit test in `tests/unit/test_checksum.py` passes.

- [ ] T007 Implement `code/data/fetch_github.py` with `fetch_batch(repo: str, limit: int, max_retries: int = 3)` that:
  1. Calls the GitHub REST API with pagination,
  2. Applies exponential back‑off on HTTP 429/5xx,
  3. Writes each raw JSON payload to `data/raw/<repo>_prs.jsonl`,
  4. Stores a SHA‑256 checksum file `data/raw/<repo>_checksums.txt`.  
  – **Verification**: Running `python -c "from code.data.fetch_github import fetch_batch; fetch_batch('psf/requests', 10)"` creates the JSONL and checksum files; a forced 429 triggers three retries then raises `RuntimeError`.

- [ ] T009 Add `code/audit/manual_validation.py` helper `calculate_sample_size(N_llm, min_threshold=10, scaling_factor=0.1)` returning the larger of `min_threshold` and `ceil(N_llm * scaling_factor)`.  
  – **Verification**: Function returns `10` for `N_llm=5` and `12` for `N_llm=120`.

- [ ] T015a/T015c Secondary detector (`code/data/entropy_detector.py`) that computes a simple token‑entropy score over the PR diff and adds `entropy_score` (0‑1).  The detector is used later for validation (FR‑007).  
  – **Verification**: Unit test confirms higher entropy for a synthetic noisy diff vs. a clean diff.

- [ ] T014 Primary signature classification (`code/data/classify_prs.py`) that:
  * Reads the raw JSONL files,
  * Detects known LLM‑bot usernames (`copilot-bot`, `github-copilot`) and commit‑message markers,
  * Assigns `source_type` (`llm`/`human`), a `confidence_score` (1.0 for exact bot match, else 0.5‑0.9 based on pattern strength),
  * Flags `flagged_for_audit` when `confidence_score < 0.6`.  
  – **Verification**: Running the script on the fetched data produces `data/processed/classification_tmp.csv` with the required columns and the correct enum values.

- [ ] T018 Repository fallback logic (in `fetch_github.py`) that, after the initial repo is processed, checks the count of rows labeled `llm`; if `< 10`, the script automatically proceeds to the next repo in `REPOS` until the target of 200 total PRs or the list is exhausted.  
  – **Verification**: Configure `REPOS` to start with a repository known to contain < 10 LLM-labeled PRs; execute `python -m code.data.fetch_github` and verify that `data/raw/` contains JSONL files for *both* the first and second repositories in the list, confirming the fallback triggered.

- [ ] T013 Fetch up to 200 PRs across the prioritized repos (batch size = 50) using the driver from T007, storing raw JSON in `data/raw/`.  Respect FR‑001 and fail loudly on unrecoverable API errors.  
  – **Verification**: After `python -m code.data.fetch_github`, `data/raw/` contains at least one JSONL file and the total number of PR records is ≤ 200.

- [ ] T019a Provide an audit checklist template `code/audit/manual_audit_checklist.csv` containing columns `pr_id, bot_signature_present, entropy_high, human_judgment, notes`.  
  – **Verification**: File exists and contains a header row.

- [ ] T024b Implement Mann‑Whitney U sensitivity‑test helper (`code/analysis/mann_whitney.py`) that returns `u_statistic`, `p_value_u`, and rank‑biserial `effect_size_u`.  
  – **Verification**: Test on two synthetic groups matches `scipy.stats.mannwhitneyu` output.

- [ ] T025 Compute Cohen’s d effect size (`code/analysis/effect_size.py`) and expose `is_significant(p, alpha=0.05)`.  
  – **Verification**: Known examples produce the expected d and significance flag.

- [ ] T026 Sensitivity analysis script (`code/analysis/sensitivity_analysis.py`) that re‑defines the LLM cohort using **only** the secondary detector (`entropy_score > 0.7`) and re‑runs the statistical tests.  
  – **Verification**: Generates `data/processed/sensitivity_results.json` with the same schema as the primary results.

- [ ] T035 Correlation analysis (`code/analysis/correlation.py`) that computes Pearson’s r between `complexity_score` and each review metric, writing `data/processed/complexity_correlation.json`.  
  – **Verification**: Correlation file contains keys `metric`, `pearson_r`, `p_value`.

- [ ] T036c Narrative synthesis helper (`code/analysis/narrative_synthesis.py`) that formats discussion bullet points based on statistical significance, effect‑size magnitude, and audit error rate.  
  – **Verification**: Function returns a markdown string that can be inserted into the final report.

- [ ] T042 PII‑filter (`code/utils/pii_scan.py`) that scans all CSV/JSON artefacts for email‑like strings and removes them before artefact publication.  
  – **Verification**: Running the scanner on a test file containing `user@example.com` produces a cleaned copy without the email.

- [ ] T060 Build a single end‑to‑end pipeline driver `code/data/run_pipeline.py` that sequentially:
  1. Calls `fetch_github.fetch_batch` for each repo until 200 PRs are collected,
  2. Executes `classify_prs.py` (primary + secondary detector) producing `data/processed/prs_labeled.csv` that conforms to `specs/001-evaluating-llm-code-review-impact/contracts/pr_schema.schema.yaml` (validated row‑wise with a Pydantic model `LabeledPR`),
  3. Writes the CSV atomically and logs a success message.  
  – **Verification**: `python code/data/run_pipeline.py` exits with status 0, the file `data/processed/prs_labeled.csv` exists, is non‑empty, contains exactly the schema columns, and all `source_type` values are either `llm` or `human`.

- [ ] T061 Extend `code/analysis/complexity.py` to:
  * Read `prs_labeled.csv`,
  * For each PR fetch its diff from the corresponding raw JSON,
  * Compute cyclomatic complexity using `networkx` (build a control‑flow graph from the AST and count decision nodes),
  * Compute lines‑of‑code (`loc`),
  * Append `complexity_score` and `loc` to the original CSV, writing `data/processed/complexity_scores.csv`.  
  – **Verification**: Output file exists, has one row per PR, all numeric fields ≥ 0, and a spot‑check of a known simple PR yields `complexity_score == 1`.

- [ ] T062 Implement `code/data/extract_metrics.py` that:
  * Joins `prs_labeled.csv` with `complexity_scores.csv` on `pr_id`,
  * Calculates `comment_count` (from raw `comments_count`), `time_to_merge_minutes` (difference between `created_at` and `merged_at`), and `review_cycles` (heuristic `max(1, comments_count // 2)`),
  * Adds temporal covariates `hour_of_day` and `day_of_week` extracted from `created_at`,
  * Writes the fully populated dataset to `data/processed/prs_metrics.csv` respecting the full `pr_schema` (including `entropy_score`).  
  – **Verification**: File exists, schema validation passes, and a PR with `merged_at=None` is excluded with a logged warning (no fabricated rows).

- [ ] T063 Complete `code/analysis/statistical_tests.py` to perform the **primary** analysis:
  * For each metric (`comment_count`, `time_to_merge_minutes`):
    - Run Shapiro‑Wilk normality test per group; if any p < 0.05 log “Data non‑normal, proceeding with t‑test per FR‑004”.
    - Conduct independent two‑sample **t‑test** (unequal variance) and compute Cohen’s d.
    - Conduct Mann‑Whitney U as a sensitivity check (using the helper from T024b).
    - Record all statistics, effect sizes, sample sizes, and significance flags in `data/processed/results.json` conforming to `statistical_result.schema.yaml`.  
  – **Verification**: JSON file exists, contains keys `metric_name`, `group_a_mean`, `group_b_mean`, `u_statistic`, `p_value_u`, `effect_size_u`, `is_significant_u`, `t_statistic`, `p_value_t`, `effect_size_t`, `is_significant_t`, `sample_size_a`, `sample_size_b`.  Running the script on the generated `prs_metrics.csv` produces no exceptions.

- [ ] T064 Re‑implement the full manual audit CLI in `code/audit/manual_validation.py`:
  * Load `prs_labeled.csv`,
  * Determine the required sample size via `calculate_sample_size`,
  * Randomly (seeded) select a stratified subset of LLM‑labelled PRs,
  * Export a JSONL `data/audit/audit_input.jsonl` containing diff snippets and the checklist columns,
  * Prompt the user (or read from a supplied `--answers-file`) for `human_ground_truth`,
  * Write decisions to `data/audit/audit_log.jsonl`,
  * Compute the error rate of the automated `source_type` vs. human ground truth and write `data/audit/error_rate.json` (`{"error_rate": <float>}`) and a summary `manual_audit_results.json`.  
  – **Verification**: Running `python -m code.audit.manual_validation --dry-run` creates the three artefacts; providing an answers file makes the script exit with status 0 and the error‑rate file contains a numeric value between 0 and 1.  If no answers are supplied, the script exits non‑zero with a clear message (“Manual audit required”).

- [ ] T065 Implement a gating step `code/analysis/generate_results_report.py` that:
  * Reads `data/audit/error_rate.json` (if present) and the count of LLM PRs,
  * Writes `data/processed/gate_status.json` with `{"status": "blocked"}` if `error_rate > 0.05`, `{"status": "exploratory"}` if `N_LLM < 10`, otherwise `{"status": "passed"}`,
  * If the error‑rate file is missing, writes `{"status": "human_input_needed"}` and exits non‑zero,
  * Merges the gate status into the final `results.json` (adds a top‑level field `gate_status`).  
  – **Verification**: After a successful audit, the gate file exists with one of the three allowed strings; the combined `results.json` now contains `"gate_status": "passed"` (or the appropriate alternative).

- [ ] T066 Create `code/analysis/visualizations.py` that:
  * Reads `prs_metrics.csv`,
  * Generates side‑by‑side boxplots for `comment_count` and `time_to_merge_minutes` by `source_type`,
  * Generates histograms of the same metrics,
  * Saves PDFs `reports/figures/boxplots.pdf` and `reports/figures/histograms.pdf` (each > 50 KB, ≥ 2 vector paths verified by `tests/integration/test_visualizations.py`).  
  – **Verification**: PDFs are produced, size check passes, and a test that opens the PDF confirms the presence of the expected subplot titles.

- [ ] T067 Implement `code/analysis/generate_report_narrative.py` that:
  * Loads `results.json`, `gate_status.json`, `complexity_correlation.json`,
  * Calls the narrative synthesis helper (T036c) to compose the Discussion and Limitations sections,
  * Inserts the quantitative findings into a markdown template `docs/report_template.md`,
  * Uses `matplotlib.backends.backend_pdf.PdfPages` to combine the markdown (converted via `pandoc` or a simple markdown‑to‑PDF renderer) with the two figure PDFs into a single `reports/final_report.pdf`.  
  – **Verification**: The final PDF exists, contains the headings *Executive Summary*, *Methodology*, *Results*, *Discussion*, *Limitations*, and embeds the two figure pages.  If `gate_status` is `"blocked"` the script raises `ValueError` and aborts; if `"exploratory"` it adds a note about limited power.

- [ ] T068 Re‑run the entire workflow from the command line, update `quickstart.md` with the exact command sequence, and verify reproducibility:
  1. `python code/data/run_pipeline.py`  
  2. `python code/analysis/complexity.py`  
  3. `python code/data/extract_metrics.py`  
  4. `python code/analysis/statistical_tests.py`  
  5. `python -m code.audit.manual_validation --answers-file data/audit/sample_answers.csv` (or run interactively)  
  6. `python code/analysis/generate_results_report.py`  
  7. `python code/analysis/visualizations.py`  
  8. `python code/analysis/generate_report_narrative.py`  
  *After a fresh clone* following `quickstart.md` must reproduce **all** artefacts (`prs_labeled.csv`, `complexity_scores.csv`, `prs_metrics.csv`, `results.json`, `gate_status.json`, audit files, PDFs).  
  – **Verification**: A CI job that deletes the `data/` and `reports/` directories, runs the steps from `quickstart.md`, and asserts the existence and schema validity of each output passes without error.

---

## Phase 2 – Complete the study and validate its evidence

(Tasks T060–T068 collectively satisfy FR‑001 through FR‑008, SC‑001 through SC‑004, and the statistical requirements.)

---

## Phase 3 – Reproducible results and paper handoff

(Phase 3 is realized by T068, which documents the full end‑to‑end run and produces the final report PDF ready for downstream paper‑stage handoff.)

--- 

### Dependency and requirement coverage

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001 (download ≤200 PRs) | T013, T018, T060 |
| FR‑002 (classification & confidence) | T014, T015a, T060 |
| FR‑003 (review metrics) | T062 |
| FR‑004 (t‑test & effect sizes) | T063, T065 |
| FR‑005 (complexity) | T061 |
| FR‑006 (visualizations) | T066, T067 |
| FR‑007 (secondary detector) | T015a, T060 |
| FR‑008 (sensitivity analysis) | T026, T063, T065 |
| SC‑001 / SC‑002 (comment & time significance) | T063 |
| SC‑003 (complexity correlation) | T035, T065 |
| SC‑004 (audit error‑rate < 5 %) | T064, T065 |

All tasks respect data‑flow ordering, use real GitHub data, and never fall back to synthetic placeholders.