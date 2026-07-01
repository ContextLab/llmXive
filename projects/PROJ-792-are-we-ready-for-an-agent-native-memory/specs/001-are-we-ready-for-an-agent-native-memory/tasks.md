# Tasks: Are We Ready For An Agent-Native Memory System?

**Input**: Design documents from `/specs/792-are-we-ready-for-an-agent-native-memory/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

- [X] T001 Create project structure per implementation plan (src/, tests/, data/, results/)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `sentence-transformers` CPU build, `datasets`, `pandas`, `scikit-learn`, `numpy`, `huggingface_hub`, `pytest`)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Clone and verify `awesome-agent-memory` submodule integrity
- [X] T005 [P] Implement `src/utils/memory_guard.py`: RAM monitoring with OOM prevention (threshold set to a predefined safe limit) and automatic dataset downsampling trigger (DEPENDS ON T007)
- [X] T006 [P] Create `src/config/defaults.yaml` with memory limits, random seeds, and model fallback paths (TinyLlama CPU); includes specific task to implement deterministic seeding logic for all stochastic processes.
- [X] T007 Implement `src/utils/logging.py` for structured logging of "Downsampled" events and "CPU-Limited Baseline" flags
- [X] T008 Setup `tests/unit/test_memory_guard.py` to verify OOM trigger logic

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Validate Execution Environment and Data Ingestion (Priority: P1) 🎯 MVP

**Goal**: Initialize environment, ingest a real benchmark dataset, and confirm the data pipeline is functional on CPU-only CI without GPU/CUDA dependencies.

**Independent Test**: The user runs the setup script; the script exits with code 0 and produces a non-empty `data/` directory containing ingested artifacts, with no CUDA errors.

### Tests for User Story 1

- [X] T009 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_ingestion_schema.py`
- [X] T010 [P] [US1] Integration test for ingestion script with memory guard in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `src/ingestion/loader.py`: Fetch real dataset (e.g., MixSub-LLaMA subset) from verified URL or HuggingFace `datasets`
- [X] T014 [US1] Add validation to ensure ingested data matches `awesome-agent-memory` entry script requirements AND temporal structure; raise ValueError with specific message if invalid and generate `validation_report.json` artifact.
- [X] T012 [P] [US1] Implement `src/ingestion/preprocessor.py`: Context truncation and downsampling logic to fit constrained RAM, enforcing deterministic seeding from T006 config.
- [X] T013 [US1] Implement `src/ingestion/__init__.py` entry point with GPU/CUDA detection; if detected, automatically fallback to CPU-tractable approximations (e.g., TinyLlama) rather than immediate failure.
- [X] T015 [US1] Add logging for "Ingestion Complete" and file count verification

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Reproduce Core Module Evaluation (Priority: P2)

**Goal**: Execute evaluation of the four core modules (Representation, Extraction, Retrieval, Maintenance) against a subset of workloads, generating raw metrics for at least 3 memory systems.

**Independent Test**: The evaluation script completes and generates a JSON/CSV artifact with valid metrics (normalized range) for 3 systems, handling OOM via downsampling.

### Tests for User Story 2

- [X] T016 [P] [US2] Contract test for metric schema in `tests/contract/test_metrics_schema.py`
- [X] T017 [P] [US2] Integration test for evaluation runner with memory safety in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement `src/evaluation/modules/representation.py`: CPU-tractable representation test
- [X] T019 [P] [US2] Implement `src/evaluation/modules/extraction.py`: CPU-tractable extraction test
- [X] T020 [P] [US2] Implement `src/evaluation/modules/retrieval.py`: CPU-tractable retrieval test
- [X] T021 [P] [US2] Implement `src/evaluation/modules/maintenance.py`: Synthetic Update Protocol to simulate maintenance on static data (explicitly labeled as proxy); enforce deterministic seeding logic for synthetic generation to meet SC-005 variance requirements.
- [X] T022 [US2] Implement `src/evaluation/runner.py`: Orchestrator that runs ablation studies for multiple systems, explicitly executing Representation, Extraction, Retrieval, and Maintenance modules; integrates memory guard and outputs raw metrics.
- [X] T023 [US2] Integrate `src/evaluation/metrics.py` for precision, recall, and update correctness calculation
- [X] T024 [US2] Add logic to switch to TinyLlama CPU (not rule-based baseline) if external LLM API keys are missing
- [X] T025 [US2] Implement logic in `src/evaluation/runner.py` to trigger `src/ingestion/preprocessor.py` downsampling in response to `src/utils/memory_guard.py` signals during the evaluation run.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Cost-Performance Trade-off Analysis (Priority: P3)

**Goal**: Aggregate raw metrics into a summary report visualizing cost-performance trade-offs and comparing localized vs. global maintenance strategies.

**Independent Test**: The aggregation script produces a Markdown report with a sorted table of "Cost Efficiency" scores and a specific conclusion on the maintenance claim.

### Tests for User Story 3

- [X] T026 [P] [US3] Contract test for report schema in `tests/contract/test_report_schema.py`
- [X] T027 [P] [US3] Integration test for report generation in `tests/integration/test_report_gen.py`

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement `src/analysis/aggregator.py`: Calculate "Cost Efficiency" (Performance / Cost) and sort systems
- [X] T029 [US3] Implement `src/analysis/report_gen.py`: Generate Markdown report with comparative analysis of Local vs. Global maintenance
- [X] T030 [US3] Add explicit logic to flag whether data supports/refutes the "localized maintenance is more cost-efficient" claim by appending a boolean column `supports_local_maintenance` to the report CSV.
- [X] T031 [US3] Ensure report explicitly labels results as "Proxy Evaluation" due to dataset limitations (per plan.md)
- [X] T032 [US3] Implement logic in `src/analysis/report_gen.py` to generate a dedicated "Limitations: Technical Feasibility vs. Cognitive Evolution" section, explicitly discussing the gap between reproduced metrics and the paper's claims about "evolutionary stability" without making unvalidated claims.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Concern Integration - Cognitive Coherence & Evolutionary Stability

**Goal**: Address David Krakauer's review regarding the framing of memory as a "technical architecture problem" vs. "cognitive prosthesis evolution." Tasks here ensure the project explicitly acknowledges the limitations of technical reproduction in validating cognitive claims.

### Implementation for Reviewer Concerns

- [X] T033 [US2] Extend `src/evaluation/modules/maintenance.py` documentation and output to explicitly state that "Synthetic Updates" do not validate "coherence across temporal scales"
- [X] T034 [P] Update `specs/792-are-we-ready-for-an-agent-native-memory/research.md` to incorporate the historical trajectory of memory (hippocampal -> external -> computational) as context for the reproduction's scope

---

## Phase 7: Performance & Optimization (Addressing Executability)

**Goal**: Ensure the pipeline completes within the -hour CI limit and handles resource constraints deterministically.

- [X] T035 [P] Implement caching mechanism in `src/evaluation/runner.py` to store intermediate embeddings and avoid re-computation for repeated system evaluations.
- [X] T036 [P] Implement strict timeout enforcement in `src/evaluation/runner.py` to abort individual system evaluations that exceed a reasonable time threshold, logging the timeout and proceeding to the next system.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `README.md` explaining the CPU-only constraints and proxy data nature
- [X] T038 [P] Additional unit tests for downsampling logic in `tests/unit/test_downsampling.py`
- [X] T039 Run `quickstart.md` validation to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data ingestion
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for metrics
- **Reviewer Concerns (Phase 6)**: Can run in parallel with US3 or after, but requires US2 data for specific analysis

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, and US3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/contract/test_ingestion_schema.py"
Task: "Integration test for ingestion script with memory guard in tests/integration/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement src/ingestion/loader.py"
Task: "Implement src/ingestion/preprocessor.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (real data ingestion on CPU)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Phase 6 (Reviewer Concerns) → Finalize Report
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Ingestion)
   - Developer B: User Story 2 (Evaluation)
   - Developer C: User Story 3 (Analysis)
3. Stories complete and integrate independently
4. Phase 6 tasks can be handled by Developer C or a dedicated reviewer

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: No task may assume GPU/CUDA availability or use 8-bit/4-bit quantization requiring CUDA. All heavy operations must use CPU-tractable approximations.
- **Data Integrity**: No task may generate fake input data. All datasets must be real and fetched from verified sources.
- **Reviewer Alignment**: Phase 6 tasks explicitly address the "cognitive prosthesis" vs. "technical architecture" framing concern.
- **Determinism**: All stochastic processes (synthetic updates, downsampling) must use seeds defined in `defaults.yaml` to meet SC-005 variance requirements.
- **Proxy Labeling**: All output artifacts from synthetic protocols must be explicitly labeled "Proxy Evaluation".
- **Performance**: Phase 7 tasks ensure the pipeline respects the 6-hour CI time limit via caching and timeouts.