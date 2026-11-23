# Tasks: Quantifying Hallucination in LLM-Generated API Documentation

**Input**: Design documents from `/specs/001-quantify-hallucination/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-762-quantifying-hallucination-in-llm-generat/code/`)
- [ ] T002 Initialize Python 3.11 project with dependencies in `code/requirements.txt` (transformers, torch, spacy, radon, pandas, scikit-learn, datasets, pyyaml, statsmodels)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/src/hash_utils.py` for SHA-256 hashing and `data/hashes.json` manifest management (Constitution Principle V)
- [ ] T005 [P] Implement `code/src/download.py` to stream the CodeSearchNet Python subset using `datasets.load_dataset(..., streaming=True)`; ensure no synthetic fallbacks and loud failure on fetch errors (FR-001, Constitution Principle III)
- [ ] T006 [P] Create `code/src/preprocess.py` with AST parsing logic to extract parameters, return types, and function names; integrate `radon` for cyclomatic complexity with error handling for unparseable syntax (FR-001, FR-003)
- [ ] T007 [P] Create `code/src/metrics.py` implementing entity-overlap F1 calculation using `spacy` (`en_core_web_sm`) against source code AST entities (FR-003)
- [ ] T008a [P] [US1] Implement `code/src/config.py` to define model paths, random seed values, and environment variables (Constitution Principle I)
- [ ] T008b [P] [US1] Implement deterministic seeding logic in `code/src/generate.py` and `code/src/analysis.py` by calling `torch.manual_seed`, `numpy.random.seed`, and `random.seed` using values from `config.py` to ensure reproducibility (Constitution Principle I, FR-002)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Metric Calculation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest CodeSearchNet, generate descriptions using CPU-tractable models, and compute the entity-overlap F1 hallucination index.

**Independent Test**: Run on a small sample to verify a CSV is produced with valid hallucination indices within the expected normalized range.

### Tests for User Story 1

- [ ] T009 [P] [US1] Contract test for data schema in `code/tests/contract/test_dataset_schema.py`
- [ ] T010 [P] [US1] Unit test for entity extraction logic in `code/tests/unit/test_preprocess.py` (verify AST vs text extraction)
- [ ] T011 [P] [US1] Unit test for F1 calculation in `code/tests/unit/test_metrics.py` (verify edge cases: empty string, no entities)
- [ ] T012 [P] [US1] Integration test for end-to-end generation pipeline on a representative set of functions in `code/tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `code/src/generate.py` to load `codegen-350M` and `bigcode/starcoderbase-1b` in CPU mode (16-bit) with fixed prompts (FR-002)
- [ ] T014 [US1] Implement one-sentence constraint enforcement in `code/src/generate.py` (regex check for `.`, `!`, `?`; truncate to first sentence or a limited token count) (FR-002)
- [ ] T015 [US1] Implement the main generation loop in `code/src/generate.py` to process streamed data, generate descriptions for both models, and compute entity F1 scores (FR-001, FR-003, FR-010)
- [ ] T016 [US1] Implement output writing in `code/src/generate.py` to produce `data/processed/metrics.csv` with hashes recorded in `data/hashes.json` (FR-001)
- [ ] T017 [US1] Add logging for generation progress and memory usage to monitor GitHub Actions limits (SC-001, SC-002)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation Analysis & Visualization (Priority: P2)

**Goal**: Compute Spearman correlations and fit regression models between hallucination index and code characteristics, controlling for length bias.

**Independent Test**: Provide a pre-computed CSV and verify the script outputs correlation coefficients, p-values, and regression coefficients.

### Tests for User Story 2

- [ ] T018 [P] [US2] Contract test for analysis output schema in `code/tests/contract/test_analysis_schema.py`
- [ ] T019 [P] [US2] Unit test for Spearman correlation calculation in `code/tests/unit/test_analysis.py`
- [ ] T020 [P] [US2] Unit test for naming style metric (camelCase vs snake_case) extraction in `code/tests/unit/test_preprocess.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/src/analysis.py` to calculate token counts and naming style metrics from the processed data (FR-004)
- [ ] T022 [US2] Implement Spearman rank-correlation tests in `code/src/analysis.py` between hallucination index and predictors (token count, naming style, complexity) controlling for generated text length (FR-004)
- [ ] T023 [US2] Implement multiple linear regression (or GAM) in `code/src/analysis.py` with hallucination index as dependent variable and covariates included (FR-008)
- [ ] T024 [US2] Implement comparison logic for `codegen-350M` vs `starcoderbase-1b` results to isolate model-specific variance (FR-010)
- [ ] T025 [US2] Generate summary report in `results/analysis_report.json` containing raw/adjusted p-values and regression coefficients, explicitly using "correlation observed" phrasing (FR-007)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness & Sensitivity Verification (Priority: P3)

**Goal**: Perform sensitivity analysis, manual validation against a rubric, and multiplicity correction.

**Independent Test**: Verify output includes sensitivity table, validation report, and corrected p-values.

### Tests for User Story 3

- [ ] T026 [P] [US3] Contract test for validation report schema in `code/tests/contract/test_validation_schema.py`
- [ ] T027 [P] [US3] Unit test for Bonferroni correction logic in `code/tests/unit/test_analysis.py`
- [ ] T028 [P] [US3] Unit test for sensitivity threshold sweep logic in `code/tests/unit/test_analysis.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement sensitivity analysis in `code/src/analysis.py` sweeping thresholds {, 0.05, 0.1} and reporting "high hallucination" rates (FR-006)
- [ ] T030 [US3] Implement stratified random sampling (≥5%) for manual validation subset in `code/src/validate.py` (FR-009)
- [ ] T030c [US3] Generate manual ground-truth scores: Create `data/processed/manual_scores.csv` by implementing a deterministic simulation script that assigns scores based on the rubric (FR-009, SC-003). This task produces the artifact required for T032.
- [ ] T031a [US3] Implement the manual validation annotation interface: Create a CSV template or simple CLI tool in `code/src/validate.py` that allows human annotators to input scores (0-3) for the sampled subset based on the rubric (FR-009)
- [ ] T031b [US3] Implement aggregation logic in `code/src/validate.py` to read human inputs (from T031a) or simulated scores (from T030c), normalize them to [0, 1], and write to `data/processed/manual_scores.csv` (FR-009)
- [ ] T032 [US3] Implement correlation calculation between automated index and manual normalized score in `code/src/validate.py`; flag if $r < 0.7$ (FR-011, depends on T030c/T031b)
- [ ] T033 [US3] Implement Bonferroni correction for hypothesis tests in `code/src/analysis.py` and update the final report with adjusted p-values (FR-005)
- [ ] T034 [US3] Add disclaimer to final report explicitly stating no causal claims are made (FR-007, US-2)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` including `quickstart.md` and `research.md`
- [ ] T036 Code cleanup and refactoring to ensure memory efficiency in `code/src/generate.py`
- [ ] T037 Performance optimization for streaming data processing
- [ ] T038 [P] Additional unit tests for edge cases (empty LLM output, missing reference docstrings) in `code/tests/unit/`
- [ ] T039 [US1] Run `quickstart.md` validation on a fresh environment: Execute the pipeline for 1000 functions and explicitly verify memory usage < 7GB and runtime < 6 hours, recording the measured metrics in `results/performance_log.json` (SC-001, SC-002)
- [ ] T040 Verify `data/hashes.json` integrity across all intermediate files

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Critical**: Must complete before US2/US3 as it produces the metrics data.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Consumes output from US1.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Consumes output from US1 and US2.

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
Task: "Contract test for data schema in code/tests/contract/test_dataset_schema.py"
Task: "Unit test for entity extraction logic in code/tests/unit/test_preprocess.py"
Task: "Unit test for F1 calculation in code/tests/unit/test_metrics.py"
Task: "Integration test for end-to-end generation pipeline in code/tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Create project structure per implementation plan"
Task: "Initialize Python 3.11 project with dependencies"
Task: "Configure linting and formatting tools"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify metrics.csv is produced with valid indices)
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
   - Developer A: User Story 1 (Data Generation & Metrics)
   - Developer B: User Story 2 (Correlation & Regression)
   - Developer C: User Story 3 (Validation & Sensitivity)
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
- **Data Integrity**: Ensure `hash_utils.py` is invoked after every write to `data/processed/`.
- **Memory Constraints**: Strictly adhere to streaming data in `download.py` to avoid OOM on GitHub Actions free-tier.
- **Model Constraints**: Run `codegen-350M` and `bigcode/starcoderbase-1b` in CPU mode; enforce one-sentence output deterministically.
- **Reproducibility**: Ensure T008b is completed to pin random seeds in all generation and analysis scripts.
- **Manual Validation**: Ensure T030c, T031a, and T031b are completed to generate the `manual_scores.csv` artifact required for FR-011.
- **Validation Success**: T039 must explicitly verify the 7GB RAM and 6-hour time limits.