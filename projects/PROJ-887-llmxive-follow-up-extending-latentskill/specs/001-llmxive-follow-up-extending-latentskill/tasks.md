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

- [X] T001b [P] Create all `__init__.py` files for the following exact paths: `src/ingestion/__init__.py`, `src/retrieval/__init__.py`, `src/evaluation/__init__.py`, `src/validation/__init__.py`, `src/utils/__init__.py`, `src/validate/__init__.py`. (Empty or minimal docstring). **Note**: Ensures both `src/validate` (for citation_check) and `src/validation` (for linearity) directories are initialized as per plan.md structure.
- [X] T002a Create `requirements.txt` with pinned versions for: `torch`, `numpy`, `scikit-learn`, `sentence-transformers`, `transformers`, `pandas`, `scipy`, `llama-cpp-python`, `pytest`. **REMOVE** `faiss-cpu` as it is not in the plan's approved dependencies.
- [X] T002b Run `pip install -r requirements.txt` to verify dependency resolution
- [X] T003a [P] Create `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections (line-length=88, target-version=py311)
- [X] T003b [P] Create `.ruff.toml` with `line-length = 88` and `ignore = ["E501", "W293"]`
- [X] T001c [P] Ensure `data/`, `artifacts/`, and `data/raw/`, `data/processed/`, `data/results/`, `data/logs/` directories exist in the repo. **Note**: These directories should be added to `.gitignore` to prevent tracking of generated data. Do NOT create `.gitkeep` files here.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `src/utils/config.py` for seed pinning, path resolution, and environment variable loading
- [X] T005 [P] Implement `src/utils/versioning.py` to compute SHA256 hashes for artifacts and update `state/projects/...yaml`
- [X] T006a [P] Create `data_sources.yaml` defining the canonical URLs/IDs for NAB, UCI, HuggingFace, and LatentSkill repo datasets to serve as the source of truth for validation.
- [X] T006 [P] Create `src/validate/citation_check.py` to verify dataset URLs listed in `data_sources.yaml`. **Implementation**: Create the script to perform HTTP 200 checks AND validate the specific existence of weight files within the dataset (not just URL reachability). **Handle Fallback**: If the primary HF dataset is missing, the script must validate the existence of the arXiv source and prepare for fallback. (Depends on T006a, T004)
- [ ] T012 [US1] Implement `src/ingestion/download_weights.py` to fetch real LoRA weights from the **HuggingFace dataset 'latent-skills/alfworld-weights'** (path: `weights/alfworld/*.npz`) and **'latent-skills/searchqa-weights'** (path: `weights/searchqa/*.npz`) for ALFWorld and Search-QA benchmarks. **Execute** citation check (T006) **first** to verify the source. **Pre-flight Check**: Verify existence of dataset paths. **Fallback**: If real weights are unavailable, **FAIL LOUDLY** for production runs. **DO NOT** generate proxy data in production. **ArXiv Fallback**: If HF is down, attempt to fetch from arXiv source as per T006. **Expected Dimensions**: If real data is found, verify shapes match `in_features=4096, out_features=1024` (or log mismatch). **Output**: Save real weights to `data/raw/alfworld_weights.npz` and `data/raw/searchqa_weights.npz`. Log the exact resolved URL/ID used. (Depends on T006, T004)
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

- [X] T013 [US1] Implement `src/ingestion/flatten_lora.py` (FR-001) to load A/B matrices from `data/raw/`, flatten to 1D, and apply L2 normalization. **Input**: Real weights from T012. (Depends on T012)
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

- [X] T019 [US2] Implement `src/retrieval/query.py` (FR-002) to generate query vectors using `sentence-transformers/all-MiniLM-L6-v2`. **Include** logic to measure and log wall-clock latency for text embedding generation to `data/logs/latency.log` to satisfy SC-003. (Depends on T014b)
- [X] T022a [US2] Implement synthesis logic in `src/retrieval/strategies.py` (FR-003) for: (1) Single Nearest Neighbor, (2) Unweighted Arithmetic Mean (k-top), (3) Cosine-Weighted Averaging. **Include** logic to handle edge cases: (a) out-of-distribution queries (raise `ValueError`), (b) identical similarity scores (random tie-breaking or weighted average). **Include** logic to measure and log wall-clock latency for retrieval/interpolation to `data/logs/latency.log` to satisfy SC-003. (Depends on T014b, T019)
- [X] T022b [US2] Implement serialization logic in `src/retrieval/strategies.py` to save synthesized A/B matrices to `artifacts/synthesized_adapters/` based on query results. **Output**: Verify file structure (correct dimensions, non-NaN). Explicitly **DO NOT** apply the adapter to a model or run inference in this task (application logic is deferred to T026/US3). (Depends on T022a)
- [ ] T022c-gen [US2] Implement `src/validation/fetch_ground_truth.py` to fetch **REAL** known composite task weights from the LatentSkill repository (or a verified HuggingFace mirror) to serve as ground truth for FR-007 and SC-005. **Selection Rule**: Select pairs based on **semantic similarity (cosine distance < 0.3)** using task descriptions from the real dataset. **Use seed=43** for reproducibility. **Fallback**: If real composite tasks are unavailable, **FAIL LOUDLY** with a specific error message. **DO NOT** generate synthetic mock weights. **Output**: Save to `data/processed/composite_ground_truth.npz` AND generate `data/processed/pairs.yaml` with schema: `[{task_a_id, task_b_id, composite_task_id, task_a_desc, task_b_desc, composite_task_desc, expected_correlation}]`. **Note**: The `task_*_desc` and `composite_task_desc` fields are REQUIRED for FR-007 correlation checks (T030). **Validate**: Ensure fetched weights are non-NaN and non-zero. **FAIL LOUDLY** if real base adapters are not found. (Depends on T006, T012 - **Note**: Strict dependency on T012 success).
- [ ] T022c-verify [US2] Execute `src/validation/fetch_ground_truth.py` to select and validate the held-out pairs for linearity check. **Output**: Generate `data/processed/linearity_pairs.yaml` containing the specific subset of pairs used for FR-007 validation. **Distinctness**: Ensure this set is distinct from the sensitivity analysis set (T022e). **Strict Rule**: If real data is missing, **FAIL LOUDLY**. (Depends on T022c-gen)
- [ ] T022d [US2] Implement `src/validation/reconstruction_error.py` to calculate the cosine distance (reconstruction error) between the synthesized LoRA weights (from T022b serialization) and the true weights of a known composite task (from T022c-gen). **Output** the **mean** error value AND the **maximum** error value across the held-out set to `data/results/reconstruction_error.json`. **Include** logic to flag if the **mean** error exceeds 0.05 (SC-005) and record this flag. **Strict Rule**: If **mean** error > 0.05, the `validity_flag` must be set to False. **Outlier Handling**: Flag individual outliers > 0.05 but do not fail the entire set unless the mean threshold is breached. (Depends on T022b serialization, T022c-gen)
- [ ] T022e [US2] Implement `src/validation/generate_eval_tasks.py` to generate `data/processed/eval_tasks.yaml` containing the **held-out set of task IDs** required for the sensitivity analysis (SC-004). **Selection Rule**: If a real held-out set is available, perform a **stratified split (seed=42, held-out)**. **Fallback**: If the LatentSkill repo does not provide a specific held-out set, **FAIL LOUDLY** (do not generate synthetic tasks). **Output**: Save to `data/processed/eval_tasks.yaml`. **Strict Rule**: If real data is missing, the task must fail. (Depends on T006, T012 - **Note**: Strict dependency on T012 success).
- [ ] T030 [US2] Implement `src/validation/linearity_check.py` ([FR-007]) to calculate Pearson correlation between text-space and weight-space distances for the held-out set of known task pairs stored in `data/processed/linearity_pairs.yaml` (generated by T022c-verify). **Output** the **exact correlation value** (as `correlation_value`) and a `validity_flag` (True if >= 0.6, False otherwise) to `data/results/linearity_check.json`. **Strict Rule**: If `linearity_pairs.yaml` is missing or contains mock data, **FAIL LOUDLY**. Ensure downstream tasks consume this flag. (Depends on T014b, T019, T022c-verify, T022e)
- [ ] T030-exec [US2] Execute `src/validation/linearity_check.py` to generate the final `data/results/linearity_check.json`. **Precondition**: Ensure T022c-verify has run (with real data only). **Strict Rule**: If `linearity_pairs.yaml` is missing or mock, **FAIL LOUDLY**. (Depends on T030, T022c-verify)

**Checkpoint**: Retrieval and interpolation mechanisms produce valid synthesized adapters; linearity assumption validated (or measured).

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for `src/retrieval/strategies.py` verifying unweighted and weighted averaging math in `tests/unit/test_strategies.py`
- [X] T018 [P] [US2] Contract test for `src/retrieval/query.py` output format in `tests/contract/test_schemas.py`

---

## Phase 5: User Story 3 - Validating Performance via Environment Logic (Priority: P3)

**Goal**: Evaluate synthesized adapters on composite tasks using environment logic, run multiple trials (N≥5), and perform statistical testing with BH correction.

**Independent Test**: System runs evaluation, outputs success/failure logs, and generates a statistical report with p-values and BH correction.

### Implementation for User Story 3

- [X] T026a [P] [US3] Download and convert the base LLM to GGUF format. **Action**: Use `llama.cpp` to download `TinyLlama/TinyLlamaB-Chat-v` (exact repo URL). **Command**: `python convert-hf-to-gguf.py --model TinyLlama/TinyLlama-Chat-v1.0 --outfile model.gguf --outtype f16` followed by `./quantize model.gguf data/models/tinyllama-1.1b-q4_0.gguf q4_0`. **Constraint**: Ensure file size fits within GB RAM limit during inference. **Validate**: Check file size and fail loudly if > 6.5 GB. **Fallback**: If download fails, **FAIL LOUDLY** with a specific error message directing to the verified source. **Memory Management**: Explicitly mandate 'load adapter -> run -> unload adapter' cycle to prevent memory accumulation. Log memory usage during the first run and fail loudly if it exceeds a predefined threshold. (Depends on T004)
- [ ] T026a-1 [US3] Implement `src/evaluation/download_baseline.py` to download the 'standard fine-tuned baseline' adapters from the LatentSkill repo's 'baseline' directory. **Constraint**: If the specific 'baseline' directory is missing, **fetch a proxy baseline** from HuggingFace repo 'llmXive/baselines' (artifact: 'TinyLlama-1.1B-finetuned-v1'). **Log**: If proxy is used, mark report as "proxy_baseline". **DO NOT** generate mock baseline. (Depends on T006)
- [ ] T026 [US3] Implement `src/evaluation/runner.py` (FR-004) to apply adapters (from T022b) to a frozen base LLM (via `llama-cpp-python` GGUF, model path: `data/models/tinyllama-1.1b-q4_0.gguf`, quantization: q_) and execute environment logic (ALFWorld/Search-QA). (Depends on T022b, T026a, T026a-1)
- [ ] T026b [US3] Implement memory validation and streaming/chunking logic in `src/evaluation/runner.py` to ensure the base LLM inference fits within 7GB RAM. **Explicitly mandate**: 'load adapter -> run -> unload adapter' cycle to prevent memory accumulation. Log memory usage during the first run and fail loudly if it exceeds **6.5 GB**. (Depends on T026)
- [ ] T027 [US3] Implement `src/evaluation/runner.py` loop to execute **N >= 5** independent runs per task (FR-008) and record binary outcomes, calculating the **mean of these binary outcomes** to establish a stable success probability. (Depends on T026b)
- [ ] T031 [US3] Implement sensitivity analysis logic (SC-004) for **k in {1, 3, 5, 10}** in `src/retrieval/strategies.py` and `src/evaluation/runner.py`. **Input**: Load the held-out set of task IDs from `data/processed/eval_tasks.yaml` (generated by T022e). **Output** results to `data/results/stats_report.json` under the key `sensitivity_analysis`. **Mandate**: Report specific performance degradation thresholds (calculated as `baseline_success_rate - strategy_success_rate`) to make the analysis measurable. **Include** the **baseline** performance (k=0 or standard fine-tuned) alongside the sensitivity results. (Depends on T022a, T026a, T022e)
- [ ] T028 [US3] Implement `src/evaluation/stats.py` (FR-005) to perform paired t-test or Wilcoxon signed-rank test on success rates between strategies and baseline. **Output**: Store raw p-values in `data/results/raw_pvalues.json` for consumption by T029-bh. (Depends on T027)
- [ ] T029-bh [US3] Implement `src/evaluation/stats.py` (FR-006) to apply Benjamini-Hochberg correction for multiple comparisons across **BOTH** the primary strategy-vs-baseline comparisons (raw p-values from T028) **AND** the sensitivity sweeps (results from T031). **Input**: Collect raw p-values from T028 and T031. **Output**: Prepare corrected q-values for T029-bh-exec. **Unified Step**: Ensure single-pass FDR control over all hypotheses. (Depends on T028, T031)
- [ ] T029-bh-exec [US3] Execute `src/evaluation/stats.py` to run the unified Benjamini-Hochberg correction and write the final `data/results/stats_report.json` including `combined_bh_correction`. **Precondition**: Ensure T031 and T028 have completed. **Fallback**: If T031 fails, run BH on T028 data alone and flag report as "partial_sensitivity". (Depends on T029-bh, T031, T028)
- [ ] T032 [US3] Generate final report in `data/results/stats_report.json` including p-values, BH-adjusted q-values, reconstruction errors (SC-005, from T022d), and linearity correlation (from T030-exec). (Depends on T031, T029-bh-exec, T022d, T030-exec)
- [ ] T033-latency-exec [US2/US3] Execute a dedicated benchmarking script on the **standard multi-core CPU runner** (GitHub Actions free-tier) to aggregate latency logs from `data/logs/latency.log` (generated by T019 and T022a) into `data/results/latency_report.json`. **Input**: Read `data/logs/latency.log`. **Output**: Aggregate mean, median, and max latency for each stage. **Constraint**: Must run on the **standard 2-core CPU runner** environment to satisfy SC-003 and Constitution Principle VII. (Depends on T019, T022a, T026)

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
- Models/Scripts before implementation
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
- **Data**: No fabrication. All datasets must be fetched from real sources (specifically the LatentSkill repository for weights). If real weights are missing, **FAIL LOUDLY** in production. **DO NOT** use `--mock` flags for ground truth or sensitivity analysis tasks.
- **Critical Data Hygiene**: `src/ingestion/download_weights.py` (T012) MUST raise an exception if the real fetch fails.
- **Memory Management**: T012 and T013 must stream or chunk the LoRA weight loading to ensure the 7GB RAM limit is not exceeded during ingestion of large adapters. T026b must explicitly validate memory during inference with a 6.5 GB threshold and mandate adapter unloading between runs.
- **Statistical Rigor**: T030-exec must output the correlation value and validity flag to the report, not halt execution.
- **Sensitivity Analysis**: T031 must use k in {1, 3, 5, 10} per SC-004 and report performance degradation thresholds (baseline - strategy).
- **Latency Reporting**: Latency logging is integrated into T019 and T022a to satisfy SC-003. T033-latency-exec explicitly executes the benchmarking script on the **standard 2-core CPU runner** to generate the formal report.
- **Ground Truth Generation**: T022c-gen must fetch **REAL** known composite task weights from the LatentSkill repository. **DO NOT** generate synthetic adapters. **Must include textual descriptions** in `pairs.yaml`. **Use seed=43** for distinctness from T022e. **Strict Rule**: If real data is missing, **FAIL LOUDLY**.
- **Base Model Provisioning**: T026a must download and quantize the base model (TinyLlama-1.1B) AND the baseline adapters before T026 executes. **Baseline adapters must be real or a verified proxy** in production; `--mock` is not allowed.
- **Dependency Relaxation**: T022c-gen, T022e, T026a-1 now depend on T006 (citation check) and **strictly require** T012 (real data) for ground truth and sensitivity analysis.
- **Unified BH Correction**: T029-bh and T029-bh-exec perform a single-pass FDR control over all hypotheses (primary + sensitivity) to avoid compounding errors.
- **Distinct Validation Sets**: T022c-verify generates `linearity_pairs.yaml` for FR-007, distinct from `eval_tasks.yaml` (T022e) used for sensitivity analysis.