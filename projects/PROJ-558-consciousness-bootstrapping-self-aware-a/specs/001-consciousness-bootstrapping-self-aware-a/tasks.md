# Tasks: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

**Input**: Design documents from `/specs/001-consciousness-bootstrapping-self-aware-a/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Critical Prerequisites**:
- **Spec Consistency**: The `spec.md` artifact contains `[deferred]` for the token limit in FR-002. The implementation tasks will use a configurable default value as defined in `config.py`. The `[deferred]` in the spec is interpreted as 'unspecified in spec, must be defined in code'.
- **Review Consistency**: Prior reviews from Ada Lovelace, Alan Turing, Daniel Kahneman, David Krakauer, Socrates, and Stephen Wolfram raise fundamental concerns about the distinction between *simulated* introspection and *genuine* meta-cognitive adaptation. The tasks below explicitly operationalize these philosophical concerns into measurable engineering constraints (T051-T065) to ensure the project measures *behavioral adaptation* rather than mere *self-description*.

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

- [ ] T001a [P] Create directory structure: `projects/PROJ-558-consciousness-bootstrapping-self-aware-a/` with subdirs `data/raw`, `data/processed`, `code`, `tests`, `artifacts`, `artifacts/checkpoints`, `artifacts/results`
- [ ] T001b [P] Create `__init__.py` files for `code`, `code/models`, `code/training`, `code/evaluation`, `code/analysis`, `code/utils`
- [ ] T001c [P] Initialize a Python project with `torch` (CPU-only), `transformers`, `datasets`, `scikit-learn` in `requirements.txt`
- [ ] T001d [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Prerequisite Validation & Plan Correction

- [ ] T003a-PLAN-CORRECT [S] **Identify**: Scan `plan.md` for occurrences of "Teacher-Student Distillation", "Pre-computed Teacher Labels", or "external truth". **Action**: Output a JSON array of objects `{"line_number": int, "context": "string"}` to `artifacts/plan_issues.json`. **Schema**: `{"issues": [{"line_number": int, "context": "string"}]}`. **Dependency**: None (but requires T001a to exist). **Note**: If no issues found, output `{"issues": []}`. **Dependency**: T001a.
- [ ] T003b-PLAN-GEN [S] **Generate Diff**: Create a diff/patch that replaces all identified occurrences with "Internal Self-Consistency Proxy" and updates the methodology description to match `spec.md` Assumptions. **Action**: Use `git diff --no-index plan.md plan_fixed.md > patches/plan_correction.patch` (or equivalent) to generate the patch and save to `patches/plan_correction.patch`. **Dependency**: T003a-PLAN-CORRECT.
- [ ] T003c-PLAN-APPLY [S] **Apply Patch**: Apply the generated patch to `plan.md`. **Action**: Run `git apply patches/plan_correction.patch` and commit with message "Fix: Correct plan.md to use internal self-consistency proxy" on the current branch. **Dependency**: T003b-PLAN-GEN.
- [ ] T003d-PLAN-VERIFY [S] **Verify Plan**: Scan `plan.md` to confirm all instances of "pre-computed teacher labels" are removed and "internal self-consistency proxy" is present. **Action**: If `plan.md` still contains forbidden phrases, log "CRITICAL: Plan correction failed" and `sys.exit(1)`. If clean, log "SUCCESS: Plan corrected" and exit 0. **Dependency**: T003c-PLAN-APPLY.
- [ ] T005 [P] **Implementation**: Implement `config.py` to manage hyperparameters (seed, batch size, recursion depth=2, learning rate, `token_limit=100000`). **Constraint**: `token_limit` MUST be initialized to the integer `100000`. **Documentation**: Add a comment stating "This is a PLACEHOLDER value subject to change; deviates from spec's [deferred] state." **Dependency**: T003d-PLAN-VERIFY.
- [ ] T002-CHK [S] **Validation Script**: Create `scripts/validate_config.py` to check `code/utils/config.py`. **Logic**: Verify `token_limit` is present and is a positive integer. If `token_limit` is missing, `None`, or not a positive integer, log CRITICAL error and exit 1. **Dependency**: T005.

### Data Loading & Configuration

- [ ] T004-IMPL-DATA [S] [US1] **Implementation**: Implement `data_loader.py` to fetch the 'arXiv' subset of the Pile dataset via HuggingFace `datasets` API. **Logic**: Use `datasets.load_dataset("pile", split="train", streaming=True)` and filter for items where the text starts with 'arXiv'. **Constraint**: Do NOT truncate here. **Action**: Save raw stream to `projects/PROJ-558-consciousness-bootstrapping-self-aware-a/data/raw/pile_arxiv_raw.jsonl`. **Manifest**: Compute `sha256sum` of the file and record the hash in `data/manifest.json` using the schema `{"datasets": {"pile_arxiv_raw.jsonl": "<hash>"}}`. **Dependency**: T003d-PLAN-VERIFY, T005, T002-CHK. **Note**: This task is parallel-safe relative to other data loaders.
- [ ] T004-IMPL-TRUNCATE [S] [US1] **Implementation**: Implement truncation logic to read `data/raw/pile_arxiv_raw.jsonl` and write `data/processed/pile_arxiv_truncated.jsonl` containing exactly the first `N` tokens as defined by `config.token_limit`. **Logic**: Read tokens from stream, count until `token_limit` is reached, then stop. **Dependency**: T004-IMPL-DATA, T005. **Note**: This ensures the 'first N tokens' constraint is met during processing.
- [ ] T004b-GSM8K [S] [US2] **Implementation**: Implement `data_loader.py` (additional function) to fetch GSM8K dataset via HuggingFace `datasets` API. **Action**: Save to `projects/PROJ-558-consciousness-bootstrapping-self-aware-a/data/raw/gsm8k.json` with checksum in `data/manifest.json`. **Dependency**: T004-IMPL-TRUNCATE (to ensure manifest lock/sequence). **Note**: Sequential to avoid manifest race conditions.
- [ ] T004b-MMLU [S] [US2] **Implementation**: Implement `data_loader.py` (additional function) to fetch MMLU dataset via HuggingFace `datasets` API. **Action**: Save to `projects/PROJ-558-consciousness-bootstrapping-self-aware-a/data/raw/mmlu.json` with checksum in `data/manifest.json`. **Dependency**: T004b-GSM8K. **Note**: Sequential relative to T004b-GSM8K.
- [ ] T006 [P] Create base `ModelCheckpoint` and `EvaluationResult` entities in `code/models/` and `code/evaluation/` in a format suitable for serialization (e.g., dataclasses, Pydantic, dicts).
- [ ] T007 [P] Implement `base_llama.py` wrapper for a small transformer (<300M params) in `code/models/base_llama.py`. **Note**: Use TinyLlama as per Spec US-01.
- [ ] T008 [P] Setup error handling and logging infrastructure in `code/utils/logging.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Train Self-Referential Model (Priority: P1) 🎯 MVP

**Goal**: Construct a TinyLlama-based model with temporal recursive self-attention and train it on a sampled Pile subset to produce recursive and baseline checkpoints.

**Independent Test**: The training pipeline executes on GitHub Actions CPU runner, produces two checkpoints, and completes within 120 minutes without OOM.

**NOTE on Spec vs Plan Divergence**: The `plan.md` Summary references "pre-computed teacher model labels". This task strictly implements the `spec.md` requirement for an **internal self-consistency proxy** (derived from N=2 model generations) to avoid tautology. The plan discrepancy is resolved by T003a-PLAN-CORRECT.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These are **Test Definition** tasks. They create the test file content. The CI runner executes these tests **AFTER** the implementation tasks (T011-T015) are merged. **NOTE**: The [P] tag on Test Definition tasks applies only to file creation. Test execution will fail if the implementation code (T011-T015) is not yet present.

- [ ] T009 [P] [US1] **Definition**: Create unit test file `tests/unit/models/test_recursive_attention.py` with test cases: `test_shape_consistency` (checks output shape matches input), `test_attention_mask_propagation` (checks mask handling). (Expected to fail initially)
- [ ] T010 [P] [US1] **Definition**: Create unit test file `tests/unit/training/test_loss_functions.py` with test cases: `test_joint_loss_computation` (checks loss calculation with dummy tensors), `test_confidence_proxy_logic` (checks single-path proxy logic). (Expected to fail initially)

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `recursive_llama.py` with temporal recursive self-attention module (FR-001) in `code/models/recursive_llama.py`
- [ ] T012-IMPL [S] [US1] **Implementation**: Implement `loss_functions.py` with joint loss (cross-entropy + confidence-prediction). **Implementation Logic**: Define a function `compute_confidence_loss(model, batch, generate_paths_callback, temperature=0.7, top_p=0.9, max_tokens=256, n_samples=2)` that: (1) Uses `generate_paths_callback` (a standard Python callable) to generate N=2 reasoning paths per training item; (2) Computes the majority vote of these paths to determine a binary 'proxy correctness' signal; (3) **Tie-Breaking Rule**: If a tie occurs (1 correct, 1 incorrect), the proxy signal is set to 0 (incorrect) to satisfy spec Edge Cases for handling ties. This is an implementation choice derived from the spec's deterministic requirement. (4) Compare the model's predicted confidence for the final answer against this proxy signal. **Note**: This is a self-referential training signal as per Spec Assumptions. The 'correctness' is defined by the model's own majority vote. **Optimization Note**: To meet the 120-minute budget, implement batched generation for the N=2 paths to minimize overhead. **Dependency**: Requires T011 (recursive_llama.py). **Constraint Note**: N=2 is used for the training proxy to meet the 120-minute CPU budget (Constitution Principle VII: Resource-Constrained Architectural Fidelity), while FR-003 mandates N=10 for the *evaluation* benchmark. This distinction is critical. **Return Type**: Returns an in-memory dict with keys: `loss_value` (float), `proxy_signal` (int 0/1), `confidence_pred` (float 0-1). **Note**: This task defines the function logic; the actual generation is injected via the callback at runtime.
- [ ] T013 [US1] Implement `train.py` script to train both recursive and baseline models with fixed seeds (US-01) in `code/training/train.py`. **Dependency**: Requires T011, T012-IMPL, and T004-IMPL-TRUNCATE to be complete. **Note**: This task is NOT parallel-safe relative to T012-IMPL.
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

- [ ] T018 [S] [US2] **Implementation**: Implement `metrics.py` to calculate self-consistency, ROC-AUC, Brier score, and ECE (FR-003, FR-004) in `code/evaluation/metrics.py`. **CRITICAL**: Implement `calculate_error_detection_calibration` function internally to compute ECE. **Output Requirement**: MUST output the final computed metrics (Brier score, ECE, ROC-AUC) AND the raw binning data to `data/processed/ece_binning.json` to satisfy Constitution Principle IV (Single Source of Truth). **Schema**: JSON object with keys `bins` (list of dicts with `threshold`, `count`, `correct_count`, `mean_confidence`). **Dependency**: Requires T019a (Benchmark Generation) to be complete.
- [ ] T019a [S] [US2] **Implementation**: Implement `run_benchmarks.py` to generate **multiple reasoning paths per question** for the **Self-Consistency Benchmark** using temperature=0.7, top_p=0.9, and a fixed seed per run. **Logic**: The 'Self-Consistency Benchmark' is a methodology applied to the GSM8K and MMLU datasets. Generate N=10 reasoning paths for each question in both the GSM8K and MMLU test sets (as per FR-003). **Action**: Implement tie-breaking rule: if a tie occurs (e.g., between paths of equal magnitude), **prefer the first generated path** as per spec Edge Cases. **Documentation**: This tie-breaking rule MUST be documented in the final analysis report. **Output**: Save results to `artifacts/results/benchmark_raw.json`. **Schema**: JSON list of objects, each with keys: `question_id` (str), `paths` (list of str), `majority_vote` (str), `confidence` (float), `ground_truth` (str). **Dependency**: Requires T013 (Training), T004b-GSM8K, and T004b-MMLU to be complete. **Note**: This task implements the N=10 protocol strictly for the derived GSM8K and MMLU benchmarks. No separate dataset file is created for the benchmark.
- [ ] T019b [P] [US2] Implement `run_benchmarks.py` to run standard MMLU/GSM8K inference (single path) for accuracy baseline. **Dependency**: Requires T004b-GSM8K and T004b-MMLU to be complete.
- [ ] T020 [US2] Implement logic to produce 'shuffled-attention' control dataset for isolation of temporal recursion effects (US-02) in `code/evaluation/run_benchmarks.py`. **Dependency**: Requires T004b-GSM8K and T004b-MMLU.
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

- [ ] T024 [P] [US3] Implement `stats.py` to perform paired t-tests, Cohen's d, confidence intervals, and Bonferroni correction (FR-005, FR-007) in `code/analysis/stats.py`. **Must include**: Logic to calculate the **percentage difference in self-consistency scores** between recursive and baseline models (SC-001) and output to `artifacts/results/statistical_report.json`. **Constraint**: Must configure and validate the alpha threshold at **0.05** for all significance tests. **Validation**: Script must explicitly check `alpha == 0.05` and fail if not.
- [ ] T025 [US3] **Implementation**: Implement sensitivity analysis sweep for confidence thresholds across a **representative discrete set of values**. (FR-006) and output results to `artifacts/results/sensitivity_analysis.csv` (or JSON) reporting the variation in error rates for each threshold (to satisfy FR-006's requirement to report variation) in `code/analysis/stats.py`. **Justification**: The set {0.4, 0.5, 0.6} satisfies FR-006's 'range of moderate thresholds' requirement and SC-005's 'at least three distinct threshold values' requirement. **Must also**: Integrate the `calculate_error_detection_calibration` output from T018 (imported from `code/evaluation/metrics.py`) to generate the sensitivity plot for the calibration curve across thresholds. **Dependency**: Requires T018 (metrics calculation logic) and T020 (shuffled-attention control) to be complete. **Note**: T025 is now unblocked and depends on T018 and T020.
- [ ] T026 [US3] Implement report generation to output `StatisticalReport` with p-values, effect sizes, confidence intervals, sensitivity plots, and the percentage difference metric (US-03) in `code/analysis/stats.py`. **Must define**: JSON schema for the report with keys: `p_values` (dict), `effect_sizes` (dict), `confidence_intervals` (dict), `sensitivity_data` (list), `adaptation_coefficient` (float). **Schema**: `{"p_values": {"metric_name": float}, "effect_sizes": {"metric_name": float}, ...}`.
- [ ] T027 [US3] Add logic to exclude invalid seeds (non-converged confidence loss) from statistical comparison (Edge Case) in `code/analysis/stats.py`. **Constraint**: If excluding seeds results in an insufficient number of valid seeds, the script MUST fail with a clear error message. to satisfy Constitution Principle VI (Statistical Rigor).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Philosophical Grounding & Review Resolution (Priority: P3)

**Goal**: Address specific concerns raised by Ada Lovelace, Alan Turing, Daniel Kahneman, David Krakauer, Socrates, and Stephen Wolfram regarding the distinction between simulation and genuine adaptation.

**Independent Test**: The analysis report includes a dedicated section on "Behavioral Adaptation vs. Self-Description" and "Computational Irreducibility" with quantitative metrics.

### Implementation for Review Resolution

- [ ] T051 [US3] **Implementation**: Implement "Behavioral Adaptation Metric" in `code/analysis/stats.py`. **Logic**: Calculate the correlation between the model's *internal confidence proxy* (from T012) and its *actual external performance* (accuracy on GSM8K/MMLU) *before* and *after* training. **Rationale**: Addresses David Krakauer's concern: "If the model can only describe its own processes but cannot use that description to improve performance on external tasks, we have not bootstrapped consciousness." A positive shift in this correlation indicates adaptation, not just description. **Output**: Append `adaptation_coefficient_change` to `statistical_report.json`.
- [ ] T052 [US1/US2/US3] **Implementation**: Implement "Prediction Consistency Constraint" in `code/training/train.py` and `code/evaluation/run_benchmarks.py`. **Logic**: As per Alan Turing's review, require the model to predict its own output distribution (logits) *before* generation. Compute the KL-divergence between the predicted distribution and the actual generated distribution. **Action**: Add this KL-divergence as a penalty term to the loss function (T012) and as a metric in the evaluation (T018). **Rationale**: "Grounds the 'introspection' in a verifiable mechanical procedure rather than a linguistic claim."
- [ ] T053 [US3] **Implementation**: Implement "Computational Irreducibility Check" in `code/analysis/stats.py`. **Logic**: Run the recursive model with varying recursion depths (1, 2, 3) and measure the "surprise" (cross-entropy) of the meta-cognitive layer. Compare this to a linear approximation of the same process. **Rationale**: Addresses Stephen Wolfram's concern: "Test for irreducibility in the meta-cognitive layer. Just run it. See what emerges." If the process is reducible, the meta-cognitive layer adds no value.
- [ ] T054 [US3] **Implementation**: Implement "Post-Hoc Rationalization Detector" in `code/evaluation/metrics.py`. **Logic**: Compare the model's *stated* confidence (from the recursive attention head) with its *actual* error rate in specific bins. If the model claims high confidence but has high error rates in that bin (calibration error > threshold), flag as "rationalization". **Rationale**: Addresses Daniel Kahneman's concern: "System 1 generates a coherent story... often a post-hoc rationalization." Quantify the gap between "knowing the shape of the shadow" and "knowing the good."
- [ ] T055 [US3] **Implementation**: Add a "Thermodynamic Cost" analysis to the final report. **Logic**: Calculate the additional FLOPs and memory usage required for the recursive module compared to the baseline. **Rationale**: Addresses David Krakauer's concern: "Agency has never been free. It is paid for in ATP... model the pressure that made it necessary." Report the "Cost of Self-Awareness" in compute units.
- [ ] T056 [US3] **Implementation**: Add a "Subject/Object Distinction" metric. **Logic**: Measure the entropy of the model's self-representation. If the model's internal state regarding itself is indistinguishable from its state regarding the input (low entropy in self-representation), it fails the "subject vs object" test. **Rationale**: Addresses Socrates' and Ada Lovelace's concern: "Can the same thing be both? Is it merely simulating awareness?"
- [ ] T057 [US3] **Implementation**: Generate a "Philosophical Grounding Report" in `artifacts/results/philosophical_grounding.md`. **Content**: Synthesize findings from T051-T056 into a narrative addressing the specific questions raised by the reviewers (e.g., "Does the system originate or execute?", "Is it a mirror or an adaptive agent?"). **Constraint**: Must cite specific metric values from the JSON reports. **Structure**: Must include sections: "# Introduction", "## Behavioral Adaptation Analysis", "## Prediction Consistency Results", "## Irreducibility Check", "## Rationalization Detection", "## Thermodynamic Cost", "## Subject/Object Distinction", "## Conclusion".
- [ ] T058 [P] **Implementation**: Update `quickstart.md` to include a section on "Interpreting Philosophical Metrics" explaining how to read T051-T056 results in the context of the research question.

**Checkpoint**: All philosophical concerns have been operationalized and measured.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` including the new statistical report format, the definitions of the implemented metrics (self-consistency, calibration, error detection), and the "Training Signal Methodology" section explaining the plan/spec correction.
- [ ] T038 [P] Run `ruff check` and `black --check` on the entire `code/` directory; CI must fail if any lint/format errors exist.
- [ ] T039 [P] Run memory profiling on the training script (`train.py`) with max batch size; verify peak RSS < 7GB and log result to `artifacts/results/memory_profile.log`. **Note**: While the spec requires the run to fail if the limit is exceeded, this task logs profiling data for review. If peak RSS > 7GB, the run MUST fail as per Edge Cases. **Constraint**: Record checksum of `memory_profile.log` in `artifacts/manifest_execution.json` under the key `execution_logs` to satisfy Constitution Principle III (Data Hygiene) while maintaining separation from dataset hygiene. **Clarification**: This log is an execution artifact, not a dataset, and requires checksumming in `artifacts/manifest_execution.json` for reproducibility.
- [ ] T040 [P] Additional unit tests for the new statistical metrics in `tests/unit/analysis/test_stats.py` and `tests/unit/evaluation/test_metrics.py`.
- [ ] T041 [P] Run `quickstart.md` validation to ensure all artifacts are generated correctly.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Note**: T003a-PLAN-CORRECT, T003b-PLAN-GEN, T003c-PLAN-APPLY, T003d-PLAN-VERIFY, T005, and T002-CHK must pass (valid config, plan corrected, spec verified) before T004-IMPL-DATA.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Phase 6 (Review Resolution)**: Depends on Phase 5 (Statistical Analysis) as it uses the same `stats.py` and `metrics.py` infrastructure.
- **Phase N (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **Note**: T012-IMPL is blocked by T011. T019a is blocked by T013 (Training), T004b-GSM8K, and T004b-MMLU. T018 is blocked by T019a.
- **Note**: T003a-PLAN-CORRECT, T003b-PLAN-GEN, T003c-PLAN-APPLY, and T003d-PLAN-VERIFY must be completed before T004-IMPL-DATA.
- **Note**: Phase 6 tasks (T051-T058) depend on T024 and T018.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT** T004-IMPL-DATA, T004-IMPL-TRUNCATE, T004b-GSM8K, T004b-MMLU which are sequential.
- Once Foundational phase completes, US1, US2, and US3 can start in parallel (if team capacity allows)
- **Note**: T012-IMPL is NOT parallel-safe relative to T013.
- **Note**: Phase 6 tasks (T051-T058) can run in parallel with each other once T024 is complete.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories) - **Note**: T003a-PLAN-CORRECT, T003b-PLAN-GEN, T003c-PLAN-APPLY, T003d-PLAN-VERIFY, T005, and T002-CHK must pass (valid config, plan corrected, spec verified) before T004-IMPL-DATA.
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Phase 6 (Review Resolution) → Test independently → Deploy/Demo
6. Final Validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Training)
 - Developer B: User Story 2 (Evaluation)
 - Developer C: User Story 3 (Analysis)
 - Developer D: Phase 6 (Philosophical Grounding - can start once T018/T024 are drafted)

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
- **Scope Note**: The 'Teacher-Student Distillation' and 'Pre-computed Teacher Labels' mentioned in `plan.md` are inconsistent with `spec.md` Assumptions. **This task file assumes `plan.md` has been corrected upstream by T003a-PLAN-CORRECT**. If not, execution must halt (T002-CHK).
- **Dependency Note**: Task T012-IMPL (loss_functions.py) is a strict prerequisite for T013 (train.py) and is not parallel-safe relative to T013.
- **Tie-Breaking Note**: Task T012-IMPL implements a deterministic tie-breaking rule (signal=0) as explicitly defined to satisfy `spec.md` Edge Cases.
- **Token Limit Note**: Task T005 sets `token_limit` to the integer `100000`. The spec's `[deferred]` is interpreted as 'unspecified in spec, defined in code'. T002-CHK validates this integer.
- **N=10 Note**: T019a strictly limits N=10 generation to the Self-Consistency benchmark (methodology applied to GSM8K and MMLU). MMLU/GSM8K single-pass uses single paths.
- **Manifest Note**: T039 clarifies that execution logs are not datasets and DO require checksumming in `artifacts/manifest_execution.json` (not `data/manifest.json`) for reproducibility under the `execution_logs` key.
- **Seed Note**: T027 enforces the constitutional requirement of a minimum number of seeds by failing if the count drops below the specified threshold.
- **N=2 Note**: T012-IMPL uses N=2 samples for the training proxy to ensure the 120-minute budget is met (Constitution VII). This is distinct from FR-003's N=10 for evaluation.
- **Phase 6 Note**: Phase 6 (T051-T058) addresses the specific philosophical concerns raised by the research-stage reviews (Ada Lovelace, Turing, Kahneman, Krakauer, Socrates, Wolfram) by operationalizing them into measurable metrics (Adaptation Coefficient, Prediction Consistency, Irreducibility, Rationalization Detection, Thermodynamic Cost, Subject/Object Distinction).
- **Review Resolution Note**: The philosophical concerns raised by reviewers are addressed by the rigorous statistical analysis of the measurable metrics defined in the spec (self-consistency, calibration, error detection) AND the new Phase 6 metrics.
- **OOM Note**: T014 and the Foundational phase notes strictly enforce a hard-fail on OOM. The system MUST NOT reduce recursion depth.
- **N=10 Note**: T019a strictly limits N=10 generation to the Self-Consistency benchmark (derived from GSM8K and MMLU). MMLU/GSM8K use single-pass.
- **Manifest Note**: T039 clarifies that execution logs are not datasets and do require checksumming in `artifacts/manifest_execution.json`.
- **Seed Note**: T027 enforces the constitutional requirement of a minimum number of seeds by failing if the count drops below the specified threshold.
- **N=2 Note**: T012-IMPL uses N=2 samples for the training proxy to ensure the 120-minute budget is met (Constitution VII).