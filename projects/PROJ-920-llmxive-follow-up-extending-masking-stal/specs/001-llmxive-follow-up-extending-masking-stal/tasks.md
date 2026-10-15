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

- [ ] T001 Create the project directory tree (`data/raw/`, `data/logs/`, `results/`, `code/`, `tests/`) and add a minimal `quickstart.md`.  
- [ ] T002 Generate a default technical‑term list (`code/config/density_terms.json`).  
- [ ] [x] T003 Implement `code/utils/entropy.py` (Shannon entropy on UTF‑8 bytes, with clamping for zero).  
- [ ] [x] T004 Implement `code/utils/heuristics.py` (composite density = 0.6 × entropy + 0.4 × technical‑token‑ratio).  
- [ ] [x] T005 Add unit tests for entropy (`tests/unit/test_entropy.py`).  
- [ ] [x] T006 Add unit tests for heuristics (`tests/unit/test_heuristics.py`).  
- [ ] [x] T007 Create `code/config/simulation_config.json` (α, threshold, seed, density‑levels, …).  
- [ ] [x] T008 Create `code/config/analysis_config.json` (min samples per bin, spline df candidates, density bins, horizon bins).  
- [ ] [x] T009 Add `code/validate_config.py` (schema & range checks for both config files).  
- [ ] [x] T010 Add `code/validate_grounding_config.py` (ensure simulation parameters respect Constitution VI).  

All scaffolding tasks are verified and checked.

---

## Phase 1 – Synthetic trajectory generation

- [ ] T011 **Generate synthetic trajectories**  
  *Script*: `code/generate_trajectories.py`  
  *Produces*: `data/raw/trajectories.json` (exactly 500 trajectories, balanced low/medium/high density).  
  *Key behaviour*:  
  – Accepts `--count` (default 500) and `--seed`.  
  – Uses `utils/entropy.py` and `utils/heuristics.py` to compute per‑turn entropy, technical‑token‑ratio, and final composite density.  
  – Enforces that each density bin contains ≥ 150 trajectories; aborts with error `INSUFFICIENT_SAMPLES_PER_BIN` otherwise.  
  – Logs bin counts and total file size (must be ≤ 100 MB).  

- [ ] T012 **Validate trajectories & edge‑case metadata**  
  *Script*: `code/validate_trajectories.py` (covers both T012 and T048).  
  *Consumes*: `data/raw/trajectories.json`.  
  *Checks*:  
  – For every trajectory, the entropy of the injected evidence block matches the requested density level within ±0.01 bits/token.  
  – If `critical_evidence_turn == T‑1` the trajectory includes `"is_last_turn": true`; otherwise the flag must be false.  
  – Exits with non‑zero status and a detailed error report on any violation.  

- [ ] T013 **Unit test for density isolation**  
  *Test file*: `tests/unit/test_density_isolation.py`  
  *Ensures*: `utils/heuristics.py` implements the exact composite formula from FR‑008 and does **not** depend on any agent‑output data.  

---

## Phase 2 – Agent simulation with variable retention horizons

- [ ] T014 **Simulate agent across horizons**  
  *Script*: `code/simulate_agent.py`  
  *Inputs*: `data/raw/trajectories.json`, `code/config/simulation_config.json`.  
  *Outputs*: `data/logs/simulation_results.csv` (conforms to `contracts/simulation_log.schema.yaml`).  
  *Logic*:  
  – Streams trajectories to keep RAM ≤ 2 GB.  
  – For each horizon = 1…T, computes visibility of the critical evidence and retrieval probability `P = sigmoid(α · (density ‑ threshold))`.  
  – Samples binary `success` = 1 iff evidence is visible **and** a Bernoulli draw with probability P succeeds; otherwise 0.  
  – Handles the “last‑turn” edge case via the `is_last_turn` flag.  
  – Accepts `--seed` for reproducibility.  

- [ ] T015 **Validate simulation resources & schema compliance**  
  *Script*: `code/validate_simulation.py` (covers T015, T016, T017).  
  *Checks*:  
  – Runs `simulate_agent.py` under `memory_profiler`; aborts with `MEMORY_LIMIT_EXCEEDED` if RSS > 7168 MiB.  
  – Confirms `data/logs/simulation_results.csv` exists, is non‑empty, and validates against `contracts/simulation_log.schema.yaml`.  
  – Executes contract tests `tests/contract/test_simulation_output.py` and integration test `tests/integration/test_horizon_masking.py`; any failure aborts with clear message.  

---

## Phase 3 – Statistical analysis & regime‑map generation

- [ ] T016 **Fit logistic regression & produce summary**  
  *Script*: `code/analyze_results.py`  
  *Inputs*: `data/logs/simulation_results.csv`, `code/config/analysis_config.json`.  
  *Outputs*:  
  – `results/regression_summary.json` (conforms to `contracts/regression_output.schema.yaml`).  
  – `results/hypothesis_summary.md` (includes coefficient, p‑value, and boolean `hypothesis_supported`).  
  *Steps*:  
  – Verify ≥ 10 samples per (density, horizon) bin; abort with informative error if not.  
  – Fit GLM: `success ~ density * ns(horizon, df_selected)` using `statsmodels`.  
  – Select spline degrees of freedom via AIC (helpers `fit_splines.py`, `select_spline_df.py`, `write_spline_output.py`).  

- [ ] T017 **Visualize regime map**  
  *Script*: `code/visualize_results.py`  
  *Consumes*: `data/logs/simulation_results.csv` and the selected spline df.  
  *Produces*: `results/regime_map.png` (3‑D surface, axes labeled “Masking Horizon”, “Semantic Density”, “Success Rate”, size ≤ 5 MB).  
  *Verification*:  
  – Runs contract test `tests/contract/test_regression_output.py` (ensures JSON schema).  
  – Runs integration test `tests/integration/test_plot_generation.py` (checks PNG exists, size > 10 KB, pixel variance > 0.01).  

---

## Phase 4 – End‑to‑end pipeline orchestration & smoke test

- [ ] T018 **Pipeline script**  
  *File*: `run_pipeline.sh`  
  *Orchestrates*: `generate_trajectories.py → validate_trajectories.py → simulate_agent.py → validate_simulation.py → analyze_results.py → visualize_results.py`.  
  *Features*:  
  – Propagates a single `--seed` to every stage.  
  – Performs data‑flow checks before each stage; aborts with “Data Flow Violation” if prerequisites are missing.  
  – After successful run, recomputes SHA‑256 checksums of all output files and aborts with “REPRODUCIBILITY_FAILURE” on mismatch.  

- [ ] T019 **End‑to‑end smoke test**  
  *Test file*: `tests/e2e/test_pipeline_smoke.py`  
  *Runs*: `run_pipeline.sh --count 100` (reduced trajectory count).  
  *Asserts*:  
  – All expected artifacts (`trajectories.json`, `simulation_results.csv`, `regression_summary.json`, `hypothesis_summary.md`, `regime_map.png`) are present and pass their respective schema/contract tests.  
  – Total runtime ≤ 6 h and peak RAM ≤ 7 GB (checked via `psutil`).  

---

## Phase 5 – Compliance, integrity checks, and final hand‑off

- [ ] T020 **Procedural integrity verification**  
  *Script*: `code/verify_procedural_integrity.py`  
  *Validates*: raw JSON & CSV schemas, non‑zero file sizes, and that SHA‑256 hashes match those recorded in `state/projects/PROJ-920-llmxive-follow-up-extending-masking-stal.yaml`.  

- [ ] T021 **Results integrity verification**  
  *Script*: `code/verify_results_integrity.py`  
  *Validates*: `results/regression_summary.json` against its schema, ensures all p‑values lie in [0, 1], checks `results/regime_map.png` size > 10 KB and pixel variance > 0.01.  

- [ ] T022 **Update quickstart with compliance step**  
  *File*: `docs/quickstart.md` (already exists) – add a section instructing users to run `verify_results_integrity.py` after the pipeline completes.  

- [ ] T023 **Final report generation**  
  *File*: `FINAL_REPORT.md`  
  *Contents*: seed used, interaction‑term coefficient, p‑value, boolean support decision, confirmation that all data are real synthetic outputs, and a concise answer to the research question.  

---

## Phase 6 – Optional documentation polish (not required for verification)

- [ ] T024 Update repository `README.md` with overview, installation, and usage.  
- [ ] T025 Create `docs/api.md` documenting public functions in `utils/`, `generate_trajectories.py`, and `simulate_agent.py`.  

---

### Dependency & execution order summary

| Task | Depends on |
|------|------------|
| T001‑T010 (scaffolding) | – |
| T011 | T001‑T010 |
| T012 | T011 |
| T013 | T007‑T010 (utility unit tests) |
| T014 | T011, T007 (simulation config) |
| T015 | T014 |
| T016 | T015 |
| T017 | T016 |
| T018 | T011, T012, T014, T015, T016, T017 |
| T019 | T018 |
| T020 | T018 (any successful run) |
| T021 | T018 |
| T022 | T018 |
| T023 | T018 |
| T024‑T025 | T001‑T010 (optional) |

All unchecked tasks are pending implementation; checked tasks have been verified against the specification and contracts. Running the pipeline from `T018` onward will produce a complete, reproducible end‑to‑end result that satisfies every functional requirement and success criterion.
