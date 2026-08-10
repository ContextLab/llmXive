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

- [X] T001b [P] Create all `__init__.py` files for the following exact paths: `src/ingestion/__init__.py`, `src/retrieval/__init__.py`, `src/evaluation/__init__.py`, `src/validation/__init__.py`, `src/validate/__init__.py`, `src/utils/__init__.py`. (Empty or minimal docstring)
- [X] T002a Create `requirements.txt` with pinned versions for: `torch`, `numpy`, `scikit-learn`, `sentence-transformers`, `transformers`, `pandas`, `scipy`, `llama-cpp-python`, `pytest`. **REMOVE** `faiss-cpu` as it is not in the plan's approved dependencies.
- [X] T002b Run `pip install -r requirements.txt` to verify dependency resolution
- [X] T003a [P] Create `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections (line-length=88, target-version=py311)
- [X] T003b [P] Create `.ruff.toml` with `line-length = 88` and `ignore = ["E501", "W293"]`
- [X] T001c [P] Ensure `data/`, `artifacts/`, and `data/raw/`, `data/processed/`, `data/results/` directories exist in the repo. **Note**: These directories should be added to `.gitignore` to prevent tracking of generated data. Do NOT create `.gitkeep` files here.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `src/utils/config.py` for seed pinning, path resolution, and environment variable loading
- [X] T005 [P] Implement `src/utils/versioning.py` to compute SHA256 hashes for artifacts and update `state/projects/...yaml`
- [X] T006a [P] Create `data_sources.yaml` defining the canonical URLs/IDs for NAB, UCI, HuggingFace, and LatentSkill repo datasets to serve as the source of truth for validation.
- [X] T006 [P] Create `src/validate/citation_check.py` to verify dataset URLs listed in `data_sources.yaml`. **Implementation**: Create the script to perform HTTP 200 checks AND validate the specific existence of weight files within the dataset (not just URL reachability). **Handle Fallback**: If the primary HF dataset is missing, the script must validate the existence of the arXiv source and prepare for fallback. (Depends on T006a, T004)
- [X] T012 [US1] Implement `src/ingestion/download_weights.py` to fetch real LoRA weights from the **HuggingFace dataset 'latent-skills/alfworld-weights'** (path: `weights/alfworld/*.npz`) and **'latent-skills/searchqa-weights'** (path: `weights/searchqa/*.npz`) for ALFWorld and Search-QA benchmarks. **Execute** citation check (T006) **first** to verify the source. **If real weights are unavailable, check for 'STAGED' mode (env var `PROJECT_STAGE=staged`):**
 - **In 'PROD' mode (default)**: **FAIL LOUDLY** with an exception. **DO NOT** generate proxy data.
 - **In 'STAGED' mode**: Generate a deterministic mock dataset using a fixed random seed (`np.random.seed(42)`) with dimensions `in_features=4096, out_features=1024` to unblock the pipeline for development. Log a CRITICAL warning that this is a mock.
 - **Expected Dimensions**: If real data is found, verify shapes match `in_features=4096, out_features=1024` (or log mismatch).
 - **Output**: Save real weights to `data/raw/alfworld_weights.npz` and `data/raw/searchqa_weights.npz`. Log the exact resolved URL/ID used. (Depends on T006, T004)
- [X] T007a [P] Create `specs/001-lattentskill-retrieval-geometry/contracts/skill-vector.schema.yaml` with the following content:
 ```yaml
 type: object
 properties:
 id: {type: string}
 task_desc: {type: string}
 vector: {type: array, items: {type: number}}
 metadata: {type: object}
 required: [id, task_desc, vector]
 ```
- [X] T007b [P] Create `specs/001-lattentskill-retrieval-geometry/contracts/evaluation-result.schema.yaml` with the following content:
 ```yaml
 type: object
 properties:
 task_id: {type: string}
 strategy: {type: string}
 success: {type: boolean}
 latency_ms: {type: number}
 required: [task_id, strategy, success]
 ```
- [X] T008 Setup `tests/contract/test_schemas.py` to validate JSON/YAML outputs against contracts
- [X] T009 Configure `src/ingestion/__init__.py` and `src/retrieval/__init__.py` package structures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Constructing the Skill Vector Database (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-trained LoRA adapters (A and B matrices) from ALFWorld and Search-QA, flatten them into normalized high-dimensional vectors, and generate a static CPU-compatible index.

**Independent Test**: System loads raw LoRA weights, normalizes them, and outputs a `.npy` or `.npz` index file with metadata without requiring GPU.

### Implementation for User Story 1

- [X] T013 [US1] Implement `src/ingestion/flatten_lora.py` (FR-001) to load A/B matrices from `data/raw/`, flatten to 1D, and apply L2 normalization. **Input**: Real weights from T012 (or mock if staged). (Depends on T012)
- [X] T014a [US1] Implement logic in `src/retrieval/vector_db.py` (FR-001) to load flattened vectors from T013, compute the index structure, and prepare data for serialization. (Depends on T013)
- [ ] T014b [US1] Execute `src/retrieval/vector_db.py` to construct and save the static index to `data/processed/skill_index.npz`. **Output**: Verify file existence and integrity. (Depends on T014a)
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

- [X] T019 [US2] Implement `src/retrieval/query.py` (FR-002) to generate query vectors using `all-MiniLM-L6-v2`. **Include** logic to measure and log wall-clock latency for text embedding generation to satisfy SC-003. (Depends on T014b)
- [X] T022a [US2] Implement synthesis logic in `src/retrieval/strategies.py` (FR-003) for: (1) Single Nearest Neighbor, (2) Unweighted Arithmetic Mean (k-top), (3) Cosine-Weighted Averaging. **Include** logic to handle edge cases: (a) out-of-distribution queries (raise `ValueError`), (b) identical similarity scores (random tie-breaking or weighted average). **Include** logic to measure and log wall-clock latency for retrieval/interpolation to satisfy SC-003. (Depends on T014b, T019)
- [X] T022b [US2] Implement serialization logic in `src/retrieval/strategies.py` to save synthesized A/B matrices to `artifacts/synthesized_adapters/` based on query results. **Output**: Verify file structure (correct dimensions, non-NaN). Explicitly **DO NOT** apply the adapter to a model or run inference in this task (application logic is deferred to T026/US3). (Depends on T022a)
- [ ] T022d [P] [US2] Implement `src/validation/reconstruction_error.py` to calculate the cosine distance (reconstruction error) between the synthesized LoRA weights (from T022b serialization) and the true weights of a known composite task (from T022c). **Output** the **mean** error value across the held-out set to `data/results/reconstruction_error.json`. **Include** logic to flag if the **mean** error exceeds 0.05 (SC-005) and record this flag. (Depends on T022b serialization, T022c)
- [ ] T023 [US2] Add logging for retrieval latency (SC-003) and similarity scores in `src/retrieval/query.py`

### Data Generation for Linearity Check (Prerequisite for US2/US3 Validation)
- [ ] T022c [US2] Implement `src/validation/generate_ground_truth.py` to load **REAL** base LoRA adapters from `data/raw/` (from T012) and generate **SYNTHETIC COMPOSITE ADAPTERS** by linearly interpolating two base adapters (e.g., `task_a` and `task_b`). **Fallback**: If real adapters are missing (T012 failed), generate deterministic mock adapters with `np.random.seed(42)` and dimensions `4096x1024`. **Output**: Save to `data/processed/composite_ground_truth.npz` AND generate `data/processed/pairs.yaml` with schema: `[{task_a_id, task_b_id, composite_task_id, expected_correlation}]`. **Validate**: Ensure interpolated weights are non-NaN and non-zero. **FAIL LOUDLY** if real base adapters are not found AND not in 'staged' mode. (Depends on T012)
- [ ] T022e [US2] Implement `src/validation/generate_eval_tasks.py` to generate `data/processed/eval_tasks.yaml` containing the **held-out set of task IDs** required for the sensitivity analysis (SC-004). This file should be populated with the actual held-out set of tasks (e.g., from the dataset or a defined list). **Fallback**: If the LatentSkill repo does not provide a specific held-out set, generate a deterministic list of task IDs (seed=42) from the available base adapters. **Output**: Save to `data/processed/eval_tasks.yaml`. (Depends on T012)
- [ ] T030 [US2] Implement `src/validation/linearity_check.py` ([FR-007]) to calculate Pearson correlation between text-space and weight-space distances for the held-out set of known task pairs stored in `data/processed/pairs.yaml` (generated by T022c). **Output** the **exact correlation value** (as `correlation_value`) and a `validity_flag` (True if >= 0.6, False otherwise) to `data/results/linearity_check.json`. **DO NOT** raise an error if the threshold is not met; the experiment must proceed to measure the impact of non-linearity. Ensure downstream tasks consume this flag. (Depends on T014b, T019, T022c, T022e)

**Checkpoint**: Retrieval and interpolation mechanisms produce valid synthesized adapters; linearity assumption validated (or measured).

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for `src/retrieval/strategies.py` verifying unweighted and weighted averaging math in `tests/unit/test_strategies.py`
- [X] T018 [P] [US2] Contract test for `src/retrieval/query.py` output format in `tests/contract/test_schemas.py`

---

## Phase 5: User Story 3 - Validating Performance via Environment Logic (Priority: P3)

**Goal**: Evaluate synthesized adapters on composite tasks using environment logic, run multiple trials (N≥5), and perform statistical testing with BH correction.

**Independent Test**: System runs evaluation, outputs success/failure logs, and generates a statistical report with p-values and BH correction.

### Implementation for User Story 3

- [X] T026a [P] [US3] Download and convert the base LLM to GGUF format. **Action**: Use `llama.cpp` to download `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (exact repo URL). **Command**: `python convert-hf-to-gguf.py --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 --outfile model.gguf --outtype f16` followed by `./quantize model.gguf data/models/tinyllama-1.1b-q4_0.gguf q4_0`. **Constraint**: Ensure file size fits within 7GB RAM limit during inference. **Validate**: Check file size and fail loudly if > 6.5 GB. **Fallback**: If download fails, **FAIL LOUDLY** with a specific error message directing to the verified source. **Memory Management**: Explicitly mandate 'load adapter -> run -> unload adapter' cycle to prevent memory accumulation. Log memory usage during the first run and fail loudly if it exceeds **6.5 GB**. (Depends on T004)
- [ ] T026a-1 [US3] Implement `src/evaluation/download_baseline.py` to download the 'standard fine-tuned baseline' adapters from the LatentSkill repo's 'baseline' directory. **Fallback**: If missing, generate them by fine-tuning a small subset (with a 'STAGED' flag) or **FAIL LOUDLY** with a specific error message. If the repo structure differs (e.g., no 'baseline' directory), generate deterministic mock baseline adapters with `np.random.seed(42)` and dimensions `4096x1024`. Log the fallback action. (Depends on T006)
- [ ] T026 [US3] Implement `src/evaluation/runner.py` (FR-004) to apply adapters (from T022b) to a frozen base LLM (via `llama-cpp-python` GGUF, model path: `data/models/tinyllama-1.1b-q4_0.gguf`, quantization: q4_0) and execute environment logic (ALFWorld/Search-QA). (Depends on T022b, T026a, T026a-1)
- [ ] T026b [US3] Implement memory validation and streaming/chunking logic in `src/evaluation/runner.py` to ensure the base LLM inference fits within 7GB RAM. **Explicitly mandate**: 'load adapter -> run -> unload adapter' cycle to prevent memory accumulation. Log memory usage during the first run and fail loudly if it exceeds **6.5 GB**. (Depends on T026)
- [ ] T027 [US3] Implement `src/evaluation/runner.py` loop to execute **N >= 5** independent runs per task (FR-008) and record binary outcomes, calculating the **mean of these binary outcomes** to establish a stable success probability. (Depends on T026b)
- [ ] T031 [US3] Implement sensitivity analysis logic (SC-004) for **k in {1, 3, 5, 10}** in `src/retrieval/strategies.py` and `src/evaluation/runner.py`. **Input**: Load the held-out set of task IDs from `data/processed/eval_tasks.yaml` (generated by T022e). **Output** results to `data/results/stats_report.json` under the key `sensitivity_analysis`. **Mandate**: Report specific performance degradation thresholds (calculated as `baseline_success_rate - strategy_success_rate`) to make the analysis measurable. **Include** the **baseline** performance (k=0 or standard fine-tuned) alongside the sensitivity results. (Depends on T022a, T026a, T022e)
- [ ] T028 [US3] Implement `src/evaluation/stats.py` (FR-005) to perform paired t-test or Wilcoxon signed-rank test on success rates between strategies and baseline. (Depends on T027)
- [ ] T029 [US3] Implement `src/evaluation/stats.py` (FR-006) to apply Benjamini-Hochberg correction for multiple comparisons across all primary strategies and **sensitivity sweeps** (results from T031). **Output**: Append corrected q-values to `data/results/stats_report.json`. (Depends on T028, T031)
- [ ] T032 [US3] Generate final report in `data/results/stats_report.json` including p-values, BH-adjusted q-values, reconstruction errors (SC-005, from T022d), and linearity correlation (from T030). (Depends on T031, T029, T022d, T030)

### Tests for User Story 3

- [ ] T024 [P] [US3] Contract test for `src/evaluation/stats.py` output schema in `tests/contract/test_schemas.py`
- [ ] T025 [P] [US3] Integration test for full evaluation loop in `tests/integration/test_pipeline.py`

**Checkpoint**: Evaluation complete with statistical validation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T033a Update `README.md` with sections: 'Installation', 'Usage', 'Data Sources', and 'Results' containing the specific content defined in the plan.
- [X] T033b Create `docs/api.md` with function signatures and module descriptions
- [X] T034 Code cleanup and refactoring of `src/retrieval/strategies.py`
- [ ] T036 [P] Additional unit tests for edge cases in `tests/unit/`
- [X] T037 Run `src/validate/citation_check.py` to verify all dataset sources
- [ ] T038 [P] Run `docs/quickstart.md` validation: Execute the pipeline script referenced in `docs/quickstart.md` and save the output log to `data/results/quickstart_validation.log`. (Depends on T033a)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T014b (Index generation)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T022b (Synthesis) and T026a (Base Model)

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
- **Data**: No fabrication. All datasets must be fetched from real sources (specifically the LatentSkill repository for weights). If real weights are unavailable, **FAIL LOUDLY** in PROD mode. A 'STAGED' fallback is allowed in DEV mode for development.
- **Critical Data Hygiene**: `src/ingestion/download_weights.py` (T012) MUST raise an exception if the real fetch fails in PROD mode.
- **Memory Management**: T012 and T013 must stream or chunk the LoRA weight loading to ensure the 7GB RAM limit is not exceeded during ingestion of large adapters. T026b must explicitly validate memory during inference with a 6.5 GB threshold and mandate adapter unloading between runs.
- **Statistical Rigor**: T030 must output the correlation value and validity flag to the report, not halt execution.
- **Sensitivity Analysis**: T031 must use k in {1, 3, 5, 10} per SC-004 and report performance degradation thresholds (baseline - strategy).
- **Latency Reporting**: Latency logging is integrated into T019 and T020 to satisfy SC-003.
- **Ground Truth Generation**: T022c must generate **SYNTHETIC COMPOSITE ADAPTERS** via interpolation of real base adapters (or mock if staged) to serve as ground truth for T022d and T030.
- **Base Model Provisioning**: T026a must download and quantize the base model (TinyLlama-1.1B) AND the baseline adapters before T026 executes.