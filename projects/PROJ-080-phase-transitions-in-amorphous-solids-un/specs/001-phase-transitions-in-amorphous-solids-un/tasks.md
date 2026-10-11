# Tasks: Phase Transitions in Amorphous Solids Under Shear Stress

**Input**: Design documents from `/specs/001-phase-transitions-in-amorphous-solids/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL – only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `- [ ] T### [P?] [USx?] description with exact artifact paths`

- **[P]** – can run in parallel (different files, no dependencies)  
- **[USx]** – which user story this task belongs to (e.g., US1, US2, US3)  
- Include the exact file path(s) that the task reads or writes in an indented continuation line.

---

## Phase 1: Setup and first end‑to‑end analysis (split into sub‑tasks)

- [ ] T070-setup-dirs Create project directory hierarchy required for the pipeline.  
  Path: `projects/PROJ-080-phase-transitions-in-amorphous-solids-un/{data/raw,data/processed,code,tests/unit,tests/integration,specs/contracts}`  

- [ ] T071-setup-schemas Create all required JSON‑Schema contract files (trajectory, output, precursor_metrics, analysis_results).  
  Path: `specs/contracts/trajectory.schema.yaml`, `specs/contracts/output.schema.yaml`, `specs/contracts/precursor_metrics.schema.yaml`, `specs/contracts/analysis_results.schema.yaml`  

- [ ] T001a-dirs‑verify Verify that the directory structure created by T070 exists.  
  Path: (test script) `tests/unit/test_directory_structure.py`

- [ ] T001a-schemas‑verify Verify that the four schema files created by T071 are syntactically valid YAML and conform to their JSON‑Schema definitions.  
  Path: (test script) `tests/unit/test_schemas.py`

- [ ] T001b Initialize a Python 3.11 project with `pytest`, `ruff`, `black`, and `mypy` dependencies in `pyproject.toml`.  
  Path: `pyproject.toml`  

- [ ] T001b‑verify‑pyproject Verify that `pyproject.toml` contains the required dependencies and correct Python version.  
  Path: (test script) `tests/unit/test_pyproject.py`

- [ ] T001c Configure linting and formatting tools (`ruff.toml`, `mypy.ini`).  
  Path: `ruff.toml`, `mypy.ini`  

- [ ] T001c‑verify‑lint Verify that `ruff.toml` and `mypy.ini` contain the expected sections and settings.  
  Path: (test script) `tests/unit/test_lint_config.py`

- [ ] T002 Implement `code/utils.py` with a global `SEED = 42` and streaming helpers `stream_hdf5(path, chunk_size)` and `stream_parquet(path, chunk_size)` to keep memory usage low (satisfies FR‑006).  
  Path: `code/utils.py`  

- [ ] T002‑verify‑utils Verify that `SEED` equals 42 and that the streaming helpers return correctly sized chunks.  
  Path: `tests/unit/test_utils.py`

- [ ] T070-create-logs-dir Create the logs directory required for file‑based logging.  
  Path: `code/logs/`

- [ ] T004-logging‑full Configure logging infrastructure: create `code/logging_config.py` with a file handler (`code/logs/pipeline.log`) and a console handler; set log level to `INFO` and format `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`. Also add the specific warning formatter for indeterminate trajectories.  
  Path: `code/logging_config.py`  

- [ ] T004‑logging‑verify Verify that `code/logging_config.py` creates both handlers with the correct format and that `code/logs/pipeline.log` exists.  
  Path: `tests/unit/test_logging_config.py`

- [ ] T004b‑warning‑verify Trigger an indeterminate‑trajectory condition and capture the exact warning message to ensure it matches the specification.  
  Path: `tests/unit/test_indeterminate_warning.py`

- [ ] T006 Implement `code/data_generator.py` to create synthetic MD trajectories (coordinates, box dimensions, stress tensors) and assign “brittle” or “ductile” labels based on strain‑rate/temperature. Include a `--large` flag that generates a sparse amorphous configuration with ≤ 100 000 particles (to test FR‑006).  
  Path: `code/data_generator.py`  

- [ ] T006‑verify‑schema Validate that generated HDF5 files and `metadata.json` conform to `trajectory.schema.yaml` and contain the deterministic seed (42).  
  Path: `tests/unit/test_data_generator_schema.py`

- [ ] T006‑gen Execute `code/data_generator.py` to produce the initial synthetic trajectory `data/raw/synthetic_trajectory_001.h5` and accompanying `data/raw/metadata.json` (seed = 42).  
  Path: `data/raw/synthetic_trajectory_001.h5`, `data/raw/metadata.json`  

- [ ] T006‑gen‑verify Verify that the generated files exist and that `metadata.json` records the seed value 42.  
  Path: `tests/unit/test_data_generator_output.py`

- [ ] T007 Implement `code/data_loader.py` with a HuggingFace streaming loader (`datasets.load_dataset(..., streaming=True)`). The loader must first attempt to fetch the real dataset `materials-science/amorphous-silicon-shear-trajectories`; on failure it falls back to the synthetic data generated by T006.  
  Path: `code/data_loader.py`  

- [ ] T007‑fallback‑verify Simulate a `DatasetNotFoundError` and ensure the loader correctly falls back to the synthetic files.  
  Path: `tests/unit/test_data_loader_fallback.py`

- [ ] T008‑log‑verify Capture the log message “SYNTHETIC FALLBACK ACTIVE” when the fallback path is taken.  
  Path: `tests/unit/test_fallback_logging.py`

- [ ] T009‑chunk‑verify Ensure that streaming processes trajectories in chunks of **1000 timesteps** or **≈100 MB**, whichever is smaller, and that memory usage stays below 1 GB.  
  Path: `tests/unit/test_chunking.py`

- [ ] T010‑checksum‑verify Compute the SHA‑256 checksum of the raw trajectory file and write it to `state/projects/PROJ-080-phase-transitions-in-amorphous-solids-un.yaml`; then verify the entry is correctly written.  
  Path: `state/projects/PROJ-080-phase-transitions-in-amorphous-solids-un.yaml`  

- [ ] T011‑gen‑checksum Generate checksum entry if missing; T011‑verify‑checksum Verify that the checksum entry matches the computed value.  
  Path: `state/projects/PROJ-080-phase-transitions-in-amorphous-solids-un.yaml`  

- [ ] **T011-verify-gen** Verify that checksum generation runs when the entry is missing.  
  Path: `tests/unit/test_checksum_generation.py`

---

## Phase 2: User Story 1 – Precursor Detection Pipeline (Priority P1)

- [ ] T015a Implement `code/preprocess.py::load_and_validate_trajectory(path: str) → TrajectoryData`. Enforce FR‑006: raise `ValueError` if particle count > 100 000.  
  Path: `code/preprocess.py`  

- [ ] T015a‑verify Verify that trajectories exceeding 100 000 particles raise the appropriate exception.  
  Path: `tests/unit/test_preprocess_particle_limit.py`

- [ ] T015b Implement `code/preprocess.py::build_neighbor_list(coordinates: np.ndarray, cutoff: float) → NeighborList`.  
  Path: `code/preprocess.py`  

- [ ] T015c Implement `code/preprocess.py::compute_d2_min(current_coords: np.ndarray, prev_coords: np.ndarray, neighbor_list: NeighborList) → np.ndarray` (Falk‑Langer algorithm).  
  Path: `code/preprocess.py`  

- [ ] T016a Implement `code/preprocess.py::extract_stress_curve(stress_tensor: np.ndarray) → np.ndarray`.  
  Path: `code/preprocess.py`  

- [ ] T016b Implement `code/preprocess.py::detect_yielding(stress_curve: np.ndarray) → int` – first drop > 5 % relative to the local maximum over the preceding 50 timesteps (FR‑002).  
  Path: `code/preprocess.py`  

- [ ] T016c‑verify Add strict verification of the 50‑timestep window and local‑maximum calculation; ignore subsequent drops.  
  Path: `tests/unit/test_yield_detection.py`

- [ ] T017 Flag a trajectory as “indeterminate” when no sharp stress peak is found; log the warning using the logger from T004‑logging‑full.  
  Path: `code/preprocess.py`  

- [ ] T018 Add robust error handling for corrupted or incomplete trajectory files (missing frames, NaNs).  
  Path: `code/preprocess.py`  

- [ ] T019 Add numerical‑stability checks for NaN/Infinity values in $D^{2}_{\min}$ calculations; raise a clear exception if encountered.  
  Path: `code/preprocess.py`  

- [ ] T020 Write unit tests for edge cases (corrupted files, missing frames, NaNs) in `tests/unit/test_preprocess.py`.  
  Path: `tests/unit/test_preprocess.py`  

- [ ] T021 Write output artifacts:  
  * `data/processed/precursor_metrics.csv` (per‑particle $D^{2}_{\min}$)  
  * `data/processed/yield_flags.json` (yielding timestep and indeterminate flag)  
  Path: `data/processed/precursor_metrics.csv`, `data/processed/yield_flags.json`  

- [ ] T021‑verify Verify that `precursor_metrics.csv` conforms to `precursor_metrics.schema.yaml` and that `yield_flags.json` contains the required fields.  
  Path: `tests/unit/test_precursor_output.py`

- [ ] **T021-verify-output** Verify existence and schema compliance of `precursor_metrics.csv` and `yield_flags.json`.  
  Path: `tests/unit/test_precursor_output_verification.py`

---

## Phase 3: User Story 2 – Statistical Correlation Analysis (Priority P2)

- [ ] T025 Aggregate $D^{2}_{\min}$ to shear‑band level using k‑means (`n_clusters=3`, `random_state=42`). Write `data/processed/shear_band_stats.csv` with columns `shear_band_id`, `mean_D2_min`, `particle_count`, `label`.  
  Path: `code/analysis.py`, `data/processed/shear_band_stats.csv`  

- [ ] T025‑verify Verify that k‑means uses the fixed seed and that the CSV matches `analysis_results.schema.yaml`.  
  Path: `tests/unit/test_shear_band_aggregation.py`

- [ ] **T025-verify-clustering** Ensure k‑means seed usage and CSV schema compliance.  
  Path: `tests/unit/test_shear_band_clustering.py`

- [ ] T026-log Log the amendment note: “Permutation Test applied per Plan.md Spec Deviation. Spec FR‑003 (KS‑Test) is overridden by Plan.”  
  Path: `code/analysis.py`  

- [ ] T026-perm Perform a **Permutation Test** (fixed random seed, ≥ 10 000 permutations) on the shear‑band mean $D^{2}_{\min}$ values for brittle vs. ductile groups. Output `data/processed/permutation_results.json`.  
  Path: `code/analysis.py`, `data/processed/permutation_results.json`  

- [ ] T026‑perm‑verify Verify that at least 10 000 permutations were performed and that the JSON conforms to `output.schema.yaml`.  
  Path: `tests/unit/test_permutation.py`

- [ ] **T026-verify-permutation** Verify permutation count ≥10 000 and JSON schema compliance.  
  Path: `tests/unit/test_permutation_output.py`

- [ ] T046b‑create-ks-test Implement the two‑sample Kolmogorov‑Smirnov test on shear‑band aggregated $D^{2}_{\min}$ values (FR‑003). Output `data/processed/ks_test_results.json`.  
  Path: `code/analysis.py`, `data/processed/ks_test_results.json`  

- [ ] T046b‑verify‑ks-test Verify that the KS‑test returns both statistic and p‑value and that the JSON matches `analysis_results.schema.yaml`.  
  Path: `tests/unit/test_ks_test.py`

- [ ] T027 Verify sample size (number of shear bands ≥ 30). If below, halt and emit a “Power Limitation” warning as required by US‑2 Acceptance Scenario 2.  
  Path: `code/analysis.py`  

- [ ] T028a Detect whether more than one hypothesis test is being performed (multiple strain‑rate/temperature combos). Set flag `multiple_tests` and count.  
  Path: `code/analysis.py`  

- [ ] T028 Apply Bonferroni correction to the permutation p‑value when `multiple_tests` is true; write corrected value to `data/processed/corrected_p_values.json`.  
  Path: `data/processed/corrected_p_values.json`  

- [ ] T028‑verify Verify that the Bonferroni correction is correctly applied and that the output conforms to the schema.  
  Path: `tests/unit/test_bonferroni.py`

- [ ] **T028-verify-bonferroni** Validate correct Bonferroni adjustment and schema compliance.  
  Path: `tests/unit/test_bonferroni_correction.py`

- [ ] T029 Generate final statistical artifacts:  
  * `data/processed/permutation_results.json` (already produced)  
  * `data/processed/histograms.png` (overlaid brittle/ductile shear‑band $D^{2}_{\min}$ histograms)  
  * `data/processed/significance_report.json` (contains corrected p‑value, pass/fail against α = 0.05)  
  Path: `data/processed/histograms.png`, `data/processed/significance_report.json`  

- [ ] T029‑verify Verify that histogram image is created and that `significance_report.json` follows the expected schema.  
  Path: `tests/unit/test_statistical_artifacts.py`

- [ ] T029b Extract the derived threshold value from the permutation output (e.g., the $D^{2}_{\min}$ value that maximizes the test statistic) and save it to `data/processed/derived_threshold.json`.  
  Path: `data/processed/derived_threshold.json`  

- [ ] T029b‑verify Verify that the saved threshold corresponds to the maximum statistic in `permutation_results.json`.  
  Path: `tests/unit/test_derived_threshold.py`

- [ ] **T029b-verify-threshold** Confirm that the extracted threshold matches the maximum permutation statistic.  
  Path: `tests/unit/test_derived_threshold_verification.py`

---

## Phase 4: User Story 3 – Predictive Threshold Validation (Priority P3)

- [ ] T032a-deriv Update `data/raw/metadata.json` with derived “brittle” / “ductile” labels based on physical simulation parameters.  
  Path: `data/raw/metadata.json`  

- [ ] T032a‑deriv‑verify Verify that updated labels conform to the definitions in the spec (e.g., strain‑rate or temperature thresholds).  
  Path: `tests/unit/test_metadata_labels.py`

- [ ] **T032a-verify-deriv** Verify that `metadata.json` labels conform to the trajectory schema and spec definitions.  
  Path: `tests/unit/test_metadata_labels_verification.py`

- [ ] T032a-split Perform a stratified train‑test split (test = 20 %, `random_state=42`) on the dataset after freezing the threshold from `derived_threshold.json`. Save split indices to `data/processed/validation_set_indices.json`.  
  Path: `code/validation.py`, `data/processed/validation_set_indices.json`  

- [ ] T032a‑split‑verify Verify that the split respects the 20 % proportion and reproducibility (same seed yields same indices).  
  Path: `tests/unit/test_train_test_split.py`

- [ ] **T032a-verify-split** Verify split size (20 %) and reproducibility with fixed seed.  
  Path: `tests/unit/test_train_test_split_verification.py`

- [ ] T032a-eval Apply the frozen threshold to the held‑out validation set, compute confusion matrix, FPR, FNR, and F1‑score; write results to `data/processed/validation_metrics.json`.  
  Path: `data/processed/validation_metrics.json`  

- [ ] T032a‑eval‑verify Verify that `validation_metrics.json` conforms to `analysis_results.schema.yaml` and that metrics are numerically sensible.  
  Path: `tests/unit/test_validation_metrics.py`

- [ ] T033 Sweep the threshold over `{threshold‑0.05, threshold, threshold+0.05}` (using the frozen value) and compute performance metrics for each point. Store intermediate results in memory for the next task.  
  Path: (internal)  

- [ ] T034 Write the full sensitivity table (`threshold`, `FPR`, `FNR`, `F1`) to `data/processed/sensitivity_table.csv`.  
  Path: `data/processed/sensitivity_table.csv`  

- [ ] T034‑verify Verify that the CSV matches the schema defined in `output.schema.yaml`.  
  Path: `tests/unit/test_sensitivity_table.py`

- [ ] T035 Produce final predictive artifacts:  
  * `data/processed/prediction_results.json` (confusion matrix, F‑score, FPR, FNR)  
  * `data/processed/sensitivity_table.csv` (already produced)  
  Path: `data/processed/prediction_results.json`  

- [ ] T035‑verify Verify that `prediction_results.json` conforms to the schema and that the F‑score calculation is correct.  
  Path: `tests/unit/test_prediction_results.py`

---

## Phase 5: Performance & validation (cross‑cutting)

- [ ] T036a Implement `code/metrics.py::time_wrapper(func)` to measure wall‑clock execution time of any pipeline stage.  
  Path: `code/metrics.py`  

- [ ] T036a‑verify Verify that the wrapper records timing metadata for a dummy function.  
  Path: `tests/unit/test_time_wrapper.py`

- [ ] **T036a-verify-timing** Verify that `time_wrapper` records wall‑clock time correctly.  
  Path: `tests/unit/test_time_wrapper_verification.py`

- [ ] T037a Implement `code/metrics.py::memory_tracker(func)` using the `memory_profiler` library to capture peak RAM usage.  
  Path: `code/metrics.py`  

- [ ] T037a‑verify Verify that the tracker captures peak RAM for a memory‑intensive dummy function and writes to `data/processed/performance_report.json`.  
  Path: `tests/unit/test_memory_tracker.py`

- [ ] **T037a-verify-memory** Verify that `memory_tracker` writes peak RAM usage to `performance_report.json`.  
  Path: `tests/unit/test_memory_tracker_verification.py`

- [ ] T038 Execute the complete pipeline (data loading → preprocessing → analysis → validation) on the GitHub Actions `ubuntu‑latest` runner, instrumented with `time_wrapper` and `memory_tracker`. If runtime > 6 h or peak RAM > 7 GB, write a warning in `data/processed/performance_report.json` (status = "WARN") but do **not** abort unless limits exceed 20 % of the thresholds.  
  Path: `data/processed/performance_report.json`  

- [ ] T038‑warn‑verify Simulate exceeding runtime/RAM and verify that `status` is set to `"WARN"` in the performance report.  
  Path: `tests/unit/test_performance_warning.py`

- [ ] T039 Consolidate all measured performance metrics into `data/processed/performance_report.json` (runtime, peak RAM, status).  
  Path: `data/processed/performance_report.json`  

- [ ] T039‑verify Verify that the final performance report contains the required fields and respects the schema defined in `output.schema.yaml`.  
  Path: `tests/unit/test_performance_report_schema.py`

---

## Phase 6: Documentation & handoff

- [ ] T014 Integration test for “indeterminate” flagging when stress drop is ambiguous (`tests/integration/test_full_pipeline.py`).  
  Path: `tests/integration/test_full_pipeline.py`  

- [ ] T022 Unit test for shear‑band aggregation logic (`tests/unit/test_analysis.py`).  
  Path: `tests/unit/test_analysis.py`  

- [ ] T023 Unit test for the Permutation Test implementation (`tests/unit/test_analysis.py`).  
  Path: `tests/unit/test_analysis.py`  

- [ ] T024 Integration test for the “Power Limitation” warning when sample size < 30 (`tests/integration/test_full_pipeline.py`).  
  Path: `tests/integration/test_full_pipeline.py`  

- [ ] T030 Unit test for sensitivity sweep logic (`tests/unit/test_predict.py`).  
  Path: `tests/unit/test_predict.py`  

- [ ] T031 Integration test for confusion‑matrix generation (`tests/integration/test_full_pipeline.py`).  
  Path: `tests/integration/test_full_pipeline.py`  

- [ ] T040 Update `quickstart.md` with a concise command‑line example that runs the full end‑to‑end pipeline on a single synthetic trajectory and points to the main result files (`data/processed/*`).  
  Path: `quickstart.md`  

- [ ] T040‑verify Run the quickstart command in a test and assert that all listed result files are produced.  
  Path: `tests/integration/test_quickstart.py`

- [ ] T041 Draft a short “methods” markdown (`research.md`) that links each requirement (FR‑001 – FR‑006) to the concrete implementation files and output artifacts (e.g., “FR‑001 is satisfied by `code/preprocess.py::compute_d2_min`”).  
  Path: `research.md`  

- [ ] T041‑lint Verify that every FR‑001 – FR‑006 appears exactly once in `research.md`.  
  Path: `tests/unit/test_methods_coverage.py`

- [ ] T042 Create a handoff checklist (`paper/handshake.md`) summarizing where each scientific output lives (figures, tables, performance report) for the downstream paper‑generation stage.  
  Path: `paper/handshake.md`  

- [ ] T042‑verify Verify that `handshake.md` lists all files present in `data/processed/` and that each listed file exists.  
  Path: `tests/unit/test_handshake.py`

---

## Dependencies & execution order (summary)

| Phase | Tasks (must complete before) |
|------|-------------------------------|
| **Phase 1** (setup) | Enables all later phases. |
| **Phase 2** (data ingestion) | Required before **Phase 3**, **Phase 4**, **Phase 5**. |
| **Phase 3** (US 1) | Produces `precursor_metrics.csv` used by **Phase 4**. |
| **Phase 4** (US 2) | Needs `precursor_metrics.csv` and `shear_band_stats.csv`. |
| **Phase 5** (US 3) | Needs derived threshold (`derived_threshold.json`) and validation split (`validation_set_indices.json`). |
| **Phase 5** (performance) | Runs after **Phases 3‑5** are complete. |
| **Phase 6** (docs) | Can be done anytime after the corresponding artifacts exist. |

All **[P]** tasks have been reviewed for parallel safety; unsafe parallelism has been removed or reordered.  
