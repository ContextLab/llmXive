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
- [X] T002a Create `requirements.txt` with the following EXACT pinned versions: `torch==2.1.0`, `numpy==1.24.0`, `scikit-learn==1.3.0`, `sentence-transformers==2.2.2`, `transformers==4.35.0`, `pandas==2.1.0`, `scipy==1.11.0`, `llama-cpp-python==0.2.30`, `faiss-cpu==1.7.4`, `pyyaml==6.0.1`, `pytest==7.4.0`, `psutil==5.9.0`, `huggingface-hub==0.19.0`. **Do not rely on external files to verify this list; this task defines the definitive dependency set.**
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
- [X] T006a [P] Create `data_sources.yaml` defining the canonical URLs/IDs for NAB, UCI, HuggingFace, and LatentSkill repo datasets to serve as the source of truth for validation. **Content**: Must include:
 1. `latent-skills/alfworld-weights` (HF Dataset ID: `latent-skills/alfworld-weights`)
 2. `latent-skills/searchqa-weights` (HF Dataset ID: `latent-skills/searchqa-weights`)
 3. `arXiv:2606.06087` (Supplementary URL: `)
 4. `NAB` (URL: `)
 5. `UCI` (URL: `)
- [X] T006 [P] Create `src/validate/citation_check.py` to verify dataset URLs listed in `data_sources.yaml`. **Implementation**: Create the script to perform HTTP 200 checks AND validate the specific existence of weight files within the dataset (not just URL reachability). **Handle Fallback**: If the primary HF dataset is missing, the script must validate the existence of the arXiv source and prepare for fallback. (Depends on T006a, T004)
- [X] T006b [P] **Execute** `src/validate/citation_check.py` to verify all dataset sources before proceeding. **Output**: Save verification results to `data/processed/citation_verification.json`. If any critical source fails, log an error and halt. (Depends on T006, T004)
- [X] T055 [P] **Update Plan**: Edit `specs/001-lattentskill-retrieval-geometry/plan.md` to correct the 'Constitution Check' table. **Action**: Locate the row where Principle VI is defined and change the text from "FR-007 (Spearman correlation)" to "FR-007 (Pearson correlation)" to align with spec.md. (Depends on T004)
- [X] T055c **Execute Plan Update**: Run `python src/validate/update_plan.py --file specs/001-lattentskill-retrieval-geometry/plan.md --find "Spearman correlation" --replace "Pearson correlation" --target "Principle VI"` (or equivalent deterministic edit) to apply the change from T055. **Verification**: Confirm the text "Pearson correlation" now appears in the Constitution Check table for Principle VI. (Depends on T055)
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
- [X] T026e1-restored [P] **Implement** `src/evaluation/synthesize_baseline.py` to create a **Standard Fine-Tuned Baseline**. **Action**: Fine-tune a small proxy model (TinyLlamaB) on a subset of the training data (e.g., a representative sample from the ALFWorld training split) to produce a real, trainable baseline adapter. **Explicitly state**: This is a 'Standard Fine-Tuned Baseline' created to satisfy SC-001 when the original hypernetwork is unavailable. **Output**: Save to `artifacts/baseline_adapter.pt`. **Constraint**: This proxy is ONLY used if the real hypernetwork is missing; the report must explicitly state this limitation. (Depends on T004, T026a1)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Constructing the Skill Vector Database (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-trained LoRA adapters (A and B matrices) from ALFWorld and Search-QA, flatten them into normalized high-dimensional vectors, and generate a static CPU-compatible index.

**Independent Test**: System loads raw LoRA weights, normalizes them, and outputs a `.npy` or `.npz` index file with metadata without requiring GPU.

### Implementation for User Story 1

- [X] T012a [US1] **Attempt** `src/ingestion/download_weights.py` to fetch real LoRA weights. **Primary Source**: HuggingFace dataset 'latent-skills/alfworld-weights' (path: `weights/alfworld/*.npz`) and 'latent-skills/searchqa-weights' (path: `weights/searchqa/*.npz`). **Fallback 1**: If HF fails, attempt to download from arXiv supplementary URL (`). **Fallback 2**: If arXiv fails, attempt to clone the original GitHub repository (`). **Strict Failure**: If ALL sources fail, raise `FileNotFoundError` and **halt** (do not generate synthetic data here). **Output**: Log the exact source used or the specific failure reason. (Depends on T006b, T004)
- [X] T012b [US1] **Execute** `src/ingestion/download_weights.py`. **If it fails (FileNotFoundError), halt the pipeline immediately and trigger T012c.** **Output**: Ensure `data/raw/` contains real weights. (Depends on T012a, T006b)
- [X] T012c [US1] **Generate Verified Synthetic Proxy** (ONLY if T012b fails with FileNotFoundError). **Action**: Generate LoRA-like weight matrices with dimensions matching the expected base model (TinyLlama: hidden_size=2048, rank=16, num_layers=16) using seed=42. **Constraint**: This is a fallback ONLY. Log 'SYNTHETIC DATA USED' and save to `data/raw/synthetic_proxy_weights.npz`. (Depends on T012b failure)
- [X] T013 [US1] Implement `src/ingestion/flatten_lora.py` (FR-001) to load A/B matrices from `data/raw/` (real or synthetic proxy), flatten to 1D, and apply L2 normalization. **Input**: Real weights from T012b OR synthetic from T012c. (Depends on T012b or T012c)
- [X] T014c [US1] Implement logic in `src/retrieval/vector_db.py` (FR-001) to load flattened vectors and prepare data for serialization. **CLI Interface**: Must accept `--input <path>` and `--output <path>` and `--k <int>` arguments. (Depends on T013)
- [X] T014d [US1] **Execute** `python src/retrieval/vector_db.py --input data/raw/weights.npz --output data/processed/skill_index.npz --k 5` **to construct and save the static index.** **Verification**: Verify file existence, checksum, and data type compatibility. (Depends on T014c)
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

- [X] T019 [US2] Implement `src/retrieval/query.py` (FR-002) to generate query vectors using a lightweight sentence-transformer model (`all-MiniLM-L6-v2`). **Mandatory Latency Logging**: Measure and log three distinct metrics to `data/results/latency_metrics.json` to satisfy SC-003: (1) `embedding_latency_ms` (time to generate query vector), (2) `retrieval_latency_ms` (time for vector DB index lookup to find top-k), and (3) `interpolation_latency_ms` (time to compute weighted average of top-k vectors). **Action**: Explicitly wrap the retrieval and interpolation logic blocks with `time.time()` calls. The sum of these three must be recorded as `total_skill_selection_latency_ms`. **Output**: Ensure `data/results/latency_metrics.json` contains all four keys. (Depends on T014c)
- [X] T059 [US2] **Implement** `src/retrieval/query.py` to measure **baseline hypernetwork latency** using a real model. **Action**: If the original LatentSkill hypernetwork weights are available, load and time a single inference. **Constraint**: The comparison MUST be against the real hypernetwork; **DO NOT** use a proxy baseline adapter (TinyLlama) as a substitute. If the real hypernetwork is unavailable, **halt** the pipeline and log `ERROR: Baseline hypernetwork missing; cannot measure computational savings.` **Output**: Append `baseline_latency_ms` to `data/results/latency_metrics.json`. (Depends on T019, T026e1-restored)
- [X] T019c [US2] **Implement** `src/retrieval/query.py` to calculate **computational savings**. **Action**: Calculate `savings_ms = baseline_latency_ms - total_skill_selection_latency_ms`. If `baseline_latency_ms` is NaN (due to missing baseline), set `savings_ms` to NaN. **Output**: Append `computational_savings_ms` to `data/results/latency_metrics.json`. (Depends on T019, T059)
- [X] T022a [US2] Implement `src/retrieval/strategies.py` (FR-003) for: (1) Single Nearest Neighbor selection, (2) Unweighted Arithmetic Mean of top-$k$ vectors, and (3) Cosine-Weighted Averaging. **Algorithm**: Return vector with highest cosine similarity. Average top-k vectors. Weight vectors by cosine similarity, normalize weights, sum. **Include Edge Case Logic**: Raise `ValueError` for OOD queries (similarity < threshold) and handle random tie-breaking for identical similarities within this function. **Consolidation**: This single task replaces T022a1, T022a2, T022a3 to ensure atomic implementation. (Depends on T014c, T019)
- [X] T022e [US2] Implement serialization logic in `src/retrieval/strategies.py` to save synthesized A/B matrices to `artifacts/synthesized_adapters/` based on query results. **Output**: Verify file structure (correct dimensions, non-NaN). Explicitly **DO NOT** apply the adapter to a model or run inference in this task (application logic is deferred to T026/US3). (Depends on T022a)
- [X] T023a [US2] **Implement** `src/validation/generate_known_pairs.py` to generate **held-out set of known task pairs** with **true composite weights**. **Action**: (1) Scan `data/raw/` for existing composite tasks (ground truth). (2) If found, select 20 pairs using `random.sample` with seed=42. (3) If no true composite weights exist in the dataset, **halt** the pipeline and log `ERROR: FR-007 requires true composite weights; dataset does not provide them.` **Output**: Save to `data/processed/known_composites_pairs.yaml` (containing `composite_desc`, `base_skill_ids`, `true_weights_path`). (Depends on T014d)
- [X] T023b [US2] **Generate N/A Artifact** (ONLY if T023a fails to find true weights). **Action**: Create `data/processed/fr007_ground_truth_status.json` with `status: 'untestable'` and `reason: 'True composite weights missing'`. **Output**: This allows the pipeline to continue with a documented missing validation. (Depends on T023a failure)
- [X] T022g1 [US2] **Implement** `src/validation/generate_eval_tasks.py` to generate **held-out composite task descriptions** by: (1) Selecting exactly **20 random pairs** of base skills from the Skill Vector Database (T014d) with seed 42. (2) **Stratification**: If the dataset provides stratified splits (ALFWorld, Search-QA), sample proportionally. If not, use `random.sample` on the union of all tasks until 20 pairs are formed. (3) Combining their task descriptions textually to form composite descriptions. **Output**: Save to `data/processed/known_composites_pairs.yaml` (containing `composite_desc`, `base_skill_ids`). (Depends on T014d)
- [X] T022d [US2] **Implement** `src/validation/reconstruction_error.py` to calculate the cosine distance (reconstruction error) between the synthesized LoRA weights (from T022e) and the **true composite weights** (from T023a). **Logic**: (1) Load true composite weights from `data/processed/known_composites_pairs.yaml`. (2) If true weights are missing, **halt** and log `ERROR: SC-005 requires true composite weights for reconstruction error; cannot use theoretical bounds.` **Output** the **mean** AND **maximum** error values to `data/results/reconstruction_error.json`. Flag if `max_error > 0.05`. (Depends on T022e, T023a)
- [X] T022i [US2] **Implement** `src/validation/generate_eval_tasks.py` to generate `data/processed/eval_tasks.yaml` containing the held-out set of task IDs for sensitivity analysis. (Depends on T022g1)
- [X] T030 [US2] **Implement** `src/validation/linearity_check.py` to calculate **Pearson** correlation between text-space and weight-space distances AND validate SC-005. **Input**: Use the held-out set of pairs from T023a (true weights). **Metric**: Text-space: cosine distance of embeddings from `all-MiniLM-L6-v2` (T019). Weight-space: cosine distance of flattened A/B vectors. **Action**: (1) Calculate Pearson correlation. (2) Read `reconstruction_error.json` from T022d. (3) If `max_error > 0.05`, set `linearity_valid` to `false`. **Output**: Save `correlation_coefficient`, `linearity_valid`, and `reconstruction_error` to a single `data/results/linearity_validation.json`. **Constraint**: The 0.05 threshold is a **hard gate** defined in SC-005. (Depends on T023a, T019, T022d)
- [X] T030b [US2] **Aggregate Linearity Validation**. **Action**: Read `reconstruction_error.json` (T022d) and `linearity_validation.json` (T030). If T023b generated an 'untestable' status, set `linearity_valid: null` and `reason: 'Ground truth weights missing'`. Otherwise, combine results into a single `data/results/linearity_validation.json` with `linearity_valid` boolean and `reconstruction_error` values. (Depends on T023b or T030)

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for `src/retrieval/strategies.py` verifying unweighted and weighted averaging math in `tests/unit/test_strategies.py`
- [X] T018 [P] [US2] Contract test for `src/retrieval/query.py` output format in `tests/contract/test_schemas.py`

**Checkpoint**: Retrieval and interpolation mechanisms produce valid synthesized adapters; linearity assumption validated (or measured).

---

## Phase 5: User Story 3 - Validating Performance via Environment Logic (Priority: P3)

**Goal**: Evaluate synthesized adapters on composite tasks using environment logic, run multiple trials (N≥5), and perform statistical testing with BH correction.

**Independent Test**: System runs evaluation, outputs success/failure logs, and generates a statistical report with p-values and BH correction.

### Implementation for User Story 3

- [X] T026a1 [US3] Download and convert the base LLM to GGUF format. **Action**: Use `llama.cpp`'s `convert-hf-to-gguf.py` script: `python convert-hf-to-gguf.py --model TinyLlama/TinyLlama-1B-Chat-v1.0 --outfile model.gguf`. **Pre-check**: Verify the model size fits within 7GB RAM using `os.path.getsize` on the downloaded file; if not, select `TheBloke/phi-2-GGUF` (quantized) as fallback. **Runtime Check**: Perform a dry-run inference to verify *runtime* memory usage remains within acceptable limits. If both models fail the runtime check, raise `MemoryError` and halt. (Depends on T004)
- [X] T026f [US3] **Implement** `src/evaluation/verify_memory_footprint.py` to explicitly verify the memory footprint of the quantized base LLM on the target runner before proceeding with the full evaluation loop. **Action**: Run a dry-run inference and log memory usage to ensure compliance with the system memory constraint. (Depends on T026a1)
- [X] T026b [US3] Implement memory validation and streaming/chunking logic in `src/evaluation/runner.py` to ensure the base LLM inference fits within 7GB RAM. Explicitly mandate 'load adapter -> run -> unload adapter' cycle. Log memory usage during first run. (Depends on T026f)
- [X] T025a [US3] **Implement** `src/evaluation/init_env_logic.py` to initialize and verify the **ALFWorld** environment logic before evaluation. **Action**: Run a dry-run task to ensure the environment returns a success/failure flag. **Interface**: `run_task(adapter_path: str, task_id: str) -> bool`. (Depends on T026a1)
- [X] T026 [US3] **Implement** `src/evaluation/runner.py` (FR-004) to apply adapters (from T022e) to a frozen base LLM and execute environment logic. **Input**: Use baseline from T026e1-restored for primary comparison. **Explicitly specify**: Use ALFWorld environment logic for primary evaluation; fallback to Search-QA if ALFWorld is unavailable. **Interface**: `run_task(adapter_path: str, task_id: str) -> bool` (import `alfworld.agents.environment`). (Depends on T026a1, T026e1-restored, T022e, T025a)
- [X] T027 [US3] **Implement** `src/evaluation/runner.py` loop to execute N >= 5 independent runs per task (FR-008) and record binary outcomes, calculating the mean of these outcomes. (Depends on T026)
- [X] T031a [US3] **Implement** `src/evaluation/run_sensitivity_sweep.py` to perform **descriptive analysis** of sensitivity results for k in {small integers, 3, 5, 10}. **Action**: Plot success rates vs k values and calculate variance. **Synthesis**: Combine descriptive and statistical findings into a single `robustness_score` (e.g., variance * -1 + mean_success). **DO NOT** generate p-values or perform statistical tests on this data. **Output**: Save descriptive statistics, plots, and `robustness_score` to `data/results/sensitivity.yaml`. (Depends on T022a)
- [X] T058 [US3] **Implement** `src/evaluation/run_sensitivity_sweep.py` to perform **statistical analysis** of sensitivity results. **Action**: Calculate p-values for differences between k values using a paired t-test or Wilcoxon test. **Output**: Save **raw (uncorrected)** p-values to `data/results/sensitivity_raw.json`. (Depends on T031a, T022a)
- [X] T057 [US3] **Implement** `src/evaluation/stats.py` (FR-005, FR-006) to perform paired t-test or Wilcoxon signed-rank test on success rates between strategies and baseline. **Action**: Aggregate p-values from primary comparisons only. **DO NOT** include sensitivity sweep p-values (as T058 handles those). **Output**: Save **raw (uncorrected)** p-values to `data/results/stats_raw.json`. (Depends on T027)
- [X] T032a [US3] **Implement** `src/evaluation/report_schema.py` to define the exact schema for `data/results/stats_report.json`. **Action**: Specify the exact fields: 'mean_success_rate', 'bh_corrected_p_values' (primary), 'linearity_correlation_coefficient' (for FR-007), 'reconstruction_error' (for SC-005), 'memory_footprint', 'sensitivity_bh_corrected_p_values', 'observed_success_rate_diff' (calculated as `mean(strategy_success) - mean(baseline_success)`). (Depends on T057, T058)
- [X] T032b [US3] **Implement** `src/evaluation/report_generator.py` to compile `data/results/sensitivity.yaml`, `data/results/sensitivity_raw.json`, `data/results/stats_raw.json`, and `data/results/reconstruction_error.json` into a single `data/results/stats_report.json`. **Action**: Apply Benjamini-Hochberg correction **separately** to the primary p-value list (from T057) and the sensitivity p-value list (from T058), storing them in distinct keys `bh_corrected_primary` and `bh_corrected_sensitivity`. **Schema**: Output must contain keys: 'mean_success_rate', 'bh_corrected_primary', 'bh_corrected_sensitivity', 'linearity_correlation_coefficient', 'reconstruction_error', 'memory_footprint', 'observed_success_rate_diff'. (Depends on T032a, T057, T022d, T058, T030, T030b)

### Tests for User Story 3

- [X] T024 [P] [US3] Contract test for `src/evaluation/stats.py` output schema in `tests/contract/test_schemas.py`
- [X] T025 [P] [US3] Integration test for full evaluation loop in `tests/integration/test_pipeline.py`

**Checkpoint**: Evaluation complete with statistical validation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T033a [P] Create `README.md` template with sections: 'Installation', 'Usage', 'Data Sources', and 'Results'. (Depends on T032b)
- [X] T033b [P] Populate `README.md` with specific content, code snippets, and data paths from the project. (Depends on T033a)
- [X] T033c [P] Create `docs/api.md` with function signatures and module descriptions. **Depends on T033b and completion of US1-US3**. (Depends on T033b)
- [X] T034 Code cleanup and refactoring of `src/retrieval/strategies.py`
- [X] T036 [P] Additional unit tests for edge cases in `tests/unit/`
- [X] T060 [P] **Re-verify** `src/validate/citation_check.py` **only if** `data_sources.yaml` hash has changed since the last run. **Action**: Compare current hash of `data_sources.yaml` with the hash stored in `data/processed/citation_verification.json`. If different, re-run verification. (Depends on T006b, T032b)
- [X] T038 Validate the quickstart path.

---

## Phase 7: Revision - Data Source & Execution Robustness

**Purpose**: Address specific review concerns regarding data source availability, execution failure handling, and memory constraints on the free runner.

### Implementation for Revision Concerns

- [X] T039 [US1] **Revise** `src/ingestion/download_weights.py` to implement a **strict streaming/fallback policy** for large datasets. **Action**: If the primary HuggingFace dataset is too large to download entirely, implement `datasets.load_dataset(..., streaming=True)` to iterate and save chunks to `data/raw/` sequentially. **Constraint**: If streaming fails or the dataset is inaccessible, the script MUST raise a `FileNotFoundError` and **halt**; do NOT fall back to synthetic data. **Note**: This task is an *additional* step after T012a succeeds. If T012a succeeds via arXiv, T039 is skipped. (Depends on T012a, T006b)
- [X] T040 [US3] **Revise** `src/evaluation/runner.py` to enforce a **strict memory cleanup cycle** between tasks. **Action**: Explicitly call `torch.cuda.empty_cache()` (if applicable) and `del adapter, model` followed by `gc.collect()` after every single task run to prevent memory accumulation during the N>=5 runs. Add a hard check: if `psutil.virtual_memory().percent > 90`, pause and log a warning before proceeding. (Depends on T026b, T026f)
- [X] T041 [US3] **Revise** `src/evaluation/init_env_logic.py` to include a **timeout mechanism** for the ALFWorld environment. **Action**: Wrap the `run_task` call in a `multiprocessing.Process` with a timeout. If the task exceeds the timeout, log it as a "timeout_failure" (treated as a failure outcome) and return `False` to prevent the runner from hanging indefinitely. (Depends on T025a)
- [X] T042 [US2] **Revise** `src/retrieval/query.py` to handle **out-of-distribution (OOD) queries** explicitly. **Action**: Calculate the distance to the nearest neighbor. If `distance > threshold` (configurable in `config.py`, default 0.8), raise a `ValueError` with a clear message indicating the query is OOD. Do NOT return a random or default vector. (Depends on T019, T022a)
- [X] T043 [US3] **Revise** `src/evaluation/stats.py` to include a **power analysis check** before running the final tests. **Action**: Implement a function to estimate statistical power based on the observed effect size using `statsmodels.stats.power.TTestIndPower`. **Input**: Read `observed_success_rate_diff` from `data/results/stats_report.json` (produced by T032b). **Fallback**: If T032b has not yet generated the report, use a conservative default effect size `d=0.3` for the power estimation. **Parameters**: Assume effect size `d=0.5`, `alpha=0.05`, desired power `=0.8`. If power < 0.8, log a warning and suggest increasing N, but proceed with the test (as per FR-008). Output the estimated power to `data/results/stats_report.json`. (Depends on T032b)

### Tests for Revision Concerns

- [X] T044 [P] [US1] Unit test for `src/ingestion/download_weights.py` to verify it raises `FileNotFoundError` when the source is missing and does NOT generate synthetic data. (Depends on T039)
- [X] T045 [P] [US3] Integration test for `src/evaluation/runner.py` to verify memory is released after each run and the process does not exceed 7GB RAM. (Depends on T040)
- [X] T046 [P] [US3] Unit test for `src/evaluation/init_env_logic.py` to verify the timeout mechanism triggers correctly on a simulated hanging task. (Depends on T041)

---

## Phase 8: Revision - Execution Safety & Edge Case Handling

**Purpose**: Add missing safety checks and edge case handling for robust execution on constrained runners.

### Implementation for Execution Safety

- [X] T047 [US3] **Implement** `src/evaluation/runner.py` to include a **disk space check** before writing large adapter files or logs. **Action**: Check `shutil.disk_usage()` immediately before any write operation and before the first run. If free space < 500MB, raise `RuntimeError` to prevent partial writes. (Depends on T026b)
- [X] T048 [US2] **Implement** `src/retrieval/strategies.py` to handle **empty result sets** when top-k retrieval returns fewer than k items. **Action**: If `len(retrieved) < k`, proceed with available items but log a `Warning: Insufficient neighbors retrieved (k={k}, found={len(retrieved)})`. Do not crash. (Depends on T022a)
- [X] T049 [US1] **Implement** `src/ingestion/download_weights.py` to include a **checksum validation** step after downloading. **Action**: Compare the SHA256 hash of the downloaded file against a known-good hash (if available in `data_sources.yaml` or a `checksums.json`). If hash is missing, log a warning and skip validation. If mismatch, delete the file and raise `FileNotFoundError`. (Depends on T012a)
- [X] T050 [US3] **Implement** `src/evaluation/stats.py` to handle **non-convergence** in statistical tests (e.g., all successes or all failures). **Action**: If variance is zero in a group, skip the t-test/Wilcoxon for that pair and log `Warning: Zero variance in group, statistical test skipped`. Output `NaN` for the p-value in that specific comparison. (Depends on T057)

### Tests for Execution Safety

- [X] T051 [P] [US3] Integration test for `src/evaluation/runner.py` to verify disk space check triggers correctly when space is low. (Depends on T047)
- [X] T052 [P] [US2] Unit test for `src/retrieval/strategies.py` to verify graceful handling of empty result sets. (Depends on T048)
- [X] T053 [P] [US1] Unit test for `src/ingestion/download_weights.py` to verify checksum validation fails on corrupted files. (Depends on T049)
- [X] T054 [P] [US3] Unit test for `src/evaluation/stats.py` to verify handling of zero-variance groups. (Depends on T050)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7 & 8)**: Depends on completion of Phase 3, 4, and 5 to ensure the core logic exists to be revised.

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
- Revision tasks (Phase 7 & 8) can be parallelized if they target different modules (e.g., T039 vs T040 vs T047).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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

### Revision Strategy

1. After US1-US3 are implemented and basic tests pass, execute Phase 7 and 8.
2. Run T039, T040, T041, T042, T043, T047, T048, T049, T050 in parallel if possible (different modules).
3. Execute T044, T045, T046, T051, T052, T053, T054 to validate the robustness improvements.
4. Re-run the full pipeline to ensure stability under load, OOD conditions, and edge cases.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All data loading tasks MUST fail loudly if real data is missing. Synthetic data is strictly prohibited unless explicitly generated as a fallback (T012c) with full documentation.
- **Plan.md Note**: The Constitution Check table in `plan.md` has been corrected to cite 'Pearson correlation' for FR-007 (Task T055c).

---

## Phase 9: Revision - Final Validation & Reporting

**Purpose**: Finalize the report generation, ensure all metrics are correctly aggregated, and prepare for the final review.

### Implementation for Final Validation

- [ ] T061 [P] **Implement** `src/evaluation/final_report.py` to generate the final human-readable report. **Action**: Aggregate all JSON/YAML results from `data/results/` (stats, sensitivity, latency, linearity, reconstruction) into a single Markdown document `reports/final_report.md`. **Template**:
 ```markdown
 # Final Report: llmXive LatentSkill Extension
 ## 1. Methodology
 - Dataset: [Source]
 - Models: [Base Model, Hypernetwork]
 - Metrics: [Success Rate, Latency, Linearity]
 ## 2. Results
 - Success Rates: [Table]
 - Latency: [Table]
 - Linearity: [Correlation, Error]
 ## 3. Statistical Significance
 - Primary BH Corrected P-Values: [Values]
 - Sensitivity BH Corrected P-Values: [Values]
 ## 4. Limitations
 - Power Analysis: [Result]
 - OOD Handling: [Result]
 ```
 **Output**: Save to `reports/final_report.md`. (Depends on T032b, T058, T019, T030)
- [ ] T062 [P] **Implement** `src/utils/plotting.py` to generate static plots for the final report. **Action**: Create functions to plot: (1) Success Rate vs Top-k, (2) Text-Weight Correlation, (3) Latency Breakdown. **Output**: Save high-res PNGs to `reports/plots/`. (Depends on T031a, T030, T019)
- [ ] T063 [P] **Execute** the full pipeline in "dry-run" mode (N=1 per task) to verify the entire flow from ingestion to final report generation without timing out. **Output**: Log any errors or warnings encountered during the dry-run. (Depends on T061, T062, T026)
- [ ] T064 [P] **Review** `reports/final_report.md` for completeness and accuracy. **Action**: Ensure all required metrics (SC-001 to SC-005) are present and correctly interpreted. Verify that all warnings (e.g., power < 0.8, OOD queries) are explicitly mentioned in the limitations section. (Depends on T061)

### Tests for Final Validation

- [ ] T065 [P] [US3] Unit test for `src/evaluation/final_report.py` to verify that all required keys are present in the generated report. (Depends on T061)
- [ ] T066 [P] [US3] Integration test for `src/utils/plotting.py` to verify that all plots are generated without errors and saved to the correct directory. (Depends on T062)

**Checkpoint**: Final report generated and validated. Project ready for final review.