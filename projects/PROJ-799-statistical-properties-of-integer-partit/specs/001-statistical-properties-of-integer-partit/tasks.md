# Tasks: Statistical Properties of Integer Partitions Into Distinct Prime Summands

**Input**: Design documents from `/specs/001-statistical-properties-of-integer-partitions-into-distinct-prime-summands/`
**Prerequisites**: plan.md, spec.md, research.md
**Tests**: Included as contract tests for mathematical correctness and pipeline integration.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root (adjusted to plan structure: `projects/PROJ-799.../code/`, `tests/`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create directory structure: `projects/PROJ-799-statistical-properties-of-integer-partit/` with subdirs `code/`, `code/utils/`, `data/raw/`, `data/processed/`, `data/schemas/`, `tests/`, `tests/data/`, `docs/`. **Also create `state/projects/` at the repository root (not inside the project folder).**
- [X] T001b [P] Create placeholder files: `README.md`, `.gitignore`, `requirements.txt` (empty initially), `state/projects/PROJ-799.yaml` (empty initially). **Requires T001a completion.**
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (numpy, scipy, scikit-learn, statsmodels, matplotlib, pandas, pygam)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools scoped specifically to `projects/PROJ-799-statistical-properties-of-integer-partit/code/` by creating a `.flake8` file in the repository root with `exclude` or `per-file-ignores` patterns targeting the subdirectory, and a `pyproject.toml` for black configuration.
- [ ] T003b [P] Re-plan Setup: Verify T001a and T003 artifacts exist and are valid before proceeding to Phase 2.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/prime_sieve.py`: Generate primes up to **[deferred]** (to cover nearest neighbors for n=50,000) using Sieve of Eratosthenes. Implementation MUST use a boolean array or bitset for memory efficiency (O(N) space, N=50,100). Output: List of primes.
- [X] T005b [P] Reference-Validator Step: Verify the asymptotic formula for distinct prime partitions against Roth & Szekeres (1954). **Explicitly derive and write the leading-order formula to `docs/verified_formula.md`.** The formula is: $Q_{as}(n) \sim \exp\left( C \sqrt{\frac{n}{\ln n}} \right)$ where $C$ is a constant determined by the underlying theoretical framework. (or the specific constant derived from the distinct prime generating function $\prod (1+q^p)$). Document the derivation steps and the exact constant used. This artifact is required for T005.
- [ ] T005 [P] Implement `code/utils/asymptotic_baseline.py`: Implement $Q_{as}(n)$ based strictly on the **distinct-partition variant** of Meinardus' theorem. **CRITICAL**: Read the verified formula and constants from `docs/verified_formula.md` (output of T005b). Do NOT hardcode the formula in the task description or code. Explicitly document the leading-order formula used in comments. **Requires T005b completion.**
- [ ] T006 [P] Create `data/schemas/partition_record.schema.yaml` and `data/schemas/regression_output.schema.yaml`
- [ ] T007 [P] Setup `state/projects/PROJ-799.yaml` structure for checksums and versioning (keys: `artifact_hashes`, `updated_at`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Exact Partition Values and Asymptotic Baseline (Priority: P1) 🎯 MVP

**Goal**: Compute exact $p_{\mathcal{P}}(n)$ for $n \in [1, 50000]$ and generate $Q_{as}(n)$ baseline, ensuring memory < 6.5 GB.

**Independent Test**: Verify output CSV has correct columns, non-negative integers for counts, and matches reference values for small sample sizes.

### Tests for User Story 1

- [ ] T008 [P] [US1] Generate Reference Data: Create `tests/data/reference_values.csv` containing exact $p_{\mathcal{P}}(n)$ for **n in a representative range**. **Implementation**: Use the Sieve of Eratosthenes from T004 and a simplified DP logic (or a temporary script) to compute exact counts for this small range. This file serves as the ground truth for T009 and the validation logic in T011 (via test suite). **Requires T004 completion.**
- [ ] T009 [P] [US1] Contract test: Verify $p_{\mathcal{P}}(n)$ matches `tests/data/reference_values.csv` for $n \in [1, 100]$ in `tests/test_partition_logic.py`. **This test loads the reference file and compares it against the output of `generate_partitions.py` for the small range.**
- [ ] T010a [P] [US1] Integration test: Verify `generate_partitions.py` completes within 2 hours and memory < 6.5 GB in `tests/test_pipeline.py`
- [ ] T010b [P] [US1] Time-budget test: Verify that the DP generation phase completes within a reasonable time frame, leaving 4 hours for modeling/plotting to meet SC-004 (6h total).

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/generate_partitions.py`:
 - Use 1D `int64` array for DP to count partitions into distinct primes.
 - Iterate primes only (skip composites) to enforce distinct prime constraint.
 - Handle edge cases ($n < 5$ where $p_{\mathcal{P}}(n)=0$) by setting count to 0.
 - Calculate $Q_{as}(n)$ using the verified Roth & Szekeres formula. **CRITICAL**: Read the formula from `docs/verified_formula.md` (output of T005b). **Do NOT hardcode the formula in the code or task description.**
 - Clamp $Q_{as}(n)$ to a negligible minimum threshold to prevent log(0).
 - **Generate `data/raw/partitions_raw.csv` with columns: n, p_P_n, Q_as_n.**
 - **Requires T008 and T005b completion.**
- [ ] T012 [US1] Implement `code/generate_partitions.py` data export:
 - Generate SHA-256 checksum of `data/raw/partitions_raw.csv` and update `state/projects/PROJ-799.yaml` at key `artifact_hashes.generate_partitions_raw` (format: hex string).
 - Update `state/projects/PROJ-799.yaml` key `updated_at` with current ISO timestamp.
- [ ] T013 [US1] Add validation logic to `generate_partitions.py` to skip $n$ where $p_{\mathcal{P}}(n)=0$ or $Q_{as}(n) \le 0$ for log-residual calculation.
- [ ] T031 [US1] **Research-Stage Revision**: Explicitly document the generating function $\prod_{p \in \mathbb{P}} (1+q^p)$ in the code comments of `generate_partitions.py` to distinguish it from the unrestricted partition generating function $\prod (1-q^k)^{-1}$, addressing the concern that prime gaps create 'holes' in the summands.
- [ ] T032 [US1] **Research-Stage Revision**: Add a configuration parameter `n_max` to `generate_partitions.py` and `asymptotic_baseline.py` with a default set to a sufficiently large magnitude to ensure robust partition coverage., and explicitly log the chosen `n_max` at runtime. This addresses the requirement to state whether the analysis targets small $n$, large $n$, or a transition region, ensuring the asymptotic regime is defined.

**Checkpoint**: US1 functional. Data generation complete.

---

## Phase 4: User Story 2 - Calculate and Model Residual Error with Density Features (Priority: P2)

**Goal**: Calculate $R(n)$ and fit a model using prime density features to detect systematic bias.

**Independent Test**: Verify regression outputs coefficients, p-values, and $R^2 > 0.05$.

### Tests for User Story 2

- [ ] T014 [P] [US2] Contract test: Verify $R(n)$ calculation handles log(0) gracefully and matches expected values for sample $n$ in `tests/test_feature_engineering.py`
- [ ] T015 [P] [US2] Integration test: Verify regression model outputs valid p-values and $R^$ score in `tests/test_regression_model.py`
- [ ] T016c [P] [US2] Prepare Multiple-Test Dataset: Generate a synthetic dataset with multiple density predictors (e.g., varying $\pi(n)$, $1/\ln(n)$, distance to nearest prime, oscillatory terms) specifically designed to trigger the Benjamini-Hochberg correction logic. This dataset is required for T021 to verify the correction mechanism under multiple hypothesis testing conditions. **Requires T004 completion.**
- [ ] T021 [P] [US2] Test: Verify Benjamini-Hochberg correction is applied correctly and p-values are adjusted in `tests/test_regression_model.py`. **Must run after T016c (Dataset) and T017c (Implementation of correction logic).**

### Implementation for User Story 2

- [ ] T016a [US2] Implement `code/feature_engineering.py`:
 - Load `data/raw/partitions_raw.csv`.
 - Compute $R(n) = \log(p_{\mathcal{P}}(n)) - \log(Q_{as}(n))$ for valid $n$.
 - Generate features: $\pi(n)$ (via precomputed sieve from T004, which now covers up to 50,100), $1/\ln(n)$.
 - Calculate 'distance to nearest prime' as the **absolute difference to the closest prime**. **Algorithm**: Use binary search (`bisect` module) on the precomputed prime list from T004 (which includes primes > 50,000) to find the nearest prime efficiently for all $n \le [deferred]$.
 - Add oscillatory features: $\sin(\log n)$, $\cos(\log n)$ to capture periodic anomalies.
 - Save `data/processed/features.csv`.
 - **Requires T012 completion.**
- [ ] T016b [P] [US2] Validate `data/processed/features.csv`: Verify 'distance to nearest prime' and oscillatory terms are present and non-null before regression.
- [ ] T017a [US2] Implement `code/regression_model.py` (Full Model):
 - Fit Generalized Additive Model (GAM) or Linear Regression with splines for density terms.
 - **Explicitly include oscillatory terms: `sin(log(n))`, `cos(log(n))` in the model formula as required by FR-005.** Add terms: beta1*sin(log(n)) + beta2*cos(log(n)) to the linear predictor.
 - Output coefficients, p-values, $R^2$ to `data/processed/model_results.json`.
- [ ] T017b [US2] Implement `code/regression_model.py` (Null Model):
 - Fit an intercept-only (null) model.
 - Compare null model performance against the full model to verify systematic bias (FR-008).
 - Include null model stats in `data/processed/model_results.json`.
- [ ] T017c [US2] Implement `code/regression_model.py` P-value Correction:
 - Apply **Benjamini-Hochberg correction (alpha=0.05)** to p-values (FR-005, SC-005).
 - Write corrected p-values to `data/processed/model_results.json`.
- [ ] T033 [US2] **Research-Stage Revision**: In `feature_engineering.py`, explicitly calculate and log the density of available primes $\pi(n)/n$ vs the density of all integers $$ for the range $n \in [1, 50000]$. Include this comparison in the analysis report to quantify the 'hole' effect mentioned in the review.
- [ ] T034 [US2] **Research-Stage Revision**: In `regression_model.py`, add a specific test or diagnostic to check if the residuals show a systematic trend correlated with prime gaps (e.g., plot residuals against the gap size to the next prime). This directly addresses the concern about prime gaps altering the asymptotic regime.

**Checkpoint**: US2 functional. Statistical model trained and validated.

---

## Phase 5: User Story 3 - Validate Model Robustness and Visualize Convergence (Priority: P3)

**Goal**: Perform cross-validation and generate visualizations to confirm generalizability.

**Independent Test**: Verify CV MSE is reported and plot is generated.

### Tests for User Story 3

- [ ] T022 [P] [US3] Contract test: Verify that k-fold cross-validation returns k MSE values and a mean, as described in standard validation frameworks (Bishop; Arlot & Celisse). in `tests/test_visualize_results.py`
- [ ] T023a [P] [US3] Integration test: Verify plot generation produces a valid PNG/PDF file in `tests/test_visualize_results.py`
- [ ] T023b [P] [US3] Time-budget test: Verify total pipeline (DP + Model + Plot) completes within 6 hours (SC-004).

### Implementation for User Story 3

- [ ] T024 [US3] Implement `code/regression_model.py` (CV logic):
 - Use scikit-learn's `cross_val_score` with k-fold cross-validation to compute MSE for each fold on the fitted model.
 - Record MSE for each fold and mean MSE.
 - (Depends on T022 passing).
 - **Requires T022 passing and T017c completion.**
- [ ] T025 [US3] Implement `code/visualize_results.py`:
 - Plot $n$ (x-axis) vs $R(n)$ (raw residuals) and fitted correction term.
 - Highlight regions of high prime density vs. gaps.
 - Save plot to `data/processed/residual_convergence.png`.
- [ ] T026 [US3] Implement `code/visualize_results.py`:
 - Generate residual vs. fitted plot to check for homoscedasticity.
- [ ] T035 [US3] **Research-Stage Revision**: In `visualize_results.py`, generate a specific plot comparing the residual trend $R(n)$ against the local prime gap size. This visualization will explicitly test the hypothesis that prime gaps (the 'holes') drive the deviation from the unrestricted partition asymptotic, addressing the core concern of the research-stage review.

**Checkpoint**: US3 functional. All visualizations and CV metrics ready.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027a [P] Documentation: Update `README.md` with project overview and run instructions.
- [ ] T027b [P] Documentation: Update `docs/methodology.md` with detailed justification for the Roth & Szekeres distinct-partition generating function and the $n_{max}=50000$ limit.
- [ ] T028 [P] Documentation: Create `docs/scope_justification.md` explaining the choice of $n_{max}=50000$ and the mechanism to update the spec if the limit changes (addressing FR-001/002 scope mismatch).
- [ ] T029a [P] Code cleanup: Remove unused imports from all Python files using `autoflake`.
- [ ] T029b [P] Code cleanup: Optimize DP loops using `numpy` vectorization where applicable.
- [ ] T030 [P] Run `quickstart.md` validation to ensure full pipeline executes end-to-end within 6 hours.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1) must complete before US2 (P2) and US3 (P3) due to data dependencies.**
 - **US2 strictly requires `data/raw/partitions_raw.csv` produced by US1.**
 - **US3 strictly requires `data/processed/model_results.json` produced by US2.**
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 output (`partitions_raw.csv`) and T008 (reference data)
- **User Story 3 (P3)**: Depends on US2 output (`model_results.json`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- Different user stories **CANNOT** be worked on in parallel by different team members if they share data artifacts (e.g., US2 cannot start until US1 produces `partitions_raw.csv`).

---

## Sequential Data-Flow Strategy (Replaces Parallel Team Strategy)

Due to strict data dependencies (US1 -> US2 -> US3), the project follows a sequential data-flow strategy:

1. **Team completes Setup + Foundational together**.
2. **Once Foundational is done**:
 - **Developer A: User Story 1 (Data Generation)**.
 - **Wait for US1 completion** (Data artifact `partitions_raw.csv` must exist).
 - **Developer B: User Story 2 (Feature Engineering & Modeling)**. (Cannot start until US1 data exists).
 - **Wait for US2 completion** (Data artifact `model_results.json` must exist).
 - **Developer C: User Story 3 (Visualization)**. (Cannot start until US2 data exists).
3. Stories complete and integrate sequentially based on data flow.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify $p_{\mathcal{P}}(n)$ against known values).
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: Ensure `generate_partitions.py` uses 1D array and iterates only primes to respect the "distinct prime" constraint and memory limits.
- **Critical Constraint**: The asymptotic baseline $Q_{as}(n)$ MUST use the verified formula from `docs/verified_formula.md` (Roth & Szekeres) as per the spec, not a hardcoded formula.
- **Critical Constraint**: The entire pipeline must complete within 6 hours (SC-004). Monitor time budgets in T010b and T023b.
- **Critical Constraint**: P-value correction (Benjamini-Hochberg, alpha=0.05) is mandatory (SC-005).
- **Critical Constraint**: US2 and US3 must be executed sequentially after US1 due to strict data dependencies.
- **Revision Constraint**: Tasks referencing non-existent reviews (T013b, T013c, T017d, T026b) have been removed to ensure all work is grounded in verified spec requirements.
- **Revision Constraint**: New tasks T031-T035 have been added to explicitly address the research-stage review concerning the distinction between unrestricted and distinct-prime generating functions and the impact of prime gaps on the asymptotic regime.
- **Revision Constraint**: All stale claim markers have been removed and replaced with explicit implementation details or file references.
- **Revision Constraint**: T008 now generates reference data for $n \in [1, 100]$ only, matching the bounded range test requirement in T011 and SC-003, resolving the circular dependency with T011.
- **Revision Constraint**: T004 now generates primes up to 50,100 to ensure the "nearest prime" calculation for n=50,000 is valid.
- **Revision Constraint**: T011 no longer loads test artifacts at runtime; validation is handled by T009.