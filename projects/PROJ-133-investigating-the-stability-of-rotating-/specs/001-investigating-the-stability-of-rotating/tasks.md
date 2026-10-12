# Tasks: Investigating the Stability of Rotating Bose‑Einstein Condensates with Dipolar Interactions  

**Input**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, and reviewer feedback.  

**Goal**: Deliver a fully reproducible end‑to‑end study that (1) runs the time‑dependent Gross‑Pitaevskii solver on a 64 × 64 grid for the full Ω × ε₍dd₎ scan, (2) detects vortices, (3) computes stability metrics, (4) performs a Two‑Way ANOVA + Dunnett post‑hoc, (5) generates phase‑map visualisations, (6) provides complete documentation, and (7) updates the specification so that the scientific requirements are consistent with the implementation.

---

## Phase 1 – Project scaffolding (must exist before any scientific code runs)

- [ ] **T001** [P] Create the core source tree under `code/` with the sub‑packages required by the specification.  
  - **Paths**: `code/`, `code/simulation/`, `code/analysis/`, `code/statistics/`, `code/viz/`, `code/utils/`  
  - **Verification**: `tree -L 2 code/` must list exactly the six directories; a contract test `tests/contract/test_code_tree.py` asserts their existence.

- [ ] **T002** [P] Create the data hierarchy that stores raw snapshots, processed metrics, and aggregated results.  
  - **Paths**: `data/raw/`, `data/processed/`, `data/aggregated/`  
  - **Verification**: `tree -L 2 data/` must show the three sub‑folders; `tests/contract/test_data_tree.py` checks that each folder contains at least one file after the first run.

- [X] **T003** [P] Create the test hierarchy required for unit, contract, and integration verification.  
  - **Paths**: `tests/unit/`, `tests/contract/`, `tests/integration/`  
  - **Verification**: `tree -L 2 tests/` must list the three directories; `pytest -q` must discover at least one test in each sub‑folder.

- [ ] **T004** [P] Add linting and formatting configuration so the project adheres to the platform’s style standards.  
  - **Files**: `.ruff.toml`, `pyproject.toml` (black section), `.pre-commit-config.yaml`  
  - **Verification**: `ruff check .` returns exit‑code 0; `black --check .` returns exit‑code 0; `pre‑commit run --all-files` passes; a CI step `tests/contract/test_lint_config.py` confirms the files exist.

- [ ] **T005** [P] Write a top‑level `README.md` that (a) describes the scientific question, (b) lists required dependencies, (c) provides a single‑command quick‑start example, and (d) points to the generated figures in `figures/`.  
  - **File**: `README.md`  
  - **Verification**: `markdownlint` passes with no errors; `tests/contract/test_readme.py` checks for the presence of the quick‑start command string.

- [ ] **T006** [P] Add comprehensive NumPy‑style docstrings to **all public functions and classes** in the `code/` package (including `gpe_solver.py`, `runner.py`, `vortex_detector.py`, `metrics.py`, `aggregators.py`, `plotter.py`).  
  - **Verification**: `pydocstyle code/` reports zero violations; `tests/contract/test_docstrings.py` asserts that each public object has a non‑empty `__doc__`.

- [ ] **T007** [P] Create a `quickstart.md` inside `specs/001-investigating-the-stability-of-rotating/` that reproduces the entire workflow in three commands (environment setup, full‑grid run, figure generation).  
  - **File**: `specs/001-investigating-the-stability-of-rotating/quickstart.md`  
  - **Verification**: The file exists and contains exactly three shell‑command lines; `tests/contract/test_quickstart.py` parses the file and validates the syntax of each command.

- [ ] **T008** [P] Update `spec.md` to replace the invalid statistical requirements (one‑sample t‑test, vortex‑number retention fraction) with the corrected Two‑Way ANOVA and Vortex‑Density metric, and to reference the new section numbers where the changes appear.  
  - **File**: `specs/001-investigating-the-stability-of-rotating/spec.md`  
  - **Verification**: `scripts/verify_spec_update.py` confirms that the old FR‑005 text is absent and that the new wording matches the plan; a contract test `tests/contract/test_spec_consistency.py` ensures the spec now mentions Two‑Way ANOVA and Vortex Density.

---

## Phase 2 – Core scientific implementation (blocking prerequisites for the user stories)

- [ ] **T009** [P] Implement deterministic random‑seed management in `code/utils/seed_manager.py`.  
  - **Verification**: `tests/unit/test_seed_manager.py` confirms that `set_seed(42)` yields reproducible NumPy and Python RNG states.

- [ ] **T010** [P] Implement the split‑step Fourier Gross‑Pitaevskii solver with dipolar term in `code/simulation/gpe_solver.py`.  
  - **Requirement**: Supports conditional grid size – 64 × 64 when `RUN_FULL_GRID=true`, otherwise 256 × 256 (FR‑001).  
  - **Note**: Initial conditions are supplied by task **T010a**.  
  - **Verification**: `tests/unit/test_gpe_solver.py` checks norm preservation, correct handling of the `grid_size` argument, and that dipolar contributions are included.

- [ ] **T010a** [P] Generate and validate Thomas‑Fermi initial conditions in `code/simulation/initial_conditions.py`.  
  - **Verification**: `tests/unit/test_initial_conditions.py` asserts that the density profile matches the analytical Thomas‑Fermi shape for given parameters and that the phase imprint for rotation is correctly applied.

- [ ] **T011** [P] Implement the batch runner in `code/simulation/runner.py` that iterates over the full (Ω, ε₍dd₎, N) grid, writes each run’s metadata to `data/raw/<run_id>_meta.json` and snapshots to `data/raw/<run_id>_dens.npy` / `..._phase.npy`.  
  - **Verification**: Integration test `tests/integration/test_full_grid.py` confirms that ~300 runs complete within the 6 h CI wall‑time limit, that each run produces a `status` field (`completed` or `unstable`), and that the file naming convention matches the schema.

- [ ] **T011a** [P] Ensure that the batch runner executes **≥ 5 independent noise‑seed repeats** for every (Ω, ε₍dd₎) configuration.  
  - **Verification**: `tests/unit/test_runner_repeats.py` checks that for each parameter tuple the runner creates exactly five runs with distinct `seed` values and that the metadata reflects this.

- [ ] **T011b** [P] Add a configurable `MAX_RUNTIME` parameter to the runner; after each run the script logs a warning if the cumulative estimated runtime would exceed this limit instead of asserting a hard failure.  
  - **Verification**: `tests/unit/test_runtime_guard.py` validates that when the projected total exceeds `MAX_RUNTIME` a warning is emitted and the script continues gracefully.

- [ ] **T012** [P] Implement phase‑winding vortex detection in `code/analysis/vortex_detector.py` (FR‑003).  
  - **Verification**: Unit test `tests/unit/test_vortex_detector.py` validates detection on a synthetic single‑vortex field and on a vortex‑antivortex pair; the output format must match `stability_metric.schema.yaml`.

- [ ] **T013** [P] Implement stability‑metric calculation (vortex density, radial variance, structure‑factor sharpness) in `code/analysis/metrics.py` (FR‑004).  
  - **Verification**: Contract test `tests/contract/test_metrics_schema.py` checks each CSV row against `stability_metric.schema.yaml`; a unit test `tests/unit/test_metrics_values.py` verifies numerical sanity on a known test case.

- [ ] **T014** [P] Implement metastability classification strictly according to Constitution‑VII (≥ 30 % vortex‑count drop **or** crystalline‑order loss). No additional vortex‑density threshold is introduced.  
  - **File**: `code/analysis/metastability.py` writes `data/processed/metastability_report.csv` containing columns `run_id`, `instability_classified`, `false_positive_rate`, `false_negative_rate`.  
  - **Verification**: `tests/unit/test_metastability.py` asserts that any run meeting the Constitution‑VII criteria is flagged, and that FP/FN rates are correctly computed on a synthetic benchmark set.

- [ ] **T015** [P] Perform Two‑Way ANOVA (Ω × ε₍dd₎) and Dunnett’s post‑hoc test in `code/statistics/aggregators.py`, outputting `data/aggregated/statistical_results.json` conforming to `statistical_aggregation.schema.yaml` (FR‑005).  
  - **Verification**: Unit test `tests/unit/test_two_way_anova.py` checks that the JSON contains `p_value_anova_interaction` and `p_value_dunnett` formatted to ≥ 4 dp; a regression test `tests/integration/test_aggregation_consistency.py` ensures the same results are obtained on repeated runs.

- [ ] **T015a** [P] Run the required **two‑sample t‑test** (α = 0.05) on each stability claim using the ≥ 5 seed repeats, and record its p‑value (`p_value_two_sample`) in the aggregation JSON.  
  - **Verification**: `tests/unit/test_two_sample_ttest.py` confirms that the test is executed for every configuration and that the p‑value field appears with at least four decimal places.

- [ ] **T015b** [P] Enforce output precision: all statistical numbers (p‑values, means, standard deviations, etc.) in `statistical_results.json` and CSV files are formatted to **≥ 4 decimal places**.  
  - **Verification**: `tests/unit/test_precision.py` parses the JSON/CSV and asserts the formatting requirement.

- [ ] **T016** [P] Generate contour phase‑maps and representative density/phase figures in `code/viz/plotter.py`; write PNGs to `figures/phase_map.png`, `figures/stable_example.png`, `figures/metastable_example.png`, `figures/unstable_example.png` (US‑3).  
  - **Verification**: Integration test `tests/integration/test_plotting.py` confirms that each PNG file is created, that the colour‑scale matches the underlying `mean_vortex_density` values, and that the files are non‑empty.

---

## Phase 3 – Validation, reproducibility & hand‑off

- [ ] **T017** [P] Run the full 64 × 64 grid scan (`RUN_FULL_GRID=true`) on the CI runner, then re‑run the selected verification subset at 256 × 256. Store the performance log in `data/processed/performance_log.txt`.  
  - **Verification**: `tests/integration/test_performance.py` parses the log and asserts total runtime ≤ 6 h and peak memory ≤ 14 GB; the log must contain timestamps for the first and last run.

- [ ] **T017a** [P] Ensure that the full‑grid run (T017) also respects the **≥ 5 independent noise‑seed repeats** per configuration.  
  - **Verification**: `tests/unit/test_full_grid_repeats.py` checks that for every (Ω, ε₍dd₎) point the log contains five distinct seed entries.

- [ ] **T018** [P] Validate that the statistical pipeline correctly handles the “zero initial vortex” edge case without division‑by‑zero errors.  
  - **File**: `tests/unit/test_zero_vortex_stats.py` (already present).  
  - **Verification**: The test must pass on the real `statistical_results.json`; a CI step fails if any `NaN` or `inf` appears in the aggregated JSON.

- [ ] **T019** [P] Produce the final research artefacts:  
  - **Files**: `data/aggregated/final_phase_diagram.json`, `figures/final_phase_diagram.png`, `docs/methods.md` (detailing solver, vortex detection, metrics, statistics).  
  - **Verification**: Contract test `tests/contract/test_final_artifacts.py` checks that the JSON conforms to the aggregation schema, that the PNG is readable, and that `methods.md` contains at least one citation to each of the three primary references listed in the spec.

- [ ] **T020** [P] Create a reproducibility script `scripts/reproduce.sh` that (1) installs dependencies from `code/requirements.txt`, (2) runs the full grid, (3) runs the aggregation, and (4) generates the figures. The script must exit with status 0 on success.  
  - **Verification**: CI step executes `bash scripts/reproduce.sh`; `tests/contract/test_repro.sh.py` checks that the script prints a success message and that all expected output files exist afterward.

---

## Phase 4 – Reviewer response & hand‑off to paper pipeline

- [ ] **T021** [P] Compile a short “Research Summary” (`research_summary.md`) that links directly to the generated figures, tables, and the `methods.md` documentation. This file will be consumed by the downstream paper‑generation pipeline.  
  - **Verification**: `tests/contract/test_summary_links.py` parses the markdown and confirms that every referenced figure or JSON file exists.

- [ ] **T022** [P] Archive a provenance manifest `data/provenance.yaml` that records the git commit hash, the exact command‑line used for the full‑grid run, and the versions of the major scientific libraries (`numpy`, `scipy`, `matplotlib`).  
  - **Verification**: `tests/contract/test_provenance.yaml` validates the YAML syntax and the presence of required keys (`commit`, `command`, `library_versions`).

---

### Dependency matrix (for reviewer reference)

| Task | Depends on |
|------|------------|
| T001–T008 | – |
| T009 | – |
| T010 | T001, T009 |
| T010a | T009 |
| T011 | T001, T002, T009, T010 |
| T011a | T011 |
| T011b | T011a |
| T012 | T001, T009 |
| T013 | T012 |
| T014 | T013 |
| T015 | T013, T014 |
| T015a | T015 |
| T015b | T015a |
| T016 | T015 |
| T017 | T011, T015 |
| T017a | T017 |
| T018 | T015 |
| T019 | T016, T017 |
| T020 | T011, T015, T016 |
| T021 | T019, T020 |
| T022 | T017, T020 |

---  

*All unchecked tasks must produce real files or executable scripts that can be inspected by the platform’s verifier.  When a task is completed, its checkbox will be checked by the CI pipeline.*  