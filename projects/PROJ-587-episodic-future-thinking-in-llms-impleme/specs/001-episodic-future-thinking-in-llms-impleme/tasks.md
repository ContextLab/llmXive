# Tasks: Episodic Future Thinking in LLMs: Implementing Mental Time Travel

**Input**: Design documents from `/specs/001-episodic-future-thinking/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python 3.11 project with PyTorch/Transformers dependencies
- [X] T003 [P] Configure linting and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 [P] Implement data loading pipeline for ALFWorld/TextWorld benchmarks
- [X] T004a [P] Generate `data/processed/trajectories.parquet` by parsing raw ALFWorld/TextWorld datasets (specifically `data/raw/alfworld/*.jsonl` and `data/raw/textworld/*.jsonl`) into (state, action, outcome) tuples; ensure at least 100 trajectories are generated for testing. Raise `ValueError` if < 100 valid tuples are found. Depends on: T004.
- [X] T004b [P] Generate SHA-256 checksum for `data/processed/trajectories.parquet` and record it in `data/checksums.txt` and update `state/projects/PROJ-587-episodic-future-thinking-in-llms-impleme.yaml` artifact_hashes. Depends on: T004a.
- [X] T005 [P] Implement authentication/authorization framework
- [X] T006 [P] Setup API routing and middleware structure
- [X] T007 Create base models/entities that all stories depend on
- [X] T008 [P] Setup environment configuration management
- [X] T008a [P] Generate `config/config.yaml`at `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/config/config.yaml` with concrete defaults: `similarity_threshold: 0.75 `, `{{claim:c_7ef7f8af}} (Wikipedia: Redmi Note 6 Pro, https://en.wikipedia.org/wiki/Redmi_Note_6_Pro)`, `faiss_hnsw_m: 16 `, `faiss_hnsw_ef_construction: 100 `.
- [X] T008b [P] Implement `config_loader.py` to validate `config.yaml` keys and types; raise `ValueError` if `max_ram_gb` > 7 or `faiss_hnsw_m` is invalid. Depends on: T008a.
- [X] T008c [P] Implement memory limit enforcement in `utils/memory_monitor.py` to raise RuntimeError if process exceeds 6 GB RAM. Depends on: T008a.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Episodic Memory Module Integration (Priority: P1) 🎯 MVP

**Goal**: Implement a CPU-optimized neural episodic control module that stores (state, action, outcome) tuples with semantic embeddings and supports high-precision retrieval.

**Independent Test**: Record 100 planning trajectories, store them, and verify top-5 retrieval precision ≥ 0.80 with cosine similarity ≥ 0.75 within 500ms on CPU.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010a [P] [US1] Define `IEpisodicMemory` protocol/interface in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/models/episodic_memory.py` (abstract class or Protocol) with `store`, `retrieve`, `update` methods.
- [X] T010b [US1] Write test stub `test_store_returns_id` in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/tests/unit/test_episodic_memory.py` that imports `IEpisodicMemory` and asserts `store()` returns a valid episode ID (using mock factory). Depends on: T010a.
- [X] T011a [P] [US1] Write test `test_retrieval_latency_1k` in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/tests/integration/test_retrieval_latency.py` that uses a generated mock dataset to assert `latency < 0.5s` (unit test). Depends on: T010a.
- [X] T011b [US1] Write test `test_retrieval_latency_10k` in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/tests/integration/test_retrieval_latency.py` that loads REAL entries from `data/processed/trajectories.parquet` (generated by T004a) and asserts `latency < 0.5s` and `memory_usage < 7GB`. Ensure T004a has been executed successfully before running this test. Implementation (T012) must be complete before test execution. Depends on: T012, T004a.

### Implementation for User Story 1

- [X] T012 [US1] Implement `EpisodicMemory` class with FAISS HNSW index in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/models/episodic_memory.py`.
 - *Addressing Alan Turing*: Explicitly define storage as discrete-state machine configurations (state-action-outcome tuples) rather than weight updates.
 - *Addressing Eric Kandel*: Implement "consolidation" (timestamp-based) to distinguish specific events from semantic patterns.

- [X] T013a [US1] Implement `encode_state()` function in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/models/episodic_memory.py` with signature: `def encode_state(state_text: str) -> np.ndarray` (returns a fixed-dimensional embedding).

- [X] T013b [US1] Implement `encode_action()` function in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/models/episodic_memory.py` with signature: `def encode_action(action_text: str) -> np.ndarray` (returns a fixed-dimensional embedding).

- [X] T014 [US1] Implement `RetrievalService` with conflict resolution logic in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/services/retrieval_service.py`.
 - *Conflict Definition*: Same `state_hash`, different `outcome_hash`.
 - *Logic*: {{claim:c_703d23d6}}; default to most recent.
 - *Addressing Eric Kandel*: Ensure timestamps act as the "cellular alphabet" for consolidation.

- [X] T015 [US1] Implement fallback logic: if retrieval count ≤ 2, default to baseline transformer and log event in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/services/retrieval_service.py`.

- [X] T016 [US1] Add `validate_similarity_threshold()` function in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/services/retrieval_service.py`.
 - *Operational Default*: Enforce `similarity_threshold == 0.75` via `ValueError` if different value is passed without `--override-threshold` flag.
 - *Experimental Override*: Allow `--override-threshold` flag (used by T029) to bypass the 0.75 check for sensitivity analysis.
 - *Addressing FR-002*: Ensures the fixed threshold is enforced for operational retrieval.

- [ ] T017 [US1] Add logging for retrieval events, confidence scores, and fallback triggers in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/utils/logging.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Future Scenario Simulation with Episodic Retrieval (Priority: P2)

**Goal**: Generate future planning scenarios by combining retrieved episodic memories with current state, ensuring coherence and statistical validity.

**Independent Test**: Generate plans for a set of held-out tasks.; measure accuracy against baseline; report effect size d≥0.8.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for scenario generation output format in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/tests/contract/test_scenario_gen.py`.
- [X] T019 [P] [US2] Integration test for full planning pipeline (retrieve + generate + evaluate) in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/tests/integration/test_planning_service.py`.

### Implementation for User Story 2

- [X] T020 [US2] Implement `PlanningService` to combine retrieved episodes with current state in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/services/planning_service.py`.
 - *Depends on: T012, T013a, T013b, T014, T015, T017, T004a* (US1 components + data).
 - *Integration*: Use `RetrievalService.retrieve()` and `EpisodicMemory` classes.
 - *Addressing Dan Rockmore*: Ensure generation explicitly navigates "topology" of possible futures by weighting retrieved trajectories.
 - *Addressing David Krakauer*: Implement error-minimization update rule to revise internal models when predictions fail.
 - *Sub-task*: Add uncertainty markers for details not supported by retrieved memories (WYSIATI prevention) in this same task.

- [X] T021 [US2] Implement baseline transformer inference (medium-scale parameter count, CPU-optimized) in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/models/baseline_transformer.py`.

- [X] T022 [US2] Implement augmented LLM inference (Transformer + Episodic Control) in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/models/augmented_llm.py`.

- [ ] T023 [US2] Implement `run_mixed_effects_test()` in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/utils/stats.py` using `statsmodels` with Bonferroni correction for multiple-comparison testing (FR-008).

- [X] T023b [US2] Integrate `run_mixed_effects_test()` into the main evaluation pipeline in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/experiments/run_episodic.py`, ensuring Bonferroni correction is applied to final reported p-values. Depends on: T023.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Episodic vs Semantic Retrieval Validation Protocol (Priority: P3)

**Goal**: Validate true episodic recollection vs. pattern matching using counterfactual confidence calibration.

**Independent Test**: Generate scenarios with perturbed counterfactual details; verify model confidence scores are low for unknown details.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for confidence score reporting in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/tests/contract/test_confidence.py`.
- [X] T026 [P] [US3] Integration test for counterfactual perturbation and confidence calibration in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/tests/integration/test_validation_service.py`.

### Implementation for User Story 3

- [X] T027a [US3] Implement protocol for implement protocol for recruiting ≥ 3 human raters and managing the evaluation interface in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/validation/evaluation_protocol.md`. This task defines the workflow, rater instructions, and data collection format.
 - *Addressing Daniel Kahneman*: Distinguish "simulation" vs "evaluation"; ensure System 2 checks System 1.

- [X] T027b [US3] Implement `CounterfactualGenerator` to create perturbed scenarios (swapping outcome values) in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/validation/counterfactual_gen.py`.
 - *Addressing Daniel Kahneman*: Explicitly measure confidence in counterfactual details to detect WYSIATI bias.

- [X] T027c [US3] Implement `ValidationService` to measure confidence calibration, flagging rates, calculate inter-rater reliability (Krippendorff's alpha), and sweep similarity thresholds in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/validation/confidence_calib.py`.
 - *Note*: Consolidates T027c and T028 logic.
 - *Sensitivity Analysis*: Include logic to run with `--override-threshold` flag (from T016) for the set {0.70, 0.75, 0.80}.

- [X] T027d [US3] Implement `scripts/run_human_eval.py` to automate rater recruitment interface, present generated scenarios, collect raw Likert ratings, and aggregate results into `data/results/human_eval_ratings.csv`. This task executes the measurement required by SC-004. Depends on: T027a.

- [X] T029 [US3] Implement sensitivity analysis script to sweep similarity thresholds across a specific set of representative values and report precision variation in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/experiments/sensitivity_analysis.py`.
 - *Output Format*: Generate `data/results/sensitivity_analysis.csv` with columns: `threshold`, `precision`, `recall`, `latency_ms`.
 - *Execution*: Must invoke `ValidationService` with `--override-threshold` flag to bypass T016's default check.
 - *Addressing FR-006*: Explicitly executes the sweep required by FR-006.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Update `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/docs/architecture.md` to document reproducibility mechanisms (human evaluation workflow) and address methodological concerns regarding episodic vs. semantic retrieval in plain prose.
- [X] T033 [P] Code cleanup: Remove unused imports and refactor `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/models/episodic_memory.py` (T012) to use dependency injection.
- [X] T034 [P] Performance optimization: Tune FAISS HNSW parameters in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/models/episodic_memory.py` to achieve index build time < 10s for 10k entries.
- [ ] T035 [P] Additional unit tests for statistical utilities in `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/tests/unit/test_stats.py`.
- [X] T036 [P] Add GPG signature verification to `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/scripts/download_data.sh` for data download security.
- [X] T037 [P] Create `projects/PROJ-587-episodic-future-thinking-in-llms-impleme/.github/workflows/validate_quickstart.yml` to run `quickstart.md` end-to-end validation.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 components (T012-T017) for retrieval logic.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable.

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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Write test stub test_store_returns_id in tests/unit/test_episodic_memory.py"
Task: "Write test stub test_retrieval_latency_1k in tests/integration/test_retrieval_latency.py"

# Launch all models for User Story 1 together:
Task: "Implement EpisodicMemory class skeleton with FAISS HNSW index in models/episodic_memory.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **CPU Constraint**: All models and data processing MUST fit within 7GB RAM and run on a standard multi-core CPU configuration. No CUDA, no 8-bit quantization, no large LLMs.
- **Data Integrity**: Use real ALFWorld/TextWorld datasets via official repositories. No synthetic/fake data generation for inputs.
- **Reproducibility**: All evaluation metrics (including human evaluation) must be reproducible via deterministic recording of raw ratings and calculation of inter-rater reliability in CI.
- **Reviewer Alignment**:
 - **Alan Turing**: Task T012 explicitly defines episodic memory as discrete-state machine configurations.
 - **Dan Rockmore**: Task T020 ensures navigation of the "topology" of possible futures.
 - **Daniel Kahneman**: Tasks T027a, T027b, T027c, T027d implement System 2 validation, counterfactual confidence calibration, and execution of human evaluation to prevent WYSIATI bias.
 - **David Krakauer**: Task T020 includes error-minimization update rules for model revision.
 - **Eric Kandel**: Task T012 implements timestamp-based consolidation to distinguish specific events from semantic patterns.
