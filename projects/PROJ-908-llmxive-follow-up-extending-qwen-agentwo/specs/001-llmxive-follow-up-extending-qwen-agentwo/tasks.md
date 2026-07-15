# Tasks: llmXive follow-up: extending "Qwen-AgentWorld: Language World Models for General Agents"

**Input**: Design documents from `/specs/001-llmxive-followup/`
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

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` in `projects/PROJ-908-llmxive-follow-up-extending-qwen-agentwo/`
- [X] T002 Initialize a Python project with a recent stable version. with `requirements.txt` (pinning `datasets`, `scikit-learn`, `prolog`, `networkx`, `pandas`, `pytest`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/loaders.py` with strict real-data fetching (no synthetic fallbacks) using `datasets.load_dataset` or verified HF URLs
- [X] T005 Implement `code/utils/checksums.py` for data hygiene and source verification
- [ ] T006 [P] Setup `data/raw/` and `data/processed/` directory structure and `.gitignore`
- [ ] T007 Create base schema definitions in `specs/001-llmxive-followup/contracts/` (oracle, rules, divergence)
- [ ] T008 Configure `pytest` with fixed random seed (42) and integration test scaffolding
- [X] T009 Implement `code/__init__.py` and `code/main.py` entry point structure

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ground Truth Oracle Construction (Priority: P1) 🎯 MVP

**Goal**: Parse Qwen-AgentWorld source code to generate a deterministic state-transition oracle for independent ground truth verification.

**Independent Test**: Run parser on a known subset; verify generated oracle matches original environment simulator trajectories for N=1,000 random inputs (seed=42) with ≥99.9% accuracy.

### Tests for User Story 1 ⚠️

- [X] T010 [P] [US1] Contract test for `oracle/parser.py` in `tests/unit/test_oracle_parser.py` (verifies schema alignment)
- [X] T011 [US1] Integration test for Oracle vs. Environment Simulator in `tests/integration/test_oracle_validation.py` (N=1,000 random seeds, seed=42)

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/oracle/parser.py` to parse Qwen-AgentWorld source and extract interaction logic (spatial, temporal, causal)
- [ ] T013 [US1] Implement `code/oracle/simulator.py` to execute deterministic state transitions based on parsed logic
- [ ] T014 [US1] Generate `data/processed/oracle_graph.json` (Deterministic State-Transition Oracle) and invoke checksum verification
- [ ] T015 [US1] Implement orchestration step in `code/main.py` or `oracle/parser.py` to invoke `code/utils/checksums.py` during Oracle generation and fail on mismatch (Code Drift check)
- [ ] T016 [US1] Add logging for Oracle generation and validation steps

**Checkpoint**: Ground Truth Oracle is fully functional, validated against simulator, and ready for rule extraction.

---

## Phase 4: User Story 2 - Rule Extraction from Reasoning Traces (Priority: P2)

**Goal**: Apply ILP/Decision Tree to LLM CoT traces to extract explicit logical rules and validate against the Oracle.

**Independent Test**: Feed 500 synthetic traces with known patterns; verify extracted rules reproduce patterns with ≥95% precision.

### Implementation for User Story 2

- [ ] T020 [US2] Generate or Load LLM CoT traces: First attempt to load pre-generated traces from `data/raw/cot_traces.json`. If missing, run `code/inference/runner.py` using the verified CPU-quantized model `Qwen/Qwen1.5-1.8B-Chat-GGUF` to generate traces for a representative set of planning tasks. (Note: T020 is NOT parallel; it blocks T021 and T028).
- [ ] T021 [US2] Implement `code/rules/extractor.py` using FOL/ILP (e.g., Prolog induction) to derive rules from CoT traces
- [ ] T022 [US2] Implement `code/rules/validator.py` to cross-check extracted rules against the Ground Truth Oracle (FR-002)
- [ ] T023 [US2] Generate `data/processed/extracted_rules.json` (Hypothesized Rule Set)
- [ ] T024 [US2] Implement logic to flag "Extraction Uncertainty" for ambiguous/contradictory traces AND output a separate `excluded_metrics` field in the final report containing counts for `extraction_uncertainty` and `cold_start` (per FR-004).
- [ ] T025 [US2] Add logging for rule extraction confidence and validation failures
- [ ] T026 [US2] Implement `code/analysis/metrics.py` to calculate "CoT quality" metrics (e.g., perplexity, internal consistency score) for each trace and output to `data/processed/cot_quality_metrics.json` for SC-005 correlation analysis
- [ ] T027 [US2] Implement `code/rules/metrics.py` to calculate **Rule Precision** by comparing `extracted_rules.json` against `oracle_graph.json` (Ground Truth) and output `data/processed/rule_precision.json` (scalar metric) to satisfy SC-005.

**Checkpoint**: Hypothesized Rule Set is extracted, validated against Oracle, uncertainty is properly flagged and reported separately, CoT quality metrics are generated, and Rule Precision is calculated.

---

## Phase 5: User Story 3 - Divergence Quantification and Classification (Priority: P3)

**Goal**: Compare LLM, Extracted Rules, and Oracle on long-horizon tasks; classify errors into "Hallucination" and "Rule Gap"; perform statistical significance testing.

**Independent Test**: Run on small manually verified dataset; confirm error classification (Hallucination vs Rule Gap) matches human annotation (Cohen's Kappa ≥ 0.8).

### Tests for User Story 3 ⚠️

- [ ] T028 [P] [US3] Contract test for `analysis/diverge.py` in `tests/unit/test_divergence_classifier.py`
- [ ] T029 [US3] Integration test for Statistical Significance (Permutation Test) in `tests/integration/test_stats_significance.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/analysis/diverge.py` to execute standardized tasks and classify transitions:
 - **Match**: LLM == Oracle
 - **Hallucination**: LLM != Oracle AND Rule Inferable (verified by Oracle)
 - **Rule Gap**: LLM != Oracle AND Rule Inferable (verified by Oracle) BUT LLM failed to execute it. (Note: Corrected definition per FR-004; removed "Extracted Rule != Oracle" condition).
 - **Extraction Uncertainty** & **Coverage Gap (Cold Start)**: Detect and log these separately; exclude from primary Hallucination/Rule Gap counts.
- [ ] T031 [US3] Generate `data/processed/divergence_report.json` with classified counts, `excluded_metrics` (uncertainty/cold start), and metadata.
- [ ] T032 [US3] Implement logic in `code/analysis/stats.py` to identify the specific step count or state complexity boundary where measured adherence drops below the **95%** threshold (per FR-006/SC-004).
- [ ] T033 [US3] Calculate Pearson's correlation (r) between extracted rule precision (from T027 `data/processed/rule_precision.json`) and CoT quality metrics (from T026 `data/processed/cot_quality_metrics.json`) to satisfy SC-005.
- [ ] T034 [US3] Finalize `divergence_report.json` with p-values (α ≤ 0.05), boundary conditions (from T032), and correlation metrics (from T033).

**Checkpoint**: Divergence Report is generated with statistically significant error classification, boundary analysis, and correlation metrics.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `README.md`
- [ ] T036 Code cleanup and refactoring across `code/`
- [ ] T037 Performance optimization for ILP induction on CPU (ensure <6h runtime)
- [ ] T038 [P] Additional unit tests coverage in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation and end-to-end smoke test

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1)**: Must complete first to provide the Ground Truth Oracle required by US2 and US3.
 - **US2 (P2)**: Depends on US1 (Oracle) for validation.
 - **US3 (P3)**: Depends on US1 (Oracle) and US2 (Extracted Rules) for comparison.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundation. No dependencies on other stories.
- **User Story 2 (P2)**: Depends on US1 (Oracle) for rule validation.
- **User Story 3 (P3)**: Depends on US1 (Oracle) and US2 (Rules) for divergence analysis.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loaders (`utils/loaders.py`) must be implemented before any data fetching tasks
- Models/Logic before services/executors
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Once Foundational phase completes, US1 must run first; US2 and US3 can be prepared in parallel (but US3 execution waits for US2 completion)
- All tests for a user story marked [P] can run in parallel
- **T020 is NOT parallel** as it produces critical input for T021 and T030.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Oracle Construction)
4. **STOP and VALIDATE**: Verify Oracle matches simulator on N=1,000 samples.
5. Deploy/Demo Oracle generation pipeline.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Rule Extraction)
4. Add User Story 3 → Test independently → Deploy/Demo (Divergence Analysis)
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Critical Path)
 - Developer B: User Story 2 (Can start logic, waits for Oracle)
 - Developer C: User Story 3 (Can start logic, waits for Oracle & Rules)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Data Hygiene**: Strictly no synthetic data fallbacks in `code/utils/loaders.py`. Fail loudly on fetch errors.
- **Compute**: Ensure ILP tasks are CPU-tractable; if GPU is required for a specific step, mark it explicitly for offloading, but prefer CPU for the main pipeline.
- **ID Conflict Resolution**: All task IDs (T001-T039) are now unique and sequential.
- **Revision Note**: T027 added for Rule Precision; T020 updated for pre-generated traces; T030 updated for correct Rule Gap definition; T032 updated for 95% threshold; T041 removed (logic integrated).
