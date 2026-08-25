# Tasks: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

**Input**: Design documents from `/specs/001-eval-code-doc-completeness/`
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

- [ ] T001 Create project structure: `code/`, `code/utils/`, `data/raw/`, `data/raw/repos/`, `data/processed/`, `tests/unit/`, `tests/integration/`, `state/`, `logs/`
- [ ] T001.5 [P] Fix spec.md FR-002 typo: change "codegen-mono" to "Salesforce/codegen-350M-mono" to eliminate ambiguity
- [ ] T002 Initialize Python 3.10+ project with `requirements.txt` dependencies (`transformers`, `torch`, `bitsandbytes`, `sentence-transformers`, `docstring_parser`, `scipy`, `requests`, `pyyaml`, `pytest`) AND implement logic to handle CPU fallback (8-bit/full precision) if 4-bit quantization fails
- [ ] T003 [P] Create `.flake8` (max-line-length=88) and `pyproject.toml` (black settings) configuration files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data loading utilities and model loaders.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement robust AST parser utility with error handling for syntax errors in `code/utils/ast_parser.py`
- [ ] T005 [P] Implement parameter coverage calculation logic using `docstring_parser` (text parsing only) in `code/utils/coverage.py`
- [ ] T006 [P] Implement statistical testing utility (Wilcoxon) in `code/utils/stats.py`
- [ ] T007 [P] Create base data models (MethodSignature, DocstringPair) and serialization logic in `code/utils/models.py`
- [ ] T008 [P] Configure memory monitoring utility (reading `/proc/self/status`) and logging infrastructure in `code/utils/monitor.py`
- [ ] T009 [P] Setup environment configuration management for model paths and rate-limit retries
- [ ] T010 [P] Implement logic to load frozen `data/raw/repo_list.json` (top repositories) and validate list structure in `code/utils/repo_loader.py`
- [ ] T011 [P] Implement model loader for `Salesforce/codegen-350M-mono` with 4-bit quantization and strict abort on deviation, verifying model name matches Constitution Principle VII exactly in `code/utils/model_loader.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Repository Data Extraction and Ground Truth Preparation (Priority: P1) 🎯 MVP

**Goal**: Extract public method signatures and human-written docstrings from a representative set of top PyPI repositories, **truncate the list to a maximum of 1,000 methods per repository** (fixed sample), and output a structured JSON dataset.

**Independent Test**: Run extraction on a single known repository (e.g., `requests`) and verify output JSON contains correct signatures, `null` for missing docstrings, and **row count <= 1,000** (or less if repo has fewer).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Unit test for AST parser skipping malformed files in `tests/unit/test_ast_parser.py`
- [ ] T013 [P] [US1] Unit test for `null` handling when no docstring exists in `tests/unit/test_coverage.py`
- [ ] T014 [P] [US1] Integration test for single-repo extraction pipeline in `tests/integration/test_extraction.py`

### Implementation for User Story 1

- [ ] T015 [P] [US1] Implement Git repository clone utility in `code/extract.py`
- [ ] T016 [US1] Implement file walker to filter `.py` files in `code/extract.py`
- [ ] T017 [US1] Integrate AST parser to extract public method signatures and docstrings in `code/extract.py`
- [ ] T018 [US1] Implement logic to truncate method lists to **max [deferred]** per repository (fixed sample) and log counts in `code/extract.py`
- [ ] T019 [US1] Implement JSON serialization and checksumming of raw data to `data/raw/repos/`, write SHA-256 to `data/checksums.json` AND record in `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml` in `code/extract.py`
- [ ] T020 [US1] Add validation to ensure `human_docstring` is `null` (not empty string) when missing in `code/extract.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - LLM Docstring Generation with Resource Constraints (Priority: P2)

**Goal**: Load the `Salesforce/codegen-350M-mono` model in **4-bit** quantization and generate docstrings for the extracted methods with a **fixed temperature**, ensuring completion within 6 hours on CPU.

**Independent Test**: Run generation on a subset of **50** methods. Verify output file contains generated text, model loads in CPU mode (or 8-bit fallback), and memory stays **under 7 GB RAM** as monitored via `/proc/self/status`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for model loading with 4-bit quantization and abort logic in `tests/unit/test_generation.py`
- [ ] T022 [P] [US2] Unit test for memory monitoring during generation in `tests/unit/test_monitor.py`
- [ ] T023 [P] [US2] Integration test for generation on a small batch in `tests/integration/test_generation.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement docstring generation loop with a **fixed temperature of 0.2** reading from `data/raw/repos/*.json` in `code/generate.py`
- [ ] T025 [US2] Integrate memory monitoring to abort if RAM > 7 GB, logging a specific `RAM_LIMIT_EXCEEDED` entry to `logs/monitor.log` and raising a `MemoryLimitException` in `code/generate.py`
- [ ] T026 [US2] Implement batch processing to handle repositories sequentially to manage memory reading from `data/raw/repos/*.json` in `code/generate.py`
- [ ] T027 [US2] Add logic to handle empty/whitespace generated docstrings (flag for review) reading from `data/raw/repos/*.json` in `code/generate.py`
- [ ] T028 [US2] Serialize generated results (including `generated_docstring`) to `data/processed/results.json` in `code/generate.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Parameter Coverage Analysis and Statistical Comparison (Priority: P3)

**Goal**: Calculate Parameter Coverage Scores, compute auxiliary semantic similarity, and perform Wilcoxon signed-rank test to determine statistical significance.

**Independent Test**: Feed synthetic dataset of balanced perfect matches and mismatches; verify Wilcoxon p-value < 0.05 and coverage scores align with labels.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for Parameter Coverage Score calculation edge cases (complex type hints) in `tests/unit/test_coverage.py`
- [ ] T030 [P] [US3] Unit test for semantic similarity calculation in `tests/unit/test_stats.py`
- [ ] T031 [P] [US3] Unit test for Wilcoxon test with small dataset warning in `tests/unit/test_stats.py`
- [ ] T032 [P] [US3] Integration test for full analysis pipeline on processed results in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement Parameter Coverage Score calculation: `(matched params / total AST params)` using AST-matching logic reading from `data/processed/results.json` in `code/analyze.py`
- [ ] T034 [US3] Implement semantic similarity calculation using `sentence-transformers/all-MiniLM-L6-v2` as auxiliary metric reading from `data/processed/results.json` in `code/analyze.py`
- [ ] T035 [US3] Implement Wilcoxon signed-rank test for paired Human vs. LLM scores reading from `data/processed/results.json` in `code/analyze.py`
- [ ] T036 [US3] Add logic to log warning if dataset size < 30 but proceed with calculation reading from `data/processed/results.json` in `code/analyze.py`
- [ ] T037 [US3] Generate final report with p-value, test statistic, and coverage rates to `data/processed/final_report.json` reading from `data/processed/results.json` in `code/analyze.py`
- [ ] T038 [US3] Handle complex type hints (e.g., `List[Dict[str, Any]]`) as unmatched but non-crashing reading from `data/processed/results.json` in `code/analyze.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Update README.md with installation instructions and usage examples
- [ ] T040 [P] Update quickstart.md with step-by-step execution guide
- [ ] T041 Code cleanup and refactoring (specific: refactor `extract.py` to use single entry point)
- [ ] T042 [P] Performance optimization: Verify total runtime < 6 hours including a **-minute safety buffer** on a fresh runner
- [ ] T043 [P] Add unit tests for uncovered code paths identified by coverage report
- [ ] T044 Run `python -m code.quickstart` and verify exit code 0
- [ ] T045 Run `scripts/verify_repro.sh` and ensure `data/checksums.json` matches previous run

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Data Dependency**: Requires output from US1 (`data/raw/repos/`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Data Dependency**: Requires output from US2 (`data/processed/results.json`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Utilities (AST, Coverage, Stats) in Phase 2 must be complete first
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
Task: "Unit test for AST parser skipping malformed files in tests/unit/test_ast_parser.py"
Task: "Unit test for null handling when no docstring exists in tests/unit/test_coverage.py"

# Launch all models for User Story 1 together:
Task: "Implement Git repository clone utility in code/extract.py"
Task: "Implement file walker to filter .py files in code/extract.py"
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
   - Developer B: User Story 2 (can start if mock data is available for dev, but final run needs US1)
   - Developer C: User Story 3 (can start if mock data is available for dev, but final run needs US2)
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
- **CRITICAL**: Data flow must be respected: US1 (Extract) → US2 (Generate) → US3 (Analyze). Do not run US2 before US1 produces data.
- **CRITICAL**: Model loading must explicitly handle CPU-only constraints and 4-bit quantization with abort on deviation.
- **CRITICAL**: All data sources must be real; no synthetic fallbacks for data loading.
- **CRITICAL**: Fixed sample size is a sufficient number of methods per repository to meet Spec's maximum limit ([deferred]).
- **NOTE**: Plan.md 'Performance Goals' section currently states 'Fixed a set of methods each'. This is a known inconsistency with the Spec ([deferred] cap) and must be corrected in the next plan revision.