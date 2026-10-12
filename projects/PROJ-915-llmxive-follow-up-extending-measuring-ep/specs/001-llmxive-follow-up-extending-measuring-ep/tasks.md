# Tasks: llmXive follow‑up “Measuring Epistemic Resilience of LLMs Under Misleading Medical Context”

**Input**: `spec.md`, `plan.md`, `data‑model.md`, contracts in `specs/001-llmxive-follow-up-extending-measuring-ep/`  
**Verification**: Each task must produce the file(s) listed in its description; the verifier will check existence, schema compliance, and any unit‑test outcomes.

---

## Phase 1 – Project bootstrap & tooling  

- [ ] **T001** [US0] Create the required project directory hierarchy and verify it with `tree -L 2`.  
  **Artifacts**:  
  - `projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/` (root)  
  - Sub‑folders: `code/`, `data/raw/`, `data/processed/`, `data/interim/`, `data/results/`, `state/`, `tests/unit/`, `tests/integration/`, `docs/`  
  **Verification**: Run `tree -L 2 projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/` and capture the output in `data/results/project_structure.txt`. The file must list all expected directories.

- [ ] **T002** [US0] Initialize a Python 3.11 environment and generate `requirements.txt` with the exact versions required by the plan (`datasets`, `scikit-learn`, `statsmodels`, `sentence‑transformers`, `llama‑cpp‑python`, `pandas`, `numpy`, `tqdm`, `biopython`, `firth‑logistic`, `requests`).  
  **Verification**: `pip install -r requirements.txt` must succeed without version conflicts.

- [ ] **T003a** [US0] Create a lint‑configuration file `code/.ruff.toml` that enables the project‑standard rules (max line length 100, ignore `__init__.py`, enforce `flake8‑annotations`).  
  **Verification**: `ruff check code/` runs with exit code 0; the file must exist.

- [ ] **T003b** [US0] Create `pyproject.toml` configuring Black (line length 100, target Python 3.11).  
  **Verification**: `black --check code/` returns 0.

---

## Phase 2 – Foundational infrastructure  

- [ ] **T005** [US0] Implement configuration management in `code/config.py` (seeds, data‑path constants, `MAX_RUNTIME_HOURS = 6`).  
  **Verification**: Importing `code.config` exposes the constants; a unit test `tests/unit/test_config.py` asserts `MAX_RUNTIME_HOURS == 6`.

- [ ] **T006a** [US0] Add a lightweight logging helper in `code/validation.py` that creates `data/results/pipeline_log.json` (initial empty JSON object) and records timestamps for each pipeline stage.  
  **Verification**: After running any stage, `pipeline_log.json` contains a new key with an ISO‑8601 timestamp.

- [ ] **T006b** [US0] Extend `code/validation.py` with an active compute‑time guard that sums elapsed stage times and aborts with a clear `TimeoutError` if the total exceeds `MAX_RUNTIME_HOURS`. On abort it writes `data/results/compute_time_report.md` summarising partial progress.  
  **Verification**: Simulated run (mocked short times) must leave `pipeline_log.json` unchanged; a forced over‑run must produce `compute_time_report.md` and raise the exception.

- [ ] **T007** [US0] Define the core data‑model classes (`PromptItem`, `ModelResponse`, `AnalysisResult`) in `code/data_models.py` with `@dataclass` annotations and type hints.  
  **Verification**: `python -c "from code.data_models import PromptItem; print(PromptItem.__annotations__)"` prints the expected field list.

- [ ] **T008** [US0] Create `code/error_handler.py` exposing `retry_with_backoff(callable, max_retries=3)` and `fatal_error(message)` utilities. The retry helper must implement exponential back‑off (1 s, 2 s, 4 s).  
  **Verification**: Unit test `tests/unit/test_error_handler.py` confirms back‑off timing and that `fatal_error` raises `RuntimeError`.

- [ ] **T044** [US0] Write the pipeline orchestrator `code/main.py` that sequentially invokes: ingestion → feature extraction → human‑pilot gate → inference → labeling → modeling → sensitivity analysis. It must read configuration from `code/config.py`, update `pipeline_log.json` after each step, and enforce the compute‑time guard.  
  **Verification**: Running `python -m code.main --dry-run` prints the ordered stage list and exits with code 0.

---

## Phase 3 – User Story 1: Data ingestion & linguistic feature extraction  

- [ ] **T013** [US1] Implement `code/ingestion.py` to stream‑download MedMisBench via `datasets.load_dataset(..., streaming=True)`, filter for `source_label` ∈ {`Authority‑framed`, `Exception‑poisoning`}, write rows to `data/raw/medmis_subset.csv`, and compute a SHA‑256 checksum stored in `state/artifact_hashes.yaml`. The script must **fail loudly** on any download error (no synthetic fallback) and must process the data in chunks (≤ 1000 rows) to stay within RAM limits.  
  **Verification**: After execution, `data/raw/medmis_subset.csv` exists, has ≥ 500 rows, and the checksum entry matches the file’s hash.

- [ ] **T014** [US1] Implement `code/features.py` to read `medmis_subset.csv`, compute the linguistic features defined in `features.schema.yaml` (modal verb count, imperative‑to‑declarative ratio, citation density, sentence count). Division‑by‑zero cases must set `imperative_ratio` to `NaN` and add a boolean column `ratio_undefined`. Output is `data/processed/features.csv`.  
  **Verification**: The CSV conforms to `features.schema.yaml`; a unit test `tests/unit/test_features.py` checks that a known prompt yields the expected counts.

- [ ] **T038** [US1] Add batch‑processing logic to `code/ingestion.py` that automatically switches to chunked streaming when the dataset size exceeds 1 000 rows, writing each chunk to the same CSV without reopening it.  
  **Verification**: Log file `data/results/ingestion_log.txt` contains the line “Batch mode enabled (chunks of 1000)”.

---

## Phase 3.5 – Human annotation pilot (hard validation gate)  

- [ ] **T017a‑Code** [US1] Create `code/annotation.py` function `generate_survey_payload()` that produces `data/raw/survey_payload.json` containing, for each prompt, `prompt_id`, `raw_text`, and the extracted features from `features.csv`. Also write `docs/recruitment_instructions.md` describing how a researcher should recruit ≥ 50 raters on Prolific, upload the survey, and collect responses into `data/raw/human_pilot_raw.csv`.  
  **Verification**: Both files exist; the JSON contains at least 50 entries.

- [ ] **T017b‑Protocol** [US1] *Manual* step – researchers follow `docs/recruitment_instructions.md` and upload the completed CSV `data/raw/human_pilot_raw.csv`. (No code change required.)

- [ ] **T017b‑Trigger** [US1] Add to `code/annotation.py` a function `verify_pilot_completion()` that checks for `data/raw/human_pilot_raw.csv`, validates the schema (`prompt_id`, `rater_id`, `authority_score`), and appends a `"human_pilot_ready": true` flag to `pipeline_log.json`. If the file is missing or malformed, raise `RuntimeError` with a clear message.  
  **Verification**: After running `python -m code.annotation verify`, the log contains `"human_pilot_ready": true`.

- [ ] **T017b‑Load** [US1] Extend `code/annotation.py` with `load_pilot_data()` that reads `human_pilot_raw.csv` and writes a clean copy to `data/interim/human_pilot_raw_loaded.csv`. It must verify that every `prompt_id` exists in `features.csv`.  
  **Verification**: The loaded file exists and has the same row count as the raw file.

- [ ] **T017c** [US1] Implement `clean_pilot_data()` in `code/annotation.py` that (1) removes any rater whose responses on a set of 5 control items have < 80 % agreement, (2) drops rows with missing `authority_score`, and (3) aborts with `RuntimeError` if fewer than 50 rows remain. Output is `data/interim/human_pilot_cleaned.csv`.  
  **Verification**: The CSV exists, has ≥ 50 rows, and a column `rater_id` with only accepted raters.

- [ ] **T017d** [US1] Add `compute_correlation_and_kappa()` to `code/annotation.py` that merges `human_pilot_cleaned.csv` with `features.csv`, computes Pearson (or Spearman) correlation between each linguistic feature and `authority_score`, and calculates Cohen’s κ across raters. Results are saved as JSON `data/results/feature_correlation_and_kappa.json` with keys `correlation_coefficients` (dict) and `cohen_kappa`.  
  **Verification**: The JSON file is present and contains numeric values for every feature.

- [ ] **T017e** [US1] Create the **hard validation gate** `validate_human_pilot()` in `code/annotation.py`. It reads `feature_correlation_and_kappa.json` and checks that **r > 0.6** *and* **κ > 0.7**. It writes a human‑readable report `data/results/feature_validation_report.md` containing “PASS” or “FAIL” and the numeric thresholds. On FAIL it raises `RuntimeError` halting the pipeline.  
  **Verification**: After execution, the markdown file exists; its first line is either “PASS” or “FAIL” matching the numeric check.

- [ ] **T017h** [US1] Implement `contingency_report()` in `code/annotation.py` that is invoked automatically when `validate_human_pilot()` raises an error. It writes `data/results/contingency_report.md` explaining that the pilot did not meet quality thresholds and that the pipeline must be paused for a new pilot. It also appends `"human_pilot_failed": true` to `pipeline_log.json`.  
  **Verification**: The contingency markdown exists and the log flag is set.

- [ ] **T017g** [US1] Record the outcome of the validation gate (PASS/FAIL) into `pipeline_log.json` (already implemented).  

---

## Phase 4 – User Story 2: Model inference & adherence labeling  

- [ ] **T019a** [US2] Write unit test `tests/unit/test_labeling_independence.py` that asserts the labeling function signature does **not** accept any feature vector argument. The test must fail before the labeling code is written.  
  **Verification**: The test file exists; running `pytest tests/unit/test_labeling_independence.py` fails initially.

- [ ] **T020‑Entrez** [US2] Implement `code/labeling.py` function `fetch_external_fact(prompt_id, false_claim)` that queries PubMed via Entrez (using the `biopython` Entrez API), extracts the first abstract, and stores the result in `data/interim/external_facts.json` (JSON mapping `prompt_id → external_fact`). The function must raise `RuntimeError` on any API failure.  
  **Verification**: After processing a sample prompt, the JSON file contains the expected abstract text.

- [ ] **T020a‑Timeout** [US2] Update `code/inference.py` to wrap the `llama_cpp` generation call in a cross‑platform timeout (30 s per prompt). On timeout, log the `prompt_id` to `data/interim/timeout_failures.log`, set `generation_time = 30.0`, and skip to the next prompt.  
  **Verification**: A deliberately slow prompt results in an entry in the log and the generated CSV records `generation_time = 30.0`.

- [ ] **T022** [US2] Add semantic‑similarity scoring in `code/labeling.py` using a `sentence‑transformers` model to compute `sim_false` (output vs. false claim) and `sim_correct` (output vs. external fact). Store both scores alongside the prompt ID in `data/interim/similarity_scores.csv`.  
  **Verification**: The CSV contains columns `prompt_id`, `sim_false`, `sim_correct` with values in [0, 1].

- [ ] **T023** [US2] Implement the three‑state labeling logic in `code/labeling.py` (rules defined in the spec). Output `data/interim/labeled_responses_raw.csv` with columns `prompt_id`, `generated_text`, `adherence_label`, `generation_time`, `is_refusal`, `safety_refusal`, `labeling_method`.  
  **Verification**: The file exists; a spot‑check on a known prompt yields the expected label.

- [ ] **T024** [US2] Add safety‑trigger detection (regex list) inside `code/labeling.py`; set `safety_refusal` accordingly.  
  **Verification**: Prompts containing “I cannot …” have `safety_refusal = true` in the CSV.

- [ ] **T025** [US2] Merge all intermediate artifacts (`features.csv`, `labeled_responses_raw.csv`, `similarity_scores.csv`, `external_facts.json`) into a single dataset `data/interim/labeled_responses.csv` that conforms to `labeling.schema.yaml`. Abort with a clear error if any required column is missing.  
  **Verification**: The merged CSV validates against `labeling.schema.yaml` (use `jsonschema` in a test).

- [ ] **T026** [US2] Run the unit test from **T019a** to confirm labeling independence after T025 is complete. The test must now pass; otherwise the pipeline aborts.  
  **Verification**: `pytest tests/unit/test_labeling_independence.py` returns exit code 0.

---

## Phase 5 – User Story 3: Statistical modeling & sensitivity analysis  

- [ ] **T029** [US3] Implement Model A in `code/modeling.py`: logistic regression (Adherent vs Non‑Adherent) using `statsmodels.api.Logit` on the linguistic features. Exclude rows where `ratio_undefined` is true. Save raw coefficients to `data/results/model_a_raw.csv`.  
  **Verification**: The CSV exists and contains columns `feature_name`, `coefficient`, `std_err`, `p_value`.

- [ ] **T030** [US3] Implement Model B in `code/modeling.py`: logistic regression (Refusal vs Non‑Refusal) **excluding** rows where `safety_refusal = true`. Save to `data/results/model_b_raw.csv`.  
  **Verification**: Same schema as Model A.

- [ ] **T031a** [US3] Add diagnostics to detect perfect separation for both models (use `statsmodels` warnings or check infinite coefficients). Write a flag `perfect_separation` to `data/results/convergence_log.csv`.  
  **Verification**: The CSV contains a row per model with `status = converged` or `status = separation_detected`.

- [ ] **T031b** [US3] If perfect separation is detected, automatically fall back to Firth’s penalized logistic regression via the `firth‑logistic` package, overwrite the model coefficients, and set `status = firth_fallback` in `convergence_log.csv`.  
  **Verification**: After a separation case, the log shows `firth_fallback` and the corresponding result files exist.

- [ ] **T032a** [US3] Apply Holm‑Bonferroni correction to all raw p‑values from Models A and B using `statsmodels.stats.multitest.multipletests`. Append the adjusted p‑value column `p_corrected` and a boolean `is_significant` (p_corrected < 0.05) to `data/results/regression_results.csv`.  
  **Verification**: The CSV contains the new columns and passes the `analysis.schema.yaml` validation.

- [ ] **T032b** [US3] Export the fully corrected regression table to `data/results/regression_results.csv` (already done by T032a) and also create a human‑readable Markdown summary `data/results/regression_summary.md` listing significant features per model.  
  **Verification**: The markdown file exists and lists at least one significant feature (if any).

- [ ] **T033‑Sensitivity** [US3] Implement a sweep over probability thresholds `{0.01, 0.05, 0.10}` to compute Attack Success Rate (ASR) and Refusal Rate at each threshold. Write results to `data/results/sensitivity_analysis.csv` and a concise report `data/results/sensitivity_report.md` that includes the variance metric. If variance > 5 % a warning must be added to the report (but the pipeline continues).  
  **Verification**: The CSV has columns `threshold`, `asr`, `refusal_rate`, `variance`; the markdown contains the word “WARNING” when appropriate.

- [ ] **T034** [US3] Generate raw result artifacts: copy `model_a_raw.csv`, `model_b_raw.csv`, `sensitivity_analysis.csv` into `data/results/` with the exact filenames `regression_results_raw.csv` and `sensitivity_analysis_raw.csv`.  
  **Verification**: Files exist and match the originals byte‑for‑byte (checksum recorded in `state/artifact_hashes.yaml`).

- [ ] **T045‑ExtractBaseline** [US3] Programmatically retrieve the baseline Attack Success Rate reported in the MedMisBench ACL 2024 paper (value 0.42) and write it to `data/results/baseline_asr.yaml` (fields: `source`, `value`, `reference`). No external web‑scraping; the value is hard‑coded after verification.  
  **Verification**: The YAML file exists and `value == 0.42`.

- [ ] **T045** [US3] Compare the computed ASR (from Model A) against the baseline. Append columns `computed_asr`, `baseline_asr`, `delta`, `interpretation` to `data/results/regression_results.csv`. Abort with error if the baseline file is missing or the `verified` flag is false.  
  **Verification**: The CSV now contains the four new columns; a sanity check confirms `delta = computed_asr - baseline_asr`.

- [ ] **T046** [US3] Add a selection‑bias warning module in `code/modeling.py` that calculates the overall adherence rate; if it is < 5 % or > 95 % write a warning to `data/results/regression_results.csv` (`selection_bias_warning` column) and also generate an IPW (inverse‑probability‑weighting) sensitivity file `data/results/ipw_sensitivity.csv`.  
  **Verification**: When the rate is extreme, the warning column reads “EXTREME_BASELINE”; the IPW file exists.

---

## Phase 6 – Polish & cross‑cutting concerns  

- [ ] **T036** [US0] Update `README.md` to include a usage example that runs `python -m code.main --config config.yaml` and describes the directory layout, required Python version, and how to locate result artifacts.  
  **Verification**: The README contains a fenced code block with the command and a bullet list of result files.

- [ ] **T037** [US0] Run linting (`ruff check --fix code/`) and formatting (`black code/`). Commit the cleaned code. The task must fail if any lint error remains.  
  **Verification**: `ruff check code/` returns exit code 0; `black --check code/` returns 0.

- [ ] **T039** [US0] Add any missing unit tests identified during development (e.g., for `fetch_external_fact`, `compute_correlation_and_kappa`, `sensitivity sweep`). Place them under `tests/unit/` and ensure they all pass.  
  **Verification**: `pytest tests/unit/ -q` exits with 0 and reports the new tests.

- [ ] **T040** [US0] Security hardening: audit all log statements in `code/validation.py` and `code/annotation.py` to ensure no PII (prompt text, rater IDs) are written to `pipeline_log.json`. Replace any such fields with hashed identifiers.  
  **Verification**: A static analysis script (`scripts/check_pii.py`) runs and reports “No PII found”.

- [ ] **T041** [US0] Execute the full pipeline end‑to‑end (`python -m code.main`) and generate `data/results/validation_report.md` that lists each stage, its runtime, and a checksum of the final `regression_results.csv`.  
  **Verification**: The markdown exists and contains a table with all stages and their timings.

- [ ] **T042** [US0] Unit‑test the compute‑time guard by mocking stage durations to exceed `MAX_RUNTIME_HOURS`; ensure `compute_time_report.md` is produced and the pipeline aborts. Store the test in `tests/unit/test_runtime_guard.py`.  
  **Verification**: The test passes; the report file is created during the mock run.

---

## Phase 7 – Revision & comprehensive verification  

- [ ] **T079‑Consolidated** [US0] Run a full verification suite that executes every unit and integration test, validates all JSON‑Schema contracts (`ingestion.schema.yaml`, `features.schema.yaml`, `labeling.schema.yaml`, `analysis.schema.yaml`, `sensitivity.schema.yaml`), checks that all required output files exist, and confirms that no task remains unchecked without its artifact. The suite writes a summary `data/results/verification_suite_report.md` with pass/fail counts. If any check fails, the pipeline aborts.  
  **Verification**: The markdown report lists “All checks passed” when the project is ready for reviewer hand‑off.

--- 

### Dependency summary (implicit ordering)

1. **Phase 1** → **Phase 2** → **Phase 3** (US1) → **Phase 3.5** (pilot) → **Phase 4** (US2) → **Phase 5** (US3) → **Phase 6** (polish) → **Phase 7** (final verification).  

All tasks marked `[P]` can run in parallel when their file targets do not overlap; otherwise respect the data‑flow ordering shown above.
