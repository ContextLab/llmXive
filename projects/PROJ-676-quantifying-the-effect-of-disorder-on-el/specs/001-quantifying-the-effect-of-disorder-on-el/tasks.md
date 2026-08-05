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

- [X] T001a [P] Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `data/metadata/`, `tests/`, `docs/`, `specs/` inside `projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/`. **Command**: `mkdir -p code data/raw data/processed data/metadata tests docs specs`. Verify existence of directories.
- [X] T001b [P] Create `.gitkeep` files in `data/raw/`, `data/processed/`, `data/metadata/`, `docs/`, `specs/` to ensure they are tracked. **Command**: `touch data/raw/.gitkeep data/processed/.gitkeep data/metadata/.gitkeep docs/.gitkeep specs/.gitkeep`.
- [X] T001c [P] Create `docs/physical_interpretation.md` with a header structure: `# Physical Interpretation`, `## Worked Example: W=2.0`, `## Strong Disorder Limit: W=5.0`. This file will be populated by T029 and T035.
- [X] T003a [P] Configure linting tools (flake8/pylint) and create `.flake8` and `.pylintrc` in project root. `.flake8` must contain: `[flake8] max-line-length = 88 ignore = E501, W503`. **File**: `projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/.flake8`.
- [X] T003b [P] Configure formatting tool (black) and create `pyproject.toml` for black settings in project root. **File**: `projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/pyproject.toml`.
- [X] T003c [P] Add a CI step or script `run_linting.sh` to execute flake8 and black --check on `code/` and fail the build if violations are found. **Script**: `projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/run_linting.sh` with content: `#!/bin/bash; flake8 code/; black --check code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes plan artifact updates required to resolve Spec/Plan contradictions.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `code/config.py` with hyperparameters, random seeds, and path constants. **MUST define keys**: `W_LIST` (float list), `L_LIST` (int list), `NUM_REALIZATIONS` (int), `SEED` (int), `WEAK_DISORDER_CUTOFF` (float, default 1.0), `NUMERICAL_RESIDUAL_THRESHOLD` (float, default 1e-6), `MAX_TM_ITERATIONS` (int, default 1000, **justified in research.md based on convergence studies**). **Verification**: Script to load config and assert all keys exist and are non-empty.
- [X] T005 [P] Implement `code/generate_hamiltonian.py` (FR-001) to generate 1D tight-binding matrices $L \times L$ with hopping $t=1$ and on-site $\epsilon_i \sim U(-W/2, W/2)$. **Depends on**: T017a.
- [X] T006a [P] Create `disorder_realization_schema.json` in `specs/001-quantifying-disorder-effect/contracts/` for the 'Disorder Realization' entity. **Schema Content**:
```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "title": "Disorder Realization",
 "type": "object",
 "properties": {
 "W": {"type": "number"},
 "L": {"type": "integer"},
 "realization_index": {"type": "integer"},
 "seed": {"type": "integer"}
 },
 "required": ["W", "L", "realization_index", "seed"]
}
```
- [X] T006b [P] Create base data schemas in `specs/001-quantifying-disorder-effect/contracts/` for Hamiltonian (`hamiltonian_schema.json`), Eigenstate (`eigenstate_schema.json`), and Localization Length (`localization_length_schema.json`). **Schema Content**:
```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "title": "Hamiltonian",
 "type": "object",
 "properties": {
 "L": {"type": "integer"},
 "W": {"type": "number"},
 "eigenvalues": {"type": "array", "items": {"type": "number"}},
 "eigenvectors": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}}
 },
 "required": ["L", "W", "eigenvalues", "eigenvectors"]
}
```
```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "title": "Eigenstate",
 "properties": {
 "energy": {"type": "number"},
 "probability_density": {"type": "array", "items": {"type": "number"}},
 "participation_ratio": {"type": "number"}
 },
 "required": ["energy", "probability_density", "participation_ratio"]
}
```
```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "title": "Localization Length",
 "properties": {
 "xi": {"type": "number"},
 "uncertainty": {"type": "number"},
 "disorder_width": {"type": "number"}
 },
 "required": ["xi", "uncertainty", "disorder_width"]
}
```
- [X] T007 [P] Implement `code/storage_utils.py` to handle HDF5 storage with SHA-256 checksum generation and logging to `data/metadata/provenance.json`. **MUST log** `realization_index`, `seed`, `W`, `L` for every generated instance.
- [X] T017a [P] **Implement Numerical Stability Logger Class**: Create `code/logger.py` with a `NumericalLogger` class. **MUST** implement methods `log_residual(norm, flag)` and `log_convergence(metric)`. **Output Format**: JSON lines appended to `data/metadata/residuals.json`. **MUST** use file open mode 'a' (append) and call `file.flush()` after every write to ensure real-time streaming. **MUST** provide utility functions/decorators to facilitate injection of logging calls. **Note**: This task implements the class only. (FR-008, Constitution Principle VI).
- [X] T017b [P] **Inject Logging Hooks**: Integrate `NumericalLogger` into `code/generate_hamiltonian.py` (T005) and `code/analyze_pr.py` (T012). **MUST** call `log_residual` for every eigenvalue problem solved. **Depends on**: T017a, T005. (Note: T017b modifies code/generate_hamiltonian.py; T005 creates the base file). (FR-008, Constitution Principle VI).
- [X] T015a [P] **Update Plan Artifact for Bonferroni Correction**: Edit `plan.md` (specifically the FR/SC Coverage Matrix and Plan Summary) to replace the phrase "Bonferroni correction for pairwise comparisons only" with "Bonferroni correction for the full family of disorder widths". **Rationale**: This aligns the plan with Spec SC-005 (FWER control across full family) and enables T015. **Verification**: Provide a diff or updated content reference showing the change; grep alone is insufficient. **Depends on**: None (Phase 2).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Localization Length via Participation Ratio (Priority: P1) 🎯 MVP

**Goal**: Generate disordered 1D Hamiltonians and compute localization lengths via PR finite-size scaling to quantify disorder effects.

**Independent Test**: Run on a single realization (L=400, W=1.0), compute eigenstates, extract PR for $|E|<0.1$, and verify PR decreases with increasing W.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for PR calculation output schema in `tests/contract/test_pr_schema.py`. **Asserts output matches `localization_length_schema.json`**.
- [ ] T011-Impl [P] [US1] Integration test for finite-size scaling workflow in `tests/integration/test_pr_scaling.py`. **Asserts existence of `data/processed/scaling_fits.json` with schema validation: keys `xi` (float), `uncertainty` (float), `disorder_width` (float) must be present and non-null.** **Depends on**: T013d-Aggregate. **Note**: This task asserts the artifact produced by T013d-Aggregate. If the file is missing, the test fails with a clear error message.

### Implementation for User Story 1

- [X] T012 [US1] **Implement `code/analyze_pr.py`**: Compute Participation Ratio $PR = (\sum|\psi_i|^2)^2 / \sum|\psi_i|^4$ for eigenstates within $|E|<0.1$ (FR-002). **MUST** integrate the logging hooks defined in T017b to record residuals and convergence flags. **Output**: Write raw PR values for all eigenstates to `data/processed/pr_raw.json` (list of objects with `W`, `L`, `realization_index`, `energy`, `pr`). **Depends on**: T005, T007, T017b.
- [ ] T013b [US1] **Generate Multi-L PR Dataset**: Run PR computation for all disorder widths $W$ in `config.W_LIST` and all system sizes $L$ in `config.L_LIST`. **Logic**: Read configuration, generate Hamiltonians (T005), compute PR (T012), and aggregate. **Output**: Write raw PR data for all L, W, realization combinations to `data/processed/pr_raw_multiL.json`. **Schema**: List of objects with `W`, `L`, `realization_index`, `energy`, `pr`. **Depends on**: T012.
- [ ] T013a-Fit [US1] **Implement Finite-Size Scaling Fit Logic**: Read `data/processed/pr_raw_multiL.json` (from T013b). **Fitting Model**: Fit PR(L) to a saturation curve (e.g., exponential or power-law saturation) consistent with 1D localization theory to extract $\xi$. **Constraint**: **DO NOT** fall back to linear interpolation. If the fit fails to converge or yields non-physical $\xi$ (e.g., negative, R^2 < 0.95), **log a warning to `data/metadata/warnings.json` and skip this realization** (do not raise a hard error) to preserve SC-006 (Compute feasibility). **Output**: Write definitive fit results to `data/processed/pr_scaling_raw.json`. **Depends on**: T013b.
- [ ] T013c [US1] **Implement W=0 Edge Case Handler**: Detect W=0 in `config.W_LIST`. If present, compute PR for $L \in [100, 200, 400]$ using T012 logic. **Logic**: Verify PR scales extensively (PR ~ L). **Output**: Write results to `data/processed/w0_results.json` with `is_delocalized: true` and `PR_values`. **CRITICAL**: Ensure W=0 results are **excluded** from downstream log-log regression (T013e-Reg). **Depends on**: T012, T013b.
- [ ] T013d-Aggregate [US1] **Aggregate Scaling Results**: Read `data/processed/pr_scaling_raw.json` (T013a-Fit) and `data/processed/w0_results.json` (T013c). Merge W>0 fits and W=0 delocalized results into a single list. **Output**: Write merged list to `data/processed/scaling_fits.json`. **Schema**: List of objects with `disorder_width`, `xi`, `uncertainty`, `is_delocalized` (optional). **Depends on**: T013a-Fit, T013c.
- [ ] T013e-Reg [US1] **Perform Global Regression**: Read `data/processed/scaling_fits.json` (T013d-Aggregate). **Logic**: Filter to W > 0. Perform linear regression of $\log(\xi)$ vs $\log(W)$. **CRITICAL**: Explicitly exclude W=0 from this regression to avoid log(0) errors. **Output**: Regression parameters. **Depends on**: T013d-Aggregate.
- [ ] T013e-Test [US1] **Calculate T-Statistic**: Read regression parameters from T013e-Reg. **Logic**: Calculate t-statistic for slope deviation from -2. **Output**: T-statistic and p-value. **Depends on**: T013e-Reg.
- [ ] T013e-Write [US1] **Write Global Regression Results**: Serialize results to `data/processed/global_regression.json` with `slope`, `p_value`, `confidence_interval`, `r_squared`. **Depends on**: T013e-Test.
- [ ] T015b [US1] **Apply Bonferroni Correction**: Read `data/processed/global_regression.json` (T013e-Write). **Logic**: Validate that `p_value` exists, is numeric, and is < 1.0. If valid, apply Bonferroni correction for the **full family** of disorder widths (using `len(config.W_LIST)`), as required by Spec SC-005 (overriding Plan's 'pairwise' definition). Log the override. **Output**: Write `data/processed/bonferroni_results.json` with keys: `slope`, `p_value`, `bonferroni_p_value`, `is_significant`. **Depends on**: T013e-Write.
- [X] T014 [US1] Implement `code/stats.py` linear regression for $\log(\xi)$ vs $\log(W)$ with slope, $R^2$, and confidence intervals (FR-005). **MUST** restrict the regression for slope -2 validation (SC-001) to the subset where $W < \text{config.WEAK_DISORDER_CUTOFF}$. **Depends on**: T004.
- [X] T016 [US1] Add fallback mechanism in `code/analyze_pr.py` to use `scipy.sparse.linalg.eigsh` if `scipy.linalg.eigh` exceeds 6GB RAM for $L=1600$ (FR-008)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Verify with Transfer Matrix Method (Priority: P2)

**Goal**: Implement Transfer Matrix Method with QR orthogonalization to independently validate PR results.

**Independent Test**: Run TM on same realizations as PR, compute Lyapunov exponents, and verify $\xi_{TM} \approx \xi_{PR}$ within 10% for $L \ge 400$.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for TM output schema in `tests/contract/test_tm_schema.py`. **Asserts output matches `localization_length_schema.json`**.
- [X] T019 [P] [US2] Integration test for TM convergence and method agreement in `tests/integration/test_tm_validation.py`. **Asserts convergence trace exists and relative change criteria are met**.

### Implementation for User Story 2

- [ ] T020b-Impl [US2] **Implement TM Algorithm with QR and Scaling**: Implement `code/analyze_tm.py` with QR-based orthogonalization at every step. **MUST** use **logarithmic accumulation** (sum of log singular values) to prevent numerical underflow (FR-009, Constitution Principle VI). **Input**: Read Hamiltonians from `data/raw/hamiltonians.h5`. **Algorithm**: Iterate L over a range of increasing magnitudes. **Fitting**: Perform a linear fit of $\gamma(L)$ vs $1/L$ to extract $\gamma_{\infty}$ and $\xi = 1/\gamma_{\infty}$. **Output**: Append convergence trace to `data/metadata/tm_convergence.json`. Save results to `data/processed/lyapunov_exponents.json` with schema: `disorder_width`, `localization_length`, `uncertainty`. **Depends on**: T005, T007, T017b.
- [X] T022 [US2] Add convergence monitoring logic to track relative change in $\gamma$ between consecutive size doublings ($L=100 \to 800$). **Append convergence trace to `data/metadata/tm_convergence.json`.** (FR-009)

**Checkpoint**: US2 core logic complete. Validation against US1 requires Phase 4.5.

---

## Phase 4.5: Cross-Story Validation (Blocking)

**Purpose**: Validate US2 results against US1 results. Requires both US1 and US2 to be complete.

- [ ] T023 [US1+US2] Implement `code/compare_methods.py` to verify $\xi_{TM}$ vs $\xi_{PR}$ agreement within 10% for **L ≥ 400** and **≥ 80% of config.NUM_REALIZATIONS realizations** (calculated as `int(0.8 * config.NUM_REALIZATIONS)`). **MUST verify that `config.NUM_REALIZATIONS` is defined in `code/config.py` before execution.** **Input**: `data/processed/scaling_fits.json` (T013d-Aggregate), `data/processed/lyapunov_exponents.json` (T020b-Impl). **Logic**: Compare raw localization lengths against the 10% threshold defined in SC-002. **Note**: This task validates SC-002 (relative error) and does NOT use Bonferroni-corrected p-values from T015b for validation logic. Generate `data/processed/method_agreement_report.json` (US-2 Acceptance Scenario 3). (SC-002, US-2). **Depends on**: T013d-Aggregate, T020b-Impl. **Fallback**: If the number of realizations is < 80%, log a warning and mark the report as 'insufficient_data'.

**Checkpoint**: US1 and US2 validated against each other.

---

## Phase 5: User Story 3 - Visualize Eigenstate Localization Patterns (Priority: P3)

**Goal**: Visualize individual eigenstate probability densities to provide a physical picture of localization (addressing Feynman's review).

**Independent Test**: Generate a single eigenstate visualization ($L=200, W=2.0, E \approx 0$), confirm exponential decay, and verify decay length matches computed $\xi$.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for visualization output format in `tests/contract/test_viz_schema.py`. **Asserts output JSON contains `decay_length`, `R_squared`, `site_index`.**
- [X] T025 [P] [US3] Integration test for decay length consistency in `tests/integration/test_viz_validation.py`. **Asserts decay length matches computed ξ within 20%**.

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement `code/visualize.py` to plot $|\psi_i|^2$ vs site index for eigenstates near $E=0$ (FR-006). **Save plot to `data/processed/visualizations/eigenstate_W2.0_L200.png`.**
- [X] T027 [US3] Implement log-linear fit logic in `code/visualize.py` to calculate decay length and $R^2$ from probability density (US-3 Acceptance Scenario 1). **Append fit parameters to `data/processed/fit_results.json`.**
- [X] T028 [US3] Add comparison visualization logic to overlay $W=0.5$ and $W=2.0$ states and verify FWHM reduction (US-3 Acceptance Scenario 3). **Save to `data/processed/visualizations/comparison_W_W2.0.png`.**
- [ ] T029-Identify [US3] **Identify Half-Amplitude Site**: Read eigenstate data from T026. **Logic**: Perform linear interpolation on `log(|ψ_i|^2)` vs site index to find the site index `i` where the value is closest to `0.5 * max(|ψ|^2)`, where 'max' is the **global maximum** of the probability density across all sites. **Fallback**: If amplitude never drops to 0.5 * global_max, report `decay_length = None`. **Depends on**: T026.
- [ ] T029-Fit [US3] **Perform Log-Linear Fit**: Read interpolated data from T029-Identify. **Logic**: Calculate decay length and R². **Depends on**: T029-Identify.
- [ ] T029-Write [US3] **Generate Quantitative Physical Summary**: Write a quantitative summary to `docs/physical_interpretation.md` under header "Worked Example: W=2.0". **Output Format**: Markdown table or list with columns: `Site Index`, `Decay Length (lattice units)`, `R²`, `Is Delocalized`. **Constraint**: No qualitative analogies. **Depends on**: T029-Fit.
- [X] T035 [US3] **Implement "Feynman Review" Response: Strong Disorder Limit**: Extend `code/visualize.py` to generate a specific analysis for a representative strong disorder case (e.g., W=5.0). **Task**: For a single realization at W=5.0, identify the localization center (site with maximum probability density), calculate the distance to the nearest site where `|ψ|^2 < 0.5 * max(|ψ|^2)` (global max), and explicitly verify that the wavefunction exhibits exponential decay behavior consistent with Anderson localization theory. **Output**: Append a section "Strong Disorder Limit: W=5.0" to `docs/physical_interpretation.md` containing: (1) The specific site index of the localization center, (2) The calculated distance (in lattice units), (3) A statement confirming whether the interference pattern matches exponential decay behavior. **Output Format**: Markdown table or list with columns: `Localization Center (Site)`, `Distance to 0.5*Max (lattice units)`, `Exponential Decay Confirmed`. **Constraint**: Must be derived from real computed eigenstates, not theoretical extrapolation. (Reviewer: richard-feynman-simulated, US-3). **Depends on**: T026.
- [ ] T037 [P] **Implement "Feynman Review" Response: Zero Disorder Limit**: Extend `code/visualize.py` to generate a specific analysis for the clean limit ($W=0$). **Task**: For a single realization at $W=0$, identify the site index of maximum probability, calculate the "spread" (e.g., standard deviation of $|\psi|^2$ or distance to half-max), and explicitly verify the delocalized, sinusoidal nature of the wavefunction. **Output**: Append a section "Clean Limit: W=0" to `docs/physical_interpretation.md` containing: (1) The site index of maximum amplitude, (2) The calculated "spread" (in lattice units), (3) A statement confirming the wavefunction is delocalized (non-exponential). **Output Format**: Markdown table or list with columns: `Max Amplitude Site`, `Spread (lattice units)`, `Delocalized Status`. **Constraint**: Must be derived from real computed eigenstates. (Reviewer: richard-feynman-simulated, US-3). **Depends on**: T026.
- [ ] T038-Iterate [US3] **Iterate Over Widths**: Loop over representative widths (W=0, 0.5, 1.0, 2.0, 5.0), compute metrics (distance/spread, localization center) for each. **Depends on**: T026, T035, T037.
- [ ] T038-Table [US3] **Format Evolution Sketch**: Generate a summary table showing the transition from W=0 to W=5.0. **Output**: Append a section "Evolution of Localization: W=0 to W=5.0" to `docs/physical_interpretation.md` containing a table with columns: `Disorder Width (W)`, `Localization Center (Site)`, `Distance / Spread`, `Behavior Type (Delocalized/Localized)`. **Depends on**: T038-Iterate.
- [ ] T036-Synthesize [US3] **Synthesize Physical Narrative**: Read "Worked Example: W=2.0", "Strong Disorder Limit: W=5.0", and "Clean Limit: W=0" sections from `docs/physical_interpretation.md`. **Logic**: Synthesize metrics into a concise, non-mathematical explanation. **Template**: "At W={W}, the electron is trapped at site {site} with a distance of {dist} lattice units. The decay length is {decay}." **Fallback**: If metrics are None/NaN, use "delocalized" or "N/A". **Output**: Append the synthesized narrative to `docs/physical_interpretation.md`. **Depends on**: T029-Write, T035, T037.

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
- **Cross-Story Validation (Phase 4.5)**: Depends on completion of Phase 3 (US1) and Phase 4 (US2). **Specifically depends on T013d-Aggregate and T020b-Impl.**
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
# Note: T013b (Generate Multi-L Dataset) depends on T012.
# T013a-Fit depends on T013b.
# T013d-Aggregate depends on T013a-Fit and T013c.
# T013e-Reg depends on T013d-Aggregate.
# T015b depends on T013e-Write.
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
6. Run Phase N: Polish → Generate physical narrative (T036-Synthesize, T037, T038)
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
- **Crucial**: T015b applies Bonferroni correction for FWER across ALL widths (full family), aligning with SC-005, and enforces the Spec over the Plan if they contradict. **Self-correction logic added to handle plan.md updates in-place.**
- **Crucial**: T017 is now split into T017a (Class) and T017b (Integration) to resolve circular dependencies and ensure streaming.
- **Crucial**: T023 validates SC-002 (relative error) and does NOT use Bonferroni p-values.
- **Crucial**: T035 specifically addresses the "Feynman" review's request for a "worked example" in the strong disorder limit ($W \gg 1$) to demonstrate the physical picture of "trapping" and "suppression of diffusion" without relying solely on abstract fitting. It requires identifying specific lattice sites and distances, directly answering "when does it stop wandering?".
- **Crucial**: T015b dynamically calculates Bonferroni factor based on `len(processed_widths)`.
- **Crucial**: T029 and T035 define specific algorithms for "half-amplitude site" and "localization center" to ensure deterministic implementation.
- **Crucial**: T036 synthesizes the quantitative findings from T029/T035 into a direct answer to the reviewer's request for a "physical picture" without equations, strictly grounded in the computed site indices and distances using a specific text template with fallback for delocalized states.
- **Crucial**: T014 explicitly restricts the slope -2 validation to the weak disorder subset ($W < 1.0$).
- **Crucial**: T015a ensures the plan.md is updated to reflect the full family correction before T015b runs (though T015b now has self-correction).
- **Crucial**: T012 now correctly depends on T017b for logging integration.
- **Crucial**: T013a updated to include specific plot requirements and verification criteria.
- **Crucial**: T020b updated to specify output artifact schema and finite-size scaling fit requirement.
- **Crucial**: T029 updated to specify output format for quantitative summary.
- **Crucial**: T036 updated to be robust to edge cases (W=0).
- **Crucial**: T037 addresses the Feynman review's request for the clean limit (W=0) to contrast with the localized cases, explicitly verifying delocalization.
- **Crucial**: T038 addresses the Feynman review's request for a "sketch" of the evolution by providing a quantitative summary of the transition from W=0 to W=5.0, directly answering "what happens as you turn the disorder knob".
- **Crucial**: T013c and T013d handle the W=0 edge case explicitly, preventing T013a from failing.
- **Crucial**: T013e performs the global regression, decoupling it from per-width fits.
- **Crucial**: T015a and T015b split the statistical testing and correction logic.
- **Crucial**: T023 uses dynamic calculation for `min_realizations`.
- **Crucial**: T017a enforces JSON-lines streaming.
- **Crucial**: T013b (new) generates the multi-L dataset required for FR-003.
- **Crucial**: T013a updated to explicitly read `data/processed/pr_raw_multiL.json` from T013b and write `data/processed/pr_scaling_raw.json`.
- **Crucial**: T020b-Core enforces logarithmic accumulation to prevent underflow.
- **Crucial**: T013e-Reg explicitly excludes W=0 from log-log regression.
- **Crucial**: T015b applies Bonferroni to the full family of widths regardless of plan state.
- **Crucial**: T013a is the single source of truth for `data/processed/pr_scaling_raw.json`, eliminating the redundant T013a-Write task.
- **Crucial**: T037 and T038 ensure the "Feynman" review's request for a "sketch" of the evolution is met with quantitative data points, not just qualitative description.
- **Crucial**: T013c and T013d-Aggregate handle the W=0 edge case explicitly, preventing T013a from failing.
- **Crucial**: T013e performs the global regression, decoupling it from per-width fits.
- **Crucial**: T015b applies Bonferroni to the full family of widths regardless of plan state.
- **Crucial**: T013a is the single source of truth for `data/processed/pr_scaling_raw.json`, eliminating the redundant T013a-Write task.
- **Crucial**: T037 and T038 ensure the "Feynman" review's request for a "sketch" of the evolution is met with quantitative data points, not just qualitative description.
- **Crucial**: T020b-Impl consolidates the TM algorithm, fitting, and output writing into a single, executable task.
- **Crucial**: T011-Impl ensures the integration test is executable by depending on T013d-Aggregate.
- **Crucial**: T036-Synthesize ensures the physical narrative is generated only after all required sections exist.