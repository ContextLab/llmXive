# Tasks: llmXive follow-up: extending "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills"

**Input**: Design documents from `/specs/001-lattentskill-retrieval-geometry/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001b [P] Create all `__init__.py` files for the following exact paths: `src/ingestion/__init__.py`, `src/retrieval/__init__.py`, `src/evaluation/__init__.py`, `src/validation/__init__.py`, `src/validate/__init__.py`, `src/utils/__init__.py`. (Empty or minimal docstring)
- [X] T002a Create `requirements.txt` with pinned versions for: `torch`, `numpy`, `scikit-learn`, `sentence-transformers`, `transformers`, `pandas`, `scipy`, `llama-cpp-python`. **REMOVE** `faiss-cpu` as it is not in the plan's approved dependencies.
- [X] T002b Run `pip install -r requirements.txt` to verify dependency resolution
- [X] T003a [P] Create `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections (line-length=88, target-version=py311)
- [X] T003b [P] Create `.ruff.toml` with `line-length = 88` and `ignore = ["E***", "W***"]`
- [X] T001c [P] Ensure `data/`, `artifacts/`, and `data/raw/`, `data/processed/`, `data/results/` directories exist in the repo. **Note**: These directories should be added to `.gitignore` to prevent tracking of generated data. Do NOT create `.gitkeep` files here.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `src/utils/config.py` for seed pinning, path resolution, and environment variable loading
- [X] T005 [P] Implement `src/utils/versioning.py` to compute SHA256 hashes for artifacts and update `state/projects/...yaml`
- [X] T006a [P] Create `data_sources.yaml` defining the canonical URLs/IDs for NAB, UCI, HuggingFace, and LatentSkill repo datasets to serve as the source of truth for validation.
- [X] T006 [P] Create `src/validate/citation_check.py` to verify dataset URLs listed in `data_sources.yaml`. **Implementation**: Create the script to perform HTTP 200 checks AND validate the specific existence of weight files within the dataset (not just URL reachability). **Handle Fallback**: If the primary HF dataset is missing, the script must validate the existence of the arXiv source and prepare for fallback. (Depends on T006a, T004)
- [X] T006b [P] **Execute** `src/validate/citation_check.py` to verify all dataset sources before proceeding. **Output**: Save verification results to `data/processed/citation_verification.json`. If any critical source fails, log an error and halt. (Depends on T006, T004)
- [X] T012 [US1] Implement `src/ingestion/download_weights.py` to fetch real LoRA weights from the **HuggingFace dataset 'latent-skills/alfworld-weights'** (path: `weights/alfworld/*.npz`) and **'latent-skills/searchqa-weights'** (path: `weights/searchqa/*.npz`) for ALFWorld and Search-QA benchmarks. **Execute** citation check (T006b) **first** to verify the source. **If real weights are unavailable, the task MUST generate synthetic proxy weights via T022f logic to allow the project to proceed, logging a WARNING and saving them to `data/raw/`. DO NOT fail the entire project if real weights are missing; instead, use the synthetic fallback for validation tasks.** **Expected Dimensions**: If real data is found, verify shapes match `in_features=4096, out_features=1024` (or log mismatch). **Output**: Save real weights to `data/raw/alfworld_weights.npz` and `data/raw/searchqa_weights.npz`. Log the exact resolved URL/ID used. (Depends on T006b, T004)
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

- [X] T013 [US1] Implement `src/ingestion/flatten_lora.py` (FR-001) to load A/B matrices from `data/raw/`, flatten to 1D, and apply L2 normalization. **Input**: Real weights from T012 (or synthetic fallback if T012 used fallback). (Depends on T012)
- [X] T014c [US1] Implement logic in `src/retrieval/vector_db.py` (FR-001) to load flattened vectors and prepare data for serialization. (Depends on T013)
- [X] T014d [US1] **Execute** `python src/retrieval/vector_db.py` **to construct and save the static index to `data/processed/skill_index.npz`. Verify file existence, checksum, and data type compatibility.** (Depends on T014c)
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

- [X] T019 [US2] Implement `src/retrieval/query.py` (FR-002) to generate query vectors using a lightweight sentence-transformer model. **Include** logic to measure and log wall-clock latency for text embedding generation. (Depends on T014c)
- [X] T022a [US2] Implement synthesis logic in `src/retrieval/strategies.py` (FR-003) for: (1) Single Nearest Neighbor, (2) Unweighted Arithmetic Mean of top-$k$ vectors, and (3) Cosine-Weighted Averaging. **Include** logic to handle edge cases: (a) out-of-distribution queries (raise `ValueError`), (b) identical similarity scores (random tie-breaking or weighted average). **Include** logic to measure and log wall-clock latency for retrieval/interpolation. (Depends on T014c, T019)
- [X] T022b [US2] Implement serialization logic in `src/retrieval/strategies.py` to save synthesized A/B matrices to `artifacts/synthesized_adapters/` based on query results. **Output**: Verify file structure (correct dimensions, non-NaN). Explicitly **DO NOT** apply the adapter to a model or run inference in this task (application logic is deferred to T026/US3). (Depends on T022a)
- [X] T022f [US2] **NEW**: Implement `src/validation/generate_known_composites.py` to generate a **held-out set of known composite tasks** by linearly interpolating existing skill vectors (creating synthetic 'true weights'). **Selection Rule**: Select a representative subset of all possible pairs of existing skills, interpolate them, and save as `data/processed/known_composites_pairs.yaml`. **Explicitly define**: These synthetic weights are the 'true weights' for SC-005 and FR-007 validation. (Depends on T014d)
- [X] T022c [US2] Implement `src/validation/generate_ground_truth.py` to generate **synthetic** composite adapters by linearly interpolating two base adapters. **Selection Rule**: Pair the first two adapters alphabetically by task ID to ensure determinism. **Output**: Save to `data/processed/composite_ground_truth.npz` AND generate `data/processed/pairs.yaml`. Synthetic composite adapters serve as ground truth *because* true weights for novel compositions are not available, and SC-005's linearity validation is defined against this synthesized data. (Depends on T014d)
- [X] T022d [US2] Implement `src/validation/reconstruction_error.py` to calculate the cosine distance (reconstruction error) between the synthesized LoRA weights (from T022b) and the synthetic ground truth (from T022f). **Explicitly state**: Use the synthetic weights from T022f as the ground truth for SC-005. **Output** the **mean** AND **maximum** error values to `data/results/reconstruction_error.json`. Flag if maximum deviation exceeds a pre-defined threshold, indicating potential non-linearity. (Depends on T022b, T022f)
- [X] T022e [US2] Implement `src/validation/generate_eval_tasks.py` to generate `data/processed/eval_tasks.yaml` containing the held-out set of task IDs for sensitivity analysis. (Depends on T014d)
- [X] T030 [US2] Implement `src/validation/linearity_check.py` to calculate Pearson correlation between text-space and weight-space distances. **Input**: Use the held-out set of known task pairs generated in T022f, specifically reading from `data/processed/known_composites_pairs.yaml`. (Depends on T022f, T019)

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for `src/retrieval/strategies.py` verifying unweighted and weighted averaging math in `tests/unit/test_strategies.py`
- [X] T018 [P] [US2] Contract test for `src/retrieval/query.py` output format in `tests/contract/test_schemas.py`

**Checkpoint**: Retrieval and interpolation mechanisms produce valid synthesized adapters; linearity assumption validated (or measured).

---

## Phase 5: User Story 3 - Validating Performance via Environment Logic (Priority: P3)

**Goal**: Evaluate synthesized adapters on composite tasks using environment logic, run multiple trials (N≥5), and perform statistical testing with BH correction.

**Independent Test**: System runs evaluation, outputs success/failure logs, and generates a statistical report with p-values and BH correction.

### Implementation for User Story 3

- [X] T026a [US3] Download and convert the base LLM to GGUF format. **Action**: Use `llama.cpp` to download `TinyLlama/TinyLlama-Chat-v1.0`.
- [X] T026c [US3] **NEW**: Implement `src/evaluation/train_proxy_baseline.py` to train a small MLP (hypernetwork proxy) on the skill vectors (from T014d) to serve as the "standard fine-tuned baseline" proxy. **Action**: Train on a majority of skill vectors, validate on the remainder. Save model weights to `artifacts/baseline_mlp.pt`. **Measure** and log wall-clock latency for this baseline inference. **Explicitly state**: This MLP latency serves as the 'hypernetwork baseline' latency metric required by SC-003, as the original hypernetwork weights are unavailable. (Depends on T014d)
- [X] T026d [US3] **NEW**: Implement `src/evaluation/generate_finetuned_baseline.py` to train a **standard fine-tuned LoRA adapter** on a held-out composite task (from T022f) to serve as the actual control group for SC-001. **Action**: Fine-tune the base model on the synthetic composite task (from T022f) for a fixed number of steps. Save the resulting LoRA adapter to `artifacts/baseline_adapter.pt`. (Depends on T022f, T026a)
- [ ] T026 [US3] Implement `src/evaluation/runner.py` (FR-004) to apply adapters (from T022b) to a frozen base LLM and execute environment logic. **Input**: Use baseline from T026d (LoRA adapter) for comparison. **Explicitly specify**: Use ALFWorld environment logic for primary evaluation; fallback to Search-QA if ALFWorld is unavailable. (Depends on T026a, T026d, T022b)
- [ ] T026b [US3] Implement memory validation and streaming/chunking logic in `src/evaluation/runner.py` to ensure the base LLM inference fits within 7GB RAM. Explicitly mandate 'load adapter -> run -> unload adapter' cycle. Log memory usage during first run. (Depends on T026)
- [ ] T027 [US3] Implement `src/evaluation/runner.py` loop to execute N >= 5 independent runs per task (FR-008) and record binary outcomes, calculating the mean of these outcomes. (Depends on T026)
- [X] T025a [US3] **NEW**: Implement `src/evaluation/init_env_logic.py` to initialize and verify the **ALFWorld** environment logic before evaluation. **Action**: Run a dry-run task to ensure the environment returns a success/failure flag. (Depends on T026a)
- [ ] T031a [US3] Implement sensitivity analysis logic (SC-004) for k in {, 3, 5, 10} in `src/evaluation/run_sensitivity_sweep.py`. (Depends on T022a)
- [ ] T031b [US3] **NEW**: **Execute** the sensitivity analysis sweeps for k in {1, 3, 5, 10} using the logic from T031a and the script `src/evaluation/run_sensitivity_sweep.py`. **Output**: Save comparative results to `data/results/sensitivity.yaml`. (Depends on T031a, T022a)
- [ ] T028 [US3] Implement `src/evaluation/stats.py` (FR-005) to perform paired t-test or Wilcoxon signed-rank test on success rates between strategies and baseline. (Depends on T027)
- [ ] T029a [US3] Implement `src/evaluation/stats.py` (FR-006) to apply Benjamini-Hochberg correction for primary strategy comparisons. (Depends on T028)
- [ ] T029b [US3] Implement `src/evaluation/stats.py` (FR-006) to apply Benjamini-Hochberg correction for sensitivity sweeps. (Depends on T031b)
- [ ] T032 [US3] Generate final report in `data/results/stats_report.json`. (Depends on T029a, T029b)

### Tests for User Story 3

- [ ] T024 [P] [US3] Contract test for `src/evaluation/stats.py` output schema in `tests/contract/test_schemas.py`
- [ ] T025 [P] [US3] Integration test for full evaluation loop in `tests/integration/test_pipeline.py`

**Checkpoint**: Evaluation complete with statistical validation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T033a Update `README.md` with sections: 'Installation', 'Usage', 'Data Sources', and 'Results'
- [X] T033b Create `docs/api.md` with function signatures and module descriptions
- [X] T034 Code cleanup and refactoring of `src/retrieval/strategies.py`
- [ ] T036 [P] Additional unit tests for edge cases in `tests/unit/`
- [X] T037 Run `src/validate/citation_check.py` to verify all dataset sources
- [X] T038 Validate the quickstart path.

---

## Dependencies & Execution Order

(Same content as original plan)

## Notes

(Same content as original plan)