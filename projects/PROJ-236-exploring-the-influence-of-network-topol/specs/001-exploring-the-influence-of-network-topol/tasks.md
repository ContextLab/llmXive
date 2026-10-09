---
description: "Task list template for feature implementation"
---

# Tasks: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

**Input**: Design documents from `/specs/001-exploring-the-influence-of-network-topol/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/  
**Branch**: `001-gene-regulation`  
**Spec**: `specs/001-exploring-the-influence-of-network-topol/spec.md`

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3...)
- Include exact file paths in descriptions

## Phase 0: Documentation Alignment, Power Analysis Script & Pilot Data Planning

**Purpose**: Implement the power analysis script and runtime monitoring.

- [X] T000a [P] [FR-010] Implement `code/power_analysis.py` script to perform statistical power analysis for correlation detection (r≥0.3, power≥0.80). **Verification**: Script runs without error and outputs required sample size N.
- [ ] T000c [P] [FR-010] Verify that the sample size N produced by `code/power_analysis.py` achieves statistical power ≥ 0.80 for effect size r ≥ 0.3. **Verification**: Unit test `tests/unit/test_power_analysis.py::test_output_power` reads N from script output and checks power using `statsmodels.stats.power` utilities.
- [ ] T000d [P] [FR-010] Persist calculated sample size N to `code/power_analysis_output.txt`. **Verification**: Unit test `tests/unit/test_power_output_persistence.py::test_output_file_exists_and_correct`.
- [ ] T001b [P] [Orchestrator] Implement global runtime monitor in `code/orchestrator.py` to track total wall‑clock time of the ensemble execution and enforce a predefined temporal limit (SC-002). If total time > 6 h, log a warning and flag the sample size as potentially insufficient rather than failing the pipeline. **Verification**: CI assertion `tests/unit/test_runtime_monitor.py::test_warning_flag` that total runtime metric is logged; warning flag is set when > 6 h.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create project structure per implementation plan in `projects/PROJ-236-exploring-the-influence-of-network-topol/` by executing: `mkdir -p code/utils code/tests/unit code/tests/integration data/raw data/networks data/transport data/analysis plots state/projects`. **Verification**: Unit test `tests/unit/test_project_structure.py::test_directories_exist` asserts that each listed directory exists after execution.
- [X] T002 [P] Initialize Python 3 project with dependencies in `code/requirements.txt` including: `numpy`, `networkx`, `scipy`, `scikit-learn`, `pandas`, `matplotlib`, `seaborn`, `ase`, `pyyaml`, `pydantic`, `pytest`, `pytest-cov`, `ruff`, `black`, `mypy`, `pymatgen`. **Verification**: Run `pip install -r code/requirements.txt` and ensure exit code 0.
- [~] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`. **Verification**: Unit test `tests/unit/test_linting_config.py::test_ruff_black_config` runs `ruff --quiet` and `black --check` on the codebase; both must exit with no warnings/errors.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [~] T004 Setup configuration loader for `code/simulation_config.yaml` in `code/utils/io.py`. **Verification**: Unit test `tests/unit/test_io_config_loader.py::test_load_config` loads a sample config and asserts expected keys.
- [~] T005 Implement checksumming utility for `data/` artifacts in `code/utils/io.py`. **Verification**: Unit test `tests/unit/test_io_checksum.py::test_checksum_consistency` generates a file, computes checksum, recomputes, and matches.
- [~] T006 Create base logging infrastructure in `code/utils/logging.py`. **Verification**: Integration test `tests/integration/test_logging.py::test_logging_to_file` logs a message and checks that it appears in the designated log file.
- [~] T007 Create Pydantic base entities `NetworkRealization` and `TransportResult` in `code/utils/models.py`. **Verification**: Unit test `tests/unit/test_models.py::test_network_realization_validation` instantiates each model with valid data and expects no `ValidationError`.
- [~] T008 Setup random seed management (np.random.seed()) in `code/utils/seeds.py`. **Verification**: Unit test `tests/unit/test_seeds.py::test_reproducibility` sets a seed, generates random numbers, resets seed, and verifies reproducibility.
- [~] T009 Generate contract schema `contracts/network_realization.schema.yaml` describing the NetworkRealization data model. **Verification**: Unit test `tests/unit/test_contracts.py::test_network_schema_validates` validates a sample instance against the schema.
- [~] T010 Generate contract schema `contracts/transport_schema.schema.yaml` describing the TransportResult data model. **Verification**: Unit test `tests/unit/test_contracts.py::test_transport_schema_validates` validates a sample instance against the schema.
- [~] T011 Generate contract schema `contracts/analysis_schema.schema.yaml` describing the CorrelationAnalysis data model. **Verification**: Unit test `tests/unit/test_contracts.py::test_analysis_schema_validates` validates a sample instance against the schema.
- [~] T012 Implement distance‑based cutoff logic (x × nearest‑neighbor distance, retry up to 2.0×) in `code/generate_networks.py`. Tagged **[FR‑001]**. **Verification**: Unit test `tests/unit/test_cutoff_logic.py::test_scaling_behavior` checks scaling behavior for several factor values.
- [~] T014 Generate or fetch a small set of atomic coordinate seeds (XYZ/POSCAR files) representing disordered alloys for N = 500 atoms. Store in `data/raw/atomic_seeds/`. **Verification**: Unit test `tests/unit/test_seed_files.py::test_seed_files_checksum` checks each seed file's SHA‑256 against entries in `data/checksums.txt`.
- [~] T015 Implement Physical Stability Filter in `code/utils/validation.py` that checks bond‑distance thresholds (> 0.8 × nearest‑neighbor) and basic atomic stability. Consumes seeds from T014. **Verification**: Unit test `tests/unit/test_physical_stability.py::test_filter_pass_fail` with known valid/invalid structures.
- [~] T016 Implement explicit connectivity validation logic in `code/generate_networks.py` to ensure > 95 % of realizations are connected. Retries cutoff up to 2.0×; flags invalid realizations. **Verification**: Unit test `tests/unit/test_connectivity_validation.py::test_connectivity_rate` runs on a fixed seed and asserts ≥ 95 % connectivity.
- [ ] T017 Create CI script `ci/check_connectivity.sh` that enforces ≥ 95 % connectivity success rate. **Verification**: Unit test `tests/unit/test_connectivity_gate.py::test_connectivity_rate` that fails if rate < 95 %.
- [ ] T018 Create CI script `ci/check_physical_stability.sh` enforcing ≤ 5 % rejection by the Physical Stability Filter. **Verification**: Unit test `tests/unit/test_physical_stability_gate.py::test_rejection_rate`.
- [ ] T019 Create CI script `ci/check_cutoff_scaling.sh` asserting correct distance‑cutoff scaling behavior. **Verification**: Unit test `tests/unit/test_cutoff_scaling_gate.py::test_scaling_behavior`.
- [~] T020 Create CI script `ci/check_checksums.sh` for recomputation and verification of all `data/` artifact checksums. **Verification**: Unit test `tests/unit/test_checksum_verification.py::test_all_artifacts_checksum`.
- [ ] T030 [Merged T030/T030b] Implement EAM force constant derivation from atomic seeds (T014) and store in `data/processed/force_constants/`. Ensure derivation is independent of graph topology. **Verification**: Unit test `tests/unit/test_force_constants_derivation.py::test_non_negative_and_independent` checks non‑negativity, magnitude, and independence from topology.
- [ ] T031 Implement **Allen‑Feldman theory** solver core in `code/compute_transport.py` (reads `data/networks/*.graphml`, uses force constants, computes VDOS, applies Allen‑Feldman diffusivity formula, converts to W/mK). **Verification**: Integration test `tests/integration/test_compute_transport.py::test_1d_chain_kappa` runs on a 1D chain benchmark and checks κ within 10 % of literature value, runtime ≤ 45 min, AND verifies solver stability under varying cutoff conditions defined in the sensitivity sweep (FR-008).
- [ ] T031b Implement NEMD fallback and regime detection logic in `code/compute_transport.py`. Detect ballistic regimes (e.g., high‑degree hubs, **low clustering indicative of ballistic transport**) and switch to a simplified NEMD solver or flag Green‑Kubo as invalid per FR‑011. **Verification**: Unit test `tests/unit/test_regime_detection.py::test_nemd_switch_triggered` with low-clustering inputs and high-degree hub inputs.
- [ ] T031c Implement sensitivity analysis stability check for Allen-Feldman solver under varying cutoff conditions (FR-008). **Verification**: Unit test `tests/unit/test_sensitivity_stability.py::test_solver_stability` confirms convergence across cutoff sweep.
- [ ] T032 Implement convergence check and retry logic (max limited retries with adjusted solver parameters). **Verification**: Unit test `tests/unit/test_convergence_retry.py::test_retry_success`.

## Phase 3: User Story 1 - Construct and Validate Network Realizations (Priority: P1) 🎯 MVP

**Goal**: Generate reproducible ensembles of Small‑World, Scale‑Free, and Random atomic connectivity networks with distance‑based cutoffs and topological sanity checks.

- [~] T021 [P] [US1] Implement Small‑World (Watts‑Strogatz) graph generator in `code/generate_networks.py` (depends on T012). **Verification**: Unit test `tests/unit/test_small_world.py::test_clustering_within_tolerance`.
- [~] T022 [P] [US1] Implement Scale‑Free (Barabási‑Albert) graph generator in `code/generate_networks.py` (depends on T012). **Verification**: Unit test `tests/unit/test_scale_free.py::test_degree_exponent_range`.
- [~] T023 [P] [US1] Implement Random (Erdős‑Rený) graph generator in `code/generate_networks.py` (depends on T012). **Verification**: Unit test `tests/unit/test_random_graph.py::test_average_path_length_tolerance`.
- [~] T024 [P] [US1] [FR‑003] Implement topological metric extraction (clustering, degree variance, spectral gap, betweenness) in `code/generate_networks.py`. **Verification**: Unit test `tests/unit/test_metric_extraction.py::test_metrics_computed`.
- [ ] T025 [P] [US1] [DEPENDS ON T000d] Ensemble generation loop with meta‑logging and cutoff sweep. **Verification**: Integration test `tests/integration/test_ensemble_generation.py::test_meta_logging` checks `meta.json` entries for each realization and confirms cutoff sweep recording.
- [~] T025b [P] [US1] Sensitivity analysis orchestrator in `code/generate_networks.py` that iterates through cutoff values from the cutoff sweep defined in T025, generates networks, and prepares data for transport calculation. **Verification**: Integration test `tests/integration/test_sensitivity_sweep.py::test_sweep_outputs_csv` asserts existence and correctness of `data/analysis/sensitivity_metadata.csv`.
- [~] T026 [P] Enforce connectivity success rate ≥ 95 % (hard gate). **Verification**: CI step `ci/enforce_connectivity_rate.sh` and unit test `tests/unit/test_connectivity_enforcement.py::test_hard_gate`.
- [ ] T027 [P] Record generated graph checksums in `state/projects/PROJ-236-exploring-the-influence-of-network-topol.yaml`. **Verification**: Unit test `tests/unit/test_checksum_record.py::test_checksum_recorded`.
- [ ] T028 [P] Generate pilot dataset CSV `data/processed/pilot_data/pilot_metrics.csv` (metrics only, no transport). **Verification**: Unit test `tests/unit/test_pilot_dataset.py::test_pilot_csv_structure`.
- [~] T059 [P] Unit test for clustering‑coefficient accuracy. **Verification**: Unit test `tests/unit/test_network_metrics.py::test_clustering_coefficient_accuracy`.
- [~] T060 [P] Unit test for connectivity retry logic. **Verification**: Unit test `tests/unit/test_network_metrics.py::test_connectivity_retry_logic`.
- [~] T061 [P] Integration test for full network ensemble with physical filter. **Verification**: Integration test `tests/integration/test_network_ensemble.py::test_ensemble_with_physical_filter`.

## Phase 4: User Story 2 - Compute Phonon Transport and Thermal Conductivity (Priority: P2)

**Goal**: Calculate effective thermal conductivity (κ) for each network realization using Allen‑Feldman theory (CPU-tractable) with EAM-derived force constants, ensuring CPU-only execution.

- [ ] T025c [P] [US2] [DEPENDS ON T031] Sensitivity Analysis Transport Loop: iterate through cutoff values from T025b, invoke transport calculation (T031/T031b) for each cutoff, and aggregate results into `data/analysis/sensitivity_results.csv`. **Verification**: Integration test `tests/integration/test_transport_sweep.py::test_all_cutoffs_present` confirms a row for every cutoff value.
- [~] T033 [P] [US2] Abort if runtime per realization exceeds a predefined acceptable duration. **Verification**: CI script `ci/check_runtime_limit.sh` and unit test `tests/unit/test_runtime_limit.py::test_all_runtimes_within_limit`.
- [~] T034 [P] [US2] Aggregate total ensemble runtime and enforce ≤ 6 h using orchestrator monitor (T001b). **Verification**: CI script `ci/check_total_runtime.sh` and unit test `tests/unit/test_total_runtime.py::test_total_runtime_within_limit`.
- [ ] T035 [P] [US2] Save transport results to `data/transport/transport_results.csv` with metadata columns `[network_id, kappa, error_estimate, convergence_status, runtime, regime_flag]`. **Verification**: Unit test `tests/unit/test_transport_output.py::test_csv_columns`.
- [~] T036 [P] [US2] Verify that all κ values are finite real numbers and that no singular‑matrix or convergence‑failure errors remain unflagged. **Verification**: Unit test `tests/unit/test_finite_transport_values.py::test_all_finite`.

## Phase 5: User Story 3 - Analyze Topology‑Transport Correlations (Priority: P3)

**Goal**: Perform statistical regression analyses between network metrics and thermal conductivity, including bootstrap resampling, multiple‑comparison correction, and hypothesis testing.

- [ ] T037 [P] [US3] Implement linear regression and correlation coefficient calculation in `code/analyze_correlations.py`. Save results to `data/analysis/correlation_results.csv`. **Verification**: Unit test `tests/unit/test_correlation_analysis.py::test_output_columns`.
- [ ] T038 [P] [US3] Implement bootstrap resampling with **≥ 1000 iterations** for confidence intervals. **Verification**: Unit test `tests/unit/test_bootstrap_iterations.py::test_iteration_count`.
- [~] T039 [P] [US3] CI check that bootstrap confidence‑interval width ≤ 0.2. **Verification**: CI script `ci/check_bootstrap_width.sh` and unit test `tests/unit/test_bootstrap_width.py::test_width_within_threshold`.
- [ ] T040 [P] [US3] Implement multiple‑comparison correction (Bonferroni/FDR) for p‑values (FR‑005). **Verification**: Unit test `tests/unit/test_multiple_comparison_correction.py::test_correction`.
- [~] T041 [P] [US3] CI check verifying corrected p‑values for significant metrics are < 0.05 (SC‑003). **Verification**: CI script `ci/check_corrected_pvalues.sh` and unit test `tests/unit/test_corrected_pvalues.py::test_all_significant_corrected`.
- [ ] T042 [P] [US3] Implement power‑law fit between disorder parameters and conductivity, compute R², and perform **F-test or permutation test against the null hypothesis (R² = 0)** at α = 0.05 (SC‑005). **Verification**: Unit test `tests/unit/test_power_law_fit.py::test_significant_r2` validates the null hypothesis test procedure.
- [~] T043 [P] [US3] Stability test: verify that correlation coefficient variance across cutoff sweep is below defined threshold (FR‑008). **Verification**: CI script `ci/check_correlation_stability.sh` and unit test `tests/unit/test_correlation_stability.py::test_variance_below_threshold`.
- [ ] T044 [P] [US3] Generate publication‑ready scatter plots (`data/analysis/plots/metric_vs_kappa.png`) with error bars representing bootstrap confidence intervals. **Verification**: Unit test `tests/unit/test_plot_generation.py::test_scatter_plot_exists`.
- [ ] T045 [P] [US3] Generate power‑law fit plot (`data/analysis/plots/powerlaw_fit.png`) with R² annotation. **Verification**: Unit test `tests/unit/test_plot_generation.py::test_powerlaw_plot_exists`.
- [~] T046 [P] [US3] Save analysis summary (`research.md` appendix) ensuring all statements use associational language only. **Verification**: Unit test `tests/unit/test_research_md_lint.py::test_no_causal_language`.

## Phase N: Polish & Cross‑Cutting Concerns

- [~] T048 [P] Update `quickstart.md` with execution instructions for the full pipeline. **Verification**: CI step `ci/check_quickstart_md.sh` using `markdownlint`; all commands must execute without error on a fresh CI run.
- [~] T049 [P] Code cleanup and refactoring for type‑hint consistency. Run `mypy --strict` and assert exit code 0. **Verification**: CI step `ci/run_mypy.sh`.
- [~] T050 [P] Performance optimization: implement multiprocessing in `code/generate_networks.py` for ensemble generation. **Verification**: Benchmark script `benchmarks/generate_networks_benchmark.py` and CI step `ci/check_performance.sh` require ≥ 10 % speedup compared to single‑process baseline.
- [~] T051 [P] Add edge‑case unit tests (zero variance, disconnected graphs) in `tests/unit/` and verify coverage ≥ 90 % for edge‑case branches. **Verification**: CI step `ci/check_coverage.sh` must report ≥ 90 % coverage for specified files.
- [~] T052 [P] Validate final artifact hashes and update `state/projects/PROJ-236-exploring-the-influence-of-network-topol.yaml` `artifact_hashes` map accordingly. **Verification**: Script `scripts/update_artifact_hashes.py` and CI test `ci/check_artifact_hashes.sh` ensure the map matches recomputed hashes.
- [ ] T068 [P] Record random seeds, algorithm identifiers, and cutoff parameters for each generated graph in `data/metadata/graph_manifest.json` to satisfy Principle VII. **Verification**: Unit test `tests/unit/test_graph_manifest.py::test_manifest_contents`.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T069 Reconcile run-book vs implementation for `code/01_generate_networks.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/01_generate_networks.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T070 Reconcile run-book vs implementation for `code/02_compute_transport.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/02_compute_transport.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T071 Reconcile run-book vs implementation for `code/03_analyze_correlations.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/03_analyze_correlations.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
