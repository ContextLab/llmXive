# Tasks: LLM Agent Efficiency vs. Reasoning Trade‑off Analysis  

**Inputs**: `spec.md`, `plan.md`, the contracts in `specs/001-llmxive-follow-up-extending-a-matter-of/contracts/`.  

The study must satisfy all functional requirements (FR‑001 – FR‑008) and success criteria (SC‑001 – SC‑010). Tasks are ordered to respect data dependencies; each task’s output is a concrete artifact that can be validated by the schemas in `specs/.../`.  

---  

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] T001 [US-1] **Download τⁿ‑Bench dataset** from the official HuggingFace repository (`datasets.load_dataset("tau_c_bench")`) into `data/raw/τc_bench/`. Abort with a clear error if the repository cannot be reached.   <!-- FAILED-IN-EXECUTION: src/pipelines/run_all.py exit=1 -->
  - **Output**: `data/raw/τc_bench/tasks.json` (raw JSON) and `data/raw/τc_bench/README.md` (checksum).  
  - **Verification**: SHA‑256 checksum matches the value recorded in `state/projects/...yaml`; unit test `tests/integration/test_download.py` asserts the file exists, is non‑empty, and the checksum is correct.  

- [ ] T002 [US-1] **Parse task definitions** from `data/raw/τc_bench/tasks.json` into a canonical CSV `data/derived/task_definitions.csv` containing the fields required by the `Task` schema (`task_id, goal, environment, optimal_path_length, tool_diversity_k, …`). Missing `optimal_path_length` values are left as `null`.   <!-- FAILED-IN-EXECUTION: code/parse_task_definitions.py exit=1 -->
  - **Output**: `data/derived/task_definitions.csv`.  
  - **Verification**: `pytest tests/contract/test_task_schema.py` validates each row against the schema; the script logs any `null` `optimal_path_length` entries for later warning handling.  

- [ ] T003 [US-1] **Run baseline CPU‑tractable agent** (Llama‑2‑7B 8‑bit via Ollama) on the first ≤ 150 tasks (sorted by `task_id`). Enforce a hard 6‑hour wall‑clock limit per task; overruns are recorded as `status="timeout"` with partial resource usage.  
  - **Output**: `data/derived/baseline_execution.csv` (conforms to `execution_log.schema.yaml`).  
  - **Verification**: `tests/contract/test_execution_log.py` checks schema compliance; a summary printed at the end must show exactly the number of rows requested (≤ 150).  

- [ ] T004 [US-1] **Validate baseline execution logs** by running the full contract test suite. Any record violating the schema (e.g., missing required fields) must cause the step to fail loudly.  
  - **Output**: `tests/reports/baseline_log_report.txt`.  
  - **Verification**: CI succeeds only when the report contains “0 failures”.  

- [ ] T005 [US-2] **Compute efficiency penalty** for every task in `baseline_execution.csv`. Use the **optimal path length** when the field `optimal_path_length` is present; otherwise fall back to the **tool‑diversity heuristic** (`tool_diversity_k`).  
    - Formula: `penalty = total_calls / optimal_path_length` if `optimal_path_length` is not null, else `penalty = total_calls / tool_diversity_k`.  
    - If **both** `optimal_path_length` **and** `tool_diversity_k` are missing, emit warning code `OPTIMAL_PATH_MISSING` and skip the task.  
  Produce two derived files:  
    1. `data/derived/penalty_metrics.csv` (adds columns `optimal_used`, `penalty`, `warning_codes`).  
    2. `data/derived/high_penalty_tasks.csv` (rows with `penalty > 2.0`).  
  - **Verification**: A sanity‑check script asserts that at least 30 % of tasks have `penalty > 2.0` (SC‑002) and that every row with a warning includes `OPTIMAL_PATH_MISSING` in the `warning_codes` array.  

---  

## Phase 2 – Modeling, evolution, and trade‑off evaluation  

- [ ] T006 [US-4] **Point‑biserial correlation** between the continuous `penalty` (full task set) and binary `success`. Store results in `data/derived/correlation_results.json` (Pearson *r*, *p*‑value, 95 % CI). Verify that *p* < 0.05 and |*r*| ≥ 0.2 (SC‑009).  
  - **Verification**: CI step parses the JSON and fails if the statistical thresholds are not met.  

- [ ] T007 [US-3] **Train regression tree** to predict the efficiency penalty from task features. Use `DecisionTreeRegressor(max_depth=5, random_state=42)` on the **full** task set (80/20 split, seed = 42). Persist the model as `data/derived/penalty_model.pkl`. Require hold‑out R² ≥ 0.6 (SC‑007).  
  - **Verification**: Training script prints the R²; a CI step extracts the value and fails if it falls below 0.6.  

- [ ] T008 [US-3] **Generate evolved task variants** for each high‑penalty task (`high_penalty_tasks.csv`). For every base task, create **≥ 5** variations that maximize the predicted penalty gap, guaranteeing `predicted_penalty ≥ 1.10 × base_penalty`. Emit records conforming to `evolved_task.schema.yaml` in `data/derived/evolved_tasks.csv`.  
  - **Verification**: Validation script checks (a) schema compliance, (b) the 10 % penalty increase, and (c) that each `base_task_id` appears at least five times.  

- [ ] T009 [US-4] **Re‑run baseline agent on evolved tasks** with the same timeout policy. Produce `data/derived/evolved_execution.csv` (schema‑compliant).  
  - **Verification**: Contract test `tests/contract/test_execution_log.py` runs again; the report must show zero violations.  

- [ ] T010 [US-4] **Trade‑off evaluation (primary analysis)**:  
    1. **McNemar’s test** on paired success outcomes (`baseline_success` vs. `evolved_success`).  
    2. **Paired t‑test** on baseline vs. evolved success‑rate differences (new task T016 supplies the results).  
    3. **Logistic regression** `evolved_success ~ baseline_penalty + difficulty_score` and record coefficients, odds ratios, *p*‑values, and 95 % CIs.  
    4. **Cost‑performance frontier** quantified via the effect size from the paired t‑test (difference in success proportion per unit penalty) and stored in `data/outputs/cost_performance_frontier.csv`.  
    5. Generate `data/outputs/summary.csv` (includes McNemar χ², *p*‑value, paired‑t *p*‑value, logistic coefficients, frontier effect size, and a `power_warning` flag if discordant pairs < 10).  
    6. Produce figures `data/outputs/figures/mcnemar.png`, `data/outputs/figures/logistic_coefficients.png`, and `data/outputs/figures/cost_performance_frontier.png`.  
  - **Verification**: CI parses `summary.csv`; it must contain a numeric `mcnemar_pvalue` < 0.05 **or** a `power_warning=true`. Logistic coefficient for `baseline_penalty` must be negative and *p* < 0.05. The cost‑performance frontier effect size must be reported and the corresponding PNG must exist.  

- [ ] T011 [US-4] **Sensitivity analysis** using the alternative optimal metric **minimum step count** (if `minimum_step_count` exists in `task_definitions.csv`; otherwise fall back to `optimal_path_length` then to `tool_diversity_k`). Repeat steps T005‑T010 with this metric, producing a second set of artifacts prefixed with `sensitivity_` (e.g., `data/derived/sensitivity_penalty_metrics.csv`, `data/outputs/summary_sensitivity.csv`, `data/outputs/figures/sensitivity_mcnemar.png`). Verify that the logistic‑regression penalty coefficient retains the same sign and that the absolute difference between the two coefficients ≤ 0.05 (SC‑010).  
  - **Verification**: Diff script asserts the sign match and effect‑size difference constraint; CI fails otherwise.  

- [ ] T016 [US-4] **Paired t‑test on success‑rate differences** between baseline and evolved task runs. Compute mean difference, 95 % CI, t‑statistic, and *p*‑value; store results in `data/derived/paired_t_test_results.csv`.  
  - **Verification**: CI ensures the CSV contains numeric `pvalue` and that either `pvalue < 0.05` or a `power_warning=true` flag is set.  

- [ ] T017 [US-4] **Cost‑performance frontier (effect‑size) calculation** using the paired t‑test results. Derive the marginal change in success proportion per unit penalty increase, write to `data/outputs/cost_performance_frontier.csv`, and plot `data/outputs/figures/cost_performance_frontier.png`.  
  - **Verification**: CI checks that the CSV contains a numeric `effect_size` column and that the PNG file exists.  

- [ ] T018 [US-4] **SC‑001 compliance check**: Verify that the average success rate on evolved tasks is ≤ 0.90 × baseline success rate and that this drop is statistically significant (uses results from T016). Produce `data/outputs/sc001_report.txt` summarizing the observed drop and significance.  
  - **Verification**: CI parses the report and fails if the drop is < 10 % or the paired‑t *p*‑value ≥ 0.05.  

---  

## Phase 3 – Reproducibility, runtime budget, and hand‑off  

- [ ] T013 [US-1 & US-4] **Measure total pipeline runtime**. Wrap the entire end‑to‑end execution (download → baseline → penalty → correlation → model → evolution → re‑run → evaluation → sensitivity → report) with a timer and write the total seconds to `data/derived/pipeline_runtime.txt`. CI fails if the total exceeds **6 hours** (21600 s) on a 2‑core CPU runner (SC‑005).  
  - **Verification**: CI parses the file and asserts the limit.  

- [ ] T014 [US-1] **Create entry‑point script** `src/__main__.py` that orchestrates the full workflow in the correct order, accepts `--skip-download` to reuse cached data, and logs each phase’s start/end timestamps.  
  - **Verification**: Running `python -m src --skip-download` on a fresh clone reproduces all artifacts; a CI step compares the newly generated SHA‑256 hashes against those recorded in `state/projects/...yaml`.  

- [ ] T015 [US-1] **Update quickstart guide** `quickstart.md` with the exact command to reproduce the study, required Python version, Ollama setup instructions, and the optional `--skip-download` flag.  
  - **Verification**: CI parses the guide, executes the documented command, and checks for exit status 0.  

---  

### Requirement / Success‑Criterion Mapping  

| FR | Covered by Tasks |
|----|------------------|
| FR‑001 | T001, T002 |
| FR‑002 | T003, T009 |
| FR‑003 | T005 |
| FR‑004 | T006, T010, T011 |
| FR‑005 | T010 (paired t‑test via T016) |
| FR‑006 | T005 (warning `OPTIMAL_PATH_MISSING`) |
| FR‑007 | T007, T008 |
| FR‑008 | T011 (alternative metric) |

| SC | Covered by Tasks |
|----|------------------|
| SC‑001 | T018 (success‑rate drop) |
| SC‑002 | T005 (≥ 30 % tasks with penalty > 2.0) |
| SC‑003 | T010, T011 (p < 0.05 or power warning) |
| SC‑004 | T007 (R² ≥ 0.6), T008 (penalty ≥ 10 % increase) |
| SC‑005 | T013 (overall runtime ≤ 6 h) |
| SC‑006 | T003, T009 (log completeness) |
| SC‑007 | T007 (R² ≥ 0.6) |
| SC‑008 | T008 (≥ 10 % penalty increase) |
| SC‑009 | T006 (|r| ≥ 0.2, p < 0.05) |
| SC‑010 | T011 (sign consistency, effect‑size Δ ≤ 0.05) |

*All tasks remain unchecked (`[ ]`) until their implementation and verification succeed.*  