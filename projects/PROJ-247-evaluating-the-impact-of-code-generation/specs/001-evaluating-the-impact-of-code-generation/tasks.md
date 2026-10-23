# Tasks: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

**Inputs**: `specs/001-code-maintainability-impact/spec.md`, `plan.md`, data‑model.md, contracts, original idea, verifier feedback.  
All tasks must produce **real** artifacts (GitHub data, ONNX inference, etc.) and must run on the default CPU‑first CI environment.

---

## Phase 1 – Setup and first end‑to‑end analysis  

**Goal**: Verify that the pipeline can run on a small real subset of repositories and produce the first usable tagged‑and‑matched dataset.

- [ ] T000 [US1] **A‑priori power analysis**  
  - Using the `statsmodels.stats.power.WilcoxonPower` function, simulate a range of matched‑pair sample sizes to determine the minimum number required to achieve 0.80 power for detecting a medium effect size (rank‑biserial ≥ 0.3) with α = 0.05.  
  - Target **≥ 250 matched pairs** (as required by FR‑009).  
  - Output the result to `data/analysis/power_analysis_a_priori.json` containing fields `target_pairs`, `achieved_power`, `effect_size_target`.  
  - **Verification**: A pytest test `test_power_a_priori.py` checks that `target_pairs >= 250` and that the JSON file exists.

- [ ] T001 [US1] **Create project‑level configuration files**  
  - Add a `.env.example` at the project root defining `GITHUB_TOKEN`, `DATA_PATH=./data`, and `LOG_PATH=./logs`.  
  - Add a logging configuration file `code/config/logging.yaml` (standard Python logging dictConfig) that routes INFO‑level logs to `$(LOG_PATH)/pipeline.log`.  
  - Update `specs/001-code-maintainability-impact/quickstart.md` to include the command `source .env.example && python code/main.py --stage quickstart` and a note that the `.env` file must be populated with a personal GitHub token.  
  - **Verification**:  
    1. Load the `.env.example` with `python -c "import dotenv; dotenv.load_dotenv('.env.example')"` and ensure the three variables are present.  
    2. Parse `code/config/logging.yaml` with `yaml.safe_load` without error.  
    3. Assert that `quickstart.md` contains the exact command line string.

- [ ] T002 [US1] **Implement repository search & shallow clone, write CSV outputs**  
  - In `code/01_data_curation.py` query the GitHub Search API for repositories with `topic:llm-generated` or `topic:copilot`; if fewer than 50 are found, expand to the keywords `"LLM generated code"` and `"Copilot generated"` until the target is met or the API limit is reached.  
  - Apply activity filters (≥ 1 commit in last 90 days, ≥ 5 ★) and record each repository’s `owner/name`, `stargazers_count`, `created_at`, `updated_at`, and total LOC (computed with `cloc` on the shallow clone).  
  - Perform a shallow clone (`git clone --depth 100`) for each repository into `data/raw/clones/<repo_id>/`.  
  - Write two CSV files **exactly** to `data/raw/`:  
    1. `repo_list.csv` – columns `repo_id,clone_path,clone_status`.  
    2. `repo_metadata.csv` – columns `repo_id,stars,created_at,updated_at,total_loc`.  
  - **Verification**: After running the script, assert that both CSV files exist, are non‑empty, contain at least 50 rows, and that each row has valid fields. A pytest test `test_curation_outputs.py` performs these checks.

- [ ] T003 [US1] **Extract code blocks with rename tracking and unit tests**  
  - Implement `code/03_code_block_extraction.py` to walk each cloned repository, parse **Python** (`ast`) and **JavaScript** (`tree‑sitter`) files, and extract top‑level functions/classes as code blocks.  
  - For each block record `block_id` (`repo_id:file_path:start_line:end_line`), `file_path`, `start_line`, `end_line`, `language`, `introduction_commit` (first commit containing the block via `git log --diff-filter=A`), and `introduction_timestamp`.  
  - Use `git log --follow` to detect renames; if a block’s file path changes in a way that alters the directory depth or parent folder, **exclude** the block and log the exclusion to `data/logs/refactor_exclusions.log` (`block_id,old_path,new_path,reason`).  
  - Write the full list of extracted blocks to `data/raw/code_blocks.csv`.  
  - Provide focused unit tests in `code/tests/unit/test_git_mv_detection.py` covering (a) no rename, (b) rename within same directory, (c) rename across directories (should be excluded).  
  - **Verification**: The script exits with status 0, the CSV exists with ≥ 100 rows, and all unit tests pass (`pytest -q code/tests/unit/test_git_mv_detection.py`).

- [ ] T004 [US1] **Classify blocks with CodeBERT, add static metrics, and document classifier provenance**  
  - Load the ONNX‑converted `microsoft/codebert-base` model using `onnxruntime` (CPU).  
  - For each block in `data/raw/code_blocks.csv`, run inference to obtain a probability for “LLM”. Assign label **LLM** if `p ≥ 0.8`, otherwise **Human**; blocks with confidence `< 0.8` are excluded and logged to `data/logs/classifier_exclusions.log`.  
  - Compute static complexity metrics with `radon` (cyclomatic complexity, maximum nesting depth, LOC) and append them to each retained block.  
  - Output the final tagged dataset to `data/processed/tagged_blocks.csv`, which must conform to the `TaggedCodeBlock` schema (`specs/001‑.../contracts/dataset.schema.yaml`).  
  - Add a citation entry in `docs/references.bib` for *Zhang et al., 2023* (the CodeBERT validation study) and a short description in `docs/methods/classifier.md` summarising the reported ≥ 80 % accuracy **and** include the concrete validation numbers (accuracy = 0.84, F1 = 0.82 on a held‑out benchmark).  
  - **Verification**: Run a smoke test on three known blocks (`python code/04_classifier_smoke_test.py`) that prints label and confidence; ensure the CSV validates against the schema (use `jsonschema.validate`). Also check that the citation file contains the new entry.

- [ ] T005 [US1] **Ground‑truth verification on a statistically adequate sample**  
  - Randomly select **≥ 100** tagged blocks (stratified by predicted label) using a fixed seed (`SEED=20261023`) and write their identifiers to `data/ground_truth/manual_labels.csv`.  
  - Provide the source snippets (`block_id, code_snippet`) to human annotators (outside the CI) and collect their labels in `data/ground_truth/manual_labels_completed.csv`.  
  - Compute **precision**, **recall**, **95 % Wilson confidence intervals**, and **F1** for the classifier on this sample; write the results to `data/ground_truth/classifier_metrics.json` following the `ground_truth_schema`.  
  - Verify that both precision and recall are **≥ 0.85**; if not, record `threshold_met: false` and a brief reason in `docs/paper/limitations.json`.  
  - **Verification**: A pytest test `test_classifier_metrics.py` loads the JSON, asserts the thresholds, and also checks that the CI‑reported confidence intervals are present and non‑null.

- [ ] T006 [US1] **Perform propensity‑score matching within repositories**  
  - Using `data/processed/tagged_blocks.csv`, fit a logistic regression (scikit‑learn) on covariates: cyclomatic complexity, LOC, repository stars, repository age (days), total repository LOC, developer count, test‑coverage proxy, prior bug density, average contributor tenure, and code domain.  
  - Compute propensity scores and perform **1:1 nearest‑neighbor matching** (`NearestNeighbors(n_neighbors=1)`) **within the same repository** with a caliper of 0.05.  
  - Write all matched pairs to `data/processed/matched_pairs.csv`.  
  - Enforce the inclusion rule: a repository must have at least **2 LLM‑generated** and **2 Human‑written** blocks after tagging; repositories failing this are logged to `data/logs/repo_exclusions.csv` and omitted from the final filtered file `data/processed/matched_pairs_filtered.csv`.  
  - Ensure no `block_id` appears in more than one pair.  
  - **Verification**: A test script checks for duplicate block IDs, confirms that every retained repository satisfies the ≥ 2 LLM / ≥ 2 Human rule, and that the filtered file contains ≥ 250 pairs (or logs the shortfall).

---

## Phase 2 – Complete the study and validate its evidence  

**Goal**: Compute longitudinal maintenance metrics, run the full statistical analysis, and produce all required visualisations.

- [ ] T007 [US2] **Extract longitudinal metrics (code churn & bug‑fix latency) and write per‑event records**  
  - For each block in `matched_pairs_filtered.csv`, identify the **introduction commit** (from the tagging step) and define the observation window of **six months** (primary) and **three months** (secondary).  
  - **Code churn**: Use `git log --follow --since=<introduction_date> --until=<window_end>` to sum lines added + deleted for the block (exclude the generation commit). Record `churn_lines` and compute normalized `churn_rate = churn_lines / loc`.  
  - **Bug‑fix latency**: Scan commits within the window for messages containing `Fixes #N` or `Closes #N`. For each matched issue, query the GitHub Issues API to obtain the issue’s `closed_at` timestamp and compute `latency_days = closed_at – commit_timestamp`. If no linked issue exists, record `latency_days = null` (right‑censored).  
  - **Maintenance events**: For every churn change and every bug‑fix linkage, emit a `MaintenanceEvent` record adhering to the `MaintenanceEvent` schema and write all records to `data/processed/maintenance_events.json`.  
  - Persist per‑pair results to `data/processed/metrics_longitudinal.csv` complying with `metrics.schema.yaml`.  
  - Log any exclusions (e.g., missing issues, 404 repo deletions) to `data/logs/metric_exclusions.log`.  
  - **Verification**: Run the script on a single repository, compare a hand‑checked block’s churn and latency against the output, and assert that `maintenance_events.json` validates against its schema.

- [ ] T008 [US1] **Merge all processed artifacts into a master dataset**  
  - Join `tagged_blocks.csv`, `matched_pairs_filtered.csv`, and `metrics_longitudinal.csv` on block IDs, adding repository‑level fields (`repo_stars`, `repo_age_days`, `repo_total_loc`).  
  - Output the consolidated file to `data/processed/master_dataset.json`, which must validate against the `dataset_schema.schema.yaml`.  
  - **Verification**: Use a validation script that loads the JSON and runs `jsonschema.validate`; the script must exit with status 0.

- [ ] T009 [US3] **Perform statistical analysis with cluster‑robust permutation and FDR control**  
  - Load `master_dataset.json`.  
  - For **code churn**, compute the paired differences (LLM – Human) and apply a **stratified within‑repo permutation test** (permute labels within each matched pair, aggregate across repos) to obtain a Wilcoxon W‑statistic and a permutation‑based p‑value.  
  - For **bug‑fix latency**, first drop pairs where either latency is null, then run the same permutation‑based Wilcoxon test.  
  - Compute **rank‑biserial correlation** and its 95 % CI for each outcome.  
  - Apply the **Benjamini‑Yekutieli** procedure across the two tests; store adjusted p‑values.  
  - Write results to `data/analysis/wilcoxon_results.json` following the `metrics_schema` contract, including `analysis_metadata`, `tests`, and `figures` placeholders.  
  - **Verification**: Run the analysis on the **real** `master_dataset.json` produced by the pipeline and assert that the output file exists, validates against the schema, and contains non‑null statistics.

- [ ] T010a [US3] **Coverage verification for paired metrics (SC‑007)**  
  - Compute the proportion of matched pairs that have **both** non‑null churn **and** latency values.  
  - Assert that this proportion is ≥ 0.90; if not, emit a warning and record the exact proportion in `data/analysis/metric_coverage_report.json`.  
  - **Verification**: A pytest test loads the report and fails the CI if the threshold is not met.

- [ ] T010b [US3] **Robustness of conclusions across observation windows**  
  - Compare the effect sizes and significance from the 6‑month and 3‑month analyses (outputs from T007).  
  - Assert that the direction (sign of rank‑biserial) and the BY‑adjusted significance (p < 0.05) are identical across windows; otherwise, log a discrepancy in `data/analysis/window_consistency.json` and fail the verification.  
  - **Verification**: Test script checks the JSON flags and fails if inconsistency detected.

- [ ] T011 [US3] **Post‑hoc power verification**  
  - Using `statsmodels.stats.power.WilcoxonPower`, compute the achieved power given the observed sample size, effect size (rank‑biserial), and α = 0.05.  
  - Write the output to `data/analysis/power_analysis_posthoc.json` (fields: `sample_size`, `achieved_power`, `target_power`, `effect_size_observed`).  
  - **Verification**: The JSON must contain `achieved_power >= 0.80`; if not, the script logs a warning.

- [ ] T012 [US3] **Generate final visualisations**  
  - Create **box plots** for normalized churn rates (LLM vs Human) and **kernel density plots** for bug‑fix latency (excluding nulls) using `matplotlib` in CPU‑only mode.  
  - Save PNG files (< 2 MB) to `figures/fig_churn_boxplot.png` and `figures/fig_latency_density.png`.  
  - Populate the `figures` array in `wilcoxon_results.json` with `figure_name`, `file_path`, `metric`, and `file_size_bytes`.  
  - **Verification**: A test checks that each PNG exists, is a valid image, and its size ≤ 2 MB.

- [ ] T013 [US3] **Write methods & results summary for paper handoff**  
  - Draft `docs/paper/results_summary.md` that:  
    * Describes the dataset creation (repo search, block extraction, classifier, matching).  
    * Reports classifier precision, recall, and 95 % CIs.  
    * Presents the Wilcoxon W‑statistics, raw and BY‑adjusted p‑values, rank‑biserial effect sizes, and confidence intervals.  
    * Summarises the power analysis, sensitivity analyses (window & bias), and any exclusions.  
    * Discusses limitations (observational design, reliance on topic tags, confidence‑filter bias, 404 repo deletions).  
  - Link directly to artifact files (e.g., `data/analysis/wilcoxon_results.json`, `figures/fig_churn_boxplot.png`).  
  - **Verification**: A lint test ensures all referenced paths exist and that the markdown contains the required sections.

- [ ] T014a [US3] **Re‑run the full pipeline from the quickstart command and verify reproducibility**  
  - Execute `source .env.example && python code/main.py --stage quickstart` which orchestrates tasks T002–T013 in order.  
  - Run the full test suite (`pytest -q`) and assert that all contract‑validation tests pass.  

- [ ] T014b [US3] **Compute‑resource enforcement (FR‑016)**  
  - Before the full pipeline runs, check that the execution environment reports at least 4 CPU cores and 16 GB of RAM (or that a self‑hosted runner is being used).  
  - If the requirement is not met, abort with a clear error message.  
  - **Verification**: A pytest test `test_compute_resources.py` reads `/proc/cpuinfo` and `/proc/meminfo` (or platform equivalents) and fails if the thresholds are not satisfied.

- [ ] T015 [US3] **Archive raw GitHub API responses and clone snapshots for future reproducibility**  
  - After a successful full run, copy the raw API JSON responses (`data/raw/github_api/*.json`) and the shallow clone directories (`data/raw/clones/`) into a compressed archive `data/archive/run_<timestamp>.tar.gz`.  
  - Record the archive’s SHA‑256 checksum in `docs/paper/archive_checksum.txt`.  
  - **Verification**: A checksum verification script confirms the archive integrity.

- [ ] T016 [US3] **Document computational environment**  
  - Export the exact Python environment (`pip freeze > requirements.txt`) and capture the OS details (`uname -a`) into `docs/environment.txt`.  
  - Include these files in the handoff archive generated by T014.  
  - **Verification**: The CI step checks that `requirements.txt` contains the pinned versions listed in the plan and that `environment.txt` is non‑empty.

--- 

## Phase 3 – Reproducible results and paper handoff  

- [ ] T017 [US3] **Finalize handoff package**  
  - Consolidate `master_dataset.json`, `wilcoxon_results.json`, the two PNG figures, `archive_checksum.txt`, `environment.txt`, and all provenance files into `docs/paper/handshake.yaml` listing each artifact’s SHA‑256 hash.  
  - Ensure the handshake file is present and syntactically valid YAML.  
  - **Verification**: A test parses the YAML and checks that each listed file exists and that the recorded hash matches the on‑disk hash.