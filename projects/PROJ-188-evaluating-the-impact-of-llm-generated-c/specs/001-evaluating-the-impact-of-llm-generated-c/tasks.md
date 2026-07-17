# Tasks: Evaluating the Impact of LLM-Generated Code Explanations on Comprehension

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-llm-generated-c/`
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

## Phase 0: Governance & Prerequisites

**Purpose**: Resolve governance conflicts and establish prerequisites before implementation.

- [ ] T000 [P] [Governance] **CRITICAL PREREQUISITE**: Verify that the Constitution has been amended to align Principle VII (StarCoder-15B) with Spec FR-001 (CodeLlama-7B). If not amended, halt execution and log an error. This task must be completed before T014.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create `projects/PROJ-188-evaluating-the-impact-of-llm-generated-c/` at the repository root
- [ ] T001b Create `code/` and `tests/` subdirectories
- [ ] T001c Create `data/` subdirectories: `raw/`, `intermediate/`, `processed/`
- [ ] T001d Create empty `__init__.py` files in `code/` and `tests/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with `code/requirements.txt` containing: `transformers==4.36.0`, `torch==2.1.0+cpu`, `scikit-learn==1.3.0`, `statsmodels==0.14.0`, `sacrebleu==2.3.0`, `datasets==2.14.0`, `pandas==2.1.0`, `numpy==1.24.0`, `pyyaml==6.0.1`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 Setup `data/` directory structure: `raw/`, `intermediate/`, `processed/`
- [X] T005 [P] Implement `code/utils/config.py` with seeds (42), paths, and constants (max_tokens=150, timeout=300s)
- [X] T006 [P] Create `code/utils/metrics.py` with BLEU calculation and latency parsing helpers
- [X] T007 Setup `code/__init__.py` and empty `tests/` directory
- [ ] T008 Configure environment variable loading for HuggingFace token and model paths

**Pre-implementation Test Skeletons (Write tests FIRST, ensure they FAIL)**

- [X] T009 [P] [US1] Unit test for complexity labeling logic in `tests/test_curation.py`: Create `test_complexity_labeling()` that asserts `complexity_label in ['low', 'medium', 'high']` and currently fails because the function is not implemented.
- [X] T010 [P] [US1] Integration test for model loading fallback in `tests/test_curation.py`: Create `test_model_fallback()` that asserts `model_loaded == True` when CodeLlama fails and TinyLlama is used, and currently fails because the fallback logic is not implemented.
- [X] T011 [P] [US2] Unit test for randomization logic (stratified, seed=42) in `tests/test_survey_logic.py`: Create `test_stratified_randomization()` that asserts `len(condition_A) == len(condition_B) == len(condition_C)` and currently fails because the function is not implemented.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Curation and Explanation Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest CodeSearchNet corpus, label complexity, and generate LLM explanations (with CPU-tractable fallback)

**Independent Test**: The script produces a JSON file with ≥20 snippets, valid explanations <150 tokens, and correct complexity labels.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement data ingestion in `code/01_data_curation.py`: Fetch Python subset from CodeSearchNet (HuggingFace `codeparrot/code-search-net`)
- [X] T013 [US1] Implement cyclomatic complexity calculation and labeling (low/medium/high) for each snippet in `code/01_data_curation.py`
- [X] T014 [US1] Implement LLM explanation generation in `code/01_data_curation.py`:
 - **⚠️ GOVERNANCE BLOCK**: This task requires the Constitution to be amended to align with Spec FR-001. If not amended, halt execution with error "Constitution Amendment Required".
 - Attempt CodeLlama-7B (4-bit quantized) with CPU device map.
 - **Fallback Logic**: If `torch.cuda.is_available()` is False AND memory usage > 6GB, switch to TinyLlama (verified CPU-tractable) as per Plan.md.
 - Enforce a token limit and a multi-retry backoff strategy.
 - **Output**: Save `data/intermediate/explanations.json` with fields: `snippet_id`, `code`, `complexity`, `explanation`, `token_count`, `model_used`, `status` (success/skipped).
- [X] T015 [US1] Implement output serialization: Save `data/intermediate/explanations.json` with fields: `snippet_id`, `code`, `complexity`, `explanation`, `token_count`, `model_used`, `status` (success/skipped). <!-- FAILED: unspecified -->
- [ ] T016 [US1] Implement validation script to verify: no nulls, all labels valid, token counts <150, and N ≥ 20.
- [ ] T017 [US1] Add logging for skipped snippets and fallback triggers.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Study Survey Construction and Deployment (Priority: P2)

**Goal**: Construct survey logic (simulation) for three conditions, randomization, and data recording.

**Independent Test**: Mock survey logic correctly assigns conditions, records latency, and outputs structured CSV.

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement participant randomization in `code/02_survey_logic.py`: Stratified assignment to Code Only, Code+LLM, Code+Docstring (seed=42).
- [ ] T019 [US2] Implement condition rendering logic:
 - Condition A: Code only.
 - Condition B: Code + LLM Explanation (from `explanations.json`).
 - Condition C: Code + Official Docstring (or "No Doc" placeholder if missing).
- [X] T020a [P] [US2] Unit test for mock survey logic in `tests/test_survey_logic.py`: Create `test_mock_survey_logic()` that asserts condition assignment and latency recording, and currently fails because the logic is not implemented.
- [ ] T020b [US2] Implement mock survey runner in `code/02_survey_logic.py`: Simulate N=10 participants with random latency >30s. Output `data/intermediate/mock_responses.csv` with columns: `participant_id`, `condition`, `snippet_id`, `answer` (bool), `latency_ms`, `timestamp`. **[Depends on: T014]**
- [ ] T021a [US2] Implement script to ingest real participant data (from a deployed survey or CSV) into `data/intermediate/responses.csv`.
- [ ] T021b [US2] Implement script to ingest mock survey data (from T020b) into `data/intermediate/responses.csv`. **[Depends on: T020b]**
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
 - **⚠️ GOVERNANCE DRIFT**: Plan.md proposes GLMM with SnippetID random effects, but Spec FR-005 mandates LMM with participant-only random intercepts. This task implements the Spec.
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
 - **Logic**: Count participants where `latency > 30000` AND `missing_count < 0.8 * total_questions` (where `total_questions` = 3 per participant).
 - **Validation**: If pass rate < 90%, flag the report with a warning but DO NOT halt the pipeline.
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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T014** (explanations.json) for T019/T020b
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
- **Task Ordering**: T014 (Generation) must complete before T019/T020b (Survey Logic) can use the explanations. T022 (Responses) must complete before T025/T026 (Analysis) can run the full pipeline.
- **Constitutional Warnings**: Tasks T014 and T026 contain explicit warnings about conflicts between the Constitution and the Spec/Plan. These tasks implement the Spec but flag the governance drift.