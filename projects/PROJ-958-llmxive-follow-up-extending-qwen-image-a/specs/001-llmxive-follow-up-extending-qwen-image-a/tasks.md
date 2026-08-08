# Tasks: llmXive follow-up: extending "Qwen-Image-Agent: Bridging the Context Gap in Real-World Image Generation"

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

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`)
- [ ] T002 Initialize Python 3.11 project with dependencies (`pandas`, `numpy`, `scikit-learn`, `nltk`, `spacy`, `torch`, `transformers`, `statsmodels`, `textstat`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/config.py` with pinned random seeds, path configurations, and threshold constants (0.2, 0.6)
- [ ] T005 [P] Implement `code/utils.py` with logging infrastructure, error handling wrappers, and domain stratification helpers
- [ ] T006a [P] [US1] Setup `code/data_loader.py` to stream IA-Bench dataset (prompts + images) using `datasets.load_dataset(streaming=True)` and download real images to `data/raw/ia-bench/` with checksums
- [ ] T006b [P] [US3] Setup `code/data_loader.py` to fetch "human-verified reference descriptions" from the dataset (IA-Bench) and save to `data/raw/ia-bench/references.jsonl` with checksums
- [ ] T006c [P] [US1] Setup `code/data_loader.py` to download WISE-Verified dataset (prompts + images + metadata) using explicit URL/package fetch to `data/raw/wise-verified/`
- [ ] T007 [P] [US1] Implement `code/data_loader.py` logic to fail loudly if real data fetch fails (NO synthetic fallback) for IA-Bench
- [ ] T007b [P] [US1] Implement `code/data_loader.py` logic to fail loudly if WISE-Verified fetch fails (NO synthetic fallback) and validate WISE-Verified schema
- [ ] T008 Implement `code/main.py` orchestration script including the `Reference-Validator` gate invocation before data loading

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ambiguity Scoring & Dataset Stratification (Priority: P1) 🎯 MVP

**Goal**: Compute a deterministic "Ambiguity Score" (0.0–1.0) for every input prompt using only syntactic complexity and lexical diversity, explicitly excluding semantic embeddings.

**Independent Test**: Run the scoring script on a known subset of prompts and verify the output CSV contains scores, syntactic features, and lexical features, with no semantic embedding vectors present.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for `code/scoring.py` in `tests/unit/test_scoring.py` verifying no semantic embeddings are used (check for absence of BERT/CLIP text encoder calls)
- [ ] T010 [P] [US1] Unit test for malformed prompt handling in `tests/unit/test_scoring.py` (verify default 0.0 score and warning log)

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `code/scoring.py` with syntactic complexity metrics (parse tree depth, clause count) using `nltk`/`spacy`
- [ ] T012 [P] [US1] Implement `code/scoring.py` with lexical diversity metric (MTLD) using `textstat`
- [ ] T013 [US1] Implement the weighted average formula in `code/scoring.py` to combine metrics into a raw score
- [ ] T013b [US1] Implement `code/scoring.py` normalization logic to clamp raw score strictly to [0.0, 1.0] range (min-max scaling)
- [ ] T014 [US1] Implement logic in `code/scoring.py` to handle parse failures gracefully (assign 0.0, log warning)
- [ ] T015 [US1] Create script `code/run_scoring.py` to process the full dataset (IA-Bench + WISE-Verified) and write `data/derived/scoring_results.csv`
- [ ] T015b [US1] Add logic in `run_scoring.py` to output reference metadata (if available) alongside scores
- [ ] T016 [US1] Add logging in `code/scoring.py` to confirm no semantic embeddings were used during execution

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hybrid Routing & Execution Simulation (Priority: P2)

**Goal**: Implement a deterministic "Router" that classifies prompts into "low," "medium," or "high" ambiguity categories and routes them to either rule-based expansion or simulated agent execution.

**Independent Test**: Feed a mix of clearly simple and complex prompts and verify that simple prompts trigger the rule-based path (logging "Router: Low") while complex prompts trigger the agent path (logging "Router: High").

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for `code/router.py` in `tests/unit/test_router.py` verifying threshold logic (< 0.2, 0.2–0.6, > 0.6)
- [ ] T018 [P] [US2] Unit test for `code/simulation.py` in `tests/unit/test_simulation.py` verifying mock generation time formula

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/router.py` with deterministic classification logic based on Ambiguity Score thresholds
- [ ] T020 [P] [US2] Implement `code/expansion.py` with rule-based context expansion module (fixed templates) for low/medium ambiguity
- [ ] T020b [US2] Implement `code/expansion.py` to calculate and expose "simulated token count" for the expanded text output
- [ ] T021 [US2] Implement `code/simulation.py` with deterministic mock logic: mock generation time = 15 ms/token + 500ms overhead
- [ ] T022 [US2] Integrate Router, Expansion, and Simulation in `code/main.py` to process the dataset and log routing decisions (FR-007)
- [ ] T023 [US2] Add logging in `code/main.py` to record simulated token counts (from both expansion and agent paths) and latency
- [ ] T024 [US2] Write routing logs to `data/derived/routing_decisions.csv` including input score, category, target path, and token counts

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fidelity Measurement & Threshold Detection (Priority: P3)

**Goal**: Compute "Context Fidelity" delta using frozen CLIP (ViT-B/32) against human-verified references and identify the "knee point" via piecewise linear regression.

**Independent Test**: Run the regression analysis on pre-computed data and verify the output includes a calculated knee point, a plot, and a statistical justification (F-test) that the piecewise model is superior.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for `code/fidelity.py` in `tests/unit/test_fidelity.py` verifying CLIP inference and error handling (skip on format mismatch)
- [ ] T026 [P] [US3] Unit test for `code/regression.py` in `tests/unit/test_regression.py` verifying F-test and knee point detection logic

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/fidelity.py` with frozen CLIP (ViT-B/32) inference, CPU-batched processing, and delta calculation (Baseline vs. Hybrid) using **human-verified reference descriptions** from `data/raw/ia-bench/references.jsonl`
- [ ] T028 [P] [US3] Implement `code/fidelity.py` to handle CLIP failures gracefully (log error, skip data point, continue)
- [ ] T032a [US3] Implement `code/regression.py` to validate presence of "visual domain" metadata in the dataset; if missing, flag for limitation report
- [ ] T032b [US3] Implement `code/regression.py` with stratified regression analysis by visual domain (if metadata exists) OR generate a formal "limitation report" stating inability to stratify (if metadata missing)
- [ ] T029 [US3] Implement `code/regression.py` with piecewise linear regression to identify the "knee point" where slope change < 0.01
- [ ] T030 [US3] Implement statistical validation in `code/regression.py` including F-test (p < 0.05) comparing piecewise vs. linear models
- [ ] T031 [US3] Implement permutation test (A sufficient number of permutations will be conducted to ensure robust statistical inference., alpha = 0.05) in `code/regression.py` to validate significance of fidelity difference below threshold
- [ ] T033 [US3] Create script `code/run_fidelity_analysis.py` to orchestrate CLIP scoring and regression, outputting `data/derived/regression_results.json` (including knee point, p-values, and limitation report if applicable) and plots
- [ ] T034 [US3] Add logic to handle "No Threshold Found" case (R² < 0.85 or slope change < 0.01) and record max observed delta

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035a [P] Update `docs/data_flow.md` with diagram showing data flow from raw fetch (T006a/b/c) to derived results
- [ ] T035b [P] Update `docs/thresholds.md` with explicit definitions of routing thresholds (0.2, 0.6) and normalization logic
- [ ] T035c [P] Update `docs/api.md` with module descriptions for `scoring.py`, `router.py`, `fidelity.py`
- [ ] T036a [P] Refactor `code/scoring.py` to remove duplicate parsing logic and standardize error handling
- [ ] T036b [P] Refactor `code/fidelity.py` to standardize logging format and batch processing logic
- [ ] T037 Performance optimization for CLIP batching to fit within ~7GB RAM
- [ ] T038 [P] Additional unit tests for edge cases (e.g., empty datasets, all-malformed prompts)
- [ ] T039 Run `quickstart.md` validation to ensure end-to-end pipeline execution
- [ ] T040 Verify all artifacts in `data/derived/` are reproducible with pinned seeds

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. Produces `data/derived/scoring_results.csv`.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Consumes `scoring_results.csv`. Produces `routing_decisions.csv` and simulated metrics.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Consumes `scoring_results.csv`, `routing_decisions.csv`, and **human-verified references** (from T006b). Produces `regression_results.json`.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Modules before integration
- Core implementation before logging/reporting
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for code/scoring.py in tests/unit/test_scoring.py"
Task: "Unit test for malformed prompt handling in tests/unit/test_scoring.py"

# Launch implementation tasks for User Story 1 together:
Task: "Implement code/scoring.py with syntactic complexity metrics"
Task: "Implement code/scoring.py with lexical diversity metric (MTLD)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify no semantic embeddings, correct scoring)
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
   - Developer A: User Story 1 (Scoring)
   - Developer B: User Story 2 (Routing/Simulation)
   - Developer C: User Story 3 (Fidelity/Regression)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Data Rule**: The `code/data_loader.py` MUST fail loudly if real data fetch fails. NO synthetic fallbacks allowed.
- **Critical Scoring Rule**: `code/scoring.py` MUST NOT use any semantic embeddings (BERT, CLIP text). Only syntax/lexical.
- **Critical Compute Rule**: CLIP inference must be CPU-batched to fit in ~7GB RAM. If GPU is needed for speed, the execution stage will auto-offload, but the code must be written for CPU-first compatibility.
- **Critical Regression Rule**: If domain metadata is missing, do NOT aggregate or guess. Report limitation and perform global regression only (Task T032b).
- **Critical Fidelity Rule**: Fidelity calculation (T027) MUST use **human-verified reference descriptions** (Task T006b), not raw prompts or images.
- **Critical Normalization Rule**: Ambiguity score MUST be strictly clamped to [0.0, 1.0] (Task T013b).
- **Critical Token Count Rule**: Rule-based expansion MUST expose token counts (Task T020b) for logging (T023).