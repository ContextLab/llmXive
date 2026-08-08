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

- [ ] T001b1 [P] Create `src/ingestion/__init__.py` (empty file or minimal docstring)
- [ ] T001b2 [P] Create `src/retrieval/__init__.py` (empty file or minimal docstring)
- [ ] T001b3 [P] Create `src/evaluation/__init__.py` (empty file or minimal docstring)
- [ ] T001b4 [P] Create `src/validation/__init__.py` (empty file or minimal docstring)
- [ ] T001b5 [P] Create `src/validate/__init__.py` (empty file or minimal docstring)
- [ ] T001b6 [P] Create `src/utils/__init__.py` (empty file or minimal docstring)
- [ ] T001c [P] Create `.gitkeep` files in `data/raw/`, `data/processed/`, `data/results/`, `artifacts/synthesized_adapters/`, `specs/001-lattentskill-retrieval-geometry/contracts/`
- [X] T002a Create `requirements.txt` with pinned versions for: `torch`, `numpy`, `scikit-learn`, `sentence-transformers`, `transformers`, `pandas`, `scipy`, `llama-cpp-python`, `pytest`. **REMOVE** `faiss-cpu` as it is not in the plan's approved dependencies.
- [X] T002b Run `pip install -r requirements.txt` to verify dependency resolution
- [X] T003a [P] Create `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections (line-length=88, target-version=py311)
- [ ] T003b [P] Create `.ruff.toml` with specific ignore rules and line-length settings

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `src/utils/config.py` for seed pinning, path resolution, and environment variable loading
- [X] T005 [P] Implement `src/utils/versioning.py` to compute SHA256 hashes for artifacts and update `state/projects/...yaml`
- [X] T006a [P] Create `data_sources.yaml` defining the canonical URLs/IDs for NAB, UCI, HuggingFace, and LatentSkill repo datasets to serve as the source of truth for validation.
- [X] T006 Create `src/validate/citation_check.py` to verify dataset URLs listed in `data_sources.yaml`. **Implementation**: Create the script to perform HTTP 200 checks and metadata schema validation against the URLs defined in `data_sources.yaml`. (Depends on T006a, T004)
- [ ] T007 Create `specs/001-lattentskill-retrieval-geometry/contracts/skill-vector.schema.yaml` and `evaluation-result.schema.yaml`
- [X] T008 Setup `tests/contract/test_schemas.py` to validate JSON/YAML outputs against contracts
- [X] T009 Configure `src/ingestion/__init__.py` and `src/retrieval/__init__.py` package structures
- [X] T012 [US1] Implement `src/ingestion/download_weights.py` to fetch real LoRA weights from the **HuggingFace dataset 'latent-skills/alfworld-weights'** and **'latent-skills/searchqa-weights'** for ALFWorld and Search-QA benchmarks. **Execute** `src/validate/citation_check.py` (T006) **first** to verify the source. **If real weights are unavailable**, generate a documented proxy using `numpy.random.normal` with shape matching the expected A/B matrices and `dtype=float32`, ensuring structural identity. Mark metadata with `is_proxy=true`. **NEVER** fall back to random data without this specific generation method; the proxy must preserve matrix dimensions. Raise an exception only if the proxy generation logic itself fails. Log the exact resolved URL/ID used. (Depends on T006, T004)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Constructing the Skill Vector Database (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-trained LoRA adapters (A and B matrices) from ALFWorld and Search-QA, flatten them into normalized high-dimensional vectors, and generate a static CPU-compatible index.

**Independent Test**: System loads raw LoRA weights, normalizes them, and outputs a `.npy` or `.npz` index file with metadata without requiring GPU.

### Implementation for User Story 1

- [X] T013 [US1] Implement `src/ingestion/flatten_lora.py` (FR-001) to load A/B matrices, flatten to 1D, and apply L2 normalization
- [ ] T014 [US1] Implement `src/retrieval/vector_db.py` (FR-001) to construct and save the static index to `data/processed/skill_index.npz`
- [X] T015 [US1] Add validation in `src/ingestion/flatten_lora.py` to ensure consistent dimensions across all adapters
- [X] T016 [US1] Add logging for ingestion metrics (vectors processed, index size) in `src/ingestion/flatten_lora.py`

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test for `src/ingestion/flatten_lora.py` to verify vector dimensionality matches A*B product in `tests/unit/test_ingestion.py`. (Depends on T013 completion)
- [X] T011 [P] [US1] Integration test for ingestion pipeline in `tests/integration/test_pipeline.py` verifying index generation on CPU. (Depends on T013 completion)

**Checkpoint**: Skill Vector Database is generated and ready for retrieval.

---

## Phase 4: User Story 2 - Executing Retrieval and Interpolation Strategies (Priority: P2)

**Goal**: Query the Skill Vector Database using text embeddings, retrieve nearest neighbors, and synthesize LoRA adapters via unweighted mean and cosine-weighted averaging.

**Independent Test**: System takes a novel task description, executes retrieval/interpolation, and outputs synthesized LoRA adapter files on CPU.

### Implementation for User Story 2

- [X] T019 [US2] Implement `src/retrieval/query.py` (FR-002) to generate query vectors using `all-MiniLM-L6-v2`. **Include** logic to measure and log wall-clock latency for text embedding generation to satisfy SC-003. (Depends on T014)
- [X] T020 [US2] Implement `src/retrieval/strategies.py` (FR-003) for: (1) Single Nearest Neighbor, (2) Unweighted Arithmetic Mean (k-top), (3) Cosine-Weighted Averaging. **Include** logic to measure and log wall-clock latency for retrieval/interpolation to satisfy SC-003.
- [X] T021 [US2] Implement `src/retrieval/strategies.py` to handle edge cases (out-of-distribution queries, identical similarity scores)
- [X] T022 [US2] Implement `src/retrieval/strategies.py` to synthesize and **save** the LoRA adapter file (A/B matrices) to `artifacts/synthesized_adapters/` based on query results; explicitly **DO NOT** apply the adapter to a model or run inference in this task (application logic is deferred to T026/US3).
- [ ] T022b [US2] Implement `src/validation/reconstruction_error.py` to calculate the cosine distance (reconstruction error) between the synthesized LoRA weights and the true weights of a known composite task. **Output** the error value to `data/results/reconstruction_error.json`. (Depends on T022)
- [X] T023 [US2] Add logging for retrieval latency (SC-003) and similarity scores in `src/retrieval/query.py`

### Validation for User Story 2 (Blocking Gate for US3)

- [ ] T030 [US2] Implement `src/validation/linearity_check.py` ([FR-007]) to calculate Pearson correlation between text-space and weight-space distances for a held-out set of known task pairs. **Output** the correlation value and a validity flag (True if >= 0.6, False otherwise) to `data/results/linearity_check.json`. **DO NOT** raise an error if the threshold is not met; the experiment must proceed to measure the impact of non-linearity. (Depends on T014, T019)

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for `src/retrieval/strategies.py` verifying unweighted and weighted averaging math in `tests/unit/test_strategies.py`
- [X] T018 [P] [US2] Contract test for `src/retrieval/query.py` output format in `tests/contract/test_schemas.py`

**Checkpoint**: Retrieval and interpolation mechanisms produce valid synthesized adapters; linearity assumption validated (or measured).

---

## Phase 5: User Story 3 - Validating Performance via Environment Logic (Priority: P3)

**Goal**: Evaluate synthesized adapters on composite tasks using environment logic, run multiple trials (N≥5), and perform statistical testing with BH correction.

**Independent Test**: System runs evaluation, outputs success/failure logs, and generates a statistical report with p-values and BH correction.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/evaluation/runner.py` (FR-004) to apply adapters (from T022) to a frozen base LLM (via `llama-cpp-python` GGUF, model path: `data/models/llama-2-7b-q4_0.gguf`, quantization: q4_0) and execute environment logic (ALFWorld/Search-QA). (Depends on T022, T030, T014, T019) <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T026b [US3] Implement memory validation and streaming/chunking logic in `src/evaluation/runner.py` to ensure the base LLM inference fits within 7GB RAM. Explicitly log memory usage during the first run and fail loudly if it exceeds **6.5 GB**. (Depends on T026)
- [X] T027 [US3] Implement `src/evaluation/runner.py` loop to execute **N >= 5** independent runs per task (FR-008) and record binary outcomes, calculating the **mean of these binary outcomes** to establish a stable success probability. (Depends on T026b)
- [X] T028 [US3] Implement `src/evaluation/stats.py` (FR-005) to perform paired t-test or Wilcoxon signed-rank test on success rates between strategies and baseline. (Depends on T027)
- [X] T029 [US3] Implement `src/evaluation/stats.py` (FR-006) to apply Benjamini-Hochberg correction for multiple comparisons across all primary strategies and **sensitivity sweeps** (T031). (Depends on T028, T031)
- [ ] T031 [US3] Implement sensitivity analysis logic (SC-004) for **k in {1, 3, 5}** in `src/retrieval/strategies.py` and `src/evaluation/runner.py`. **Output** results to `data/results/stats_report.json` under the key `sensitivity_analysis`. (Depends on T020, T026) <!-- FAILED: unspecified -->
- [ ] T032 [US3] Generate final report in `data/results/stats_report.json` including p-values, BH-adjusted q-values, reconstruction errors (SC-005, from T022b), and linearity correlation (from T030). (Depends on T031, T029, T022b, T030)

### Tests for User Story 3

- [X] T024 [P] [US3] Contract test for `src/evaluation/stats.py` output schema in `tests/contract/test_schemas.py`
- [X] T025 [P] [US3] Integration test for full evaluation loop in `tests/integration/test_pipeline.py`

**Checkpoint**: Evaluation complete with statistical validation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T033a Update `README.md` with installation instructions, usage examples, and data source details
- [ ] T033b Create `docs/api.md` with function signatures and module descriptions
- [ ] T034 Code cleanup and refactoring of `src/retrieval/strategies.py`
- [ ] T036 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T037 Run `src/validate/citation_check.py` to verify all dataset sources
- [ ] T038 Run `quickstart.md` validation to ensure full pipeline reproducibility

**Removed Tasks**: T035a, T035b1, T035b2 (FAISS/PQ optimization) removed as they constitute scope creep and violate the CPU-only standard library constraint. Latency benchmarking (SC-003) is now integrated into T019 and T020.

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T022 (Synthesis) and T026 (Runner setup)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Scripts before execution logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT** T006 (sequential prerequisite) and T012 which depends on T006.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel **after** the implementation task they depend on is complete.
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (after T013 is done):
Task: "Unit test for flatten_lora.py in tests/unit/test_ingestion.py"
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
- **Constraint**: All tasks MUST run on CPU-only free-tier CI (limited cores, 7GB RAM). No `bitsandbytes` CUDA usage. Use `llama-cpp-python` (GGUF) for inference.
- **Data**: No fabrication. All datasets must be fetched from real sources (specifically the LatentSkill repository for weights). If real weights are unavailable, use a documented proxy with `is_proxy=true` flag, generated via `numpy.random.normal` with matching shapes.
- **Critical Data Hygiene**: `src/ingestion/download_weights.py` (T012) MUST raise an exception only if the proxy generation logic fails; otherwise, it must log the unavailability and proceed with the proxy.
- **Memory Management**: T012 and T013 must stream or chunk the LoRA weight loading to ensure the 7GB RAM limit is not exceeded during ingestion of large adapters. T026b must explicitly validate memory during inference with a 6.5 GB threshold.
- **Statistical Rigor**: T030 must output the correlation value and validity flag to the report, not halt execution.
- **Sensitivity Analysis**: T031 must use k in {1, 3, 5} per SC-004.
- **Latency Reporting**: Latency logging is integrated into T019 and T020 to satisfy SC-003.