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

- [ ] T001 [P] Create the complete directory structure for the project: `projects/PROJ-799-statistical-properties-of-integer-partit/` and all subdirectories including `code/`, `code/utils/`, `data/raw/`, `data/processed/`, `data/schemas/`, `tests/`, `tests/data/`, `docs/`, and `state/projects/`.
- [ ] T003a [P] Create `code/.flake8` configuration file for linting.
- [ ] T003b [P] Create `code/.black` configuration file for formatting.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Note**: Tasks T004 and T005 are independent and can run in parallel. T008 and T009 depend on T004 and must be executed sequentially after T004.

- [ ] T004 [P] Implement `code/utils/prime_sieve.py`: Generate primes up to 50,000 using Sieve of Eratosthenes. [UNRESOLVED-CLAIM: c_e43dc5aa — status=not_enough_info] Use a boolean array for memory optimization. {{claim:c_24aecec7}} (OEIS A000959, https://oeis.org/A000959) **Output**: Save the list of primes to `code/utils/primes.npy` as a **1D `np.int32` array**. **Verification**: Ensure the file exists, dtype is `int32`, and shape matches the count of primes <= 50,000. **Data Hygiene**: Generate SHA-256 checksum of the output file and update `state/projects/PROJ-799.yaml` at key `artifact_hashes.primes_sieve` (format: hex string). Update `state/projects/PROJ-799.yaml` key `updated_at` with current ISO timestamp.
- [X] T005 [P] Implement `code/utils/asymptotic_baseline.py`: Implement $Q_{as}(n)$ based on the distinct-partition variant of Meinardus' theorem. The implementation must use the leading-order term derived from the generating function $\prod (1+q^p)$. Explicitly document the leading-order formula used in the code comments. **Note**: T005 is independent of T004 and can run in parallel.
- [X] T006 [P] Create `data/schemas/partition_record.schema.yaml` and `data/schemas/regression_output.schema.yaml`.
- [X] T007 [P] Setup `state/projects/PROJ-799.yaml` structure for checksums and versioning (keys: `artifact_hashes`, `updated_at`).
- [X] T018 [P] Implement `docs/scope_justification.md`: Explicitly define and document the asymptotic regime (small n vs large n vs transition) for the analysis. Justify the $n_{max}=50,000$ limit as a transition region where prime gaps begin to significantly impact the density of summands, distinguishing it from the unrestricted partition regime. **Addresses Reviewer Concern: "Does the current treatment account for the fact that prime gaps create 'holes'..." and "explicitly state which asymptotic regime is being targeted".** **This task must be completed before T016a and T017a to ensure model design is informed by the defined regime.**
- [X] T021 [P] [US2] Test: Verify Benjamini-Hochberg correction is applied correctly and p-values are adjusted in `tests/test_regression_model.py`. **Implementation**: Test the correction function in isolation using synthetic p-values (independent of full model output). **Note**: Must be written and failing before T017c implementation. **Moved to Phase 2 to ensure it is completed before T017c in Phase 4.**
- [X] T008 [US1] Generate Reference Data: Implement `code/generate_reference.py` to compute exact $p_{\mathcal{P}}(n)$ for **all** $n$ in the range **n in [1, 100]** using the **exact same distinct-prime DP algorithm** as T011, limited to this range. **Algorithm**: Use a 1D array DP iterating over primes <= n (where n<=100). **Output**: Save the output to `tests/data/reference_values.csv` with columns `n`, `p_P(n)`. **Verification**: Ensure the file contains a dataset of non-negative integer counts. **Requires T004 to complete.**
- [X] T009 [US1] Contract test: Implement `tests/test_partition_logic.py` to verify $p_{\mathcal{P}}(n)$ matches `tests/data/reference_values.csv` for **all** $n \in [1, 100]$. **Requires T008 to complete.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Exact Partition Values and Asymptotic Baseline (Priority: P1) 🎯 MVP

**Goal**: Compute exact $p_{\mathcal{P}}(n)$ for $n \in [1, 50000]$ and generate $Q_{as}(n)$ baseline, ensuring memory < 6.5 GB.

**Independent Test**: Verify output CSV has correct columns, non-negative integers for counts, and matches reference values for small sample sizes.

### Tests for User Story 1

- [X] T010a [P] [US1] Integration test: Verify `generate_partitions.py` completes within 2 hours and memory < 6.5 GB in `tests/test_pipeline.py`.
- [X] T010b [P] [US1] Time-budget test: Verify that the DP generation phase completes within 1.5 hours (derived from SC-004 total time budget of several hours minus estimated time for US2 and US3 phases) in `tests/test_pipeline.py`. **Implementation**: Use `pytest-timeout` decorator to enforce the 1.5-hour limit. Reference SC-004 for total budget context. **Requires T011 completion.**
- [X] T010c [P] [US2] Time-budget test: Verify that the feature engineering and modeling phase (US2) completes within 3.5 hours (derived from SC-004 total 6h minus 1.5h DP and 1h for US3) in `tests/test_pipeline.py`.
- [X] T010d [P] [US3] Time-budget test: Verify that the visualization phase (US3) completes within 1 hour (derived from SC-004 total 6h minus 1.5h DP and 3.5h US2) in `tests/test_pipeline.py`.

### Implementation for User Story 1

- [X] T013 [US1] Validate Reference Data: Implement `tests/test_reference_validation.py` to verify `tests/data/reference_values.csv` (produced by T008) contains valid integers and correct column headers. **This task validates the reference file ONLY, not the full generation output.** **Requires T008 and T009 to complete.**
- [X] T011 [US1] Implement `code/generate_partitions.py`:
 - **Create** the script `code/generate_partitions.py` from scratch.
 - Use **arbitrary-precision integers** (Python native `int`) for DP to count partitions into distinct primes.
 - Iterate primes only (skip composites) to enforce distinct prime constraint.
 - Handle edge cases ($n < 5$ where $p_{\mathcal{P}}(n)=0$) by setting count to 0.
 - Calculate $Q_{as}(n)$ using the distinct-partition variant of Meinardus' theorem as defined in the plan.
 - Clamp $Q_{as}(n)$ to a small positive lower bound to prevent log(0).
 - **Generate data for the full range of n values up to 50,000. [UNRESOLVED-CLAIM: c_70425371 — status=not_enough_info]**
 - **Include `--n-max` argument using `argparse` with a default set to 50000. Log the chosen `n_max` to stdout at runtime.**
 - **Load reference values from `tests/data/reference_values.csv` (produced by T008) for validation during execution, instead of hardcoding.**
 - **Include inline validation logic to exclude rows where `p_P(n) <= 0` or `Q_as(n) <= 0` before any log-residual calculation.**
 - **Requires T004, T005, T013, and T018 to complete.**
- [ ] T012 [US1] Implement `code/generate_partitions.py` data export:
 - Export data to `data/raw/partitions_raw.csv` with columns: `n`, `p_P(n)`, `Q_as(n)`.
 - Generate SHA-256 checksum of the output file and update `state/projects/PROJ-799.yaml` at key `artifact_hashes.generate_partitions_raw` (format: hex string).
 - Update `state/projects/PROJ-799.yaml` key `updated_at` with current ISO timestamp.
 - **Requires T011 to complete.**
- [ ] T031 [US1] Add documentation to `generate_partitions.py`: Add a docstring explaining the generating function $\prod_{p \in \mathbb{P}} (1+q^p)$ and explicitly distinguishing it from the unrestricted partition generating function $\prod (1-q^k)^{-1}$. **Requires T011 to complete.**

**Checkpoint**: US1 functional. Data generation complete.

---

## Phase 4: User Story 2 - Calculate and Model Residual Error with Density Features (Priority: P2)

**Goal**: Calculate $R(n)$ and fit a model using prime density features to detect systematic bias.

**Independent Test**: Verify regression outputs coefficients, p-values, and $R^2 > 0.05$.

### Tests for User Story 2

- [ ] T014 [P] [US2] Contract test: Verify $R(n)$ calculation handles log(0) gracefully and matches expected values for sample $n$ in `tests/test_feature_engineering.py`.
- [ ] T015 [P] [US2] Integration test: Verify regression model outputs valid p-values and $R^2$ score in `tests/test_regression_model.py`.

### Implementation for User Story 2

- [ ] T016a [US2] Implement `code/feature_engineering.py`:
 - Load `data/raw/partitions_raw.csv`.
 - Compute $R(n) = \log(p_{\mathcal{P}}(n)) - \log(Q_{as}(n))$ for valid $n$.
 - **Explicitly exclude rows where n < 5 or p_P(n) <= 0 from the output `features.csv` to handle edge cases as required by the spec.**
 - Generate features: $\pi(n)$ (via precomputed sieve from T004), $1/\ln(n)$.
 - Calculate 'distance_to_nearest_prime' as the **absolute difference to the closest prime (either smaller or larger than n)**.
 - Calculate 'prime_gap_size' with the following logic to ensure deterministic, non-zero features:
 - **If n is prime**: Calculate the distance to the *next* prime (the gap size initiated by n).
 - **If n is composite**: Calculate the distance between the *next* prime and the *previous* prime (the size of the gap containing n).
 - **Rationale**: This ensures a consistent 'gap size' metric for all n, distinguishing the 'holes' (gaps) in the summand set.
 - Add oscillatory features: $\sin(\log n)$, $\cos(\log n)$ to capture periodic anomalies. **Ensure these columns are saved to `data/processed/features.csv`.**
 - Save `data/processed/features.csv`.
 - **Verify** that 'distance_to_nearest_prime', 'prime_gap_size', 'sin_log_n', and 'cos_log_n' are present and non-null.
 - **Requires T012 completion.**
- [ ] T016b [US2] Validate `data/processed/features.csv`: Implement `tests/test_feature_validation.py::test_features_non_null` that asserts columns 'distance_to_nearest_prime', 'prime_gap_size', 'sin_log_n', and 'cos_log_n' exist and are non-null in `data/processed/features.csv`. **Requires T016a to complete.**
- [ ] T017a [US2] Implement `code/regression_model.py` (Full Model):
 - Fit Generalized Additive Model (GAM) or Linear Regression with splines for density terms.
 - **Explicitly include oscillatory terms: `sin(log(n))`, `cos(log(n))` in the model formula as required by FR-005. This requirement applies regardless of whether GAM or Linear Regression is chosen. Add terms: beta1*sin(log(n)) + beta2*cos(log(n)) to the linear predictor.**
 - Output coefficients, p-values, $R^2$ to `data/processed/model_results.json` under a key 'full_model'.
 - **Requires T016a and T016b completion.**
- [ ] T017b [US2] Implement `code/regression_model.py` (Multiple Hypothesis Testing):
 - Perform per-predictor t-tests and ANOVA to generate a list of raw p-values for each predictor in the full model.
 - Output the list of raw p-values to `data/processed/raw_p_values.json`.
 - **Requires T017a completion.**
- [ ] T017c [US2] Implement `code/regression_model.py` P-value Correction:
 - Read the raw p-values from `data/processed/raw_p_values.json` generated by T017b.
 - Apply **Benjamini-Hochberg correction (alpha=0.05)** to the list of raw p-values (FR-005, SC-005).
 - Write corrected p-values to `data/processed/model_results.json` under the 'full_model' key.
 - **Requires T017a, T017b, and T021 completion.**
- [ ] T017b_null [US2] Implement `code/regression_model.py` (Null Model):
 - Fit an intercept-only (null) model.
 - Compare null model performance against the full model to verify systematic bias (FR-008).
 - **Output null model stats to `data/processed/model_results.json` under a nested key 'null_model' to prevent data collision with T017a's 'full_model' results.**
 - **Requires T016a and T016b completion.**
- [ ] T038 [US2] Implement `code/generate_residual_error_report.py`:
 - **Create a distinct artifact `docs/residual_error_term_report.md` as required by Constitution Principle VI.**
 - This report must explicitly document the finite-regime error term analysis, including the methodology for computing $R(n)$, the range of n, and the observed behavior of the error term.
 - **Requires T016a completion.**

**Checkpoint**: US2 functional. Statistical model trained and validated.

---

## Phase 5: User Story 3 - Validate Model Robustness and Visualize Convergence (Priority: P3)

**Goal**: Perform cross-validation with a standard k-fold partitioning scheme. and generate visualizations to confirm generalizability.

**Independent Test**: Verify CV MSE is reported and plot is generated.

### Tests for User Story 3

- [ ] T022 [US3] Contract test: Verify that k-fold cross-validation returns k MSE values and a mean, as described in standard validation frameworks (Bishop; Arlot & Celisse). in `tests/test_regression_model.py`. **Requires T024 to complete.**
- [ ] T023a [P] [US3] Integration test: Verify plot generation produces a valid PNG/PDF file in `tests/test_visualize_results.py`.

### Implementation for User Story 3

- [ ] T024 [US3] Implement `code/regression_model.py` (CV logic):
 - Perform k-fold cross-validation on the fitted model using scikit-learn's KFold.
 - Record MSE for each fold and mean MSE.
 - **Explicitly record the MEAN CV MSE and the corresponding derived R^2 as the final reported metrics in `model_results.json` (overriding training scores) to satisfy SC-002.**
 - **If the CV R^ is less than 0.05, the task must report this failure and trigger a model re-specification or a note in the final report explaining the failure.**
 - **Requires T017c completion.**
- [ ] T025 [US3] Implement `code/visualize_results.py`:
 - Plot $n$ (x-axis) vs $R(n)$ (raw residuals) and fitted correction term.
 - Highlight regions of high prime density vs. gaps.
 - **Overlay vertical lines at known prime gaps to visualize the impact of "holes" in the summand set on the residual trend. Use the 'prime_gap_size' column from `data/processed/features.csv` for this visualization.** **Addresses Reviewer Concern: "prime gaps create 'holes'... that fundamentally alter the asymptotic regime".**
 - Save plot to `data/processed/residual_convergence.png`.
 - **Requires T024 completion.**
- [ ] T026 [US3] Implement `code/visualize_results.py`:
 - Generate residual vs. fitted plot to check for homoscedasticity.
 - **Requires T024 completion.**
- [ ] T035 [US3] Implement `code/visualize_results.py`: Generate a specific plot comparing the residual trend $R(n)$ against the local prime gap size. This visualization will explicitly test the hypothesis that prime gaps (the 'holes') drive the deviation from the unrestricted partition asymptotic, as described in the spec's Edge Cases and US2. **Use the 'prime_gap_size' column from `data/processed/features.csv`.** **Requires T024 completion.**
- [ ] T039 [P] [US3] Run Full Pipeline: Implement `code/run_full_pipeline.py` to execute the entire sequence (US1 -> US2 -> US3) in a single run. **Measure and report the total execution time to verify SC-004 (6-hour limit).** **This task replaces the reliance on summing individual phase times.** **Requires T011, T016a, T024, T025, T026, T035 completion.**

**Checkpoint**: US3 functional. All visualizations and CV metrics ready.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027a [P] Documentation: Update `README.md` with project overview and run instructions.
- [ ] T027b [P] Documentation: Update `docs/methodology.md` with detailed justification for the distinct-prime generating function and the $n_{max}=50,000$ limit.
- [ ] T029a [P] Code cleanup: Remove unused imports from all Python files using `autoflake`.
- [ ] T029b [P] Code cleanup: Optimize DP loops using `numpy` vectorization where applicable.
- [ ] T030 [P] Run `quickstart.md` validation to ensure full pipeline executes end-to-end within 6 hours. **Note: This task is now superseded by T039 which performs the actual execution and timing.**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T004 and T005 are independent and can run in parallel.**
 - **T008 and T009 depend on T004 and must be executed after T004.**
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2) EXCEPT T008 and T009 which depend on T004. T005 is independent of T004 and can run in parallel.
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
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: Ensure `generate_partitions.py` uses arbitrary-precision integers and iterates only primes to respect the "distinct prime" constraint and memory limits.
- **Critical Constraint**: The asymptotic baseline $Q_{as}(n)$ MUST use the distinct-partition variant of Meinardus' theorem as per the spec.
- **Critical Constraint**: The entire pipeline must complete within 6 hours (SC-004). Monitor time budgets in T010b, T010c, T010d, and T039.
- **Critical Constraint**: P-value correction (Benjamini-Hochberg, alpha=0.05) is mandatory (SC-005).
- **Critical Constraint**: US2 and US3 must be executed sequentially after US1 due to strict data dependencies.
- **Revision Constraint**: T032 merged into T011 to resolve circular dependency.
- **Revision Constraint**: T018 moved to Phase 2 to ensure asymptotic regime is defined before implementation.
- **Revision Constraint**: T017b added to generate p-values for T017c correction.
- **Revision Constraint**: T016a updated to calculate 'prime_gap_size' for T025/T035 visualization.
- **Revision Constraint**: T011 updated to use arbitrary-precision integers and hardcoded reference validation.
- **Revision Constraint**: T008 updated to use exact same algorithm as T011.
- **Revision Constraint**: T004 updated to include checksumming.
- **Important**: No downstream tasks can be marked complete until their producer tasks are verified and complete.
- **Revision Concern**: T036 addresses the reviewer's concern about prime gaps altering the asymptotic regime by explicitly modeling the gap size as a predictor and visualizing its impact.
- **Revision Concern**: T028 removed to merge duplicate efforts into T018.
- **Revision Concern**: T011 updated to load reference data from file instead of hardcoding.
- **Revision Concern**: T011 default `--n-max` set to 50000.
- **Revision Concern**: T021 moved to Phase 2 to ensure it is completed before T017c.
- **Revision Concern**: T017c updated to read raw p-values from T017b's output file.
- **Revision Concern**: T016a updated to define `prime_gap_size` for prime n as distance to next prime.
- **Revision Concern**: T017b_null updated to use nested JSON key 'null_model'.
- **Revision Concern**: T024 updated to include failure mode for R^2 threshold.
- **Revision Concern**: T038 added to document residual error term as distinct artifact.
- **Revision Concern**: T039 added to execute and time full end-to-end pipeline.