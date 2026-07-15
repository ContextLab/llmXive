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

- [ ] T001a Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `data/metadata/`, `tests/`, `docs/`, `specs/` inside `projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/` <!-- FAILED: unspecified -->
- [ ] T001b Initialize `requirements.txt` in `projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/` with pinned versions for `numpy`, `scipy`, `matplotlib`, `pandas`, `h5py`, `pytest`, `joblib`
- [ ] T003a Configure linting tools (flake8/pylint) and create `.flake8` and `.pylintrc` in project root
- [ ] T003b Configure formatting tool (black) and create `pyproject.toml` for black settings in project root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `code/config.py` with hyperparameters, random seeds, and path constants
- [X] T005 [P] Implement `code/generate_hamiltonian.py` (FR-001) to generate 1D tight-binding matrices $L \times L$ with hopping $t=1$ and on-site $\epsilon_i \sim U(-W/2, W/2)$
- [ ] T006a Create directory structure `data/raw/`, `data/processed/`, `data/metadata/` and `data/metadata/provenance.json` schema file
- [X] T006b Implement `code/storage_utils.py` to handle HDF5 storage with SHA-256 checksum generation and logging to `data/metadata/provenance.json`
- [~] T007a Create base data schemas in `specs/001-quantifying-disorder-effect/contracts/` for Hamiltonian (`hamiltonian_schema.json`), Eigenstate (`eigenstate_schema.json`), and Localization Length (`localization_length_schema.json`)
- [~] T007b Create `disorder_realization_schema.json` in `specs/001-quantifying-disorder-effect/contracts/` for the 'Disorder Realization' entity (W, L, realization_index)
- [~] T008 Implement error handling and logging infrastructure in `code/` to capture numerical residuals and convergence flags for *every* eigenvalue problem (Constitution Principle VI; exceeds Spec's minimal 'warning' requirement for reproducibility)
- [X] T009 Implement `code/main.py` orchestration skeleton using `joblib` for parallel disorder realization execution (FR-011), specifically targeting a sufficient number of realizations (multiple widths × 100 samples)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Localization Length via Participation Ratio (Priority: P1) 🎯 MVP

**Goal**: Generate disordered 1D Hamiltonians and compute localization lengths via PR finite-size scaling to quantify disorder effects.

**Independent Test**: Run on a single realization (L=400, W=1.0), compute eigenstates, extract PR for $|E|<0.1$, and verify PR decreases with increasing W.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for PR calculation output schema in `tests/contract/test_pr_schema.py`
- [X] T011 [P] [US1] Integration test for finite-size scaling workflow in `tests/integration/test_pr_scaling.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/analyze_pr.py` to compute Participation Ratio $PR = (\sum|\psi_i|^2)^2 / \sum|\psi_i|^4$ for eigenstates within $|E|<0.1$ (FR-002)
- [~] T013 [US1] Implement finite-size scaling by fitting PR(L) saturation across a range of system sizes L to extract ξ. This implements the corrected methodology defined in Plan.md, section Complexity Tracking (dual-method validation requires finite-size scaling saturation, not simple proportionality), which supersedes the simplified proportionality in FR-003. Output a `dict` with keys `xi`, `uncertainty`, and `fit_params` (FR-003, Plan correction)
- [X] T014 [US1] Implement `code/stats.py` linear regression for $\log(\xi)$ vs $\log(W)$ with slope, $R^2$, and confidence intervals (FR-005). **Depends on T013 output**
- [~] T015 [US1] Aggregate results from T014 for *all* disorder widths, then apply Bonferroni correction for FWER across the full family of tests (FR-010, SC-005). Note: The Plan's 'pairwise' summary refers to result interpretation, but the correction scope must be global to satisfy SC-005. **Depends on T014 output**
- [~] T015b [US1] Perform a priori power analysis to verify 100 realizations provide ≥80% power to detect slope deviation from -2 at α=0.05 (SC-003). Log results to `data/metadata/power_analysis.json`.
- [X] T016 [US1] Add fallback mechanism in `code/analyze_pr.py` to use `scipy.sparse.linalg.eigsh` if `scipy.linalg.eigh` exceeds 6GB RAM for $L=1600$ (FR-008)
- [ ] T017 [US1] Add logging for residual norms and convergence flags for every eigenvalue problem to `data/metadata/residuals.json` (Constitution Principle VI)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Verify with Transfer Matrix Method (Priority: P2)

**Goal**: Implement Transfer Matrix Method with QR orthogonalization to independently validate PR results.

**Independent Test**: Run TM on same realizations as PR, compute Lyapunov exponents, and verify $\xi_{TM} \approx \xi_{PR}$ within 10% for $L \ge 400$.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for TM output schema in `tests/contract/test_tm_schema.py`
- [ ] T019 [P] [US2] Integration test for TM convergence and method agreement in `tests/integration/test_tm_validation.py`

### Implementation for User Story 2

- [ ] T020a [P] [US2] Research Task: Determine the iteration count for Transfer Matrix products based on convergence studies in literature. Document the chosen count and rationale in `docs/research_notes.md`.
- [ ] T020b [US2] Implement `code/analyze_tm.py` with QR-based orthogonalization at every step to compute Lyapunov exponent $\gamma$. Stopping Criterion: Iterate until relative change in γ < 1e-4 for 3 consecutive steps OR max 2000 iterations. (FR-004, FR-009)
- [ ] T021 [US2] Implement logarithmic accumulation in `code/analyze_tm.py` to prevent numerical underflow for large $L$ (FR-009)
- [ ] T022 [US2] Add convergence monitoring logic to track relative change in $\gamma$ between consecutive size doublings ($L=100 \to 800$)

**Checkpoint**: US2 core logic complete. Validation against US1 requires Phase 4.5.

---

## Phase 4.5: Cross-Story Validation (Blocking)

**Purpose**: Validate US2 results against US1 results. Requires both US1 and US2 to be complete.

- [ ] T023 [US2] Implement `code/compare_methods.py` to verify $\xi_{TM}$ vs $\xi_{PR}$ agreement within 10% for **L ≥ 400** and **≥ 80% of config.NUM_REALIZATIONS realizations** (calculated as `int(0.8 * config.NUM_REALIZATIONS)`). Generate `data/processed/method_agreement_report.json` (US-2 Acceptance Scenario 3). **Input: data/processed/localization_lengths.json (aggregated from T014/T015)**. **Depends on: T015 (aggregated results)**

**Checkpoint**: US1 and US2 validated against each other.

---

## Phase 5: User Story 3 - Visualize Eigenstate Localization Patterns (Priority: P3)

**Goal**: Visualize individual eigenstate probability densities to provide a physical picture of localization (addressing Feynman's review).

**Independent Test**: Generate a single eigenstate visualization ($L=200, W=2.0, E \approx 0$), confirm exponential decay, and verify decay length matches computed $\xi$.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for visualization output format in `tests/contract/test_viz_schema.py`
- [ ] T025 [P] [US3] Integration test for decay length consistency in `tests/integration/test_viz_validation.py`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `code/visualize.py` to plot $|\psi_i|^2$ vs site index for eigenstates near $E=0$ (FR-006)
- [ ] T027 [US3] Implement log-linear fit logic in `code/visualize.py` to calculate decay length and $R^2$ from probability density (US-3 Acceptance Scenario 1)
- [ ] T028 [US3] Add comparison visualization logic to overlay $W=0.5$ and $W=2.0$ states and verify FWHM reduction (US-3 Acceptance Scenario 3)
- [ ] T029 [US3] **Address Feynman Review**: Implement a "worked example" generator in `code/visualize.py` that identifies the specific site index where amplitude drops by half, calculates the decay length, and writes a **human-readable summary string** (e.g., 'At site {site_idx}, amplitude drops to {value:.4f}') to `docs/physical_interpretation.md` (US-3, Feynman Review)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address specific reviewer concerns

- [ ] T030 [P] Documentation updates: Create `docs/physical_interpretation.md` including a "Physical Interpretation" section explaining the electron's behavior without equations (Addressing Reviewer Feynman)
- [ ] T031 Code cleanup and refactoring to ensure modular separation of PR and TM logic
- [ ] T032 Performance optimization: Tune `joblib` parallelization to ensure 1000 realizations complete within 6 hours on 2 CPU cores. Generate `data/metadata/performance_benchmark.json` with wall-clock time and peak RAM metrics (FR-007, SC-006)
- [ ] T033 [P] Additional unit tests for edge cases: $W=0$ (delocalized), large $L$ memory limits, and transfer matrix underflow handling
- [ ] T034 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T035 [US3] **Address Feynman Review (Physical Picture)**: Implement a script in `code/physical_narrative.py` that iterates through a representative set of disorder widths ($W=0.1, 1.0, 10.0$) and generates a **qualitative narrative** describing the electron's "wiggling" behavior, explicitly identifying the transition from "wandering" (delocalized) to "trapped" (localized) based on the computed localization length, and writes this narrative to `docs/physical_narrative.md` (Feynman Review: "Can you sketch what happens... without the math?")
- [ ] T036 [US3] **Address Feynman Review (Anderson's Argument)**: Implement a verification task in `code/verify_anderson_1958.py` that explicitly checks if the strong-disorder limit (simulated by W=100.0) recovers the interference-based suppression of diffusion predicted by Anderson (1958), and logs a "Pass/Fail" status with a brief textual explanation to `data/metadata/anderson_verification.json` (Feynman Review: "Does your work recover that picture?")

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Cross-Story Validation (Phase 4.5)**: Depends on completion of Phase 3 (US1) and Phase 4 (US2)
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
- **Crucial**: Task T029 specifically addresses the "Feynman" review by demanding a physical, non-equation explanation of the electron's behavior.
- **Crucial**: T013 overrides the simplified FR-003 proportionality to implement the correct finite-size scaling saturation logic as per the Plan.
- **Crucial**: T015 applies Bonferroni correction for FWER across all widths, aligning with SC-005.
- **Crucial**: T035 and T036 directly address the specific "physical picture" and "Anderson's 1958 argument" concerns raised by the Feynman reviewer, ensuring the project delivers a conceptual understanding beyond numerical fitting.