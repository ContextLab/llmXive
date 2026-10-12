# Tasks: LLM Agent Efficiency vs. Reasoning Trade‑off Analysis

**Inputs**: `spec.md`, `plan.md`, the research idea, and the contracts in `specs/001-llmxive-follow-up-extending-a-matter-of/contracts/`.

The study must satisfy all functional requirements (FR‑001 – FR‑008) and success criteria (SC‑001 – SC‑005).  
The tasks are ordered to respect data dependencies; each task’s output is a concrete artifact that can be validated by the schemas in `specs/.../`.  

---  

## Phase 1: Setup and first end‑to‑end analysis  

| Goal | Run a minimal, fully‑reproducible pipeline on real inputs and produce the first set of logged results. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] T001 [US1] Download the τⁿ‑Bench dataset from its official HuggingFace repository into `data/raw/τc_bench/` and abort with a clear error if the repository cannot be reached.   <!-- FAILED-IN-EXECUTION: code/download_tau_c_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_tau_c_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_tau_c_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/pipelines/run_all.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/pipelines/run_all.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/pipelines/run_all.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_tau_c_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_tau_c_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_tau_c_bench.py exit=1 -->
  - **Output**: `data/raw/τc_bench/tasks.json` (raw JSON) and `data/raw/τc_bench/README.md` (download checksum).  
  - **Verification**: SHA‑256 checksum matches the value recorded in `state/projects/...yaml`; a unit test `tests/integration/test_download.py` asserts the file exists and is non‑empty.

- [ ] T002 [US1] Parse the downloaded JSON into a canonical CSV `data/derived/task_definitions.csv` containing the fields required by the `Task` schema (`task_id, goal, environment, optimal_path_length, tool_diversity_k, …`).  
  - **Output**: `data/derived/task_definitions.csv`.  
  - **Verification**: `pytest tests/contract/test_task_schema.py` validates the CSV against the schema; missing `optimal_path_length` values are left as `null`.

- [ ] T003 [US1] Execute the baseline CPU‑tractable agent (Llama‑2‑7B 8‑bit via Ollama) on the first ≤ 200 tasks (sorted by `task_id`) and record an execution log for each run. The script must enforce a hard 6‑hour wall‑clock limit per task, marking overruns as `status="timeout"` and logging the partial resource usage.  
  - **Output**: `data/derived/baseline_execution.csv` (conforms to `execution_log.schema.yaml`).  
  - **Verification**: `tests/contract/test_execution_log.py` checks schema compliance; a summary printed at the end of the run must show ≤ 200 rows.

- [ ] T004 [US1] Run the contract test suite for the baseline execution log and fail loudly if any record violates the schema (e.g., missing `warning_codes`).  
  - **Output**: Test report `tests/reports/baseline_log_report.txt`.  
  - **Verification**: CI step succeeds only when the report contains “0 failures”.

- [ ] T005 [US2] Compute the **efficiency penalty** for every task in `baseline_execution.csv` as  

  `penalty = total_calls / optimal_path_length`  

  If `optimal_path_length` is `null`, use `tool_diversity_k` and emit warning code `OPTIMAL_PATH_MISSING`. Produce a filtered CSV `data/derived/high_penalty_tasks.csv` that contains only rows with `penalty > 2.0`.  
  - **Output**: `data/derived/high_penalty_tasks.csv` (adds columns `optimal_used`, `penalty`, `warning_codes`).  
  - **Verification**: A sanity‑check script asserts that at least 10 tasks survive the filter and that every row with a warning includes `OPTIMAL_PATH_MISSING` in the `warning_codes` array.

---  

## Phase 2: Complete the study and validate its evidence  

| Goal | Build the difficulty predictor, evolve harder tasks, re‑run the agent, and perform statistical testing. |
|------|----------------------------------------------------------------------------------------------|

- [ ] T006 [US3] Train a lightweight `DecisionTreeRegressor` (max_depth = 5, `random_state=42`) on the feature set of `high_penalty_tasks.csv` to **predict the efficiency penalty** for each task. Split the data 80/20 (seed = 42) and require a hold‑out **R² ≥ 0.6** on the penalty prediction. Persist the model as a pickle.  
  - **Output**: `data/derived/penalty_model.pkl`.  
  - **Verification**: The training script prints the R²; a CI step parses the log and fails if R² < 0.6.

- [ ] T007 [US3] Using the trained penalty model, generate **≥ 5 evolved variants** for each high‑penalty task. Each variant must modify the task description or tool list to **maximize the predicted efficiency‑penalty gap**, ensuring the predicted **penalty** increases by at least 10 % over the base task. Store all variants in `data/derived/evolved_tasks.csv` adhering to the `evolved_task.schema.yaml`.  
  - **Output**: `data/derived/evolved_tasks.csv`.  
  - **Verification**: A validation script checks (a) schema compliance, (b) that `predicted_penalty` ≥ 1.1 × base `penalty`, and (c) that each `base_task_id` appears at least five times.

- [ ] T008 [US4] Re‑run the baseline agent on the **evolved task set** (`evolved_tasks.csv`) with the same timeout policy, producing a second execution log.  
  - **Output**: `data/derived/evolved_execution.csv` (schema‑compliant).  
  - **Verification**: Contract test `tests/contract/test_execution_log.py` is executed again; the report must show zero schema violations.

- [ ] T009 [US4] Perform the **trade‑off evaluation**:  
  1. Compute the **Spearman rank correlation** between the original baseline penalty (from `baseline_execution.csv`) and the change in success status (`success_baseline → success_evolved`).  
  2. Run **McNemar’s test** on the paired success outcomes of baseline vs. evolved tasks.  
  3. If the number of discordant pairs < 10, emit a power‑warning in the summary.  
  4. Generate `data/outputs/summary.csv` (includes correlation coefficient, p‑value, power flag) and two figures (`correlation.png`, `mcnemar.png`).  
  - **Output**: `data/outputs/summary.csv`, `data/outputs/figures/correlation.png`, `data/outputs/figures/mcnemar.png`.  
  - **Verification**: A CI step parses `summary.csv`; it must contain a numeric `spearman_rho`, a `mcnemar_pvalue`, and a `power_warning` column (`true/false`). The step also asserts that both PNG files exist. The step fails if `mcnemar_pvalue` ≥ 0.05 **and** `power_warning` is `false`.

- [ ] T010 [US4] **Sensitivity analysis**: repeat steps T005, T006, T007, T008, and T009 using an alternative optimal metric – the **minimum step count** (available in `task_definitions.csv` as `min_step_count`, or if absent, fallback to `tool_diversity_k`). Produce a second summary file `data/outputs/summary_sensitivity.csv` and accompanying figures prefixed with `sensitivity_`.  
  - **Output**: `data/outputs/summary_sensitivity.csv`, `data/outputs/figures/sensitivity_correlation.png`, `data/outputs/figures/sensitivity_mcnemar.png`.  
  - **Verification**: The same CI checks as T009 apply; additionally, a diff script asserts that the two summary files differ in at least one numeric column, confirming the analysis is not identical, and the step asserts that both sensitivity PNG files exist.

- [ ] T011 [US4] Assemble the **final research report** (`paper/report.md`) that:  
  1. Summarizes the methodology, cites the exact artifact paths, and includes the two figures (correlation & McNemar) for both primary and sensitivity runs.  
  2. Lists all quantitative results from `summary.csv` and `summary_sensitivity.csv`.  
  3. Discusses limitations (e.g., reliance on the tool‑diversity heuristic) and future work.  
  - **Output**: `paper/report.md`.  
  - **Verification**: A lightweight markdown linter (`markdownlint`) runs; the CI step also checks that every figure referenced exists in `data/outputs/figures/`.

- [ ] T014 [US1 & US4] Measure the **total wall‑clock runtime** of the full end‑to‑end pipeline (download → baseline → penalty → model → evolution → re‑run → evaluation → sensitivity → report). The script must fail if the cumulative runtime exceeds **6 hours** on a 2‑core CPU runner.  
  - **Output**: `data/derived/pipeline_runtime.txt` (contains total seconds).  
  - **Verification**: CI step parses the file and asserts total ≤ 21600 seconds; otherwise the run is marked failed.

- [ ] T015 [US4] Compute a **paired‑t‑test** on the paired success rates versus efficiency penalties (cost‑performance frontier) and record the test statistic and p‑value in `data/outputs/paired_t_test.csv`. The CI step must verify that the p‑value < 0.05 (or emit a power‑warning if sample size is insufficient).  
  - **Output**: `data/outputs/paired_t_test.csv`.  
  - **Verification**: CI parses the CSV; it fails if p‑value ≥ 0.05 **and** no power‑warning is present.

---  

## Phase 3: Reproducible results and paper handoff  

| Goal | Ensure that an external reviewer can re‑run the entire pipeline from raw data to the final report. |
|------|------------------------------------------------------------------------------------------|

- [ ] T012 [US1 & US4] Create a **single entry‑point script** `src/__main__.py` that orchestrates the full workflow in the correct order (download → baseline → penalty → model → evolution → re‑run → evaluation → sensitivity → report). The script must accept a single optional argument `--skip‑download` for cached runs.  
  - **Output**: `src/__main__.py`.  
  - **Verification**: Running `python -m src --skip-download` on a fresh clone reproduces all artifacts; a CI step compares the newly generated SHA‑256 hashes against those recorded in `state/projects/...yaml`.

- [ ] T013 [US1] Add a **quickstart guide** (`quickstart.md`) that documents the exact command to reproduce the study, the required Python version, and the environment variables for Ollama.  
  - **Output**: `quickstart.md`.  
  - **Verification**: The guide is parsed by a CI step that executes the command and checks that it exits with status 0.

---  

### Dependency / Requirement Coverage

| FR | Covered by Task(s) |
|----|--------------------|
| FR‑001 | T001, T002 |
| FR‑002 | T003, T008 |
| FR‑003 | T005 |
| FR‑004 | T009, T010 |
| FR‑005 | T009, T010 |
| FR‑006 | T005 (warning `OPTIMAL_PATH_MISSING`) |
| FR‑007 | T006, T007 |
| FR‑008 | T010 (alternative metric) |

| SC | Covered by Task(s) |
|----|--------------------|
| SC‑001 | T003, T008 (runtime ≤ 6 h, ≤ 200 tasks) |
| SC‑002 | T005 (penalty calculation) |
| SC‑003 | T009, T010 (p‑value < 0.05 or power warning) |
| SC‑004 | T006 (R² ≥ 0.6), T007 (penalty increase ≥ 10 %) |
| SC‑005 | T014 (overall pipeline runtime) |
| SC‑006 (Cost‑Performance Frontier) | T015 (paired‑t‑test) |

---  

*All tasks remain unchecked (`[ ]`) until their implementation and verification succeed.*  