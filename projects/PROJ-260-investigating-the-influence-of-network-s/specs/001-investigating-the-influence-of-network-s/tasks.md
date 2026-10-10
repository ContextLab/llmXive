# Tasks: Investigating the Influence of Network Structure on Heat Conduction in Amorphous Solids

**Input**: Design documents from `/specs/001-investigate-network-heat-conduction/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

---

## Phase 1 – Project scaffolding & quick‑start documentation  

**Goal**: Establish a reproducible directory layout, dependency list, and a runnable CLI entry point that can be demonstrated on a tiny real dataset.

- [ ] T001a [P] Create the full data‑directory hierarchy (`data/raw/`, `data/derived/`, `data/derived/topology/`, `data/derived/vdos/`, `data/derived/reference/`, `data/derived/correlation/`, `data/metadata/`) and write a machine‑generated tree listing to `docs/design/directory_structure.txt`.  
  *Verification*: `cat docs/design/directory_structure.txt` must show all required folders.

- [ ] T001b [P] Create the output‑directory hierarchy (`outputs/`, `outputs/figures/`, `outputs/reports/`) and write a tree listing to `docs/design/output_structure.txt`.  
  *Verification*: `cat docs/design/output_structure.txt` must list the three output folders.

- [ ] T002 [P] Initialise a Python project with a pinned `requirements.txt` containing `numpy`, `scipy`, `pandas`, `scikit-learn`, `ase`, `matplotlib`, `seaborn`, `networkx`, `pytest`, `pytest-cov`, `pytest-randomly`, `statsmodels`.  

- [ ] T003a [P] Add `ruff.toml` with strict linting (select = ["E","F","I","W"], line‑length = 88, target‑version = "py311").  

- [ ] T003b [P] Add `pyproject.toml` with a `[tool.black]` section (line‑length = 88, target‑version = ["py311"]).  

- [ ] T009 [P] Add `__init__.py` files to `tests/unit/`, `tests/integration/`, and `tests/contract/` so that the test package is importable.  

- [ ] T010 [P] Configure `pyproject.toml` to enable `pytest-randomly` and `pytest-cov` with a minimum coverage of 80 %.  

- [ ] T045 [P] Implement `src/cli/main.py` – the top‑level CLI that sequentially calls the topology extractor, VDOS calculator, κ‑ingester, and statistical analyzer, writing all artefacts under `data/derived/` and `outputs/`.  

- [ ] T048 [P] Create a documentation‑only `config.yaml` containing `bootstrap_iterations: 1000` and a placeholder `effect_size` entry (ignored by the code).  

- [ ] T049 [P] Implement `scripts/update_state_hashes.py` which computes SHA‑256 hashes of every file under `data/`, `src/`, and `outputs/` and writes a summary to `state/projects/PROJ-260-investigating-the-influence-of-network-s.yaml`.  

---

## Phase 2 – Foundational data acquisition & independence checks  

**Goal**: Fetch real amorphous‑silicon trajectories from verified repositories, validate them, and ingest independently sourced thermal‑conductivity values.

- [ ] T055a [Foundational] Implement `src/services/registry_generator.py` to write `data/metadata/dataset_registry.json` mapping system‑size labels (`N1000`, `N2000`, `N4000`) to verified Materials‑Cloud/Zenodo dataset IDs (constant `VERIFIED_DATASET_IDS` in `src/lib/config.py`).  

- [ ] T055b [Foundational] Implement `src/services/registry_validator.py` to verify each ID in `dataset_registry.json` via the Zenodo API, aborting with a clear error if any ID is unreachable.  Writes `data/metadata/valid_sources.json` and a log `data/metadata/registry_validation.log`.  

- [ ] T056 [Foundational] Implement `src/services/data_loader.py` that streams the three verified datasets (using `datasets.load_dataset(..., streaming=True)`) into `data/raw/`.  The loader must:
  * Ensure **all three** system sizes are present.
  * Write a SHA‑256 checksum file `data/metadata/checksums.txt`.
  * Abort loudly on any download failure (no synthetic fallback).  

- [ ] T057 [Foundational] Implement `src/services/kappa_ingester.py` to read a researcher‑provided CSV (default `data/derived/reference/kappa_values.csv`) containing columns `system_size,kappa,source_id,source_type,trajectory_id`.  
  *Validate*:
  * `source_id` matches an entry in `valid_sources.json`.
  * `source_id` ≠ `trajectory_id` (independence check, abort with `FatalError: Circular Dependency Detected` if violated).
  * All rows have `is_independent=True`.
  * Write the validated CSV back to `data/derived/reference/kappa_values_validated.csv`.  

- [ ] T061 [P] Extend `src/services/topology_extractor.py` to stream trajectory files larger than 100 k atoms using `ase.io.iread` with a configurable `chunk_size`.  When streaming is used, log the sampled atom count, random seed, and limitation description to `data/metadata/sampling_log.txt`.  

- [ ] T062 [P] Add RDF‑ambiguity detection to `topology_extractor.py`: if the first minimum is shallow (< 5 % of the preceding peak) or multiple minima lie within 0.2 Å, log a warning and require the user to supply `--rdf-cutoff-override`.  

---

## Phase 3 – User Story 1: Topology extraction  

**Goal**: Parse trajectories, build a distance‑cutoff bond network, and compute per‑atom and global topological metrics.

- [ ] T017 [US1] Implement `src/services/topology_extractor.py` (FR‑001, FR‑002).  
  *Features*:
  * Load LAMMPS or XYZ files via `ase`.
  * Compute RDF, locate the first minimum (dynamic cutoff) or use `--rdf-cutoff-override`.
  * Build a `networkx` graph of bonds.
  * Compute per‑atom coordination number, bond‑angle variance, and flag any atom with coordination > 6 as a “Physical Anomaly” (non‑fatal).
  * Compute global mean coordination; if |mean − 4.00| > 0.05, log a critical message and set exit code 3 (pipeline continues).
  * Write per‑atom CSV to `data/derived/topology/<box_id>_topology.csv` and a summary JSON to `data/derived/topology/<box_id>_summary.json`.  

- [ ] T018 [P] Add structured logging (INFO/DEBUG) for all steps of `topology_extractor.py`; write logs to `data/metadata/topology_log.log`.  

- [ ] T020 [P] Add CLI flag `--rdf-cutoff-override` to `src/cli/main.py` (propagated to the extractor).  

- [ ] T019 [P] Add integration test `tests/integration/test_full_topology.py` that runs the extractor on a tiny public a‑Si trajectory (≤ 500 atoms) and checks that the output CSV contains the required columns and that the mean coordination is within the accepted tolerance.  

---

## Phase 4 – User Story 2: Vibrational analysis & bottleneck identification  

**Goal**: From velocity data, compute the VDOS, participation ratios, and quantify topological bottlenecks.

- [ ] T063 [US2] Implement `src/services/vdos_calculator.py` (FR‑003, FR‑004).  
  *Steps*:
  * Verify that velocity data exists; if missing, raise `VelocityDataMissingError` with exit code 4 (pipeline halts for VDOS but not for topology).
  * Compute the velocity autocorrelation function (VACF) using `numpy.float64` precision.
  * Perform FFT to obtain the VDOS spectrum.
  * Calculate the participation ratio for each frequency bin.
  * Identify localized modes (high PR, low frequency) and compute `localized_mode_density` (integrated over 10–15 THz).
  * Detect the high‑frequency peak (‑15 THz) and log a “Spectral Anomaly” if the peak height < 5 % of the global maximum **and** the system is not perfectly coordinated.
  * Write CSV `data/derived/vdos/<box_id>_vdos.csv` and a summary JSON `data/derived/vdos/<box_id>_summary.json`.  

- [ ] T026 [US2] (previous implementation retained; now superseded by T063 – keep as reference).  

- [ ] T027 [P] Implement `src/services/sensitivity_analyzer.py` to sweep the under‑coordination threshold (default < 3 ± 0.5) and report the coefficient of variation of bottleneck density in `data/derived/topology/sensitivity_report.txt`.  

- [ ] T028 [P] Add acoustic‑mode / high‑freq‑peak validation logic (see T063 description).  

- [ ] T029 [P] Add integration test `tests/integration/test_full_vdos.py` that runs the VDOS calculator on a verified small trajectory with velocities and checks that the output CSV contains `frequency_THz`, `density_of_states`, `participation_ratio` columns and that a high‑frequency peak is recorded.  

---

## Phase 5 – User Story 3: Correlation, robustness & power analysis  

**Goal**: Aggregate topology, VDOS, and κ data across three system sizes, perform bootstrap‑based correlation, apply multiple‑comparison correction, and report statistical power.

- [ ] T046 [US3] Implement a data‑aggregation script `src/services/aggregate_data.py` that:
  * Scans `data/derived/topology/*_N{size}*.csv` for the three required sizes (1000, 2000, 4000 atoms).
  * Joins each record with the corresponding VDOS summary and κ value from `kappa_values_validated.csv`.
  * Asserts that **exactly** three distinct system sizes are present; abort with a clear error if not.
  * Writes the combined dataset to `data/derived/correlation/aggregated_dataset.csv`.  

- [ ] T041 [US3] Implement `src/services/statistical_analyzer.py` (FR‑005, FR‑006, FR‑007).  
  *Operations*:
  * Load `aggregated_dataset.csv`.
  * For each topological metric (`mean_coordination`, `bottleneck_density`, `bond_angle_variance`) compute Spearman and Pearson r, raw p‑values, and 95 % CI via **1000** bootstrap iterations (`scipy.stats.bootstrap`).
  * Apply Bonferroni correction across all metric‑size tests; store corrected p‑values.
  * Perform a power analysis using the observed effect size (Cohen’s d for Pearson r conversion) via `statsmodels.stats.power.NormalIndPower`; flag `low_power_warning` if power < 0.8.
  * Write one JSON file per metric‑size combination to `data/derived/correlation/<metric>_N{size}.json` that conforms to `contracts/correlation.schema.yaml`.  

- [ ] T042 [P] In `statistical_analyzer.py`, compute and output the variance of correlation coefficients across the three system sizes (finite‑size effect) to `outputs/reports/finite_size_effect.txt`.  

- [ ] T043 [P] Log a “Low Power” warning (and set `low_power_warning: true` in the JSON) when power < 0.8.  

- [ ] T047 [P] Add a human‑readable summary table `outputs/reports/correlation_summary.csv` that lists, for each metric‑size pair, `spearman_r`, `pearson_r`, `p_value_corrected`, `ci_lower`, `ci_upper`, `bootstrap_iterations`, `statistical_power`, and `low_power_warning`.  

- [ ] T047b [P] Add unit test `tests/unit/test_power_ignores_config.py` that temporarily patches `config.yaml` with a dummy effect size and verifies that `statistical_analyzer` still uses the observed effect size for power calculation.  

- [ ] T044 [P] Add integration test `tests/integration/test_full_correlation.py` that runs the full aggregation → statistical pipeline on a minimal but complete three‑size dataset (≤ 30 realizations per size) and checks that the JSON outputs validate against `contracts/correlation.schema.yaml`.  

---

## Phase 6 – Reporting & final hand‑off  

**Goal**: Produce reproducible figures, tables, and a concise methods/results write‑up linked to the actual artefacts.

- [ ] T050 [P] Generate a PDF/HTML report in `outputs/reports/` containing:
  * RDF plots, VDOS spectra, bottleneck density sensitivity curves.
  * Correlation scatter plots with 95 % CI bands for each metric‑size pair.
  * Tables from `correlation_summary.csv`.
  * Explicit statements of any warnings (low power, ambiguous RDF, missing velocity data).  

- [ ] T051 [P] Save all figures (PNG) to `outputs/figures/` with descriptive filenames (e.g., `rdf_N1000.png`, `vdos_N2000.png`, `corr_bottleneck_N4000.png`).  

- [ ] T052 [P] Update `README.md` with a “Quick‑start” section that shows how to run the full pipeline via `python -m src.cli.main --kappa-file data/derived/reference/kappa_values.csv`.  

- [ ] T053 [P] Generate API documentation for `src/services/` using `pdoc` and place it under `docs/api/`.  

- [ ] T055 [P] Run the full automated test suite (`pytest -q`) and ensure ≥ 80 % coverage; failures must be fixed before proceeding.  

---

## Phase 7 – Manual reference calculation & SC‑001 verification  

**Goal**: Provide an independent, deterministic reference correlation calculation to verify the pipeline’s numerical accuracy.

- [ ] T059 [US3] Implement `scripts/manual_reference.py` that:
  * Programmatically builds a small amorphous‑silicon structure using the Wooten‑Winer‑Weaire (WWA) algorithm (≈ 200 atoms).
  * Runs `topology_extractor.py` on this structure to obtain `mean_coordination` and `bottleneck_density`.
  * Generates a synthetic κ value using the Cahill‑Pohl model (purely deterministic, documented).
  * Computes the Spearman rank correlation between the two metrics **using the same code path** (`scipy.stats.spearmanr`).
  * Writes the resulting `r` and the input vectors to `data/metadata/manual_reference.json`.  

- [ ] T060 [P] Add test `tests/unit/test_sc001_accuracy.py` that loads `manual_reference.json` and compares the pipeline’s correlation output (run on the same synthetic dataset) against the stored reference, asserting `|pipeline_r ‑ reference_r| < 1e-6`.  

---

## Phase 8 – Edge‑case robustness (review‑driven)  

- [ ] T064 [P] Extend `statistical_analyzer.py` to detect when fewer than three system sizes are present; log `"LIMITATION: Insufficient System Sizes for Finite‑Size Validation"` and set `finite_size_validation_status: "SKIPPED"` in the final JSON report.  

- [ ] T065 [P] Add integration test `tests/integration/test_data_loader_fail.py` that mocks a download failure and asserts `data_loader.py` raises `DataFetchError` and exits with code 1, without invoking any synthetic‑data generator.  

---

### Dependencies & execution order  

| Phase | Tasks (must finish before) |
|-------|-----------------------------|
| 1 | T001a, T001b, T002‑T010 |
| 2 | T055a → T055b → T056 → T057 |
| 3 | T017 (depends on T056) |
| 4 | T063 (depends on T056) |
| 5 | T046 (depends on T056 & T057) → T041 |
| 6 | T045 (orchestrates all above) |
| 7 | T059 (independent) → T060 |
| 8 | Independent robustness checks (can run after core pipeline) |

All tasks marked `[P]` may run in parallel provided their file‑level dependencies are respected. Checked tasks (`[X]`) have already produced verifiable artefacts; unchecked tasks must be completed before the next verification round.
