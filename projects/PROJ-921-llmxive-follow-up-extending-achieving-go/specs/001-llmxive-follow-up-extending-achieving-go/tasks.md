---

description: "Task list template for feature implementation"
---

# Tasks: llmXive follow-up: extending "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified S"

**Input**: Design documents from `/specs/001-llmxive-followup/`
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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize [language] project with [framework] dependencies
- [ ] T003 [P] Configure linting and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup database schema and migrations framework
- [ ] T005 [P] Implement authentication/authorization framework
- [ ] T006 [P] Setup API routing and middleware structure
- [ ] T007 Create base models/entities that all stories depend on
- [ ] T008 Configure error handling and logging infrastructure
- [ ] T009 Setup environment configuration management

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Benchmark Ingestion and Model Inference (Priority: P1) 🎯 MVP

**Goal**: Implement data ingestion and model inference for both datasets

**Independent Test**: Verify inference pipeline generates valid JSONL output for both datasets within the time/memory constraints.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Contract test for inference endpoint in tests/contract/test_inference.py
- [ ] T011 [P] [US1] Integration test for full inference pipeline in tests/integration/test_pipeline.py

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create data models for IMO/IPhO/OpenSci-Reason in src/models/dataset.py
- [ ] T013 [P] [US1] Implement dataset loading and parsing in src/data/data_loader.py
- [ ] T014 [US1] Implement inference runner for SU-01 and baseline in src/inference/inference.py (depends on T012, T013)
- [ ] T015 [US1] Add validation and error handling for inference
- [ ] T016 [US1] Add logging for inference operations
- [ ] T017 [US1] Implement JSONL output formatting in src/utils/output_formatter.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated Expert Simulation and Scoring (Priority: P2)

**Goal**: Implement automated scoring using a proxy LLM

**Independent Test**: Verify proxy model scores correlate >0.6 with gold standard responses

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for scoring endpoint in tests/contract/test_scoring.py
- [ ] T019 [P] [US2] Integration test for scoring pipeline in tests/integration/test_scoring_pipeline.py

### Implementation for User Story 2

- [ ] T020 [P] [US2] Load and freeze Llama-3-8B scoring model in src/scoring/proxy_model.py
- [ ] T021 [US2] Implement scoring logic (Novelty, Feasibility, Consistency) in src/scoring/scorer.py
- [ ] T022 [US2] Implement validation against gold standard in src/scoring/validator.py
- [ ] T023 [US2] Integrate scoring pipeline with User Story 1 output

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Rigidity Analysis (Priority: P3)

**Goal**: Perform statistical analysis to determine correlation between Olympiad accuracy and OpenSci-Reason creativity

**Independent Test**: Verify synthetic dataset analysis yields expected correlation

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for analysis API in tests/contract/test_analysis.py
- [ ] T025 [P] [US3] Integration test for full analysis pipeline in tests/integration/test_analysis_pipeline.py

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement statistical functions (correlation, t-test) in src/analysis/stats.py
- [ ] T027 [US3] Implement data aggregation and preparation in src/analysis/data_prep.py
- [ ] T028 [US3] Implement analysis pipeline to compute correlation and perform t-test in src/analysis/analysis.py

**Checkpoint**: All user stories should now be independently functional

---

- [ ] T029 [P] [US3] Implement power analysis to justify sample size in src/analysis/power_analysis.py
- [ ] T030 [P] [US3] Generate analysis report in src/analysis/report.py

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for inference endpoint in tests/contract/test_inference.py"
Task: "Integration test for full inference pipeline in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Create data models for IMO/IPhO/OpenSci-Reason in src/models/dataset.py"
Task: "Implement dataset loading and parsing in src/data/data_loader.py"
```

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Address reviewer concern #1 (FR-006):
  - [ ] T031 [P] [US1] Implement token limit enforcement in src/inference/inference.py and log truncation events.
- Address reviewer concern #2 (Edge Case - Ambiguous Prompts):
  - [ ] T032 [US2] Implement low-confidence prompt flagging logic in src/scoring/scorer.py based on variance and entropy.
- Address reviewer concern #3 (Edge Case - Inference Timeouts):
  - [ ] T033 [US1] Implement hard token limit (2048) and truncation logging in src/inference/inference.py.
