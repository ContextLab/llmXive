# Tasks: llmXive follow-up: extending "MemGUI-Agent: An End-to-End Long-Horizon Mobile GUI Agent with Proacti"

**Input**: Design documents from `/specs/001-llmxive-long-horizon-context/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (adjusted from template to match plan.md structure)

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

**Revision Note**: The following tasks (T001a, T001b, T003) are marked as **[X]** because they were previously rejected due to lack of evidence. The original attempts were incomplete. A new task T001h is added to explicitly re-initialize the structure if the previous state is invalid.

- [X] T001a [P] **REJECTED/Obsolete**: Create `code/data_generation` directory AND create `__init__.py` (See T001h for redo)
- [X] T001b [P] **REJECTED/Obsolete**: Create `code/agents` directory AND create `__init__.py` (See T001h for redo)
- [X] T001c [P] **REJECTED/Obsolete**: Create `code/retrieval` directory AND create `__init__.py` (See T001h for redo)
- [X] T001d [P] **REJECTED/Obsolete**: Create `code/evaluation` directory AND create `__init__.py` (See T001h for redo)
- [X] T001e [P] **REJECTED/Obsolete**: Create `code/utils` directory AND create `__init__.py` (See T001h for redo)
- [X] T001f [P] **REJECTED/Obsolete**: Create `tests/` directory structure (See T001h for redo)
- [X] T001g [P] Create `code/main.py` (orchestration entry point)
- [X] T001h [P] **REDO**: Re-initialize project structure: Create `code/` subdirectories (`data_generation`, `agents`, `retrieval`, `evaluation`, `utils`) AND create `__init__.py` in EACH AND create `tests/` structure with `__init__.py` in `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/` AND create `tests/test_placeholder.py`. **Verify**: Run `ls -R code/ tests/` to confirm structure.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create base `ExecutionLog` data model (dataclass) for structured decision recording in `code/utils/execution_log.py`
- [X] T006 [P] Implement `code/utils/memory_profiler.py` to log peak memory footprint and inference latency to `data/synthetic_benchmark/memory_profile.json` (fields: `peak_memory_mb`, `latency_ms`, `agent_type`)
- [X] T007 [P] Implement `code/data_generation/validator.py` to check dependency links in trajectories
- [X] T008 [P] Implement `code/data_generation/coherence_validator.py` for semantic plausibility checks (automated only)
- [X] T002 [P] Create `code/requirements.txt` with pinned versions of: `transformers`, `sentence-transformers`, `datasets`, `statsmodels`, `scipy`, `accelerate`, `pandas`, `pytest`, `bitsandbytes`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`: Create `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections enforcing specific rules (e.g., line-length=88, target-version=py310)
- [X] T004 [P] Setup deterministic random seed utilities: Implement `code/utils/config.py` with `set_seed(seed: int)` function; verify that `main.py` (T001g) calls `set_seed()` at startup with a fixed seed (e.g., 42)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Ultra-Long Horizon Benchmark Generation (Priority: P1) 🎯 MVP

**Goal**: Construct a synthetic test dataset with a representative set of trajectories (multiple steps) containing explicit cross-app dependencies.

**Independent Test**: The generation script runs successfully, outputs a JSONL file, and the validation script asserts dependency links exist for >95% of trajectories.

**Scope Note**: Spec FR-001 mandates "≥50 trajectories". The Task MUST implement the Spec as written using streaming/batching to meet this target without hard failure.

**Testing Strategy**: TDD approach. T009/T010 are MANDATORY for MVP. Write tests first (expected to fail initially). These tests can be run in parallel *while failing* as part of the TDD cycle.

### Tests for User Story 1 (MANDATORY for MVP) ⚠️

- [X] T009 [P] [US1] Write unit test for dependency link injection logic in `tests/unit/data_generation/test_dependency_injection.py` (Expected to fail initially; parallel-safe while failing)
- [X] T010 [P] [US1] Write integration test for end-to-end trajectory generation in `tests/integration/data_generation/test_benchmark_gen.py` (Expected to fail initially; parallel-safe while failing)

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/data_generation/synthetic_benchmark.py`: Load `UltraData-SFT-Agent-2609` (split=train, streaming=True) to extract state templates; **implement a generator function that yields trajectories one-by-one using streaming/batching to avoid memory overflow**, accumulating results to disk, ensuring the loop continues until **≥50 valid trajectories are persisted** complying with Spec FR-001; output `data/synthetic_benchmark/trajectories.jsonl` with annotated "dependency links". **Do NOT fail loudly if 50 are not immediately reachable; instead, optimize the generation loop (streaming/batching) to meet the ≥50 target.** <!-- FAILED: unspecified -->
- [X] T012 [US1] Integrate `code/data_generation/coherence_validator.py` (automated) to validate dependency links and semantic consistency of the generated trajectories.
- [ ] T013 [US1] Implement `code/data_generation/expert_system_validator.py`: An automated expert-system validator to review a subset (≥10) for "semantically plausible" rating (FR-007); output review results to `data/synthetic_benchmark/review_results.json`. **Trigger Mechanism**: If automated check fails (score < 80%), the script MUST generate `needs_human_review.json` with schema `{trajectory_id: str, reason: str, timestamp: str}` AND **The system will exit with a non-zero error code indicating failure.** to signal the need for human intervention. **Note**: Implements the 'expert-system' path; T013b/T013c handle the 'human-in-the-loop' path.
- [ ] T013b [US1] Implement `code/data_generation/human_review_consumer.py`: A script to consume `needs_human_review.json` (if present), facilitate human review (e.g., via CLI or simple HTML report), and update `data/synthetic_benchmark/review_results.json` with human feedback; ensure the workflow completes the 'OR' clause of FR-007.
- [X] T013c [US1] Implement `code/data_generation/human_review_trigger.py`: A wrapper script that detects exit code 42 from T013 (or presence of `needs_human_review.json`) and automatically invokes T013b (human_review_consumer.py). **This task defines the missing 'producer' mechanism for the human review fallback.**

**Trigger Mechanism for Human Review**: The hand-off between T013 and T013b is defined by the `needs_human_review.json` file and the exit code 42. T013c automates this detection and invocation.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline ConAct Execution & Decay Measurement (Priority: P2)

**Goal**: Execute the standard MemGUI-SFT agent (CPU-only, 4-bit quantized) on the synthetic benchmark to measure information decay.

**Independent Test**: The baseline agent runs on the synthetic set without GPU acceleration, completes the execution log, and records step-level success/failure.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T014 [P] [US2] Contract test for agent execution interface in `tests/contract/test_agent_interface.py`
- [X] T015 [P] [US2] Integration test for baseline execution loop in `tests/integration/agents/test_baseline_execution.py`

### Implementation for User Story 2

- [X] T016 [P] [US2] Implement `code/agents/model_checker.py`: Perform a **static pre-verification** check against the "Verified datasets" block in **Plan.md** for "MemGUI-8B-SFT" or a pre-verified substitute. **Hardcode the list of allowed substitute model IDs**: `['microsoft/Phi-3-mini-4k-instruct', 'microsoft/Phi-3.5-mini-instruct']`. **Logic**: If "MemGUI-8B-SFT" is NOT found in the "Verified datasets" block of Plan.md, dynamically pivot to a substitute from the hardcoded list; **do NOT fail the build.**
- [X] T017 [P] [US2] Implement `code/agents/base_conact.py` wrapper for the model selected by T016 (static verification) using `bitsandbytes` 4-bit quantization.
- [X] T018 [US2] Configure `code/agents/base_conact.py` to force CPU-only execution (no CUDA) and manage memory footprint (<7GB).
- [X] T019 [P] [US2] Define `code/evaluation/interfaces.py` with `RunnerProtocol` interface (methods: `run_trajectory`, `get_logs`) to decouple baseline and recall runners. **Prerequisite: T005 (ExecutionLog data model) must be defined before this task.**
- [ ] T020 [US2] Implement `code/evaluation/runner.py` (ATOMIC): Execute the baseline agent on `data/synthetic_benchmark/trajectories.jsonl`, record the exact step where "information decay" causes a failure, **implement explicit attribution logic to attribute the failure to missing context from a step >10 indices prior**, and generate `data/results/baseline_execution_logs.jsonl`. Adhere to `RunnerProtocol` (T019). **Prerequisite: T012 must be completed to ensure valid dependency links. Prerequisite: T005 (ExecutionLog) must be complete.**
- [X] T021 [US2] Implement `code/evaluation/stats.py` preliminary analysis to calculate success rate trend (early vs late step).
- [X] T022 [US2] Add `code/utils/memory_profiler.py` (T006) integration to log peak memory for baseline runs.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Semantic Recall Augmentation & Efficacy Validation (Priority: P3)

**Goal**: Implement a lightweight "selective recall" module using `all-MiniLM-L-v2` to retrieve historical snippets and measure improvement.

**Independent Test**: The recall-enhanced agent runs on the same synthetic set, and the success rate in the early-step range is compared to the baseline.

**Statistical Methodology Note**: The Plan selects "Mixed-Effects Logistic Regression (GLMM)" as primary analysis. However, Spec FR-005 mandates Wilcoxon as primary. The tasks below implement the **Spec (Wilcoxon)** as the primary analysis to preserve requirement integrity. The Plan's GLMM preference is treated as a secondary or governance issue to be resolved separately, not by altering the task implementation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for retrieval query generation (no ground-truth leakage) in `tests/unit/retrieval/test_query_gen.py`
- [ ] T024 [P] [US3] Integration test for recall injection and re-execution in `tests/integration/retrieval/test_recall_injection.py`

### Implementation for User Story 3

- [X] T025 [P] [US3] Implement `code/retrieval/index_builder.py` to build an in-memory index from the agent's folded history.
- [X] T026 [P] [US3] Implement `code/retrieval/retriever.py` using `all-MiniLM-L6-v2` to generate embeddings for historical snippets.
- [X] T027 [US3] Implement `code/retrieval/retriever.py` to generate queries based *solely* on the current goal state (no ground-truth metadata).
- [X] T028 [US3] Implement `code/agents/recall_agent.py` to inject retrieved "memory flashes" into the prompt when similarity > threshold.
- [ ] T029 [US3] Implement `code/evaluation/recall_runner.py`: Execute the recall-enhanced agent on `data/synthetic_benchmark/trajectories.jsonl` adhering to `RunnerProtocol` (T019), generate `data/results/recall_execution_logs.jsonl`. **Implement as a subclass/adapter of the RunnerProtocol, not a direct extension of T020 file.**
- [~] T030 [US3] Implement `code/evaluation/log_merger.py`: Merge `data/results/baseline_execution_logs.jsonl` (from T020) and `data/results/recall_execution_logs.jsonl` (from T029) into `data/results/combined_logs.csv` (long-form: `trajectory_id`, `step`, `success`, `agent_type`, `latency_ms`). **Preserve hierarchical structure required for GLMM analysis (T032) and the justification task (T031b).**
- [ ] T031 [US3] Implement `code/evaluation/stats.py` to perform **Wilcoxon signed-rank test** as **Primary Analysis** comparing baseline vs recall success rates, complying with Spec FR-005.
- [ ] T031b [US3] Implement `code/evaluation/stats_doc.py`: Create a documentation file `docs/statistical_methodology_justification.md` explicitly justifying the override of the Plan's GLMM preference with Spec's Wilcoxon as primary. **This document MUST reference the specific sections in Plan.md and Spec.md that conflict and explain the decision to follow Spec FR-005.** Update plan.md to reflect this decision, resolving the conflict between Plan and Tasks.
- [ ] T032 [US3] Implement `code/evaluation/stats.py` to perform **Mixed-Effects Logistic Regression (GLMM)** as **Secondary/Validation Analysis**: Input `data/results/combined_logs.csv` (from T030); Model: `success ~ agent_type + (|trajectory_id)`; Output p-value and effect size. Comply with Plan methodology as secondary.
- [ ] T033 [US3] Integrate `code/utils/memory_profiler.py` (T006) to log overhead and ensure <10% latency increase (FR-006 / Constitution Principle VII).
- [ ] T034 [US3] Implement `code/evaluation/stats.py` to handle negative/shuffled controls to isolate retrieval variable.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates: Create `docs/benchmark_generation.md` with specific sections: 'Input Parameters', 'Output Schema' (as JSON Schema), 'Usage Examples' (as bash commands), ensuring deterministic content.
- [ ] T036 Code cleanup and refactoring of `code/evaluation/stats.py` for clarity
- [ ] T037 Performance optimization for retrieval index building (ensure it fits in RAM)
- [ ] T038 [P] Additional unit tests for edge cases in `tests/unit/retrieval/test_edge_cases.py`: Implement `test_ambiguous_similarity_raises` (assert `ValueError` is raised), `test_missing_context_fallback` (assert result is `None` or specific fallback behavior)
- [ ] T039 Run `code/quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately (T001h is the active task)
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T011) AND T012 (Coherence Validation) must be completed before T020
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 baseline results (via interface)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (TDD):
Task: "Write unit test for dependency link injection logic in tests/unit/data_generation/test_dependency_injection.py"
Task: "Write integration test for end-to-end trajectory generation in tests/integration/data_generation/test_benchmark_gen.py"

# Launch implementation after tests are written:
Task: "Implement code/data_generation/synthetic_benchmark.py..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001h)
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T009, T010, T011, T012, T013, T013b, T013c)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Baseline Execution)
 - Developer C: User Story 3 (Recall & Stats)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: The synthetic benchmark MUST use procedural generation based on verified templates; no fallback to synthetic mock data if the generator fails.
- **Resource Constraints**: All agent execution tasks MUST enforce CPU-only and 4-bit quantization to fit within the GB RAM limit.
- **Statistical Rigor**: The primary analysis MUST use Wilcoxon signed-rank test as per Spec FR-005, with GLMM as secondary validation.
- **Scope**: Tasks reflect the Spec's requirements (≥50 trajectories, Wilcoxon primary) while implementing the Plan's methodology where it does not conflict.
- **Reproducibility**: All validation (T013, T013b) is automated or human-in-the-loop as per FR-007.
- **Model Verification**: T016 enforces static pre-verification of models; runtime pivots are forbidden without verified substitutes.
- **TDD Enforcement**: T011 cannot be considered 'done' until T009 and T010 pass.
- **Human Review Trigger**: T013 exits with code 42 to trigger T013c, which invokes T013b.
- **Dependency Note**: T019 (RunnerProtocol) depends on T005 (ExecutionLog data model).