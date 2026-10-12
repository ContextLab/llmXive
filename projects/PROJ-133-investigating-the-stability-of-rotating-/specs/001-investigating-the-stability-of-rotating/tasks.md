# Tasks: Investigating the Stability of Rotating Bose‑Einstein Condensates with Dipolar Interactions  

**Input**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, and reviewer feedback.  

**Goal**: Produce a fully reproducible end‑to‑end study that (1) runs the time‑dependent Gross‑Pitaevskii solver on a 64 × 64 grid for the full Ω × ε₍dd₎ scan, (2) detects vortices, (3) computes stability metrics, (4) performs a Two‑Way ANOVA + Dunnett post‑hoc, (5) generates phase‑map visualisations, and (6) delivers complete documentation and quality‑assurance artefacts.  

Tasks are written in the canonical checklist format.  Checked boxes (`[X]`) indicate work that has already been verified; unchecked boxes (`[ ]`) are pending and must produce a real file that can be inspected by the verifier.

---

## Phase 1 – Project scaffolding (must exist before any scientific code runs)

- [ ] **T001** [P] Create the core source tree under `code/` with sub‑packages required by the specification.  
  - **Paths**: `code/`, `code/simulation/`, `code/analysis/`, `code/statistics/`, `code/viz/`, `code/utils/`  
  - **Verification**: `tree -L 2 code/` must list all six sub‑directories; a CI test `tests/contract/test_code_tree.py` asserts their existence.

- [ ] **T002** [P] Create the data hierarchy that stores raw snapshots, processed metrics, and aggregated results.  
  - **Paths**: `data/raw/`, `data/processed/`, `data/aggregated/`  
  - **Verification**: `tree -L 2 data/` must show the three sub‑folders; a contract test validates that each folder contains at least one file after the first run.

- [ ] **T003** [P] Create the test hierarchy required for unit, contract, and integration verification.  
  - **Paths**: `tests/unit/`, `tests/contract/`, `tests/integration/`  
  - **Verification**: `tree -L 2 tests/` must list the three directories; `pytest -q` must discover at least one test in each sub‑folder.

- [ ] **T004** [P] Add linting and formatting configuration so the project adheres to the platform’s style standards.  
  - **Files**: `.ruff.toml`, `pyproject.toml` (black section), `.pre‑commit‑config.yaml`  
  - **Verification**: `ruff check .` returns exit‑code 0; `black --check .` returns exit‑code 0; `pre‑commit run --all-files` passes.

---

## Phase 2 – Core scientific implementation (blocking prerequisites for the user stories)

- [ ] **T005** [P] Implement deterministic random‑seed management in `code/utils/seed_manager.py`.  
  - **Verification**: `tests/unit/test_seed_manager.py` confirms that `set_seed(42)` yields reproducible NumPy and Python RNG states.

- [ ] **T006** [P] Implement the split‑step Fourier Gross‑Pitaevskii solver with dipolar term in `code/simulation/gpe_solver.py`.  
  - **Requirement**: Supports conditional grid size – 64 × 64 when `RUN_FULL_GRID=true`, otherwise 256 × 256 (FR‑001).  
  - **Verification**: `tests/unit/test_gpe_solver.py` checks norm preservation and correct handling of the `grid_size` argument.

- [ ] **T007** [P] Implement the batch runner in `code/simulation/runner.py` that iterates over the full (Ω, ε₍dd₎, N) grid, writes each run’s metadata to `data/raw/<run_id>_meta.json` and snapshots to `data/raw/<run_id>_dens.npy` / `..._phase.npy`.  
  - **Verification**: Integration test `tests/integration/test_full_grid.py` confirms that ~300 runs complete within the 6 h CI wall‑time limit and that each run produces a `status` field.

- [ ] **T008** [P] Implement phase‑winding vortex detection in `code/analysis/vortex_detector.py` (FR‑003).  
  - **Verification**: Unit test `tests/unit/test_vortex_detector.py` validates detection on a synthetic single‑vortex field and on a vortex‑antivortex pair.

- [ ] **T009** [P] Implement stability‑metric calculation (vortex density, radial variance, structure‑factor sharpness) in `code/analysis/metrics.py` (FR‑004).  
  - **Verification**: Contract test `tests/contract/test_metrics_schema.py` checks each row against `stability_metric.schema.yaml`.

- [ ] **T010** [P] Implement metastability classification and the required sensitivity analysis (FR‑006, SC‑002).  
  - **File**: `code/analysis/metastability.py` writes `data/processed/metastability_report.csv` containing columns `run_id`, `instability_classified`, `false_positive_rate`, `false_negative_rate`.  
  - **Verification**: `tests/unit/test_metastability.py` asserts that (i) any run with > 30 % density drop or vortex‑density > threshold is flagged, and (ii) the script correctly computes FP/FN rates across a controlled synthetic set.

- [ ] **T011** [P] Perform Two‑Way ANOVA (Ω × ε₍dd₎) and Dunnett’s post‑hoc test in `code/statistics/aggregators.py`, outputting `data/aggregated/statistical_results.json` conforming to `statistical_aggregation.schema.yaml` (FR‑005).  
  - **Verification**: Unit test `tests/unit/test_two_way_anova.py` checks that the JSON contains `p_value_anova_interaction` and `p_value_dunnett` formatted to ≥ 4 dp.

- [ ] **T012** [P] Generate contour phase‑maps and representative density/phase figures in `code/viz/plotter.py`; write PNGs to `figures/phase_map.png`, `figures/stable_example.png`, `figures/metastable_example.png`, `figures/unstable_example.png` (US‑3).  
  - **Verification**: Integration test `tests/integration/test_plotting.py` confirms that each PNG file is created and that the colour‑scale matches the underlying `mean_vortex_density` values.

---

## Phase 3 – Validation, reproducibility & hand‑off

- [ ] **T013** [P] Run the full 64 × 64 grid scan (`RUN_FULL_GRID=true`) on the CI runner, then re‑run the selected verification subset at 256 × 256. Store the performance log in `data/processed/performance_log.txt`.  
  - **Verification**: `tests/integration/test_performance.py` parses the log and asserts runtime ≤ 6 h and peak memory ≤ 14 GB.

- [ ] **T014** [P] Validate that the statistical pipeline correctly handles the “zero initial vortex” edge case without division‑by‑zero errors.  
  - **File**: `tests/unit/test_zero_vortex_stats.py` (already present).  
  - **Verification**: Test must pass on the real aggregated JSON.

---

## Phase 4 – Documentation, quality & reviewer‑response artefacts

- [ ] **T015** [P] Write a top‑level `README.md` that (a) describes the scientific question, (b) lists required dependencies, (c) provides a single‑command quick‑start example (`python -m code.simulation.runner --grid 64 --full`), and (d) points to the generated figures in `figures/`.  
  - **Verification**: CI step `markdownlint` runs with no errors; a custom test `tests/contract/test_readme.py` checks for the presence of the quick‑start command string.

- [ ] **T016** [P] Add comprehensive NumPy‑style docstrings to **all public functions and classes** in the `code/` package (including `gpe_solver.py`, `runner.py`, `vortex_detector.py`, `metrics.py`, `aggregators.py`, `plotter.py`).  
  - **Verification**: `pydocstyle code/` must report zero violations; a contract test `tests/contract/test_docstrings.py` asserts that each public object has a non‑empty `__doc__`.

- [ ] **T017** [P] Create a `quickstart.md` inside `specs/001-investigating-the-stability-of-rotating/` that reproduces the entire end‑to‑end workflow in three commands (environment setup, full‑grid run, figure generation).  
  - **Verification**: The file must exist and contain the exact three‑command snippet; a test `tests/contract/test_quickstart.py` parses the file and verifies the commands are syntactically valid.

- [ ] **T018** [P] Update `spec.md` to replace the invalid statistical requirements (one‑sample t‑test, vortex‑number retention fraction) with the corrected Two‑Way ANOVA and Vortex Density metric, and to reference the new section numbers where the changes appear.  
  - **Verification**: A diff‑check script `scripts/verify_spec_update.py` confirms that the old FR‑005 text no longer appears and that the new wording matches the plan.

---

### Dependency matrix (for reviewer reference)

| Task | Depends on |
|------|------------|
| T001–T004 | – |
| T005 | – |
| T006 | T001, T005 |
| T007 | T001, T002, T005, T006 |
| T008 | T001, T005 |
| T009 | T008 |
| T010 | T009 |
| T011 | T009, T010 |
| T012 | T011 |
| T013 | T007, T011 |
| T014 | T011 |
| T015 | T001–T012 |
| T016 | T001–T012 |
| T017 | T001–T012 |
| T018 | T005–T012 (to ensure spec matches implementation) |

---  

*All unchecked tasks must produce real files or executable scripts that can be inspected by the platform’s verifier.  Checked tasks have already passed their respective verification suites.*
