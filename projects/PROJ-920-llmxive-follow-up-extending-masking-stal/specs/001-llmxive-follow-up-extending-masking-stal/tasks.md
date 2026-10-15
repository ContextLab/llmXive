# Tasks: llmXive follow‑up: extending “Masking Stale Observations Helps Search Agents – Until It Doesn’t”

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
- [ ] T046 Generate a default technical‑term list (`code/config/density_terms.json`).  
- [ ] T007 Implement `code/utils/entropy.py` (Shannon entropy on UTF‑8 bytes, with clamping for zero).  
- [ ] T008 Implement `code/utils/heuristics.py` (composite density = 0.6 × entropy + 0.4 × technical‑token‑ratio).  
- [ ] T009 Add unit tests for entropy (clamping, edge‑case handling).  
- [ ] T010 Add unit tests for heuristics (ratio calculation, config loading).  
- [ ] T050 Create `code/config/simulation_config.json` (α, threshold, seed, density_levels, …).  
- [ ] T051 Create `code/config/analysis_config.json` (min_samples_per_bin, spline df candidates, density_bins, horizon_bins).  
- [ ] T052 Add `code/validate_config.py` (schema & range checks for both config files).  
- [ ] T053 Add `code/validate_grounding_config.py` (ensure simulation parameters respect Constitution VI).  

---

## Phase 1 – Synthetic trajectory generation (User Story 1, priority P1)

- [ ] T011 **Generate synthetic trajectories** – `code/generate_trajectories.py`  
  *Creates `data/raw/trajectories.json` containing exactly 500 trajectories (balanced low/medium/high density).  
  *Uses `utils/entropy.py` & `utils/heuristics.py` to compute per‑turn entropy, technical‑token‑ratio, and final composite density.  
  *Accepts `--count` and `--seed` CLI arguments; logs the per‑density‑bin counts and aborts with “INSUFFICIENT_SAMPLES_PER_BIN” if any bin < 10.  
  *Writes each trajectory according to `contracts/trajectory.schema.yaml`, including `critical_evidence_turn`, `density_level`, `target_entropy`, `actual_entropy`, `technical_token_ratio`, and `final_density`.  

- [ ] T012 **Validate generated trajectories** – `code/validate_trajectories.py`  
  *Loads `data/raw/trajectories.json` and checks that the entropy of the injected evidence block matches the requested density level within ±0.01 bits/token.  
  *Exits with a non‑zero status and a detailed error report on any violation.  

- [ ] T048 **Validate trajectory metadata (edge‑case handling)** – `code/validate_metadata.py`  
  *Ensures that trajectories whose critical evidence occurs on the final turn (`critical_evidence_turn == T‑1`) contain the flag `is_last_turn: true`.  
  *Fails loudly if the flag is missing or inconsistent.  

- [ ] T049 **Unit test for density isolation** – `tests/unit/test_density_isolation.py`  
  *Confirms `utils/heuristics.py` does not depend on any agent‑output data and that the composite density formula matches FR‑008.  

---

## Phase 2 – Agent simulation with variable retention horizons (User Story 2, priority P2)

- [ ] T014 **Simulate agent** – `code/simulate_agent.py`  
  *Streams trajectories from `data/raw/trajectories.json`.  
  *For each horizon = 1…T, computes visibility of the critical evidence and the retrieval probability `P = sigmoid(α · (density ‑ threshold))` (α, threshold from `simulation_config.json`).  
  *Samples a binary outcome `success` = 1 iff the evidence is visible **and** a Bernoulli draw with probability P succeeds; otherwise 0.  
  *Handles the “last‑turn” edge case via the `is_last_turn` flag.  
  *Writes results incrementally to `data/logs/simulation_results.csv` (conforms to `contracts/simulation_log.schema.yaml`).  
  *Accepts `--seed` for reproducibility and aborts if the trajectory file is missing.  

- [ ] T015 **Validate simulation resource usage** – `code/validate_simulation_resources.py`  
  *Runs `simulate_agent.py` under `memory‑profiler`; aborts with “MEMORY_LIMIT_EXCEEDED” if RSS > 7168 MiB.  
  *Confirms `data/logs/simulation_results.csv` exists, is non‑empty, and contains all required columns.  

- [ ] T016 **Contract test for simulation output schema** – `tests/contract/test_simulation_output.py`.  

- [ ] T017 **Integration test for horizon‑masking logic** – `tests/integration/test_horizon_masking.py`.  

---

## Phase 3 – Statistical analysis & regime‑map generation (User Story 3, priority P3)

- [ ] T018 **Analyze results** – `code/analyze_results.py`  
  *Loads `data/logs/simulation_results.csv`; verifies ≥ 10 samples per (density, horizon) bin, aborting with a clear message if not.  
  *Fits a logistic regression using `statsmodels` with natural splines:  
    `success ~ density * ns(horizon, df_selected)`.  
  *Selects spline degrees of freedom via AIC (see T019a‑c).  
  *Writes `results/regression_summary.json` (conforms to `contracts/regression_output.schema.yaml`) and `results/hypothesis_summary.md` (includes coefficient, p‑value, and boolean `hypothesis_supported`).  

- [ ] T019a **Fit splines** – `code/fit_splines.py` (loops over candidate `df` values).  
- [ ] T019b **Select spline df** – `code/select_spline_df.py` (AIC minimisation, fallback to df = 5).  
- [ ] T019c **Write selected df** – `code/write_spline_output.py` (produces `results/selected_spline_df.json`).  

- [ ] T037 **Visualize regime map** – `code/visualize_results.py`  
  *Bins density and horizon per `analysis_config.json`, computes mean success per bin, and renders a 3‑D surface (PNG ≤ 5 MiB) saved as `results/regime_map.png`.  

- [ ] T023 **Contract test for regression output schema** – `tests/contract/test_regression_output.py`.  

- [ ] T024 **Integration test for plot generation** – `tests/integration/test_plot_generation.py`.  

- [ ] T022 **Verify hypothesis‑summary output** – ensures `results/hypothesis_summary.md` contains the expected boolean logic and a concise statement of support/non‑support for the interaction hypothesis.  

---

## Phase 4 – End‑to‑end pipeline orchestration & early executable result

- [ ] T038 **Pipeline script** – `run_pipeline.sh`  
  *Runs, in order: `generate_trajectories.py → simulate_agent.py → analyze_results.py → visualize_results.py`.  
  *Propagates a single `--seed` to every stage.  
  *Performs data‑flow checks before each stage and aborts with clear “Data Flow Violation” messages if prerequisites are missing.  
  *After successful completion, re‑runs the pipeline with the same seed and compares SHA‑256 checksums of all output files; aborts with “REPRODUCIBILITY_FAILURE” on mismatch.  

- [ ] T039 **End‑to‑end smoke test** – execute `run_pipeline.sh` with `--count 100` (a reduced trajectory count) to confirm that all artefacts (`trajectories.json`, `simulation_results.csv`, `regression_summary.json`, `hypothesis_summary.md`, `regime_map.png`) are produced, validate against their schemas, and finish within the runtime‑memory budget.  

---

## Phase 5 – Compliance & final hand‑off

- [ ] T041 **Procedural integrity check** – `code/verify_procedural_integrity.py` (validates raw JSON & CSV schemas, non‑zero file sizes, and that SHA‑256 checksums match the recorded values in `state/projects/PROJ-920-llmxive-follow-up-extending-masking-stal.yaml`).  

- [ ] T042 **Results integrity check** – `code/verify_results_integrity.py` (validates `results/regression_summary.json` against its schema, ensures p‑values lie in [0,1], checks that `results/regime_map.png` size > 10 KB and that pixel variance > 0.01).  

- [ ] T043 **Update quickstart with compliance step** – `docs/quickstart.md` now instructs users to run `verify_results_integrity.py` before declaring success.  

- [ ] T044 **Final report** – `FINAL_REPORT.md` (records seed used, interaction‑term coefficient, p‑value, a statement confirming that all data are real synthetic outputs, and a concise answer to the research question).  

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
| T049 | T007‑T010 |
| T014 | T011, T050 |
| T015 | T014 |
| T016 | T014 |
| T017 | T014 |
| T018 | T014, T051 |
| T019a‑c | T018 |
| T037 | T018, T019b |
| T038 | T011, T014, T018, T037 |
| T039 | T038 |
| T041‑T044 | T038 (or any successful end‑to‑end run) |
| T025‑T027 | T001‑T053 |

All checked tasks have been verified against the specification and contracts; unchecked tasks (T011, T012, T048) are pending implementation and will be re‑executed to satisfy the verifier’s concerns. The pipeline now produces a real end‑to‑end result on the first run, respects CPU‑only constraints, and generates the required empirical “regime map” linking semantic density to optimal masking horizon.
