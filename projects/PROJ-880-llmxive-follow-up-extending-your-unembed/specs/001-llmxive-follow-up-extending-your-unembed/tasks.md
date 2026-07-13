# Tasks: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Input**: Design documents from `/specs/001-llmxive-crosslingual/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per plan.md structure)
- Paths shown below assume single project structure as defined in `plan.md`

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

- [ ] T001 Create project structure per `plan.md` (directories: `code/`, `data/raw/`, `data/processed/`, `tests/`, `contracts/`)
- [ ] T002 Initialize a Python project with `requirements.txt` (pins `transformers`, `torch`, `numpy`, `scipy`, `pandas`, `huggingface_hub`, `datasets`) using a compatible major version.
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` with paths, seeds, and hyperparameters (k=100, n_bootstrap=1000); ensure these constants are importable by `model_analyzer.py` and `statistical_test.py`
- [ ] T005 [P] Implement `code/validate_citations.py` to parse markdown, extract URLs, and verify against a local manifest (Constitution Principle II)
- [ ] T006 [P] Implement `code/data_loader.py` skeleton with functions for downloading, verifying checksums, and hashing datasets
- [ ] T007 Create base `code/__init__.py` and error handling infrastructure
- [ ] T008 Setup `tests/contract/test_schemas.py` skeleton for validating JSON output schemas

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract and Compare Edge Spectrum Subspaces (Priority: P1) 🎯 MVP

**Goal**: Compute the "edge spectrum" subspace (top-k singular vectors) of $W_U$ for Llama-3, Mistral, and BLOOM and calculate cosine similarity between subspaces to quantify geometric rotation.

**Independent Test**: The system runs SVD on three models and outputs a JSON report with non-zero cosine similarity scores between model pairs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for `similarity_report.schema.yaml` in `tests/contract/test_schemas.py`
- [ ] T010 [P] [US1] Unit test for SVD extraction on a mock matrix in `tests/unit/test_math.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/model_analyzer.py` to load unembedding matrix $W_U$ from HuggingFace models (Llama-3, Mistral, BLOOM) using CPU-only float32 loading, with error handling for missing/corrupted weight files
- [ ] T012 [US1] Implement SVD extraction in `code/model_analyzer.py` to compute top-k (k=100) singular vectors, handling numerical instability and rank-deficient matrices
- [ ] T013 [US1] Implement cosine similarity calculation in `code/model_analyzer.py` between subspace bases of English models vs. BLOOM
- [ ] T014 [US1] Implement `code/main.py` orchestrator to run the SVD and similarity pipeline, outputting `data/processed/similarity_matrix.json`
- [ ] T015 [US1] Implement logic to calculate anisotropy deviation from the hypothesized null (0.95) and compute the confidence interval for SC-001, outputting results to `data/processed/anisotropy_deviation.json`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Cross-Lingual Token Shift (Priority: P2)

**Goal**: Identify tokens with highest logit weights in the edge spectrum subspace for each language and compare semantic categories to determine typological shift.

**Independent Test**: The system projects frequency distributions onto the subspace and outputs ranked token lists distinct from the English baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Contract test for `token_attribution.schema.yaml` in `tests/contract/test_schemas.py`
- [ ] T017 [P] [US2] Unit test for centroid calculation logic in `tests/unit/test_math.py`

### Implementation for User Story 2

- [ ] T018 [US2] Implement `code/data_loader.py` functions to acquire and validate Common Crawl subsets (French/Chinese) and RedPajama lists, ensuring minimum size requirements
- [ ] T019 [US2] Implement `code/data_loader.py` to load frequency distributions and output `data/processed/frequency_distributions.json` (Requires: T018)
- [ ] T020 [US2] Implement `code/token_attribution.py` to project the frequency-weighted mean embedding vector (computed from RedPajama/Common Crawl frequencies) onto the Moore-Penrose pseudo-inverse of $W_U$ to compute the "mean embedding" vector (Requires: T019)
- [ ] T021 [US2] Implement token ranking logic in `code/token_attribution.py` to identify the top-ranked tokens driving subspace variance for each language. (Requires: T020)
- [ ] T022 [US2] Implement overlap ratio calculation between English and non-English top-10 token lists (Requires: T021)
- [ ] T023 [US2] Integrate `code/main.py` to execute the token attribution pipeline, outputting `data/processed/token_attribution_report.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Statistical Significance of Shift (Priority: P3)

**Goal**: Perform a permutation test (multiple iterations) using a Within-Language Baseline (Llama-3 vs. Mistral) to assess if the observed cross-lingual similarity is statistically significant.

**Independent Test**: The system runs a sufficient number of bootstrap iterations on CPU and outputs a p-value and significance flag.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for `permutation_result.schema.yaml` in `tests/contract/test_schemas.py`
- [ ] T025 [P] [US3] Unit test for permutation logic with fixed seed in `tests/unit/test_math.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/statistical_test.py` to generate the null distribution by bootstrapping the Within-Language Baseline (Llama-3 vs Mistral) similarity scores with added noise/variance scaling to approximate seed-variant differences (staged simplification proxy for model-seed null distribution due to unavailability of seed-variant models). Requires: T015 (US1 completion).
- [ ] T027 [US3] Implement the permutation test loop (1,000 iterations) in `code/statistical_test.py`, ensuring CPU-only execution and < 6h runtime
- [ ] T028 [US3] Implement p-value calculation and "Statistically Significant Shift" flag generation in `code/statistical_test.py`
- [ ] T029 [US3] Implement `code/external_validation.py` to fetch WALS data and compute correlation coefficient between subspace orientation and WALS features. If data is unavailable, the task must fail or output a 'data_unavailable' flag (no mock validation allowed).
- [ ] T030 [US3] Integrate `code/main.py` to run the statistical test and external validation, outputting `data/processed/permutation_result.json` and `data/processed/wals_validation.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Generate `data/checksums.json` including hashes for all raw data and code artifacts
- [ ] T032 Code cleanup and refactoring of `code/main.py` orchestrator
- [ ] T033 Performance optimization for SVD and permutation loops to ensure < 6h runtime
- [ ] T034 [P] Additional unit tests for edge cases (e.g., missing vocabulary mapping) in `tests/unit/`
- [ ] T035 Run `quickstart.md` validation and update documentation
- [ ] T036 Final verification of all JSON outputs against contract schemas

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for similarity_report.schema.yaml in tests/contract/test_schemas.py"
Task: "Unit test for SVD extraction on a mock matrix in tests/unit/test_math.py"

# Launch all models for User Story 1 together:
Task: "Implement code/model_analyzer.py to load unembedding matrix W_U..."
Task: "Implement SVD extraction in code/model_analyzer.py..."
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
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Feasibility Note**: All tasks strictly adhere to CPU-only constraints (no CUDA, no 8-bit quantization, float32 SVD on sampled k=100 vectors).
- **Data Integrity**: No synthetic data generation; all tasks require real datasets (Common Crawl, RedPajama) via `data_loader.py`.
- **Methodology Note**: T019 explicitly uses external frequency distributions (FR-005). T025 uses a bootstrapped Within-Language Baseline as a proxy for the seed-variant null distribution due to data availability constraints. T029 enforces strict WALS validation without mocks.