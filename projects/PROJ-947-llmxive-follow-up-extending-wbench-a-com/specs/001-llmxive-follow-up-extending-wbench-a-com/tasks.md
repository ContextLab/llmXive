# Tasks: llmXive Follow-up: Extending WBench with Sequence Complexity Analysis

**Input**: Design documents from `/specs/001-llmxive-wbench-entropy/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/`, `results/` at repository root
- Paths shown below assume single project structure as defined in `plan.md`

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

- [ ] T001a [P] Create `code/`, `tests/`, `data/`, `results/` directory structure at repository root
- [X] T001b [P] Create `data/raw/`, `data/processed/`, `data/checksums.json` placeholder
- [ ] T001c [P] Create `tests/unit/`, `tests/integration/`, `tests/contract/` directory structure
- [X] T002a [P] Create `code/requirements.txt` with pinned versions (datasets, pandas, networkx, scipy, scikit-learn, torch, transformers, opencv-python-headless)
- [X] T002b [P] Create virtualenv script and instructions in `code/README.md`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup data directory structure: `data/raw/`, `data/processed/`, `data/checksums.json` and verify existence via `ls`
- [ ] T005 [P] Implement environment configuration management (seeds, model paths, limits) in `code/config.py`
- [X] T006 [P] Create base logging infrastructure with structured JSON output in `code/utils/logging.py`
- [X] T007 Implement `code/data/verify_checksums.py` to validate downloaded artifacts against `data/checksums.json`
- [X] T008 [P] Setup error handling wrappers in `code/utils/errors.py`: implement `fail_loudly()` and `skip_on_error()` functions that raise exceptions or skip with logs, explicitly forbidding synthetic fallbacks

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Annotate Sequence Complexity (Priority: P1) 🎯 MVP

**Goal**: Programmatically generate low, medium, and high-entropy variants of WBench interaction sequences and compute "Sequence Complexity Scores" to establish the independent predictor variable.

**Independent Test**: Run the data processing pipeline on a subset of WBench cases; verify output CSV contains valid entropy values within the normalized range, dependency depth integers, and that variants show statistically distinct complexity scores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These are stub tests. They will fail on import until the implementation code exists. They are listed first to enforce TDD mindset but must be run AFTER implementation to be meaningful.

- [X] T009 [P] [US1] Unit test for Shannon entropy calculation in `tests/unit/entropy/test_scorer.py` (stub: asserts function exists)
- [X] T010 [P] [US1] Unit test for dependency graph depth calculation in `tests/unit/entropy/test_scorer.py` (stub: asserts function exists)
- [X] T011 [P] [US1] Integration test for variant generation (10 cases) in `tests/integration/entropy/test_generator.py` (stub: asserts pipeline exists)

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data/download_wbench.py` to fetch WBench dataset from verified HuggingFace source (no synthetic fallback)
- [ ] T013 [US1] Implement `code/entropy/generator.py` for token-reweighting and resampling algorithm to create Low (<0.3), Medium (0.3-0.7), and High (>0.7) entropy variants. **Constraint**: Per Plan: Stratified Sub-sampling (N=50 cases). **Logic**: Converge on targets within ≤20 iterations; if convergence fails, raise `ConvergenceError`. **Output**: `data/processed/variants.csv` (columns: case_id, variant_type, entropy_score) and `data/processed/generation_logs.json` (iteration counts). **Verify**: Unit test asserts `ConvergenceError` is raised if max_iter exceeded.
- [ ] T014 [US1] Implement `code/entropy/validator.py` for Task Validity Validator (Action Chain Check). **Input**: `data/processed/variants.csv`. **Algorithm**: Verify action chains are physically plausible. **Output**: `data/processed/validity_flags.csv` (columns: case_id, variant_type, is_valid). **Verify**: Unit test with known broken chain returns False.
- [ ] T015 [US1] Implement `code/entropy/scorer.py` to compute Sequence Complexity Score. **Constraint**: MUST derive graph depth from the *original semantic intent* of the base case, NOT the generated text (to avoid circular correlation per FR-002/Constitution VI). **Output**: `data/processed/complexity_scores.csv` with columns [case_id, variant_type, entropy, depth, complexity_score]. **Verify**: Verify depth is integer >= 1 and matches manual trace for 1 sample.
- [X] T016 [US1] Create pipeline script `code/entropy/run_pipeline.py` to generate variants and scores for the stratified sample (N=50 cases)
- [ ] T017 [US1] Implement pre-run validation logic in `code/entropy/run_pipeline.py` to abort if variance of complexity scores < 0.05 (per SC-005)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute CPU-Optimized Inference on Stratified Data (Priority: P2)

**Goal**: Run inference on publicly available, CPU-optimized world models using the stratified sequences to collect visual output data for fidelity metrics.

**Independent Test**: Execute inference script on a single test case with a recent model; process must complete within 60 mins, produce MP4, and log RAM usage < 6.5 GB.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for RAM profiling utility in `tests/unit/inference/test_runner.py`
- [ ] T019 [P] [US2] Integration test for single-case inference with a CPU-compatible model in `tests/integration/inference/test_inference.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/inference/models.py` to register and validate CPU-only models (<7GB RAM) from HuggingFace
- [ ] T021 [US2] Implement `code/inference/runner.py` with pre-flight RAM profiling; skip models exceeding GB limit. **Logic**: If video generation fails or exceeds RAM, use pre-validated CPU-compatible model metrics (proxy) or skip; DO NOT generate synthetic data. **Output**: Log error/skip. If proxy used, append row to `data/processed/inference_results.csv` with `status='proxy'` and NaN scores. **Verify**: Unit test: mock OOM error; assert CSV row exists with NaN scores.
- [ ] T022 [US2] Implement logic to handle inference failures. **Output**: Append row to `data/processed/inference_results.csv` with `status='failed'`, `error_msg` column, and NaN scores. **Verify**: Unit test: mock OOM error; assert CSV row exists with NaN scores.
- [ ] T023 [US2] Create pipeline script `code/inference/run_inference.py` to process a set of cases × 3 variants × N models
- [ ] T024 [US2] Ensure at least 3 valid models are loaded before proceeding; raise error if fewer are available

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlate Complexity with Fidelity Degradation (Priority: P3)

**Goal**: Compute ANOVA with trend analysis and Bonferroni correction to identify the "tipping point" of model failure and the non-linear degradation pattern.

**Independent Test**: Feed synthetic dataset with known negative correlation into analysis script; verify output trend shows correct direction and significance within ±0.05 tolerance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for ANOVA and trend analysis in `tests/unit/analysis/test_correlation.py`
- [ ] T026 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/analysis/test_correction.py`

### Implementation for User Story 3

- [ ] T027a [US3] Implement `code/metrics/baseline.py` to generate a random-noise video and calculate the motion artifact baseline score. **Output**: `data/processed/baseline_scores.json` with the baseline value. **Verify**: Unit test with known noise input.
- [ ] T027b [US3] Implement `code/metrics/wbench_suite.py` to calculate physics compliance and temporal consistency scores. **Requirement**: MUST subtract the motion artifact baseline (from T027a) from raw scores (per FR-004). **Output**: `data/processed/fidelity_metrics.csv` with columns [case_id, physics_score, consistency_score, baseline_subtracted]. **Verify**: Unit test with known baseline subtraction logic.
- [ ] T028 [US3] Implement `code/analysis/correlation.py` to perform **ANOVA with trend analysis** (per Plan & FR-005). **Constraint**: Do NOT implement Pearson correlation for discrete groups. **Output**: Intermediate stats CSV with F-statistic, p-value, and trend direction. **Verify**: Unit test: assert trend direction matches input data.
- [ ] T029 [US3] Implement `code/analysis/correction.py` for Bonferroni correction across N models (controlling family-wise error rate). **Requirement**: MUST integrate corrected p-values into the final output CSV. **Verify**: Unit test: assert corrected p-value < 0.05 triggers significance flag (SC-003).
- [ ] T030 [US3] Create pipeline script `code/analysis/run_analysis.py` to merge results, compute statistics, and output final CSVs
- [ ] T031a [US3] Implement logic to detect and report significant trends. **Output**: Append summary row to `results/analysis_summary.csv` with columns `model_id`, `trend_type`, `p_value_corrected`. **Verify**: Assert p-value < 0.05 triggers `trend_type='significant'`.
- [ ] T031b [US3] Implement Chow test logic for breakpoint detection (optional per US-3). **Output**: If breakpoint detected with p < 0.05, append to `results/analysis_summary.csv`. **Verify**: Unit test with synthetic breakpoint data.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Generate content hashes for all data artifacts and update `data/checksums.json`
- [ ] T033 Run full integration test suite on stratified sample (cases)
- [ ] T034 Update `code/requirements.txt` with exact versions used in successful run
- [ ] T035a [US3] Generate `results/summary.csv` with correlation coefficients, p-values, and trend data
- [ ] T035b [US3] Generate `results/trend_plot.png` visualizing the degradation curves
- [ ] T036 [P] Documentation updates: `quickstart.md` with execution instructions and `contracts/` for data schemas

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1)**: Must complete first to generate the input data (variants/scores) for US2 and US3
 - **US2 (P2)**: Depends on US1 (needs generated sequences)
 - **US3 (P3)**: Depends on US1 (scores) and US2 (video/fidelity results)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires generated sequence variants)
- **User Story 3 (P3)**: Depends on US1 (complexity scores) and US2 (fidelity metrics)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (as stubs)
- Data download (T012) must precede generation (T013)
- Generation (T013) must precede validation (T014)
- Validation (T014) must precede scoring (T015)
- Inference (T023) must precede metrics calculation (T027b)
- Metrics (T027b) must precede correlation analysis (T028)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Once Foundational phase completes, US1 can start immediately
- US2 and US3 must wait for upstream data (US1 for US2, US1+US2 for US3)
- All tests for a user story marked [P] can run in parallel (as stubs)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for Shannon entropy calculation in tests/unit/entropy/test_scorer.py"
Task: "Unit test for dependency graph depth calculation in tests/unit/entropy/test_scorer.py"

# Launch generation and scoring in sequence (data dependency):
Task: "Implement generator.py for token-reweighting"
Task: "Implement scorer.py for Sequence Complexity Score"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Generation & Scoring)
4. **STOP and VALIDATE**: Verify generated variants have distinct entropy scores and pass validity checks
5. Deploy/demo data pipeline if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! Data ready)
3. Add User Story 2 → Test independently → Deploy/Demo (Inference ready)
4. Add User Story 3 → Test independently → Deploy/Demo (Analysis ready)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Inference Engine) - *Wait for US1 data*
 - Developer C: User Story 3 (Analysis) - *Wait for US1+US2 data*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: No synthetic data generation for results. All data must be from real WBench source or real model inference.
- **Critical Constraint**: Inference must fail loudly if model exceeds RAM limits; do not fallback to synthetic data.
- **Critical Constraint**: Sequence variants must be validated for physical plausibility before scoring.
- **Critical Constraint**: Causal depth MUST be derived from original intent, NOT generated text.
- **Critical Constraint**: Pearson correlation is NOT to be implemented for discrete stratified groups; use ANOVA with trend analysis.