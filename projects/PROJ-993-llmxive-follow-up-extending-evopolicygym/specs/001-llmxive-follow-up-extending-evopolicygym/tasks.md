# Tasks: llmXive follow‑up – extending **EvoPolicyGym** with counterfactual feedback  

**Inputs**: `spec.md`, `plan.md`, all contract files under `specs/.../contracts/`, the current source tree under `code/`, and the `data/` directory.  

The goal is to deliver a reproducible end‑to‑end study that  

1. augments EvoPolicyGym with a **dynamic‑shift** mode,  
2. supplies a **CPU‑tractable counterfactual explanation generator** (with deterministic fallback to a template **or** a scalar‑reward signal),  
3. runs the evolutionary harness under baseline and counterfactual conditions,  
4. analyses the results with a mixed‑effects model (plus power‑analysis), and  
5. hands‑off the final results for the paper‑stage pipeline.  

All tasks are ordered to respect data flow – a task that consumes a file appears after the task that produces it.

---  

## Phase 1 – Environment discovery & dynamic‑shift validation (FR‑001)

- [ ] **T001 [S] [US1]** Discover the 16 EvoPolicyGym environments and record them.   <!-- FAILED-IN-EXECUTION: code/main.py exit=2 -->
  *Implementation*: `code/environments/registry_wrapper.py` imports the EvoPolicyGym registry, writes the list of environment IDs to `data/discovered_envs.json` (JSON array) and a human‑readable log to `data/discovered_envs.log`.  
  *Verification*:  
  1. `data/discovered_envs.json` exists and contains exactly 16 string IDs.  
  2. `data/discovered_envs.log` contains a line “Discovered 16 environments”.  
  3. If the count ≠ 16, the script raises `RuntimeError` (CI fails).

- [X] **T002 [S] [US1]** Define the CSV schema for the static‑agent sensitivity report.  
  *Artifact*: `data/sensitivity_report.schema.yaml` describing columns `env_id` (string), `shift_step` (int), `pre_shift_score` (float), `post_shift_score` (float), `drop_percent` (float), `p_value` (float), `is_significant` (bool).  
  *Verification*: The file parses as valid YAML, and a CI lint step confirms that all required column names and types are present.

- **T003 [S] [US1]** Run a non‑adaptive static agent on every discovered environment to produce `data/sensitivity_report.csv`.  
  *Script*: `code/scripts/run_static_shift_validation.py` reads `data/discovered_envs.json`, wraps each environment with `DynamicShiftEnvironment` (default shift at 50 % of the interaction budget), executes the static agent for the full budget, records pre‑ and post‑shift rewards, computes `drop_percent` and a one‑tailed t‑test p‑value, and writes the CSV.  
  *Verification*:  
  - CSV header exactly matches `data/sensitivity_report.schema.yaml`.  
  - At least one row has `is_significant == true`.  
  - File size > 0 bytes.

- [ ] **T004 [S] [US1]** Implement the orchestrator (`code/main.py`).   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  *Logic*:  
   1. Loads `data/discovered_envs.json`; if missing, aborts with a clear error.  
   2. Calls `generate_all_dynamic_shift_envs()` (implemented in `code/environments/dynamic_shift_env.py`) to create `DynamicShiftEnvironment` wrappers for all discovered IDs and writes the wrappers to `code/environments/generated/`.  
   3. Checks that `data/sensitivity_report.csv` exists; if not, aborts with a non‑zero exit code and an informative message.  
   4. Provides CLI flags:  
    - `--check` → prints “All pre‑conditions satisfied” when both files exist.  
    - `--run-evolution` → invokes the evolutionary harness (Phase 3).  
    - `--run-full-pipeline` → executes every downstream phase (Phase 2‑4) in order.  
  *Verification*: `python -m code.main --check` on a clean checkout prints the success message; missing files cause a non‑zero exit code and a descriptive stderr message.

---  

## Phase 2 – Counterfactual explanation module (FR‑002, FR‑006)

- [ ] **T005 [S] [US2]** Produce a masked rule schema (`data/masked_schema.json`).  
  *Script*: `code/explanation/mask_schema.py` loads the full rule schema (`data/rules_schema.json`), removes any logical‑predicate fields while preserving every `rule_id` and its human‑readable description, and writes the masked version.  
  *Verification*: The output JSON contains the same set of `rule_id`s as the source and no keys named `logic` (or similar).

- [ ] **T006 [S] [US2]** Implement LLM inference with a hard 30‑second timeout, 200‑token limit, and dual fallback handling (template **or** scalar‑reward).  
  *File*: `code/explanation/generator.py`  
   - Loads a lightweight 4‑bit quantized model (e.g., `TinyLlama-1.1B-Chat-v1.0`) via `bitsandbytes`.  
   - Builds a prompt from a trajectory log + `data/masked_schema.json`.  
   - Runs inference inside a `signal.alarm(30)` guard (Unix) or a `threading.Timer` fallback on other platforms.  
   - After generation, counts tokens; if > 200, raises `TokenLimitExceeded`.  
   - **Fallback handling** (`handle_fallback(reason)`) creates **either** a template‑based `CounterfactualExplanation` object **or** a scalar‑reward dict `{ "reward": 0.0, "fallback_reason": reason }`. Both are written as a single JSON line to `data/fallbacks.log`. The function returns the selected payload.  
  *Verification*:  
   - `tests/test_explanation_timeout.py` forces a sleep > 30 s and asserts that the returned payload contains a `reward` field set to `0.0` and that the log entry’s `fallback_reason` equals `"timeout"`.  
   - `tests/test_explanation_token_limit.py` supplies a deliberately long generation and asserts `fallback_reason == "exceeds_token_limit"`.  
   - `tests/test_explanation_scalar_fallback.py` triggers a model error and asserts a scalar‑reward payload with appropriate `fallback_reason`.  
   - **New** `tests/test_explanation_template_fallback_schema.py` forces the template‑fallback path and asserts that the produced `CounterfactualExplanation` object validates against the canonical schema.  
   - Successful generation (≤ 200 tokens, < 30 s) returns a JSON object with keys `explanation_id`, `rule_id`, `counterfactual_action`, etc., **without** a `reward` field.

- [ ] **T024 [S] [US2]** Verify that the template‑fallback path yields a schema‑compliant `CounterfactualExplanation`.  
  *Implementation*: `tests/test_explanation_template_fallback_schema.py` mocks the LLM to raise an exception, invokes `generator.handle_fallback("validation_fail")` (or triggers a deterministic fallback), and runs `jsonschema.validate` against `specs/001-llmxive-follow-up-extending-evopolicygym/contracts/counterfactual_explanation.schema.yaml`.  
  *Verification*: The test passes only if the fallback object conforms to the schema; otherwise it fails, ensuring template fallback correctness.

- [ ] **T007 [S] [US2]** Validate each generated explanation against the canonical JSON schema and log outcomes.  
  *Implementation*: `generator.py` calls `jsonschema.validate` against `specs/001-llmxive-follow-up-extending-evopolicygym/contracts/counterfactual_explanation.schema.yaml`.  
   - On success, appends a line to `data/success_log.jsonl` containing `{ "run_id": <str>, "env_id": <str>, "rule_id": <str>, "timestamp": <ISO‑8601> }`.  
   - On validation failure, invokes `handle_fallback("validation_fail")`.  
  *Verification*: `tests/test_explanation_schema.py` feeds a malformed object and checks that a `"validation_fail"` entry appears in `data/fallbacks.log`.  
   - `tests/test_explanation_template_fallback_schema.py` (added above) forces the template fallback path and asserts that the produced `CounterfactualExplanation` object validates against the schema.

---  

## Phase 3 – Evolutionary harness & metric collection (FR‑003, FR‑004)

- [ ] **T008 [S] [US3]** Implement the evolutionary harness for baseline and counterfactual conditions.  
  *File*: `code/agents/evolutionary_harness.py`  
   - Reads `data/discovered_envs.json`.  
   - Filters to environments where `is_significant == true` (from `data/sensitivity_report.csv`).  
   - For each seed (configurable via CLI) and each condition (`baseline`, `counterfactual`) runs the EvoPolicyGym evolution loop.  
   - Saves raw policy code to `data/policies/<run_id>.py`.  
   - Records metadata (`run_id`, `seed`, `condition`, `env_id`, `generation`) in `data/run_state.json`.  
  *Verification*: After `python -m code.agents.evolutionary_harness --seeds 2 --conditions baseline,counterfactual`, the directory `data/policies/` contains at least one `.py` file per condition and `data/run_state.json` includes matching entries.

- [ ] **T009 [S] [US3]** Compute structural metrics for each evolved policy and integrate them into the harness.  
  *File*: `code/analysis/complexity_metrics.py` wraps the `radon` library to return `cyclomatic_complexity` (float) and `branch_count` (int).  
   - If the policy file raises `SyntaxError`, the function returns `cc = -1` and `branches = -1`.  
   - The harness calls this function after each policy is written; on `-1` values it increments `generation_errors` in the run record and logs the traceback to `data/generation_errors.log`.  
  *Verification*: `tests/test_complexity_metrics.py` runs the function on a valid file (expects positive values) and on a deliberately broken file (expects `-1`).

- [ ] **T010 [S] [US3]** Write the evolution results CSV adhering to the contract.  
  *Artifact*: `data/evolution_results.csv` must conform to `specs/001-llmxive-follow-up-extending-evopolicygym/contracts/evolution_results.schema.yaml`.  
   - Columns: `run_id`, `seed`, `condition`, `generalization_score`, `complexity`, `branch_count`, `generation_errors`.  
   - Values are aggregated from `data/run_state.json`, the complexity metrics, and pre/post‑shift scores from `data/sensitivity_report.csv`.  
   - After writing, generate a SHA‑256 checksum file `data/evolution_results.sha256`.  
  *Verification*: A CI step runs `csvkit` to confirm the header matches the schema, checks that at least one row exists for each condition, and verifies that the checksum file is non‑empty and matches the CSV.

---  

## Phase 4 – Statistical analysis & result aggregation (FR‑005)

- [ ] **T011 [S] [US3]** Fit a mixed‑effects model and output statistical results.  
  *File*: `code/analysis/statistical_test.py` loads `data/evolution_results.csv` and fits the model  
  `generalization_score ~ condition + complexity + (1|seed)` using `statsmodels`.  
   - Extracts `p_value`, `effect_size` (Cohen’s d), and the sign of the `condition` coefficient.  
   - Sets `significant = true` only if `p_value < 0.05` **and** the coefficient is positive.  
   - Writes `data/stats_results.json` adhering to `specs/001-llmxive-follow-up-extending-evopolicygym/contracts/stats_results.schema.yaml`.  
  *Verification*: `tests/test_statistical_test.py` runs the script on a tiny synthetic dataset and asserts that the JSON contains keys `p_value`, `effect_size`, `significant`, and `model_id`.

- [ ] **T012 [S] [US3]** Perform a power analysis and flag under‑powered studies.  
  *File*: `code/analysis/power_analysis.py` computes statistical power given the sample size, estimated effect size, and α = 0.05 (using `statsmodels.stats.power`).  
   - If power < 0.8, writes a warning line to `data/power_analysis.log` and adds `"underpowered": true` to `data/stats_results.json`; otherwise adds `"underpowered": false`.  
  *Verification*: With fewer than 10 runs per condition, the log appears and the JSON flag is `true`; `tests/test_power_analysis.py` confirms this behavior.

- [ ] **T013 [S] [US3]** Aggregate the explanation‑success rate across all runs.  
  *Script*: `code/analysis/aggregate_success.py` reads `data/success_log.jsonl` and `data/fallbacks.log`, computes  
  `rate = successes / (successes + failures)`.  
   - Writes `data/aggregation_stats.json` containing `successful_explanations`, `fallback_count`, `overall_success_rate`.  
  *Verification*: The JSON file exists, fields are numeric, and `tests/test_aggregate_success.py` validates the computation on a handcrafted log.

- [ ] **T014 [S] [US3]** End‑to‑end pipeline CLI (`code/main.py`).  
  *Flags*:  
   - `--run-full-pipeline` executes, in order, **T001–T004**, **T005–T007**, **T008–T010**, **T011–T013**, then merges `data/evolution_results.csv`, `data/stats_results.json`, and `data/aggregation_stats.json` into `data/final_results.csv` (adds a summary row labeled `OVERALL`).  
   - `--check` only performs pre‑condition validation (Phase 1).  
  *Verification*: After a minimal run (2 environments, 1 seed, both conditions) `data/final_results.csv` exists, contains the merged columns, and the summary row’s `overall_success_rate` matches the value in `aggregation_stats.json`.

- [ ] **T023 [S] [US3]** Compute the generalization performance difference metric required by SC‑001 and assert a concrete effect‑size threshold.  
  *File*: `code/analysis/generalization_metric.py` reads `data/evolution_results.csv`, calculates for each run `diff = post_shift_score - pre_shift_score` (using the shift scores stored in the CSV), aggregates the mean difference per condition, and checks that the counterfactual condition’s mean improvement exceeds the baseline’s mean drop‑off by at least **Cohen’s d ≥ 0.2**.  
  *Verification*: `tests/test_generalization_metric.py` runs the script on a synthetic dataset and asserts that the script exits with success only when the threshold is met; otherwise it logs a warning.

---  

## Phase 5 – Checksums & Versioning (Constitution compliance)

- [ ] **T018 [S]** Compute SHA‑256 checksums for all generated data artifacts (`data/discovered_envs.json`, `data/sensitivity_report.csv`, `data/evolution_results.csv`, `data/stats_results.json`, `data/aggregation_stats.json`).  
  *Implementation*: `code/utils/checksum.py` iterates over the listed files, writes `<filename>.sha256` files containing the hex digest.  
  *Verification*: Each `.sha256` file exists and matches the current file content (CI re‑computes and compares).

- [ ] **T019 [S]** Verify checksums before downstream consumption.  
  *Implementation*: `code/utils/verify_checksums.py` reads each `<filename>.sha256` and aborts with an error if any mismatch is detected.  
  *Verification*: CI step runs the verifier; a mismatch causes a non‑zero exit code.

- [ ] **T020 [S]** Update the project state file with artifact hashes.  
  *File*: `state/projects/PROJ-993-llmxive-follow-up-extending-evopolicygym.yaml`  
  *Implementation*: After checksum generation, a script `code/utils/update_state_hashes.py` loads the state YAML, inserts a map `artifact_hashes` with entries `{ "data/discovered_envs.json": "<sha>", ... }`, and writes the file back.  
  *Verification*: CI step parses the state file and confirms that each listed artifact hash matches the corresponding `.sha256` file.

---  

## Phase 6 – Documentation & CI sanity check

- [ ] **T015 [S]** Write `README.md` with project overview, installation (`pip install -r requirements.txt`), and CLI usage examples (`python -m code.main --run-full-pipeline`).  
  *Verification*: File exists, contains a top‑level heading `# llmXive – Counterfactual EvoPolicyGym Extension`, and the example command matches the actual CLI flag.

- [ ] **T016 [S]** Write `quickstart.md` that walks a new user through a single‑command end‑to‑end run and lists the expected output files (`data/final_results.csv`, `data/stats_results.json`).  
  *Verification*: File exists, the described command matches `python -m code.main --run-full-pipeline`, and the listed output files are present after the command.

- [ ] **T017 [S]** Add a CI‑friendly test (`tests/test_quickstart.py`) that invokes the quick‑start on a reduced subset (2 environments, 1 seed) and asserts that `data/final_results.csv` is created and contains at least one row per condition.  
  *Verification*: The test passes on a fresh checkout; CI reports “passed”.