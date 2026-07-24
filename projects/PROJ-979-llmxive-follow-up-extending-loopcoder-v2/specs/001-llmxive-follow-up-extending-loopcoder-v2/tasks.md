# Tasks: llmXive follow-up: extending "LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-loopcoder-v2/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

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

## Model Substitution Note

**CRITICAL**: The spec's `Assumptions` section states `LoopCoder-v2-2B` is available. However, this checkpoint is not available in the current execution environment (HuggingFace/Local). This project substitutes `LoopCoder-v2-2B` with `CodeLlama-1.3b-Instruct` (CPU validation) and `CodeLlama-3b/7b-Instruct` (GPU full analysis). **This is a necessary adaptation to environmental constraints, not a relaxation of the scientific goal.** The methodology (entropy extraction, convergence tracking) remains identical, but specific metrics (e.g., baseline entropy values) must be validated via the pilot study (T008b1) before full execution. The tasks below reflect this re-baselined scope. The core scientific constraints (semantic entropy vs. convergence trajectory) are preserved; only the model weights are adapted to available hardware.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize project directory structure. Execute `code/scripts/run_setup.py` which creates `data/`, `code/`, `paper/`, `state/`, `contracts/` and their subdirectories (`raw`, `processed`, `src`, `tests`, `notebooks`). Script must exit 0 only if all directories exist.

- [X] T002 Initialize Python project with `transformers`, `torch`, `scikit-learn`, `pandas`, `datasets`, `pytest`, `docker` dependencies in `code/requirements.txt`

- [ ] T003a [P] Create `.ruff.toml` configuration file in `code/` with `line-length = 88`, `target-version = "py310"`, and rules `["E", "F", `W`, `I`]` enabled.
- [ ] T003b [P] Create `pyproject.toml` with `[tool.black]` section in `code/` setting `line-length = 88` and `target-version = ['py310']`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Implement `code/src/data_loader.py` function `fetch_datasets()`: Fetch HumanEval and MBPP via `datasets.load_dataset`. Save raw copies to `data/raw/`.
- [X] T004b [P] Implement `code/src/data_loader.py` function `checksum_datasets()`: Compute SHA256 checksums for raw files and record in `data/checksums.txt`.
- [X] T004c [P] Implement `code/src/data_loader.py` function `stratify_data()`: Apply stratified sampling by difficulty (using 'difficulty' column or hashing 'task_id'). Flag strata with <50 samples as 'underpowered' in `data/processed/strata_log.json`.
- [X] T004d [P] Implement `code/src/data_loader.py` function `save_splits()`: Save processed splits to `data/processed/`.
- [ ] T004e [P] Implement `code/src/data_loader.py` function `filter_underpowered()`: Read `data/processed/strata_log.json` and **exclude** all samples belonging to strata flagged as 'underpowered'. Save the filtered dataset to `data/processed/filtered_dataset.json`. **Dependencies: T004c.**
- [X] T005 [P] Create `code/src/entropy.py` stub with function signature for semantic entropy extraction (FR-001). **NOTE: Implementation (T012a-d) depends on T004e.**
- [X] T005d [P] Define FLOPs utility function in `code/src/utils.py`: Implement formula `FLOPs = parameters * sequence_length * k` for baseline calculation (FR-006, SC-002).
- [ ] T005e [P] Implement resource monitoring utility in `code/src/utils.py`: Create `capture_metrics()` using `psutil` and `torch.cuda` (if available) to log runtime, RAM, GPU usage. Save to `data/processed/resource_metrics.json` (SC-005).
- [X] T006 [P] Create `code/src/inference.py` stub with function signature for iterative refinement execution (FR-002). **NOTE: Implementation (T013a-d) depends on T004e and T009.**
- [X] T007 Define `InputProblem` and `ConvergenceTrajectory` dataclasses in `code/src/models.py`
- [X] T008 [P] Setup environment configuration for model paths (CodeLlama-1.3b for CPU, CodeLlama-3b/7b for GPU) in `code/.env.example`
- [ ] T008b1 [P] Run pilot study (N=10). Execute `code/scripts/run_pilot.py` to sample 10 problems, run k=1 inference with CodeLlama-1.3b, and save metrics to `data/processed/pilot_metrics.json`.
- [ ] T008b2 [P] Generate Model Substitution Rationale. Create `paper/model_substitution_rationale.md` based on T008b1 results. **Mandatory before T029.** **Deliverable Schema**: The document MUST contain sections: 1) 'Model Comparison' (LoopCoder-v2-2B vs CodeLlama specs), 2) 'Pilot Metrics' (pass@1, latency from T008b1), 3) 'Feasibility Conclusion' (why substitution is necessary), 4) 'Re-baselining Impact' (how metrics are adjusted). **Dependencies: T008b1.**
- [X] T009 Implement Docker sandbox configuration for code execution safety in `code/Dockerfile` and `code/docker-compose.yml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3a: User Story 1 - Core Correlation Analysis (Data Generation) (Priority: P1) 🎯 MVP

**Goal**: Extract initial semantic entropy and track convergence trajectories to compute Spearman correlation.

**Independent Test**: Run `code/src/entropy.py` and `code/src/inference.py` on a stratified sample (N=50 for CPU validation) to produce `data/processed/entropy_results.csv` and `data/processed/convergence_results.csv`, then verify `code/src/analysis.py` computes a non-error correlation coefficient.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for entropy clustering logic in `code/tests/test_entropy.py`
- [X] T011 [P] [US1] Integration test for end-to-end entropy + convergence pipeline on N=5 sample using mock fixtures in `code/tests/test_analysis.py` (ensure independent of T012/T013 artifacts)

### Implementation for User Story 1 (Data Generation)

- [X] T012a [US1] Implement sampling function in `code/src/entropy.py`: Create `generate_samples(prompt, n=10)` using `model.generate`. **Dependencies: T004e.**
- [X] T012b [US1] Implement clustering function in `code/src/entropy.py`: Create `cluster_by_semantic_equivalence(samples)`. **Primary Logic**: Use `astunparse` (or equivalent) to normalize ASTs of generated code; group by identical AST structure. **Secondary Logic**: If AST parsing fails, execute code in Docker sandbox and group by identical execution output (stdout/stderr + exit code). **Tertiary**: Exact string match. **Output**: JSON cluster ID map `{sample_idx: cluster_id}`. Compute Shannon entropy over cluster probabilities (FR-001). **Dependencies: T012a, T009.**
- [X] T012c [US1] Implement entropy calculation in `code/src/entropy.py`: Compute Shannon entropy over cluster probabilities. Handle undefined entropy (zero entropy) by assigning `entropy=1e-9` or excluding. **Dependencies: T012b.**
- [ ] T012d [US1] Implement exclusion logging and serialization in `code/src/entropy.py`: Create `write_entropy_results(results, path)` to save `data/processed/entropy_results.csv` (columns: `task_id, entropy, cluster_count, excluded_reason`). Log exclusion count/rate to `data/processed/exclusion_log.json` (FR-007). **Dependencies: T012c.**
- [X] T013a [US1] Implement iterative refinement loop in `code/src/inference.py`: Create `run_refinement_loop(prompt, max_k=3)`. **CRITICAL**: For k=1, input is `prompt`. For k>1, input is `prompt + "\n" + prev_output` (where `prev_output` is the output of step k-1). This implements true iterative refinement, not independent runs. **Dependencies: T004e, T009.**
- [X] T013b [US1] Implement sandbox wrapper in `code/src/inference.py`: Execute generated code via Docker sandbox and compare output against 'test' field. **Dependencies: T009.**
- [X] T013c [US1] Implement convergence detector in `code/src/inference.py`: Detect first correct solution. Record non-convergence events (FR-007). **Dependencies: T013a, T013b.**
- [ ] T013d [US1] Implement result logger in `code/src/inference.py`: Create `write_convergence_results(traj, path)` to save `data/processed/convergence_results.csv` (columns: `task_id, k_correct, trajectory_status`). **Dependencies: T013c.**
- [X] T013e [US1] Implement sensitivity inference pass in `code/src/inference.py`: Re-run model for `k=4` on the same dataset to generate trajectory data for sensitivity analysis (SC-004). **Dependencies: T004e, T009.** (Note: T013e is parallel to T012a-d).

**Checkpoint**: At this point, User Story 1 data generation is complete (Core Correlation Data Generated)

---

## Phase 3b: User Story 1 - Analysis (Priority: P1)

**Goal**: Compute correlation and statistical significance.

- [X] T015 [US1] Implement Spearman correlation calculation in `code/src/analysis.py`: Create `compute_correlation(entropy_df, conv_df)` to compute $\rho$ between entropy and convergence step, calculate p-value (FR-003). **Dependencies: T012d, T013d.**
- [ ] T015b [US1] Implement significance flag generation in `code/src/analysis.py`: Create `generate_significance_flag(p_value)` to return `true` if $p < 0.05$ else `false`. Save the result to `data/processed/analysis_summary.json` as a new key `is_significant` (SC-001). **Dependencies: T015.**
- [ ] T016 [US1] Aggregate results. Merge `entropy_results.csv`, `convergence_results.csv`, `exclusion_log.json`, and `is_significant` flag into `data/processed/analysis_summary.json`. **Dependencies: T012d, T013d, T015b.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Core Correlation Data Generated)

---

## Phase 4: User Story 2 - Dynamic Router Simulation (Priority: P2)

**Goal**: Simulate a lightweight dynamic routing strategy using logistic regression to predict optimal loop counts and evaluate FLOPs savings.

**Independent Test**: Train a logistic regression model on US1 data, apply to test set, and verify reports of prediction accuracy vs random baseline and FLOPs savings vs static $k=2$ baseline with statistical significance testing.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for logistic regression training and prediction in `code/tests/test_analysis.py`
- [X] T018 [P] [US2] Statistical test validation for non-inferiority vs static baseline in `code/tests/test_analysis.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement logistic regression router training in `code/src/analysis.py`: Create `train_router(entropy_df, conv_df)`. Target: **optimal loop count** (defined as the minimum k where solution is correct). Use `sklearn.linear_model.LogisticRegression` with `multi_class='multinomial'`. Loss: sparse categorical cross-entropy (FR-004). **Output**: `data/processed/router_model.pkl`, `data/processed/router_metrics.json`. **Dependencies: T012d, T013d.**
- [ ] T020 [US2] Implement router evaluation logic: Compare prediction accuracy against random baseline (predict $k=1$ for all samples). **Perform a paired t-test** using `scipy.stats.ttest_rel` to confirm statistical significance ($p < 0.05$) (FR-006). **Output**: `data/processed/router_accuracy_test.json`. **Dependencies: T019.**
- [ ] T021a [US2] Implement FLOPs estimation and savings calculation: **Use the formula from T005d** (`parameters * sequence_length * k`) to calculate static $k=2$ baseline FLOPs. Compare dynamic router vs static baseline. **Dependencies: T005d, T019.**
- [ ] T021b [US2] Perform non-inferiority test on accuracy (FR-006, SC-002). **Use `scipy.stats.ttest_rel`** (one-sided) to test if dynamic router accuracy is non-inferior to static baseline. **Output**: `data/processed/flops_savings.json`. **Dependencies: T020, T021a.**
- [ ] T022 [US2] Integrate router simulation results into `data/processed/router_results.csv` and update `code/src/analysis.py` report generation. **Dependencies: T021b.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Router Simulation Complete)

---

## Phase 5: User Story 3 - Statistical Robustness & Sensitivity Analysis (Priority: P3)

**Goal**: Ensure findings are robust to multiple comparisons and convergence definition sensitivity.

**Independent Test**: Re-run correlation analysis with Bonferroni/Holm-Bonferroni correction and sweep convergence thresholds ($k \in \{2, 3, 4\}$) to verify stability of correlation coefficients.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for multiple-comparison correction implementation in `code/tests/test_robustness.py`
- [X] T024 [P] [US3] Sensitivity analysis sweep validation in `code/tests/test_robustness.py`

### Implementation for User Story 3

- [ ] T025a [US3] Implement Holm-Bonferroni correction function in `code/src/robustness.py`: Create a function that takes a list of p-values and returns adjusted p-values (FR-005).
- [ ] T025b [US3] Apply multiple-comparison correction in `code/src/robustness.py`: **Group p-values by difficulty strata** (from T004c) but apply Holm-Bonferroni to the **global union** of all p-values to control family-wise error rate across the entire experiment. **Output**: Save results to `data/processed/adjusted_pvalues.json` with schema: `{ "stratum_id": "<id>", "original_p": <float>, "adjusted_p": <float> }` (FR-005, US-003). **Dependencies: T015, T025a, T004c.**
- [ ] T026 [US3] Implement sensitivity analysis loop in `code/src/robustness.py`: **Consume data from T013 (k=2,3) and T013e (k=4)**. Sweep convergence threshold **$k \in \{, 3, 4\}$** and compute variation in $\rho$ (SC-004). Output: `data/processed/sensitivity_sweep.json` (columns: `threshold_k, rho, p_value`). **Dependencies: T013d, T013e.**
- [ ] T027 [US3] Generate robustness report summarizing adjusted p-values and threshold stability in `data/processed/robustness_report.json`. **Dependencies: T025b, T026.**

**Checkpoint**: All user stories should now be independently functional (Robustness Validated)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [ ] T028 [P] Finalize `paper/draft.md` with generated results, ensuring all stats trace to `data/processed/` files (Principle IV)
- [ ] T028b [P] Aggregate computational feasibility metrics. Read `data/processed/resource_metrics.json` and append a "Computational Feasibility" section to `paper/draft.md` (SC-005) containing total runtime, peak RAM, and peak GPU usage. **Dependencies: T005e, T028.**
- [ ] T029 Run full validation suite on CPU (N=50) to verify pipeline within 6-hour limit (Assumption: Compute feasibility). **Execute `code/src/run_validation.py` with N=50 and verify exit code 0 and existence of `data/processed/validation_report.json`.** **Dependencies: T005e, T008b2.**
- [ ] T030 Update `quickstart.md` with instructions for CPU validation vs GPU full analysis modes
- [ ] T031 [P] Add `state/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2.yaml` with content hashes
- [ ] T032 Run quickstart.md validation to ensure reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Critical Data Flow**: `code/src/entropy.py` (T012a-d) MUST complete and write `data/processed/entropy_results.csv` BEFORE `analysis.py` (T015) can run.
 - **Critical Data Flow**: `convergence_results.csv` (T013d) MUST exist before Router Simulation (T019) and Robustness (T025, T026).
 - **Critical Data Flow**: `filtered_dataset.json` (T004e) MUST exist before T012 and T013 to ensure underpowered data is excluded.
 - **Sensitivity Flow**: T026 requires T013d (k=2,3) and T013e (k=4) to be completed.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Depends on US1 data generation (T012d, T013d completion).
- **User Story 3 (P3)**: Depends on US1 data generation (T012d, T013d, T013e completion).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading (T004a-d) and Filtering (T004e) before Entropy/Inference (T012a-d, T013a-d)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005d, T005e, T007, T008, T008b1, T009) can run in parallel
- Once Foundational phase completes, US2 and US3 can start in parallel (both depend only on US1 data, not each other)
- All tests for a user story marked [P] can run in parallel
- **T012 (Entropy)** and **T013 (Inference)** are parallel tasks (both depend on T004e, T009).
- **T013e (Sensitivity Inference)** is parallel to **T012 (Entropy)**.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3a: User Story 1 (Core Correlation Data Generation)
4. **STOP and VALIDATE**: Test US1 independently on CPU (N=50)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Data Gen) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 1 (Analysis) → Test independently → Deploy/Demo
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data generation & Correlation)
 - Developer B: User Story 2 (Router Simulation) - *Can start once T012d/T013d are done*
 - Developer C: User Story 3 (Robustness) - *Can start once T012d/T013d/T013e are done*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks must run on free CPU-only CI for validation (T002, T012a-d, T013a-d with N=50, CodeLlama-1.3b). Full analysis (N=full, GPU) is a separate mode.
- **Critical Constraint**: Never fabricate data. Use real HumanEval/MBPP datasets via `datasets` library.
- **Critical Constraint**: Entropy extraction (T012) must not run convergence loops; strict separation of predictor (entropy) and target (convergence) is required by Principle VI.
- **Model Substitution**: CodeLlama models are used instead of LoopCoder-v2-2B due to environmental availability constraints. Success criteria are re-baselined accordingly. The methodology (entropy + convergence) is the invariant constraint.