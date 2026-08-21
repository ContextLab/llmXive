# Tasks: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

**Input**: Design documents from `/specs/001-assess-heterogeneity-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per `plan.md`)
- Paths shown below assume single project structure - adjusted based on `plan.md`

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `plan.md` (mkdir `code/simulation`, `code/analysis`, `code/visualization`, `code/reporting`, `data/raw`, `data/processed`, `data/results`, `tests/unit`, `tests/integration`, `contracts`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing `numpy`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `pyyaml`, `pytest`- [X] T003 [P] Configure linting (flake8/black) and pre-commit hooks in `code/`
- [X] T006b [P] **Create Configuration File**: Create `code/config.yaml` with keys `nominal_confidence_level` (default 0.95 (1710.08708, https://arxiv.org/abs/1710.08708)), `simulation_parameters` (replicate counts, tau2 levels). **This defines the schema.**
- [X] T006c [P] **Implement Config Loader**: Implement `code/config_loader.py` to parse `code/config.yaml`. **Must catch `FileNotFoundError` from data fetch and trigger fallback logic.**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data ingestion, and contracts that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Data must be fetched and verified before simulation.

- [ ] T004a [P] **Define Simulated Dataset Schema**: Create `specs/001-assess-heterogeneity-impact/contracts/simulated_dataset.schema.yaml`. **Must include `injected_true_effect`, `injected_tau2`, `N_studies`, `reliability_flag` (boolean).** **[Key Entity: SimulatedDataset] [FR-001]**
- [ ] T004b [P] **Define Estimation Result Schema**: Create `specs/001-assess-heterogeneity-impact/contracts/estimation_result.schema.yaml`. **Must include `I^2`, `Q`, `reliability_flag` (boolean).** **[Key Entity: EstimationResult] [SC-002]**
- [X] T004c [P] **Define Aggregated Metric Schema**: Create `specs/001-assess-heterogeneity-impact/contracts/aggregated_metric.schema.yaml`. **[Key Entity: AggregatedMetric]**
- [X] T005 [P] Implement `code/simulation/__init__.py` and `code/analysis/__init__.py` to expose core classes
- [X] T006 Create `code/main.py` entry point that orchestrates the pipeline (generation -> estimation -> analysis -> reporting) with CLI argument support for seeds and levels
- [X] T007 Setup logging infrastructure in `code/utils/logging.py` to capture convergence failures and simulation progress to `data/results/simulation.log`
- [X] T040 [P] **Fetch Real Data**: Create `code/scripts/fetch_cochrane.py`. **Execute: `python code/scripts/fetch_cochrane.py`.** **Source**: Attempt to fetch from a verified Cochrane URL (e.g., `https://osf.io/...` or a specific Zenodo DOI). **CRITICAL**: The script MUST raise `FileNotFoundError('REAL_DATA_FETCH_FAILED')` if the fetch fails. **This specific exception triggers the controlled fallback to T040b-gen.** Do not halt the pipeline; the loader (T006c) must catch this and invoke T040b-gen.
- [ ] T040b-gen [P] **Generate Verified Synthetic Base**: Create `code/scripts/generate_synthetic_base.py`. **Execute: `python code/scripts/generate_synthetic_base.py`.** **Trigger**: Only executed if T040 raises `FileNotFoundError('REAL_DATA_FETCH_FAILED')`. **Parameters**: Accept `base_params` from config or derive from literature (Jackson et al., 2010) if not provided. **Source**: Cite source: Jackson et al. (). **Write these parameters to `code/config.yaml` under `synthetic_base_params`. Save as `data/raw/cochrane_base_synthetic.csv`.** **Verify `data/raw/cochrane_base_synthetic.csv` exists and contains a representative set of rows with columns [effect, se, study_id].** **Verify `research.md` contains the string "synthetic_base_params" and "Jackson et al. (2010)" by running a Python script that parses the file and confirms the citation exists in the bibliography or text.** **Output**: Generate a raw statistics file `data/raw/synthetic_base_stats.json` containing the empirical mean and SE distribution parameters of the generated synthetic base.
- [ ] T040b-adapt [P] **Adapt Synthetic Parameters**: Create `code/scripts/adapt_synthetic_parameters.py`. **Trigger**: Executed after T040b-gen if real data fetch failed. **Logic**: Parse `data/raw/synthetic_base_stats.json` (from T040b-gen) to calculate empirical mean effect, SE distribution parameters (mu, sigma), and N_studies. Update `code/config.yaml` with these derived `synthetic_base_params`. **This ensures the simulation perturbs based on the structural properties of the synthetic base.** **[FR-001]** **DEPENDS ON: T040b-gen.**
- [ ] T040b-doc [P] **Verify Synthetic Base Documentation**: Create a script to verify `research.md` and `data/raw/README.md`. **Execute**: Python script to check `research.md` contains "synthetic_base_params" and "Jackson et al. (2010)", AND `data/raw/README.md` contains "Synthetic Base Used". **Fail if checks return non-zero.** **Update `data/raw/README.md` to explicitly state "Synthetic Base Used" with parameters.**
- [X] T040c [P] **Adapt Parameters (Real Data)**: Create `code/scripts/adapt_parameters.py`. **Trigger**: Executed only if T040 succeeds (real data fetched). **Logic**: Parse the fetched Cochrane data to calculate empirical mean effect, SE distribution parameters (mu, sigma), and N_studies. Update `code/config.yaml` with these derived `synthetic_base_params`. **This ensures the simulation perturbs based on the structural properties of the real data.** **[FR-001]**
- [X] T041 [US1] **Document Data Source**: Create `data/raw/README.md` and update `research.md` to explicitly document the source URL, accession ID, and citation for the base dataset used in T040 OR (T040b-gen AND T040b-adapt AND T040b-doc). **DEPENDS ON: T040 completion OR (T040b-gen completion AND T040b-adapt completion AND T040b-doc completion).**

---

## Phase 3: User Story 1 - Simulation Engine Execution (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic meta-analysis datasets with controlled $\tau^2$ levels based on Cochrane data structures.

**Independent Test**: Run `code/simulation/generator.py` with $\tau^2 \in \{0, 0.1\}$ and multiple replicates; verify output JSON contains injected $\tau^2$ and generated effect sizes; process exits 0 within 10 mins.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/simulation/generator.py` to load base data from `data/raw/` (either `cochrane_base.csv` from T040/T040c or `cochrane_base_synthetic.csv` from T040b-gen/T040b-adapt) and implement a loop generating ≥500 replicates per level for heterogeneity levels $\{0, 0.1, 0.5, 1.0, 2.0\}$. **Ensure output conforms to `contracts/simulated_dataset.schema.yaml` (including `N_studies` and `reliability_flag` fields).** **Output must include `injected_true_effect` and `injected_tau2` columns.** **Verify output artifact `data/results/simulation_raw.json` contains a sufficient number of records to support statistical power across all experimental conditions (500 replicates x 5 levels).** **[FR-001, SC-004]** **DEPENDS ON: T040b-adapt OR T040c.**
- [ ] T012 [US1] Implement logic in `generator.py` to handle $\tau^2=0$ without numerical instability (Edge Case: Zero Variance)

### Tests for User Story 1 (Run AFTER T010 implementation)

- [ ] T008-code [P] [US1] **Write Unit Test Code**: Write `test_generator.py` verifying that generated variance matches injected $\tau^2$ within Monte Carlo error. **Use a sufficient number of replicates for this unit test to ensure statistical stability.** **Verify output artifact `data/results/test_variance_check.json` contains mean variance within 0.01 of target**. **DEPENDS ON: T010 (Implementation).**
- [ ] T008-run [P] [US1] **Run Unit Test**: Execute `pytest tests/unit/test_generator.py::test_variance_match` to generate the artifact. **Verify `data/results/test_variance_check.json` exists and confirms mean variance error <= 0.01**.
- [ ] T009 [P] [US1] Unit test `test_generator.py` verifying that $\tau^2=0$ produces zero between-study variance (homogeneity). **Use a sufficient number of replicates to ensure statistical stability.** **Verify output artifact `data/results/test_homogeneity_check.json` confirms zero variance**. **DEPENDS ON: T010 (Implementation).**

### Execution for User Story 1

- [ ] T014a [US1] **Fail-Fast Performance Check**: Run `code/simulation/generator.py` with a small subset (e.g., 50 replicates) across all 5 levels. **Measure RAM usage and execution time.** **Verify the process completes within 10 minutes and RAM usage < 2GB. ** **If this fails, halt and optimize T010 before proceeding.** **DEPENDS ON: T010 completion.**
- [ ] T014b [US1] **Execute Primary Sweep**: Run `code/simulation/generator.py` with the full set of heterogeneity levels $\{0, 0.1, 0.5, 1.0, 2.0\}$ and 500 replicates each (Total: 2500 replicates). **Output: `data/results/simulation_raw.json` containing all 2,500 replicates.** **Verify file size and record count == 2500. ** **[FR-001, SC-004]** **DEPENDS ON: T010 completion, T014a completion.**

**Checkpoint**: Simulation engine generates valid, reproducible datasets with known ground truths.

---

## Phase 4: User Story 2 - Estimator Application and Metric Calculation (Priority: P2)

**Goal**: Apply Fixed-Effects, DL, and REML estimators to simulated data and calculate bias/coverage.

**Independent Test**: Process a pre-generated small set of simulated datasets; verify output includes pooled estimate, confidence interval, and coverage flag for true effect.

### Implementation for User Story 2

- [ ] T011a [US2] **Add N_studies Column**: Implement logic in `code/analysis/metrics.py` to add `N_studies` column to output. **[FR-001]**
- [ ] T011b [US2] **Implement Reliability Flag**: Implement logic in `code/analysis/metrics.py` to set `reliability_flag` (boolean) to `False` if `N_studies < 5`. **Explicit threshold: N_studies < 5.** **[Edge Case: Small Study Effects]**
- [ ] T011c [US2] **Implement Exclusion Logic**: Implement logic in `code/analysis/metrics.py` to filter out replicates where `reliability_flag` is `False` (N_studies < 5) before calculating aggregated bias and coverage. **Ensure T019 and T028 depend on this filtering step.** **[Edge Case: Small Study Effects] [SC-002]** **DEPENDS ON: T011b.**
- [ ] T017 [US2] Implement `code/simulation/estimators.py` with Fixed-Effects, DerSimonian-Laird (DL), and REML estimators (CPU-tractable, no CUDA). **Must calculate and output $I^2$ and $Q$ statistics per replicate**. **Output must conform to `contracts/estimation_result.schema.yaml`**.
- [ ] T018 [US2] Implement REML convergence failure logic in `estimators.py`: log event, impute minimal positive variance or skip, record count. **Write failures to `data/results/reml_failures.json` with count.** **[FR-006]**
- [ ] T019 [US2] Implement `code/analysis/metrics.py` to calculate bias (`pooled - true_effect`) and 95% CI coverage for each replicate. **CRITICAL**: `true_effect` MUST be read from the `injected_true_effect` column in the input JSON (from T010). **If `injected_true_effect` is missing, raise `ValueError`.** **Do not reference research.md.** **Add a verification step to confirm `injected_true_effect` is consistently used across all bias calculations.** **DEPENDS ON: T011c.**
- [ ] T020 [US2] **Implement Exact Binomial Test Logic**: Implement logic in `code/analysis/stats.py` to prepare the Exact Binomial Test for coverage deviation. **Read `nominal_confidence_level` from `code/config.yaml` (defined in T006b) and use it as the expected success probability `p` in the Exact Binomial Test.** **Use the Exact Binomial Test (scipy.stats.binom_test) with `p` set to the `nominal_confidence_level` (e.g., 0.95).** **Apply Bonferroni correction (alpha = 0.05/5 = 0.01) to the significance threshold for the test decision. ** **This task implements the function, not the execution loop.** **DEPENDS ON: T010, T011a, T011b, T011c, T024, T026.**
- [ ] T021 [US2] Output results to `data/results/estimation_results.csv` conforming to `contracts/estimation_result.schema.yaml` (including `I^2` and `reliability_flag` fields)

### Tests for User Story 2 (Run AFTER Implementation)

- [ ] T015 [P] [US2] Unit test `test_estimators.py` verifying Fixed-Effects, DL, and REML against standard normal data cases. **Assertion**: Pooled estimate within 0.001 of expected value; CI bounds correct. **DEPENDS ON: T017.**
- [ ] T016 [P] [US2] Unit test `test_estimators.py` verifying REML convergence failure handling (negative variance -> fallback/skip). **Assertion**: Failure logged to `reml_failures.json` with count; no crash. **DEPENDS ON: T018.**
- [ ] T016b [P] [US2] Unit test `test_estimators.py` verifying that Fixed-Effects converges when $\tau^2=0$ and that bias calculation handles excluded $N<5$ studies correctly. **Assertion**: Bias calculated correctly; $N<5$ studies flagged. **DEPENDS ON: T011b, T011c.**
- [ ] T020b [P] [US2] Unit test `test_stats.py` verifying that bias metrics are correctly calculated for excluded $N<5$ studies from T011c. **Assertion**: Bias metric matches expected value for excluded set. **DEPENDS ON: T011c.**

**Checkpoint**: Estimators applied correctly; bias and coverage metrics calculated for all replicates.

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Aggregate results, perform statistical tests (Binomial, Kruskal-Wallis), and generate visualizations.

**Independent Test**: Run analysis script on pre-computed CSV; verify summary table of coverage rates and PNG plot of coverage vs. $\tau^2$.

### Sensitivity Sweep Tasks (Part of US3)

- [ ] T034a [US3] **Sensitivity Sweep CLI**: Add CLI arguments to `code/main.py` to support a secondary sensitivity sweep with levels $\{0.05, 0.1, 0.5\}$ and other standard significance thresholds. **Rationale**: These levels target the low-to-moderate transition zone (SC-004) to detect non-linearities near the homogeneity threshold, distinct from the primary sweep. **[SC-004]**
- [ ] T034d [US3] **Execute Sensitivity Sweep**: Run `code/simulation/generator.py` with levels $\{0.05, 0.1, 0.5\}$ and 500 replicates each. **Output: `data/results/sensitivity_sweep.csv`.** **DEPENDS ON: T004c completion, T010 completion.** **[SC-004]**
- [ ] T034c [US3] **Sensitivity Sweep Verification**: Unit test `test_stats.py` or `test_pipeline.py` verifying that the sensitivity sweep generates multiple levels x 1500 replicates and outputs `sensitivity_sweep.csv` with valid data conforming to `aggregated_metric.schema.yaml`. **Verify output artifact `data/results/sensitivity_sweep.csv` exists and has record count == 1500 and correct structure.** **[SC-004]**

### Implementation for User Story 3

- [ ] T024 [US3] Implement `code/analysis/stats.py` with exact binomial test for coverage deviation (FR-004)
- [ ] T025 [US3] Implement `code/analysis/stats.py` with Shapiro-Wilk test for normality (FR-008)
- [ ] T026 [US3] Implement `code/analysis/stats.py` with Bonferroni correction for multiple hypothesis tests (FR-007)
- [ ] T020b [US2] **Execute Exact Binomial Test Loop**: Execute the Exact Binomial Test logic (from T020) across **ALL 5 heterogeneity levels** ($\tau^2 \in \{0, 0.1, 0.5, 1.0, 2.0\}$). **Aggregate results into a summary table.** **Apply Bonferroni correction (alpha = 0.05/5 = 0.01) to the significance threshold for the test decision. ** **Output results to `data/results/coverage_test_results.csv`.** **DEPENDS ON: T020, T010, T021.**
- [ ] T037 [US3] Implement conditional branching logic in `code/analysis/stats.py` to select Kruskal-Wallis if Shapiro-Wilk $p < 0.05$, else ANOVA (FR-008). **Integrate logic from T025 (Shapiro-Wilk) and T026 (Bonferroni) into this branching flow.** **Apply Bonferroni correction (alpha = 0.05/5 = 0.01) to the significance threshold (alpha) before interpreting the test result.** **DEPENDS ON: T025, T026.**
- [ ] T027 [US3] Implement `code/visualization/plots.py` to generate PNG plots: Coverage vs. $\tau^2$ and Mean Bias vs. $\tau^2$ (FR-005). **Ensure plots utilize data from `estimation_results.csv` produced by T021. The x-axis must be the injected $\tau^2$ value. The y-axes must be coverage probability and mean bias. Do NOT plot $I^2$ as the primary metric; $I^2$ data from T021 may be used for context only.** **Include metadata or links within the generated report to demonstrate traceability to source data and code blocks.**
- [ ] T028 [US3] **Generate Report**: Implement `code/reporting/report_gen.py` to aggregate metrics, perform tests, and generate `data/results/report.md`. **Must include sensitivity sweep data from T034d.** **Must read `reml_failures.json` from T018 and include failure counts.** **Must include explicit "associational" labeling (SC-005).** **Must read coverage results from T020b.** **DEPENDS ON: T034d completion, T021 completion, T018 completion, T011c completion, T020b completion.**
- [ ] T029 [US3] Ensure `report_gen.py` explicitly labels results as "associational" and avoids causal claims (SC-005)
- [ ] T030 [US3] Validate final report content against `contracts/aggregated_metric.schema.yaml`

### Tests for User Story 3 (Run AFTER Implementation)

- [ ] T022 [P] [US3] Unit test `test_stats.py` verifying exact binomial test calculation against known proportions. **Assertion**: p-value matches expected value for given proportion. **DEPENDS ON: T024.**
- [ ] T023 [P] [US3] Unit test `test_stats.py` verifying Bonferroni correction application ($\alpha = 0.05/5$). **Assertion**: Corrected alpha is 0.01. **DEPENDS ON: T026.**
- [ ] T023_test_conditional_logic [P] [US3] Unit test `test_stats.py` verifying the conditional branching logic: explicitly test that Shapiro-Wilk $p < 0.05$ triggers Kruskal-Wallis, and $p \ge 0.05$ triggers ANOVA. **DEPENDS ON: T037.**
- [ ] T029b [P] [US3] **Report Framing Validation**: Unit test `test_reporting.py` verifying that the generated `report.md` contains the required "associational" label and validates framing against the contract. **Assertion**: "associational" label present; no causal claims. **DEPENDS ON: T028.**

**Checkpoint**: Statistical analysis complete; visualizations generated; report framed correctly.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T014 [P] [US1] **Full Scale Performance Test**: Run `generator.py` for the full set (5 levels $\times$ 500 replicates = 2,500 total). Verify the process completes within 360 minutes (6 hours) and RAM usage < 7GB on CPU-only runner. [NO UNRESOLVED CLAIMS] **Use `memory_profiler` (mprof run) to measure and record RAM usage.** **Record start/end timestamps in `data/results/simulation.log` and verify duration < 21600 seconds.** Verify integrity of `data/results/simulation_raw.json` (records). **This is an Integration/Performance Benchmark, not a Unit Test. Run after T010-T013 implementation and T014a completion.**
- [ ] T031 [P] Run full integration test `tests/integration/test_pipeline.py` on a fresh runner to verify end-to-end flow. **NOTE: The core integration logic can be validated against a small synthetic dataset first. The final validation run depends on T014 and T034 completion.**
- [ ] T032 [P] Update `docs/quickstart.md` with instructions to run the simulation engine locally
- [ ] T033 [P] Verify `requirements.txt` contains only CPU-tractable dependencies (no `torch[cuda]`, `bitsandbytes`, etc.)
- [ ] T035 [P] Update `state/` with content hashes of `data/results/` artifacts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes Data Fetch (T040), Synthetic Base Fallback (T040b-gen/T040b-adapt/T040b-doc/T041), and Documentation (T041).**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (needs simulated data to estimate)
- **User Story 3 (P3)**: Depends on US2 (needs estimation results to analyze)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Generators before Estimators
- Estimators before Metrics/Analysis
- Core implementation before Visualization/Reporting
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) EXCEPT T041 which depends on T040/T040b-gen.
- Tests for a user story marked [P] can run in parallel
- Different modules (Generator vs Estimator logic) can be developed in parallel once interfaces are defined

---

## Parallel Example: User Story 1

```bash
# Launch implementation first:
Task: "Implement generator.py for perturbation logic (T010)"

# Then launch tests:
Task: "Unit test test_generator.py verifying variance match (T008-code)"
Task: "Unit test test_generator.py verifying homogeneity (T009)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (Including T040/T040b-gen/T040b-adapt/T040b-doc/T041 Data Fetch/Fallback)
3. Complete Phase 3: User Story 1 (Simulation)
4. **STOP and VALIDATE**: Run simulation with small seed, verify JSON output and variance match.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Simulation) → Test independently → MVP Data Generation
3. Add User Story 2 (Estimation) → Test independently → MVP Metrics
4. Add User Story 3 (Analysis) → Test independently → MVP Report
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Simulation Engine)
 - Developer B: User Story 2 (Estimators & Metrics)
 - Developer C: User Story 3 (Stats & Reporting)
3. Stories complete and integrate via `main.py`.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: All simulation tasks must run on CPU-only (cores, 7GB RAM) within 6 hours. No GPU/CUDA dependencies allowed.
- **CRITICAL**: Data must be real (Cochrane) or verified synthetic base. No fabrication of input data. T040/T040b-gen/T040b-adapt/T040c ensures this by mandating a fetch step with a verified synthetic fallback path and parameter adaptation.
- **CRITICAL**: REML convergence failures must be handled gracefully (log/skip) to ensure full pipeline completion.
- **CRITICAL**: T010 must implement a loop for ≥500 replicates per level and verify the count.
- **CRITICAL**: T037 must implement conditional branching for statistical test selection AND apply Bonferroni correction to the alpha threshold.
- **CRITICAL**: T038 (Performance) is now T014 and moved to Phase 6.
- **CRITICAL**: T034 (Sensitivity Sweep) is a core success criterion, not optional polish, and is now in Phase 5.
- **CRITICAL**: T039 (I^2) is now integrated into T017 to satisfy schema requirements and resolve ordering conflicts.
- **CRITICAL**: T041 ensures traceability of the base dataset to satisfy Constitution II.
- **CRITICAL**: T014 explicitly verifies the full 2,500 replicate generation loop and performance constraints as an integration test.
- **CRITICAL**: T040b-gen provides the necessary fallback path for data unavailability.
- **CRITICAL**: T040c ensures parameter adaptation for real data.
- **CRITICAL**: T040b-adapt ensures parameter adaptation for synthetic data.
- **CRITICAL**: T034c and T029b ensure verification of sensitivity sweep and report framing.
- **CRITICAL**: T020 reads nominal_confidence_level from config.yaml (T006b) as 'p' and uses Exact Binomial Test with Bonferroni-corrected alpha (0.01) as threshold for ALL levels (via T020b).
- **CRITICAL**: T019 explicitly reads `true_effect` from `injected_true_effect` column and raises ValueError if missing.
- **CRITICAL**: T011 generates the `reliability_flag` in the metrics output.
- **CRITICAL**: T034a, T034b, T034c split generation and verification of the sensitivity sweep.
- **CRITICAL**: T004 includes `reliability_flag` and `I^2` as required fields.
- **CRITICAL**: T008 uses 100 replicates for verification and 0.01 error margin.
- **CRITICAL**: T040/T040b/T040c treat synthetic base as a valid co-equal path with adaptation.
- **CRITICAL**: T014 uses `memory_profiler` for RAM verification.
- **CRITICAL**: T014b executes the primary sweep (2,500 replicates) and verifies count == 2500.
- **CRITICAL**: T034d executes the sensitivity sweep.
- **CRITICAL**: T040b-gen writes parameters to config.yaml, cites Jackson et al. (2010) with mu=0.0, sigma=1.0, seed=42, and updates research.md.
- **CRITICAL**: T040b-doc verifies documentation via Python script.
- **CRITICAL**: T011a/b/c split logic for N_studies, reliability_flag, and exclusion.
- **CRITICAL**: T018 writes `reml_failures.json`.
- **CRITICAL**: T020b uses `scipy.stats.binom_test` with p=nominal_confidence_level and alpha=0.01 for all levels.
- **CRITICAL**: T015, T016, T016b, T020b, T022, T023, T029b include concrete assertion logic.
- **CRITICAL**: T014a is the fail-fast performance check in Phase 3.
- **CRITICAL**: T037 depends on T025 and T026.
- **CRITICAL**: T020b executes the loop for ALL 5 levels.
- **CRITICAL**: T027 plots injected $\tau^2$ vs coverage/bias.
- **CRITICAL**: T011c explicitly excludes N<5 studies from aggregation.