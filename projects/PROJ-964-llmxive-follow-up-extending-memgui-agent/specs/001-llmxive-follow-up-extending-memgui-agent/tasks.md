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

- [ ] T001a [P] Create `code/data_generation` directory
- [ ] T001b [P] Create `code/agents` directory
- [ ] T001c [P] Create `code/retrieval` directory
- [ ] T001d [P] Create `code/evaluation` directory
- [ ] T001e [P] Create `code/utils` directory
- [ ] T001f [P] Create `tests/` directory structure (`unit`, `integration`, `contract`)
- [X] T001g [P] Create `code/main.py` (orchestration entry point)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create base `ExecutionLog` data model (dataclass) for structured decision recording in `code/utils/execution_log.py`
- [ ] T006 [P] Implement `code/utils/memory_profiler.py` to log peak memory footprint and inference latency to `data/synthetic_benchmark/memory_profile.json` (fields: `peak_memory_mb`, `latency_ms`, `agent_type`)
- [ ] T007 [P] Implement `code/data_generation/validator.py` to check dependency links in trajectories
- [ ] T008 [P] Implement `code/data_generation/coherence_validator.py` for semantic plausibility checks (automated only)
- [ ] T002 [P] Create `code/requirements.txt` with pinned versions of: `transformers`, `sentence-transformers`, `datasets`, `statsmodels`, `scipy`, `accelerate`, `pandas`, `pytest`, `bitsandbytes`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`
- [ ] T004 [P] Setup deterministic random seed utilities for reproducible synthetic generation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Ultra-Long Horizon Benchmark Generation (Priority: P1) 🎯 MVP

**Goal**: Construct a synthetic test dataset with a representative set of trajectories (multiple steps) containing explicit cross-app dependencies.

**Independent Test**: The generation script runs successfully, outputs a JSONL file, and the validation script asserts dependency links exist for >95% of trajectories.

**Scope Note**: Spec FR-001 mandates "≥50 trajectories". The Plan notes a reduction to a feasible limit for memory constraints, but the Task MUST implement the Spec as written. If resources prevent 50, the script must fail loudly with a `RESOURCE_LIMIT` error code, preserving the requirement rather than weakening it.

**Testing Strategy**: TDD approach. T009/T010 are MANDATORY for MVP. Write tests first (expected to fail), then implement.

### Tests for User Story 1 (MANDATORY for MVP) ⚠️

- [ ] T009 [P] [US1] Write unit test for dependency link injection logic in `tests/unit/data_generation/test_dependency_injection.py` (Expected to fail initially)
- [ ] T010 [P] [US1] Write integration test for end-to-end trajectory generation in `tests/integration/data_generation/test_benchmark_gen.py` (Expected to fail initially)

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/data_generation/synthetic_benchmark.py`: Load `UltraData-SFT-Agent-2609` (split=train, streaming=True) to extract state templates; implement procedural generation logic to chain workflows ensuring critical info is available only several steps prior; output `data/synthetic_benchmark/trajectories.jsonl` with annotated "dependency links"; generate **≥50 synthetic trajectories** complying with Spec FR-001. **If resource constraints prevent generating 50, the script must fail loudly with a `RESOURCE_LIMIT` error code.**
- [ ] T012 [US1] Integrate `code/data_generation/coherence_validator.py` (automated) to validate dependency links and semantic consistency of the generated trajectories.
- [ ] T013 [US1] Implement `code/data_generation/expert_system_validator.py`: An automated expert-system validator to review a subset (≥10) for "semantically plausible" rating (FR-007); output review results to `data/synthetic_benchmark/review_results.json`. **Note**: Implements the 'expert-system' path explicitly allowed by FR-007 ('human-in-the-loop OR expert-system'). The task must ensure the 'human-in-the-loop' option remains a valid, active path in the spec as written, and if the expert-system fails, the system must be able to trigger human review as per the 'OR' clause.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline ConAct Execution & Decay Measurement (Priority: P2)

**Goal**: Execute the standard MemGUI-SFT agent (CPU-only, 4-bit quantized) on the synthetic benchmark to measure information decay.

**Independent Test**: The baseline agent runs on the synthetic set without GPU acceleration, completes the execution log, and records step-level success/failure.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T014 [P] [US2] Contract test for agent execution interface in `tests/contract/test_agent_interface.py`
- [ ] T015 [P] [US2] Integration test for baseline execution loop in `tests/integration/agents/test_baseline_execution.py`

### Implementation for User Story 2

- [ ] T016 [P] [US2] Implement `code/agents/model_checker.py` to perform a **static pre-verification** check against the "Verified datasets" block in Plan/Spec for "MemGUI-8B-SFT" or a pre-verified substitute (e.g., "microsoft/Phi-3-mini-4k-instruct"). **Fail loud** if no pre-verified model is found; do NOT pivot at runtime.
- [ ] T017 [P] [US2] Implement `code/agents/base_conact.py` wrapper for the model selected by T016 (static verification) using `bitsandbytes` 4-bit quantization.
- [ ] T018 [US2] Configure `code/agents/base_conact.py` to force CPU-only execution (no CUDA) and manage memory footprint (<7GB).
- [ ] T019 [P] [US2] Define `code/evaluation/interfaces.py` with `RunnerProtocol` interface (methods: `run_trajectory`, `get_logs`) to decouple baseline and recall runners.
- [ ] T020 [US2] Implement `code/evaluation/runner.py` (ATOMIC): Execute the baseline agent on `data/synthetic_benchmark/trajectories.jsonl`, record the exact step where "information decay" causes a failure, **implement explicit attribution logic to attribute the failure to missing context from a step >10 indices prior **, and generate `data/results/baseline_execution_logs.jsonl`. Adhere to `RunnerProtocol` (T019).
- [ ] T021 [US2] Implement `code/evaluation/stats.py` preliminary analysis to calculate success rate trend (early vs late step).
- [ ] T022 [US2] Add `code/utils/memory_profiler.py` (T006) integration to log peak memory for baseline runs.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Semantic Recall Augmentation & Efficacy Validation (Priority: P3)

**Goal**: Implement a lightweight "selective recall" module using `all-MiniLM-L6-v2` to retrieve historical snippets and measure improvement.

**Independent Test**: The recall-enhanced agent runs on the same synthetic set, and the success rate in the early-step range is compared to the baseline.

**Statistical Methodology Note**: The Plan selects "Mixed-Effects Logistic Regression (GLMM)" as primary analysis. However, Spec FR-005 mandates Wilcoxon as primary. The tasks below implement the **Spec (Wilcoxon)** as the primary analysis to preserve requirement integrity. The Plan's GLMM preference is treated as a secondary or governance issue to be resolved separately, not by altering the task implementation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for retrieval query generation (no ground-truth leakage) in `tests/unit/retrieval/test_query_gen.py`
- [ ] T024 [P] [US3] Integration test for recall injection and re-execution in `tests/integration/retrieval/test_recall_injection.py`

### Implementation for User Story 3

- [ ] T025 [P] [US3] Implement `code/retrieval/index_builder.py` to build an in-memory index from the agent's folded history.
- [ ] T026 [P] [US3] Implement `code/retrieval/retriever.py` using `all-MiniLM-L6-v2` to generate embeddings for historical snippets.
- [ ] T027 [US3] Implement `code/retrieval/retriever.py` to generate queries based *solely* on the current goal state (no ground-truth metadata).
- [ ] T028 [US3] Implement `code/agents/recall_agent.py` to inject retrieved "memory flashes" into the prompt when similarity > threshold.
- [ ] T029 [US3] Implement `code/evaluation/recall_runner.py`: Execute the recall-enhanced agent on `data/synthetic_benchmark/trajectories.jsonl` adhering to `RunnerProtocol` (T019), generate `data/results/recall_execution_logs.jsonl`. **Implement as a subclass/adapter of the RunnerProtocol, not a direct extension of T020 file.**
- [ ] T030 [US3] Implement `code/evaluation/log_merger.py`: Merge `data/results/baseline_execution_logs.jsonl` (from T020) and `data/results/recall_execution_logs.jsonl` (from T029) into `data/results/combined_logs.csv` (long-form: `trajectory_id`, `step`, `success`, `agent_type`, `latency_ms`). **Preserve hierarchical structure required for GLMM analysis.**
- [ ] T031 [US3] Implement `code/evaluation/stats.py` to perform **Wilcoxon signed-rank test** as **Primary Analysis** comparing baseline vs recall success rates, complying with Spec FR-005.
- [ ] T032 [US3] Implement `code/evaluation/stats.py` to perform **Mixed-Effects Logistic Regression (GLMM)** as **Secondary/Validation Analysis**: Input `data/results/combined_logs.csv` (from T030); Model: `success ~ agent_type + (1|trajectory_id)`; Output p-value and effect size. Comply with Plan methodology as secondary.
- [ ] T033 [US3] Integrate `code/utils/memory_profiler.py` (T006) to log overhead and ensure <10% latency increase (FR-006 / Constitution Principle VII).
- [ ] T034 [US3] Implement `code/evaluation/stats.py` to handle negative/shuffled controls to isolate retrieval variable.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` for the synthetic benchmark generation logic
- [ ] T036 Code cleanup and refactoring of `code/evaluation/stats.py` for clarity
- [ ] T037 Performance optimization for retrieval index building (ensure it fits in RAM)
- [ ] T038 [P] Additional unit tests for edge cases (ambiguous similarity scores, missing context) in `tests/unit/`
- [ ] T039 Run `code/quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
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

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T009, T010, T011, T012, T013)
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
- **Reproducibility**: All validation (T013) is automated (expert-system) but must preserve the 'human-in-the-loop' option as per FR-007.
- **Model Verification**: T016 enforces static pre-verification of models; runtime pivots are forbidden.