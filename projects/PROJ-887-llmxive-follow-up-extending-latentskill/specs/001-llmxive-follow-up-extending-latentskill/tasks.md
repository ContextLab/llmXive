# Tasks: llmXive follow-up: extending "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills"

**Input**: Design documents from `/specs/001-lattentskill-retrieval-geometry/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with dependencies (`torch`, `numpy`, `scikit-learn`, `sentence-transformers`, `transformers`, `pandas`, `scipy`, `llama-cpp-python`, `pytest`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `src/utils/config.py` for seed pinning, path resolution, and environment variable loading
- [ ] T005 [P] Implement `src/utils/versioning.py` to compute SHA256 hashes for artifacts and update `state/projects/...yaml`
- [ ] T006 [P] Create `src/validate/citation_check.py` to verify dataset URLs (NAB, UCI, HuggingFace) before execution
- [ ] T007 Create `specs/001-lattentskill-retrieval-geometry/contracts/skill-vector.schema.yaml` and `evaluation-result.schema.yaml`
- [ ] T008 Setup `tests/contract/test_schemas.py` to validate JSON/YAML outputs against contracts
- [ ] T009 Configure `src/ingestion/__init__.py` and `src/retrieval/__init__.py` package structures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Constructing the Skill Vector Database (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-trained LoRA adapters (A and B matrices) from ALFWorld and Search-QA, flatten them into normalized high-dimensional vectors, and generate a static CPU-compatible index.

**Independent Test**: System loads raw LoRA weights, normalizes them, and outputs a `.npy` or `.npz` index file with metadata without requiring GPU.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for `src/ingestion/flatten_lora.py` to verify vector dimensionality matches A*B product in `tests/unit/test_strategies.py`
- [ ] T011 [P] [US1] Integration test for ingestion pipeline in `tests/integration/test_pipeline.py` verifying index generation on CPU

### Implementation for User Story 1

- [ ] T012 [US1] Implement `src/ingestion/download_weights.py` to fetch real LoRA weights from the **original LatentSkill repository (arXiv:2606.06087)** for ALFWorld and Search-QA benchmarks (no fabrication; do NOT use NAB/UCI for weights)
- [ ] T013 [US1] Implement `src/ingestion/flatten_lora.py` (FR-001) to load A/B matrices, flatten to 1D, and apply L2 normalization
- [ ] T014 [US1] Implement `src/retrieval/vector_db.py` (FR-001) to construct and save the static index to `data/processed/skill_index.npz`
- [ ] T015 [US1] Add validation in `src/ingestion/flatten_lora.py` to ensure consistent dimensions across all adapters
- [ ] T016 [US1] Add logging for ingestion metrics (vectors processed, index size) in `src/ingestion/flatten_lora.py`

**Checkpoint**: Skill Vector Database is generated and ready for retrieval.

---

## Phase 4: User Story 2 - Executing Retrieval and Interpolation Strategies (Priority: P2)

**Goal**: Query the Skill Vector Database using text embeddings, retrieve nearest neighbors, and synthesize LoRA adapters via unweighted mean and cosine-weighted averaging.

**Independent Test**: System takes a novel task description, executes retrieval/interpolation, and outputs synthesized LoRA adapter files on CPU.

### Tests for User Story 2

- [ ] T017 [P] [US2] Unit test for `src/retrieval/strategies.py` verifying unweighted and weighted averaging math in `tests/unit/test_strategies.py`
- [ ] T018 [P] [US2] Contract test for `src/retrieval/query.py` output format in `tests/contract/test_schemas.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `src/retrieval/query.py` (FR-002) to generate query vectors using `all-MiniLM-L6-v2`
- [ ] T020 [US2] Implement `src/retrieval/strategies.py` (FR-003) for: (1) Single Nearest Neighbor, (2) Unweighted Arithmetic Mean (k-top), (3) Cosine-Weighted Averaging
- [ ] T021 [US2] Implement `src/retrieval/strategies.py` to handle edge cases (out-of-distribution queries, identical similarity scores)
- [ ] T022 [US2] Implement `src/retrieval/strategies.py` to synthesize and **save** the LoRA adapter file (A/B matrices) to `artifacts/synthesized_adapters/` based on query results; explicitly **DO NOT** apply the adapter to a model or run inference in this task (application logic is deferred to T026/US3)
- [ ] T023 [US2] Add logging for retrieval latency (SC-003) and similarity scores in `src/retrieval/query.py`

**Checkpoint**: Retrieval and interpolation mechanisms produce valid synthesized adapters.

---

## Phase 5: User Story 3 - Validating Performance via Environment Logic (Priority: P3)

**Goal**: Evaluate synthesized adapters on composite tasks using environment logic, run multiple trials (N≥5), and perform statistical testing with BH correction.

**Independent Test**: System runs evaluation, outputs success/failure logs, and generates a statistical report with p-values and BH correction.

### Tests for User Story 3

- [ ] T024 [P] [US3] Contract test for `src/evaluation/stats.py` output schema in `tests/contract/test_schemas.py`
- [ ] T025 [P] [US3] Integration test for full evaluation loop in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/evaluation/runner.py` (FR-004) to apply adapters to a frozen base LLM (via `llama-cpp-python` GGUF) and execute environment logic (ALFWorld/Search-QA)
- [ ] T027 [US3] Implement `src/evaluation/runner.py` loop to execute $N \ge 5$ runs per task (FR-008) and record binary outcomes
- [ ] T028 [US3] Implement `src/evaluation/stats.py` (FR-005) to perform paired t-test/Wilcoxon signed-rank test
- [ ] T029 [US3] Implement `src/evaluation/stats.py` (FR-006) to apply Benjamini-Hochberg correction for multiple comparisons
- [ ] T030 [US3] Implement `src/validation/linearity_check.py` (FR-007) to calculate Pearson correlation between text-space and weight-space distances and **explicitly validate that correlation meets a predefined minimum threshold; raise an error if the threshold is not met**
- [ ] T031 [US3] Implement sensitivity analysis logic (SC-004) for $k \in \{1, 3, 5, 10\}$ in `src/retrieval/strategies.py`
- [ ] T032 [US3] Generate final report in `data/results/stats_report.json` including p-values, BH-adjusted q-values, and reconstruction errors (SC-005)

**Checkpoint**: Evaluation complete with statistical validation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T033 [P] Documentation updates in `docs/` and `README.md`
- [ ] T034 Code cleanup and refactoring of `src/retrieval/strategies.py`
- [ ] T035 [P] Performance optimization and benchmarking for the **entire skill selection mechanism** (retrieval + interpolation/averaging) to ensure total latency <1s per SC-003 and Principle VII
- [ ] T036 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T037 Run `src/validate/citation_check.py` to verify all dataset sources
- [ ] T038 Run `quickstart.md` validation to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T014 (Index generation)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T020 (Synthesis) and T026 (Runner setup)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Scripts before execution logic
- Core implementation before integration
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
# Launch all tests for User Story 1 together:
Task: "Unit test for flatten_lora.py in tests/unit/test_strategies.py"
Task: "Integration test for ingestion pipeline in tests/integration/test_pipeline.py"

# Launch implementation tasks (sequential within story, but can be parallelized if split):
Task: "Implement download_weights.py"
Task: "Implement flatten_lora.py"
Task: "Implement vector_db.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Index generation)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Retrieval)
4. Add User Story 3 → Test independently → Deploy/Demo (Evaluation)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Ingestion)
   - Developer B: User Story 2 (Retrieval)
   - Developer C: User Story 3 (Evaluation)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Constraint**: All tasks MUST run on CPU-only free-tier CI (cores, 7GB RAM). No `bitsandbytes` CUDA usage. Use `llama-cpp-python` (GGUF) for inference.
- **Data**: No fabrication. All datasets must be fetched from real sources (specifically the LatentSkill repository for weights).