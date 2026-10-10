# Tasks: Investigating the Influence of Network Structure on Heat Conduction in Amorphous Solids

**Inputs**: `spec.md`, `plan.md`, existing code base, data‑model, and contracts.  
All tasks are written as canonical checkbox items; each includes the required
artifact paths and an explicit verification step.

---

## Phase 1 – Project scaffolding & quick‑start

| Goal | Produce a reproducible directory layout, dependency list, and a runnable CLI that can be demonstrated on a tiny real dataset. |
|------|-----------------------------------------------------------------------------------------------------------------------------------|

- [X] **T001**  Create the full data‑directory hierarchy  
  `data/raw/`, `data/derived/`, `data/derived/topology/`, `data/derived/vdos/`, `data/derived/reference/`, `data/derived/correlation/`, `data/metadata/`  
  and write a machine‑generated tree listing to `docs/design/data_tree.txt`.  
  **Verification**: `cat docs/design/data_tree.txt` must contain all seven directories (one per line).

- [X] **T002**  Create the output‑directory hierarchy `outputs/`, `outputs/figures/`, `outputs/reports/` and write its tree to `docs/design/output_tree.txt`.  
  **Verification**: `cat docs/design/output_tree.txt` must list the three output folders.

- [ ] **T003**  Initialise a Python project with a pinned `requirements.txt` containing  
  `numpy`, `scipy`, `pandas`, `scikit-learn`, `ase`, `matplotlib`, `seaborn`, `networkx`, `pytest`, `pytest-cov`, `pytest-randomly`, `statsmodels`.  
  **Verification**: `pip install -r requirements.txt` succeeds without version conflicts.

- [ ] **T004**  Add linting and formatting configs: `ruff.toml` (strict E/F/I/W, line‑length 88, Python 3.11) and `pyproject.toml` with a `[tool.black]` section (same line‑length, target‑version 3.11).  
  **Verification**: Running `ruff check .` and `black --check .` reports no violations.

- [ ] **T005**  Implement the top‑level CLI entry point `src/cli/main.py`.  
  It must expose sub‑commands `extract-topology`, `calc-vdos`, `ingest-kappa`, `aggregate`, `analyze`, and orchestrate the full pipeline, writing all artefacts under `data/derived/` and `outputs/`.  
  **Verification**: `python -m src.cli.main --help` lists all sub‑commands and exits with code 0.

- [X] **T006**  Create a minimal `config.yaml` in the project root containing  
  ```yaml
  bootstrap_iterations: 1000
  ```  
  (additional keys may be added later).  
  **Verification**: `yaml.safe_load(open("config.yaml"))` returns a dict with the key `bootstrap_iterations`.

- [X] **T007**  Implement `scripts/update_state_hashes.py` that computes SHA‑256 hashes of every file under `data/`, `src/`, and `outputs/` and writes a summary to `state/projects/PROJ-260-investigating-the-influence-of-network-s.yaml`.
  **Verification**: Running the script creates the YAML file and contains at least one hash entry.

---

## Phase 2 – Data acquisition & independence checks

| Goal | Fetch real amorphous‑silicon trajectories, validate them, and ingest independently‑sourced thermal‑conductivity values. |
|------|--------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T008** [Foundational] Implement `src/services/registry_generator.py` that writes `data/metadata/dataset_registry.json`. This JSON maps system‑size labels (`N1000`, `N2000`, `N4000`) to verified Materials‑Cloud/Zenodo dataset identifiers (hard‑coded in `src/lib/config.py` as `VERIFIED_DATASET_IDS`).  
  **Verification**: The JSON file exists and contains three keys matching the size labels.

- [ ] **T009** [Foundational] Implement `src/services/registry_validator.py` which reads `dataset_registry.json`, queries the Zenodo API for each ID, aborts with a clear error if any ID is unreachable, and writes `data/metadata/valid_sources.json` plus a log `data/metadata/registry_validation.log`.   <!-- FAILED-IN-EXECUTION: src/services/run_registry_validator.py exit=1 -->
  **Verification**: The log contains the line `VALIDATION SUCCESS` and `valid_sources.json` lists the same three IDs.

- [ ] **T010** [Foundational] Implement `src/services/data_loader.py` that streams the three verified datasets (using `datasets.load_dataset(..., streaming=True)`) into `data/raw/`. It must:  
  * Write a SHA‑256 checksum per downloaded file to `data/metadata/checksums.txt`.  
  * Abort loudly (`raise RuntimeError`) on any download failure (no synthetic fallback).  
  **Verification**: After a successful run, `data/raw/` contains at least one file per system size and `checksums.txt` lists a hash for each file.

- [ ] **T011** [Foundational] Implement `src/services/kappa_ingester.py` that reads `data/derived/reference/kappa_values.csv` (columns: `system_size,kappa,source_id,source_type,trajectory_id`), validates that:  
  * `source_id` appears in `valid_sources.json`.  
  * `source_id` ≠ `trajectory_id` (independence check).  
  * All rows have `is_independent=True` (or raise if missing).  
  It then writes the validated table to `data/derived/reference/kappa_values_validated.csv`.  
  **Verification**: The output CSV exists, contains the same number of rows as the input, and a grep for the string `FatalError` returns nothing.

- [ ] **T031** [FR‑006] Verify that at least **30** independent disorder snapshots have been ingested for each of the three system sizes. Scan `data/raw/` (or the manifest generated by T010) and count files per size; abort with an error if any size has fewer than 30 files.  
  **Verification**: The task logs the counts and fails with a clear message if the threshold is not met.

---

## Phase 3 – User Story 1: Topology extraction

| Goal | Parse trajectories, build a bond network, and compute per‑atom & global topology metrics. |
|------|----------------------------------------------------------------------------------------|

- [ ] **T012** [US1] Implement `src/services/topology_extractor.py` (FR‑001, FR‑002). It must:  
  * Load LAMMPS dump or XYZ files via `ase.io.read`.  
  * Compute the radial distribution function, locate the **first minimum** (dynamic cutoff) or honor a user‑provided `--rdf-cutoff-override`.  
  * **Verification**: Confirm that the cutoff used equals the RDF first minimum within ±0.01 Å.  
  * Build a `networkx` graph of bonds using that cutoff.  
  * Compute per‑atom coordination number, bond‑angle variance, flag any atom with coordination > 6 as a non‑fatal “Physical Anomaly”.  
  * Compute global `mean_coordination` and `bottleneck_density`.  
  * Write per‑atom CSV to `data/derived/topology/<box_id>_topology.csv` and a summary JSON to `data/derived/topology/<box_id>_summary.json`.  
  **Verification**: Running the extractor on a tiny public a‑Si trajectory (≤ 500 atoms) creates both files; the CSV contains columns `atom_id,coordination_number,bond_angle_variance,is_bottleneck`; the JSON field `mean_coordination` satisfies `|mean‑4.00| ≤ 0.05`.

- [ ] **T013**  Add structured logging (`INFO`/`DEBUG`) for all steps of `topology_extractor.py` to `data/metadata/topology_log.log`.  
  **Verification**: The log file exists and contains the line `RDF cutoff =`.

- [ ] **T014**  Add an integration test `tests/integration/test_full_topology.py` that invokes the extractor on the tiny dataset and asserts the CSV schema and mean‑coordination tolerance.  
  **Verification**: `pytest -q tests/integration/test_full_topology.py` passes.

---

## Phase 4 – User Story 2: Vibrational analysis & bottleneck identification

| Goal | Compute VDOS, participation ratios, and quantify topological bottlenecks. |
|------|--------------------------------------------------------------------------|

- [ ] **T015** [US2] Implement `src/services/vdos_calculator.py` (FR‑003, FR‑004). It must:  
  * Verify that a velocity dump is present; if missing, raise `VelocityDataMissingError` with exit code 4 (graceful halt, topology results retained).  
  * Compute the velocity autocorrelation function (VACF) using `numpy.float64`.  
  * Perform an FFT to obtain the VDOS spectrum.  
  * Calculate the participation ratio for every frequency bin.  
  * Identify localized modes in the high‑frequency range (10–15 THz) and compute `localized_mode_density`.  
  * Detect the high‑frequency peak (≈ ‑15 THz) and log a “Spectral Anomaly” if the peak height < 5 % of the global maximum **and** the box is not perfectly coordinated.  
  * Write CSV `data/derived/vdos/<box_id>_vdos.csv` (columns `frequency_THz,density_of_states,participation_ratio`) and summary JSON `data/derived/vdos/<box_id>_summary.json`.  
  **Verification**: Running the calculator on a verified small trajectory with velocities creates both files; the CSV contains the required columns and the JSON field `high_freq_peak_THz` lies between 10 and 15 THz. Additionally, a negative‑path test confirms that missing velocity data raises the specified error with exit code 4.

- [ ] **T016**  Implement `src/services/sensitivity_analyzer.py` that sweeps the under‑coordination threshold (`< 3 ± 0.5`) and writes the coefficient of variation of bottleneck density to `data/derived/topology/sensitivity_report.txt`.  
  **Verification**: The report file exists and contains a line `CV =` with a numeric value.

- [ ] **T017**  Add an integration test `tests/integration/test_full_vdos.py` that runs `vdos_calculator.py` on the same tiny trajectory and asserts the CSV schema and that `high_freq_peak_THz` is recorded.  
  **Verification**: `pytest -q tests/integration/test_full_vdos.py` passes.

---

## Phase 5 – Aggregation & statistical correlation (User Story 3)

| Goal | Assemble all derived data, perform bootstrap‑based correlation, apply multiple‑comparison correction, and report statistical power. |
|------|------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T018** [US3] Implement `src/services/aggregate_data.py`. It must:  
  * Scan `data/derived/topology/*_N{size}.csv` for the required sizes (at least three distinct sizes, e.g., 1000, 2000, 4000 atoms).  
  * Join each record with the corresponding VDOS summary (`*_summary.json`) and the validated κ value from `kappa_values_validated.csv`.  
  * Abort with a clear error if **fewer than three** distinct system sizes are present.  
  * Write the combined dataset to `data/derived/correlation/aggregated_dataset.csv`.  
  **Verification**: After a successful run, the CSV exists and has a column `system_size_group` with ≥ 3 unique values.

- [ ] **T019** [US3] Implement `src/services/statistical_analyzer.py` (FR‑005, FR‑006, FR‑007). It must:  
  * Load `aggregated_dataset.csv`.  
  * For each topological metric (`mean_coordination`, `bottleneck_density`, `bond_angle_variance`) compute Spearman and Pearson coefficients, raw p‑values, and 95 % confidence intervals via **1000** bootstrap iterations (`scipy.stats.bootstrap`).  
  * Apply Bonferroni correction across all metric‑size tests and store `p_value_corrected`.  
  * Perform a power analysis using the observed effect size (Cohen’s d derived from Pearson r) via `statsmodels.stats.power.NormalIndPower`; set `low_power_warning: true` if power < 0.8.  
  * Write one JSON per metric‑size pair to `data/derived/correlation/<metric>_N{size}.json` conforming to `contracts/correlation.schema.yaml`.  
  * Produce a human‑readable summary CSV `outputs/reports/correlation_summary.csv` with all statistical fields, and a variance‑of‑coefficients report `outputs/reports/finite_size_effect.txt`.  
  **Verification**: All JSON files validate against the schema (run `jsonschema`), the summary CSV contains the header row, and `low_power_warning` is a boolean.

- [ ] **T032** [FR‑008] Validate thermal‑conductivity source independence before correlation. The task reads `data/derived/reference/kappa_values_validated.csv` and checks that every `source_id` differs from the associated `trajectory_id`. It also confirms that the `reference_generator.py` script is **not** invoked in the production pipeline (e.g., by ensuring no file `data/derived/reference/kappa_generated.csv` exists).  
  **Verification**: The validation script exits with code 0 and logs “All κ values independent”; pipeline aborts if any violation is detected.

- [ ] **T036** [SC‑003] Compute the variance of the correlation coefficients (Spearman `r`) across the three system sizes for each metric and assert that the variance does not exceed a tolerance of 0.02 (indicating consistency). Write the result to `outputs/reports/correlation_consistency.txt`.  
  **Verification**: The file exists and contains `Variance =` with a numeric value ≤ 0.02.

- [ ] **T030** [SC‑005] Measure the total wall‑clock time of the full pipeline (from topology extraction through statistical analysis) on a 4000‑atom dataset and assert that it is ≤ 1800 seconds. Record the elapsed time in `outputs/reports/runtime_report.txt`.  
  **Verification**: The report file exists and contains `Elapsed time =` with a value ≤ 1800 s.

- [ ] **T020** [P] Add an integration test `tests/integration/test_full_correlation.py` that runs the aggregation → statistical pipeline on a minimal three‑size dataset (≤ 30 realizations per size) and asserts that each generated JSON validates against `contracts/correlation.schema.yaml`.  
  **Verification**: `pytest -q tests/integration/test_full_correlation.py` passes.

---

## Phase 6 – Reporting & final hand‑off

| Goal | Produce reproducible figures, tables, and a concise methods/results write‑up linked to the actual artefacts. |
|------|-----------------------------------------------------------------------------------------------------------|

- [ ] **T021**  Generate a PDF report `outputs/reports/report.pdf` (or HTML) that includes:  
  * RDF plots per system size.  
  * VDOS spectra with participation‑ratio overlays.  
  * Bottleneck‑density sensitivity curves.  
  * Correlation scatter plots with 95 % CI bands for each metric‑size pair.  
  * Tables from `correlation_summary.csv`.  
  * Explicit statements of any warnings (low power, ambiguous RDF, missing velocity).  
  **Verification**: The PDF opens without errors and each figure filename appears in the document.

- [ ] **T022**  Save all generated figures (PNG) to `outputs/figures/` with descriptive filenames (e.g., `rdf_N1000.png`, `vdos_N2000.png`, `corr_bottleneck_N4000.png`).  
  **Verification**: The directory contains at least three PNG files and `ls outputs/figures/` lists them.

- [ ] **T023**  Update `README.md` with a “Quick‑start” section that shows how to run the full pipeline via  
  `python -m src.cli.main --kappa-file data/derived/reference/kappa_values_validated.csv`.  
  **Verification**: The README contains the exact command line snippet.

- [ ] **T024**  Generate API documentation for the `src/services/` package using `pdoc` and place it under `docs/api/`.  
  **Verification**: `docs/api/` contains an `index.html` file.

- [ ] **T025**  Run the full automated test suite (`pytest -q`) and ensure **≥ 80 %** line coverage; fix any failures before proceeding.  
  **Verification**: The pytest summary reports `coverage: 80%` (or higher) and `0 failed`.

---

## Phase 7 – Manual reference calculation & SC‑001 verification

| Goal | Provide an independent deterministic reference calculation to validate the pipeline’s numerical accuracy. |
|------|-------------------------------------------------------------------------------------------------------------|

- [ ] **T026** [US3] Implement `scripts/manual_reference.py` that:  
  * Builds a small amorphous‑silicon structure (~200 atoms) using the Wooten‑Winer‑Weaire algorithm (deterministic seed).  
  * Runs `topology_extractor.py` on this structure to obtain `mean_coordination` and `bottleneck_density`.  
  * Generates a synthetic thermal‑conductivity value using the Cahill‑Pohl model (purely formula‑based, documented).  
  * Computes the Spearman rank correlation between the two metrics **using the same code path** (`scipy.stats.spearmanr`).  
  * Writes the inputs and resulting `r` to `data/metadata/manual_reference.json`.  
  **Verification**: The JSON file exists and contains keys `mean_coordination`, `bottleneck_density`, `thermal_conductivity`, `spearman_r`.  
  *Note*: This reference is **solely for internal validation** and its κ values are **not used** in the production correlation pipeline, thereby preserving FR‑008 independence.

- [ ] **T027** [P] Add a unit test `tests/unit/test_sc001_accuracy.py` that loads `manual_reference.json`, runs the pipeline’s correlation routine on the same synthetic dataset, and asserts `|pipeline_r – reference_r| < 1e-6`.  
  **Verification**: The test passes (`pytest -q tests/unit/test_sc001_accuracy.py`).

---

## Phase 8 – Edge‑case robustness (review‑driven)

| Goal | Ensure the pipeline behaves gracefully when assumptions are violated. |
|------|------------------------------------------------------------------------|

- [ ] **T028** [P] Extend `statistical_analyzer.py` to detect when fewer than three system sizes are present; log `"LIMITATION: Insufficient System Sizes for Finite‑Size Validation"` and set `finite_size_validation_status: "SKIPPED"` in the final JSON report.  
  **Verification**: Running the analyzer on a two‑size dataset creates a JSON with the field `finite_size_validation_status` set to `"SKIPPED"` and the log contains the warning string.

- [ ] **T029** [P] Add an integration test `tests/integration/test_data_loader_fail.py` that mocks a download failure (e.g., by pointing the registry to a non‑existent Zenodo ID) and asserts that `data_loader.py` raises `RuntimeError` with exit code 1 and **does not** invoke any synthetic‑data generator.  
  **Verification**: The test passes and the traceback contains `DataFetchError`.
