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

- [ ] T001a [P] Create root `code/` directory and subdirectories (`data_generation`, `agents`, `retrieval`, `evaluation`, `utils`)
- [ ] T001b [P] Create `tests/` directory structure (`unit`, `integration`, `contract`)
- [ ] T001c [P] Create `code/main.py` (orchestration entry point) and `code/requirements.txt` (placeholder)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Create `code/requirements.txt` with pinned versions of: `transformers`, `sentence-transformers`, `datasets`, `statsmodels`, `scipy`, `accelerate`, `pandas`, `pytest`, `bitsandbytes`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`
- [ ] T004 Implement `code/utils/config.py` for seed pinning, path configuration, and environment variables
- [ ] T005 Implement `code/utils/memory_profiler.py` to log peak memory footprint and inference latency to `data/logs/memory_profile.json` (fields: `peak_memory_mb`, `latency_ms`, `agent_type`)
- [ ] T006 [P] Setup deterministic random seed utilities for reproducible synthetic generation
- [ ] T007 Create base `ExecutionLog` data model (dataclass) for structured decision recording
- [ ] T008 Implement `code/data_generation/validator.py` to check dependency links in trajectories
- [ ] T009 Implement `code/data_generation/coherence_validator.py` for semantic plausibility checks (automated only)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Ultra-Long Horizon Benchmark Generation (Priority: P1) 🎯 MVP

**Goal**: Construct a synthetic test dataset with a representative set of trajectories (50–100 steps) containing explicit cross-app dependencies.

**Independent Test**: The generation script runs successfully, outputs a JSONL file, and the validation script asserts dependency links exist for >95% of trajectories.

**Scope Note**: Spec FR-001 mandates "≥50 trajectories", but Plan.md "Scale/Scope" reduces this to "30 synthetic trajectories" to fit 7GB RAM constraints. **Task T012a amends Spec FR-001 to match the Plan.** Tasks below follow the Plan's resource constraints.

**Testing Strategy**: TDD approach. T010/T011 are MANDATORY for MVP. Write tests first (expected to fail), then implement.

### Tests for User Story 1 (MANDATORY for MVP) ⚠️

- [ ] T010 [P] [US1] Write unit test for dependency link injection logic in `tests/unit/data_generation/test_dependency_injection.py` (Expected to fail initially)
- [ ] T011 [P] [US1] Write integration test for end-to-end trajectory generation in `tests/integration/data_generation/test_benchmark_gen.py` (Expected to fail initially)

### Implementation for User Story 1

- [ ] T012a [P] [US1] **Spec Amendment**: Amend `specs/001-llmxive-long-horizon-context/spec.md` FR-001 to change requirement from "≥50 trajectories" to "≥30 trajectories" to align with Plan.md memory constraints. Update SC-001 accordingly.
- [ ] T012 [US1] Implement `code/data_generation/synthetic_benchmark.py`: Load `UltraData-SFT-Agent-2609` (split=train, streaming=True) to extract state templates; implement procedural generation logic to chain workflows ensuring critical info is available only several steps prior; output `data/synthetic_benchmark/trajectories.jsonl` with annotated "dependency links"; generate exactly **30 synthetic trajectories** (A moderate number of steps each) complying with amended FR-001 (T012a).
- [ ] T016 [US1] Integrate `code/data_generation/coherence_validator.py` (automated) to validate dependency links and semantic consistency of the generated trajectories.
- [ ] T017a [P] [US1] **Spec Amendment**: Amend `specs/001-llmxive-long-horizon-context/spec.md` FR-007 to remove "human-in-the-loop" and mandate only "expert-system" validation to align with Constitution Principle I (Reproducibility).
- [ ] T017b [US1] Implement `code/data_generation/expert_system_validator.py`: An automated expert-system validator to review a subset (≥10) for "semantically plausible" rating (FR-007 amended); output review results to `data/synthetic_benchmark/review_results.json`. **Note**: Replaces human-in-the-loop requirement to ensure reproducibility (Constitution Principle I).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline ConAct Execution & Decay Measurement (Priority: P2)

**Goal**: Execute the standard MemGUI-SFT agent (CPU-only, 4-bit quantized) on the synthetic benchmark to measure information decay.

**Independent Test**: The baseline agent runs on the synthetic set without GPU acceleration, completes the execution log, and records step-level success/failure.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for agent execution interface in `tests/contract/test_agent_interface.py`
- [ ] T019 [P] [US2] Integration test for baseline execution loop in `tests/integration/agents/test_baseline_execution.py`

### Implementation for User Story 2

- [ ] T020a [P] [US2] Implement `code/agents/model_checker.py` to perform a **static pre-verification** check against the "Verified datasets" block in Plan/Spec for "MemGUI-8B-SFT" or a pre-verified substitute (e.g., "microsoft/Phi-3-mini-4k-instruct"). **Fail loud** if no pre-verified model is found; do NOT pivot at runtime.
- [ ] T020 [P] [US2] Implement `code/agents/base_conact.py` wrapper for the model selected by T020a (static verification) using `bitsandbytes` 4-bit quantization.
- [ ] T021 [US2] Configure `code/agents/base_conact.py` to force CPU-only execution (no CUDA) and manage memory footprint (<7GB).
- [ ] T022b [P] [US2] Define `code/evaluation/interfaces.py` with `RunnerProtocol` interface (methods: `run_trajectory`, `get_logs`) to decouple baseline and recall runners.
- [ ] T022 [US2] Implement `code/evaluation/runner.py` (ATOMIC): Execute the baseline agent on `data/synthetic_benchmark/trajectories.jsonl`, record the exact step where "information decay" causes a failure, **implement explicit attribution logic to attribute the failure to missing context from a step >10 indices prior**, and generate `data/results/baseline_execution_logs.jsonl`. Adhere to `RunnerProtocol` (T022b).
- [ ] T025 [US2] Implement `code/evaluation/stats.py` preliminary analysis to calculate success rate trend (early vs late step).
- [ ] T026 [US2] Add `code/utils/memory_profiler.py` integration to log peak memory for baseline runs.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Semantic Recall Augmentation & Efficacy Validation (Priority: P3)

**Goal**: Implement a lightweight "selective recall" module using `all-MiniLM-L6-v2` to retrieve historical snippets and measure improvement.

**Independent Test**: The recall-enhanced agent runs on the same synthetic set, and the success rate in the early-step range is compared to the baseline.

**Statistical Methodology Note**: Plan.md selects "Mixed-Effects Logistic Regression (GLMM)" as primary analysis due to hierarchical data. Spec FR-005 mandates Wilcoxon as primary. **Task T036a amends Spec FR-005 to adopt GLMM as primary.** Tasks below follow the amended Spec.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for retrieval query generation (no ground-truth leakage) in `tests/unit/retrieval/test_query_gen.py`
- [ ] T028 [P] [US3] Integration test for recall injection and re-execution in `tests/integration/retrieval/test_recall_injection.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/retrieval/index_builder.py` to build an in-memory index from the agent's folded history.
- [ ] T030 [P] [US3] Implement `code/retrieval/retriever.py` using `all-MiniLM-L6-v2` to generate embeddings for historical snippets.
- [ ] T031 [US3] Implement `code/retrieval/retriever.py` to generate queries based *solely* on the current goal state (no ground-truth metadata).
- [ ] T032 [US3] Implement `code/agents/recall_agent.py` to inject retrieved "memory flashes" into the prompt when similarity > threshold.
- [ ] T033 [US3] Implement `code/evaluation/recall_runner.py`: Execute the recall-enhanced agent on `data/synthetic_benchmark/trajectories.jsonl` adhering to `RunnerProtocol` (T022b), generate `data/results/recall_execution_logs.jsonl`. **Implement as a subclass/adapter of the RunnerProtocol, not a direct extension of T022 file.**
- [ ] T034 [US3] Implement `code/evaluation/log_merger.py`: Merge `data/results/baseline_execution_logs.jsonl` (from T022) and `data/results/recall_execution_logs.jsonl` (from T033) into `data/results/combined_logs.csv` (long-form: trajectory_id, step, success, agent_type).
- [ ] T035 [US3] Implement `code/evaluation/stats.py` to perform Wilcoxon signed-rank test as **Secondary/Validation** analysis comparing baseline vs recall success rates.
- [ ] T036a [P] [US3] **Spec Amendment**: Amend `specs/001-llmxive-long-horizon-context/spec.md` FR-005 to change primary analysis from "Wilcoxon signed-rank test" to "Mixed-Effects Logistic Regression (GLMM)" to align with Plan.md and T036.
- [ ] T036 [US3] Implement `code/evaluation/stats.py` to perform **Mixed-Effects Logistic Regression (GLMM)** as **Primary Analysis**: Input `data/results/combined_logs.csv` (from T034); Model: `success ~ agent_type + (1|trajectory_id)`; Output p-value and effect size. Comply with amended FR-005 (T036a).
- [ ] T037a [P] [US3] **Spec Amendment**: Amend `specs/001-llmxive-long-horizon-context/spec.md` SC-004 to replace "[deferred] limit" with "hard limit of <10% overhead" to align with Constitution Principle VII and FR-006.
- [ ] T037 [US3] Integrate `code/utils/memory_profiler.py` to log overhead and ensure <10% latency increase (FR-006 / Constitution Principle VII / amended SC-004).
- [ ] T038 [US3] Implement `code/evaluation/stats.py` to handle negative/shuffled controls to isolate retrieval variable.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` for the synthetic benchmark generation logic
- [ ] T040 Code cleanup and refactoring of `code/evaluation/stats.py` for clarity
- [ ] T041 Performance optimization for retrieval index building (ensure it fits in RAM)
- [ ] T042 [P] Additional unit tests for edge cases (ambiguous similarity scores, missing context) in `tests/unit/`
- [ ] T043 Run `code/quickstart.md` validation to ensure end-to-end reproducibility

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
3. Complete Phase 3: User Story 1 (T010, T011, T012, T016, T017b)
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
- **Statistical Rigor**: The primary analysis MUST use Mixed-Effects Logistic Regression (GLMM) as per the Plan and amended Spec FR-005 (T036a), with Wilcoxon as a secondary check.
- **Scope**: Tasks reflect the Plan's reduced scope (30 trajectories) per amended Spec FR-001 (T012a).
- **Reproducibility**: All validation (T017b) is automated (expert-system) to comply with Constitution Principle I.
- **Model Verification**: T020a enforces static pre-verification of models; runtime pivots are forbidden.