# Tasks: llmXive follow‑up – extending **EvoPolicyGym** with counterfactual feedback  

**Inputs**: `spec.md`, `plan.md`, all contract files under `specs/.../contracts/`, current source tree under `code/`, and the `data/` directory.  

The goal is to deliver a reproducible end‑to‑end study that (1) augments EvoPolicyGym with a **dynamic‑shift** mode, (2) supplies a **CPU‑tractable counterfactual explanation generator** (with deterministic fallback to a scalar‑reward signal), (3) runs the evolutionary harness under baseline and counterfactual conditions, (4) analyses the results with a mixed‑effects model, and (5) hands‑off the final results for paper‑stage reporting.

---  

## Phase 1 – Environment discovery & dynamic‑shift validation (FR‑001)

- [ ] **T001 [P] [US1]** Discover the 16 EvoPolicyGym environments and record them.  
  *Implementation*: `code/environments/registry_wrapper.py` imports the EvoPolicyGym registry, writes the list of environment IDs to `data/discovered_envs.json` (JSON array) and a human‑readable log to `data/discovered_envs.log`.  
  *Verification*:  
  1. `data/discovered_envs.json` exists and contains exactly 16 string IDs.  
  2. `data/discovered_envs.log` contains a line “Discovered 16 environments”.  
  3. If the count ≠ 16, the script raises `RuntimeError` (CI fails).

- [ ] **T002 [P] [US1]** Create a concrete CSV‑schema file for the sensitivity report.  
  *Artifact*: `data/sensitivity_report.schema.yaml` defining columns `env_id` (string), `shift_step` (int), `pre_shift_score` (float), `post_shift_score` (float), `drop_percent` (float), `p_value` (float), `is_significant` (bool).  
  *Verification*: The file exists, parses as valid YAML, and passes a schema‑lint check.

- [ ] **T003 [P] [US1]** Run a non‑adaptive static agent on every discovered environment to generate `data/sensitivity_report.csv`.  
  *Script*: `code/scripts/run_static_shift_validation.py` reads `data/discovered_envs.json`, wraps each environment with `DynamicShiftEnvironment` (default shift at 50 % of the interaction budget), executes the static agent for the full budget, records pre‑ and post‑shift rewards, computes `drop_percent` and a one‑tailed t‑test p‑value, and writes the CSV.  
  *Verification*:  
  - CSV header exactly matches `data/sensitivity_report.schema.yaml`.  
  - At least one row has `is_significant == true`.  
  - File size > 0 bytes.

- [ ] **T004 [P] [US1]** Implement an orchestrator (`code/main.py`) that validates pre‑conditions and optionally launches the evolutionary phase.  
  *Logic*:  
   1. If `data/discovered_envs.json` is missing, invoke **T001**.  
   2. If `data/sensitivity_report.csv` is missing, abort with a clear error message.  
   3. Provide CLI flag `--run-evolution` that calls the evolutionary harness (Phase 2).  
   4. Provide a `--check` flag that prints “All pre‑conditions satisfied” only when both files exist.  
  *Verification*: Running `python -m code.main --check` on a clean checkout prints the success message; missing files cause a non‑zero exit code.

---  

## Phase 2 – Counterfactual explanation module (FR‑002, FR‑006)

- [ ] **T005 [P] [US2]** Produce a masked rule schema (`data/masked_schema.json`).  
  *Script*: `code/explanation/mask_schema.py` loads the full rule schema (`data/rules_schema.json`), removes any logical predicate fields while preserving every `rule_id` and its human‑readable description, and writes the masked version.  
  *Verification*: The output JSON contains the same set of `rule_id`s as the source and no fields named `logic` or similar.

- [ ] **T006 [P] [US2]** Implement LLM inference with a 30‑second hard timeout.  
  *File*: `code/explanation/generator.py` loads `TinyLlama/TinyLlama-1.1B-Chat-v1.0` in 4‑bit mode via `bitsandbytes`, builds a prompt from a trajectory log + `data/masked_schema.json`, and runs inference inside a `signal.alarm(30)` guard (Unix) or a `threading.Timer` fallback on other platforms.  
  *Verification*: Unit test `tests/test_explanation_timeout.py` forces a sleep > 30 s and asserts that the fallback path is taken.

- [ ] **T007 [P] [US2]** Add dual fallback handling that returns **either** a template‑based textual explanation **or** a scalar‑reward signal (reward = 0.0).  
  *Implementation*: In `generator.py`, `handle_fallback(reason)` creates a `CounterfactualExplanation` object with `is_fallback=True` **and** a dictionary `{"reward": 0.0, "fallback_reason": reason}`. Both objects are written as a single JSON line to `data/fallbacks.log`.  
  *Verification*: Integration test triggers a timeout and checks that the returned payload contains a `reward` field set to `0.0` and that the log entry’s `fallback_reason` equals `"timeout"`.

- [ ] **T008 [P] [US2]** Enforce the 200‑token limit on generated explanations.  
  *Logic*: After generation, count tokens with the model’s tokenizer. If the count exceeds 200, raise `TokenLimitExceeded` which invokes `handle_fallback("exceeds_token_limit")`. No truncation is performed.  
  *Verification*: Test `tests/test_explanation_token_limit.py` supplies a deliberately long generation and asserts that the fallback log reason is `"exceeds_token_limit"`.

- [ ] **T009 [P] [US2]** Validate each explanation against the canonical JSON schema (`specs/…/counterfactual_explanation.schema.yaml`).  
  *Implementation*: `generator.py` calls `validate_explanation(obj, schema_path)` (wrapper around `jsonschema.validate`). If validation fails, invoke `handle_fallback("validation_fail")`.  
  *Verification*: Test `tests/test_explanation_schema.py` feeds a malformed object and checks for the `"validation_fail"` entry in `data/fallbacks.log`.

- [ ] **T010 [P] [US2]** Log successful explanations.  
  *File*: `data/success_log.jsonl` – each line is a JSON object `{ "run_id": <str>, "env_id": <str>, "rule_id": <str>, "timestamp": <ISO‑8601> }`.  
  *Verification*: After a successful generation, a new line appears; a quick `grep` in CI confirms the file is non‑empty.

---  

## Phase 3 – Evolutionary harness & metric collection (FR‑003, FR‑004)

- [ ] **T011 [P] [US3]** Implement the evolutionary harness that runs both baseline (scalar reward) and counterfactual conditions.  
  *File*: `code/agents/evolutionary_harness.py` defines `EvolutionaryHarness`. It reads `data/discovered_envs.json`, filters to environments where `is_significant == true` (from `data/sensitivity_report.csv`), iterates over a user‑specified list of seeds, and for each condition (`baseline`, `counterfactual`) runs the EvoPolicyGym evolution loop, saving raw policy code to `data/policies/<run_id>.py` and recording metadata (seed, condition, env_id, generation).  
  *Verification*: After invoking `python -m code.agents.evolutionary_harness --seeds 3 --conditions baseline,counterfactual`, the directory `data/policies/` contains at least one `.py` file per condition and a JSON state file `data/run_state.json` with entries for each run.

- [ ] **T012 [P] [US3]** Compute structural metrics for each evolved policy.  
  *File*: `code/analysis/complexity_metrics.py` wraps the `radon` library to return `cyclomatic_complexity` (float) and `branch_count` (int). If the policy file raises `SyntaxError`, the function returns `cc = -1` and `branches = -1`.  
  *Verification*: Unit test `tests/test_complexity_metrics.py` runs the function on a known good file (expects positive values) and on a deliberately broken file (expects `-1`).

- [ ] **T013 [P] [US3]** Integrate complexity analysis into the harness and handle generation errors.  
  *Logic*: After each policy is written, the harness calls `complexity_metrics.py`. If `cc == -1`, the run record increments `generation_errors`, logs the traceback to `data/generation_errors.log`, and the run is excluded from the final CSV.  
  *Verification*: Inject a broken policy (e.g., syntax error) via a test harness run and confirm that `data/generation_errors.log` contains an entry and that the corresponding row is absent from `data/evolution_results.csv`.

- [ ] **T014 [P] [US3]** Write the evolution results CSV (`data/evolution_results.csv`).  
  *Schema*: Must conform to `contracts/evolution_results.schema.yaml` (fields: `run_id`, `seed`, `condition`, `generalization_score`, `complexity`, `branch_count`, `generation_errors`). The script aggregates data from `run_state.json`, complexity metrics, and the pre/post‑shift scores from `sensitivity_report.csv`.  
  *Verification*: The CSV header matches the schema, the file contains at least one row for each condition, and a checksum file `data/evolution_results.sha256` is generated.

---  

## Phase 4 – Statistical analysis & result aggregation (FR‑005)

- [ ] **T015 [P] [US3]** Run a mixed‑effects model on the evolution results.  
  *File*: `code/analysis/statistical_test.py` loads `data/evolution_results.csv` and fits a model with formula  
  `generalization_score ~ condition + complexity + (1|seed)` using `statsmodels`. It extracts `p_value`, `effect_size` (Cohen’s d), and the sign of the `condition` coefficient. If `p_value < 0.05` **and** the coefficient is positive, `significant = true`; otherwise `significant = false`. The results are written to `data/stats_results.json` adhering to `contracts/stats_results.schema.yaml`.  
  *Verification*: Running the script on a synthetic mini‑dataset produces a JSON file with the required keys; a CI test (`tests/test_statistical_test.py`) asserts the presence of `p_value` and `significant`.

- [ ] **T016 [P] [US3]** Perform a power analysis and warn if under‑powered.  
  *File*: `code/analysis/power_analysis.py` computes statistical power given the sample size, effect size estimate, and α = 0.05 (using `statsmodels.stats.power`). If power < 0.8, it writes a warning line to `data/power_analysis.log` and adds `"underpowered": true` to `data/stats_results.json`.  
  *Verification*: With fewer than 10 runs per condition, the log file appears and the JSON flag is set; a test (`tests/test_power_analysis.py`) checks this behavior.

- [ ] **T017 [P] [US3]** Aggregate the explanation‑success rate.  
  *Script*: `code/analysis/aggregate_success.py` reads `data/success_log.jsonl` and `data/fallbacks.log`, computes `rate = successes / (successes + failures)`, and writes `data/aggregation_stats.json` matching a simple schema (`successful_explanations`, `fallback_count`, `overall_success_rate`).  
  *Verification*: The JSON file exists and the three fields are numeric; a test (`tests/test_aggregate_success.py`) validates the computation on a tiny handcrafted log.

- [ ] **T018 [P] [US3]** End‑to‑end pipeline CLI (`code/main.py`).  
  *Flags*:  
   - `--run-full-pipeline` executes, in order, **T001–T004**, **T005–T010**, **T011–T014**, **T015–T017**, then merges `evolution_results.csv`, `stats_results.json`, and `aggregation_stats.json` into `data/final_results.csv` (adds a summary row labeled `OVERALL`).  
   - `--check` only performs pre‑condition validation (Phase 1).  
  *Verification*: After a successful run on a minimal configuration (2 environments, 1 seed, both conditions), `data/final_results.csv` exists, contains the merged columns, and the summary row’s `overall_success_rate` matches the aggregation file.

---  

## Phase 5 – Documentation & CI sanity check

- [ ] **T019 [P]** Write `README.md` with project overview, installation steps (`pip install -r requirements.txt`), and CLI usage examples (`python -m code.main --run-full-pipeline`).  
  *Verification*: File exists and contains a heading `# llmXive – Counterfactual EvoPolicyGym Extension`.

- [ ] **T020 [P]** Write `quickstart.md` that walks a new user through the single‑command end‑to‑end run and lists the expected output files (`data/final_results.csv`, `data/stats_results.json`).  
  *Verification*: File exists and the described command matches the actual CLI flag.

- [ ] **T021 [P]** Add a CI‑friendly test (`tests/test_quickstart.py`) that invokes the quick‑start on a reduced subset (2 environments, 1 seed) and asserts that `data/final_results.csv` is created and contains at least one row per condition.  
  *Verification*: The test passes on a fresh checkout; CI reports “passed”.

---  

### Summary of pending (unchecked) substantive tasks  

| ID | Story | Core description |
|----|-------|-------------------|
| **T001** | US1 | Discover environments → `discovered_envs.json` + log |
| **T002** | US1 | Create CSV schema for sensitivity report |
| **T003** | US1 | Run static agent → `sensitivity_report.csv` |
| **T004** | US1 | Orchestrator (`code.main`) with pre‑condition checks |
| **T005** | US2 | Mask rule schema → `masked_schema.json` |
| **T006** | US2 | LLM inference with 30 s timeout |
| **T007** | US2 | Dual fallback: template explanation **or** scalar reward |
| **T008** | US2 | Enforce 200‑token limit, trigger fallback |
| **T009** | US2 | Schema validation of explanations |
| **T010** | US2 | Log successful explanations |
| **T011** | US3 | Evolutionary harness for both conditions |
| **T012** | US3 | Policy complexity & branch count via `radon` |
| **T013** | US3 | Generation‑error handling & logging |
| **T014** | US3 | Write `evolution_results.csv` per contract |
| **T015** | US3 | Mixed‑effects model → `stats_results.json` |
| **T016** | US3 | Power analysis warning & flag |
| **T017** | US3 | Aggregate explanation success rate |
| **T018** | US3 | End‑to‑end pipeline CLI → `final_results.csv` |
| **T019** | –   | README documentation |
| **T020** | –   | Quick‑start guide |
| **T021** | –   | CI test for quick‑start |

All tasks respect data flow: a task that consumes a file is listed after the task that produces it. Each task includes concrete artifact paths and an explicit verification step so that the CI can automatically mark the checkbox as completed.
