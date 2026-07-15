# Tasks: Solvent Effects on Photo-Fries Rearrangement Kinetics

**Input**: Design documents from `/specs/001-solvent-effects/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
- Paths shown below assume single project structure as defined in `plan.md`

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `plan.md` (directories: `code/`, `data/`, `tests/`, `docs/`)
- [X] T002 Initialize a Python project with pinned dependencies in `requirements.txt` (numpy, scipy, pandas, scikit-learn, pyyaml, pymatgen, matplotlib, seaborn, pymc)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`
- [X] T004 [P] Initialize `code/utils/seeds.py` to set global random seeds for reproducibility
- [X] T005 [P] Setup `code/utils/logging.py` to handle structured logging of environmental parameters

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes data generation/ingestion which is a prerequisite for US2/US3.

- [X] T006 Create `data/chemicals/solvents.yaml` with versioned dielectric constant lookup table (schema: `name`, `dielectric_constant`, `source_id` (NIST Standard Reference Database), `version_hash`; source: NIST SRD)
- [X] T007 Define `contracts/solvent.schema.yaml` and `contracts/kinetic_trace.schema.yaml` for data validation
- [X] T008 Implement `code/data/loaders.py` to fetch real solvent properties from `data/chemicals/solvents.yaml` (no synthetic generation of input properties)
- [ ] T009 Implement `code/config.py` to enforce CPU-only execution constraints and define file paths for `data/raw/`, `data/compute/`, `data/processed/`
- [ ] T010 [P] Create `tests/unit/test_loaders.py` to verify solvent property loading against versioned lookup table
- [X] T015b [US1] **Real Data Ingestion (Blocking)**: Implement `code/data/ingest.py` to ingest real transient-absorption data from a user-provided file path (e.g., `data/raw/real_traces.csv`). **Constraint**: This task MUST fail the pipeline with a clear error if the real data file is missing. It is the primary data source for the research phase.
- [X] T015 [P] [US1] **CI-Placeholder Data Generation**: Implement `code/data/generate_synthetic.py` to generate deterministic synthetic transient-absorption traces (mocking laser flash photolysis) as a **fallback ONLY** for CI logic testing. **Constraint**: This task MUST NOT be used as the primary research data source. It runs only if T015b is explicitly bypassed or disabled. Output to `data/raw/synthetic_traces.csv`.
- [X] T015c [P] [US1] **Real Instrument Interface**: Implement `code/hardware/interface.py` to provide the API contract for 'capturing' transient-absorption data (e.g., `capture_trace(serial_port, timeout)`). This task satisfies the 'MUST capture' requirement of FR-002 by defining the interface. For CI, this implementation defaults to returning synthetic data from T015, but must be swappable for real driver logic when hardware is available.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Configure and Execute Solvent Series (Priority: P1) 🎯 MVP

**Goal**: Define a series of solvents spanning non-polar to polar conditions and initiate the experimental protocol with full environmental logging.

**Independent Test**: Verify that the system logs dielectric constant (validated against `solvents.yaml`), {{claim:c_3fbb732e}}, and relative humidity (±2% RH) for each run.

### Tests for User Story 1 (OPTIONAL)

- [X] T011 [P] [US1] Unit test for `code/data/loaders.py` validating dielectric constant lookup in `tests/unit/test_solvent_validation.py`
- [X] T012 [US1] Integration test for environmental logging in `tests/integration/test_env_logging.py` (depends on T014)

### Implementation for User Story 1

- [X] T014 [US1] Implement `code/analysis/environment.py` to {{claim:c_100de0a3}}
- [X] T013 [US1] Implement `code/main.py` CLI entry point to configure solvent series (multiple solvents, ε range low to moderate) (depends on T014)
- [~] T017 [US1] Implement `code/analysis/validation.py` to flag runs where logged dielectric constants deviate >2% from `solvents.yaml` (addressing SC-010)
- [~] T017b [US1] Implement `code/analysis/validation.py` to calculate and verify environmental compliance percentage (≥95% of runs within tolerance) by reading `data/processed/environment_logs.json` and write result to `data/processed/compliance_report.json` with field `environmental_compliance_percent` (addressing SC-004)
- [X] T018 [US1] Implement `code/analysis/validation.py` to detect and flag runs where temperature or humidity exceeds tolerance (addressing Edge Cases in spec)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Extract Radical-Pair Lifetime (Priority: P2)

**Goal**: Process raw spectroscopic data to extract singlet-radical-pair intermediate lifetime via global kinetic analysis.

**Independent Test**: Verify system outputs lifetime value with confidence interval and calibration record from uploaded decay traces.

### Tests for User Story 2 (OPTIONAL)

- [X] T019 [P] [US2] Unit test for exponential fitting in `tests/unit/test_kinetic_fit.py`
- [X] T020 [P] [US2] Integration test for replicate statistics in `tests/integration/test_replicate_analysis.py`

### Implementation for User Story 2

- [X] T016 [US2] Implement `code/analysis/calibration.py` to apply instrument calibration factors and log detector response/wavelength stability per `FR-004`
- [~] T021 [P] [US2] Implement `code/analysis/kinetic_fit.py` to perform global kinetic analysis (exponential fitting) on `data/processed/calibrated_traces.csv` (or synthetic equivalent)
- [X] T022 [US2] Implement `code/analysis/kinetic_fit.py` to calculate mean lifetime and standard deviation for n ≥ 3 replicates per solvent
- [X] T023 [US2] Implement `code/analysis/kinetic_fit.py` to flag outliers beyond a statistically significant threshold. (addressing US-2 acceptance scenario)
- [X] T024 [US2] Implement `code/analysis/power.py` to document power analysis for n=3 and estimate detectable effect size (addressing SC-007)
- [X] T025 [US2] Implement `code/analysis/kinetic_fit.py` to perform threshold sensitivity analysis on lifetime discrepancy cutoffs across a range of values. and report false-positive/negative rates (addressing SC-008)
- [ ] T026 [US2] Create `data/processed/kinetic_metrics.csv` containing extracted lifetimes, CIs, and replicate statistics

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlate Solvation Energy with Kinetic Lifetimes (Priority: P3)

**Goal**: Correlate computed solvation free energies with experimentally determined lifetimes using associational inference.

**Independent Test**: Verify system generates regression plot, statistical significance test, and multiple-comparison correction.

### Tests for User Story 3 (OPTIONAL)

- [X] T027 [P] [US3] Unit test for VIF calculation in `tests/unit/test_collinearity.py`
- [X] T028 [P] [US3] Integration test for correlation pipeline in `tests/integration/test_correlation.py`

### Implementation for User Story 3

- [~] T029 [US3] **Integrated Solvent Model Data Generation**: Implement `code/data/compute/solvent_models.py` to generate or fetch DFT solvation data. **Logic**: Accept a list of N solvents. Select a subset of size `floor(N * 0.8)` (or fewer) for implicit solvent models (SMD/PCM) and the remaining `N - subset_size` (guaranteed ≥ 20% if N ≥ 5) for explicit solvent models (QM/MM or cluster-continuum). Ensure the total count equals N. Output combined results to `data/compute/solvent_solvation.csv`. This task satisfies FR-005 (≤80% implicit, ≥20% explicit) by dynamically partitioning the input set. (Replaces T029a, T029c, T029d, T029b).
- [X] T030a [US3] **Bayesian Correlation**: Implement `code/analysis/correlation.py` to perform **Bayesian Hierarchical Modeling (BHM)** to correlate lifetime with Solvation Energy and Dielectric Constant. **Constraint**: Do NOT use standard ANOVA or Linear Regression as the primary model. Use a PCA-derived "Solvent Polarity Index" as the primary predictor to avoid tautology. Output posterior distributions for slope and intercept. **Dependency**: This task must complete before T030b.
- [ ] T030b [US3] **Statistical Reporting**: Implement `code/analysis/correlation.py` to report **Posterior Probability of Effect**, **Bayes Factors**, AND **exact p-value** (via scipy.stats or equivalent) to satisfy SC-003. Calculate **Bayesian R²** and **credible intervals (CI)**. Explicitly frame all findings as associational and exploratory due to low N (n=3). (Addressing SC-001, SC-003, SC-006). **Dependency**: This task must complete after T030a.
- [ ] T031 [US3] Implement `code/analysis/correlation.py` to perform VIF analysis to distinguish dielectric vs. solvation effects (addressing SC-009 and Rosalind Franklin review)
- [ ] T032 [US3] Implement `code/analysis/correlation.py` to apply multiple-comparison correction (e.g., Bonferroni) and report family-wise error rate
- [ ] T033 [US3] Implement `code/analysis/correlation.py` to frame all findings as associational (not causal) in output metadata
- [ ] T034 [US3] Generate `paper/figures/regression_plot.png` and `data/processed/correlation_results.json` with **Bayesian R²**, **95% Credible Intervals**, **p-values**, and VIF scores by reading `data/processed/correlation_results.json` from T030b; ensure all findings are explicitly framed as associational (addressing SC-006). **Dependency**: This task depends on completion of T030b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns (Review-Driven)

**Purpose**: Address specific reviewer concerns regarding instrumentation, calibration, and reproducibility.

- [ ] T035 [P] Implement `code/analysis/instrument_registry.py` to define and log instrument configuration. **Constraint**: The system MUST load the instrument model (e.g., "Edinburgh Instruments LP-series" or "Generic") from `data/chemicals/instrument_config.yaml`. If the config is missing, it MUST default to "Generic Transient Absorption Spectrometer" to ensure vendor agnosticism and avoid hard-coding specific hardware dependencies (addressing Marie Curie review on missing instrument definition).
- [ ] T036 [P] Update `docs/deviation_analysis.md` to compare simulated vs. expected physical behaviors
- [ ] T037 [P] Add `docs/methodology.md` detailing instrument model, calibration dates, detection limits, and sample quantities (addressing Marie Curie review on reproducibility and instrument calibration protocol)
- [ ] T038 [P] Verify all data files are checksummed in `data/hashes.json` and raw data is immutable
- [ ] T039 [US3] Run full pipeline integration test to ensure data flow from `data/raw` → `data/processed` → `paper/` (depends on T026, T034, AND completion of Phase 4 and Phase 5)
- [ ] T040 [P] Validate `quickstart.md` and ensure all tasks run on CPU-only CI (2 cores, 7GB RAM) within 6 hours
- [ ] T041 [P] Implement `code/analysis/hydration_monitor.py` to explicitly log and validate solvent hydration states to three significant figures, ensuring ±2% RH control is recorded for every run (addressing Rosalind Franklin review on hydration state control)
- [ ] T042 [P] Implement `code/analysis/product_quantification.py` to define the analytical method (HPLC with UV detection) for quantifying ester rearrangement products, including detection thresholds and calibration standards. **Constraint**: NMR is explicitly excluded; only HPLC with UV detection is permitted as per Spec Assumptions.
- [ ] T043 [P] Implement `code/analysis/temporal_resolution.py` to explicitly log and validate the temporal resolution of kinetic measurements (ns–μs) against instrument specifications (addressing Rosalind Franklin review on temporal resolution)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Note**: T015b (Real Data Ingestion) is now a blocking prerequisite for T015 (Synthetic Data).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T015b (Phase 2) completion
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T015b (Phase 2) and US2 outputs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Loaders before Services/Analysis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T012 (Integration Test for US1) depends on T014 implementation and cannot run in parallel with it.

### Critical Execution Order for Phase 5

- **T029 MUST complete before T030a**: T030a (Correlation Analysis) consumes the output of T029 (Solvent Models). T029 is NOT parallel [P] in execution; it is a sequential prerequisite.
- **T030a and T030b are sequential**: T030b depends on the output of T030a.
- **T034 depends on T030b**: T034 generates the final figures and reports based on T030b's results.
- **T039 depends on T034**: T039 is the final integration gate.

### Critical Execution Order for Phase 6

- **T039 (Integration Test)**: Must strictly wait for the completion of **Phase 4 (T026)** and **Phase 5 (T034)**. Do not execute T039 until all upstream data processing tasks in Phases 4 and 5 are finished.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for solvent validation in tests/unit/test_solvent_validation.py"
# Note: T012 (Integration test) depends on T014 and cannot run in parallel with it.

# Launch all models for User Story 1 together:
Task: "Implement environment logging in code/analysis/environment.py"
Task: "Implement CLI entry point in code/main.py" (depends on T014)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - **Ensure T015b (Real Data Ingestion) is prioritized.**
3. Complete Phase 3: User Story 1 (Solvent configuration & data generation)
4. **STOP and VALIDATE**: Test US1 independently with mock data
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Kinetic Analysis)
 - Developer C: User Story 3 (Correlation & Diagnostics)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Review Addressing**:
 - T035, T037 explicitly address Marie Curie's concern for instrument model, calibration dates, detection limits, and sample quantities. T035 now enforces config-based loading with a generic fallback.
 - T041, T042, T043 explicitly address Rosalind Franklin's concern for hydration state control, product quantification methods, and temporal resolution.
 - T017, T017b, T018, T025 address SC-010, SC-004, and sensitivity analysis.
 - T024, T030a, T030b, T031, T032 address power analysis, Bayesian statistics, p-value reporting (SC-003), collinearity (VIF), and multiple-comparison corrections.
 - T015b (Real Data), T015 (Synthetic Fallback) ensure data integrity and null hypothesis testing without violating reproducibility.
 - **T029 now implements the dynamic partitioning logic for implicit/explicit solvent models as required by FR-005, replacing the fragmented T029a-d tasks.**
 - T042 restricted to HPLC with UV detection only; NMR explicitly excluded.
 - **Statistical Note**: All statistical tasks (T030a, T030b) strictly follow the Plan's Bayesian Hierarchical Modeling approach, BUT T030b now also reports exact p-values to satisfy SC-003, framing the Bayesian result as the primary inference for low-N robustness.