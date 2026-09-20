# Tasks: Quantifying Entanglement Entropy in Randomly Perturbed Quantum Spin Chains

**Input**: Design documents from `/specs/PROJ-308-001-quantifying-entanglement/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/, research.md (generated in Phase 0)
**Generated Artifacts**: `research.md` (generated in Phase 0)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

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

## Phase 0: Research & Validation (Pre-Implementation)

**Purpose**: Generate and validate the scientific foundation before any code is written.

**Critical**: This phase must complete before Phase 1. The `research.md` file generated here is the source of truth for scientific hypotheses and citations.

- [ ] T000 [P] **Generate Research Document**: Create `research.md` in `specs/PROJ-308-001-quantifying-entanglement/`. Populate with:
 - Scaling ansatz: $S(L) \approx c_{eff} \log L$ (critical) vs Area Law (localized).
 - Citation: Refael-Moore (Phys. Rev. Lett. (2004)). [UNRESOLVED-CLAIM: c_6bcf5aef — status=not_enough_info]
 - Hypothesis: "S(L) $\propto L^\alpha$ with $\alpha$ indicating an area-law in the localized regime and $\alpha$ indicating logarithmic scaling in the critical regime". [UNRESOLVED-CLAIM: c_56ef6c9e — status=not_enough_info]
 - **Verification**: File must exist AND contain sections 'Scaling Ansatz', 'Citations', 'Hypothesis' (verify via `grep`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] **Initialize Project Directory Structure**: Create the following directories in `projects/PROJ-308-quantifying-entanglement-entropy-in-rand/`:
 - `code/`, `data/`, `state/`, `tests/`, `docs/`
 - `data/raw/`, `data/processed/`
 - `tests/unit/`, `tests/integration/`
 - `state/projects/`
 - `tools/`
 - Verify via `ls` and `find. -type d`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Dependency**: Phase 0 (Research) must be complete.

- [X] T002 [P] Implement `code/config.py` with strict input validation for $L$ (low to moderate range), $\delta$ (0-1), $N_{\text{real}}$ (50-200), and random seed; raise clear errors for out-of-bounds (FR-009). **Add support for `dev_mode` flag to bypass L-range checks for toy models.** Verify via `test_config.py::test_validation`.
- [X] T003 [P] Implement `code/hamiltonian.py` to generate XXZ Heisenberg Hamiltonian with random nearest-neighbour couplings $J_i \sim \mathcal{U}[-\delta, 1+\delta]$ (FR-002). Verify via `test_hamiltonian.py::test_coupling_range`.
- [X] T004 [P] Implement `code/ground_state.py` using TeNPy for imaginary-time TEBD evolution; enforce double-precision (64-bit, see arXiv:1304.4292), convergence tolerance sufficiently stringent to ensure numerical stability, and adaptive bond dimension (max $\chi=400$) with 'numerically unresolved' flagging (FR-003, Plan). Verify via `test_ground_state.py::test_convergence`.
- [X] T005 [P] Implement `code/entropy.py` to compute von Neumann entropy $S(l)$ for all bipartitions $l$ across the system per realization (FR-004). Verify via `test_entropy.py::test_entropy_calc`.
- [X] T005a [P] **Document AIC Deviation**: Implement `code/analysis.py` documentation header to explicitly state: "Model selection uses AIC per Plan.md and FR-005 (amended), superseding original Spec R² requirement." Log this deviation to `validation_log.txt` at runtime. **Dependency**: T006. Verify via `grep "AIC" code/analysis.py`.
- [X] T006 [P] **Implement AIC Model Selection**: Implement `code/analysis.py` core: Linear regression of $S(l)$ vs $\log l$ (log-fit) and $S(l)$ vs $l$ (linear-fit); implement AIC-based model selection to distinguish Area Law (Constant), Logarithmic, and Volume Law (Linear). **Note**: Implementation follows Plan's methodological correction (AIC) over Spec's R² requirement. Verify via `test_analysis.py::test_aic_selection_logic` using synthetic data with known slopes.
- [X] T007 [P] Implement `code/analysis.py` bootstrap module: Non-parametric percentile bootstrap with a sufficient number of resamples to estimate SE and p-value for $\alpha$ (FR-006). Verify via `test_analysis.py::test_bootstrap`.
- [ ] T008 [P] Implement logic in `code/analysis.py` to filter out 'numerically unresolved' realizations from the dataset before bootstrap/resampling to prevent systematic bias (Plan). Verify via `test_analysis.py::test_filter_unresolved`.
- [ ] T009 [P] Implement `code/analysis.py` plotting utilities to generate `entropy_vs_l.png` (log-log plot with fit line) (FR-007). Verify via `test_analysis.py::test_plot_generation`.
- [ ] T010 [P] Implement `code/cli.py` entry point to orchestrate the workflow, handle `delta_grid.csv` input, and manage output artifacts (FR-010). **Include integrated checks for CI width and edge entropy continuity (T037, T048, T049) as flags/warnings, not aborts.** Verify via `test_cli.py::test_cli_run`.
- [ ] T011 [P] **Implement Metadata Logging**: Implement logic to log 'numerically unresolved' realizations (count and reason) to `data/raw/metadata.json` and `state/` to ensure audit trail (Constitution Principle IV). Verify via `test_state.py::test_unresolved_log`.
- [ ] T012 [P] **Configure State Versioning**: Create `state/projects/PROJ-308-quantifying-entanglement-entropy-in-rand.yaml`. The file MUST contain keys: `artifact_hashes`, `updated_at`, `version`, `stage`. Populate with initial empty hash map. Verify via `cat` and `yaml` parsing.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: Research Validation (Critical for Scientific Validity)

**Purpose**: Address specific reviewer concerns regarding scaling ansatz, Refael-Moore comparison, and toy model validation.

**Input**: `research.md` (generated in Phase 0 at `specs/PROJ-308-001-quantifying-entanglement/research.md`)

**Independent Test**: Verify `research.md` contains explicit scaling ansatz and citations; verify `code/analysis.py` includes a "toy model" verification step.

**Dependency**: **Phase 2 (Foundational)** must be complete (T012 must pass). **All tasks in this phase depend on Phase 2 completion.**

### Implementation for Research Validation

- [ ] T013 [P] **Validate Citations**: Create `tools/validate_citations.py` script that parses `research.md`, extracts citations, and verifies them against a local database or online sources. **Rules**: 1. Check DOI validity. 2. Check title overlap > 0.7. 3. Exit code 0 on success, 1 on failure. Execute script on `research.md` and verify output log contains "All citations valid". Verify via `python tools/validate_citations.py --file specs/PROJ-308-001-quantifying-entanglement/research.md --output validator_output.log` and `grep "valid" validator_output.log`.
- [ ] T014 [P] Update `specs/PROJ-001-quantifying-entanglement/research.md` to explicitly articulate scaling ansatz: $S(L) \approx (c_{eff}/3) \log L$ (critical) vs Area Law (localized), citing Refael-Moore (Phys. Rev. Lett. 93, 207204 (2004)) as per Geoffrey West review. Verify via `grep "Refael-Moore" specs/PROJ-308-001-quantifying-entanglement/research.md`.
- [ ] T016 [P] Update `specs/PROJ-308-001-quantifying-entanglement/research.md` to include specific hypothesis: "S(L) $\propto L^\alpha$ with $\alpha \approx 0$ (area-law) in localized regime and $\alpha \approx 0$ (logarithmic) in critical regime" (Refael-Moore context). Verify via `grep "hypothesis" specs/PROJ-308-001-quantifying-entanglement/research.md`.
- [ ] T018 [P] Implement "Toy Model" verification in `code/analysis.py`: Generate a short chain (L=10) with random couplings using TEBD only (no exact diagonalization), compute entropy, and plot $S(L)$ vs $\log L$ to visually confirm slope (Richard Feynman review). **Use `dev_mode=True` to bypass FR-009 validation.** **Dependency**: T006 (AIC) must be complete. Verify via `test_analysis.py::test_toy_model`.
- [ ] T019 [P] Add a `toy_model_output/` directory and script to generate a table of $S(L)$ values for $L=4, 8, 16 $ to demonstrate the slope explicitly (Richard Feynman review). **Use `dev_mode=True`**. Verify via `ls toy_model_output/`.
- [ ] T021 [P] **Documentation Updates**: Update `docs/` and `quickstart.md` to reflect the validated research findings and AIC method. **Dependency**: T013 (Citation Validation) must pass. Verify via `quickstart.md` validation.

**Checkpoint**: Research claims are grounded in literature and validated by toy models

---

## Phase 4: User Story 1 - Compute Entanglement Scaling for a Single Parameter Set (Priority: P1) 🎯 MVP

**Goal**: Obtain entanglement-entropy scaling exponent $\alpha$ for a specific $L$ and $\delta$ with bootstrap CI and plots.

**Independent Test**: Execute workflow with $L=30, \delta=0.2, N=100$; verify `entropy_data.csv`, `scaling_fit.txt` (exponent, CI, p-value, R²), `entropy_vs_l.png`, and `bootstrap_summary.txt` are generated within 6 hours.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T022 [P] [US1] Unit test for Hamiltonian generation range validation in `tests/unit/test_hamiltonian.py`. Verify via `pytest`.
- [ ] T023 [P] [US1] Unit test for TEBD convergence logic and double-precision enforcement in `tests/unit/test_ground_state.py`. Verify via `pytest`.
- [ ] T024 [P] [US1] Unit test for AIC model selection logic (Log vs Linear vs Constant) in `tests/unit/test_analysis.py`. Verify via `pytest`.
- [ ] T025 [P] [US1] Integration test for full single-parameter workflow in `tests/integration/test_workflow_us1.py` (Verify SC-001, SC-003, SC-004). Verify via `pytest`.

### Implementation for User Story 1

- [ ] T026 [US1] **Implement Pilot Variance Estimation**: Implement logic in `code/cli.py` (pre-run step) to dynamically adjust $N_{\text{real}}$ if variance of the fitted exponent **alpha** is too high. **Algorithm**: Run multiple realizations, compute variance of alpha. If `variance > 0.05`, set `N_real = min(200, current * 2)`. **Conflict Resolution**: If pilot suggests `N_real > 200` or estimated time > 6h, **ABORT** with a clear error message indicating the specific constraint violated (FR-001, FR-008). **Artifact Flow**: Pilot run generates `data/raw/pilot_metadata.json` which is consumed by the main run. Verify via `test_analysis.py::test_pilot_abort`.
- [ ] T027 [US1] Implement output generation for `entropy_data.csv`, `scaling_fit.txt`, `bootstrap_summary.txt` in `code/cli.py` (FR-007). Verify via `test_cli.py::test_outputs`.
- [ ] T028 [US1] Add logic to detect statistical significance (p-value $\le 0.05$) and mark "statistically significant" in `scaling_fit.txt` (US-1 Scenario 2). Verify via `test_cli.py::test_significance_flag`.
- [ ] T029 [US1] Implement wall-clock timeout check (6h) in `code/cli.py` to abort with informative error if exceeded (FR-008). Verify via `test_cli.py::test_timeout`.
- [ ] T030 [US1] Add assertion in `tests/integration/test_workflow_us1.py` that raises AssertionError if fitted $\alpha \notin [0.30, 0.36]$ for $\delta=0$ (SC-001, US-1 Scenario 4). Verify via `pytest`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 5: User Story 2 - Scan Across Disorder Strengths to Locate MBL-Thermal Crossover (Priority: P2)

**Goal**: Run workflow over a range of $\delta$ values to map scaling exponent evolution and identify phase crossover.

**Independent Test**: Provide `delta_grid.csv` with $\delta$ spanning a range of small positive values.; verify `delta_vs_exponent.csv` contains multiple rows with numeric $\alpha$ and sufficiently narrow CI width for $\delta$ within a low magnitude range.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US2] Integration test for grid scan workflow in `tests/integration/test_workflow_us2.py` (Verify SC-005). Verify via `pytest`.
- [ ] T032 [P] [US2] Test for low-disorder linear-in-$l$ fit ($\beta$) and significance check in `tests/unit/test_analysis.py`. Verify via `pytest`.

### Implementation for User Story 2

- [ ] T033 [US2] Implement `delta_grid.csv` parsing and iteration logic in `code/cli.py` (FR-010). Verify via `test_cli.py::test_grid_parsing`.
- [ ] T034 [US2] **Validate Input Grid**: (Removed input step size check). Verify via `test_cli.py::test_grid_step_warn`.
- [ ] T035 [US2] Implement generation of `delta_vs_exponent.csv` with columns `delta, alpha, ci_lower, ci_upper, ci_width, p_value` (FR-010, SC-005). **Note**: Do not add 'status' column to match FR-010; log validation failures to `validation_log.txt`. Verify via `test_cli.py::test_grid_output`.
- [ ] T036 [US2] Implement logic for low-disorder linear-in-$l$ fit to extract slope $\beta$, check if p-value $\le 0.05$, and output `thermal_fit.txt` with the significance status (FR-011, SC-006). Verify via `test_analysis.py::test_thermal_fit`.
- [ ] T037 [US2] **Validate CI Width**: Implement logic to check CI width for all $\delta \le 0.3$ (matching SC-005). If exceeded, **LOG WARNING AND FLAG** the run in `validation_log.txt` (do NOT abort). Verify via `test_cli.py::test_ci_validation`.
- [ ] T038 [US2] Verify $\delta=0$ entry is flagged "critical-regime agreement" if $\alpha$ matches theoretical CFT value (US-2 Scenario 3). Verify via `test_cli.py::test_cft_flag`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Perform Bootstrap Validation of Scaling Exponents (Priority: P3)

**Goal**: Assess robustness of exponent estimates via bootstrap resampling.

**Independent Test**: After a run, verify `bootstrap_summary.txt` reports a sufficient number of resamples, a sufficiently small standard error, and a two-sided p-value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T039 [P] [US3] Unit test for bootstrap resampling logic and SE calculation in `tests/unit/test_analysis.py`. Verify via `pytest`.
- [ ] T040 [P] [US3] Integration test for bootstrap output format in `tests/integration/test_workflow_us3.py`. Verify via `pytest`.

### Implementation for User Story 3

- [ ] T041 [US3] Ensure `bootstrap_summary.txt` explicitly reports resample count, standard error, and p-value (FR-006, US-3 Scenario 1). Verify via `test_cli.py::test_bootstrap_output`.
- [ ] T042 [US3] Implement logic to label exponent "not statistically significant" if p-value $> 0.05$ and advise increasing $N_{\text{real}}$ (US-3 Scenario 2). Verify via `test_cli.py::test_significance_label`.
- [ ] T043 [US3] Verify SE is within acceptable limits for default configuration; if higher, trigger pilot study to increase $N_{\text{real}}$ (Plan, US-3 Scenario 1). Verify via `test_analysis.py::test_se_threshold`.

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should be independently functional

---

## Phase 7: User Story 4 - Extract Edge Entropy Profiles (Priority: P3)

**Goal**: Examine disorder effects on chain boundaries via edge-entropy data.

**Independent Test**: After a run, verify `boundary_entropy.csv` contains `realization_id, delta, edge_left, edge_right` with non-negative values.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T044 [P] [US4] Unit test for edge entropy calculation (l=1, l=L-1) in `tests/unit/test_entropy.py`. Verify via `pytest`.
- [ ] T045 [P] [US4] Integration test for `boundary_entropy.csv` generation in `tests/integration/test_workflow_us4.py`. Verify via `pytest`.

### Implementation for User Story 4

- [ ] T046 [US4] Implement edge entropy extraction (first and last bipartitions) in `code/entropy.py` (FR-012). Verify via `test_entropy.py::test_edge_entropy`.
- [ ] T047 [US4] Generate `boundary_entropy.csv` with `realization_id, delta, edge_left, edge_right` columns (FR-012). Verify via `test_cli.py::test_boundary_output`.
- [ ] T048 [US4] **Validate Edge Entropy Continuity**: Implement check in `code/analysis.py` to compute the standard deviation of edge entropies for each delta in the grid. Then, calculate the difference in standard deviation between consecutive deltas. If the difference > 0.2, **LOG WARNING AND FLAG** the run in `validation_log.txt` (do NOT abort) (SC-007). Verify via `test_analysis.py::test_edge_validation`.
- [ ] T049 [US4] **Check for Abrupt Spikes**: Implement check for 'abrupt spikes' in edge entropy vs $\delta$ curve defined as: deviation > 3 * std_dev of the edge entropy for that specific delta value. If detected, **LOG WARNING AND FLAG** the run in `validation_log.txt` (do NOT abort) (SC-007). Verify via `test_analysis.py::test_edge_spikes`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: [DELETED - Redundant with Phase 3]

**Note**: This phase has been removed to eliminate redundancy. Research validation tasks (T013-T021) in Phase 3 are the sole gate for 'Research Accepted'.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T051 [P] Code cleanup and refactoring of `code/analysis.py` for readability. Verify via `ruff check`.
- [ ] T052 [P] Performance optimization: Ensure TEBD runs within 6h limit for $L=30, N=100$ on CPU. [UNRESOLVED-CLAIM: c_57b3d9d6 — status=not_enough_info] Verify via `test_workflow_us.py::test_runtime`.
- [ ] T053 [P] Additional unit tests for edge cases (e.g., $\delta=0$, $\delta=1$, $L=40$) in `tests/unit/`. Verify via `pytest`.
- [ ] T054 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility. Verify via `quickstart.md` execution.
- [ ] T055 [P] Verify all artifacts (CSVs, PNGs, TXTs) are parsable and match `state/` checksums. Verify via `test_state.py::test_artifacts`.

**New Success Criterion**:
- **SC-008**: The 'Research Accepted' gate MUST be passed only after T013 (Citation Validation) is successfully completed and all citations in `research.md` are verified.

---

## Phase 10: Review Response & Operational Validity (New - Addresses Einstein, West, Feynman Reviews)

**Purpose**: Explicitly address the operational and conceptual concerns raised by the simulated reviewers (Einstein, West, Feynman) to ensure the physical interpretation and numerical demonstration are robust.

**Input**: Review feedback from `albert-einstein-simulated`, `geoffrey-west-simulated`, `richard-feynman-simulated`.

**Independent Test**: Verify `research.md` contains the "Observer's Frame" definition; verify `code/analysis.py` includes a "Local Measurement Protocol" comment; verify `toy_model_output/` contains a plot of $S$ vs $\log L$ with the specific Refael-Moore slope annotation.

**Dependency**: **Phase 3 (Research Validation)** must be fully complete. **Phase 4 (US1)** must be implemented. Tasks T056-T062 specifically depend on T014, T016 (Phase 3) for base content.

### Implementation for Review Response

- [ ] T056a [US1] **Define Observer's Frame (Doc)**: Update `research.md` to include a section "Operational Definition of Entropy Measurement" that explicitly describes how a local observer distinguishes the localized vs. ergodic phase without invoking non-local abstractions, addressing the Einstein review concern. **Dependency**: T014, T016. Verify via `grep "Observer's Frame" research.md`.
- [ ] T057 [US1] **Local Measurement Protocol (Code)**: Add a docstring and comment block in `code/entropy.py` describing the "Local Measurement Protocol" for computing entropy across a cut, ensuring it aligns with the operational definition in `research.md` (Einstein review). **Dependency**: T014, T016. Verify via `grep "Local Measurement" code/entropy.py`.
- [ ] T058a [US1] **Refael-Moore Slope Annotation (Script)**: Update the `toy_model_output/` generation script (T019) to explicitly annotate the plot with the theoretical Refael-Moore slope and compare it to the simulated slope. **Dependency**: T019. Verify via `ls toy_model_output/`.
- [ ] T058b [US1] **Refael-Moore Slope Annotation (Plot)**: Generate the plot with the annotation and verify it visually. **Dependency**: T019. Verify via `ls toy_model_output/` and visual inspection.
- [ ] T059 [US1] **Explicit Scaling Law Verification**: In `code/analysis.py`, add a function `verify_scaling_ansatz` that computes the fit for both $S(L) \approx (c_{eff}/3) \log L$ and $S(L) \approx \text{const}$, and logs the $\Delta$AIC to `validation_log.txt` to explicitly demonstrate the "Bartender Test" (West review). **Dependency**: T006. Verify via `grep "verify_scaling_ansatz" code/analysis.py`.
- [ ] T060 [US1] **Toy Model Data Table**: Ensure `toy_model_output/` contains a CSV file `toy_model_data.csv` with columns `L, S(L), log(L)` for $L=4, 8, 16$ to provide the concrete numerical example requested by Feynman. **Dependency**: T019. Verify via `cat toy_model_output/toy_model_data.csv`.
- [ ] T062a [US1] **Physical Interpretation Check (Doc)**: Update `docs/physical_interpretation.md` to explain how the computed entropy relates to the "information crossing the cut" in the context of the random singlet phase, addressing the Feynman "sum over paths" intuition. **Dependency**: T014, T016. Verify via `cat docs/physical_interpretation.md`.

**Checkpoint**: All reviewer concerns regarding operational definition, concrete examples, and physical interpretation are addressed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately. Generates `research.md`.
- **Phase 1 (Setup)**: Depends on Phase 0 completion.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - BLOCKS all user stories.
- **Phase 3 (Research Validation)**: Depends on **Phase 2 (Foundational)** (T012 must pass). **Must complete before Phase 4-7.**
- **Phase 4-7 (User Stories)**: All depend on Foundational (Phase 2) and Research Validation (Phase 3) completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 $\to$ P2 $\to$ P3)
- **Phase 9 (Polish)**: Depends on all desired user stories and research validation being complete
- **Phase 10 (Review Response)**: Depends on **Phase 3 (Research Validation)** being fully complete AND **Phase 4 (US1 Implementation)**.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) and Research Validation (Phase 3) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) and Research Validation (Phase 3) - Reuses US1 components
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) and Research Validation (Phase 3) - Reuses US1 components
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) and Research Validation (Phase 3) - Reuses US1 components
- **Research Validation (Phase 3)**: Independent of code implementation but critical for scientific validity. Must complete before code implementation (Phase 4-7).
- **Review Response (Phase 10)**: Depends on the existence of `research.md` (Phase 0) and the core implementation (Phase 2-4) to add the specific operational definitions and toy model annotations. **Strictly requires Phase 3 completion.**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories (US1-US4) can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Research Validation (Phase 3) MUST complete AFTER Phase 2 and BEFORE any User Story implementation. It cannot run in parallel with Phase 2.
- Review Response (Phase 10) can ONLY run after Phase 3 is fully complete and Phase 4 is implemented.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for Hamiltonian generation range validation in tests/unit/test_hamiltonian.py"
Task: "Unit test for TEBD convergence logic and double-precision enforcement in tests/unit/test_ground_state.py"
Task: "Unit test for AIC model selection logic (Log vs Linear vs Constant) in tests/unit/test_analysis.py"
Task: "Integration test for full single-parameter workflow in tests/integration/test_workflow_us1.py"

# Launch all models for User Story 1 together:
Task: "Implement pilot variance estimation logic in code/cli.py"
Task: "Implement output generation for entropy_data.csv, scaling_fit.txt, bootstrap_summary.txt in code/cli.py"
Task: "Add logic to detect statistical significance (p-value <= 0.05) and mark 'statistically significant' in scaling_fit.txt"
Task: "Implement wall-clock timeout check (6h) in code/cli.py to abort with informative error if exceeded"
Task: "Add assertion in test_workflow_us1.py that raises AssertionError if alpha not in [0.30, 0.36] for delta=0"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research (Generate research.md)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: Research Validation (Validate scientific claims)
5. Complete Phase 4: User Story 1
6. **STOP and VALIDATE**: Test User Story 1 independently
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0-2 $\to$ Foundation ready
2. Complete Phase 3 $\to$ Research validated
3. Add User Story 1 $\to$ Test independently $\to$ Deploy/Demo (MVP!)
4. Add User Story 2 $\to$ Test independently $\to$ Deploy/Demo
5. Add User Story 3 $\to$ Test independently $\to$ Deploy/Demo
6. Add User Story 4 $\to$ Test independently $\to$ Deploy/Demo
7. Add Polish $\to$ Finalize
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 (Research) and Phase 1 (Setup) together
2. Once Phase 1 is done:
 - Developer A: Phase 2 (Foundational)
 - Developer B: Phase 3 (Research Validation) - **Must wait for Phase 2**
3. Once Phase 2 & 3 are done:
 - Developer A: User Story 1 (P1)
 - Developer B: User Story 2 (P2)
 - Developer C: User Story 3/4 (P3)
4. Stories complete and integrate independently
5. Once US1 is done and Phase 3 is done:
 - Developer D: Phase 10 (Review Response)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: All tasks must respect the 6-hour CPU limit and double-precision constraints (FR-008, FR-003)
- **Critical**: Model selection must use AIC to distinguish Area Law (Constant) from Logarithmic growth (Plan, FR-005 amended) - documented in T005a.
- **Critical**: Research Validation (Phase 3) MUST address Geoffrey West and Richard Feynman reviews explicitly (Refael-Moore citation, scaling ansatz, toy model) and pass citation validation (T013) before Research Accepted.
- **Critical**: `research.md` is generated in Phase 0 and validated in Phase 3.
- **Critical**: SC-007 checks output statistics (std dev of edge entropy), not input grid step.
- **Critical**: CI width enforcement applies to $\delta \le 0.3$, not just $\delta \le 0.1$.
- **Critical**: 'Abrupt spikes' check uses quantitative thresholds (deviation > 3 * std_dev), not placeholders.
- **Critical**: No 'status' column in `delta_vs_exponent.csv`; failures logged to `validation_log.txt`.
- **Critical**: Pilot variance estimation is a pre-run step in US1 workflow (T026), not a foundational task.
- **Critical (New)**: Phase 10 tasks (T056-T062) MUST address the specific operational and conceptual concerns of the Einstein, West, and Feynman reviews (Observer's Frame, Local Measurement, Concrete Numerical Example) to ensure physical validity.
- **Critical (New)**: T012 is mandatory and must be completed before Phase 3.
- **Critical (New)**: T005a documents the deviation in code/logs, not spec.
- **Critical (New)**: T013a creates the `tools/validate_citations.py` script required for T015, T017, T020, T050, T061.
- **Critical (New)**: Phase 3 depends on Phase 2 (Foundational) completion.
- **Critical (New)**: Phase 3 MUST complete before Phase 4. It cannot run in parallel with Phase 2.
- **Critical (New)**: Phase 10 MUST complete after Phase 3 and Phase 4.
- **Critical (New)**: T037, T048, T049 use "LOG WARNING AND FLAG" instead of "ABORT" to match Spec SC-007.
- **Critical (New)**: T026 includes explicit algorithm and conflict resolution path.
- **Critical (New)**: T018/T019 use `dev_mode=True` to bypass FR-009 for toy models.