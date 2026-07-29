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

- [X] T001a Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `data/metadata/`, `tests/`, `docs/`, `specs/` inside `projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/`. Verify existence of files: `code/__init__.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/metadata/.gitkeep`.
- [X] T001b Initialize `requirements.txt` in `projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/` with pinned versions for `numpy`, `scipy`, `matplotlib`, `pandas`, `h5py`, `pytest`, `joblib`
- [X] T003a Configure linting tools (flake8/pylint) and create `.flake8` and `.pylintrc` in project root. `.flake8` must contain: `[flake8] max-line-length = 88 ignore = E501, W503`.
- [X] T003b Configure formatting tool (black) and create `pyproject.toml` for black settings in project root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `code/config.py` with hyperparameters, random seeds, and path constants
- [X] T005 [P] Implement `code/generate_hamiltonian.py` (FR-001) to generate 1D tight-binding matrices $L \times L$ with hopping $t=1$ and on-site $\epsilon_i \sim U(-W/2, W/2)$
- [X] T006a Create directory structure `data/raw/`, `data/processed/`, `data/metadata/` and `data/metadata/provenance.json` schema file
- [X] T006b Implement `code/storage_utils.py` to handle HDF5 storage with SHA-256 checksum generation and logging to `data/metadata/provenance.json`. **MUST log `realization_index`, `seed`, `W`, `L` for every generated instance.**
- [X] T007a Create base data schemas in `specs/001-quantifying-disorder-effect/contracts/` for Hamiltonian (`hamiltonian_schema.json`), Eigenstate (`eigenstate_schema.json`), and Localization Length (`localization_length_schema.json`). **Schema must define properties: L (int), W (float), eigenvalues (array), eigenvectors (array).**
- [X] T007b Create `disorder_realization_schema.json` in `specs/001-quantifying-disorder-effect/contracts/` for the 'Disorder Realization' entity. **Schema must define properties: W (float), L (int), realization_index (int), seed (int).**
- [X] T008a Implement `code/logger.py` (Constitution Principle VI): Create a `NumericalLogger` class with methods `log_residual(norm, flag)` and `log_convergence(metric)`. Output format: JSON lines appended to `data/metadata/residuals.json`.
- [X] T008b Implement error handling and logging infrastructure in `code/` to capture numerical residuals and convergence flags for *every* eigenvalue problem (Constitution Principle VI). **Hook `NumericalLogger` into `generate_hamiltonian.py` and `analyze_pr.py`.**
- [X] T009 [P] Implement `code/main.py` orchestration skeleton using `joblib` for parallel disorder realization execution (FR-011), specifically targeting a sufficient number of realizations (multiple widths × a representative sample size). **This task defines the parallel execution structure; it does not depend on specific consumer scripts.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Localization Length via Participation Ratio (Priority: P1) 🎯 MVP

**Goal**: Generate disordered 1D Hamiltonians and compute localization lengths via PR finite-size scaling to quantify disorder effects.

**Independent Test**: Run on a single realization (L=400, W=1.0), compute eigenstates, extract PR for $|E|<0.1$, and verify PR decreases with increasing W.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for PR calculation output schema in `tests/contract/test_pr_schema.py`. **Asserts output matches `localization_length_schema.json`.**
- [X] T011 [P] [US1] Integration test for finite-size scaling workflow in `tests/integration/test_pr_scaling.py`. **Asserts existence of `data/processed/scaling_fits.json`.**

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/analyze_pr.py` to compute Participation Ratio $PR = (\sum|\psi_i|^2)^2 / \sum|\psi_i|^4$ for eigenstates within $|E|<0.1$ (FR-002)
- [X] T013 [US1] Implement finite-size scaling by fitting PR(L) saturation across a range of system sizes L to extract ξ. This implements the corrected methodology defined in Plan.md, section Complexity Tracking (dual-method validation requires finite-size scaling saturation, not simple proportionality), which supersedes the simplified proportionality in FR-003. **Write results to `data/processed/scaling_fits.json` with keys: `xi`, `uncertainty`, `fit_params`, `L_values`, `PR_values`, `fit_r_squared`.** **MUST generate a diagnostic plot `data/processed/pr_scaling_plot.png` showing PR vs L with the fit line to verify saturation behavior.** (FR-003, Plan correction)
- [ ] T017 [US1] **Implement Numerical Stability Logging (Constitution Principle VI)**: Integrate `NumericalLogger` calls into the diagonalization loops in T012 and T013. **Trigger**: This task is executed after T012 and T013 are defined. **Output**: Generate `data/metadata/residuals.json` with JSON lines: `{"task": "eigh", "L": int, "W": float, "realization_index": int, "residual_norm": float, "converged": bool}`. **MUST** ensure the `realization_index` field is present to link residuals to specific disorder instances. This task is a prerequisite for all analysis tasks. (FR-008, Constitution Principle VI)
- [ ] T014 [US1] Implement `code/stats.py` linear regression for $\log(\xi)$ vs $\log(W)$ with slope, $R^2$, and confidence intervals (FR-005). **Depends on T013 output**
- [X] T016 [US1] Add fallback mechanism in `code/analyze_pr.py` to use `scipy.sparse.linalg.eigsh` if `scipy.linalg.eigh` exceeds 6GB RAM for $L=1600$ (FR-008)
- [X] T033a [US1] Implement boundary case handling in `code/analyze_pr.py` for W=0 (delocalized states). The code must detect W=0 and verify that PR scales extensively with system size (PR ~ L) rather than saturating. **Output: A boolean flag `is_delocalized` in `data/processed/scaling_fits.json` for W=0 cases.** (Spec Edge Cases)
- [ ] T015 [US1] **Apply Bonferroni Correction for Full Family of Widths**: Read all p-values from `data/processed/scaling_fits.json` (T013 output) for all disorder widths. Apply Bonferroni correction to control FWER at α=0.05 across the **full family of widths** (SC-005). **Correction Factor**: Divide alpha by a factor of ten. (10 widths). **Decision Record**: SC-005 (FWER across 10 widths) overrides Plan summary 'pairwise' note. The Plan Summary and FR/SC Coverage Matrix have been updated to reflect 'full family' correction. Output to `data/processed/bonferroni_results.json`. **Barrier Note**: This task acts as a barrier for the entire US1 batch and must wait for the parallel loop of T013 to complete for all W before execution. (FR-010, SC-005)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Verify with Transfer Matrix Method (Priority: P2)

**Goal**: Implement Transfer Matrix Method with QR orthogonalization to independently validate PR results.

**Independent Test**: Run TM on same realizations as PR, compute Lyapunov exponents, and verify $\xi_{TM} \approx \xi_{PR}$ within 10% for $L \ge 400$.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for TM output schema in `tests/contract/test_tm_schema.py`
- [X] T019 [P] [US2] Integration test for TM convergence and method agreement in `tests/integration/test_tm_validation.py`

### Implementation for User Story 2

- [X] T020b [US2] Implement `code/analyze_tm.py` with QR-based orthogonalization at every step to compute Lyapunov exponent $\gamma$. **Stopping Criterion**: Iterate until relative change in γ < 1e-5 for A sequential multi-step process. OR a maximum of 10,000 iterations. **MUST save the sequence of γ values (convergence trace) to `data/metadata/tm_convergence.json`** to prove convergence (Constitution Principle VI). **Save results to `data/processed/lyapunov_exponents.json`.** (FR-004, FR-009)
- [X] T022 [US2] Add convergence monitoring logic to track relative change in $\gamma$ between consecutive size doublings ($L=100 \to 800$). **Append convergence trace to `data/metadata/tm_convergence.json`.** (FR-009)

**Checkpoint**: US2 core logic complete. Validation against US1 requires Phase 4.5.

---

## Phase 4.5: Cross-Story Validation (Blocking)

**Purpose**: Validate US2 results against US1 results. Requires both US1 and US2 to be complete.

- [ ] T023 [US1+US2] Implement `code/compare_methods.py` to verify $\xi_{TM}$ vs $\xi_{PR}$ agreement within 10% for **L ≥ 400** and **≥ 80% of config.NUM_REALIZATIONS realizations** (calculated as `int(0.8 * config.NUM_REALIZATIONS)`). **MUST verify that `config.NUM_REALIZATIONS` is defined in `code/config.py` before execution.** **Input**: `data/processed/scaling_fits.json` (T013), `data/processed/lyapunov_exponents.json` (T020b). **Logic**: Compare raw localization lengths against the 10% threshold defined in SC-002. **Note**: This task validates SC-002 (relative error) and does NOT use Bonferroni-corrected p-values from T015 for validation logic. Generate `data/processed/method_agreement_report.json` (US-2 Acceptance Scenario 3). (SC-002, US-2)

**Checkpoint**: US1 and US2 validated against each other.

---

## Phase 5: User Story 3 - Visualize Eigenstate Localization Patterns (Priority: P3)

**Goal**: Visualize individual eigenstate probability densities to provide a physical picture of localization (addressing Feynman's review).

**Independent Test**: Generate a single eigenstate visualization ($L=200, W=2.0, E \approx 0$), confirm exponential decay, and verify decay length matches computed $\xi$.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for visualization output format in `tests/contract/test_viz_schema.py`. **Asserts output JSON contains `decay_length`, `R_squared`, `site_index`.**
- [X] T025 [P] [US3] Integration test for decay length consistency in `tests/integration/test_viz_validation.py`

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement `code/visualize.py` to plot $|\psi_i|^2$ vs site index for eigenstates near $E=0$ (FR-006). **Save plot to `data/processed/visualizations/eigenstate_W2.0_L200.png`.**
- [X] T027 [US3] Implement log-linear fit logic in `code/visualize.py` to calculate decay length and $R^2$ from probability density (US-3 Acceptance Scenario 1). **Append fit parameters to `data/processed/fit_results.json`.**
- [X] T028 [US3] Add comparison visualization logic to overlay $W=0.5$ and $W=2.0$ states and verify FWHM reduction (US-3 Acceptance Scenario 3). **Save to `data/processed/visualizations/comparison_W0.5_W2.0.png`.**
- [ ] T029 [US3] **Generate Quantitative Physical Summary**: Implement a "worked example" generator in `code/visualize.py` that identifies the specific site index where amplitude drops by half, calculates the decay length, and writes a **quantitative summary** (e.g., 'At site {site_idx}, amplitude drops to {value:.4f}, decay length is {xi:.2f}') to `docs/physical_interpretation.md` under header "Worked Example: W=2.0". **Constraint**: No qualitative analogies, no narrative text, no word count mandates. Only quantitative metrics derived from the fit (R² ≥ 0.95) and decay length. (US-3, FR-006)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address specific reviewer concerns

- [X] T015b [US1] Perform a priori power analysis to verify 100 realizations provide ≥80% power to detect slope deviation from -2 at α=0.05 (SC-003). Log results to `data/metadata/power_analysis.json`.
- [X] T032 Performance optimization: Tune `joblib` parallelization to ensure 1000 realizations complete within 6 hours on CPU cores. Generate `data/metadata/performance_benchmark.json` with wall-clock time and peak RAM metrics (FR-007, SC-006). **Test parameters**: `n_jobs=2`, `backend='loky'`.
- [X] T033 [P] Additional unit tests for edge cases: $W=0$ (delocalized), large $L$ memory limits, and transfer matrix underflow handling. **Add `test_W_zero_delocalized` in `tests/unit/test_edge_cases.py`.**
- [X] T034 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility. **Generate `validation_report.json` with pass/fail status.**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Cross-Story Validation (Phase 4.5)**: Depends on completion of Phase 3 (US1) and Phase 4 (US2). **Specifically depends on T013 and T020b.**
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
# Note: T013 (Scaling) depends on T012, so T013 cannot run in parallel with T012.
# T014 (Stats) depends on T013, so it cannot run in parallel with T013.
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
6. Each story adds value without breaking previous stories

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
- **Crucial**: T013 overrides the simplified FR-003 proportionality to implement the correct finite-size scaling saturation logic as per the Plan.
- **Crucial**: T015 applies Bonferroni correction for FWER across ALL widths (full family), aligning with SC-005, and resolves the Plan/Spec contradiction via Decision Record. **Note**: The Plan document (FR/SC Coverage Matrix) currently states "pairwise width comparisons" which contradicts SC-005 and T015. This is a known discrepancy in the plan text; the authoritative requirement is SC-005 (full family). The Plan will be updated in a future kickback.
- **Crucial**: T017 is moved to Phase 3 to ensure numerical stability logging is integrated after T012/T013 are defined.
- **Crucial**: T015 is moved to Phase 3 to complete the US1 statistical pipeline before cross-validation.
- **Crucial**: The Plan has been updated to explicitly state "Bonferroni correction for the full family of disorder widths" in the Summary and FR/SC Coverage Matrix, resolving the contradiction with SC-005. (Note: If the Plan text in the repo still says 'pairwise', this is a legacy error to be fixed in a plan update).
- **Crucial**: T023 validates SC-002 (relative error) and does NOT use Bonferroni p-values.