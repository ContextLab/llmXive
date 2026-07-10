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

- [ ] T000a [P] [FR-010] Implement `code/power_analysis.py` script to perform statistical power analysis for correlation detection (r≥0.3, power≥0.80). **Verification**: Script runs without error and outputs required sample size N.
- [ ] T000c [P] [FR-010] Verify that the sample size N produced by `code/power_analysis.py` achieves statistical power ≥ 0.80 for effect size r ≥ 0.3. **Verification**: Unit test that reads N from script output and checks power using `statsmodels.stats.power` utilities.
- [X] T001b [P] [Orchestrator] Implement global runtime monitor in `code/orchestrator.py` to track total wall‑clock time of the ensemble execution and enforce a predefined temporal limit (SC-002). If total time > 6 hours, log a warning and flag the sample size as potentially insufficient rather than failing the pipeline. **Verification**: CI assertion that total runtime metric is logged; if > 6h, a warning flag is set but the run is not aborted.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create project structure per implementation plan in `projects/PROJ-236-exploring-the-influence-of-network-topol/` by executing: `mkdir -p code/utils code/tests/unit code/tests/integration data/raw data/networks data/transport data/analysis plots state/projects`. **Verification**: Assert that each listed directory exists after execution.
- [X] T002 [P] Initialize Python 3 project with dependencies in `code/requirements.txt` including: `numpy`, `networkx`, `scipy`, `scikit-learn`, `pandas`, `matplotlib`, `seaborn`, `ase`, `pyyaml`, `pydantic`, `pytest`, `pytest-cov`, `ruff`, `black`, `mypy`. **Verification**: Run `pip install -r code/requirements.txt` and ensure exit code 0.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`. **Verification**: Run `ruff --quiet` and `black --check` on the codebase; both must exit with no warnings/errors.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [~] T004 [P] Setup configuration loader for `code/simulation_config.yaml` in `code/utils/io.py`. **Verification**: Unit test that loads a sample config and asserts expected keys.
- [~] T005 [P] Implement checksumming utility for `data/` artifacts in `code/utils/io.py`. **Verification**: Unit test that generates a file, computes checksum, recomputes, and matches.
- [~] T006 [P] Create base logging infrastructure in `code/utils/logging.py`. **Verification**: Integration test that logs a message and checks that it appears in the designated log file.
- [ ] T007 [P] Create Pydantic base entities `NetworkRealization` and `TransportResult` in `code/utils/models.py`. **Verification**: Unit test (`T007‑UT`) that instantiates each model with valid data and expects no `ValidationError`.
- [ ] T008 [P] Setup random seed management (np.random.seed()) in `code/utils/seeds.py`. **Verification**: Unit test that sets a seed, generates random numbers, resets seed, and verifies reproducibility.
- [ ] T009 [P] Generate contract schema `contracts/network_realization.schema.yaml` describing the NetworkRealization data model. **Verification**: File exists and validates against a sample instance.
- [ ] T010 [P] Generate contract schema `contracts/transport_schema.schema.yaml` describing the TransportResult data model. **Verification**: File exists and validates against a sample instance.
- [ ] T011 [P] Generate contract schema `contracts/analysis_schema.schema.yaml` describing the CorrelationAnalysis data model. **Verification**: File exists and validates against a sample instance.
- [ ] T012 [P] Implement distance‑based cutoff logic (x × nearest‑neighbor distance, retry up to 2.0×) in `code/generate_networks.py`. [UNRESOLVED-CLAIM: c_061126a7 — status=not_enough_info] Tagged **[FR‑001]**. **Verification**: Unit test (`T012‑UT`) that checks scaling behavior for several factor values.
- [ ] T014 [P] Generate or fetch a small set of atomic coordinate seeds (XYZ/POSCAR files) representing disordered alloys for N = 500 atoms. [UNRESOLVED-CLAIM: c_a8088e57 — status=not_enough_info] Store in `data/raw/atomic_seeds/`. **Verification**: Ensure at least 5 seed files exist and each passes a SHA‑256 checksum recorded in `data/checksums.txt`. [UNRESOLVED-CLAIM: c_7a192160 — status=not_enough_info]
- [ ] T015 [P] Implement Physical Stability Filter in `code/utils/validation.py` that checks bond‑distance thresholds (> 0.8 × nearest‑neighbor) and basic atomic stability. [UNRESOLVED-CLAIM: c_84f9b737 — status=not_enough_info] Consumes seeds from T014. **Verification**: Unit test (`T015‑UT`) with known valid/invalid structures.
- [ ] T016 [P] Implement explicit connectivity validation logic in `code/generate_networks.py` to ensure > 95% of realizations are connected. [UNRESOLVED-CLAIM: c_ef757304 — status=not_enough_info] Retries cutoff up to 2.0×; flags invalid realizations. **Verification**: Unit test (`T016‑UT`) that runs on a fixed seed and asserts ≥95% connectivity.
- [ ] T017 [P] Verification CI gate for connectivity: CI fails if overall connectivity success rate < 95% after all retries. **Verification**: CI script that reads connectivity metrics and aborts on failure.
- [ ] T018 [P] Verification for Physical Stability Filter: CI fails if > 5% of seeds are rejected by the filter. **Verification**: CI check on filter pass rate.
- [ ] T019 [P] Verification for distance‑cutoff logic: CI fails if cutoff scaling does not match expected behavior (e.g., a scaling factor that leaves the original NN distance unchanged). **Verification**: CI assertion based on `T012‑UT` results.
- [ ] T020 [P] Verification for checksumming utility: recompute checksum for each saved artifact and compare to recorded value. **Verification**: Automated test that loops over `data/` files.

---

## Phase 3: User Story 1 - Construct and Validate Network Realizations (Priority: P1) 🎯 MVP

**Goal**: Generate reproducible ensembles of Small‑World, Scale‑Free, and Random atomic connectivity networks with distance‑based cutoffs and topological sanity checks.

- [ ] T021 [P] [US1] Implement Small‑World (Watts‑Strogatz) graph generator in `code/generate_networks.py` (depends on T012). **Verification**: Unit test that generated graph matches target clustering coefficient within 5%.
- [ ] T022 [P] [US1] Implement Scale‑Free (Barabási‑Albert) graph generator in `code/generate_networks.py` (depends on T012). **Verification**: Unit test that median degree‑exponent falls within 2 < γ < 3.
- [ ] T023 [P] [US1] Implement Random (Erdős‑Rényi) graph generator in `code/generate_networks.py` (depends on T012). **Verification**: Unit test that average path length is within 10% of theoretical expectation.
- [ ] T024 [P] [US1] [FR‑003] Implement topological metric extraction (clustering, degree variance, spectral gap, betweenness) in `code/generate_networks.py`. **Verification**: Unit test that metrics are computed and saved for a sample graph.
- [ ] T025 [P] [US1] Implement ensemble generation loop with `meta.json` logging for each realization in `code/generate_networks.py`. Includes regular cutoff sweep as defined in `simulation_config.yaml` (FR‑008). [UNRESOLVED-CLAIM: c_722c4c58 — status=not_enough_info] **Verification**: Integration test that generates a mini‑ensemble (multiple realizations per topology) and produces correct meta logs.
- [ ] T025b [P] [US1] Implement sensitivity analysis orchestrator in `code/generate_networks.py` that iterates through cutoff values, generates networks, and prepares data for the transport calculation for each cutoff to ensure the full topology-transport correlation is tested. **Verification**: Integration test that runs the full sweep for multiple cutoffs and produces a CSV of network metadata.
- [ ] T025c [P] [US1] [FR-008] Implement the Sensitivity Analysis Transport Loop: explicitly iterate through cutoff values from T025b, invoke the transport calculation (T031/T031b) for each cutoff value, and aggregate results into `data/analysis/sensitivity_results.csv`. **Verification**: Integration test that confirms transport results exist for every cutoff value in the sweep.
- [ ] T026 [P] [US1] Enforce connectivity success rate ≥ 95% (hard gate). [UNRESOLVED-CLAIM: c_36e8fdea — status=not_enough_info] If rate falls below, abort ensemble generation and log failing IDs. **Verification**: CI check (see T017) validates this constraint.
- [ ] T027 [P] [US1] Save generated graphs to `data/networks/` and record checksums in `state/projects/PROJ-236-exploring-the-influence-of-network-topol.yaml`. **Verification**: Re‑compute checksum after save and compare to stored value (see T020).
- [ ] T028 [P] [Pilot] Generate pilot dataset of multiple realizations per topology (Small‑World, Scale‑Free, Random) with metrics only (no transport). Output CSV `data/processed/pilot_data/pilot_metrics.csv`. **Verification**: File exists, contains expected number of rows, and includes columns `[network_id, topology_type, cutoff, clustering_coeff]`.
- [ ] T059 [P] [US1] Unit test for network topology metrics (clustering, path length) in `tests/unit/test_network_gen.py`. **Function**: `test_clustering_coefficient_accuracy`. **Verification**: Test must pass after implementation.
- [ ] T060 [P] [US1] Unit test for connectivity retry logic in `tests/unit/test_network_gen.py`. **Function**: `test_connectivity_retry_logic`. **Verification**: Test must pass after implementation.
- [ ] T061 [P] [US1] Integration test for ensemble generation with physical validity filter in `tests/integration/test_network_ensemble.py`. **Function**: `test_ensemble_generation_with_filter`. **Verification**: Test must pass after implementation.

---

## Phase 4: User Story 2 - Compute Phonon Transport and Thermal Conductivity (Priority: P2)

**Goal**: Calculate effective thermal conductivity (κ) for each network realization using Allen-Feldman theory (CPU-tractable variant of ALD) with EAM-derived force constants, ensuring CPU-only execution.

- [ ] T030 [P] [US2] Derive force constants via **EAM potentials** from atomic seeds (T014). Output stored in `data/processed/force_constants/`. **Verification**: Unit test that force constants are non‑negative and within expected magnitude range.
- [ ] T030b [P] [US2] Explicitly implement the derivation of force constants from atomic positions using an EAM-like potential (independent of graph topology) to satisfy FR-009. **Verification**: Unit test that verifies force constants are derived solely from atomic species and positions, not graph edges.
- [ ] T031 [P] [US2] Implement **Allen-Feldman theory** solver core in `code/compute_transport.py` (reads `data/networks/*.graphml`, uses force constants, computes vibrational density of states (VDOS), applies Allen-Feldman diffusivity formula, converts to W/mK). [UNRESOLVED-CLAIM: c_f48bc16f — status=not_enough_info] **Methodology**: Uses Allen-Feldman theory as the CPU-tractable implementation for disordered systems, avoiding third-order force constants. **Verification**: Integration test (`T031‑UT`) that runs on a 1D chain benchmark and checks κ is within 10% of literature value.
- [ ] T031b [P] [US2] Implement NEMD fallback and regime detection logic in `code/compute_transport.py`. Detects ballistic regimes (e.g., high-degree hubs, low clustering) and switches to a simplified NEMD solver (Langevin thermostat on harmonic chain) or flags Green-Kubo as invalid per FR-011. **Verification**: Unit test that forces a ballistic regime and verifies the NEMD switch is triggered and a valid result is returned.
- [ ] T032 [P] [US2] Implement convergence check and retry logic (max a limited number of retries with adjusted solver parameters). **Verification**: Unit test that forces a convergence failure on first attempt and succeeds on retry.
- [ ] T033 [P] [US2] Enforce per‑realization runtime ≤ 45 minutes. [UNRESOLVED-CLAIM: c_c877bbb6 — status=not_enough_info] If exceeded, abort and flag realization as failed. **Verification**: CI assertion that recorded runtimes for all realizations are ≤ 45 min.
- [ ] T034 [P] [US2] Aggregate total ensemble runtime and enforce ≤ 6 hours (SC‑002) using orchestrator monitor (T001b). [UNRESOLVED-CLAIM: c_b4c4436d — status=not_enough_info] If limit exceeded, log warning and flag sample size as insufficient. **Verification**: CI check that total runtime metric is logged; if > 6h, a warning flag is set.
- [ ] T035 [P] [US2] Save transport results to `data/transport/transport_results.csv` with metadata columns `[network_id, kappa, error_estimate, convergence_status, runtime, regime_flag]`. **Verification**: Unit test that output file contains required columns and that `regime_flag` is set appropriately.
- [ ] T036 [P] [US2] Verify that all κ values are finite real numbers and that no singular‑matrix or convergence‑failure errors remain unflagged. **Verification**: CI test that scans `transport_results.csv` for non‑finite entries and fails if any are found.

---

## Phase 5: User Story 3 - Analyze Topology‑Transport Correlations (Priority: P3)

**Goal**: Perform statistical regression analyses between network metrics and thermal conductivity, including bootstrap resampling, multiple‑comparison correction, and hypothesis testing.

- [ ] T037 [P] [US3] Implement linear regression and correlation coefficient calculation in `code/analyze_correlations.py`. Save results to `data/analysis/correlation_results.csv`. [UNRESOLVED-CLAIM: c_a5ed33ba — status=not_enough_info] **Verification**: Unit test (`T037‑UT`) that reads the CSV and checks for columns `metric, r, p_value, slope, intercept`.
- [ ] T038 [P] [US3] Implement bootstrap resampling with **≥ 1000 iterations** for confidence intervals. [UNRESOLVED-CLAIM: c_b80e96ca — status=not_enough_info] **Verification**: Unit test (`T038‑UT`) that asserts the iteration count used is ≥ 1000.
- [ ] T039 [P] [US3] Verify that bootstrap confidence‑interval width ≤ 0.2 (SC‑004). [UNRESOLVED-CLAIM: c_2f9fa22d — status=not_enough_info] If width exceeds, fail the pipeline. **Verification**: CI check that computes width from bootstrap results and aborts on violation.
- [ ] T040 [P] [US3] Implement multiple‑comparison correction (Bonferroni/FDR) for p‑values (FR‑005). [UNRESOLVED-CLAIM: c_4059b3ee — status=not_enough_info] **Verification**: Unit test that applies correction to a known set of p‑values and checks transformed values.
- [ ] T041 [P] [US3] Verify that corrected p‑values for significant metrics are < 0.05 (SC‑003). [UNRESOLVED-CLAIM: c_1edb6655 — status=refuted] **Verification**: CI assertion that scans corrected p‑values and fails if any significant metric does not meet the threshold.
- [ ] T042 [P] [US3] Implement power‑law fit between disorder parameters and conductivity, compute R², and perform hypothesis test rejecting null (R² = 0) at α = 0.05 (SC‑005). [UNRESOLVED-CLAIM: c_80f958ab — status=not_enough_info] **Verification**: Unit test that the test statistic is significant (p < 0.05) for synthetic data with known relationship.
- [ ] T043 [P] [US3] Sensitivity analysis across cutoffs: verify that correlation coefficient remains stable (variance below a defined threshold) across the regular‑increment sweep (FR‑008). **Requirement**: Must analyze the correlation stability using results from T025c (which re-runs the transport calculation for each cutoff). **Verification**: CI test that computes variance of r across cutoffs and fails if above threshold.
- [ ] T044 [P] [US3] Generate publication‑ready scatter plots (`data/analysis/plots/metric_vs_kappa.png`) with error bars representing bootstrap confidence intervals. [UNRESOLVED-CLAIM: c_401f17dc — status=not_enough_info] **Verification**: Render check that the PNG file is created and non‑empty.
- [ ] T045 [P] [US3] Generate power‑law fit plot (`data/analysis/plots/powerlaw_fit.png`) with R² annotation. [UNRESOLVED-CLAIM: c_74da123b — status=not_enough_info] **Verification**: Render check that the PNG file exists.
- [ ] T046 [P] [US3] Save analysis summary (`research.md` appendix) ensuring all statements use associational language only. **Verification**: Linting test that scans the generated text for prohibited causal keywords (`cause`, `drive`, etc.) and fails if any are found.
- [ ] T063 [P] [US3] Unit test for bootstrap implementation in `tests/unit/test_analysis.py`. **Function**: `test_bootstrap_iterations_count`. **Verification**: Test must pass.
- [ ] T064 [P] [US3] Unit test for FDR/Bonferroni correction logic in `tests/unit/test_analysis.py`. **Function**: `test_fdr_correction_values`. **Verification**: Test must pass.
- [ ] T065 [P] [US3] Unit test for VIF multicollinearity check in `tests/unit/test_analysis.py`. **Function**: `test_vif_multicollinearity_check`. **Verification**: Test must pass.
- [ ] T066 [P] [US3] Integration test for full correlation pipeline with known synthetic data in `tests/integration/test_correlation_pipeline.py`. **Function**: `test_full_correlation_pipeline_synthetic`. **Verification**: Test must pass.

---

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T048 [P] Update `quickstart.md` with execution instructions for the full pipeline. **Verification**: Render markdown with a linter; all commands execute without error in a fresh CI run.
- [ ] T049 [P] Code cleanup and refactoring for type‑hint consistency. Run `mypy --strict` and assert exit code 0. **Verification**: CI step runs mypy and must pass.
- [ ] T050 [P] Performance optimization: implement multiprocessing in `code/generate_networks.py` for ensemble generation. **Verification**: Benchmark before/after; require ≥ 10% speedup and assert new runtime ≤ previous * 0.9.
- [ ] T051 [P] Add edge‑case unit tests (zero variance, disconnected graphs) in `tests/unit/` and verify coverage ≥ 90% for edge‑case branches. [UNRESOLVED-CLAIM: c_ec093cf0 — status=not_enough_info] **Verification**: Coverage report must show ≥ 90% for specified files.
- [ ] T052 [P] Validate final artifact hashes and update `state/projects/PROJ-236-exploring-the-influence-of-network-topol.yaml` `artifact_hashes` map accordingly. **Verification**: Script recomputes hashes, updates YAML, and CI checks that the map matches computed values.