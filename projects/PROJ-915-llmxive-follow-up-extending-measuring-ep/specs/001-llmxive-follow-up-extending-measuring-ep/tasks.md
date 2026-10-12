# Tasks: llmXive follow‑up “Measuring Epistemic Resilience of LLMs Under Misleading Medical Context”

**Input**: `spec.md`, `plan.md`, `data‑model.md`, contracts in `specs/001-llmxive-follow-up-extending-measuring-ep/`  
**Verification**: Each task must produce the file(s) listed in its description; the verifier will check existence, schema compliance, and any unit‑test outcomes.

---

## Phase 1 – Project bootstrap & tooling  

- [ ] T001 [US0] Create the required project directory hierarchy under `projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/` (sub‑folders `code/`, `data/raw/`, `data/processed/`, `data/interim/`, `data/results/`, `state/`, `tests/unit/`, `tests/integration/`, `docs/`). Capture the layout with `tree -L 2` and write it to `data/results/project_structure.txt`.  
  **Artifacts**: `data/results/project_structure.txt`.  
  **Verification**: The file must list all expected directories; a unit test `tests/unit/test_structure.py` asserts the presence of each sub‑folder.

- [ ] T002 [US0] Initialize a Python 3.11 virtual environment, pin exact dependency versions, and generate `requirements.txt` (including `datasets`, `scikit-learn`, `statsmodels`, `sentence‑transformers`, `llama‑cpp‑python`, `pandas`, `numpy`, `tqdm`, `biopython`, `firth‑logistic`, `requests`, `ruff`, `black`).  
  **Artifacts**: `requirements.txt`.  
  **Verification**: `pip install -r requirements.txt` runs without conflicts; a test `tests/unit/test_requirements.py` checks that the file contains at least the listed packages.

- [ ] T003a [US0] Create the lint‑configuration file `code/.ruff.toml` that enables the project‑standard rules (max line length 100, ignore `__init__.py`, enforce `flake8‑annotations`).  
  **Artifacts**: `code/.ruff.toml`.  
  **Verification**: Running `ruff check code/` returns exit code 0; a test `tests/unit/test_ruff_config.py` parses the file and confirms the expected settings.

- [ ] T003b [US0] Create `pyproject.toml` configuring Black (line length 100, target Python 3.11).  
  **Artifacts**: `pyproject.toml`.  
  **Verification**: `black --check code/` returns exit code 0.

- [ ] T003c [US0] Add a verification step that asserts `code/.ruff.toml` exists after T003a; fail the pipeline with a clear error if missing.  
  **Artifacts**: Updated `code/validation.py` (or a tiny script) to perform the check.  
  **Verification**: The pipeline aborts with an informative message when the file is absent.

- [ ] T004 [US0] Implement `code/config.py` with global constants (`SEED = 42`, `MAX_RUNTIME_HOURS = 6`, `DATA_ROOT = Path("../data")`, `RESULTS_ROOT = Path("../data/results")`).  
  **Artifacts**: `code/config.py`.  
  **Verification**: Importing `code.config` yields the constants; a unit test `tests/unit/test_config.py` asserts `MAX_RUNTIME_HOURS == 6`.

- [ ] T005 [US0] Add a lightweight logging helper in `code/validation.py` that creates `data/results/pipeline_log.json` (initial empty JSON object) and provides `log_stage(stage_name)` to append ISO‑8601 timestamps.  
  **Artifacts**: `code/validation.py`, `data/results/pipeline_log.json`.  
  **Verification**: After calling `log_stage("ingestion")`, the JSON contains the key `"ingestion"` with a timestamp.

- [ ] T006 [US0] Extend `code/validation.py` with a compute‑time guard `check_runtime()` that sums elapsed stage times from `pipeline_log.json` and raises `TimeoutError` if the total exceeds `MAX_RUNTIME_HOURS`. On abort it writes `data/results/compute_time_report.md`.  
  **Artifacts**: Updated `code/validation.py`, `data/results/compute_time_report.md` (when triggered).  
  **Verification**: Simulated over‑run produces the markdown and the exception.

---

## Phase 2 – Data ingestion & linguistic feature extraction (User Story 1)  

- [ ] T007 [US1] Implement `code/ingestion.py` to stream‑download MedMisBench via `datasets.load_dataset(..., streaming=True)`, filter for `source_label` in {`Authority‑framed`, `Exception‑poisoning`}, and write rows to `data/raw/medmis_subset.csv`. Record the total number of prompts in this isolated subset to `data/results/ingestion_counts.json`. Process in chunks of ≤ 1000 rows, compute a SHA‑256 checksum stored in `state/artifact_hashes.yaml`. The script must **fail loudly** on any download error (no synthetic fallback).  
  **Artifacts**: `code/ingestion.py`, `data/raw/medmis_subset.csv`, `data/results/ingestion_counts.json`, `state/artifact_hashes.yaml`.  
  **Verification**: CSV exists with ≥ 500 rows; checksum entry matches the file’s hash; a unit test `tests/unit/test_ingestion.py` validates chunked processing.

- [ ] T008 [US1] Implement `code/features.py` to read `medmis_subset.csv`, compute linguistic features defined in `features.schema.yaml` (modal verb count, imperative‑to‑declarative ratio, citation density, sentence count). Division‑by‑zero cases set `imperative_ratio` to `NaN` and add a boolean column `ratio_undefined`. Record the number of successfully processed rows to `data/results/processing_counts.json`. Output to `data/processed/features.csv`.  
  **Artifacts**: `code/features.py`, `data/processed/features.csv`, `data/results/processing_counts.json`.  
  **Verification**: CSV validates against `features.schema.yaml`; a test `tests/unit/test_features.py` checks a known prompt yields expected counts.

- [ ] T009 [US1] Add a logging entry `ingestion_log.txt` in `data/results/` that records whether batch mode was enabled and the total number of processed rows.  
  **Artifacts**: `data/results/ingestion_log.txt`.  
  **Verification**: File contains the line “Batch mode enabled (chunks of 1000)” when applicable.

---

## Phase 3 – Human annotation pilot (hard validation gate)  

- [ ] T010 [US1] Create `code/annotation.py` function `generate_survey_payload()` that writes `data/raw/survey_payload.json` containing, for each prompt, `prompt_id`, `raw_text`, and the extracted features from `features.csv`. Also write `docs/recruitment_instructions.md` describing how to recruit ≥ 50 raters on Prolific and collect responses into `data/raw/human_pilot_raw.csv`.  
  **Artifacts**: `code/annotation.py`, `data/raw/survey_payload.json`, `docs/recruitment_instructions.md`.  
  **Verification**: JSON contains ≥ 50 entries; the markdown exists.

- [ ] T010c [US1] Run the human annotation pilot on Prolific (or an equivalent crowdsourcing platform), collect the raters’ responses, and store them as `data/raw/human_pilot_raw.csv`. This task bridges the gap between payload generation and raw data availability.  
  **Artifacts**: `data/raw/human_pilot_raw.csv`.  
  **Verification**: CSV exists with columns `prompt_id`, `rater_id`, `authority_score` and at least 50 rows.

- [ ] T010b [US1] Implement `code/annotation.py` function `ingest_human_ratings()` that reads the externally collected rater responses (produced by T010c) and writes them to `data/raw/human_pilot_raw.csv` to ensure the data is available for the project pipeline.  
  **Artifacts**: Updated `code/annotation.py` (ingest function).  
  **Verification**: CSV exists and contains the expected schema.

- [ ] T011 [US1] Implement `code/annotation.py` function `verify_pilot_completion()` that checks for `data/raw/human_pilot_raw.csv`, validates its schema (`prompt_id`, `rater_id`, `authority_score`), and sets `"human_pilot_ready": true` in `pipeline_log.json`. On missing or malformed file, raise `RuntimeError` with a clear message.  
  **Artifacts**: Updated `code/annotation.py`, updated `pipeline_log.json`.  
  **Verification**: After running `python -m code.annotation verify`, the log contains the flag.

- [ ] T012 [US1] Implement `code/annotation.py` function `load_pilot_data()` that reads `human_pilot_raw.csv`, verifies that every `prompt_id` exists in `features.csv`, and writes a clean copy to `data/interim/human_pilot_loaded.csv`.  
  **Artifacts**: `data/interim/human_pilot_loaded.csv`.  
  **Verification**: The file exists and row count matches the raw file.

- [ ] T013 [US1] Implement `code/annotation.py` function `clean_pilot_data()` that (1) removes any rater whose responses on 5 control items have < 80 % agreement, (2) drops rows with missing `authority_score`, and (3) aborts with `RuntimeError` if fewer than 50 rows remain. Output to `data/interim/human_pilot_cleaned.csv`.  
  **Artifacts**: `data/interim/human_pilot_cleaned.csv`.  
  **Verification**: CSV exists, has ≥ 50 rows, and a test `tests/unit/test_clean_pilot.py` confirms the control‑item logic.

- [ ] T014 [US1] Implement `code/annotation.py` function `compute_correlation_and_kappa()` that merges `human_pilot_cleaned.csv` with `features.csv`, computes Pearson (or Spearman) correlation between each linguistic feature and `authority_score`, and calculates Cohen’s κ across raters. Save as JSON `data/results/feature_correlation_and_kappa.json` with keys `correlation_coefficients` (dict) and `cohen_kappa`.  
  **Artifacts**: `data/results/feature_correlation_and_kappa.json`.  
  **Verification**: JSON contains numeric values for every feature; a test `tests/unit/test_correlation.py` validates the structure.

- [ ] T015 [US1] Create the **hard validation gate** `validate_human_pilot()` in `code/annotation.py`. It reads `feature_correlation_and_kappa.json` and checks that **r > 0.6** *and* **κ > 0.7**. It writes `data/results/feature_validation_report.md` whose first line is either “PASS” or “FAIL” followed by the numeric thresholds. On FAIL it raises `RuntimeError`.  
  **Artifacts**: `data/results/feature_validation_report.md`.  
  **Verification**: After execution, the markdown exists and its first line matches the numeric check.

- [ ] T016 [US1] Implement `code/annotation.py` function `contingency_report()` that is invoked automatically when `validate_human_pilot()` raises an error. It writes `data/results/contingency_report.md` explaining that the pilot did not meet quality thresholds and sets `"human_pilot_failed": true` in `pipeline_log.json`.  
  **Artifacts**: `data/results/contingency_report.md`, updated `pipeline_log.json`.  
  **Verification**: The markdown exists and contains the word “FAIL”; the log flag is present.

---

## Phase 4 – Model inference & adherence labeling (User Story 2)  

- [ ] T017 [US2] Write unit test `tests/unit/test_labeling_independence.py` asserting that the labeling function signature does **not** accept a feature vector argument. The test must initially fail.  
  **Artifacts**: `tests/unit/test_labeling_independence.py`.  
  **Verification**: Running `pytest tests/unit/test_labeling_independence.py` fails before labeling code exists.

- [ ] T018 [US2] Implement `code/inference.py` to load the quantized `TinyLlama‑1.1B‑Chat` model via `llama_cpp` with `device="cpu"` and generate a response for each prompt with a **30 s timeout**. On timeout, log the `prompt_id` to `data/interim/timeout_failures.log`, set `generation_time = 30.0`, and continue. Store raw generations in `data/interim/raw_responses.csv`.  
  **Artifacts**: `code/inference.py`, `data/interim/raw_responses.csv`, `data/interim/timeout_failures.log`.  
  **Verification**: A deliberately slow prompt appears in the log with `generation_time = 30.0`.

- [ ] T019 [US2] Implement `code/labeling.py` function `fetch_external_fact(prompt_id, false_claim)` that queries PubMed via Biopython’s Entrez API, extracts the first abstract, and writes a mapping `prompt_id → external_fact` to `data/interim/external_facts.json`. The function must raise `RuntimeError` on any API failure.  
  **Artifacts**: `code/labeling.py`, `data/interim/external_facts.json`.  
  **Verification**: After processing a sample prompt, the JSON contains the expected abstract text.

- [ ] T020 [US2] Add semantic‑similarity scoring in `code/labeling.py` using a `sentence‑transformers` model to compute `sim_false` (output vs. false claim) and `sim_correct` (output vs. external fact). Store scores in `data/interim/similarity_scores.csv`.  
  **Artifacts**: `data/interim/similarity_scores.csv`.  
  **Verification**: CSV contains columns `prompt_id`, `sim_false`, `sim_correct` with values in [0, 1].

- [ ] T021 [US2] Implement the three‑state labeling logic in `code/labeling.py` (rules from the spec). Output `data/interim/labeled_responses_raw.csv` with columns `prompt_id`, `generated_text`, `adherence_label`, `generation_time`, `is_refusal`, `safety_refusal`, `labeling_method`.  
  **Artifacts**: `data/interim/labeled_responses_raw.csv`.  
  **Verification**: Spot‑check on a known prompt yields the expected label.

- [ ] T022 [US2] Add safety‑trigger detection (regex list) inside `code/labeling.py`; set `safety_refusal` accordingly.  
  **Artifacts**: Updated `code/labeling.py`.  
  **Verification**: Prompts containing phrases like “I cannot …” have `safety_refusal = true` in the CSV.

- [ ] T023 [US2] Merge intermediate artifacts (`features.csv`, `labeled_responses_raw.csv`, `similarity_scores.csv`, `external_facts.json`) into a single dataset `data/interim/labeled_responses.csv` that conforms to `labeling.schema.yaml`. Abort with a clear error if any required column is missing.  
  **Artifacts**: `data/interim/labeled_responses.csv`.  
  **Verification**: Validation test `tests/unit/test_label_schema.py` confirms compliance.

- [ ] T024 [US2] Run the unit test from **T017** to confirm labeling independence now passes.  
  **Artifacts**: Updated labeling code.  
  **Verification**: `pytest tests/unit/test_labeling_independence.py` returns exit code 0.

---

## Phase 5 – Statistical modeling & sensitivity analysis (User Story 3)  

- [ ] T025 [US3] Implement Model A in `code/modeling.py`: logistic regression (Adherent vs Non‑Adherent) using `statsmodels.api.Logit` on linguistic features, excluding rows where `ratio_undefined` is true. Save raw coefficients to `data/results/model_a_raw.csv`.  
  **Artifacts**: `code/modeling.py`, `data/results/model_a_raw.csv`.  
  **Verification**: CSV contains columns `feature_name`, `coefficient`, `std_err`, `p_value`.

- [ ] T026 [US3] Implement Model B in `code/modeling.py`: logistic regression (Refusal vs Non‑Refusal) excluding rows where `safety_refusal = true`. Save to `data/results/model_b_raw.csv`.  
  **Artifacts**: `data/results/model_b_raw.csv`.  
  **Verification**: Same schema as Model A.

- [ ] T027 [US3] Add diagnostics in `code/modeling.py` to detect perfect separation (e.g., infinite coefficients or convergence warnings). Write a flag `perfect_separation` to `data/results/convergence_log.csv`.  
  **Artifacts**: `data/results/convergence_log.csv`.  
  **Verification**: The CSV contains a row per model with `status = converged` or `status = separation_detected`.

- [ ] T028 [US3] If perfect separation is detected, automatically fall back to Firth’s penalized logistic regression via the `firth‑logistic` package, overwrite the model coefficients, and set `status = firth_fallback` in `convergence_log.csv`.  
  **Artifacts**: Updated `model_a_raw.csv` / `model_b_raw.csv`, updated `convergence_log.csv`.  
  **Verification**: After a separation case, the log shows `firth_fallback` and the result files exist.

- [ ] T029 [US3] Apply Holm‑Bonferroni correction to all raw p‑values from Models A and B using `statsmodels.stats.multitest.multipletests`. Append columns `p_corrected` and `is_significant` (p_corrected < 0.05) and write the unified table to `data/results/regression_results.csv`.  
  **Artifacts**: `data/results/regression_results.csv`.  
  **Verification**: CSV validates against `analysis.schema.yaml`; a test `tests/unit/test_analysis_schema.py` passes.

- [ ] T030 [US3] Generate a human‑readable Markdown summary `data/results/regression_summary.md` that lists, for each model, the features that are significant after correction.  
  **Artifacts**: `data/results/regression_summary.md`.  
  **Verification**: The markdown contains at least one feature marked “Significant” per model (if any).

- [ ] T031 [US3] Implement a sensitivity sweep over probability thresholds `{0.01, 0.05, 0.10}` to compute Attack Success Rate (ASR) and Refusal Rate at each threshold. Write results to `data/results/sensitivity_analysis.csv` and a concise report `data/results/sensitivity_report.md` that includes the variance metric and emits a “WARNING” line if variance > 5 %.  
  **Artifacts**: `data/results/sensitivity_analysis.csv`, `data/results/sensitivity_report.md`.  
  **Verification**: CSV has columns `threshold`, `asr`, `refusal_rate`, `variance`; the markdown contains “WARNING” when appropriate.

- [ ] T032 [US3] Programmatically write the baseline ASR (value 0.42) to `data/results/baseline_asr.yaml` (fields: `source`, `value`, `reference`).  
  **Artifacts**: `data/results/baseline_asr.yaml`.  
  **Verification**: YAML exists and `value == 0.42`.

- [ ] T033 [US3] Compare the computed ASR (from Model A) against the baseline. Append columns `computed_asr`, `baseline_asr`, `delta`, `interpretation` to `regression_results.csv`. Abort with an error if `baseline_asr.yaml` is missing.  
  **Artifacts**: Updated `data/results/regression_results.csv`.  
  **Verification**: The four new columns exist; a sanity test confirms `delta = computed_asr - baseline_asr`.

- [ ] T034 [US3] Add a selection‑bias warning module in `code/modeling.py` that calculates the overall adherence rate; if it is < 5 % or > 95 % write a warning “EXTREME_BASELINE” to `regression_results.csv` and generate an IPW sensitivity file `data/results/ipw_sensitivity.csv`.  
  **Artifacts**: Updated `regression_results.csv`, `data/results/ipw_sensitivity.csv`.  
  **Verification**: When the rate is extreme, the warning column reads “EXTREME_BASELINE”.

---

## Phase 6 – Polishing, reproducibility & hand‑off  

- [ ] T035 [US0] Update `README.md` to include a usage example (`python -m code.main --config config.yaml`), describe the directory layout, required Python version, and list the primary result artifacts.  
  **Artifacts**: `README.md`.  
  **Verification**: The README contains a fenced code block with the command and a bullet list of result files.

- [ ] T036 [US0] Run linting (`ruff check --fix code/`) and formatting (`black code/`). Ensure no lint errors remain.  
  **Artifacts**: Cleaned source files.  
  **Verification**: `ruff check code/` and `black --check code/` both return exit code 0.

- [ ] T037 [US0] Add a static‑analysis script `scripts/check_pii.py` that scans `code/validation.py` and `code/annotation.py` for any logging of raw prompt text or rater IDs, replacing them with hashed identifiers.  
  **Artifacts**: `scripts/check_pii.py`.  
  **Verification**: Running the script reports “No PII found”.

- [ ] T038 [US0] Execute the full pipeline (`python -m code.main`) and generate `data/results/validation_report.md` summarising each stage, its runtime, and a SHA‑256 checksum of the final `regression_results.csv`. This report must explicitly calculate the overall prompt completion rate (processed/total) and record it to verify SC‑001.  
  **Artifacts**: `data/results/validation_report.md`.  
  **Verification**: The markdown contains a table with all stages, timings, the checksum, and the completion rate percentage.

- [ ] T042 [US0] Compute the processed‑prompt completion rate (SC‑001) by dividing the number of successfully labeled prompts by the total number of prompts in the isolated MedMisBench subset; write the metric and a brief interpretation to `data/results/completion_rate.md`.  
  **Artifacts**: `data/results/completion_rate.md`.  
  **Verification**: The markdown reports a percentage ≥ 95 % when the pipeline meets the success criterion.

- [ ] T039 [US0] Unit‑test the compute‑time guard by mocking stage durations to exceed `MAX_RUNTIME_HOURS`; ensure `compute_time_report.md` is produced and the pipeline aborts. Store the test as `tests/unit/test_runtime_guard.py`.  
  **Artifacts**: `tests/unit/test_runtime_guard.py`, `data/results/compute_time_report.md` (when triggered).  
  **Verification**: The test passes; the report file is created during the mock run.

---

## Phase 7 – Final verification suite  

- [ ] T040 [US0] Run a consolidated verification suite that (1) executes every unit and integration test, (2) validates all JSON‑Schema contracts (`ingestion.schema.yaml`, `features.schema.yaml`, `labeling.schema.yaml`, `analysis.schema.yaml`, `sensitivity.schema.yaml`), (3) checks that all required output files exist, and (4) confirms no unchecked task remains without its artifact. Write a summary `data/results/verification_suite_report.md` with pass/fail counts. Abort if any check fails.  
  **Artifacts**: `data/results/verification_suite_report.md`.  
  **Verification**: The markdown reports “All checks passed” when the project is ready for reviewer hand‑off.

- [ ] T041 [US0] Verify the Quickstart guide (`quickstart.md`) by executing the outlined steps from a fresh environment and asserting that the primary result artifacts (e.g., `regression_results.csv`) are produced.  
  **Artifacts**: `data/results/quickstart_verification.log`.  
  **Verification**: The log confirms successful execution of every step listed in the Quickstart.
