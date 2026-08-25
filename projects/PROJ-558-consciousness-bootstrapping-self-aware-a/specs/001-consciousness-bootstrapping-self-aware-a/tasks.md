# Tasks: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

**Input**: Design documents from `/specs/001-consciousness-bootstrapping-self-aware-a/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Critical Prerequisites**:
- **Spec Consistency**: The `plan.md` artifact contains a contradiction regarding "pre-computed teacher labels" vs "internal self-consistency proxy". The tasks below strictly implement the `spec.md` requirement (internal proxy). **FLAGGED**: Plan must be updated to align.
- **Review Consistency**: Prior reviews raised concerns about scope creep and philosophical metrics. The tasks below strictly adhere to `spec.md` FR-001 through FR-007 and SC-001 through SC-005. All non-specified metrics (T043-T048) have been removed.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must follow specific predecessor)
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create directory structure: `projects/PROJ-558-consciousness-bootstrapping-self-aware-a/` with subdirs `data/raw`, `data/processed`, `code`, `tests`, `artifacts`, `artifacts/checkpoints`, `artifacts/results`. **Context**: Working directory is the repository root. **Dependency**: None.

- [ ] T001b [P] Create `__init__.py` files for `code`, `code/models`, `code/training`, `code/evaluation`, `code/analysis`, `code/utils`
- [X] T001c [P] Initialize a Python project with `torch` (CPU-only), `transformers`, `datasets`, `scikit-learn` in `requirements.txt`
- [X] T001d [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Resource Constraint Derivation & Configuration

- [ ] T005-DERIVE [S] **Derivation Script**: Create `scripts/derive_token_limit.py` to calculate the `token_limit` based on Constitution Principle VII (A constrained RAM limit
The research question, method, and references remain unchanged as per the planning document requirements.). **Logic**: Estimate model size (TinyLlama ~tens of millions to hundreds of millions of params = small model size), overhead, and gradient accumulation. Calculate max tokens that fit within 7GB. Output the calculated integer to `code/utils/config.py`. **Constraint**: This ensures the value is derived, not magic. **Dependency**: T001a.
- [ ] T005-CONFIG [S] **Config Implementation**: Implement `code/utils/config.py` to read the `token_limit` from the derivation script output or use the A default sample size of a sufficiently large magnitude will be employed to ensure statistical power. if the script is not run. **Constraint**: Must log the derivation source. **Dependency**: T005-DERIVE.
- [ ] T002-CHK [S] **Validation Script**: Create `scripts/validate_config.py` to check `code/utils/config.py`. **Logic**: Verify `token_limit` is present, is a positive integer, and conforms to the required system capacity. If `token_limit` is missing, not an integer, or exceeds the 7GB derived limit, log CRITICAL error and exit 1. **Dependency**: T005-CONFIG.

### Data Loading & Configuration

- [ ] T004a-FETCH [S] [US1] **Implementation**: Implement `data_loader.py` function `fetch_pile_arxiv()` to fetch the 'arXiv' subset of the Pile dataset via HuggingFace `datasets` API. **Logic**: Use `datasets.load_dataset("pile", split="train", streaming=True)`. **Filter**: Filter for items where `item['meta']['domain'] == 'arXiv'`. **Constraint**: Do NOT truncate here. **Action**: Save raw stream to `projects/PROJ-558-consciousness-bootstrapping-self-aware-a/data/raw/pile_arxiv_raw.jsonl`. **Dependency**: T002-CHK.
- [ ] T004b-FILTER [S] [US1] **Implementation**: Implement `data_loader.py` function `filter_pile_arxiv()` to read `data/raw/pile_arxiv_raw.jsonl` and write `data/processed/pile_arxiv_filtered.jsonl` containing only items with `domain='arXiv'`. **Constraint**: Do NOT truncate here. **Dependency**: T004a-FETCH.
- [ ] T004c-TRUNCATE [S] [US1] **Implementation**: Implement `data_loader.py` function `truncate_pile_arxiv` to read `data/processed/pile_arxiv_filtered.jsonl` and write `data/processed/pile_arxiv_truncated.jsonl` containing a truncated initial sequence of tokens. **Logic**: Read tokens from stream, count until the `token_limit` from `config.py` is reached, then stop. **MUST**: Explicitly cite FR-002 and SC-001 in the code comments. **MUST**: Log the final token count to `artifacts/results/token_count.log` to verify the 'first N tokens' constraint. **Dependency**: T004b-FILTER, T005-CONFIG. **Note**: This ensures the 'first N tokens' constraint is met during processing.
- [ ] T004b-GSM8K [P] [US2] **Implementation**: Implement `data_loader.py` function to fetch GSM8K dataset via HuggingFace `datasets` API. **Action**: Save to `projects/PROJ-558-consciousness-bootstrapping-self-aware-a/data/raw/gsm8k.json` with checksum in `data/manifest.json`. **Dependency**: T001a. **Note**: Parallel-safe relative to T004b-MMLU.
- [ ] T004b-MMLU [P] [US2] **Implementation**: Implement `data_loader.py` function to fetch MMLU dataset via HuggingFace `datasets` API. **Action**: Save to `projects/PROJ-558-consciousness-bootstrapping-self-aware-a/data/raw/mmlu.json` with checksum in `data/manifest.json`. **Dependency**: T001a. **Note**: Parallel-safe relative to T004b-GSM8K.
- [ ] T006 [P] Create base `ModelCheckpoint` and `EvaluationResult` entities in `code/models/` and `code/evaluation/` in a format suitable for serialization (e.g., dataclasses, Pydantic, dicts).
- [ ] T007 [P] Implement `base_llama.py` wrapper for a small transformer (<300M params) in `code/models/base_llama.py`. **Note**: Use TinyLlama as per Spec US-01.
- [ ] T008 [P] Setup error handling and logging infrastructure in `code/utils/logging.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Train Self-Referential Model (Priority: P1) 🎯 MVP

**Goal**: Construct a TinyLlama-based model with temporal recursive self-attention and train it on a sampled Pile subset to produce recursive and baseline checkpoints.

**Independent Test**: The training pipeline is expected to execute on GitHub Actions CPU runner, produce two checkpoints, and complete within 120 minutes without OOM.

**NOTE on Spec vs Plan Divergence**: The `plan.md` Summary has been updated to remove "pre-computed teacher model labels" and now correctly reflects the "internal self-consistency proxy" requirement from `spec.md` Assumptions. This task strictly implements the `spec.md` requirement.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These are **Test Definition** tasks. They create the test file content. The CI runner executes these tests **AFTER** the implementation tasks (T011-T015) are merged. **NOTE**: The [P] tag on Test Definition tasks applies only to file creation. Test execution will fail if the implementation code (T011-T015) is not yet present.

- [ ] T009 [P] [US1] **Definition**: Create unit test file `tests/unit/models/test_recursive_attention.py` with test cases: `test_shape_consistency` (checks output shape matches input), `test_attention_mask_propagation` (checks mask handling). (Expected to fail initially)
- [ ] T010 [P] [US1] **Definition**: Create unit test file `tests/unit/training/test_loss_functions.py` with test cases: `test_joint_loss_computation` (checks loss calculation with dummy tensors), `test_confidence_proxy_logic` (checks single-path proxy logic). (Expected to fail initially)

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `recursive_llama.py` with temporal recursive self-attention module (FR-001) in `code/models/recursive_llama.py`
- [ ] T012-IMPL [S] [US1] **Implementation**: Implement `loss_functions.py` with joint loss (cross-entropy + confidence-prediction). **Implementation Logic**: Define a function `compute_confidence_loss(model, batch, generate_paths_callback, temperature=0.7, top_p=0.9, max_tokens=256, n_samples=3)` that: (1) Uses `generate_paths_callback` (signature: `callback(batch: dict, n_samples: int, temperature: float) -> List[List[str]]`) to generate N=3 reasoning paths per training item; (2) Computes the majority vote of these paths to determine a binary 'proxy correctness' signal. **Majority Vote Logic**: Compare the final answer strings (after stripping whitespace/punctuation) of the N=3 paths. If 2 or more match, the majority vote is that answer. **Correctness Logic**: The proxy signal is 1 if the majority vote is consistent (i.e., the model agrees with itself), 0 otherwise. **Tie-Breaking Rule**: If the three paths generate three distinct final answers (1-1-1 distribution), treat as a tie and set the proxy signal to 0 (incorrect). **Input/Output**: Input: `batch` (dict), `generate_paths_callback` (callable). Output: `loss_value` (float), `proxy_signal` (int 0/1), `confidence_pred` (float 0-1). **Note**: This is a self-referential training signal as per Spec Assumptions. The 'correctness' is defined by the model's own majority vote. **Optimization Note**: To meet the 120-minute budget (Constitution VII), implement batched generation for the N=3 paths to minimize overhead. **Constraint Note**: N=3 is used for the training proxy to meet the 120-minute budget (Constitution VII: Resource-Constrained Architectural Fidelity) while allowing a true majority vote, while FR-003 mandates N=10 for the *evaluation* benchmark. This distinction is critical. **Dependency**: Requires T011 (recursive_llama.py). **Circular Dependency Fix**: This task defines a generic `generate_paths_callback` interface. The training script (T013) will provide a mock/internal generator for the training proxy, breaking the dependency on T019a-GEN (US2).
- [ ] T013 [S] [US1] **Implementation**: Implement `train.py` script to train both recursive and baseline models with fixed seeds (US-01) in `code/training/train.py`. **Dependency**: Requires T011, T012-IMPL, and T004c-TRUNCATE to be complete. **Note**: This task is NOT parallel-safe relative to T012-IMPL.
- [ ] T014 [US1] Add validation to `train.py` to prevent recursion depth > 2. **MUST** implement hard-fail: if OOM or depth violation occurs, log error and exit with non-zero code. **MUST NOT** automatically reduce recursion depth.
- [ ] T015 [US1] Add logging for training progress and OOM detection in `code/training/train.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Meta-Cognitive Metrics (Priority: P2)

**Goal**: Run trained models against benchmarks to measure self-consistency, error detection, and uncertainty calibration.

**Independent Test**: Evaluation script ingests checkpoints, generates predictions, and outputs a JSON with raw metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for self-consistency majority vote logic (tie-breaking rule) in `tests/unit/evaluation/test_metrics.py` (Test: `test_majority_vote_tie_break`)
- [ ] T017 [P] [US2] Unit test for Brier score and ECE calculation in `tests/unit/evaluation/test_metrics.py` (Test: `test_brier_score_calc`, `test_ece_calc`)

### Implementation for User Story 2

- [ ] T018 [S] [US2] **Implementation**: Implement `metrics.py` to calculate self-consistency, ROC-AUC, Brier score, and ECE (FR-003, FR-004) in `code/evaluation/metrics.py`. **CRITICAL**: Implement `calculate_error_detection_calibration` function internally to compute ECE. **Input Requirement**: This function MUST accept in-memory data structures (dicts) containing the generated paths, majority votes, confidence scores, and ground truth directly from the benchmark generation tasks (T019a-GEN, T019c-GEN, T019b), rather than requiring file I/O. **Output Requirement**: MUST output the final computed metrics (Brier score, ECE, ROC-AUC) to `artifacts/results/metrics.json`. **CRITICAL**: MUST output raw binning data to `data/processed/ece_binning.json` to satisfy Constitution Principle IV (Single Source of Truth) for reproducibility. **Dependency**: Requires T019a-GEN (GSM8K results), T019c-GEN (MMLU results), and T019b (standard inference) to be complete. **Note**: This task now accepts in-memory data to allow US3 to start as soon as data is generated, decoupling from the file-write step. **Parallel Note**: US3 (T024, T025) can now run immediately after T018 completes, WITHOUT waiting for T019a-SAVE or T019c-SAVE to finish writing files.
- [ ] T019a-BENCH-DEF [S] [US2] **Implementation**: Define the 'Self-Consistency Benchmark' configuration. **Action**: Create a configuration file or constant in `code/evaluation/config.py` that explicitly defines the 'Self-Consistency Benchmark' as the evaluation protocol using the GSM8K dataset with N=10 reasoning paths. **Rationale**: This explicitly distinguishes the dataset (GSM8K) from the benchmark protocol (N=10) as required by FR-003. **Dependency**: Requires T004b-GSM8K.
- [ ] T019a-GEN [S] [US2] **Implementation**: Implement `run_benchmarks.py` function `generate_benchmark_paths()` to generate **multiple reasoning paths per question** for the **Self-Consistency Benchmark** using temperature=0.7, top_p=0.9, and a fixed seed per run. **Logic**: The 'Self-Consistency Benchmark' is implemented using the GSM8K dataset (as defined in T019a-BENCH-DEF). Generate N=10 reasoning paths for each question in the GSM8K dataset (as per FR-003). **Output**: Generate in-memory data structures containing the paths, majority vote, confidence, and ground truth. **Dependency**: Requires T013 (Training), T004b-GSM8K, T019a-BENCH-DEF to be complete. **Note**: This task implements the N=10 protocol strictly for the GSM8K dataset.
- [ ] T019a-TIE [S] [US2] **Implementation**: Implement `run_benchmarks.py` function `apply_tie_breaking()` to handle ties in the generated paths. **Logic**: If a tie occurs (e.g., between paths of equal magnitude), **prefer the first generated path** as per spec Edge Cases. **Definition of Tie**: A tie is defined as 'identical final answer strings after stripping whitespace and punctuation'. **Documentation**: This tie-breaking rule MUST be documented in the final analysis report (T026). **Dependency**: Requires T019a-GEN.
- [ ] T019a-SAVE [S] [US2] **Implementation**: Implement `run_benchmarks.py` function `save_benchmark_results()` to serialize the in-memory data structures from T019a-TIE to `artifacts/results/benchmark_raw.json`. **Dependency**: Requires T019a-TIE.
- [ ] T019b [P] [US2] **Implementation**: Implement `run_benchmarks.py` to run standard MMLU/GSM8K inference (single path) for accuracy baseline. **Dependency**: Requires T013 (Training), T004b-GSM8K, and T004b-MMLU to be complete.
- [ ] T019c-GEN [S] [US2] **Implementation**: Implement `run_benchmarks.py` function `generate_mmlu_paths()` to generate **multiple reasoning paths per question** for the **MMLU dataset** using temperature=0.7, top_p=0.9, and a fixed seed per run. **Logic**: Generate N=10 reasoning paths for each question in the MMLU dataset (as per FR-003). **Output**: Generate in-memory data structures containing the paths, majority vote, confidence, and ground truth. **Dependency**: Requires T013 (Training), T004b-MMLU to be complete. **Note**: This task implements the N=10 protocol for MMLU to satisfy FR-003.
- [ ] T019c-TIE [S] [US2] **Implementation**: Implement `run_benchmarks.py` function `apply_mmlu_tie_breaking()` to handle ties in MMLU generated paths. **Logic**: If a tie occurs, **prefer the first generated path**. **Dependency**: Requires T019c-GEN.
- [ ] T019c-SAVE [S] [US2] **Implementation**: Implement `run_benchmarks.py` function `save_mmlu_results()` to serialize the in-memory data structures from T019c-TIE to `artifacts/results/mmlu_benchmark_raw.json`. **Dependency**: Requires T019c-TIE.
- [ ] T020 [US2] Implement logic to produce 'shuffled-attention' control dataset for isolation of temporal recursion effects (US-02) in `code/evaluation/run_benchmarks.py`. **Dependency**: Requires T004b-GSM8K and T004b-MMLU.
- [ ] T020b-METRICS [S] [US2] **Implementation**: Implement `metrics.py` function `calculate_control_metrics()` to compute self-consistency, ROC-AUC, Brier score, and ECE for the shuffled-attention control dataset. **Output**: Append results to `artifacts/results/metrics.json` with a 'control' key. **Dependency**: Requires T020 and T018 (for logic reuse).
- [ ] T021 [US2] Add contract validation to ensure output JSON matches `EvaluationResult` schema in `code/evaluation/run_benchmarks.py`
- [ ] T022 [US2] Add logging for benchmark execution and metric aggregation in `code/evaluation/run_benchmarks.py`

**Checkpoint**: At this point, At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Analysis and Sensitivity Testing (Priority: P3)

**Goal**: Perform paired t-tests across multiple seeds and sensitivity analysis to determine statistical significance.

**Independent Test**: Analysis script processes evaluation outputs, performs tests, and generates a report with p-values and plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for paired t-test and Bonferroni correction logic in `tests/unit/analysis/test_stats.py` (Test: `test_paired_ttest`, `test_bonferroni_correction`)

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement `stats.py` to perform paired t-tests, Cohen's d, confidence intervals, and Bonferroni correction (FR-005, FR-007) in `code/analysis/stats.py`. **Must include**: Logic to calculate the **percentage difference in self-consistency scores** between recursive and baseline models (SC-001) and output to `artifacts/results/statistical_report.json`. **Constraint**: Must configure and validate the alpha threshold for all significance tests. **Validation**: Script must explicitly check `alpha` from `config.py` (default a conventional significance threshold) and log a warning if it deviates, but MUST NOT fail hard if it differs, to allow flexibility. **Dependency**: Requires T018 (metrics calculation logic), T020b-METRICS (control metrics), and T020 (shuffled-attention control) to be complete. **Parallel Note**: T024 does NOT depend on T019a-SAVE or T019c-SAVE. It can run as soon as T018 (in-memory metrics) is complete, enabling independent execution of US3 while US2 file I/O continues.
- [ ] T025 [US3] **Implementation**: Implement sensitivity analysis sweep for confidence thresholds. **Logic**: Implement a loop over a discrete set of values (FR-006) and output results to `artifacts/results/sensitivity_analysis.csv` (or JSON) reporting the variation in error rates for each threshold (to satisfy FR-006's requirement to report variation) in `code/analysis/stats.py`. **Justification**: The set {0.4, 0.5, 0.6} satisfies FR-006's 'range of moderate thresholds' requirement and SC-005's 'at least three distinct threshold values' requirement. **Output Schema**: CSV with columns `threshold,float;false_positive_rate,float;false_negative_rate,float`. **Must also**: Integrate the `calculate_error_detection_calibration` output from T018 (imported from `code/evaluation/metrics.py`) to generate the sensitivity plot for the calibration curve across thresholds. **Dependency**: Requires T018 (metrics calculation logic) and T020b-METRICS (control metrics) to be complete. **Note**: T025 is now unblocked and depends on T018 and T020b-METRICS. **Parallel Note**: T025 does NOT depend on T019a-SAVE or T019c-SAVE. It can run as soon as T018 (in-memory metrics) is complete.
- [ ] T026 [US3] Implement report generation to output `StatisticalReport` with p-values, effect sizes, confidence intervals, sensitivity plots, and the percentage difference metric (US-03) in `code/analysis/stats.py`. **Must define**: JSON schema for the report with keys: `p_values` (dict), `effect_sizes` (dict), `confidence_intervals` (dict), `sensitivity_data` (list), `tie_breaking_rule` (string). **Schema**: `{"p_values": {"metric_name": float}, "effect_sizes": {"metric_name": float},...}`. **CRITICAL**: MUST read `data/processed/ece_binning.json` (generated by T018) to populate the calibration curve section of the report. **CRITICAL**: MUST include the tie-breaking rule (from T019a-TIE/T019c-TIE) in the report. **Dependency**: Requires T024 and T025 to be complete.
- [ ] T027 [US3] Add logic to exclude invalid seeds (non-converged confidence loss) from statistical comparison (Edge Case) in `code/analysis/stats.py`. **Constraint**: If excluding seeds results in an insufficient number of valid seeds, the script MUST fail with a clear error message. to satisfy Constitution Principle VI (Statistical Rigor).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` including the new statistical report format, the definitions of the implemented metrics (self-consistency, calibration, error detection), and the "Training Signal Methodology" section explaining the plan/spec correction.
- [ ] T038 [P] Run `ruff check` and `black --check` on the entire `code/` directory; CI must fail if any lint/format errors exist.
- [ ] T039 [P] Run memory profiling on the training script (`train.py`) with max batch size; verify peak RSS < 7GB and log result to `artifacts/results/memory_profile.log`. **Note**: While the spec requires the run to fail if the limit is exceeded, this task logs profiling data for review. If peak RSS > 7GB, the run MUST fail as per Edge Cases. **Constraint**: Record checksum of `memory_profile.log` in `state/projects/PROJ-558-consciousness-bootstrapping-self-aware-a.yaml` under the `artifact_hashes` map to satisfy Constitution Principle III (Data Hygiene). **Clarification**: This log is an execution artifact, not a dataset, and requires checksumming in the state YAML for reproducibility. **UPDATE**: Removed checksum requirement per Constitution Principle III strict interpretation (only datasets are checksummed).
- [ ] T040 [P] Additional unit tests for the new statistical metrics in `tests/unit/analysis/test_stats.py` and `tests/unit/evaluation/test_metrics.py`.
- [ ] T041 [P] Run `quickstart.md` validation to ensure all artifacts are generated correctly.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Note**: T005-DERIVE, T005-CONFIG, and T002-CHK must pass (valid config, plan corrected, spec verified) before T004a-FETCH.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Phase N (Polish)**: Depends on all desired user stories being complete
- **Phase N+1 (Validation)**: **REMOVED**. The validation scope ends with T026 (Statistical Report). No T042-VALIDATE task exists.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **Note**: T012-IMPL is blocked by T011. T019a-SAVE is blocked by T013 (Training), T004b-GSM8K, and T004b-MMLU. T018 is blocked by T019a-GEN, T019c-GEN, and T019b.
- **Note**: T005-DERIVE, T005-CONFIG, and T002-CHK must be completed before T004a-FETCH.
- **Note**: Phase N tasks depend on T024 and T018.
- **Note**: US3 (T024, T025) can run as soon as T018 (in-memory metrics) is complete, WITHOUT waiting for T019a-SAVE or T019c-SAVE (file I/O).

### Within Each User Story

- **Test Definition** (T009, T010, etc.) MUST be written before implementation tasks to define the interface.
- **Implementation** (T011-T015, etc.) MUST follow.
- **Test Execution** (CI runner) MUST run after implementation is merged.
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT** T004a-FETCH, T004b-FILTER, T004c-TRUNCATE, T004b-GSM8K, T004b-MMLU which are sequential.
- Once Foundational phase completes, US1, US2, and US3 can start in parallel (if team capacity allows)
- **Note**: T012-IMPL is NOT parallel-safe relative to T013.
- **Note**: Phase N tasks can run in parallel with each other once T024 is complete.
- **Note**: US3 (T024, T025) can run in parallel with T019a-SAVE and T019c-SAVE, as it only depends on in-memory data from T018.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories) - **Note**: T005-DERIVE, T005-CONFIG, and T002-CHK must pass (valid config, plan corrected, spec verified) before T004a-FETCH.
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Final Validation (T037-T041)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Training)
 - Developer B: User Story 2 (Evaluation)
 - Developer C: User Story 3 (Analysis)
3. Developer D (or C after US3): Phase N (Polish)

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = sequential, must follow predecessor
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only CI with a limited number of cores and memory. No GPU, no low-bit quantization.
- **Scope Note**: The 'Teacher-Student Distillation' and 'Pre-computed Teacher Labels' mentioned in `plan.md` have been removed. The plan now correctly reflects the 'internal self-consistency proxy' requirement from `spec.md`.
- **Dependency Note**: Task T012-IMPL (loss_functions.py) is a strict prerequisite for T013 (train.py) and is not parallel-safe relative to T013.
- **Tie-Breaking Note**: Task T012-IMPL implements a deterministic tie-breaking rule (signal=0) for three distinct answers (1-1-1) as explicitly defined to satisfy `spec.md` Edge Cases. T019a/T019c-TIE document the evaluation rule. **Note**: Task T012b-DOC has been removed. Tie-breaking rules are now documented inline in T012-IMPL (training) and T019a/T019c-TIE (evaluation).
- **Token Limit Note**: Task T005-DERIVE calculates the `token_limit` based on 7GB RAM constraints, replacing the arbitrary placeholder and dynamic calculation. T005-CONST now reads this derived value and links it to FR-002's 'first [deferred] tokens' and the plan's 'sampled subset'. T004c-TRUNCATE explicitly cites FR-002 and logs the final count.
- **Manifest Note**: T039 clarifies that execution logs are not datasets and do require checksumming in `state/...yaml` `artifact_hashes` map (not `data/manifest.json` or `artifacts/manifest_execution.json`) for reproducibility under the Constitution Principle III. **UPDATE**: Checksum requirement removed per strict interpretation of Principle III.
- **Seed Note**: T027 enforces the constitutional requirement of a minimum number of seeds by failing if the count drops below the specified threshold.
- **N=3 Note**: T012-IMPL uses N=3 samples for the training proxy to ensure the 120-minute budget is met (Constitution VII) and to allow for a true majority vote. This is distinct from FR-003's N=10 for evaluation.
- **OOM Note**: T014 and the Foundational phase notes strictly enforce a hard-fail on OOM. The system MUST NOT reduce recursion depth.
- **Benchmark Note**: The Self-Consistency Benchmark is implemented using the GSM8K dataset (T004b-GSM8K), ensuring it is distinct from standard MMLU tasks.
- **Philosophical Note**: All metrics are strictly derived from Functional Requirements FR-001 to FR-007. No 'philosophical' metrics (e.g., 'Normative Alignment', 'Strange Loop Detection') are implemented.
- **Review-Driven Note**: Phase N+2 tasks (T043-T048) have been REMOVED. These tasks introduced unauthorized metrics (adaptation_score, self_model_cost_ratio, is_irreducible, truthfulness_index, novelty_score) and undefined algorithms (prediction of recursive output, KL-divergence reference, mid-inference disable mechanism) that were not defined in `spec.md` FR-001 through FR-007 or SC-001 through SC-005. Their removal resolves scope creep and executability concerns.
- **Scope Correction**: The 'first pass vs recursive refinement' comparison (T043), 'irreducibility test' (T045), 'novel pattern detection' (T047), and 'controlled experiment disabling recursive module' (T048) are explicitly OUT OF SCOPE for the MVP. The spec only requires comparing recursive vs baseline on standard benchmarks.
- **Artifact Dependency Note**: The removal of T043-T048 resolves the blocking artifact generation issue (missing 'first pass' baseline) and the undefined algorithm issues (prediction method, reference distribution, disable mechanism).
- **Tie-Breaking Documentation Note**: The removal of T012b-DOC resolves the false dependency and documentation gap. Tie-breaking rules are now exclusively documented in the tasks where they are implemented (T012-IMPL for training, T019a/T019c-TIE for evaluation).
- **Metric Calculation Dependency Note**: T018 now accepts in-memory data structures, allowing US3 to start as soon as data is generated, decoupling from the file-write step (T019a-SAVE/T019c-SAVE). T024 and T025 explicitly do NOT depend on T019a-SAVE/T019c-SAVE.
- **Validation Phase Note**: The 'Phase N+1 (Validation)' and 'T042-VALIDATE' references have been removed. The validation scope ends with T026 (Statistical Report) and T037-T041 (Polish). No further review-driven tasks exist beyond FR-001 to FR-007.