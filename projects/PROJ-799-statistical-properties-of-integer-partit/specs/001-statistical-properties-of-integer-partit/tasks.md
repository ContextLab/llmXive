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

**Purpose**: Project initialization and basic structure (Handled by scaffolding agent; manual tasks removed)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. This phase now includes critical theoretical validations (T040-T044) to satisfy Phase 0 research requirements before implementation begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Note**: Tasks T004 and T005 are independent and can run in parallel.

- [X] T004 [P] Implement `code/utils/prime_sieve.py`: Generate primes up to **[deferred]** using Sieve of Eratosthenes. **Output**: Save the list of primes to `data/cache/primes.npy` as a **1D `np.int32` array**. **Verification**: Ensure the file exists, dtype is `int32`, shape matches the count of primes <= 50,050 (must be a sufficiently large number of primes). **Data Hygiene**: Generate SHA-256 checksum of the output file using `hashlib.sha256` and update `state/projects/PROJ-799.yaml` at key `artifact_hashes.primes_sieve` (format: hex string). Update `state/projects/PROJ-799.yaml` key `updated_at` with current ISO timestamp. **Note**: `data/cache/primes.npy` is a **cache**; it MUST be regenerated on every fresh run if the sieve algorithm changes. Do not treat as a static artifact. **Rationale**: Extending to [deferred] ensures the "next prime" exists for n=50,000 gap calculations. **Status**: Generation complete. Validation pending downstream tasks.
- [X] T005 [P] Implement `code/utils/asymptotic_baseline.py`: Implement $Q_{as}(n)$ based on the distinct-partition variant of Meinardus' theorem. The implementation must use the leading-order term derived from the generating function $\prod (+q^p)$. **Logic**: Read `data/reports/applicability_report.json` (produced by T005b). If the report indicates Meinardus conditions are not met, switch to the fallback truncated Dirichlet series parameters defined in T005b. **Note**: T005 is dependent on T005b completion. **Status**: Implementation complete. Validation pending downstream tasks.
- [X] T005b [P] Implement `code/utils/validate_meinardus.py`: Implement logic to validate the applicability of Meinardus' theorem conditions (pole structure of the prime zeta function). **Output**: If conditions are met, output `data/reports/applicability_report.json` with status "valid". If not met, output the same file with status "invalid" and provide the parameters for the fallback truncated Dirichlet series approximation. **Verification**: Ensure the report file is generated with correct JSON structure. **Requires T004 completion.**
- [X] T006 [P] Create `data/schemas/partition_record.schema.yaml` and `data/schemas/regression_output.schema.yaml`. **Status**: Schema definition complete. Ready for validation by downstream tasks.
- [X] T007 [P] Setup `state/projects/PROJ-799.yaml` structure for checksums and versioning (keys: `artifact_hashes`, `updated_at`). **Status**: Schema definition complete. Keys defined. Values to be populated by T004, T005, T011, etc. **Note**: This task defines the *structure* of the state file. It does not populate values. T004 and T005 will populate the `artifact_hashes` keys.
- [ ] T018 [P] Implement `docs/scope_justification.md`: Explicitly define and document the asymptotic regime (small n vs large n vs transition region) for the analysis. Justify the $n_{max}=50,000$ limit as a transition region where prime gaps begin to significantly impact the density of summands, distinguishing it from the unrestricted partition regime. **Addresses Reviewer Concern: "Does the current treatment account for the fact that prime gaps create 'holes'..." and "explicitly state which asymptotic regime is being targeted".** **This task must be completed before T016a and T017a to ensure model design is informed by the defined regime.** **Status**: Definition complete. Ready for implementation of T011.
- [ ] T021 [US2] Test: Verify Benjamini-Hochberg correction is applied correctly and p-values are adjusted in `tests/test_regression_model.py`. **Implementation**: Test the correction function in isolation using synthetic p-values (independent of full model output). **Note**: Must be written and failing before T017a implementation. **Moved to Phase 4 to ensure it is completed after model schema definition.** **Requires T017a completion.**
- [X] T008 [US1] Generate Reference Data: Implement `code/generate_reference.py` to compute exact $p_{\mathcal{P}}(n)$ for **all** $n$ in the range **n in [, 100]** using the **exact same distinct-prime DP algorithm** as T011, limited to this range. **Algorithm**: Use a 1D array DP iterating over primes <= n (where n<=100). **Output**: Save the output to `tests/data/reference_values.csv` with columns `n`, `p_P(n)`. **Verification**: Ensure the file contains a dataset of non-negative integer counts. **Requires T004 to complete.**
- [X] T009 [US1] Contract test: Implement `tests/test_partition_logic.py` to verify $p_{\mathcal{P}}(n)$ matches `tests/data/reference_values.csv`. **Logic**: The test must validate the algorithm on the full range [1, 100] internally. However, when comparing against the output of T011 (`data/raw/partitions_raw.csv`), it must **filter out rows where n < 5** before comparison, as T011 excludes these from the main output. For n < 5, the test verifies the algorithm logic returns 0 but does not expect rows in the output file. **Requires T008 to complete.**
- [ ] T040 [P] Update `docs/scope_justification.md`: Add a dedicated section titled "The Distinct-Prime Generating Function vs. Unrestricted Partitions". Explicitly contrast $\prod_{p \in \mathbb{P}} (1+q^p)$ with $\prod_{k \ge 1} (1-q^k)^{-1}$. Explain why the latter (Hardy-Ramanujan) is invalid here and why the Prime Number Theorem must be invoked in the saddle-point analysis for the former. **Addresses Reviewer Concern: "does the current treatment account for the fact that prime gaps create 'holes'..."**. **Requires T018 completion. Note: T011 is incomplete, so documentation for T011 is premature.**
- [ ] T041 [P] Update `code/utils/asymptotic_baseline.py`: Add a detailed docstring and inline comments deriving the leading-order term of $Q_{as}(n)$ specifically for distinct prime partitions. Cite Meinardus and Andrews regarding the application to sets with density $\pi(x) \sim x/\ln x$. Explicitly state the assumption that the leading-order term dominates in the transition region $n \le [deferred]$. **Addresses Reviewer Concern: "invoke the prime number theorem in the saddle-point analysis"**. **Requires T018 completion. Note: T011 is incomplete, so documentation for T011 is premature.**
- [ ] T044 [P] Update `docs/methodology.md`: Rewrite the "Asymptotic Regime" section to explicitly define the "Transition Region" hypothesis. State that $n=50,000$ is chosen not as a "large n" limit where asymptotics are perfect, but as a region where the discrete nature of primes (gaps) is still significant enough to be modeled by the regression features, but large enough to show a trend. **Addresses Reviewer Concern: "explicitly state which asymptotic regime is being targeted"**. **Requires T018 and T040 completion. Note: T011 is incomplete, so documentation for T011 is premature.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Exact Partition Values and Asymptotic Baseline (Priority: P1) 🎯 MVP

**Goal**: Compute exact $p_{\mathcal{P}}(n)$ for $n \in [1, 50000]$ and generate $Q_{as}(n)$ baseline, ensuring memory < 6.5 GB.

**Independent Test**: Verify output CSV has correct columns, non-negative integers for counts, and matches reference values for small sample sizes.

### Tests for User Story 1

- [ ] T010a [P] [US1] Integration test: Verify `generate_partitions.py` completes within 2 hours and memory < 6.5 GB in `tests/test_pipeline.py`. **Requires T011 completion.**
- [ ] T010b [P] [US1] Time-budget test: Verify that the DP generation phase completes within Approximately one to two hours (derived from SC-004 total time budget of h minus 1.25h buffer for US2 and US3) in `tests/test_pipeline.py`. **Implementation**: Use `pytest-timeout` decorator to enforce the -hour limit. Reference SC-004 for total budget context. **Requires T011 completion.** **Fallback Strategy**: If the 1.25h timeout is approached, the script must automatically downsample the range (e.g., to `n_max=10,000`) and log a warning. **CRITICAL**: This fallback is for debugging ONLY. If the fallback triggers, the task is considered FAILED and must be retried with optimizations. The final deliverable MUST be `n_max=50,000`. **Verification**: The test must verify the fallback strategy is triggered and logged correctly if the timeout is breached, and that the task fails if the full range is not achieved.
- [ ] T010c [P] [US2] Time-budget test: Verify that the feature engineering and modeling phase (US2) completes within 3.0 hours (derived from SC-004 total 6h minus 1.25h DP and 1.75h buffer for US3) in `tests/test_pipeline.py`. **Requires T016a completion.**
- [ ] T010d [P] [US3] Time-budget test: Verify that the visualization phase (US3) completes within 1.75 hours (derived from SC-004 total 6h minus 1.25h DP and 3.0h US2) in `tests/test_pipeline.py`. **Requires T024 completion.**

### Implementation for User Story 1

- [X] T013 [US1] Validate Reference Data: Implement `tests/test_reference_validation.py` to verify `tests/data/reference_values.csv` (produced by T008) contains valid integers and correct column headers. **This task validates the reference file ONLY, not the full generation output.** **Requires T008 to complete.**
- [ ] T011 [US1] Implement `code/generate_partitions.py`:
 - **Create** the script `code/generate_partitions.py` from scratch.
 - Use **arbitrary-precision integers** (Python native `int`) for DP to count partitions into distinct primes.
 - Initialize a 1D array `dp` of size `n_max + 1` with `dp[0] = 1` and all others `0`.
 - Iterate primes only (skip composites) to enforce distinct prime constraint.
 - Handle edge cases ($n < 5$ where $p_{\mathcal{P}}(n)=0$) by **excluding them from the main output and logging them to stdout/stderr (DO NOT create a separate artifact file)**.
 - Calculate $Q_{as}(n)$ using the distinct-partition variant of Meinardus' theorem as defined in the plan (or fallback from T005b).
 - Clamp $Q_{as}(n)$ to a small positive lower bound to prevent log(0).
 - **Generate data for the full range of n values up to 50,000.**
 - **Include `--n-max` argument using `argparse` with a default set to 50000. Log the chosen `n_max` to stdout at runtime.**
 - **Load reference values from `tests/data/reference_values.csv` (produced by T008) for validation during execution, instead of hardcoding.**
 - **Include inline validation logic to exclude rows where `p_P(n) <= 0` or `Q_as(n) <= 0` before any log-residual calculation.**
 - **Export data to `data/raw/partitions_raw.csv` with columns: `n`, `p_P(n)`, `Q_as(n)`.**
 - **Generate SHA-256 checksum of the output file and update `state/projects/PROJ-799.yaml` at key `artifact_hashes.generate_partitions_raw` (format: hex string).**
 - **Verify memory usage < 6.5 GB during execution. **
 - **Requires T004, T005, T013, T018, T040, T041, T044 to complete.**
- [ ] T031 [US1] Add documentation to `generate_partitions.py`: Add a docstring explaining the generating function $\prod_{p \in \mathbb{P}} (1+q^p)$ and explicitly distinguishing it from the unrestricted partition generating function $\prod (1-q^k)^{-1}$. **Requires T011 completion.**

**Checkpoint**: US1 functional. Data generation complete.

---

## Phase 4: User Story 2 - Calculate and Model Residual Error with Density Features (Priority: P2)

**Goal**: Calculate $R(n)$ and fit a model using prime density features to detect systematic bias.

**Independent Test**: Verify regression outputs coefficients, p-values, and $R^2 > 0.05$.

### Tests for User Story 2

- [ ] T014 [P] [US2] Contract test: Verify $R(n)$ calculation handles log(0) gracefully and matches expected values for sample $n$ in `tests/test_feature_engineering.py`. **Requires T016a completion.**
- [ ] T015 [P] [US2] Integration test: Verify regression model outputs valid p-values and $R^$ score in `tests/test_regression_model.py`. **Requires T017a completion.**
- [ ] T021 [P] [US2] Test: Verify Benjamini-Hochberg correction is applied correctly and p-values are adjusted in `tests/test_regression_model.py`. **Implementation**: Test the correction function in isolation using synthetic p-values. **Note**: Must be written and failing before T017a implementation. **Moved to Phase 4 to ensure it is completed after model schema definition.** **Requires T017a completion.**

### Implementation for User Story 2

- [ ] T016a [US2] Implement `code/feature_engineering.py`:
 - Load `data/raw/partitions_raw.csv`.
 - Compute $R(n) = \log(p_{\mathcal{P}}(n)) - \log(Q_{as}(n))$ for valid $n$.
 - **Explicitly exclude rows where n < 5 or p_P(n) <= 0 from the output `features.csv` to handle edge cases as required by the spec.**
 - Generate features: $\pi(n)$ (via precomputed sieve from T004), $1/\ln(n)$.
 - **Calculate 'cumulative_prime_density' as $\sum_{p \le n} \frac{1}{p}$ using the precomputed primes array.**
 - Calculate 'distance_to_nearest_prime' as the **absolute difference to the closest prime (either smaller or larger than n)**.
 - Calculate 'prime_gap_size' with the following logic to ensure deterministic, non-zero features:
 - **If n is prime**: Calculate the distance to the *next* prime (the gap size initiated by n).
 - **If n is composite**: Calculate the distance between the *next* prime and the *previous* prime (the size of the gap containing n).
 - **Use `np.searchsorted` on the precomputed primes array to find nearest primes efficiently (O(log N)).**
 - **Do NOT include oscillatory features like sin(log n) or cos(log n) as they are forbidden by FR-005.**
 - Add only theoretically motivated density features.
 - Save `data/processed/features.csv`.
 - **Verify** that 'cumulative_prime_density', 'distance_to_nearest_prime', 'prime_gap_size' are present and non-null.
 - **Requires T011 completion.**
- [ ] T016b [US2] Validate `data/processed/features.csv`: Implement `tests/test_feature_validation.py::test_features_non_null` that asserts columns 'cumulative_prime_density', 'distance_to_nearest_prime', 'prime_gap_size' exist and are non-null in `data/processed/features.csv`. **Requires T016a to complete.**
- [ ] T017a [US2] Implement `code/regression_analysis.py` (Full Model):
 - Fit Generalized Additive Model (GAM) using `statsmodels.gam.GLM` with formula `R ~ s(log(n)) + pi(n) + inv_log_n + cumulative_prime_density + prime_gap_size`.
 - **Explicitly include ONLY theoretically motivated terms. Do NOT include sin(log n) or cos(log n).**
 - Output **uncorrected** coefficients, p-values, $R^2$ to `data/processed/model_results_full.json` under a key 'full_model'.
 - **Requires T016a and T016b completion.**
- [ ] T017a_fallback [US2] Implement `code/regression_analysis.py` (Linear Regression Fallback):
 - If the GAM in T017a fails (e.g., convergence issues), implement a fallback Linear Regression model with the same formula structure (without `s()` smoothing) to satisfy FR-005's "or" condition.
 - Output results to `data/processed/model_results_linear.json`.
 - **Requires T017a completion.**
- [ ] T017b [US2] Implement `code/regression_analysis.py` (Multiple Hypothesis Testing):
 - Perform per-predictor t-tests and ANOVA to generate a list of raw p-values for each predictor in the full model.
 - Output the list of raw p-values to `data/processed/raw_p_values.json`.
 - **Requires T017a completion.**
- [ ] T017c [US2] Implement `code/regression_analysis.py` P-value Correction:
 - Read the raw p-values from `data/processed/raw_p_values.json` generated by T017b.
 - **Apply BOTH Bonferroni and Benjamini-Hochberg corrections (alpha=0.05) to the list of raw p-values (FR-005, SC-005).**
 - **Write both sets of corrected p-values to `data/processed/model_results_full.json` under keys 'full_model_bonferroni' and 'full_model_bh'.**
 - **Requires T017a, T017b completion.**
- [ ] T017d_new [US2] Implement `code/regression_analysis.py` (HAC Correction & Merge):
 - Calculate **Newey-West standard errors** (or HAC estimators) for the regression model coefficients to handle autocorrelation in residuals as required by the plan's 'Statistical Rigor' section.
 - **Output the HAC-corrected p-values and confidence intervals directly into `data/processed/model_results_full.json` under the key 'full_model_hac'.**
 - **This task is atomic: it calculates and writes to the final artifact in one step, eliminating the need for a separate merge task.**
 - **Requires T017a completion.**
- [ ] T017b_null [US2] Implement `code/regression_analysis.py` (Null Model):
 - Fit an intercept-only (null) model.
 - Compare null model performance against the full model to verify systematic bias (FR-008).
 - **Output null model stats to `data/processed/model_results_null.json` to prevent data collision with T017a's 'full_model' results.**
 - **Requires T016a and T016b completion.**
- [ ] T038 [US2] Implement `code/generate_residual_error_report.py`:
 - **Create a distinct artifact `docs/residual_error_term_report.md` as required by Constitution Principle VI.**
 - This report must explicitly document the finite-regime error term analysis. **Mandatory Sections**:
   1. **Methodology**: Explicit description of the DP algorithm used for exact partition values.
   2. **Finite-Range Table**: A table of $R(n)$ for $n \in [, 50000]$.
   3. **Error Term Analysis**: Observed behavior of the error term and its relationship to prime density.
   4. **Conclusion**: Summary of whether the error term is systematic or random.
 - **Requires T016a completion.**

**Checkpoint**: US2 functional. Statistical model trained and validated.

---

## Phase 5: User Story 3 - Validate Model Robustness and Visualize Convergence (Priority: P3)

**Goal**: Perform cross-validation with a standard k-fold partitioning scheme. and generate visualizations to confirm generalizability.

**Independent Test**: Verify CV MSE is reported and plot is generated.

### Tests for User Story 3

- [ ] T022 [US3] Contract test: Verify that k-fold cross-validation returns k MSE values and a mean, as described in standard validation frameworks (Bishop; Arlot & Celisse). in `tests/test_regression_model.py`. **Requires T024 to complete.**
- [ ] T023a [P] [US3] Integration test: Verify plot generation produces a valid PNG/PDF file in `tests/test_visualize_results.py`. **Requires T024 and T025 completion.**

### Implementation for User Story 3

- [ ] T024 [US3] Implement `code/regression_analysis.py` (CV logic):
 - Perform **Time-Series Cross-Validation** on the fitted model using `sklearn.model_selection.TimeSeriesSplit` with `n_splits=10`.
 - **Do NOT use standard KFold as residuals are autocorrelated.**
 - Record MSE for each fold and mean MSE.
 - **Explicitly record the MEAN CV MSE and the corresponding derived R^2 as the final reported metrics in `model_results_full.json` (overriding training scores) to satisfy SC-002.**
 - **If the CV R^ is less than 0.05, raise a `RuntimeError` with message "CV R^2 < 0.05 threshold met".**
 - **Requires T017d_new completion.**
- [ ] T025 [US3] Implement `code/validation.py`:
 - Plot $n$ (x-axis) vs $R(n)$ (raw residuals) and fitted correction term.
 - Highlight regions of high prime density vs. gaps.
 - **Overlay vertical lines at known prime gaps to visualize the impact of "holes" in the summand set on the residual trend. Use the 'prime_gap_size' column from `data/processed/features.csv` for this visualization.** **Addresses Reviewer Concern: "prime gaps create 'holes'... that fundamentally alter the asymptotic regime".**
 - Save plot to `data/processed/residual_convergence.png`.
 - **Requires T024 completion.**
- [ ] T026 [US3] Implement `code/validation.py`:
 - Generate residual vs. fitted plot to check for homoscedasticity.
 - **Requires T024 completion.**
- [ ] T035 [US3] Implement `code/validation.py`: Generate a specific plot comparing the residual trend $R(n)$ against the local prime gap size. This visualization will explicitly test the hypothesis that prime gaps (the 'holes') drive the deviation from the unrestricted partition asymptotic, as described in the spec's Edge Cases and US2. **Use the 'prime_gap_size' column from `data/processed/features.csv`.** **Requires T024 completion.**
- [ ] T039 [US3] Run Full Pipeline: Implement `code/run_full_pipeline.py` to execute the entire sequence (US1 -> US2 -> US3) in a single run. **Measure and report the total execution time to verify SC-004 (6-hour limit).** **Execute command: `python code/run_full_pipeline.py --n-max 50000`**. **This task replaces the reliance on summing individual phase times.** **Requires T011, T016a, T024, T025, T026, T035, T017d_new completion.**

**Checkpoint**: US3 functional. All visualizations and CV metrics ready.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027a [P] Documentation: Update `README.md` with project overview and run instructions. **Requires project completion.**
- [ ] T027b [P] Documentation: Update `docs/methodology.md` with detailed justification for the distinct-prime generating function and the $n_{max}=50,000$ limit. **Requires project completion.**
- [ ] T029a [P] Code cleanup: Remove unused imports from all Python files using `autoflake`. **Requires code completion.**
- [ ] T029b [P] Code cleanup: Optimize DP loops using `numpy` vectorization where applicable. **Requires code completion.**
- [ ] T030 [P] Run `quickstart.md` validation to ensure full pipeline executes end-to-end within 6 hours. **Note: This task is now superseded by T039 which performs the actual execution and timing.** **Requires T039 completion.**
- [ ] T042 [US2] Refine `code/feature_engineering.py`: Ensure the 'prime_gap_size' feature calculation logic is robust for $n$ near the upper bound ([deferred]) where the "next prime" might be outside the precomputed sieve range. Implement a fallback to generate the next prime on-the-fly if necessary, or explicitly document the truncation error if the next prime is not available. **Addresses Reviewer Concern: "prime gaps create 'holes'... that fundamentally alter the asymptotic regime"**. **Requires T004 and T016a completion.**
- [ ] T043 [US3] Enhance `code/validation.py`: In the plot generated by T025, add a secondary y-axis or annotation indicating the local density of primes ($\pi(n)/n$) alongside the residual $R(n)$. This visual correlation will help verify if the deviation is indeed driven by density fluctuations. **Addresses Reviewer Concern: "fundamentally alter the asymptotic regime"**. **Requires T025 completion.**
- [ ] T045 [US3] Implement `code/regression_analysis.py`: Consolidate all regression analysis logic (GAM, Linear Regression, HAC, CV, Null Model) into `code/regression_analysis.py` as required by the plan's `quickstart.md`. This script must be the single entry point for all statistical modeling tasks previously described in T017a, T017a_fallback, T017b, T017c, T017d_new, T017b_null, and T024. **This task ensures the file exists and contains the correct logic to satisfy the plan's execution path.** **Requires T017a, T017a_fallback, T017b, T017c, T017d_new, T017b_null, T024 completion.**
- [ ] T046 [US3] Implement `code/validation.py`: Consolidate all visualization logic (T025, T026, T035) into `code/validation.py` as required by the plan's `quickstart.md`. This script must be the single entry point for all plotting tasks. **This task ensures the file exists and contains the correct logic to satisfy the plan's execution path.** **Requires T025, T026, T035 completion.**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - handled by scaffolding
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T004 and T005b are independent and can run in parallel.**
 - **T008 and T009 depend on T004 and must be executed after T004.**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1) must complete before US2 (P2) and US3 (P3) due to data dependencies.**
 - **US2 strictly requires `data/raw/partitions_raw.csv` produced by US1.**
 - **US3 strictly requires `data/processed/model_results_full.json` produced by US2.**
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 output (`partitions_raw.csv`) and T008 (reference data). **US2 produces two distinct artifacts: `data/processed/model_results_full.json` (from T017d_new) and `data/processed/model_results_null.json` (from T017b_null).**
- **User Story 3 (P3)**: Depends on US2 output (`model_results_full.json`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (handled by scaffolding)
- All Foundational tasks marked [P] can run in parallel (within Phase 2) EXCEPT T008 and T009 which depend on T004. T005b is independent of T004 and can run in parallel. T005 depends on T005b.
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
 - **Wait for US2 completion** (Data artifact `model_results_full.json` must exist).
 - **Developer C: User Story 3 (Visualization)**. (Cannot start until US2 data exists).
3. Stories complete and integrate sequentially based on data flow.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (Scaffolding)
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
- **Critical Constraint**: P-value correction (Bonferroni AND Benjamini-Hochberg) is mandatory (SC-005).
- **Critical Constraint**: HAC standard errors (Newey-West) are mandatory for SC-001 and must be merged into the final results (T017d_new).
- **Critical Constraint**: US2 and US3 must be executed sequentially after US1 due to strict data dependencies.
- **Revision Constraint**: T032 merged into T011 to resolve circular dependency.
- **Revision Constraint**: T018 moved to Phase 2 to ensure asymptotic regime is defined before implementation.
- **Revision Constraint**: T017b added to generate p-values for T017c correction.
- **Revision Constraint**: T016a updated to calculate 'prime_gap_size' for T025/T035 visualization.
- **Revision Constraint**: T011 updated to use arbitrary-precision integers and hardcoded reference validation.
- **Revision Constraint**: T008 updated to use exact same algorithm as T011.
- **Revision Constraint**: T004 updated to include checksumming and moved to `data/cache/`.
- **Important**: No downstream tasks can be marked complete until their producer tasks are verified and complete.
- **Revision Concern**: T036 addresses the reviewer's concern about prime gaps altering the asymptotic regime by explicitly modeling the gap size as a predictor and visualizing its impact.
- **Revision Concern**: T028 removed to merge duplicate efforts into T018.
- **Revision Concern**: T011 updated to load reference data from file instead of hardcoding.
- **Revision Concern**: T011 default `--n-max` set to 50000.
- **Revision Concern**: T021 moved to Phase 4 to ensure it is completed after model schema definition.
- **Revision Concern**: T017c updated to read raw p-values from T017b's output file.
- **Revision Concern**: T016a updated to define `prime_gap_size` for prime n as distance to next prime.
- **Revision Concern**: T017b_null updated to use nested JSON key 'null_model'.
- **Revision Concern**: T024 updated to include failure mode for R^2 threshold.
- **Revision Concern**: T038 added to document residual error term as distinct artifact.
- **Revision Concern**: T039 added to execute and time full end-to-end pipeline.
- **Revision Concern**: The generating function $\prod_{p \in \mathbb{P}} (1+q^p)$ is explicitly distinguished from the unrestricted partition generating function in T031 and T011 to address the reviewer's concern about the "critical difference" in summand density.
- **Revision Concern**: The asymptotic regime (transition region) is explicitly defined in T018 to justify the $n_{max}=50,000$ limit and address the reviewer's concern about "small n, large n, or transition region".
- **Revision Concern**: The 'prime_gap_size' feature and T025/T035 visualizations explicitly model the "holes" in the summand set created by prime gaps, directly addressing the reviewer's concern about how gaps "fundamentally alter the asymptotic regime".
- **Revision Concern**: T040, T041, T042, T043, T044 moved to Phase 2/4 to ensure theoretical validation occurs before implementation.
- **Revision Concern**: T017d_new and T017e_new added to calculate and merge Newey-West standard errors into the final results.
- **Revision Concern**: T017c updated to run BOTH Bonferroni and Benjamini-Hochberg corrections.
- **Revision Concern**: T011 updated to generate `partitions_excluded.csv` for edge cases. (Note: Updated to remove artifact creation).
- **Revision Concern**: T010b updated with fallback strategy for timeout.
- **Revision Concern**: T004 updated to save to `data/cache/`.
- **Revision Concern**: T013 dependencies simplified.
- **Revision Concern**: T039 dependencies updated to include T017d_new and T017e_new.
- **Revision Concern**: The 'Phase 6' section has been removed to avoid duplication with Phase 2.
- **Revision Concern**: T045 and T046 added to explicitly create the missing scripts required by the plan's quickstart.md.
- **Revision Concern**: T005 updated to depend on T005b for fallback logic.
- **Revision Concern**: T009 updated to filter n<5 when comparing against T011 output.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T045 [Resolved] Reconcile run-book vs implementation for `code/regression_analysis.py`: The quickstart run-book invokes this script. **Action**: Implement `code/regression_analysis.py` to contain the logic previously described in T017a-T017e_null. **Requires T017a, T017a_fallback, T017b, T017c, T017d_new, T017b_null, T024 completion.**
- [ ] T046 [Resolved] Reconcile run-book vs implementation for `code/validation.py`: The quickstart run-book invokes this script. **Action**: Implement `code/validation.py` to contain the logic previously described in T025-T026. **Requires T025, T026, T035 completion.**