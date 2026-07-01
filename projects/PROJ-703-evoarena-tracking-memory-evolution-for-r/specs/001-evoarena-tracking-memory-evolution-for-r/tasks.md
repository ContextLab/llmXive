# Tasks: EvoArena: Tracking Memory Evolution for Robust LLM Agents in Dynamic Environments

**Input**: Design documents from `/specs/703-evoarena-tracking-memory-evolution-for-r/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

**Purpose**: Project initialization, environment configuration, and dependency verification for CPU-only CI.

- [X] T001 Create project structure `src/evomem_validation/` and `tests/` per `plan.md`
- [X] T002 Initialize Python 3.10+ project with `requirements.txt` (CPU-only `torch`, `transformers`, `datasets`, `pandas`, `pyyaml`, `pytest`)
- [X] T003 [P] Configure `.env` template for API keys and verify `external/EvoArena` submodule presence
- [X] T004 [P] Create `contracts/` directory and initialize `execution_log.schema.yaml`, `memory_patch.schema.yaml`, `accuracy_summary.schema.yaml`, and `reference_values.schema.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data loading, validation logic, and **entry point discovery** required before running agents.

**⚠️ CRITICAL**: No agent execution can begin until this phase is complete.

- [X] T005 Implement `src/evomem_validation/config.py` to load environment variables and define path constants for `external/EvoArena` and dataset subsets
- [X] T006 [P] Implement `src/evomem_validation/validators.py` to validate JSON logs and patch files against `contracts/` schemas (FR-005)
- [X] T007 [P] Implement `src/evomem_validation/data_loader.py` to fetch/symlink **TerminalBench-Evo** and **PersonaMem-Evo** subsets (real data, no fabrication; use vendored data or standard loaders if available)
- [X] T007a [P] **Discovery**: Inspect `external/EvoArena/` (scripts/, README.md, main entry points) to identify the **actual** baseline, EvoMem, and Persona evaluation entry points; document findings in `docs/entry_points.md` (Required before T012, T013, T018)
- [X] T008 Implement `src/evomem_validation/runner.py` skeleton with CPU-only device enforcement and OOM protection (max patch history limit)
- [X] T009 Create `tests/unit/test_validators.py` to ensure schema validation logic works before integration

**Checkpoint**: Foundation ready - data loading, validation logic, and entry point identification are verified; user story execution can now begin.

---

## Phase 3: User Story 1 - Execute Baseline and EvoMem Evaluation on TerminalBench-Evo (Priority: P1) 🎯 MVP

**Goal**: Run baseline and EvoMem agents on multiple TerminalBench-Evo chains, generating raw JSON logs and patch stores using the entry points identified in T007a.

**Independent Test**: Verify existence of valid JSON result files and patch files in output directories after running 5 chains.

### Tests for User Story 1 (Mandatory for Pipeline Integrity)

- [X] T010 [P] [US1] Unit test in `tests/unit/test_data_loader.py`: `test_data_loader_fetches_subset()` verifies real data fetch and asserts file existence + valid JSON structure
- [X] T011 [P] [US1] Integration test in `tests/integration/test_terminal_baseline.py`: `test_baseline_run_single_chain()` runs 1 chain using the discovered entry point, asserts JSON output exists and passes schema validation

### Implementation for User Story 1

- [X] T012 [US1] Implement `src/evomem_validation/runner.py` logic to invoke the **Baseline Evaluation Entry Point** (identified in T007a) for N=5 chains
- [X] T013 [US1] Implement `src/evomem_validation/runner.py` logic to invoke the **EvoMem Evaluation Entry Point** (identified in T007a) for N=5 chains, ensuring `patch_store` is populated
- [X] T014 [US1] Add exponential backoff error handling in `src/evomem_validation/runner.py` for API rate limits (Edge Case)
- [X] T015 [US1] Add logic to skip corrupted/missing chain IDs gracefully in `src/evomem_validation/runner.py` (Edge Case)
- [X] T016 [US1] Integrate `validators.py` (T006) to automatically validate logs post-run before returning success

**Checkpoint**: TerminalBench-Evo baseline and EvoMem runs execute successfully, producing valid JSON logs and patches.

---

## Phase 4: User Story 2 - Execute PersonaMem-Evo Evaluation and Chain Accuracy Analysis (Priority: P2)

**Goal**: Run PersonaMem-Evo on multiple chains, processing chat history updates and generating chain-level accuracy metrics using the entry points identified in T007a.

**Independent Test**: Verify summary report and per-chain JSON logs containing memory update sequences.

### Tests for User Story 2

- [X] T017 [P] [US2] Integration test in `tests/integration/test_persona_chain.py`: `test_persona_run_single_chain()` runs 1 chain using the discovered entry point, asserts patch history is captured in output

### Implementation for User Story 2

- [X] T018 [US2] Implement `src/evomem_validation/runner.py` logic to execute the **Persona Evaluation Entry Point** (identified in T007a) for N=3 chains
- [X] T019 [US2] Ensure the **Memory Patching Mechanism** (identified in T007a) is correctly invoked and patch history is capped to prevent OOM (Edge Case)
- [X] T020 [US2] Implement logic to capture and log "memory update sequences" in the output JSON for each chain
- [X] T021 [US2] Add validation to ensure summary report contains per-chain accuracy booleans

**Checkpoint**: PersonaMem-Evo evaluation runs successfully, producing chain-level accuracy logs and patch histories.

---

## Phase 5: User Story 3 - Generate Performance Comparison and Mechanistic Analysis Reports (Priority: P3)

**Goal**: Aggregate logs from Terminal and Persona runs to compute average/chain-level accuracy and compare with paper claims.

**Independent Test**: Verify aggregation script outputs a summary table and flags deviations >5% from reference values.

### Implementation for User Story 3

- [X] T022 [US3] Implement `src/evomem_validation/aggregator.py` to load all JSON logs from Phase 3 and Phase 4
- [X] T023 [US3] Implement logic in `aggregator.py` to calculate average accuracy and chain-level accuracy for Baseline vs. EvoMem (FR-004)
- [X] T024a [US3] **Populate Reference Values**: Extract reported accuracy/gain values from the paper abstract and populate `contracts/reference_values.schema.yaml` (Resolves SC-001/SC-002 deferred gap)
- [X] T024b [US3] **Compare Metrics**: Load `contracts/reference_values.schema.yaml` (populated in T024a) and compare reproduced metrics; flag deviations >5% (SC-001, SC-002)
- [X] T025 [US3] Generate `results/accuracy_summary.json` and `results/mechanistic_analysis.md` (evidence capture counts)
- [X] T026 [US3] Implement final validation to ensure all artifacts are non-empty and valid before marking run complete (FR-005)

**Checkpoint**: Final reports generated, metrics computed, and validation against paper claims completed.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and final verification.

- [X] T027 [P] Update `README.md` with execution instructions for the reproduction probe (N=10 chains)
- [X] T028 Run `quickstart.md` validation (if applicable) to ensure all scripts are executable
- [X] T029 Clean up temporary logs and ensure `data/` directory contains only the required subset
- [X] T030 Final check: Verify no GPU dependencies remain in `requirements.txt` or code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **US1 (Terminal)** must complete before US3 aggregation
  - **US2 (Persona)** must complete before US3 aggregation
  - US1 and US2 can run in parallel if resources allow, but US3 is strictly sequential after both
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2). No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2). No dependencies on US1, but shares data loader.
- **User Story 3 (P3)**: Depends on completion of US1 and US2 to aggregate results.

### Within Each User Story

- Tests (T010-T011, T017) MUST be written and verified before full implementation tasks (T012-T016, T018-T021).
- Data loading, validation logic, and **Entry Point Discovery** (Phase 2, T007/T007a) must be complete before any agent execution.
- Aggregation (Phase 5) cannot start until raw logs from Phase 3 and 4 exist.
- **Reference Value Population** (T024a) must complete before Comparison (T024b).

### Parallel Opportunities

- **Setup**: T002, T003, T004 can run in parallel.
- **Foundational**: T005, T006, T007, T007a, T008 can run in parallel (once T001 is done).
- **Unit Tests**: T009, T010, T017 can run in parallel.
- **US1 & US2**: If multiple runners are available, T012-T016 (Terminal) and T018-T021 (Persona) can run in parallel.
- **Validation**: T016 and T021 run automatically after their respective execution tasks.

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (including T007a Discovery)
3. Complete Phase 3: User Story 1 (TerminalBench-Evo)
4. **STOP and VALIDATE**: Ensure baseline and EvoMem runs produce valid JSON logs.
5. Proceed to US2 only if US1 is stable.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready.
2. Add US1 (Terminal) → Test independently → Deploy/Demo (MVP!).
3. Add US2 (Persona) → Test independently → Deploy/Demo.
4. Add US3 (Aggregation) → Generate final report.
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
   - Developer A: User Story 1 (Terminal)
   - Developer B: User Story 2 (Persona)
3. Once US1 and US2 are complete, Developer C (or A/B) implements User Story 3 (Aggregation).

---

## Notes

- **[P]** tasks = different files, no dependencies.
- **Real Data Only**: Tasks T007 and T012-T018 MUST use real data sources (TerminalBench-Evo, PersonaMem-Evo). No fake data generation.
- **CPU Constraints**: All tasks assume multiple CPU cores and sufficient RAM.. No GPU, no 8-bit quantization, no large model training.
- **Data Flow**: T007 (Load Data) → T007a (Discover Entry Points) → T012/T018 (Run Agents) → T022 (Aggregate). Order is strict.
- **Validation**: T006 and T016/T021 ensure artifact integrity before aggregation.
- **Reference Values**: T024a must populate the schema before T024b can compare.
- **Commit Strategy**: Commit after each Phase or logical group (e.g., after Foundational, after US1).