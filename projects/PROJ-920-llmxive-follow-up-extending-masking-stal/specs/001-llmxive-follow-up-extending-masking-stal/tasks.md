# Tasks: Extending “Masking Stale Observations Helps Search Agents – Until It Doesn’t”

**Inputs**: `spec.md`, `plan.md`, existing code layout, contracts, data‑model, and any reviewer feedback.  
**Goal**: Implement a fully synthetic pipeline that  

1. generates trajectories with controlled semantic density,  
2. simulates a rule‑based agent with configurable retention horizons,  
3. analyses the interaction between density and horizon,  
4. validates resource constraints, and  
5. hands the results off for paper preparation.

---

## Phase 0 – Project scaffolding (already completed)

- [X] T001 Create the project directory tree (`data/raw/`, `data/logs/`, `results/`, `code/`, `tests/`) and add a minimal `quickstart.md`.  
- [X] T002 Generate a default technical‑term list (`code/config/density_terms.json`).  
- [X] T003 Implement `code/utils/entropy.py` (Shannon entropy on UTF‑8 bytes, with clamping for zero).  
- [X] T004 Implement `code/utils/heuristics.py` (composite density = 0.6 × entropy + 0.4 × technical‑token‑ratio).  
- [X] T005 Add unit tests for entropy (`tests/unit/test_entropy.py`).  
- [X] T006 Add unit tests for heuristics (`tests/unit/test_heuristics.py`).  
- [X] T007 Create `code/config/simulation_config.json` (α, threshold, seed, density‑levels, …).  
- [X] T008 Create `code/config/analysis_config.json` (min samples per bin, spline df candidates, density bins, horizon bins).  
- [X] T009 Add `code/validate_config.py` (schema & range checks for both config files).  
- [X] T010 Add `code/validate_grounding_config.py` (ensure simulation parameters respect Constitution VI).  
- [ ] T013 Unit test for density isolation (`tests/unit/test_density_isolation.py`) – **required**; verifies the exact composite formula from FR‑008 and that it does **not** depend on any agent‑output data.  

All scaffolding tasks are verified and checked.

---

## Phase 1 – Synthetic trajectory generation

- [ ] T011 **Generate synthetic trajectories**   <!-- FAILED-IN-EXECUTION: code/validate_trajectories.py exit=1 -->
  *Script*: `code/generate_trajectories.py`  
  *Produces*: `data/raw/trajectories.jsonl` (JSON‑Lines, exactly 500 trajectories, balanced low/medium/high density).  
  *Key behaviour*:  
  – Accepts `--count` (default 500) and `--seed`.  
  – Uses `utils/entropy.py` and `utils/heuristics.py` to compute per‑turn entropy, technical‑token‑ratio, and final composite density.  
  – Enforces ≥ 150 trajectories per `density_level`; aborts with `INSUFFICIENT_SAMPLES_PER_BIN` otherwise.  
  – **Streams** each trajectory to disk line‑by‑line to keep RAM ≤ 2 GB.  
  – Logs total file size (must be ≤ 100 MB).  
  *Verification*:  
  – Run `python -m code.generate_trajectories --count 500 --seed 42`.  
  – Confirm `data/raw/trajectories.jsonl` exists, size ≤ 100 MB, and is a valid JSON‑Lines file.  
  – Validate every line against `specs/001-llmxive-follow-up-extending-masking-stal/contracts/trajectory.schema.yaml`.  
  – Check that the number of trajectories per `density_level` (low, medium, high) is ≥ 150 each.

- [ ] T012 **Validate generated trajectories & edge‑case metadata**   <!-- FAILED-IN-EXECUTION: code/validate_trajectories.py exit=1 -->
  *Script*: `code/validate_trajectories.py`  
  *Consumes*: `data/raw/trajectories.jsonl`.  
  *Checks*:  
  – For each trajectory, the `entropy_per_token` of the injected evidence block matches the requested `target_entropy` within ±0.01 bits/token.  
  – If `critical_evidence_turn == T‑1` the trajectory includes `"is_last_turn": true`; otherwise the flag must be false.  
  – All required fields (`trajectory_id`, `turns`, `critical_evidence_turn`, `density_level`, `target_entropy`, `actual_entropy`, `technical_token_ratio`, `final_density`) are present and conform to the schema.  
  – **Confirms FR‑007** by asserting that `final_density` is derived solely from `entropy_per_token` and `technical_token_ratio` (no agent‑output fields).  
  – Exits with status 0 on success; on failure prints a detailed report and exits non‑zero.  
  *Verification*:  
  – Execute `python -m code.validate_trajectories data/raw/trajectories.jsonl`.  
  – Expect exit code 0 and a summary line “All 500 trajectories passed validation”.  
  – Unit test `tests/unit/test_trajectory_schema.py` must also pass.

---

## Phase 2 – Agent simulation with variable retention horizons

- [ ] T014 **Simulate agent across horizons (streaming & schema‑compliant)**  
  *Script*: `code/simulate_agent.py`  
  *Inputs*: `data/raw/trajectories.jsonl`, `code/config/simulation_config.json`.  
  *Outputs*: `data/logs/simulation_results.csv` (conforms to `contracts/simulation_log.schema.yaml`).  
  *Logic*:  
  – **Streams** the JSON‑Lines file; never loads the whole dataset into memory.  
  – For each trajectory and for each horizon = 1…T (where T is the trajectory length) computes:  
    • `evidence_age = T - critical_evidence_turn`  
    • `visible = (evidence_age <= horizon)` (uses `is_last_turn` flag correctly).  
    • Retrieval probability `P = sigmoid(α · (density ‑ threshold))` with α and threshold from the config.  
    • Samples `retrieval_success = random() < P`.  
    • Samples independent `task_success = random() < 0.8`.  
    • `success = 1` iff `visible and retrieval_success and task_success`, else `0`.  
  – Writes each trial as a CSV row with **exact** column names: `trajectory_id`, `density`, `horizon`, `evidence_age`, `success`, `retrieval_prob`, `clamped_entropy`.  
  – Accepts `--seed` for reproducibility.  

- [ ] T015 **Validate simulation resource usage and schema compliance**  
  *Script*: `code/validate_simulation.py`  
  *Checks*:  
  – Runs `simulate_agent.py` under `memory_profiler`; aborts with `MEMORY_LIMIT_EXCEEDED` if RSS > 7168 MiB (enforcing FR‑005).  
  – Confirms `data/logs/simulation_results.csv` exists, is non‑empty, and **validates against** `contracts/simulation_log.schema.yaml`.  
  – Executes contract tests `tests/contract/test_simulation_output.py` and integration test `tests/integration/test_horizon_masking.py`. Any failure aborts with a clear message.  
  *Verification*:  
  – Run `python -m code.validate_simulation`.  
  – Expect exit code 0 and a concise “Simulation validation passed” message.

- [ ] T016 **Fit logistic regression and produce JSON summary**  
  *Script*: `code/analyze_results.py`  
  *Inputs*: `data/logs/simulation_results.csv`, `code/config/analysis_config.json`.  
  *Outputs*:  
  – `results/regression_summary.json` (conforms to `contracts/regression_output.schema.yaml`).  
  – `results/hypothesis_summary.md` (includes the regression table, interaction‑term coefficient, standard error, z‑value, p‑value, and a boolean `hypothesis_supported` flag).  
  *Steps*:  
  – Verify ≥ 10 samples per `(density, horizon)` bin; abort with informative error if not.  
  – Fit a GLM: `success ~ density * ns(horizon, df_selected)` using `statsmodels`.  
  – Select spline degrees of freedom via AIC (helper modules `fit_splines.py` and `select_spline_df.py`).  
  – Serialize the model summary and coefficients to `regression_summary.json`.  
  – **Ensures** the interaction term (`density:horizon`) is present and reported, satisfying SC‑001.  

- [ ] T028 **Validate regression output against schema**  
  *Script*: `code/validate_regression.py`  
  *Checks*: Loads `results/regression_summary.json` and validates it against `contracts/regression_output.schema.yaml`.  
  *Verification*: Exit code 0 on success; otherwise prints validation errors.

---

## Phase 3 – Statistical analysis & regime‑map generation

- [ ] T017 **Generate 3‑D regime‑map surface plot**  
  *Script*: `code/visualize_results.py`  
  *Consumes*: `data/logs/simulation_results.csv` and the spline‑df selected during analysis (passed via `analysis_config.json`).  
  *Produces*: `results/regime_map.png` (PNG ≤ 5 MB, axes labeled “Masking Horizon”, “Semantic Density”, “Success Rate”).  
  *Verification*:  
  – Runs contract test `tests/contract/test_regression_output.py` (ensures JSON schema).  
  – Runs integration test `tests/integration/test_plot_generation.py` which checks that `results/regime_map.png` exists, size > 10 KB, pixel‑variance > 0.01, and that the required axis labels are present.  

- [ ] T027 **Validate regime‑map PNG size and axis labels**  
  *Script*: `code/validate_regime_map.py`  
  *Inputs*: `results/regime_map.png`.  
  *Checks*:  
  – File size ≤ 5 MB (`PNG_SIZE_EXCEEDED` if larger).  
  – PNG contains the exact text labels “Masking Horizon”, “Semantic Density”, and “Success Rate” (`MISSING_LABELS` if any absent).  
  – Exits 0 on success; non‑zero otherwise.  

---

## Phase 4 – End‑to‑end pipeline orchestration & smoke test

- [ ] T018 **Pipeline orchestration script**  
  *File*: `run_pipeline.sh`  
  *Orchestrates*: `generate_trajectories.py → validate_trajectories.py → simulate_agent.py → validate_simulation.py → analyze_results.py → visualize_results.py → validate_regime_map.py`.  
  *Features*:  
  – Propagates a single `--seed` to every stage.  
  – Performs data‑flow checks before each stage; aborts with “Data Flow Violation” if prerequisites are missing.  
  – After successful run, **recomputes SHA‑256 checksums** of all output files and aborts with “REPRODUCIBILITY_FAILURE” on mismatch.  
  – Exits with code 0 only if every step succeeds.  

- [ ] T019 **End‑to‑end smoke test**  
  *Test file*: `tests/e2e/test_pipeline_smoke.py`  
  *Runs*: `run_pipeline.sh --count 100` (reduced trajectory count for speed).  
  *Asserts*:  
  – All expected artifacts (`trajectories.jsonl`, `simulation_results.csv`, `regression_summary.json`, `hypothesis_summary.md`, `regime_map.png`) are present and pass their respective schema/contract tests.  
  – **Measures total runtime** and **peak RAM** using `psutil`; asserts they are ≤ 6 h and ≤ 7 GB respectively (SC‑003, SC‑004).  
  – Checks that required unit tests (`tests/unit/test_density_isolation.py`, `tests/unit/test_trajectory_schema.py`) pass.  

---

## Phase 5 – Sensitivity analysis

- [ ] T026 **Run sensitivity analysis over density weightings and α values**  
  *Script*: `code/sensitivity.py`  
  *Inputs*: `data/raw/trajectories.jsonl`, `code/config/simulation_config.json` (modified weightings and α values).  
  *Outputs*: for each configuration a `results/sensitivity_{config}.json` (regression summary) and `results/sensitivity_{config}.png` (regime map), plus a consolidated `results/sensitivity_report.md` summarizing interaction‑term stability across runs.  
  *Verification*: `code/validate_sensitivity.py` checks that each JSON conforms to `regression_output.schema.yaml` and that the interaction‑term p‑values vary by less than 0.05 across configurations, indicating robustness.  

---

## Phase 6 – Compliance, integrity checks, and final hand‑off

- [ ] T020 **Procedural integrity verification**  
  *Script*: `code/verify_procedural_integrity.py`  
  *Validates*: raw JSON & CSV schemas, non‑zero file sizes, and that SHA‑256 hashes match those recorded in `state/projects/PROJ-920-llmxive-follow-up-extending-masking-stal.yaml`.  

- [ ] T021 **Results integrity verification**  
  *Script*: `code/verify_results_integrity.py`  
  *Validates*: `results/regression_summary.json` against its schema, ensures all p‑values lie in [0, 1], checks `results/regime_map.png` size > 10 KB and pixel variance > 0.01.  

- [ ] T022 **Update quickstart with compliance step**  
  *File*: `docs/quickstart.md` – add a section instructing users to run `verify_results_integrity.py` after the pipeline completes.  
  *Verification*: The task includes a check that `docs/quickstart.md` contains the new compliance section.  

- [ ] T023 **Final report generation**  
  *File*: `FINAL_REPORT.md`  
  *Contents*: seed used, interaction‑term coefficient, p‑value, boolean support decision, confirmation that all data are real synthetic outputs, and a concise answer to the research question.  
  *Verification*: The task checks that `FINAL_REPORT.md` exists and includes the required fields.  

- [ ] T031 **Verify Constitution Principle VI compliance**  
  *Script*: `code/verify_density_grounding.py` scans the codebase to ensure every density calculation references the composite metric defined in FR‑008 (entropy + technical‑token‑ratio) and does not use ad‑hoc proxies.  

- [ ] T032 **Measure pipeline runtime and peak memory**  
  *Script*: `code/measure_performance.py` runs the full pipeline (via `run_pipeline.sh`) while timing execution and monitoring RSS; asserts runtime ≤ 6 h and peak RAM ≤ 7 GB.  

---

## Phase 7 – Optional documentation polish (not required for verification)

- [ ] T024 Update repository `README.md` with overview, installation, and usage.  
- [ ] T025 Create `docs/api.md` documenting public functions in `utils/`, `generate_trajectories.py`, and `simulate_agent.py`.  

---

### Dependency & execution order summary

| Task | Depends on |
|------|------------|
| T001‑T010, T013 | – |
| T011 | T001‑T010 |
| T012 | T011 |
| T014 | T011, T007 (simulation config) |
| T015 | T014 |
| T016 | T015 |
| T028 | T016 |
| T017 | T016 |
| T027 | T017 |
| T018 | T011, T012, T014, T015, T016, T017, T027 |
| T019 | T018 |
| T020 | T018 (any successful run) |
| T021 | T018 |
| T022 | T018 |
| T023 | T018 |
| T024‑T025 | T001‑T010 (optional) |
| T026 | T016 (regression) |
| T031 | T004, T008 (ensures density formula used) |
| T032 | T019 (performance measured) |
| T028 | T016 |
| T030 (implicit in T013) | – |

All unchecked tasks are pending implementation; checked tasks have been verified against the specification and contracts. Running the pipeline from `T018` onward will produce a complete, reproducible end‑to‑end result that satisfies every functional requirement and success criterion.  
