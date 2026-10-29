# Tasks: The Impact of Bounded Confidence on Opinion Polarization Speed

**Input**: `specs/001-gene-regulation/spec.md`, `plan.md`, `data-model.md`, contract schemas.  
**Goal**: End‑to‑end computational study answering the research question, with reproducible artefacts, verification tests, and documentation ready for hand‑off.

---

## Phase 1 – Project scaffolding & first end‑to‑end run  

| Goal | Provide a minimal, runnable pipeline that produces a single network file and a corresponding simulation result. |
|------|-----------------------------------------------------------------------------------------------|

- [~] T001 [P] **Create project documentation** – add `README.md` and `quickstart.md` at the repository root.  
  - **File(s)**: `README.md`, `quickstart.md`  
  - **Verification**: `quickstart.md` contains the command `python -m code.generate_networks --topology ER --instances 1 --seed 0`. Running the command creates `data/raw/networks/ER_0000.edgelist` and `data/raw/networks/metadata_ER_0000.json` without errors.

- [X] T002 [P] **Pin Python 3.11 dependencies** – write `code/requirements.txt` with all required packages (`networkx`, `numpy`, `pandas`, `scipy`, `matplotlib`, `statsmodels`, `h5py`, `pytest`).  
  - **File**: `code/requirements.txt`  
  - **Verification**: `pip install -r code/requirements.txt` exits with status 0 and `pip list` shows the listed packages.

---

## Phase 2 – Core utilities & verification framework  

| Goal | Supply reusable building blocks (checksums, metrics, plots) and a deterministic test harness. |
|------|----------------------------------------------------------------------------------------------|

- [~] T003 [P] **Implement core utility modules** – `code/utils/checksums.py` (SHA‑256 for any file), `code/utils/metrics.py` (assortativity, average path length, clustering), `code/utils/plotting.py` (log‑log and scatter helpers).  
  - **Files**: `code/utils/checksums.py`, `code/utils/metrics.py`, `code/utils/plotting.py`  
  - **Verification**: Each module has a corresponding unit test in `tests/unit/` that passes; e.g. `python -c "import code.utils.checksums as c; print(len(c.sha256('README.md')))"` prints 64.

- [~] T004 [P] **Add JSON schema files & pytest configuration** – place contract schemas under `code/contracts/` (`network_instance.schema.json`, `simulation_run.schema.json`, `scaling_result.schema.json`, `regression_result.schema.json`) and create `tests/conftest.py` + `pytest.ini` that enforce a fixed RNG seed for every test.  
  - **Files**: `code/contracts/*.json`, `tests/conftest.py`, `pytest.ini`  
  - **Verification**: `jsonschema validate --schema code/contracts/network_instance.schema.json data/raw/networks/metadata_ER_0000.json` yields no errors; `pytest -q tests` reports all tests passed and the seed fixture is active.

---

## Phase 3 – Synthetic network ensembles (User Story 1)  

| Goal | Produce reproducible ensembles for ER, BA, and WS topologies, store metrics, and confirm memory limits. |
|------|-----------------------------------------------------------------------------------------------|

- [~] T005 [US1] **Generate 50 reproducible networks per topology** – `code/generate_networks.py` accepts `--topology {ER,BA,WS}`, `--instances 50`, `--seed <int>`. It writes edge‑list files to `data/raw/networks/{topology}_{idx}.edgelist` and a CSV `data/raw/networks/{topology}_metadata.csv` with one row per instance.
  - **File**: `code/generate_networks.py`  
  - **Verification**: After execution, each topology folder (`data/raw/networks/ER/`, `.../BA/`, `.../WS/`) contains exactly 50 `.edgelist` files and the CSV validates against `network_instance.schema.json`. **Additionally**, each generated network is checked to have `node_count == 500`.

- [~] T006 [US1] **Compute & store structural metrics** – the generation script calls `code/utils/metrics.py` and writes a JSON metadata file per network (`data/raw/networks/metadata_{topology}_{idx}.json`). Each JSON conforms to `network_instance.schema.json`.  
  - **File**: `code/generate_networks.py` (metrics section)  
  - **Verification**: `jsonschema validate --schema code/contracts/network_instance.schema.json data/raw/networks/metadata_BA_0001.json` passes **and** the `node_count` field equals 500.

- [~] T007 [US1] **Memory‑usage test for batch generation** – `tests/unit/test_memory_limits.py` uses `psutil` to monitor peak RAM while generating 50 × 500‑node graphs; it asserts peak < 7 GB.  
  - **File**: `tests/unit/test_memory_limits.py`  
  - **Verification**: Unit test passes on the CI runner.

---

## Phase 4 – Bounded‑confidence simulations (User Story 2)  

| Goal | Run the Hegselmann‑Krause model across all networks, sweep ε, record convergence times, and handle non‑convergence. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] T008 [US2] **Implement HK update rule & convergence detector** – `code/simulate_hk.py` provides `run_simulation(network, epsilon, seed, max_iter=10000, tol=1e-4)` and returns a dict with `convergence_time`, `status`, `final_clusters`.   <!-- FAILED-IN-EXECUTION: code/simulate_hk.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/simulate_hk.py exit=2 --> <!-- FAILED-IN-EXECUTION: code/simulate_hk.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/simulate_hk.py exit=2 -->
  - **File**: `code/simulate_hk.py` (plus `code/utils/convergence.py`)  
  - **Verification**: Unit test `tests/unit/test_hk_logic.py` on a 50‑node random graph asserts:
    1. `status == "converged"` and `convergence_time <= 200` when ε=0.2;
    2. **All opinion updates respect** the confidence bound |x_i‑x_j| ≤ ε;
    3. **Convergence is declared only** when max opinion change < 1e‑4;
    4. **When `max_iter` is exceeded** the run returns `status == "non_converged"` (see T022).

- [ ] T009 [US2] **Batch runner for ε‑sweep & seeds** – `code/run_batch.py` iterates over `ε ∈ [0.05,0.50]` step 0.05 and 50 seeds per configuration, invoking `simulate_hk`. Results are stored as HDF5 files `data/raw/simulations/run_{topology}_{epsilon}_{seed}.h5` (datasets `opinions` and `metadata`). A summary CSV `data/raw/simulations/summary.csv` records `run_id, network_id, epsilon, seed, convergence_time, status, final_clusters`.   <!-- FAILED-IN-EXECUTION: code/run_batch.py exit=2 -->
  - **File**: `code/run_batch.py`  
  - **Verification**: After a dry‑run, `summary.csv` contains exactly `3 × 10 × 50 = 1500` rows; each HDF5 file opens with `h5py` and contains the expected datasets.

- [ ] T010 [US2] **Integration test for the full simulation pipeline** – `tests/integration/test_simulation_batch.py` executes `python -m code.run_batch --dry-run` and checks file counts, schema compliance of `summary.csv`, that no `status` field is missing, **and** that total wall‑clock time reported by T021 is ≤ 5 h.  
  - **File**: `tests/integration/test_simulation_batch.py`  
  - **Verification**: Integration test passes on a fresh CI run.

- [ ] T021 [US2] **Timing benchmark for full simulation suite** – `code/run_timing.py` wraps the full batch execution, records start/end timestamps, and asserts the elapsed wall‑clock time does not exceed 5 hours (18 000 seconds). It writes a small JSON report `data/checksums/timing_report.json`.  
  - **File**: `code/run_timing.py` and `data/checksums/timing_report.json`  
  - **Verification**: The script exits with status 0 only if runtime ≤ 5 h; otherwise it fails the CI.

- [ ] T022 [US2] **Unit test for max‑iteration limit enforcement** – `tests/unit/test_max_iter_enforcement.py` calls `run_simulation` with a deliberately low `max_iter` (e.g., 5) on a network where convergence requires > 5 iterations, and asserts that `status == "non_converged"` and `convergence_time` is `null`.  
  - **File**: `tests/unit/test_max_iter_enforcement.py`  
  - **Verification**: Test passes, confirming FR‑007 is enforced.

---

## Phase 5 – Scaling analysis & structural correlations (User Story 3)  

| Goal | Detect ε_c, fit power‑law models, run regressions, and produce figures. |
|------|--------------------------------------------------------------------------------|

- [ ] T011 [US3] **Detect critical threshold ε_c via grid‑search** – `code/analyze_scaling.py` implements `detect_epsilon_c(network_id, epsilons, convergence_times)` using RSS minimisation. Results are written to `data/processed/epsilon_c_values.json` (one entry per network).  
  - **File**: `code/analyze_scaling.py` (ε_c detection)  
  - **Verification**: JSON contains `network_id` and `epsilon_c` fields; all `epsilon_c` lie in the interval `[0.05, 0.30]`.

- [ ] T012 [US3] **Fit power‑law on the critical regime** – the same module fits `T = A (ε‑ε_c)^{-γ}` for `ε > ε_c + 0.05`. Results are written to `data/processed/scaling_fits.csv` conforming to `scaling_result.schema.json`. Rows include `gamma`, `r_squared` (≥ 0.8 for successful fits) and `standard_error` (< 0.1). **Post‑fit validation** counts how many topology types achieve `r_squared ≥ 0.8` and fails if fewer than two meet this threshold (SC‑001).  
  - **File**: `code/analyze_scaling.py` (fit routine)  
  - **Verification**: `csvlook data/processed/scaling_fits.csv` shows required columns; a schema validator reports no errors; the additional count check enforces SC‑001.

- [ ] T013 [US3] **Run regression models** – two functions in `code/analyze_scaling.py`: `regression_topology()` (Model A: γ ~ topology) and `regression_structural()` (Model B: γ ~ assortativity + average_path_length within each topology). Outputs are `data/processed/regression_topology.csv` and `data/processed/regression_structural_{topology}.csv`, each validated against `regression_result.schema.json`. At least one metric achieves `p < 0.05`.  
  - **File**: `code/analyze_scaling.py` (regression section)  
  - **Verification**: CSVs contain `metric_name, coefficient, std_error, t_statistic, p_value, model_r_squared`; a quick‑look confirms a significant p‑value.

- [ ] T014 [US3] **Generate publication‑ready figures** – `code/utils/plotting.py` is used by `code/analyze_scaling.py` to produce:  
  1. `outputs/figures/gamma_vs_assort.png` (scatter of γ vs. assortativity with regression line).  
  2. `outputs/figures/time_vs_epsilon.png` (log‑log plot of convergence time vs. ε for the critical regime).  
  - **File**: `outputs/figures/` (PNG files)  
  - **Verification**: `file outputs/figures/*.png` reports “PNG image data”; both files are non‑empty (> 1 KB).

- [ ] T015 [US3] **Checksum processed artefacts** – run `code/utils/checksums.py` over all files in `data/processed/` and `outputs/figures/`, updating `data/checksums.json`.  
  - **File**: `data/checksums.json`  
  - **Verification**: `cat data/checksums.json` includes a SHA‑256 entry for each processed CSV/JSON/PNG; a validation script confirms the stored hash matches the current file.

---

## Phase 6 – Sensitivity analysis (FR‑008)  

| Goal | Verify robustness of γ to the convergence‑threshold Δ. |
|------|-------------------------------------------------------|

- [ ] T016 [US3] **Run sensitivity sweep for Δ ∈ {1e‑3, 1e‑4, 1e‑5}** – `code/run_sensitivity.py` re‑executes the fitting pipeline on a representative subset (10 % of networks) for each Δ, writing `data/processed/sensitivity_report.csv` with columns `threshold, gamma_mean, gamma_std, variation_percent`.  
  - **File**: `code/run_sensitivity.py` & `data/processed/sensitivity_report.csv`  
  - **Verification**: All rows satisfy `variation_percent < 5.0`; the script exits with status 0.

---

## Phase 7 – Documentation & research‑review resolution  

| Goal | Produce verifiable written artefacts that summarise methods, results, and address reviewer comments. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] T017 [P] **Write Methods & Results markdown** – create `docs/methods_results.md` containing clearly titled sections: *Network Generation*, *Simulation*, *Scaling Analysis*, *Sensitivity*, *Regression Results*, each referencing the exact file paths of the generated CSV/JSON/PNG artefacts.  
  - **File**: `docs/methods_results.md`  
  - **Verification**: `grep -i "data/raw" docs/methods_results.md` returns at least three matches; the file is non‑empty and committed.

- [ ] T018 [P] **Add reviewer‑response methodology notes** – extend `docs/methodology.md` with the required subsections: “Rule‑Space Exploration”, “Adaptive Thresholds: Future Work”, “Biological Imperative & Signal Detection”, “Historical Lineage of Bounded‑Confidence Models”, “Scaling of ε with Network Density”, and “Topological Constraints & Scaling”. Each subsection is ≥ 150 words and cites at least two primary sources.  
  - **File**: `docs/methodology.md`  
  - **Verification**: Each heading appears (`grep -i "Rule‑Space" docs/methodology.md`) and the file size > 5 KB.

- [ ] T019 [P] **Add unit test ensuring code does not contain adaptive HK logic** – `tests/unit/test_review_alignment.py` scans all `code/` files for prohibited keywords such as “adaptive”. It also verifies that the phrase “static HK model” appears in comments/docstrings. The test fails if any prohibited keyword is found.  
  - **File**: `tests/unit/test_review_alignment.py`  
  - **Verification**: Test passes; `pytest -q tests/unit/test_review_alignment.py` reports success.

- [ ] T023 [P] **Harmonize topology enum casing** – update all scripts under `code/` to use upper‑case topology identifiers (`ER`, `BA`, `WS`) consistently, and adjust any downstream references (e.g., CSV headers, metadata fields) to match the enums defined in `network_metrics.schema.yaml`.  
  - **File**: (multiple code files; task records the change)  
  - **Verification**: Schema validation of generated metadata passes without enum‑casing errors.

---

## Phase 8 – Final hand‑off  

| Goal | Produce the final artefact manifest for the paper‑stage pipeline. |
|------|-------------------------------------------------------------------|

- [ ] T020 [P] **Update project‑state YAML with final artifact hashes** – write `state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml` containing an `artifact_hashes` map that lists SHA‑256 hashes for every file under `data/`, `outputs/`, and `docs/`.  
  - **File**: `state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml`  
  - **Verification**: `yq '.artifact_hashes | length' state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml` equals the total number of tracked artefacts; a CI step confirms the map matches `data/checksums.json`.

--- 

*All tasks are ordered to respect data flow: utilities → network generation → simulation → analysis → sensitivity → documentation → final hand‑off.  Each unchecked box represents a pending, verifiable work item; completed tasks will be checked once the corresponding artefact exists and passes its verification step.*  