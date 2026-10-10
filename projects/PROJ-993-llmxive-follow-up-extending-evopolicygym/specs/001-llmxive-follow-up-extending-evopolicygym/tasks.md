# Tasks: llmXive follow‑up – extending **EvoPolicyGym** with counterfactual feedback  

**Inputs**: `spec.md`, `plan.md`, existing `contracts/`, current code base under `code/`, data folder `data/`.  
**Goal**: Deliver a reproducible, end‑to‑end study that (1) augments the EvoPolicyGym suite with a **dynamic‑shift** mode, (2) provides a **CPU‑tractable counterfactual explanation generator** (with deterministic fallback to a scalar‑reward signal), (3) runs the **evolutionary harness** under baseline and counterfactual conditions, (4) analyses the results with a **mixed‑effects model**, and (5) reports the measured success‑rate of the explanation module.  

---  

## Phase 0 – Verified foundation (already completed)

- [ ] T001a [P] Create project directory layout (`code/`, `tests/`, `data/`, `specs/`).  
- [ ] T001b [P] Add `__init__.py` in every new sub‑package.  
- [ ] T001c [P] Pin dependencies in `requirements.txt`.  
- [ ] T001d [P] Add `pyproject.toml` with ruff/black configs.  
- [ ] T001e [P] Install dependencies; log output to `data/install_log.txt`.  
- [ ] T004 [P] Implement `code/utils/config.py` (seed & hyper‑parameter manager).  
- [ ] T005 [P] Set up structured logging in `code/utils/logging.py`.  
- [ ] T006 [P] Create base wrapper `code/environments/base_env.py`.  
- [ ] T007 [P] Generate a **rules schema** (`data/rules_schema.json`) from the EvoPolicyGym source or a minimal template.  
- [ ] T008 [P] Provide reproducible seed utility (`code/utils/seed_utils.py`).  
- [ ] T009 [P] Separate test‑set configuration from training config in `config.py`.  
- [ ] T010 [P] [US1] Unit test for shift‑trigger logic (`code/tests/test_env_shift.py`).  
- [ ] T011 [P] [US1] Integration test for performance drop after shift (`code/tests/test_env_shift.py`).  
- [ ] T013c [P] [US1] Define and validate the **dynamic‑shift configuration schema** (`code/environments/dynamic_shift_env.py`).  
- [ ] T013b [P] [US1] Implement reward/transition alteration after `shift_step`.  
- [ ] T014 [P] [US1] Compute p‑value for shift impact; log non‑significant shifts to `data/shift_validation.log`.  
- [ ] T018 [P] [US2] Unit test for counterfactual‑explanation schema validation (`code/tests/test_explanation.py`).  
- [ ] T019 [P] [US2] Integration test for the 30‑s timeout & fallback (`code/tests/test_explanation.py`).  
- [ ] T020a [P] [US2] Define `CounterfactualExplanation` Pydantic model (`code/explanation/validator.py`).  
- [ ] T020b [P] [US2] Implement `validate_explanation()` (`code/explanation/validator.py`).  
- [ ] T021a‑Load [P] [US2] Load `data/rules_schema.json` into `data/derivation_cache.json`.  
- [ ] T024 [P] [US3] Unit test for `radon`‑based cyclomatic complexity (`code/tests/test_stats.py`).  
- [ ] T031 [P] [US3] Integration test for mixed‑effects model output (`code/tests/test_stats.py`).  

---  

## Phase 1 – Dynamic‑Shift environment pipeline (FR‑001)

> **Missing / rejected work:** `T013d`, `T013e`, `T013f`, `T015b`, `T015c`, `T015a`.  
> The following tasks replace those and produce the required artifacts.

- [ ] **T101 [P] [US1]** Discover and record the 16 EvoPolicyGym environments.  
  *Implementation*: `code/environments/registry_wrapper.py` imports `evopolicygym.envs.REGISTRY`, writes the list of IDs to `data/discovered_envs.json` **and** to a human‑readable log `data/discovered_envs.log`.  
  *Verification*:  
  1. File `data/discovered_envs.json` exists and contains a JSON array of 16 strings.  
  2. If the count ≠ 16, raise `RuntimeError` with an informative message (fails the CI).  

- [ ] **T102 [P] [US1]** Create a concrete **sensitivity‑report schema** for the CSV produced by the static‑agent validation.  
  *Artifact*: `data/sensitivity_report.schema.yaml` defining columns `env_id` (str), `shift_step` (int), `pre_shift_score` (float), `post_shift_score` (float), `drop_percent` (float), `p_value` (float), `is_significant` (bool).  
  *Verification*: The file exists and is valid YAML (schema‑lint passes).  

- [ ] **T103 [P] [US1]** Run the **static‑agent** on every discovered environment to generate the sensitivity report.  
  *Script*: `code/scripts/run_static_shift_validation.py` reads `data/discovered_envs.json`, wraps each environment with `DynamicShiftEnvironment`, executes a non‑adaptive agent for the full budget, records pre‑ and post‑shift rewards, computes `drop_percent` and a one‑tailed t‑test p‑value, and writes `data/sensitivity_report.csv`.  
  *Verification*:  
  - CSV header matches `data/sensitivity_report.schema.yaml`.  
  - At least one environment has `is_significant == true`.  

- [ ] **T104 [P] [US1]** **Orchestrator script** that ensures the sensitivity report exists before any evolution runs.  
  *File*: `code/main.py` (entry point).  
  *Logic*:  
   1. Calls `T101` (environment discovery) if `data/discovered_envs.json` missing.  
   2. Checks `data/sensitivity_report.csv`; if absent, aborts with clear error.  
   3. Provides CLI flag `--run-evolution` that triggers Phase 2 (User Story 3).  
  *Verification*: Running `python -m code.main --check` prints “All pre‑conditions satisfied” only when both files exist.  

---  

## Phase 2 – Counterfactual explanation module (FR‑002, FR‑006)

> **Missing / rejected work:** `T023` (scalar‑reward fallback) and supporting steps.  

- [ ] **T201 [P] [US2]** Generate a **masked rule schema** that hides the logical predicates but retains identifiers and human‑readable descriptions.  
  *Script*: `code/explanation/mask_schema.py` reads `data/derivation_cache.json`, produces `data/masked_schema.json`.  
  *Verification*: The output JSON contains the same `rule_id`s as the original but no `logic` fields.  

- [ ] **T202 [P] [US2]** Implement **LLM inference** with a 30‑second hard timeout.  
  *File*: `code/explanation/generator.py` – uses `transformers` to load `TinyLlama/TinyLlama-1.1B-Chat-v1.0` in 4‑bit mode (`bitsandbytes`).  
  *Behaviour*:  
   - Constructs prompt from trajectory log + `data/masked_schema.json`.  
   - Runs inference inside a `signal.alarm` (Unix) / `threading.Timer` guard.  
   - If the model exceeds 30 s or raises an exception → goto fallback (T203).  
  *Verification*: Unit test `T019` asserts that a deliberately slow model triggers fallback.  

- [ ] **T203 [P] [US2]** **Fallback handling** – two‑branch fallback:  
   1. **Template‑based textual explanation** (`TemplateExplanation`).  
   2. **Scalar‑reward fallback** (numeric reward = 0.0) when a textual explanation is not permissible.  
  *Implementation*: In `generator.py`, `handle_fallback(reason)` creates a `CounterfactualExplanation` with `is_fallback=True` **and** returns a secondary scalar‑reward object `{ "reward": 0.0, "fallback_reason": reason }`. Both objects are logged to `data/fallbacks.log` with ISO‑8601 timestamps.  
  *Verification*: Integration test `T019` checks that a timeout produces a log entry with `"fallback_reason":"timeout"` and that the returned payload contains the scalar reward field.  

- [ ] **T204 [P] [US2]** Enforce the **200‑token limit** on generated explanations.  
  *Logic*: After LLM generation, count tokens (using the tokenizer). If > 200, raise `TokenLimitExceeded` which triggers `handle_fallback("exceeds_token_limit")`. No truncation is performed.  
  *Verification*: Unit test `T021d` (added) asserts that an over‑limit generation is logged as `"exceeds_token_limit"` and no explanation object is persisted.  

- [ ] **T205 [P] [US2]** Validate each explanation against the **canonical JSON schema** (`specs/…/counterfactual_explanation.schema.yaml`).  
  *Implementation*: `generator.py` calls `validate_explanation()` (from `validator.py`) before returning the object. Invalid objects trigger fallback with reason `"validation_fail"`.  
  *Verification*: `T018` ensures that an intentionally malformed object fails validation and is logged appropriately.  

- [ ] **T206 [P] [US2]** Log **successful** explanation generations.  
  *File*: `data/success_log.jsonl` – each line contains `{ "run_id": <str>, "env_id": <str>, "rule_id": <str>, "timestamp": <ISO> }`.  
  *Verification*: After a successful generation, the line appears; a simple grep in CI confirms non‑empty file.  

---  

## Phase 3 – Evolutionary harness & metric collection (FR‑003, FR‑004)

- [ ] **T301 [P] [US3]** Implement the **baseline & counterfactual orchestration**.  
  *File*: `code/agents/evolutionary_harness.py` – `EvolutionaryHarness` class reads `data/discovered_envs.json` and filters to environments where `is_significant == true` (from `sensitivity_report.csv`). For each seed and condition, it runs the EvoPolicyGym evolution loop, stores raw policy code under `data/policies/<run_id>.py`.  
  *Verification*: Running `python -m code.agents.evolutionary_harness --seeds 3 --conditions baseline,counterfactual` produces a non‑empty `data/run_state.json`.  

- [ ] **T302 [P] [US3]** **Policy parser** for structural metrics.  
  *File*: `code/analysis/complexity_metrics.py` – wraps `radon` to compute cyclomatic complexity (`cc`) and conditional branch count. Handles `SyntaxError` by returning `cc = -1` and `branches = -1`.  
  *Verification*: Unit test `T024` confirms correct values on a known sample file; error case returns `-1`.  

- [ ] **T303 [P] [US3]** **Generation‑error handling**.  
  *Logic*: In `evolutionary_harness.py`, after each policy is written, invoke `complexity_metrics.py`. If `cc == -1`, record `generation_errors += 1` in the run record and skip inclusion in the final CSV. All errors are appended to `data/generation_errors.log`.  
  *Verification*: After a deliberately broken policy is injected, the log contains the appropriate entry and the CSV row is omitted.  

- [ ] **T304 [P] [US3]** Write **evolution results** CSV.  
  *File*: `data/evolution_results.csv` – columns conform to `contracts/evolution_results.schema.yaml` (`run_id`, `seed`, `condition`, `generalization_score`, `complexity`, `branch_count`, `generation_errors`). Data are assembled from `run_state.json`, `complexity_metrics.py`, and the static `sensitivity_report.csv`.  
  *Verification*: CSV header matches schema; at least one row per condition is present.  

---  

## Phase 4 – Statistical analysis & reporting (FR‑005)

- [ ] **T401 [P] [US3]** Run a **mixed‑effects model** on the evolution results.  
  *File*: `code/analysis/statistical_test.py` – uses `statsmodels` formula `generalization_score ~ condition + complexity + (1|seed)`.  
  *Checks*:  
   - `data/evolution_results.csv` exists and contains ≥ 1 row per condition.  
   - Model converges; extracts `p_value`, `effect_size` (Cohen’s d), `condition` coefficient sign.  
   - If `p_value < 0.05` **and** coefficient > 0, set `significant = true`.  
   - Writes `data/stats_results.json` adhering to `contracts/stats_results.schema.yaml`.  
  *Verification*: `T031` confirms that a minimal synthetic dataset yields a well‑formed JSON with the required fields.  

- [ ] **T402 [P] [US3]** **Power analysis** – compute minimum detectable effect size given the sample size; if power < 0.8, add a warning entry `data/power_analysis.log` and set `"underpowered": true` in `stats_results.json`.  
  *Verification*: CI checks that the log file appears when the sample size is < 10.  

- [ ] **T403 [P]** Aggregate **explanation‑success rate**.  
  *Script*: `code/analysis/aggregate_success.py` reads `data/success_log.jsonl` and `data/fallbacks.log`, computes `rate = successes / (successes + failures)`, writes `data/aggregation_stats.json` (matches `contracts/aggregation_stats.schema.yaml`).  
  *Verification*: The JSON contains fields `successful_explanations`, `fallback_count`, `overall_success_rate`.  

- [ ] **T404 [P]** **Final results hand‑off**.  
  *CLI*: `python -m code.main --run-full-pipeline` executes (1) environment discovery, (2) sensitivity report, (3) evolution harness, (4) statistical test, (5) aggregation, and finally writes `data/final_results.csv` that merges `evolution_results.csv` with `stats_results.json` and `aggregation_stats.json`.  
  *Verification*: The final CSV contains a row for each run plus a summary row labeled `OVERALL`.  

---  

## Phase 5 – Documentation & quick‑start (non‑research but required for reproducibility)

- [ ] **T501 [P]** Write `README.md` with project overview, install steps, and CLI usage.  
- [ ] **T502 [P]** Write `quickstart.md` that walks a new user through the **single‑command end‑to‑end run** (`python -m code.main --run-full-pipeline`).  
- [ ] **T503 [P]** Add a CI‑friendly test `tests/test_quickstart.py` that executes the quick‑start script on a minimal subset (2 environments, 1 seed) and asserts that `data/final_results.csv` exists.  

---  

## Phase 6 – Revision concerns (addressed proactively)

| Concern | Task | Remedy |
|---------|------|--------|
| Shift‑validation warnings for non‑significant drops | T014 (already checked) | Logs to `data/shift_validation.log`. |
| Token‑limit enforcement & logging | T204 (new) | Logs `"exceeds_token_limit"` in `fallbacks.log`. |
| Scalar‑reward fallback requirement | T203 (new) | Returns numeric reward alongside textual fallback. |
| Schema‑mismatch safety | T205 (new) | Validation step rejects mismatched rule IDs. |
| Mixed‑effects model coefficient sign | T401 (new) | Explicit check for positive coefficient; logs error if negative. |
| Minimum rows per condition | T401 (new) | RuntimeError if a condition missing. |
| Under‑powered analysis warning | T402 (new) | Power‑analysis log & flag. |

---  

### Summary of pending (unchecked) substantive tasks  

| ID | Story | Description |
|----|-------|-------------|
| **T101** | US1 | Discover 16 environments, write JSON & log. |
| **T102** | US1 | Create CSV schema YAML for sensitivity report. |
| **T103** | US1 | Run static agent, produce `sensitivity_report.csv`. |
| **T104** | US1 | Orchestrator (`code/main.py`) that validates pre‑conditions. |
| **T201** | US2 | Produce masked rule schema (`masked_schema.json`). |
| **T202** | US2 | LLM inference with 30 s timeout. |
| **T203** | US2 | Dual fallback: template text **or** scalar reward (0.0). |
| **T204** | US2 | Enforce 200‑token limit, trigger fallback on breach. |
| **T205** | US2 | Validate explanations against canonical schema. |
| **T206** | US2 | Log successful explanations to `success_log.jsonl`. |
| **T301** | US3 | Evolutionary harness orchestrating both conditions. |
| **T302** | US3 | Policy parser (`radon`) for complexity & branch count. |
| **T303** | US3 | Generation‑error handling & logging. |
| **T304** | US3 | Write `evolution_results.csv` per contract. |
| **T401** | US3 | Mixed‑effects model analysis, produce `stats_results.json`. |
| **T402** | US3 | Power analysis warning for small sample sizes. |
| **T403** | –   | Compute explanation success rate (`aggregation_stats.json`). |
| **T404** | –   | End‑to‑end pipeline CLI, produce `final_results.csv`. |
| **T501** | –   | README documentation. |
| **T502** | –   | Quick‑start guide. |
| **T503** | –   | CI test for quick‑start execution. |

All tasks are listed in execution order respecting data flow; no task that consumes a file is placed before the task that produces it. Each task includes the exact artifact path(s) it reads or writes, and the verification steps required for CI to mark the checkbox as completed.
