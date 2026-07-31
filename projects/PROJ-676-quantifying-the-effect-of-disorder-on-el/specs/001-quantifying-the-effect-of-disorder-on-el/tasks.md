# Tasks: Quantifying the Effect of Disorder on Electronic Transport in 1D Chains

**Input**: Design documents from `/specs/001-quantifying-disorder-effect/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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
- Paths shown below assume single project - adjust based on plan.md structure.
- **Note**: All paths in tasks refer to the project root `projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `data/metadata/`, `tests/`, `docs/`, `specs/` inside `projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/`. Verify existence of directories.
- [ ] T001b [P] Create `.gitkeep` files in `data/raw/`, `data/processed/`, `data/metadata/`, `docs/`, `specs/` to ensure they are tracked.
- [ ] T001c [P] Create `docs/physical_interpretation.md` with a header structure: `# Physical Interpretation`, `## Worked Example: W=2.0`, `## Strong Disorder Limit: W=5.0`. This file will be populated by T029 and T035.
- [ ] T003a Configure linting tools (flake8/pylint) and create `.flake8` and `.pylintrc` in project root. `.flake8` must contain: `[flake8] max-line-length = 88 ignore = E501, W503`.
- [ ] T003b Configure formatting tool (black) and create `pyproject.toml` for black settings in project root
- [ ] T003c [P] Add a CI step or script `run_linting.sh` to execute flake8 and black --check on `code/` and fail the build if violations are found.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes plan artifact updates required to resolve Spec/Plan contradictions.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `code/config.py` with hyperparameters, random seeds, and path constants. **MUST define keys: `W_LIST` (float list), `L_LIST` (int list), `NUM_REALIZATIONS` (int), `SEED` (int), `WEAK_DISORDER_CUTOFF` (float, default 1.0), `NUMERICAL_RESIDUAL_THRESHOLD` (float, default 1e-6), `MAX_TM_ITERATIONS` (int, default 1000).** Verification**: Script to load config and assert all keys exist and are non-empty.
- [ ] T005 [P] Implement `code/generate_hamiltonian.py` (FR-001) to generate 1D tight-binding matrices $L \times L$ with hopping $t=1$ and on-site $\epsilon_i \sim U(-W/2, W/2)
- [ ] T006a [P] Create `disorder_realization_schema.json` in `specs/001-quantifying-disorder-effect/contracts/` for the 'Disorder Realization' entity. **Schema must define properties: W (float), L (int), realization_index (int), seed (int).**
- [ ] T006b [P] Create base data schemas in `specs/001-quantifying-disorder-effect/contracts/` for Hamiltonian (`hamiltonian_schema.json`), Eigenstate (`eigenstate_schema.json`), and Localization Length (`localization_length_schema.json`). **Schema must define properties: L (int), W (float), eigenvalues (array), eigenvectors (array).**
- [ ] T007 [P] Implement `code/storage_utils.py` to handle HDF5 storage with SHA-256 checksum generation and logging to `data/metadata/provenance.json`. **MUST log `realization_index`, `seed`, `W`, `L` for every generated instance.**
- [ ] T008a [P] Implement `code/logger.py` (Constitution Principle VI): Create a `NumericalLogger` class with methods `log_residual(norm, flag)` and `log_convergence(metric)`. Output format: JSON lines appended to `data/metadata/residuals.json`.
- [ ] T008b [P] Implement error handling and logging infrastructure in `code/` to capture numerical residuals and convergence flags for *every* eigenvalue problem (Constitution Principle VI). **Hook `NumericalLogger` into `generate_hamiltonian.py` and `analyze_pr.py`.**
- [ ] T009 [P] Implement `code/main.py` orchestration skeleton using `joblib` for parallel disorder realization execution (FR-011). **MUST define CLI arguments: `--w_range`, `--l_range`, `--n_jobs`. Output**: Log file showing parallel job submission summary and total realizations processed. **Verification**: Run with `--help` and verify arguments exist; run with dummy data to verify log generation.
- [ ] T015a [P] **Update Plan Artifact for Bonferroni Correction**: Edit `plan.md` (specifically the FR/SC Coverage Matrix and Plan Summary) to replace the phrase "Bonferroni correction for pairwise comparisons only" with "Bonferroni correction for the full family of disorder widths". **Rationale**: This aligns the plan with Spec SC-005 (FWER control across full family) and enables T015. **Verification**: Grep `plan.md` for "pairwise" in the context of Bonferroni; ensure it is replaced by "full family". **Depends on**: None (Phase 2).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Localization Length via Participation Ratio (Priority: P1) 🎯 MVP

**Goal**: Generate disordered 1D Hamiltonians and compute localization lengths via PR finite-size scaling to quantify disorder effects.

**Independent Test**: Run on a single realization (L=400, W=1.0), compute eigenstates, extract PR for $|E|<0.1$, and verify PR decreases with increasing W.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for PR calculation output schema in `tests/contract/test_pr_schema.py`. **Asserts output matches `localization_length_schema.json`.**
- [ ] T011 [P] [US1] Integration test for finite-size scaling workflow in `tests/integration/test_pr_scaling.py`. **Asserts existence of `data/processed/scaling_fits.json`.**

### Implementation for User Story 1

- [ ] T017a [P] **Implement Numerical Stability Logger**: Create `code/logger.py` (if not done in T008) and ensure `NumericalLogger` is ready for integration. **Output**: `data/metadata/residuals.json` schema defined. (FR-008, Constitution Principle VI). **Depends on**: T008a.
- [ ] T012 [P] [US1] Implement `code/analyze_pr.py` to compute Participation Ratio $PR = (\sum|\psi_i|^2)^2 / \sum|\psi_i|^4$ for eigenstates within $|E|<0.1$ (FR-002). **Output**: Raw PR values for all eigenstates. **Depends on**: T005, T007, T017a. **Note**: This task produces raw PR values; filtering is handled in T017b.
- [ ] T017b [US1] **Implement Numerical Stability Integration & Filtering Logic**: Integrate `NumericalLogger` calls into `code/analyze_pr.py` (function `compute_eigenstates`). **MUST** implement logic to read `data/metadata/residuals.json` and **exclude** any realization where `converged` is false or `residual_norm` > `config.NUMERICAL_RESIDUAL_THRESHOLD` (default 1e-6) from the final scaling analysis. **Output**: `data/metadata/residuals.json` with JSON lines: `{"task": "eigh|tm", "L": int, "W": float, "realization_index": int, "residual_norm": float, "converged": bool}`. **Traceability**: This exclusion logic is required for SC-005 (Statistical Power) and Constitution Principle VI. (FR-008, Constitution Principle VI). **Depends on**: T017a, T012.
- [ ] T013a [US1] **Implement Finite-Size Scaling Producer**: Run PR scaling for all disorder widths $W$ in the specified range and system sizes $L$ across a range of values (as defined in Plan). **Logic**: For each $W$, generate realizations, compute PR for $|E|<0.1$, **filter out ill-conditioned instances using T017b logic**, and fit PR(L) saturation to extract $\xi$. **Fitting Model**: Use non-linear least squares to fit $PR(L) = A \times (1 - \exp(-L/\xi))$ to the data. **Fallback**: If non-linear fit fails to converge or yields non-physical $\xi$ (e.g., negative), fall back to linear interpolation of PR vs L to estimate saturation and log a warning to `data/metadata/warnings.json`. **Output**: Write results to `data/processed/scaling_fits.json` as a list of objects, each keyed by `disorder_width` and containing `xi`, `uncertainty`, `fit_params`, `L_values`, `PR_values`, `fit_r_squared`, `p_value`. **Note**: `p_value` is derived from the linear regression fit (FR-005) and is required for SC-005. **MUST** generate a diagnostic plot `data/processed/pr_scaling_plot.png` showing PR vs L with the fit line, confidence bands, and labeled axes to verify saturation behavior. (FR-003, Plan correction). **Depends on**: T012, T017b.
- [ ] T013b [US1] **Aggregate PR Scaling Results**: Read `data/processed/scaling_fits.json` and verify all $W$ values are present. Aggregate into a single list for downstream tasks. **Output**: Ensure `data/processed/scaling_fits.json` is complete and valid. **Depends on**: T013a.
- [ ] T015 [US1] **Apply Bonferroni Correction for Full Family of Widths**: **Pre-condition Check**: Read `plan.md`. If `plan.md` contains the string "pairwise" in the context of Bonferroni correction, **FAIL** immediately with an error message: "Plan contradicts Spec SC-005. Plan must state 'full family' for Bonferroni correction." **Action**: If pre-condition passes, read all p-values from `data/processed/scaling_fits.json` (T013b output) for all disorder widths. **Schema Contract**: The input JSON MUST be a list of objects, each containing keys `disorder_width`, `xi`, `uncertainty`, `p_value`. If keys are missing, fail loudly. Apply Bonferroni correction to control FWER at α=0.05 across the **full family of widths** (SC-005). **Correction Factor**: Dynamically calculate as `alpha / len(processed_widths)`. **Statistical Test**: Apply correction to the p-values derived from the t-test on slope deviation from -2. Output to `data/processed/bonferroni_results.json`. **Barrier Note**: This task acts as a barrier for the entire US1 batch and must wait for T013b to complete. (FR-010, SC-005). **Depends on**: T013b, T015a.
- [ ] T014 [US1] Implement `code/stats.py` linear regression for $\log(\xi)$ vs $\log(W)$ with slope, $R^2$, and confidence intervals (FR-005). **MUST** restrict the regression for slope -2 validation (SC-001) to the subset where $W < \text{config.WEAK_DISORDER_CUTOFF}$. **Depends on**: T015.
- [ ] T016 [US1] Add fallback mechanism in `code/analyze_pr.py` to use `scipy.sparse.linalg.eigsh` if `scipy.linalg.eigh` exceeds 6GB RAM for $L=1600$ (FR-008)
- [ ] T033a [US1] Implement boundary case handling in `code/analyze_pr.py` for W=0 (delocalized states). The code must detect W=0 and verify that PR scales extensively with system size (PR ~ L) rather than saturating. **Output: A boolean flag `is_delocalized` in `data/processed/scaling_fits.json` for W=0 cases.** (Spec Edge Cases)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Verify with Transfer Matrix Method (Priority: P2)

**Goal**: Implement Transfer Matrix Method with QR orthogonalization to independently validate PR results.

**Independent Test**: Run TM on same realizations as PR, compute Lyapunov exponents, and verify $\xi_{TM} \approx \xi_{PR}$ within 10% for $L \ge 400$.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for TM output schema in `tests/contract/test_tm_schema.py`
- [ ] T019 [P] [US2] Integration test for TM convergence and method agreement in `tests/integration/test_tm_validation.py`

### Implementation for User Story 2

- [ ] T020b [US2] Implement `code/analyze_tm.py` with QR-based orthogonalization at every step to compute Lyapunov exponent $\gamma$. **Algorithm**: Iterate L from 100 to 1600 in steps of doubling. Compute γ at each step. **Stopping Criterion**: Stop when $|\gamma_{new} - \gamma_{old}|/\gamma_{old} < 1e-5$ (solver convergence) OR when $L=800$ and relative change between $L=400$ and $L=800$ is $\le 5\%$ (physical acceptance criterion per SC-002) OR max `config.MAX_TM_ITERATIONS` (default 1000) iterations. **MUST save the sequence of γ values (convergence trace) to `data/metadata/tm_convergence.json`** to prove convergence (Constitution Principle VI). **Save results to `data/processed/lyapunov_exponents.json`.** (FR-004, FR-009). **Depends on**: T017b.
- [ ] T022 [US2] Add convergence monitoring logic to track relative change in $\gamma$ between consecutive size doublings ($L=100 \to 800$). **Append convergence trace to `data/metadata/tm_convergence.json`.** (FR-009)

**Checkpoint**: US2 core logic complete. Validation against US1 requires Phase 4.5.

---

## Phase 4.5: Cross-Story Validation (Blocking)

**Purpose**: Validate US2 results against US1 results. Requires both US1 and US2 to be complete.

- [ ] T023 [US1+US2] Implement `code/compare_methods.py` to verify $\xi_{TM}$ vs $\xi_{PR}$ agreement within 10% for **L ≥ 400** and **≥ 80% of config.NUM_REALIZATIONS realizations** (calculated as `int(0.8 * config.NUM_REALIZATIONS)`). **MUST verify that `config.NUM_REALIZATIONS` is defined in `code/config.py` before execution.** **Input**: `data/processed/scaling_fits.json` (T013b), `data/processed/lyapunov_exponents.json` (T020b). **Logic**: Compare raw localization lengths against the 10% threshold defined in SC-002. **Note**: This task validates SC-002 (relative error) and does NOT use Bonferroni-corrected p-values from T015 for validation logic. Generate `data/processed/method_agreement_report.json` (US-2 Acceptance Scenario 3). (SC-002, US-2). **Depends on**: T013b, T020b.

**Checkpoint**: US1 and US2 validated against each other.

---

## Phase 5: User Story 3 - Visualize Eigenstate Localization Patterns (Priority: P3)

**Goal**: Visualize individual eigenstate probability densities to provide a physical picture of localization (addressing Feynman's review).

**Independent Test**: Generate a single eigenstate visualization ($L=200, W=2.0, E \approx 0$), confirm exponential decay, and verify decay length matches computed $\xi$.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for visualization output format in `tests/contract/test_viz_schema.py`. **Asserts output JSON contains `decay_length`, `R_squared`, `site_index`.**
- [ ] T025 [P] [US3] Integration test for decay length consistency in `tests/integration/test_viz_validation.py`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `code/visualize.py` to plot $|\psi_i|^2$ vs site index for eigenstates near $E=0$ (FR-006). **Save plot to `data/processed/visualizations/eigenstate_W2.0_L200.png`.**
- [ ] T027 [US3] Implement log-linear fit logic in `code/visualize.py` to calculate decay length and $R^2$ from probability density (US-3 Acceptance Scenario 1). **Append fit parameters to `data/processed/fit_results.json`.**
- [ ] T028 [US3] Add comparison visualization logic to overlay $W=0.5$ and $W=2.0$ states and verify FWHM reduction (US-3 Acceptance Scenario 3). **Save to `data/processed/visualizations/comparison_W0.5_W2.0.png`.**
- [ ] T029 [US3] **Generate Quantitative Physical Summary**: Implement a "worked example" generator in `code/visualize.py` that identifies the specific site index where amplitude drops by half, calculates the decay length, and writes a **quantitative summary** to `docs/physical_interpretation.md` under header "Worked Example: W=2.0". **Algorithm**: Perform linear interpolation on the *logarithm* of the probability density (`log(|ψ_i|^2)`) vs site index to find the site index `i` where the value is closest to `0.5 * max(|ψ|^2)`. **Fallback**: If amplitude never drops to 0.5*max within the chain, report `decay_length = None` and `is_delocalized = True`. **Constraint**: No qualitative analogies, no narrative text, no word count mandates. Only quantitative metrics derived from the fit (R² ≥ 0.95) and decay length. (US-3, FR-006). **Depends on**: T026 and T027.
- [ ] T035 [US3] **Implement "Feynman Review" Response: Strong Disorder Limit**: Extend `code/visualize.py` to generate a specific analysis for the strong disorder limit ($W \gg 1$, e.g., $W=5.0$). **Task**: For a single realization at $W=5.0$, identify the localization center (site with maximum probability density), calculate the distance to the nearest site where `|ψ|^2 < 0.01 * max(|ψ|^2)` (trapping distance), and explicitly verify that the wavefunction exhibits exponential decay behavior consistent with Anderson localization theory. **Output**: Append a section "Strong Disorder Limit: W=5.0" to `docs/physical_interpretation.md` containing: (1) The specific site index of the localization center, (2) The calculated "trapping distance" (in lattice units), (3) A statement confirming whether the interference pattern matches exponential decay behavior. **Constraint**: Must be derived from real computed eigenstates, not theoretical extrapolation. (Reviewer: richard-feynman-simulated, US-3). **Depends on**: T026.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address specific reviewer concerns

- [ ] T015b [US1] Perform a priori power analysis to verify 100 realizations provide ≥80% power to detect slope deviation from -2 at α=0.05 (SC-003). Log results to `data/metadata/power_analysis.json`.
- [ ] T032 Performance optimization: Tune `joblib` parallelization to ensure 1000 realizations complete within 6 hours on CPU cores. Generate `data/metadata/performance_benchmark.json` with wall-clock time and peak RAM metrics (FR-007, SC-006). **Test parameters**: `n_jobs=2`, `backend='loky'`.
- [ ] T033 [P] Additional unit tests for edge cases: $W=0$ (delocalized), large $L$ memory limits, and transfer matrix underflow handling. **Add `test_W_zero_delocalized` in `tests/unit/test_edge_cases.py`.**
- [ ] T034 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility. **Generate `validation_report.json` with pass/fail status.**
- [ ] T036 [P] **Implement "Physical Picture" Narrative Generator**: Create a script in `code/visualize.py` (function `generate_physical_narrative`) that synthesizes the quantitative results from T029 and T035 into a concise, non-mathematical explanation of the electron's behavior for `docs/physical_interpretation.md`. **Algorithm**: Read the "Worked Example: W=2.0" and "Strong Disorder Limit: W=5.0" sections. **Template**: 
  - **Localized Case**: "At W={W}, the electron is trapped at site {site} with a distance of {dist} lattice units. The decay length is {decay}."
  - **Delocalized Case (W=0)**: "At W={W}, the electron is not trapped (delocalized) at site N/A with a distance of N/A lattice units. The decay length is N/A."
  **Constraint**: The narrative MUST be strictly derived from the computed metrics (site indices, distances, decay lengths) and must NOT introduce new theoretical claims or qualitative analogies not present in the data. It must explicitly answer: "When does it stop wandering?" and "Where is it trapped?" using the specific site indices calculated in T029/T035. (Reviewer: richard-feynman-simulated, US-3). **Depends on**: T029, T035.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Cross-Story Validation (Phase 4.5)**: Depends on completion of Phase 3 (US1) and Phase 4 (US2). **Specifically depends on T013b and T020b.**
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for PR calculation output schema in tests/contract/test_pr_schema.py"
Task: "Integration test for finite-size scaling workflow in tests/integration/test_pr_scaling.py"

# Launch all models for User Story 1 together:
Task: "Implement code/analyze_pr.py to compute Participation Ratio"
# Note: T013a (Scaling Producer) depends on T012, so T013a cannot run in parallel with T012.
# T013b (Aggregator) depends on T013a, so it cannot run in parallel with T013a.
# T015 (Bonferroni) depends on T013b, so it cannot run in parallel with T013b.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Run Phase 4.5: Cross-Story Validation → Verify agreement
5. Add User Story 3 → Test independently → Deploy/Demo
6. Run Phase N: Polish → Generate physical narrative (T036)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently (Phase 4.5 validates US1+US2)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Crucial**: All data generation must use real random seeds logged in `provenance.json`; no synthetic/fake data allowed.
- **Crucial**: T029 specifically addresses the "Feynman" review by demanding a quantitative summary of physical interpretation based on computed metrics, avoiding scope creep. No qualitative analogies or word counts.
- **Crucial**: T013a overrides the simplified FR-003 proportionality to implement the correct finite-size scaling saturation logic as per the Plan.
- **Crucial**: T015 applies Bonferroni correction for FWER across ALL widths (full family), aligning with SC-005, and enforces the Spec over the Plan if they contradict.
- **Crucial**: T017 is split into T017a (Parallel Logger) and T017b (Sequential Integration/Filtering) to ensure numerical stability logging is integrated before T012/T013 implementation begins and that ill-conditioned instances are excluded.
- **Crucial**: T023 validates SC-002 (relative error) and does NOT use Bonferroni p-values.
- **Crucial**: T035 specifically addresses the "Feynman" review's request for a "worked example" in the strong disorder limit ($W \gg 1$) to demonstrate the physical picture of "trapping" and "suppression of diffusion" without relying solely on abstract fitting. It requires identifying specific lattice sites and distances, directly answering "when does it stop wandering?".
- **Crucial**: Ta explicitly lists required system sizes $L \in \{100, 200, 400, 800, 1600\}$ and disorder widths $W \in [0.1, 0.2, \dots, 2.0]$.
- **Crucial**: T015 dynamically calculates Bonferroni factor based on `len(processed_widths)`.
- **Crucial**: T029 and T035 define specific algorithms for "half-amplitude site" and "localization center" to ensure deterministic implementation.
- **Crucial**: T036 synthesizes the quantitative findings from T029/T035 into a direct answer to the reviewer's request for a "physical picture" without equations, strictly grounded in the computed site indices and distances using a specific text template with fallback for delocalized states.
- **Crucial**: T014 explicitly restricts the slope -2 validation to the weak disorder subset ($W < 1.0$).
- **Crucial**: T015a ensures the plan.md is updated to reflect the full family correction before T015 runs.