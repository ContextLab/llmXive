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
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing `numpy`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `pyyaml`, `pytest`
- [X] T003 [P] Configure linting (flake8/black) and pre-commit hooks in `code/`
- [X] T041 [P] **Document Data Source**: Create `data/raw/README.md` and update `research.md` to explicitly document the source URL, accession ID, and citation for the base dataset used in T040 (or T040b), satisfying Constitution Principle II (Verified Accuracy). **Execute this task ONLY AFTER T040 or T040b has successfully produced a file in `data/raw/`.** <!-- FAILED: unspecified -->

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data ingestion, and contracts that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Data must be fetched and verified before simulation.

- [ ] T004 [P] Create JSON schemas for `SimulatedDataset`, `EstimationResult`, and `AggregatedMetric` in `specs/001-assess-heterogeneity-impact/contracts/` with filenames `simulated_dataset.schema.yaml`, `estimation_result.schema.yaml`, and `aggregated_metric.schema.yaml`. **Must include `I^2` as a required field in `EstimationResult`**. **NOTE: This schema is the 'contract' that blocks T010/T017/T021; ensure it is finalized before coding generators.**
- [X] T005 [P] Implement `code/simulation/__init__.py` and `code/analysis/__init__.py` to expose core classes
- [X] T006 Create `code/main.py` entry point that orchestrates the pipeline (generation -> estimation -> analysis -> reporting) with CLI argument support for seeds and levels
- [X] T007 Setup logging infrastructure in `code/utils/logging.py` to capture convergence failures and simulation progress to `data/results/simulation.log`
- [X] T039 [P] **Calculate I^2**: Implement calculation of $I^2$ statistic in `code/simulation/estimators.py` (integrated with T017/T018 logic) and ensure it is included in the `EstimationResult` output. **This task MUST be completed before T017 and T021 to satisfy the schema requirement for `I^2` in `EstimationResult`.**
- [ ] T040 [P] **Fetch Real Data**: Execute a script to download a verified Cochrane meta-analysis dataset into `data/raw/cochrane_base.csv`. **Source**: Use the `cochrane-sample-data` Python package (if available) or fetch from `. **CRITICAL**: The script MUST fail loudly (raise an exception) if the fetch fails. Do NOT implement a silent fallback. If the fetch fails, the pipeline must halt, and T040b must be manually triggered as the explicit fallback path. <!-- FAILED: unspecified -->
- [ ] T040b [P] **Generate Verified Synthetic Base**: Execute this script to generate a synthetic base dataset using parameters explicitly cited from literature (e.g., Jackson et al., 2010) **ONLY IF T040 fails**. Save as `data/raw/cochrane_base_synthetic.csv`. Update `data/raw/README.md` and `research.md` to document this as the fallback source.

**Checkpoint**: Foundation ready - data fetched (or synthetic base generated), schemas defined, user story implementation can now begin.

---

## Phase 3: User Story 1 - Simulation Engine Execution (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic meta-analysis datasets with controlled $\tau^2$ levels based on Cochrane data structures.

**Independent Test**: Run `code/simulation/generator.py` with $\tau^ \in \{, \}$ and multiple replicates; verify output JSON contains injected $\tau^2$ and generated effect sizes; process exits 0 within 10 mins.

### Tests for User Story 1

- [ ] T008 [P] [US1] Unit test `test_generator.py` verifying that generated variance matches injected $\tau^2$ within Monte Carlo error. **Use a sufficient number of replicates for this unit test**. **Verify output artifact `data/results/test_variance_check.json` contains mean variance within 0.01 of target**.
- [X] T009 [P] [US1] Unit test `test_generator.py` verifying that $\tau^2=0$ produces zero between-study variance (homogeneity). **Verify output artifact `data/results/test_homogeneity_check.json` confirms zero variance**.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/simulation/generator.py` to load base Cochrane data (from `data/raw/`, verified in T040) and implement a loop generating ≥500 replicates per level for heterogeneity levels $\{0, 0.1, 0.5, 1.0, 2.0\}$. **Ensure output conforms to `contracts/simulated_dataset.schema.yaml`**. **Output must include `injected_true_effect` and `injected_tau2` columns.**
- [ ] T011 [US1] Implement logic in `generator.py` to handle $N < 5$ studies by flagging/excluding replicates (Edge Case: Small Study Effects). **Do not implement the final `reliability_flag` output here; that is T011b.**
- [ ] T012 [US1] Implement logic in `generator.py` to handle $\tau^2=0$ without numerical instability (Edge Case: Zero Variance)
- [ ] T013 [US1] Ensure `generator.py` outputs `data/results/simulation_raw.json` conforming to `contracts/simulated_dataset.schema.yaml`

**Checkpoint**: Simulation engine generates valid, reproducible datasets with known ground truths.

---

## Phase 4: User Story 2 - Estimator Application and Metric Calculation (Priority: P2)

**Goal**: Apply Fixed-Effects, DL, and REML estimators to simulated data and calculate bias/coverage.

**Independent Test**: Process a pre-generated small set of simulated datasets; verify output includes pooled estimate, confidence interval, and coverage flag for true effect.

### Tests for User Story 2

- [ ] T015 [P] [US2] Unit test `test_estimators.py` verifying Fixed-Effects, DL, and REML against standard normal data cases
- [ ] T016 [P] [US2] Unit test `test_estimators.py` verifying REML convergence failure handling (negative variance -> fallback/skip)
- [ ] T016_test_edge_cases_estimator [P] [US2] Unit test `test_estimators.py` verifying that Fixed-Effects converges when $\tau^2=0$ and that bias calculation handles excluded $N<5$ studies correctly.
- [ ] T020_test_edge_cases_metrics [P] [US2] Unit test `test_stats.py` verifying that bias metrics are correctly calculated for excluded $N<5$ studies from T011.

### Implementation for User Story 2

- [ ] T017 [US2] Implement `code/simulation/estimators.py` with Fixed-Effects, DerSimonian-Laird (DL), and REML estimators (CPU-tractable, no CUDA)
- [ ] T018 [US2] Implement REML convergence failure logic in `estimators.py`: log event, impute minimal positive variance or skip, record count
- [ ] T019 [US2] Implement `code/analysis/metrics.py` to calculate bias (`pooled - true_effect`) and 95% CI coverage for each replicate. **CRITICAL**: `true_effect` MUST be read from the `injected_true_effect` column in the input JSON (from T010), NOT from an estimated pooled value.
- [ ] T011b [US2] **Generate Reliability Flag**: Implement logic in `code/analysis/metrics.py` to set a `reliability_flag` column in the output metrics for any replicate where $N < 5$ (as flagged by T011). **This satisfies the spec's requirement to 'explicitly flag' unreliability in the output metrics.**
- [ ] T020 [US2] Implement logic in `metrics.py` to verify coverage at $\tau^2=0$ is statistically indistinguishable from the nominal level **hardcoded as 0.95 (95% confidence level)** (within $\pm 1.5\%$, alpha=0.05, CI=95%). **Do not reference research.md.**
- [ ] T021 [US2] Output results to `data/results/estimation_results.csv` conforming to `contracts/estimation_result.schema.yaml` (including `I^2` and `reliability_flag` fields)
- [ ] T034a [US2] **Sensitivity Sweep Generation**: Implement execution of the sensitivity sweep in `main.py` for levels $\{0.05, 0.1, 0.5\}$. **Output `data/results/sensitivity_sweep.csv` conforming to `contracts/aggregated_metric.schema.yaml`.** **This task MUST run AFTER T021 and BEFORE T028.**
- [ ] T034b [US2] **Sensitivity Sweep Verification**: Unit test `test_stats.py` or `test_pipeline.py` verifying that the sensitivity sweep generates multiple levels x a sufficient number of replicates and outputs `sensitivity_sweep.csv` with valid data conforming to `aggregated_metric.schema.yaml`. **Verify output artifact `data/results/sensitivity_sweep.csv` exists and has correct structure.**

**Checkpoint**: Estimators applied correctly; bias and coverage metrics calculated for all replicates; sensitivity sweep data generated.

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Aggregate results, perform statistical tests (Binomial, Kruskal-Wallis), and generate visualizations.

**Independent Test**: Run analysis script on pre-computed CSV; verify summary table of coverage rates and PNG plot of coverage vs. $\tau^2$.

### Tests for User Story 3

- [ ] T022 [P] [US3] Unit test `test_stats.py` verifying exact binomial test calculation against known proportions
- [ ] T023 [P] [US3] Unit test `test_stats.py` verifying Bonferroni correction application ($\alpha = 0.05/5$)
- [ ] T023_test_conditional_logic [P] [US3] Unit test `test_stats.py` verifying the conditional branching logic: explicitly test that Shapiro-Wilk $p < 0.05$ triggers Kruskal-Wallis, and $p \ge 0.05$ triggers ANOVA.
- [ ] T029b [P] [US3] **Report Framing Validation**: Unit test `test_reporting.py` verifying that the generated `report.md` contains the required "associational" label and validates framing against the contract.

### Implementation for User Story 3

- [ ] T024 [US3] Implement `code/analysis/stats.py` with exact binomial test for coverage deviation (FR-004)
- [ ] T025 [US3] Implement `code/analysis/stats.py` with Shapiro-Wilk test for normality (FR-008)
- [ ] T026 [US3] Implement `code/analysis/stats.py` with Bonferroni correction for multiple hypothesis tests (FR-007)
- [ ] T037 [US3] Implement conditional branching logic in `code/analysis/stats.py` to select Kruskal-Wallis if Shapiro-Wilk $p < 0.05$, else ANOVA (FR-008)
- [ ] T027 [US3] Implement `code/visualization/plots.py` to generate PNG plots: Coverage vs. $\tau^2$ and Mean Bias vs. $\tau^2$ (FR-005). **Ensure plots utilize $I^2$ data from T039.**
- [ ] T028 [US3] Implement `code/reporting/report_gen.py` to aggregate metrics, perform tests, and generate `data/results/report.md`. **Must include sensitivity sweep data from T034a.**
- [ ] T029 [US3] Ensure `report_gen.py` explicitly labels results as "associational" and avoids causal claims (SC-005)
- [ ] T030 [US3] Validate final report content against `contracts/aggregated_metric.schema.yaml`

**Checkpoint**: Statistical analysis complete; visualizations generated; report framed correctly.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T014 [P] [US1] **Full Scale Performance Test**: Run `generator.py` for the full set (5 levels $\times$ 500 replicates = 2,500 total). Verify the process completes within 360 minutes (6 hours) and RAM usage < 7GB on CPU-only runner. Verify integrity of `data/results/simulation_raw.json` (records). **This is an Integration/Performance Benchmark, not a Unit Test. Run after T010-T013 implementation.**
- [ ] T031 [P] Run full integration test `tests/integration/test_pipeline.py` on a fresh runner to verify end-to-end flow. **NOTE: The core integration logic can be validated against a small synthetic dataset first. The final validation run depends on T014 and T034 completion.**
- [ ] T032 [P] Update `docs/quickstart.md` with instructions to run the simulation engine locally
- [ ] T033 [P] Verify `requirements.txt` contains only CPU-tractable dependencies (no `torch[cuda]`, `bitsandbytes`, etc.)
- [ ] T035 [P] Update `state/` with content hashes of `data/results/` artifacts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes Data Fetch (T040), Synthetic Base Fallback (T040b), and Documentation (T041).**
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Tests for a user story marked [P] can run in parallel
- Different modules (Generator vs Estimator logic) can be developed in parallel once interfaces are defined

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test test_generator.py verifying variance match (T008)"
Task: "Unit test test_generator.py verifying homogeneity (T009)"

# Launch implementation tasks:
Task: "Implement generator.py for perturbation logic (T010)"
Task: "Implement generator.py for edge cases (N<5, tau2=0) (T011, T012)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (Including T040/T040b/T041 Data Fetch/Fallback)
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
- **CRITICAL**: All simulation tasks must run on CPU-only (2 cores, 7GB RAM) within 6 hours. No GPU/CUDA dependencies allowed.
- **CRITICAL**: Data must be real (Cochrane) or verified synthetic base. No fabrication of input data. T040/T040b ensures this by mandating a fetch step with a verified synthetic fallback path.
- **CRITICAL**: REML convergence failures must be handled gracefully (log/skip) to ensure full pipeline completion.
- **CRITICAL**: T010 must implement a loop for ≥500 replicates per level.
- **CRITICAL**: T037 must implement conditional branching for statistical test selection.
- **CRITICAL**: T038 (Performance) is now T014 and moved to Phase 6.
- **CRITICAL**: T034 (Sensitivity Sweep) is a core success criterion, not optional polish, and is now in Phase 4.
- **CRITICAL**: T039 (I^2) is now in Phase 2 to satisfy schema requirements.
- **CRITICAL**: T041 ensures traceability of the base dataset to satisfy Constitution II.
- **CRITICAL**: T014 explicitly verifies the full 2,500 replicate generation loop and performance constraints as an integration test.
- **CRITICAL**: T040b provides the necessary fallback path for data unavailability.
- **CRITICAL**: T034b and T029b ensure verification of sensitivity sweep and report framing.
- **CRITICAL**: T020 uses a hardcoded nominal level of 0.95, removing dependency on `research.md`.
- **CRITICAL**: T019 explicitly reads `true_effect` from `injected_true_effect` column.
- **CRITICAL**: T011b generates the `reliability_flag` in the metrics output.
- **CRITICAL**: T034a and T034b split generation and verification of the sensitivity sweep.