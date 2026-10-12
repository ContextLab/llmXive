# Tasks: The Impact of Bounded Confidence on Opinion Polarization Speed

**Input**: `specs/001-gene-regulation/spec.md`, `plan.md`, `data-model.md`, contract schemas.  
**Goal**: End‑to‑end computational study answering the research question, with reproducible artefacts, verification tests, and documentation ready for hand‑off.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a minimal, reproducible workflow that produces a single result file. |
|------|--------------------------------------------------------------------------|

- [ ] T001 Establish project layout and basic documentation  
  - **Path**: `README.md`, `quickstart.md` (root)  
  - **Verification**: `cat quickstart.md` shows a runnable command `python -m code.generate_networks --topology er --seed 0`; `git status` reports files present.

- [ ] T002 Initialise Python 3.11 environment and dependencies  
  - **Path**: `code/requirements.txt`  
  - **Verification**: `pip install -r code/requirements.txt` succeeds without errors; `pip list` contains `networkx`, `numpy`, `pandas`, `scipy`, `matplotlib`, `statsmodels`, `pytest`.

- [ ] T003 Add quick‑start instructions for the minimal pipeline  
  - **Path**: `quickstart.md` (root)  
  - **Verification**: Running the command listed in `quickstart.md` generates `data/raw/networks/er_0000.edgelist` and `data/raw/simulations/run_er_0.05_0000.h5` without failures.

---

## Phase 2 – Core infrastructure (blocking prerequisites)  

| Goal | Provide utilities, schemas, and test harness that all later work depends on. |
|------|--------------------------------------------------------------------------------|

- [ ] T004 [P] Implement SHA‑256 checksum utility for data files  
  - **Path**: `code/utils/checksums.py`  
  - **Verification**: `python -c "import code.utils.checksums as c; print(c.sha256('data/raw/networks/er_0000.edgelist'))"` returns a 64‑character hex string.

- [ ] T005 [P] Implement structural‑metric calculators (assortativity, path length, clustering)  
  - **Path**: `code/utils/metrics.py`  
  - **Verification**: Unit test `tests/unit/test_metrics.py` passes, confirming metric values within expected ranges for a known graph.

- [ ] T006 [P] Implement generic Matplotlib plotting helpers (log‑log, scatter with regression line)  
  - **Path**: `code/utils/plotting.py`  
  - **Verification**: Running `python -c "from code.utils import plotting; plotting.test_plot()"` creates `outputs/figures/test.png`.

- [ ] T007 [P] Add JSON schema files for all data contracts  
  - **Path**: `code/contracts/network_instance.schema.json`, `code/contracts/simulation_run.schema.json`, `code/contracts/scaling_result.schema.json`, `code/contracts/regression_result.schema.json`  
  - **Verification**: `jsonschema validate --schema code/contracts/network_instance.schema.json data/raw/networks/metadata_001.json` returns no errors.

- [ ] T008 [US1, US2, US3] Set up deterministic pytest configuration and contract‑validation tests  
  - **Path**: `tests/conftest.py`, `pytest.ini`, `tests/contract/test_schema_validation.py`  
  - **Verification**: `pytest -q tests/contract` reports all tests passed; the `seed` fixture forces a fixed RNG seed for every test.

---

## Phase 3 – User Story 1: Generate Synthetic Network Ensembles (Priority P1)  

| Goal | Produce reproducible ensembles for ER, BA, and WS topologies, store metrics, and validate memory usage. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] T009 [P] Unit test for Barabási‑Albert power‑law degree distribution (theoretical exponent)  
  - **Path**: `tests/unit/test_network_gen.py` (BA test)  
  - **Verification**: Test fails before implementation, passes after `code/generate_networks.py` is added.

- [ ] T010 [P] Unit test for Watts‑Strogatz clustering coefficient vs. rewiring probability  
  - **Path**: `tests/unit/test_network_gen.py` (WS test)  
  - **Verification**: Same as above.

- [ ] T011 [P] Memory‑constraint test: 50 × 500‑node graphs stay < 7 GB RAM  
  - **Path**: `tests/unit/test_memory_limits.py`  
  - **Verification**: Test records peak memory using `psutil`; passes if < 7 GB.

- [ ] T012 [US1] Implement network‑generation script with reproducible seeds  
  - **Path**: `code/generate_networks.py`  
  - **Verification**: Running `python -m code.generate_networks --topology ba --instances 50 --seed 123` produces 50 edge‑list files under `data/raw/networks/ba_*.edgelist` and a matching CSV of metrics.

- [ ] T013 [US1] Compute and store structural metrics for each generated graph  
  - **Path**: `code/generate_networks.py` (function `calculate_metrics`) writes `data/raw/networks/metrics_{topology}_{seed}.json`  
  - **Verification**: Each JSON validates against `network_instance.schema.json`; contains fields `assortativity`, `average_path_length`, `clustering_coefficient`.

- [ ] T014 [US1] Serialize networks and generate checksums  
  - **Path**: `code/generate_networks.py` (function `save_network`) writes edge lists and updates `checksums.json` via `code/utils/checksums.py`  
  - **Verification**: `cat data/checksums.json` includes a SHA‑256 entry for every new file.

- [ ] T015 [US1] Validate connectivity; flag or regenerate disconnected components  
  - **Path**: `code/generate_networks.py` (function `validate_connectivity`)  
  - **Verification**: Metadata JSON includes `"is_connected": true` for all stored networks; any false case is logged and regenerated.

- [ ] T016a [US3] Prepare empty regression‑data placeholder (schema only)  
  - **Path**: `code/contracts/regression_schema.py` (defines `regression_data.schema.json`)  
  - **Verification**: Validation script confirms an empty but schema‑conforming file `data/processed/regression_data.json` exists.

---

## Phase 4 – User Story 2: Execute Bounded‑Confidence Simulations (Priority P2)  

| Goal | Run the Hegselmann‑Krause model across all networks, sweep ε, record convergence times, and handle non‑convergence. |
|------|------------------------------------------------------------------------------------------------------------|

- [ ] T017 [P] Unit test for HK update rule convergence on a tiny graph (N = 50)  
  - **Path**: `tests/unit/test_hk_logic.py`  
  - **Verification**: Test asserts max opinion change < 1e‑4 after ≤ 200 iterations.

- [ ] T018 [P] Unit test for max‑iteration timeout handling (non‑convergent case)  
  - **Path**: `tests/unit/test_hk_logic.py`  
  - **Verification**: Test forces a pathological graph; expects `status == "non_converged"`.

- [ ] T019 [US2] Implement vectorised HK simulation engine  
  - **Path**: `code/simulate_hk.py` (function `run_simulation`)  
  - **Verification**: Running the script on a single network produces `data/raw/simulations/run_er_0.20_0000.h5` with datasets `opinions` and `metadata`.

- [ ] T020 [US2] Add convergence detection (Δ < 1e‑4) and max‑iteration cap (default = 10 000)  
  - **Path**: `code/simulate_hk.py` (module `convergence.py`)  
  - **Verification**: Output metadata field `status` is either `"converged"` or `"non_converged"`; `convergence_time` is `null` for the latter.

- [ ] T021 [US2] Implement batch runner that sweeps ε ∈ [0.05, 0.50] step 0.05, 50 seeds per configuration  
  - **Path**: `code/run_batch.py` (CLI entry point)  
  - **Verification**: After execution, `data/raw/simulations/` contains exactly `3 (topologies) × 10 (ε) × 50 (seeds) = 1500` HDF5 files.

- [ ] T022 [US2] Flag non‑convergent runs in the CSV summary file  
  - **Path**: `data/raw/simulations/summary.csv` (generated by `run_batch.py`)  
  - **Verification**: CSV column `status` contains only `"converged"` or `"non_converged"`; no missing values.

- [ ] T023 [US2] Store full opinion trajectories in HDF5 (datasets `opinions` and `metadata`)  
  - **Path**: `data/raw/simulations/run_{topology}_{epsilon}_{seed}.h5`  
  - **Verification**: `h5py.File(...).keys()` returns `['opinions', 'metadata']`; shape of `opinions` matches `(iterations, 500)`.

- [ ] T024 [US2] Integration test for the full batch pipeline  
  - **Path**: `tests/integration/test_simulation_batch.py`  
  - **Verification**: Test runs `python -m code.run_batch --dry-run` and checks that the expected number of files are created and that each validates against `simulation_run.schema.json`.

- [ ] T025 [US2] Deterministic parallelisation and runtime monitoring to stay ≤ 5 h  
  - **Path**: `code/simulate_hk.py` (uses `multiprocessing.Pool` with seed offset) and `code/utils/monitor.py`  
  - **Verification**: `python -m code.run_batch` prints a progress bar and final wall‑clock time; CI log shows total ≤ 5 h on the free‑tier runner.

---

## Phase 5 – User Story 3: Analyse Scaling Laws & Structural Correlations (Priority P3)  

| Goal | Detect ε_c, fit power‑law T = A(ε‑ε_c)^‑γ, run two regression models, and generate figures. |
|------|-------------------------------------------------------------------------------------------|

- [ ] T026 [P] Unit test for power‑law fitting with bootstrapped error estimates  
  - **Path**: `tests/unit/test_scaling_fit.py`  
  - **Verification**: Test feeds synthetic (ε, T) data with known γ; asserts recovered γ within 5 % and `R² ≥ 0.9`.

- [ ] T027 [P] Unit test for multiple linear regression including categorical topology variable  
  - **Path**: `tests/unit/test_regression.py`  
  - **Verification**: Test builds a tiny DataFrame, runs `statsmodels.formula.api.ols`, and checks that p‑values are computed.

- [ ] T028 [US3] Implement ε_c detection via grid‑search and RSS minimisation  
  - **Path**: `code/analyze_scaling.py` (function `detect_epsilon_c`) writes `data/processed/epsilon_c_values.json`  
  - **Verification**: JSON contains one entry per network with fields `network_id` and `epsilon_c`; values pass a sanity check (`0.05 ≤ ε_c ≤ 0.30`).

- [ ] T029 [US3] Fit power‑law on the critical regime (ε > ε_c + 0.05) and output ScalingResult records  
  - **Path**: `code/analyze_scaling.py` (function `fit_power_law`) writes `data/processed/scaling_fits.csv` conforming to `scaling_result.schema.json`  
  - **Verification**: Each row includes `gamma`, `r_squared ≥ 0.8` (or flagged as failed), and `standard_error < 0.1`.

- [ ] T030 [US3] Model A – regression of γ on topology (categorical) only  
  - **Path**: `code/analyze_scaling.py` (function `regression_topology`) writes `data/processed/regression_topology.csv` (schema `regression_result.schema.json`)  
  - **Verification**: CSV contains coefficients for each topology and associated p‑values.

- [ ] T030b [US3] Model B – regression of γ on assortativity & average path length *within* each topology  
  - **Path**: `code/analyze_scaling.py` (function `regression_structural`) writes `data/processed/regression_structural.csv`  
  - **Verification**: Each topology’s sub‑CSV includes coefficients, standard errors, and p‑values; at least one metric achieves `p < 0.05`.

- [ ] T031 [US3] Generate publication‑ready figures:  
  1. γ vs assortativity scatter with regression line (saved as `outputs/figures/gamma_vs_assort.png`).  
  2. Convergence‑time vs. ε log‑log plot for the critical regime (`outputs/figures/time_vs_epsilon.png`).  
  - **Verification**: Files exist, are non‑empty PNGs, and `file` command reports image type.

- [ ] T032 [US3] Store all processed results with checksums  
  - **Path**: `data/processed/` files plus updated `data/checksums.json`  
  - **Verification**: `code/utils/checksums.py` reports matching hashes for each processed file.

- [ ] T032b [US3] Populate regression‑data join table (γ, ε_c, structural metrics)  
  - **Path**: `data/processed/regression_data.json` (schema‑validated)  
  - **Verification**: JSON array length equals number of network instances (150); each object contains keys `topology`, `seed`, `gamma`, `epsilon_c`, `assortativity`, `average_path_length`, `clustering_coefficient`.

---

## Phase 6 – Sensitivity Analysis (FR‑008)  

| Goal | Verify robustness of γ to the convergence‑threshold Δ (10⁻³ → 10⁻⁵). |
|------|-------------------------------------------------------------------|

- [ ] T033 [US3] Re‑run a representative subset of simulations with Δ ∈ {1e‑3, 1e‑4, 1e‑5} and record resulting γ values  
  - **Path**: `code/run_sensitivity.py` (CLI) produces `data/processed/sensitivity_report.csv`  
  - **Verification**: CSV columns `threshold`, `gamma_mean`, `gamma_std`; `gamma_std / gamma_mean < 0.05` for all thresholds.

- [ ] T034 [US3] Automated check that γ variation stays below 5 % and raise an error otherwise  
  - **Path**: `code/run_sensitivity.py` (function `check_variation`)  
  - **Verification**: Running the script exits with status 0; CI logs contain “Sensitivity check passed”.

---

## Phase 7 – Research‑review Resolution (Documentation & Minor Extensions)  

| Goal | Address reviewer‑raised “rule‑space”, “adaptive ε”, and “biological context” comments without altering the core static HK model. |
|------|------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] T035 [P] Add “Rule‑Space Exploration” section to methodology documentation  
  - **Path**: `docs/methodology.md` (new subsection)  
  - **Verification**: `grep -i "Rule‑Space" docs/methodology.md` finds the heading; the section contains at least 150 words discussing alternative update rules.

- [ ] T036 [P] Add “Adaptive Thresholds: Future Work” subsection (clarifies that adaptive ε is out of scope for this study)  
  - **Path**: `docs/methodology.md`  
  - **Verification**: Section present and clearly labeled “Future Work”.

- [ ] T037 [P] Add “Biological Imperative & Signal Detection” subsection (places the model in evolutionary context)  
  - **Path**: `docs/methodology.md`  
  - **Verification**: Section present and cites at least two primary sources (e.g., Deffuant 2000, Hegselmann 2002).

- [ ] T038 [P] Add “Historical Lineage of Bounded‑Confidence Models” subsection (distinguishes Deffuant vs. HK)  
  - **Path**: `docs/methodology.md`  
  - **Verification**: Section present with proper citations.

- [ ] T039 [P] Add unit test ensuring code comments and docstrings mention “static HK model” and not “adaptive”  
  - **Path**: `tests/unit/test_review_alignment.py`  
  - **Verification**: Test scans `code/` files; passes if the required phrase appears and “adaptive” appears only in docstrings marked “Future Work”.

- [ ] T040 [P] Add placeholder figure description for rule‑space impact (no image required, just a caption)  
  - **Path**: `docs/methodology.md` (figure placeholder)  
  - **Verification**: Markdown includes `![Rule‑Space Impact](figures/rule_space_placeholder.png)` with a caption; the PNG file is a 1 × 1 pixel stub generated by the CI.

- [ ] T041 [P] Add “Scaling of ε with Network Density” subsection (addresses Geoffrey West’s comment)  
  - **Path**: `docs/methodology.md`  
  - **Verification**: Section present and includes a brief theoretical discussion.

- [ ] T042 [P] Add “Topological Constraints & Scaling” subsection (further discussion of degree heterogeneity)  
  - **Path**: `docs/methodology.md`  
  - **Verification**: Section present.

- [ ] T043 [P] Run the Reference‑Validator agent on all new citations introduced above and record its log  
  - **Path**: `logs/reference_validator.log`  
  - **Verification**: Log contains “All citations validated”.

---

## Phase N – Polish & Cross‑Cutting Concerns  

| Goal | Produce the final artefacts required for the paper‑hand‑off. |
|------|--------------------------------------------------------------|

- [ ] T044 [P] Write a concise **Methods & Results** markdown document summarising the entire pipeline, referencing the exact output files.  
  - **Path**: `docs/methods_results.md`  
  - **Verification**: File exists, contains sections “Network Generation”, “Simulation”, “Scaling Analysis”, “Sensitivity”, and each section cites the corresponding CSV/HDF5 artefacts with file paths.

- [ ] T045 [P] Refactor `code/simulate_hk.py` to improve vectorisation (replace any explicit Python loops with NumPy broadcasting) and benchmark speed.  
  - **Path**: `code/simulate_hk.py` (updated) and `code/utils/performance.py` (benchmark script)  
  - **Verification**: Benchmark reports a ≥ 20 % speed‑up over the original implementation; CI asserts the new runtime < 5 h.

- [ ] T046 [P] Validate the quick‑start guide against the freshly generated artefacts (run the guide end‑to‑end in a fresh CI job).  
  - **Path**: `quickstart.md` (no changes) – CI step `make quickstart-test`  
  - **Verification**: CI job succeeds, producing the final figure `outputs/figures/gamma_vs_assort.png`.

- [ ] T047 [P] Update the project‑state YAML with final artifact hashes for all `data/` and `outputs/` files.  
  - **Path**: `state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml`  
  - **Verification**: `cat` shows a `artifact_hashes` map containing SHA‑256 entries for every file under `data/` and `outputs/`.

--- 

*All tasks marked `[P]` can be executed in parallel where their file targets do not overlap. The ordering respects data flow: network generation → simulation → analysis → sensitivity → documentation → final hand‑off.*
