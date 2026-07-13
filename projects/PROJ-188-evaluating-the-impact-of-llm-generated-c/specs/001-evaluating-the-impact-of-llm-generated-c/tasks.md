# Tasks: Evaluating the Impact of LLM-Generated Code Explanations on Comprehension

**Input**: Design documents from `/specs/001-eval-llm-code-explanations/`
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

- [ ] T001a Create `projects/PROJ-188-evaluating-the-impact-of-llm-generated-c/` root directory
- [ ] T001b Create `code/` and `tests/` subdirectories
- [ ] T001c Create `data/` subdirectories: `raw/`, `intermediate/`, `processed/`
- [ ] T001d Create empty `__init__.py` files in `code/` and `tests/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (transformers, torch, statsmodels, sacrebleu, datasets, pandas, numpy)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 Setup `data/` directory structure: `raw/`, `intermediate/`, `processed/`
- [ ] T005 [P] Implement `code/utils/config.py` with seeds (42), paths, and constants (max_tokens=150, timeout=300s)
- [ ] T006 [P] Create `code/utils/metrics.py` with BLEU calculation and latency parsing helpers
- [ ] T007 Setup `code/__init__.py` and empty `tests/` directory
- [ ] T008 Configure environment variable loading for HuggingFace token and model paths

**Pre-implementation Test Skeletons (Write tests FIRST, ensure they FAIL)**

- [ ] T009 [P] [US1] Unit test for complexity labeling logic in `tests/test_curation.py` (Skeleton only)
- [ ] T010 [P] [US1] Integration test for model loading fallback (CodeLlama → TinyLlama) in `tests/test_curation.py` (Skeleton only)
- [ ] T011 [P] [US2] Unit test for randomization logic (stratified, seed=42) in `tests/test_survey_logic.py` (Skeleton only)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Curation and Explanation Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest CodeSearchNet corpus, label complexity, and generate LLM explanations (with CPU-tractable fallback)

**Independent Test**: The script produces a JSON file with ≥20 snippets, valid explanations <150 tokens, and correct complexity labels.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement data ingestion in `code/01_data_curation.py`: Fetch Python subset from CodeSearchNet (HuggingFace `codeparrot/code-search-net`)
- [ ] T013 [US1] Implement cyclomatic complexity calculation and labeling (low/medium/high) for each snippet in `code/01_data_curation.py`
- [ ] T014 [US1] Implement LLM explanation generation in `code/01_data_curation.py`:
  - **⚠️ CONSTITUTIONAL WARNING**: Constitution Principle VII mandates **StarCoder-15B** (200 tokens). Spec FR-001 mandates **CodeLlama-7B** (150 tokens). This task implements the Spec (CodeLlama-7B) but flags a constitutional violation. A ratified amendment is required to resolve this drift.
  - Attempt CodeLlama with low-precision quantization and CPU device map.
  - **Fallback Logic**: If OOM or timeout, switch to TinyLlama (verified CPU-tractable) as per Plan.md.
  - Enforce a token limit and a multi-retry backoff strategy.
- [ ] T015 [US1] Implement output serialization: Save `data/intermediate/explanations.json` with fields: `snippet_id`, `code`, `complexity`, `explanation`, `token_count`, `model_used`, `status` (success/skipped).
- [ ] T016 [US1] Implement validation script to verify: no nulls, all labels valid, token counts <150, and N ≥ 20.
- [ ] T017 [US1] Add logging for skipped snippets and fallback triggers.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Study Survey Construction and Deployment (Priority: P2)

**Goal**: Construct survey logic (simulation) for three conditions, randomization, and data recording.

**Independent Test**: Mock survey logic correctly assigns conditions, records latency, and outputs structured CSV.

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement participant randomization in `code/02_survey_logic.py`: Stratified assignment to Code Only, Code+LLM, Code+Docstring (seed=42).
- [ ] T019 [US2] Implement condition rendering logic:
  - Condition A: Code only.
  - Condition B: Code + LLM Explanation (from `explanations.json`).
  - Condition C: Code + Official Docstring (or "No Doc" placeholder if missing).
- [ ] T020 [US2] Implement mock survey runner: Simulate N participants (or load external CSV) submitting answers with random latency >30s.
  - **[Depends on: T014]**
- [ ] T021 [US2] **Primary Deliverable**: Implement a script to ingest real participant data (from a deployed survey or CSV) into `data/intermediate/responses.csv`.
  - **Secondary Deliverable**: Implement a mock runner for testing that simulates N participants with random latency.
  - Output columns: `participant_id`, `condition`, `snippet_id`, `answer` (bool), `latency_ms`, `timestamp`.
- [ ] T022 [US2] Add filtering logic for invalid participants (<30s total time or >80% missing) and log exclusion counts.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Robustness Reporting (Priority: P3)

**Goal**: Execute LMM analysis, Tukey post-hoc, and BLEU sensitivity sweep.

**Independent Test**: Analysis script runs on synthetic data, produces F-stat/p-values, and generates sensitivity report.

### Implementation for User Story 3

- [ ] T023 [P] [US3] Unit test for LMM model fitting (statsmodels MixedLM) with synthetic data in `tests/test_analysis.py`
- [ ] T024 [P] [US3] Unit test for BLEU calculation and sensitivity sweep logic in `tests/test_analysis.py`

### Analysis Implementation

- [ ] T025 [US3] Implement data cleaning in `code/03_analysis.py`: Filter invalid participants, merge with snippet data (complexity, explanation).
  - **[Depends on: T014, T022]**
- [ ] T026 [US3] Implement Linear Mixed Model (LMM) in `code/03_analysis.py`:
  - **⚠️ CONSTITUTIONAL DRIFT WARNING**: Plan.md (Complexity Tracking) mandates a **GLMM with SnippetID random effects** claiming Spec is invalid. This task follows **Spec FR-005** which mandates **random intercepts for participants only**. The Plan.md requires amendment to resolve this conflict.
  - Fixed effects: `condition`, `complexity`, `condition:complexity`.
  - Random intercepts: `participant_id` (ONLY).
  - Family: Gaussian.
  - **[Depends on: T025]**
- [ ] T027 [US3] Implement post-hoc Tukey HSD test for pairwise condition comparisons with adjusted p-values.
  - **[Depends on: T026]**
- [ ] T028 [US3] Implement BLEU sensitivity sweep:
  - Calculate BLEU scores for LLM explanations vs. official docstrings (reference).
  - Re-run analysis on subsets where BLEU scores meet varying high-quality thresholds.
  - **Output Artifact**: Save `data/processed/sensitivity_report.csv` with columns: `threshold`, `accuracy_mean`, `latency_mean`, `p_value_interaction`.
  - **[Depends on: T026]**
- [ ] T029 [US3] Generate final report:
  - Include F-stat/p-value for interaction, Tukey results, sensitivity chart/table.
  - **Mandatory**: Include the exact FR-009 limitation statement: "BLEU similarity measures fidelity to the baseline (docstring) rather than intrinsic explanation quality."
  - **[Depends on: T027, T028]**
- [ ] T030 [US3] Calculate and verify participant pass rate:
  - Compute percentage of recruited participants passing quality filters (>30s time, <80% missing).
  - **Validation**: Verify pass rate >= 90% (SC-003). If < 90%, emit a critical error or flag the pipeline as failed.
  - Save results to `data/processed/analysis_results.json` and append to `data/processed/final_report.md`.
  - **[Depends on: T022, T025]**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `README.md` and `docs/`
- [ ] T032 Code cleanup and refactoring
- [ ] T033 Performance optimization (ensure CPU inference completes within 6h)
- [ ] T034 [P] Run `pytest` on all test suites
- [ ] T035 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T014** (explanations.json) for T019/T020
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on T014** (explanations.json) and **T022** (responses.csv) for full analysis.

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
Task: "Unit test for complexity labeling logic in tests/test_curation.py"
Task: "Integration test for model loading fallback in tests/test_curation.py"

# Launch models for User Story 1 together:
Task: "Implement data ingestion in code/01_data_curation.py"
Task: "Implement complexity labeling in code/01_data_curation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify N≥20, valid explanations).
5. Deploy/demo if ready.

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
   - Developer A: User Story 1 (Data & Inference)
   - Developer B: User Story 2 (Survey Logic)
   - Developer C: User Story 3 (Analysis - can mock data initially)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Do not use `load_in_8bit` or CUDA-specific device maps. Use `load_in_4bit` with CPU device map or fallback to TinyLlama to ensure execution on GitHub Actions `ubuntu-latest` (multi-core CPU, sufficient RAM).
- **Data Integrity**: All analysis must use real data from `explanations.json` and `responses.csv`. Do not fabricate synthetic input data for the final run.
- **Task Ordering**: T014 (Generation) must complete before T019/T020 (Survey Logic) can use the explanations. T022 (Responses) must complete before T025/T026 (Analysis) can run the full pipeline.
- **Constitutional Warnings**: Tasks T013 and T026 contain explicit warnings about conflicts between the Constitution (StarCoder, Participant-only LMM) and the Spec/Plan (CodeLlama, SnippetID GLMM). These tasks implement the Spec but flag the governance drift.