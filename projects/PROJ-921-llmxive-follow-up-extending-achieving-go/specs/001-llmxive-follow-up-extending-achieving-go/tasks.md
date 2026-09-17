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

- [ ] T001a Create `code/` directory structure (`code/data`, `code/inference`, `code/scoring`, `code/analysis`, `code/utils`)
- [ ] T001b Create `data/` directory structure (`data/raw`, `data/processed`, `data/gold`)
- [ ] T001c Create `tests/` directory structure (`tests/unit`, `tests/integration`)
- [ ] T001d Create `code/__init__.py` and `tests/__init__.py`
- [ ] T001e Create `pyproject.toml` with project metadata and build backend
- [ ] T001f Create `.gitignore` for Python and research artifacts (`.pyc`, `__pycache__`, `data/`, `*.log`)
- [ ] T001g Initialize `requirements.txt` with pinned versions for `transformers>=4.40`, `torch>=2.0 (cpuonly)`, `datasets>=2.19`, `scipy`, `statsmodels`, `pandas`, `pyyaml`, `huggingface_hub`, `pytest` (per plan.md Primary Dependencies)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create base data models/entities in `code/data/models.py` (Prompt, Response, BenchmarkResult, Score)
- [ ] T004 Setup environment configuration management in `code/utils/config.py` (seeds, token limits, model paths)
- [ ] T005 [P] Implement checksumming and data hygiene utilities in `code/utils/checksum.py` (depends on T007 models)
- [ ] T006 [P] Configure audit logging infrastructure for failures/truncations in `code/utils/logging.py` (depends on T007 models)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Benchmark Ingestion and Model Inference (Priority: P1) 🎯 MVP

**Goal**: Load IMO/IPhO and OpenSci-Reason datasets, run SU-01 and baseline models on CPU, generate JSONL responses.

**Independent Test**: Verify inference pipeline generates valid JSONL output for both datasets within the time limit and RAM constraint.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Contract test for dataset loader in `tests/unit/test_data_loader.py`
- [ ] T010 [P] [US1] Integration test for full inference pipeline on sample prompts in `tests/integration/test_inference.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement IMO/IPhO dataset downloader and parser in `code/data/download.py` (Verified URL: `https://huggingface.co/datasets/math-olympiad` or equivalent verified source; verify exact dataset ID before coding)
- [ ] T012 [P] [US1] Implement OpenSci-Reason dataset loader (ScienceQA derived via `datasets.load_dataset("scienceqa")`) in `code/data/download.py` with streaming support for large files
- [ ] T013 [US1] Implement unified JSONL preprocessing in `code/data/preprocess.py` (converts raw data to `code/data/processed/unified.jsonl`). **Note**: Depends on completion of T011 and T012.
- [ ] T014 [US1] Implement CPU-only inference runner for SU-01 and baseline in `code/inference/runner.py` (batch_size=1, temperature=0.7)
- [ ] T015 [US1] Enforce hard token limit (2048) and log truncation events in `code/inference/runner.py` explicitly to prevent CI job timeouts on the free tier (per FR-006)
- [ ] T016 [US1] Implement "incomplete" flagging logic for prompts with <3 valid responses in `code/inference/runner.py`
- [ ] T017 [P] [US1] Add validation and error handling for OOM/CUDA failures in `code/inference/runner.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated Expert Simulation and Scoring (Priority: P2)

**Goal**: Score generated responses using a frozen, quantized LLM proxy (Llama-3-8B-INT4) on Novelty, Feasibility, Consistency.

**Independent Test**: Verify proxy model scores correlate >0.6 with the N=50 gold standard human-rated set.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for scoring logic (Novelty/Feasibility/Consistency extraction) in `tests/unit/test_scorer.py`
- [ ] T019 [P] [US2] Integration test for scoring pipeline against gold standard in `tests/integration/test_scoring.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement loading of `meta-llama/Meta-Llama-3-8B-Instruct` (INT4 via `bitsandbytes`) in `code/scoring/proxy_model.py`. **Fallback**: If OOM, fallback to a distilled 3B model (as per Spec Edge Cases).
- [ ] T021 [US2] Implement scoring logic to evaluate Novelty, Feasibility, Consistency (on a multi-point scale) in `code/scoring/scorer.py`
- [ ] T022 [US2] Implement low-confidence flagging (variance > 1.5 or entropy > 2.0) in `code/scoring/scorer.py`
- [ ] T023 [US2] Implement gold standard validation loader in `code/data/gold_standard.py`
- [ ] T024 [US2] Implement proxy model validation script to compute correlation >0.6 in `code/scoring/validator.py`
- [ ] T025 [US2] Integrate scoring pipeline to process `code/data/processed/unified.jsonl` and output `code/data/processed/scored.jsonl`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Rigidity Analysis (Priority: P3)

**Goal**: Compute Linear Mixed Effects (LME) model (primary per Plan) and supplementary Point-Biserial/t-test (per Spec) to analyze rigidity.

**Independent Test**: Verify synthetic dataset analysis yields expected LME coefficients and p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for statistical functions (LME, Point-Biserial, t-test) in `tests/unit/test_stats.py`
- [ ] T027 [P] [US3] Integration test for full analysis pipeline with synthetic data in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement Linear Mixed Effects (LME) model in `code/analysis/stats.py` (Primary method per Plan.md Summary & Complexity Tracking) to handle nested data and interaction effects.
- [ ] T034 [US3] Implement data aggregation logic specifically for LME (exclude low-confidence prompts, handle incomplete responses, structure for nested analysis) in `code/analysis/data_prep.py`. **Note**: Must precede T030 execution.
- [ ] T031 [P] [US3] Implement Point-Biserial correlation function in `code/analysis/stats.py` (Supplementary, per Spec FR-005)
- [ ] T032 [P] [US3] Implement paired t-test function in `code/analysis/stats.py` (Supplementary, per Spec FR-005)
- [ ] T033 [US3] Perform power analysis on fixed N=500 sample to verify sufficiency for target power=0.8 and effect size=0.5 in `code/analysis/power_analysis.py` (per FR-009). **Note**: Input is the fixed N=500 from spec; do not attempt to justify a variable number.
- [ ] T035 [US3] Implement final analysis pipeline to compute LME metrics, supplementary t-tests, and generate report in `code/analysis/report.py`
- [ ] T036 [US3] Generate final summary tables and plots in `code/analysis/report.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` (README, usage instructions)
- [ ] T038 Code cleanup and refactoring: Remove unused imports in `code/analysis/stats.py` (verified by `flake8 --select=F401 code/analysis/stats.py`)
- [ ] T039 Run `quickstart.md` validation to ensure full pipeline execution
- [ ] T040 [P] Additional unit tests for edge cases (ambiguous prompts, truncation) in `tests/unit/`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (inference results)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 output (scored results)

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
Task: "Contract test for dataset loader in tests/unit/test_data_loader.py"
Task: "Integration test for full inference pipeline on sample prompts in tests/integration/test_inference.py"

# Launch all models for User Story 1 together:
Task: "Implement IMO/IPhO dataset downloader and parser in code/data/download.py"
Task: "Implement OpenSci-Reason dataset loader in code/data/download.py"
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
- **Addressing Reviewer Concerns**:
  - **LME vs t-test**: T030 implements LME (Plan primary); T031/T032 implement t-test/Point-Biserial (Spec supplementary). LME is now the primary analysis method.
  - **Token Limits & Timeouts (FR-006)**: Task T015 explicitly links limit to CI timeouts.
  - **Ambiguous Prompts (Edge Case)**: Task T022 implements low-confidence flagging.
  - **Incomplete Responses (Edge Case)**: Task T016 flags prompts with <3 valid responses.
  - **Data Integrity (FR-001, FR-009)**: Tasks T011, T012, T033 ensure verified data sources and power analysis on fixed N=500.
  - **Proxy Validation (FR-008)**: Task T024 ensures the scoring model is validated against the N=50 gold standard.
  - **Fallback Logic**: Task T020 includes fallback to distilled 3B model as per Spec Edge Cases.
  - **Statistical Consistency**: The plan's LME model is now the primary implementation, resolving the contradiction with the spec's t-test requirement by treating the t-test as supplementary validation.