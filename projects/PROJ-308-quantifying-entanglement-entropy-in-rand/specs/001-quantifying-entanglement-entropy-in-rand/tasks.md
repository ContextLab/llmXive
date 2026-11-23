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

- [ ] T000 [P] **Generate Research Document**: Create `research.md` at `specs/PROJ-308-001-quantifying-entanglement/research.md`. Populate with:
 - Scaling ansatz: $S(L) \approx c_{eff} \log L$ (critical) vs Area Law (localized) [UNRESOLVED-CLAIM: c_123140f8 — status=not_enough_info].
 - Citation: Refael-Moore (Phys. Rev. Lett., 207204 (2004)). [UNRESOLVED-CLAIM: c_1f3d1d39 — status=not_enough_info]
 - Hypothesis: "S(L) $\propto L^\alpha$ with $\alpha$ indicating an area-law in the localized regime and $\alpha$ indicating logarithmic scaling in the critical regime".
 - **Verification**: File MUST exist. Run `grep -q 'Scaling Ansatz'` and `grep -q 'Hypothesis'` on the file. **FAIL** if file missing or grep fails. Verify via `python tools/verify_research.py`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] **Initialize Project Directory Structure**: Create the following directories in `projects/PROJ-308-quantifying-entanglement-entropy-in-rand/`:
 - `code/`, `data/`, `state/`, `tests/`, `docs/`
 - `data/raw/`, `data/processed/`
 - `tests/unit/`, `tests/integration/`
 - `state/projects/`
 - `tools/`
 - `reviews/` (for simulated feedback)
 - **Verification**: Execute `python tools/verify_structure.py` which checks for all directories and outputs `setup_log.txt`. **FAIL** if script returns non-zero or log missing.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Dependency**: Phase 0 (Research) must be complete.

- [X] T002 [P] Implement `code/config.py` with strict input validation for $L$ (20 ≤ L ≤ 40), $\delta$ (0-1), $N_{\text{real}}$ (50-200), and random seed; raise clear errors for out-of-bounds (FR-009). **Add support for `dev_mode` flag to bypass L-range checks for toy models.** Verify via `test_config.py::test_validation`.
- [X] T003 [P] Implement `code/hamiltonian.py` to generate XXZ Heisenberg Hamiltonian with random nearest-neighbour couplings $J_i\sim\mathcal{U}[1-\delta,\,1+\delta]$ (FR-002). **Ensure lower bound is strictly $1-\delta$ to prevent negative couplings.** Verify via `test_hamiltonian.py::test_coupling_range` which asserts all $J_i > 0$ for $\delta < 1$.
- [X] T004 [P] Implement `code/ground_state.py` using TeNPy for imaginary-time TEBD evolution; enforce double-precision (64-bit), convergence tolerance of a sufficiently small magnitude to ensure numerical stability, and adaptive bond dimension (max $\chi=400$) with 'numerically unresolved' flagging (FR-003, Plan). Verify via `test_ground_state.py::test_convergence`.
- [X] T005 [P] Implement `code/entropy.py` to compute von Neumann entropy $S(l)$ for all bipartitions $l$ across the system per realization (FR-004). Verify via `test_entropy.py::test_entropy_calc`.
- [X] T005a [P] **Document AIC Deviation in Code**: Add a docstring header to `code/analysis.py` explicitly stating: "Model selection uses AIC per Plan.md and FR-005 (amended), superseding original Spec R² requirement." Log this deviation to `validation_log.txt` at runtime with message "AMENDMENT: AIC used per Plan.md". **Dependency**: T005 (entropy.py must exist to import). **Verification**: `grep -q "AMENDMENT: AIC used" code/analysis.py` and runtime log check.
- [ ] T005b [P] **Formalize Spec Amendment**: Update `spec.md` (or create `amendment.md`) to formally record the deviation from FR-005 (R²) to AIC-based model selection, citing Plan.md justification. **Dependency**: T005a. **Verification**: `grep -q "AIC" spec.md` or `amendment.md` exists.
- [X] T006 [P] **Implement AIC Model Selection**: Implement `code/analysis.py` core: Linear regression of $S(l)$ vs $\log l$ (log-fit) and $S(l)$ vs $l$ (linear-fit); implement AIC-based model selection to distinguish Area Law (Constant), Logarithmic, and Volume Law (Linear). **Include docstring citing Plan.md justification for AIC over R².** **Dependency**: T005a. Verify via `test_analysis.py::test_aic_selection_logic` using synthetic data with known slopes.
- [X] T007 [P] Implement `code/analysis.py` bootstrap module: Non-parametric percentile bootstrap with 1000+ resamples to estimate SE and p-value for $\alpha$ [UNRESOLVED-CLAIM: c_becbf85c — status=not_enough_info] (FR-006). Verify via `test_analysis.py::test_bootstrap`.
- [X] T008 [P] Implement logic in `code/analysis.py` to filter out 'numerically unresolved' realizations from the dataset before bootstrap/resampling to prevent systematic bias (Plan). Verify via `test_analysis.py::test_filter_unresolved`.
- [ ] T009 [P] Implement `code/analysis.py` plotting utilities to generate `entropy_vs_l.png` (log-log plot with fit line) (FR-007). Verify via `test_analysis.py::test_plot_generation`.
- [ ] T010 [P] Implement `code/cli.py` entry point to orchestrate the workflow, handle `delta_grid.csv` input, and manage output artifacts (FR-010). **Include integrated checks for CI width and edge entropy continuity (T037, T048, T049) as flags/warnings, not aborts.** Verify via `test_cli.py::test_cli_run`.
- [ ] T011 [P] **Implement Metadata Logging**: Implement logic to log 'numerically unresolved' realizations to `data/raw/metadata.json`. **Schema**: `{ "unresolved_count": int, "reasons": [str], "timestamp": str }`. Verify via `test_state.py::test_unresolved_log`.
- [ ] T012 [P] **Configure State Versioning**: Create `state/projects/PROJ-308-quantifying-entanglement-entropy-in-rand.yaml`. The file MUST contain keys: `artifact_hashes`, `updated_at`, `version`, `stage`. Populate with initial empty hash map. Verify via `cat` and `yaml` parsing.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

## Phase 3: Research Validation (Critical for Scientific Validity)

**Goal**: Address specific reviewer concerns regarding scaling ansatz, Refael-Moore comparison, and toy model validation.

**Input**: `research.md` (generated in Phase 0 at `specs/PROJ-308-001-quantifying-entanglement/research.md`)

**Independent Test**: Verify `research.md` contains explicit scaling ansatz and citations; verify `code/analysis.py` includes a "toy model" verification step.

**Dependency**: **Phase 0 (Research)** must be complete. **Runs in parallel with Phase 2 (Foundational)** as it does not depend on code infrastructure.

- [ ] T013 [P] **Validate Citations**: Create `tools/validate_citations.py` script that parses `research.md`, extracts citations, and verifies them. **Rules**: 1. Check DOI validity via `requests.get`. 2. Check title overlap > 0.7. 3. Exit code 0 on success, 1 on failure. Execute script on `research.md` and verify output log contains "All citations valid". Verify via `python tools/validate_citations.py --file specs/PROJ-308-001-quantifying-entanglement/research.md --output validator_output.log` and `grep "valid" validator_output.log`.
- [ ] T014 [P] Update `specs/PROJ-308-001-quantifying-entanglement/research.md` to explicitly articulate scaling ansatz: $S(L) \approx c_{eff} \log L$ (critical) vs Area Law (localized), citing Refael-Moore (Phys. Rev. Lett. 93, 207204 (2004)) as per Geoffrey West review. Verify via `grep "Refael-Moore" specs/PROJ-308-001-quantifying-entanglement/research.md`.
- [ ] T016 [P] Update `specs/PROJ-308-001-quantifying-entanglement/research.md` to include specific hypothesis: "S(L) $\propto L^\alpha$ with $\alpha$ indicating area-law scaling in localized regime and logarithmic scaling in critical regime" (Refael-Moore context). Verify via `grep "hypothesis" specs/PROJ-308-001-quantifying-entanglement/research.md`.
- [ ] T018 [P] Implement "Toy Model" verification in `code/analysis.py`: Generate a short chain (L=10) with random couplings using TEBD only [UNRESOLVED-CLAIM: c_ef46f188 — status=not_enough_info] (no exact diagonalization), compute entropy, and plot $S(L)$ vs $\log L$ to visually confirm slope (Richard Feynman review). **Use `dev_mode=True` to bypass FR-009 validation.** **Dependency**: T005. Verify via `test_analysis.py::test_toy_model`.
- [ ] T019 [P] Add a `toy_model_output/` directory and script `gen_toy.py` to generate `toy_model_data.csv` with columns `L, S(L), log(L)` for $L=4, 8, 16$ to demonstrate the slope explicitly (Richard Feynman review). **Use `dev_mode=True`**. Verify via `ls toy_model_output/` and `cat toy_model_output/toy_model_data.csv`.
- [ ] T021 [P] **Documentation Updates**: Update `docs/` and `quickstart.md` to reflect the validated research findings and AIC method. **Dependency**: T013, T016. Verify via `quickstart.md` validation.

**Checkpoint**: Research claims are grounded in literature and validated by toy models

## Phase 4: Core Implementation (User Story 1)

**Purpose**: Implement the core workflow for a single parameter set (US1).

**Dependency**: Phase 2 (Foundational) and Phase 3 (Research Validation).

- [ ] T030 [P] **Implement Scaling Analysis**: Implement `code/analysis.py` to perform the log-log fit and linear fit, compute $\alpha$, and write `scaling_fit.txt` with exponent, CI, p-value, and R² values. **Dependency**: T006, T007. **Verification**: Run on synthetic data and verify `scaling_fit.txt` format matches spec.
- [ ] T031 [P] **Implement Bootstrap Validation**: Integrate bootstrap logic into the CLI to run 1000 resamples and write `bootstrap_summary.txt`. **Dependency**: T007, T030. **Verification**: Run on synthetic data and verify `bootstrap_summary.txt` contains 1000 resamples.
- [ ] T032 [P] **Implement Edge Entropy Extraction**: Implement `code/entropy.py` extension to compute edge entropies ($l=1, l=L-1$) and write `boundary_entropy.csv`. **Dependency**: T005. **Verification**: Run on synthetic data and verify `boundary_entropy.csv` format.
- [ ] T033 [P] **Implement Runtime Monitoring**: Add logic in `code/cli.py` to monitor wall-clock time and abort if > 6 hours, logging to `runtime.log`. **Dependency**: T010. **Verification**: Simulate long-running task and verify abort.
- [ ] T034 [P] **Implement Input Validation**: Add logic in `code/cli.py` to validate $L$ and $\delta$ before starting, aborting with clear error if out of bounds. **Dependency**: T002. **Verification**: Run with invalid inputs and verify abort.

**Checkpoint**: US1 Core workflow complete

## Phase 5: Grid Scan Implementation (User Story 2)

**Purpose**: Implement the grid scan capability for multiple disorder strengths (US2).

**Dependency**: Phase 4 (Core Implementation).

- [ ] T035 [P] **Implement Grid Scan Logic**: Extend `code/cli.py` to read `delta_grid.csv`, iterate over $\delta$ values, and aggregate results into `delta_vs_exponent.csv`. **Dependency**: T030, T031. **Verification**: Run with `delta_grid.csv` and verify output.
- [ ] T036 [P] **Implement Thermal Fit**: Add logic to `code/analysis.py` to fit linear-in-$l$ model for $\delta \le 0.1$ and output `thermal_fit.txt`. **Dependency**: T030. **Verification**: Run on low-disorder synthetic data.
- [ ] T037 [P] **Implement CI Width Check**: Add runtime check in `code/cli.py` to flag runs where CI width > 0.05 for $\delta \le 0.3$ as warnings (not aborts per T010). **Dependency**: T035. **Verification**: Run with high-variance data and verify warning.

**Checkpoint**: US2 Grid scan complete

## Phase 6: Integration Testing

**Purpose**: Ensure all components work together.

**Dependency**: Phase 5 (Grid Scan).

- [ ] T040 [P] **End-to-End Test**: Run a full workflow with $L=30, \delta=0.2, N=100$ [UNRESOLVED-CLAIM: c_af0305b6 — status=not_enough_info] and verify all artifacts exist. **Dependency**: T030-T037. **Verification**: Check existence of all output files.
- [ ] T041 [P] **Stress Test**: Run with $L=40, N=200$ to verify memory and time constraints [UNRESOLVED-CLAIM: c_05a681bd — status=not_enough_info]. **Dependency**: T033. **Verification**: Verify job completes or aborts correctly.

**Checkpoint**: Integration tests pass

## Phase 7: Documentation & Deployment

**Purpose**: Prepare for release.

**Dependency**: Phase 6 (Integration).

- [ ] T050 [P] **Final Documentation**: Update `README.md` and `quickstart.md` with final usage instructions. **Dependency**: T021. **Verification**: Verify documentation completeness.
- [ ] T051 [P] **CI/CD Configuration**: Update GitHub Actions workflow to run the full test suite. **Dependency**: T040, T041. **Verification**: Run CI locally.

**Checkpoint**: Ready for release

## Phase 8: Review Response (Addressing Panel Concerns)

**Purpose**: Address specific reviewer concerns from the analysis report.

**Dependency**: Phase 0 (Research) and Phase 2 (Foundational).

- [ ] T056a [P] **Address Einstein Citation**: Create `tools/check_einstein.py` to search for 'Einstein' in `research.md`. **Logic**: Open file, search for string, exit 0 if found, exit 1 if not. **Verification**: Run script and verify exit code. **Dependency**: T000.
- [ ] T057 [P] **Address Ordering Ambiguity**: Update T005a and T006 descriptions to clarify that T005a (Document Deviation) must be completed before T006 (Implement Core) to ensure documentation precedes implementation. **Verification**: Verify task dependencies in `tasks.md`. **Dependency**: T005a, T006.
- [ ] T062a [P] **Address Constraint Preservation**: Ensure T005b (Formalize Spec Amendment) is completed and linked to T005a to create a complete audit trail for the AIC deviation. **Verification**: Verify `amendment.md` or `spec.md` update. **Dependency**: T005b.

**Checkpoint**: Review concerns addressed

## Phase 9: Final Validation

**Purpose**: Final validation before closure.

**Dependency**: Phase 8 (Review Response).

- [ ] T063 [P] **Final Verification Script**: Create `tools/final_check.py` to verify all required artifacts exist and are valid. **Logic**: Check existence of `scaling_fit.txt`, `bootstrap_summary.txt`, `delta_vs_exponent.csv`, etc. Exit 0 if all present, exit 1 otherwise. **Verification**: Run script and verify exit code. **Dependency**: T030-T037.

**Checkpoint**: Final validation complete

## Phase 10: Documentation & Handover

**Purpose**: Final documentation and handover.

**Dependency**: Phase 9 (Final Validation).

- [ ] T070 [P] **Final Report**: Generate a final report summarizing results and limitations. **Dependency**: T063. **Verification**: Verify report existence.
- [ ] T071 [P] **Handover**: Prepare handover documentation for future maintainers. **Dependency**: T070. **Verification**: Verify handover docs.

**Checkpoint**: Project complete