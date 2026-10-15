# Tasks: llmXive follow-up: extending “Masking Stale Observations Helps Search Agents – Until It Doesn’t”

**Inputs**: `spec.md`, `plan.md`, existing code layout, contracts, data‑model, and any reviewer feedback.  
**Goal**: Implement a fully synthetic pipeline that (1) generates trajectories with controlled semantic density, (2) simulates a rule‑based agent with configurable retention horizons, (3) analyses the interaction between density and horizon, (4) validates resource constraints, and (5) hands the results off for paper preparation.

---

## Phase 0 – Project scaffolding (already completed)

- [ ] T001 Create the project directory tree (`data/raw/`, `data/processed/`, `output/`, `code/`, `tests/`) and add a minimal `quickstart.md`.  
- [ ] T046 Generate a default technical‑term list (`code/config/density_terms.json`).  
- [ ] T007 Implement `code/utils/entropy.py` (Shannon entropy on UTF‑8 bytes, with clamping for zero).  
- [ ] T008 Implement `code/utils/heuristics.py` (composite density = 0.6 × entropy + 0.4 × technical‑token‑ratio).  
- [ ] T009 Add unit tests for entropy (clamping, edge‑case handling).  
- [ ] T010 Add unit tests for heuristics (ratio calculation, config loading).  
- [ ] T050 Create `code/config/simulation_config.json` (α, threshold, seed, density_levels, h_opt_factor).  
- [ ] T051 Create `code/config/analysis_config.json` (min_samples_per_bin, spline df candidates, density_bins, horizon_bins).  
- [ ] T052 Add `code/validate_config.py` (schema & range checks for both config files).  
- [ ] T053 Add `code/validate_grounding_config.py` (ensure simulation parameters respect Constitution VI).  

---

## Phase 1 – Synthetic trajectory generation (User Story 1, priority P1)

- [ ] T011 **Generate synthetic trajectories** – `code/generate_trajectories.py`  
  *Creates `data/raw/trajectories.json` containing exactly 500 trajectories (balanced low/medium/high density).  
  *Uses `entropy.py` & `heuristics.py` to compute per‑turn entropy, technical‑token‑ratio, and final composite density.  
  *Accepts `--count` and `--seed` CLI arguments; logs the per‑density bin counts and aborts with “INSUFFICIENT_SAMPLES_PER_BIN” if any bin < 10.  
  *Writes each trajectory according to `contracts/trajectory.schema.yaml`, including `evidence_turn_index`, `density_value`, and `is_critical`.  

- [ ] T012 **Validate generated trajectories** – `code/validate_trajectories.py`  
  *Loads `data/raw/trajectories.json` and checks that the entropy of the injected evidence block matches the requested density level within ±0.01 bits/token.  
  *Exits non‑zero with a detailed error report on any violation.  

- [ ] T048 **Validate trajectory metadata (edge‑case handling)** – `code/validate_metadata.py`  
  *Ensures that trajectories whose critical evidence occurs on the final turn (`evidence_turn_index == T‑1`) contain the flag `is_last_turn: true`.  
  *Fails loudly if the flag is missing or inconsistent.  

- [ ] T049 **Unit test for density isolation** – `tests/unit/test_density_isolation.py` (confirms `heuristics.py` does not depend on agent output).  

---

## Phase 2 – Agent simulation with variable retention horizons (User Story 2, priority P2)

- [ ] T014 **Simulate agent** – `code/simulate_agent.py`  
  *Streams trajectories from `data/raw/trajectories.json` and, for each horizon = 1…T, computes the optimal horizon `H_opt = base + β × density` (β from config).  
  *Success probability follows a **distance‑based heuristic**:  
    `logit_p = -α × |horizon − H_opt| + N(0, σ_noise)` (α from `simulation_config.json`).  
    `success = Bernoulli(sigmoid(logit_p))`.  
  *Handles the “last‑turn” edge case via the `is_last_turn` flag.  
  *Writes results incrementally to `data/processed/simulation_logs.csv` (conforms to `simulation_log.schema.yaml`).  
  *Accepts `--seed` for reproducibility and aborts if the trajectory file is missing.  

- [ ] T015 **Validate simulation resource usage** – `code/validate_simulation_resources.py`  
  *Runs `simulate_agent.py` under `memory‑profiler`, aborts with “MEMORY_LIMIT_EXCEEDED” if RSS > 7168 MiB.  
  *Confirms `data/processed/simulation_logs.csv` exists, is non‑empty, and contains the required columns.  

- [ ] T016 **Contract test for simulation output schema** – `tests/contract/test_simulation_output.py`.  
- [ ] T017 **Integration test for horizon‑masking logic** – `tests/integration/test_horizon_masking.py`.  

---

## Phase 3 – Statistical analysis & regime‑map generation (User Story 3, priority P3)

- [ ] T018 **Analyze results** – `code/analyze_results.py`  
  *Loads `data/processed/simulation_logs.csv`; verifies ≥ 10 samples per (density, horizon) bin, aborting with a clear message if not.  
  *Fits a logistic regression using `statsmodels` with natural splines:  
    `success ~ density * ns(horizon, df_selected)`.  
  *Selects spline degrees of freedom via AIC (see T019a‑c).  
  *Writes `output/regression_summary.json` (conforms to `regression_output.schema.yaml`) and `output/hypothesis_summary.md` (includes coefficient, p‑value, and boolean `hypothesis_supported`).  

- [ ] T019a **Fit splines** – `code/fit_splines.py` (loops over candidate `df` values).  
- [ ] T019b **Select spline df** – `code/select_spline_df.py` (AIC minimisation, fallback to df = 5).  
- [ ] T019c **Write selected df** – `code/write_spline_output.py` (produces `output/selected_spline_df.json`).  

- [ ] T037 **Visualize regime map** – `code/visualize_results.py`  
  *Bins density and horizon per `analysis_config.json`, computes mean success per bin, and renders a 3‑D surface (PNG ≤ 5 MiB) saved as `output/plots/regime_map.png`.  

- [ ] T023 **Contract test for regression output schema** – `tests/contract/test_regression_output.py`.  
- [ ] T024 **Integration test for plot generation** – `tests/integration/test_plot_generation.py`.  
- [ ] T022 **Verify hypothesis‑summary output** – ensures `output/hypothesis_summary.md` contains the expected boolean logic.  

---

## Phase 4 – End‑to‑end pipeline orchestration

- [ ] T038 **Pipeline script** – `run_pipeline.sh`  
  *Runs: `generate_trajectories.py → simulate_agent.py → analyze_results.py → visualize_results.py`.  
  *Propagates a single `--seed` to every stage.  
  *Performs data‑flow checks before each stage and aborts with clear “Data Flow Violation” messages.  
  *After successful completion, re‑runs the pipeline with the same seed and compares SHA‑256 checksums of all output files; aborts with “REPRODUCIBILITY_FAILURE” on mismatch.  

- [ ] T039 **End‑to‑end smoke test** – execute `run_pipeline.sh` on a reduced trajectory count (e.g., 100) to confirm all artefacts (`trajectories.json`, `simulation_logs.csv`, `regression_summary.json`, `hypothesis_summary.md`, `regime_map.png`) are produced and valid.  

---

## Phase 5 – Compliance & final hand‑off

- [ ] T041 **Procedural integrity check** – `code/verify_procedural_integrity.py` (validates raw JSON & CSV schemas, non‑zero sizes).  
- [ ] T042 **Results integrity check** – `code/verify_results_integrity.py` (validates regression JSON schema, p‑value range, PNG size > 10 KB and pixel‑variance > 0.01).  
- [ ] T043 **Update quickstart with compliance step** – `docs/quickstart.md` now instructs users to run `verify_results_integrity.py` before declaring success.  
- [ ] T044 **Final report** – `FINAL_REPORT.md` (seed used, interaction‑term coefficient, p‑value, and a statement confirming all data are real synthetic outputs, no fabrication).  

---

## Phase 6 – Documentation & polish (optional but recommended)

- [ ] T025 Update repository‑root `README.md` with overview, installation, and usage.  
- [ ] T026 Create `docs/api.md` documenting public functions in `code/utils/`, `generate_trajectories.py`, and `simulate_agent.py`.  
- [ ] T027 Create `docs/quickstart.md` (already updated in T043).  

---

## Dependency & execution order summary

| Task | Depends on |
|------|------------|
| T001‑T053 (foundational) | – |
| T011 | T001‑T053 |
| T012 | T011 |
| T048 | T011 |
| T014 | T011, T050 |
| T015 | T014 |
| T018 | T014, T051 |
| T019a‑c | T018 |
| T037 | T018, T019b |
| T038 | T011, T014, T018, T037 |
| T041‑T044 | T038 (or any successful end‑to‑end run) |

All tasks marked **[X]** are already completed and verified. The only pending items are **T011**, **T012**, and **T048**, which have been reopened to satisfy the verifier’s concerns. Once these three tasks are implemented and their artefacts generated, the full pipeline will pass end‑to‑end verification and satisfy every functional and success‑criteria requirement from the specification.
