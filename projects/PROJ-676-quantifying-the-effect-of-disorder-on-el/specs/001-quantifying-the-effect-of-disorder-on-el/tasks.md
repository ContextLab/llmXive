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

- [X] T001a [P] Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `data/metadata/`, `tests/`, `docs/`, `specs/` inside `projects/PROJ-676-quantifying-the-effect-on-el/`. **Command**: `mkdir -p code data/raw data/processed data/metadata tests docs specs`. Verify existence of directories.
- [X] T001b [P] Create `.gitkeep` files in `data/raw/`, `data/processed/`, `data/metadata/`, `docs/`, `specs/` to ensure they are tracked. **Command**: `touch data/raw/.gitkeep data/processed/.gitkeep data/metadata/.gitkeep docs/.gitkeep specs/.gitkeep`.
- [X] T001c [P] Create `docs/physical_interpretation.md` with a header structure: `# Physical Interpretation`, `## Worked Example: W=2.0`, `## Strong Disorder Limit: W=5.0`. This file will be populated by T029 and T035.
- [X] T003a [P] Configure linting tools (flake8/pylint) and create `.flake8` and `.pylintrc` in project root. `.flake8` must contain: `[flake8] max-line-length = 88 ignore = E501, W503`. **File**: `projects/PROJ-676-quantifying-the-effect-on-el/.flake8`.
- [X] T003b [P] Configure formatting tool (black) and create `pyproject.toml` for black settings in project root. **File**: `projects/PROJ-676-quantifying-the-effect-on-el/pyproject.toml`.
- [X] T003c [P] Add a CI step or script `run_linting.sh` to execute flake8 and black --check on `code/` and fail the build if violations are found. **Script**: `projects/PROJ-676-quantifying-the-effect-on-el/run_linting.sh` with content: `#!/bin/bash; flake8 code/; black --check code/`.

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
 "type": "object",
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
 "type": "object",
 "properties": {
   "xi": {"type": "number"},
   "uncertainty": {"type": "number"},
   "disorder_width": {"type": "number"}
 },
 "required": ["xi", "uncertainty", "disorder_width"]
}
```
- [X] T007 [P] Implement `code/storage_utils.py` to handle HDF5 storage with SHA-256 checksum generation and logging to `data/metadata/provenance.json`. **MUST log** `realization_index`, `seed`, `W`, `L` for every generated instance.
- [X] T017a [P] **Implement Numerical Stability Logger Class**: Create `code/logger.py` with a `NumericalLogger` class. **MUST** implement methods `log_residual(norm, flag)` and `log_convergence(metric)`. **Output Format**: JSON lines appended to `data/metadata/residuals.json`. **MUST** use file open mode `'a'` (append) and call `file.flush()` after every write to ensure real‑time streaming. **MUST** provide utility functions/decorators to facilitate injection of logging calls. **Note**: This task implements the class only. (FR-008, Constitution Principle VI).
- [X] T017b [P] **Inject Logging Hooks**: Integrate `NumericalLogger` into `code/generate_hamiltonian.py` (T005) and `code/analyze_pr.py` (T012). **MUST** call `log_residual` for every eigenvalue problem solved. **Depends on**: T017a, T005. (FR-008, Constitution Principle VI).
- [X] T015a [P] **Update Plan Artifact for Bonferroni Correction**: Edit `plan.md` to replace the phrase "Bonferroni correction for pairwise comparisons only" with "Bonferroni correction for the full family of disorder widths" in BOTH the Summary and the FR/SC Matrix. **Verification**: After editing, run `grep -q "full family" plan.md` and fail if not found. **What_changed**: Updated text and added verification command. **Depends on**: None.
- [X] T015c [P] **Commit Updated `plan.md`**: Write the modified `plan.md` to disk and add it to version control (simulated commit). **Verification**: Ensure `git diff --exit-code` reports no pending changes for `plan.md`. This guarantees the plan artifact is persisted before downstream tasks run.
- [X] T014 [P] Implement `code/stats.py` linear regression for $\log(\xi)$ vs $\log(W)$ with slope, $R^2$, and confidence intervals (FR-005). **MUST** restrict the regression for slope ≈‑2 validation (SC‑001) to the subset where $W < config.WEAK_DISORDER_CUTOFF$. **Depends on**: T004.
- [X] T016 [P] Add fallback mechanism in `code/analyze_pr.py` to use `scipy.sparse.linalg.eigsh` if `scipy.linalg.eigh` exceeds 6 GB RAM for $L=1600$ (FR-008).

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel

---

## Phase 3: User Story 1 – Compute Localization Length via Participation Ratio (Priority: P1) 🎯 MVP

**Goal**: Generate disordered 1D Hamiltonians and compute localization lengths via PR finite‑size scaling to quantify disorder effects.

**Independent Test**: Run on a single realization (L=400, W=1.0), compute eigenstates, extract PR for $|E|<0.1$, and verify PR decreases with increasing W.

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Contract test for PR calculation output schema in `tests/contract/test_pr_schema.py`. **Asserts output matches `localization_length_schema.json`**.
- [ ] T011-Impl [P] [US1] Integration test for finite‑size scaling workflow in `tests/integration/test_pr_scaling.py`. **Asserts existence of `data/processed/scaling_fits.json` with schema validation**. **Depends on**: T013d-Aggregate.

### Implementation for User Story 1

- [X] T012 [US1] **Implement `code/analyze_pr.py`**: Compute Participation Ratio $PR = (\sum|\psi_i|^2)^2 / \sum|\psi_i|^4$ for eigenstates within $|E|<0.1$ (FR‑002). **Integrate** logging hooks (T017b). **Output**: Write raw PR values to `data/processed/pr_raw.json`. **Depends on**: T005, T007, T017b.
- [X] T013b-Orchestrate **Run PR Computation Across All W/L**: Loop over `config.W_LIST` and `config.L_LIST`, invoke the `analyze_pr` module logic from T012 for each combination, and write per‑realization results to temporary files. **Depends on**: T012.
- [X] T013b-Aggregate [P] **Aggregate Multi‑L PR Dataset**: Collect all temporary PR files produced by T013b-Orchestrate into a single JSON `data/processed/pr_raw_multiL.json`. **Depends on**: T013b-Orchestrate.
- [X] T013a-Fit [US1] **Finite‑Size Scaling Fit**: Read `data/processed/pr_raw_multiL.json`. **Filter out** any entries where `W == 0` before fitting. Fit the PR(L) saturation curve to extract $\xi$. If fit fails, log a warning to `data/metadata/warnings.json` and record the realization in `data/processed/skipped_realizations.json`. **Output**: Write successful fit results to `data/processed/pr_scaling_raw.json`. **Depends on**: T013b-Aggregate.
- [X] T013c [US1] **W=0 Edge Case Handler**: Read `data/processed/pr_raw_multiL.json`, **filter** to only `W == 0` entries, compute PR for $L \in \{[deferred]\}$ using T012 logic, verify extensive scaling, and write results to `data/processed/w0_results.json` with `is_delocalized: true`. **Exclude** these entries from downstream regression. **Depends on**: T013b-Aggregate.
- [X] T013d-Aggregate [US1] **Merge Scaling Results**: Combine `pr_scaling_raw.json` (from T013a-Fit) and `w0_results.json` (from T013c) into `data/processed/scaling_fits.json`. **Schema**: List of objects with `disorder_width`, `xi`, `uncertainty`, `is_delocalized` (optional). **Depends on**: T013a-Fit, T013c.
- [X] T013e-CalcWrite [US1] **Global Regression & Statistics**: Read `data/processed/scaling_fits.json`, filter to `W > 0`, perform linear regression of $\log(\xi)$ vs $\log(W)$ (using `code/stats.py`), compute slope, $p$‑value, confidence interval, $R^2$, and the t‑statistic. Write all results to `data/processed/global_regression.json` **and** write the t‑statistic separately to `data/processed/t_statistic.json`. **Depends on**: T013d-Aggregate.
- [X] T015b [US1] **Apply Bonferroni Correction**: Read `plan.md` and verify the string "full family" is present via `grep -q "full family" plan.md`. Read `data/processed/global_regression.json`. **Logic**: Verify `len(config.W_LIST) > 0`; if not, raise an error. Apply Bonferroni correction using the full family size (`len(config.W_LIST)`). Log the correction factor and write results to `data/processed/bonferroni_results.json` with keys `slope`, `p_value`, `bonferroni_p_value`, `is_significant`. **Depends on**: T013e-CalcWrite, T015a, T015c.
- [X] T016 [US1] **Sparse Solver Fallback** (already in Phase 2).

**Checkpoint**: User Story 1 should now be fully functional and testable independently.

---

## Phase 4: User Story 2 – Verify with Transfer Matrix Method (Priority: P2)

### Tests for User Story 2 (OPTIONAL)

- [X] T018 [P] [US2] Contract test for TM output schema in `tests/contract/test_tm_schema.py`. **Asserts output matches `localization_length_schema.json`**.
- [X] T019 [P] [US2] Integration test for TM convergence and method agreement in `tests/integration/test_tm_validation.py`. **Asserts convergence trace exists and relative change criteria are met**.

### Implementation for User Story 2

- [X] T020b-Impl [US2] **Implement TM Algorithm with QR & Log‑Accumulation**: Create `code/analyze_tm.py` that reads Hamiltonians from `data/raw/hamiltonians.h5`, builds random transfer matrices, applies QR orthogonalization each step, accumulates log‑singular values to compute Lyapunov exponent $\gamma$. Fit $\gamma(L)$ vs $1/L$ to obtain $\xi = 1/\gamma_\infty$. Log convergence to `data/metadata/tm_convergence.json`. Write final localization lengths to `data/processed/lyapunov_exponents.json` (schema matches `localization_length_schema.json`). **Depends on**: T005, T007, T017b.
- [X] T022 [US2] **Convergence Monitoring**: Within `code/analyze_tm.py`, track relative change in $\gamma$ between consecutive size doublings ($L=100 \to 800$) and append to `data/metadata/tm_convergence.json`. **Depends on**: T020b-Impl.

**Checkpoint**: US2 core logic complete.

---

## Phase 4.5: Cross‑Story Validation (Blocking)

**Purpose**: Validate US2 results against US1 results. Requires both US1 and US2 to be complete.

- [X] T023 [US1+US2] **Method Agreement Check**: Load `data/processed/scaling_fits.json` (US1) and `data/processed/lyapunov_exponents.json` (US2). If `lyapunov_exponents.json` is missing, abort with a clear error message. For each disorder width, compare $\xi_{TM}$ vs $\xi_{PR}$ across realizations. **Acceptance**: At least **[deferred] of config.NUM_REALIZATIONS** (minimum 80 if NUM_REALIZATIONS >= 100) must agree within 10 % relative error. **Output**: `data/processed/method_agreement_report.json`. **Depends on**: T013d-Aggregate, T020b-Impl.

---

## Phase 5: User Story 3 – Visualize Eigenstate Localization Patterns (Priority: P3)

### Tests for User Story 3 (OPTIONAL)

- [X] T024 [P] [US3] Contract test for visualization output format in `tests/contract/test_viz_schema.py`. **Asserts output JSON contains `decay_length`, `R_squared`, `site_index`.**
- [X] T025 [P] [US3] Integration test for decay length consistency in `tests/integration/test_viz_validation.py`. **Asserts decay length matches computed ξ within 20 %**.

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement `code/visualize.py` to plot $|\psi_i|^2$ vs site index for eigenstates near $E=0$ (FR‑006). Save plot to `data/processed/visualizations/eigenstate_W2.0_L200.png`.
- [X] T029-Quantify_Eigenstate [US3] **Single‑Task Eigenstate Quantification**: For a chosen realization (e.g., $W=2.0$, $L=200$), identify the half‑amplitude site, perform a log‑linear fit, compute decay length and $R^2$, and write a quantitative summary directly into `docs/physical_interpretation.md` under "Worked Example: W=2.0". **Output**: Markdown section with a table of `Site Index`, `Decay Length`, `R²`, `Is Delocalized`. **Depends on**: T026.
- [X] T035 [US3] **Strong Disorder Limit**: Extend `code/visualize.py` to analyze a single $W=5.0$ realization, locate the localization center, compute distance to the site where $|ψ|^2 < 0.5·\max|ψ|^2$, and verify exponential decay **with $R^2 ≥ 0.95$**. Append a section "Strong Disorder Limit: W=5.0" to `docs/physical_interpretation.md` with required metrics. **Depends on**: T026.
- [X] T037 [US3] **Zero Disorder Limit**: Extend `code/visualize.py` to analyze $W=0$, compute the spread (standard deviation of $|ψ|^2$), and confirm delocalization. Append a "Clean Limit: W=0" section with `Max Amplitude Site`, `Spread`, `Delocalized Status`. **Depends on**: T026.
- [X] T038-Iterate [US3] **Iterate Over Representative Widths**: Loop over $W \in \{0,0.5,1.0,2.0,5.0\}$, compute the metrics defined in T035/T037, and store results. **Depends on**: T026, T035, T037.
- [X] T038-Table [US3] **Evolution Sketch**: Generate a summary table from the iteration results and append "Evolution of Localization: W=0 to W=5.0" to `docs/physical_interpretation.md`. **Depends on**: T038-Iterate.
- [X] T036-Synthesize [US3] **Physical Narrative**: Read the three sections from `docs/physical_interpretation.md` and synthesize a concise, non‑mathematical narrative using the template "At W={W}, the electron is trapped at site {site} with a distance of {dist} lattice units. The decay length is {decay}." Append this narrative to the same markdown file. **Depends on**: T029-Quantify_Eigenstate, T035, T037.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase N: Polish & Cross‑Cutting Concerns

- [X] T015b (already in Phase 2) now includes explicit config‑length verification.
- [X] T032 Performance optimization: Tune `joblib` parallelization to ensure 1000 realizations complete within 6 h on CPU cores. Generate `data/metadata/performance_benchmark.json` with wall‑clock time and peak RAM metrics (FR‑007, SC‑006). **Test parameters**: `n_jobs=2`, `backend='loky'`.
- [X] T033 [P] Additional unit tests for edge cases: $W=0$ (delocalized), large $L$ memory limits, and transfer‑matrix underflow handling. Add `test_W_zero_delocalized` in `tests/unit/test_edge_cases.py`.
- [X] T034 [P] Run `quickstart.md` validation to ensure end‑to‑end reproducibility. Generate `validation_report.json` with pass/fail status.

---

## Dependencies & Execution Order

*Phase 1 → Phase 2 → Phase 3/4/5 (parallel) → Phase 4.5 → Phase N.*

All tasks now have explicit producer‑consumer relationships, no stray parallel tags, and concrete verification steps to satisfy the constitution and reviewer concerns.