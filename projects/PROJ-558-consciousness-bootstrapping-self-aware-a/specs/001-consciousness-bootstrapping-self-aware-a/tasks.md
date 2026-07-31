# Tasks: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

**Input**: Design documents from `/specs/001-consciousness-bootstrapping-self-aware-a/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Critical Prerequisites**:
- **Spec Consistency**: The `spec.md` artifact contains `[deferred]` for the token limit in FR-002. The implementation tasks will use the value from `config.py` ([deferred] tokens).
- **Plan Consistency**: The `plan.md` artifact references "Teacher-Student Distillation". This is inconsistent with `spec.md` Assumptions which mandate an "internal self-consistency proxy". Implementation tasks will strictly follow `spec.md`, and T003-FIX will update `plan.md` to match.

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
- [X] T001c [P] Initialize a Python project with `torch` (CPU-only), `transformers`, `datasets`, `scikit-learn` in `requirements.txt`
- [X] T001d [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Prerequisite Validation & Plan Correction

- [ ] T003-FIX [P] **Plan Correction**: Update `plan.md` to remove references to "Teacher-Student Distillation" and replace them with "Internal Self-Consistency Proxy" as mandated by `spec.md` Assumptions. **Logic**: Search for "Teacher-Student" or "Pre-computed Teacher Labels" in `plan.md` and replace with the correct methodology described in `spec.md`. **Action**: Commit the corrected `plan.md`. **Dependency**: None. **Note**: This task MUST be completed before T004-IMPL to ensure the pipeline does not fail on the plan validation gate.
- [ ] T002-CHK [P] **Validation Script**: Create `scripts/validate_config.py` to check `code/utils/config.py`. **Logic**: Verify `token_limit` is present. If `token_limit` is missing or `None`, log CRITICAL error and exit 1. If `token_limit` is an integer, log SUCCESS. **Dependency**: None.

### Data Loading & Configuration

- [ ] T005 [P] **Implementation**: Implement config.py to manage hyperparameters (seed, batch size, recursion depth=2, learning rate). **Constraint**: `token_limit` MUST be initialized to the integer `100000` (100k) as per Constitution Principle VII and FR-002. **Dependency**: None.
- [ ] T004-IMPL [P] [US1] **Implementation**: Implement `data_loader.py` to fetch the 'arXiv' subset of the Pile dataset via HuggingFace `datasets` API. **Logic**: Use `datasets.load_dataset("pile", split="train")` and filter for items where the text starts with 'arXiv' (or use the specific `arxiv` subset if available in the library version). **Constraint**: Truncate to `token_limit` (100k tokens). Save to `data/raw/pile_arxiv_truncated.json`. **Dependency**: Requires T005. **Note**: This task is parallel-safe relative to other data loaders.
- [ ] T004b-GSM8K [P] [US2] **Implementation**: Implement `data_loader.py` (additional function) to fetch GSM8K dataset via HuggingFace `datasets` API. **Action**: Save to `data/raw/gsm8k.json` with checksum in `data/manifest.json`. **Dependency**: None. **Note**: This task is parallel-safe relative to T004-IMPL and T004b-MMLU.
- [ ] T004b-MMLU [P] [US2] **Implementation**: Implement `data_loader.py` (additional function) to fetch MMLU dataset via HuggingFace `datasets` API. **Action**: Save to `data/raw/mmlu.json` with checksum in `data/manifest.json`. **Dependency**: None. **Note**: This task is parallel-safe relative to T004-IMPL and T004b-GSM8K.
- [ ] T004c-SELFCONS [P] [US2] **Implementation**: Implement `data_loader.py` (additional function) to fetch the 'self_consistency' dataset. **Logic**: If a direct dataset exists (e.g., `lukaemon/mmlu` or a specific self-consistency benchmark), use it. If not, derive it from GSM8K by generating multiple reasoning paths for a subset of questions as per FR-003. **Action**: Save to `data/raw/self_consistency.json` with checksum in `data/manifest.json`. **Dependency**: None. **Note**: This task is parallel-safe relative to other data loaders.
- [X] T006 [P] Create base `ModelCheckpoint` and `EvaluationResult` entities in `code/models/` and `code/evaluation/` in a format suitable for serialization (e.g., dataclasses, Pydantic, dicts).
- [X] T007 [P] Implement `base_llama.py` wrapper for a small transformer (<300M params) in `code/models/base_llama.py`. **Note**: Use TinyLlama as per Spec US-01.
- [X] T008 [P] Setup error handling and logging infrastructure in `code/utils/logging.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Train Self-Referential Model (Priority: P1) 🎯 MVP

**Goal**: Construct a TinyLlama-based model with temporal recursive self-attention and train it on a sampled Pile subset to produce recursive and baseline checkpoints.

**Independent Test**: The training pipeline executes on GitHub Actions CPU runner, produces two checkpoints, and completes within 120 minutes without OOM.

**NOTE on Spec vs Plan Divergence**: The `plan.md` Summary references "pre-computed teacher model labels". This task strictly implements the `spec.md` requirement for an **internal self-consistency proxy** (derived from N=5 model generations) to avoid tautology. The plan discrepancy is resolved by T003-FIX.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These are **Test Definition** tasks. They create the test file content. The CI runner executes these tests **AFTER** the implementation tasks (T011-T015) are merged. **NOTE**: The [P] tag on Test Definition tasks applies only to file creation. Test execution will fail if the implementation code (T011-T015) is not yet present.

- [X] T009 [P] [US1] **Definition**: Create unit test file `tests/unit/models/test_recursive_attention.py` with test cases: `test_shape_consistency` (checks output shape matches input), `test_attention_mask_propagation` (checks mask handling). (Expected to fail initially)
- [X] T010 [P] [US1] **Definition**: Create unit test file `tests/unit/training/test_loss_functions.py` with test cases: `test_joint_loss_computation` (checks loss calculation with dummy tensors), `test_confidence_proxy_logic` (checks single-path proxy logic). (Expected to fail initially)

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `recursive_llama.py` with temporal recursive self-attention module (FR-001) in `code/models/recursive_llama.py`
- [ ] T012-IMPL [US1] **Implementation**: Implement `loss_functions.py` with joint loss (cross-entropy + confidence-prediction). **Implementation Logic**: Define a function `compute_confidence_loss(model, batch, temperature=0.7, top_p=0.9, max_tokens=256, n_samples=5)` that: (1) Generates N=5 reasoning paths per training item using the current model state with the specified parameters; (2) Computes the majority vote of these paths to determine a binary 'proxy correctness' signal; (3) **Tie-Breaking Rule**: Define a deterministic tie-breaking rule (specifically: prefer the first generated path) to satisfy spec Edge Cases for handling ties or no-majority scenarios. (4) Compare the model's predicted confidence for the final answer against this proxy signal. **Note**: This is a self-referential training signal as per Spec Assumptions. The 'correctness' is defined by the model's own majority vote. **Dependency**: Requires T011 (base_llama.py). **Note**: This task defines the function logic; the actual generation occurs during the training loop in T013.
- [X] T013 [US1] Implement `train.py` script to train both recursive and baseline models with fixed seeds (US-01) in `code/training/train.py`. **Dependency**: Requires T012-IMPL to be complete. **Note**: This task is NOT parallel-safe relative to T012-IMPL.
- [ ] T014 [US1] Add validation to `train.py` to prevent recursion depth > 2. **MUST** implement hard-fail: if OOM or depth violation occurs, log error and exit with non-zero code. **MUST NOT** automatically reduce depth.
- [X] T015 [US1] Add logging for training progress and OOM detection in `code/training/train.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Meta-Cognitive Metrics (Priority: P2)

**Goal**: Run trained models against benchmarks to measure self-consistency, error detection, and uncertainty calibration.

**Independent Test**: Evaluation script ingests checkpoints, generates predictions, and outputs a JSON with raw metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for self-consistency majority vote logic (tie-breaking rule) in `tests/unit/evaluation/test_metrics.py` (Test: `test_majority_vote_tie_break`)
- [X] T017 [P] [US2] Unit test for Brier score and ECE calculation in `tests/unit/evaluation/test_metrics.py` (Test: `test_brier_score_calc`, `test_ece_calc`)

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement `metrics.py` to calculate self-consistency, ROC-AUC, Brier score, and ECE (FR-003, FR-004) in `code/evaluation/metrics.py`. **CRITICAL**: Implement `calculate_error_detection_calibration` function internally to compute ECE. **Output Requirement**: MUST output the final computed metrics (Brier score, ECE, ROC-AUC) AND the raw binning data to `data/processed/ece_binning.json` to satisfy Constitution Principle IV (Single Source of Truth).
- [ ] T019a [US2] Implement `run_benchmarks.py` to generate **multiple reasoning paths per question** for the **Self-Consistency Benchmark dataset** (FR-003) using temperature=0.7, top_p=0.9, and a fixed seed per run. **Dependency**: Requires T004c-SELFCONS to be complete. **Clarification**: This task implements the N=10 protocol strictly for the Self-Consistency benchmark dataset. **Action**: Implement tie-breaking rule (prefer first generated path) as per spec Edge Cases. <!-- FAILED: unspecified -->
- [ ] T019b [US2] Implement `run_benchmarks.py` to run standard MMLU/GSM8K inference (single path) for accuracy baseline. **Dependency**: Requires T004b-GSM8K and T004b-MMLU to be complete.
- [X] T020 [US2] Implement logic to produce 'shuffled-attention' control dataset for isolation of temporal recursion effects (US-02) in `code/evaluation/run_benchmarks.py`. **Dependency**: Requires T004b-GSM8K and T004b-MMLU.
- [X] T021 [US2] Add contract validation to ensure output JSON matches `EvaluationResult` schema in `code/evaluation/run_benchmarks.py`
- [X] T022 [US2] Add logging for benchmark execution and metric aggregation in `code/evaluation/run_benchmarks.py`

**Checkpoint**: At this point, At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Analysis and Sensitivity Testing (Priority: P3)

**Goal**: Perform paired t-tests across multiple seeds and sensitivity analysis to determine statistical significance.

**Independent Test**: Analysis script processes evaluation outputs, performs tests, and generates a report with p-values and plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for paired t-test and Bonferroni correction logic in `tests/unit/analysis/test_stats.py` (Test: `test_paired_ttest`, `test_bonferroni_correction`)

### Implementation for User Story 3

- [X] T024 [P] [US3] Implement `stats.py` to perform paired t-tests, Cohen's d, confidence intervals, and Bonferroni correction (FR-005, FR-007) in `code/analysis/stats.py`. **Must include**: Logic to calculate the **percentage difference in self-consistency scores** between recursive and baseline models (SC-001) and output to `artifacts/results/statistical_report.json`.
- [X] T025 [US3] **Implementation**: Implement sensitivity analysis sweep for confidence thresholds across the **specific discrete set of values** {, 0.5, 0.6} (FR-006) and output results to `artifacts/results/sensitivity_analysis.csv` (or JSON) reporting the variation in error rates for each threshold (to satisfy FR-006's requirement to report variation) in `code/analysis/stats.py`. **Must also**: Integrate the `calculate_error_detection_calibration` output from T018 (imported from `code/evaluation/metrics.py`) to generate the sensitivity plot for the calibration curve across thresholds. **Dependency**: Requires T018 (metrics calculation logic) and T020 (shuffled-attention control) to be complete. **Note**: T025 is now unblocked and depends on T018 and T020.
- [X] T026 [US3] Implement report generation to output `StatisticalReport` with p-values, effect sizes, confidence intervals, sensitivity plots, and the percentage difference metric (US-03) in `code/analysis/stats.py`. **Must define**: JSON schema for the report.
- [X] T027 [US3] Add logic to exclude invalid seeds (non-converged confidence loss) from statistical comparison (Edge Case) in `code/analysis/stats.py`. **Constraint**: If excluding seeds results in an insufficient number of valid seeds, the script MUST fail with a clear error message. to satisfy Constitution Principle VI (Statistical Rigor).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Research-Stage Review Resolution (Documentation Only)

**Purpose**: Address the critical contradiction between `plan.md` (Teacher-Student Distillation) and `spec.md` (Internal Self-Consistency Proxy) by updating documentation to reflect the correct implementation. This phase resolves the Plan/Spec alignment issue found in the current analysis.

### Addressing Plan/Spec Contradiction

- [X] T060 [US3] **Documentation**: Update `research.md` to formally document the operationalization of the training signal. **Logic**: Create a new section "Training Signal Methodology" in `research.md` that explicitly states the system uses an **internal self-consistency proxy** (N=5 generations, majority vote) as per `spec.md` Assumptions, and explicitly notes that the previous mention of "Teacher-Student Distillation" in `plan.md` was an error corrected by T003-FIX. **Action**: Draft a PR description or markdown update that resolves the "Plan vs Spec" contradiction by confirming the internal proxy approach in `research.md`. **Dependency**: Requires T024 (stats.py) to have a defined output schema to reference. **Note**: This task resolves the "unapproved scope" concern by moving the discussion to the research documentation layer, not the code layer.

---

## Phase 7: Philosophical & Operational Clarification (Review Response)

**Purpose**: Address the fundamental concerns raised by reviewers regarding the nature of "self-awareness," the distinction between simulation and origin, and the operationalization of intelligence vs. description.

### Addressing "Simulation vs. Origin" (Lovelace, Socrates)
*Reviewers concern: The system may merely execute pre-ordained patterns of introspection without originating self-awareness.*

- [ ] T070 [P] [Research] **Documentation**: Update `research.md` to explicitly define the operational hypothesis: "We define 'bootstrapped self-awareness' not as the emergence of a metaphysical subject, but as the measurable increase in **behavioral adaptation** (error correction) driven by the internal consistency proxy." **Action**: Add a section "Operational Definitions" distinguishing between "Self-Description" (static reporting) and "Self-Modification" (performance improvement based on internal state).
- [ ] T071 [P] [Research] **Documentation**: Update `research.md` to address the "Jacquard-loom" analogy. **Action**: Explicitly state that the "cards" (architecture) are fixed, but the "weaving" (weights) is dynamic. The research question is whether the recursive loop allows the system to *re-weave* its own pattern (weights) in a way that a non-recursive system cannot, effectively "ordering itself" via the gradient signal derived from its own output distribution.

### Addressing "Intelligence vs. Description" (Krakauer)
*Reviewers concern: A system may describe itself elegantly without improving problem-solving capacity.*

- [ ] T074 [P] [US3] **Implementation**: Add a "Behavioral Adaptation" metric to `stats.py`. **Logic**: Compare the performance of the Recursive Model vs. Baseline *specifically* on items where the internal proxy flagged high uncertainty. **Action**: If the Recursive Model improves on these "hard" items significantly more than the Baseline, it proves the self-model is driving adaptation, not just description.
- [ ] T075 [P] [Research] **Documentation**: Update `research.md` to include a "Falsification Criterion" section. **Action**: Explicitly state: "The hypothesis is falsified if the Recursive Model shows no statistically significant improvement in accuracy on high-uncertainty items compared to the Baseline, despite showing improved confidence calibration. [UNRESOLVED-CLAIM: c_ca15f1c7 — status=not_enough_info]"

### Addressing "Thermodynamic Cost" (Krakauer, Wolfram)
*Reviewers concern: Agency requires a cost; the system must pay a "metabolic" price for maintaining the self-model.*

- [ ] T076 [P] [US1] **Implementation**: Add a "Computational Cost" metric to `train.py`. **Logic**: Measure the additional FLOPs and memory usage introduced by the recursive module (depth=2) vs. the baseline. **Action**: Log this to `artifacts/results/cost_analysis.json`.
- [ ] T077 [P] [US3] **Implementation**: Update `stats.py` to calculate an "Efficiency Ratio". **Logic**: (Performance Gain) / (Computational Cost). **Action**: If the ratio is negative or negligible, the "bootstrapping" is not cost-effective. This addresses the "budget constraint" concern.
- [ ] T078 [P] [Research] **Documentation**: Update `research.md` to frame the results in terms of "Computational Irreducibility" (Wolfram). **Action**: Discuss whether the recursive path reveals patterns that are not reducible to the baseline, effectively "just running it" to see what emerges.

### Addressing "Simulation vs. Phenomenon" (Turing, Kahneman)
*Reviewers concern: The system may simulate introspection without grounding it in external truth or penalizing false reports.*

- [ ] T079 [P] [US2] **Implementation**: Implement a "Prediction Penalty" mechanism in `code/evaluation/metrics.py`. **Logic**: For each generated path, record the model's predicted confidence *before* generation. Compare this prediction against the *actual* correctness of the path (determined by external ground truth in GSM8K/MMLU). **Action**: Calculate a "Calibration Gap" metric (Brier score of the prediction vs. reality) and ensure the loss function in T012-IMPL explicitly penalizes divergence between predicted confidence and actual correctness, preventing the model from "lying" about its state.
- [ ] T080 [P] [Research] **Documentation**: Update `research.md` to address the "System 1" bias (Kahneman). **Action**: Add a section "Post-Hoc Rationalization vs. Real-Time Monitoring" explaining how the internal proxy (N=5 majority vote) serves as an external benchmark for the model's own confidence, distinguishing between a coherent story and a verifiable mechanical procedure.

### Addressing "Origin of Operations" (Lovelace, Socrates)
*Reviewers concern: The engine executes orders but cannot originate the self-model; we must distinguish between executing a pattern and originating a new one.*

- [ ] T081 [P] [US3] **Implementation**: Add a "Novelty Detection" metric to `stats.py`. **Logic**: Compare the distribution of "reasoning paths" generated by the Recursive Model vs. the Baseline. **Action**: If the Recursive Model produces a statistically significant higher variance in reasoning strategies (not just answers) on hard problems, it suggests the recursion is generating *novel combinations* rather than cycling through latent patterns. Output to `artifacts/results/novelty_analysis.json`.
- [ ] T082 [P] [Research] **Documentation**: Update `research.md` to address the "Subject vs. Object" paradox (Socrates). **Action**: Explicitly state that the "Subject" in this experiment is the *gradient signal* derived from the self-consistency proxy, which acts as an external judge to the "Object" (the current weights). The "awareness" is the system's ability to minimize the error of this internal judge, effectively "knowing the good" by aligning with the proxy's majority vote.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` including the new statistical report format, the definitions of the implemented metrics (self-consistency, calibration, error detection), and the "Training Signal Methodology" section explaining the plan/spec correction.
- [ ] T038 [P] Run `ruff check` and `black --check` on the entire `code/` directory; CI must fail if any lint/format errors exist.
- [ ] T039 [P] Run memory profiling on the training script (`train.py`) with max batch size; verify peak RSS < 7GB and log result to `artifacts/results/memory_profile.log`. **Note**: While the spec requires the run to fail if the limit is exceeded, this task logs profiling data for review. If peak RSS > 7GB, the run MUST fail as per Edge Cases. **Clarification**: This log is an execution artifact, not a dataset, and does not require checksumming in `data/manifest.json`.
- [X] T040 [P] Additional unit tests for the new statistical metrics in `tests/unit/analysis/test_stats.py` and `tests/unit/evaluation/test_metrics.py`.
- [ ] T041 [P] Run `quickstart.md` validation to ensure all artifacts are generated correctly.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Note**: T003-FIX and T002-CHK must pass (valid config, plan corrected) before T004-IMPL.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Phase 6 (Review Resolution)**: Depends on US1, US2, and US3 completion. Most tasks in Phase 6 require the statistical report infrastructure from US3.
- **Phase 7 (Philosophical Clarification)**: Depends on Phase 3 (US2/US3) for the metrics required to calculate the "Behavioral Adaptation" and "Efficiency Ratio".
- **Phase N (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **Note**: T012-IMPL is blocked by T011. T019a is blocked by T004c-SELFCONS.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT** T004-IMPL, T004b-GSM8K, T004b-MMLU, T004c-SELFCONS which are parallel-safe relative to each other.
- Once Foundational phase completes, US1, US2, and US3 can start in parallel (if team capacity allows)
- **Note**: T012-IMPL is NOT parallel-safe relative to T013.
- **Note**: Phase 6 and 7 tasks can be implemented independently as documentation and metric updates.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories) - **Note**: T003-FIX and T002-CHK must pass (valid config, plan corrected) before T004-IMPL.
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. **Add Phase 6**: Implement specific review resolutions to address the Plan/Spec contradiction regarding the training signal.
6. **Add Phase 7**: Implement the philosophical and operational clarifications (Behavioral Adaptation, Efficiency Ratio) to address the "Simulation vs. Origin" and "Intelligence vs. Description" concerns.
7. Final Validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Training)
 - Developer B: User Story 2 (Evaluation)
 - Developer C: User Story 3 (Analysis)
 - Developer D: Phase 6 (Review Resolution Documentation) - *Can start once T024 is drafted*
 - Developer E: Phase 7 (Philosophical Metrics) - *Can start once T018/T024 are drafted*

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
- **Critical Constraint**: All tasks must run on CPU-only CI with a limited number of cores and memory. No GPU, no 8-bit quantization.
- **Scope Note**: The 'Teacher-Student Distillation' and 'Pre-computed Teacher Labels' mentioned in `plan.md` are inconsistent with `spec.md` Assumptions. **This task file assumes `plan.md` has been corrected upstream by T003-FIX**. If not, execution must halt (T002-CHK).
- **Dependency Note**: Task T012-IMPL (loss_functions.py) is a strict prerequisite for T013 (train.py) and is not parallel-safe relative to T013.
- **Tie-Breaking Note**: Task T012-IMPL implements a deterministic tie-breaking rule (prefer first generated path) as explicitly defined to satisfy `spec.md` Edge Cases.
- **Token Limit Note**: Task T004-IMPL reads the token limit from `config.py` ([deferred]). If the value is missing or 'deferred', the task fails. T005 sets the value to [deferred].
- **Phase 6 Note**: Tasks T060 is a direct response to the "Plan vs Spec" contradiction and is essential for the scientific validity of the project. It transforms the project from a simple benchmark run into a rigorous investigation by documenting the hypotheses and correcting the methodology description.
- **Review Resolution Note**: The philosophical concerns raised by reviewers are addressed by the rigorous statistical analysis of the measurable metrics defined in the spec (self-consistency, calibration, error detection) AND the new documentation in Phase 6 and 7. No additional "Philosophical Grounding" metrics are implemented beyond these operationalized tests.
- **OOM Note**: T014 and the Foundational phase notes strictly enforce a hard-fail on OOM. The system MUST NOT reduce recursion depth.
- **N=10 Note**: T019a strictly limits N=10 generation to the Self-Consistency benchmark. MMLU/GSM8K use single-pass.
- **Manifest Note**: T039 clarifies that execution logs are not datasets and do not require checksumming in `data/manifest.json`.
- **Philosophical Note**: Phase 7 tasks (T070-T071, T074-T078) are explicitly designed to operationalize the "Simulation vs. Origin" and "Intelligence vs. Description" debates into measurable metrics (Behavioral Adaptation, Efficiency Ratio) and documentation. This ensures the project addresses the core scientific questions raised by the reviewers without resorting to metaphysical speculation.
- **Seed Note**: T027 enforces the constitutional requirement of 5 seeds by failing if the count drops below 5.
- **New Review Tasks**: Tasks T079, T080, T081, T082 are added to specifically address the "Prediction Penalty" (Turing), "System 1 Bias" (Kahneman), "Novelty Detection" (Lovelace), and "Subject/Object Paradox" (Socrates) concerns raised in the prior research-stage reviews. These tasks ensure the project moves beyond mere simulation to measurable, falsifiable scientific claims.
