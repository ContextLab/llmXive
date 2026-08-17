# Tasks: llmXive follow-up: extending "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills"

**Input**: Design documents from `/specs/001-lattentskill-retrieval-geometry/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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
- [X] T004b [P] Add default OOD threshold in `src/utils/config.py`: `OOD_THRESHOLD = 0.5` (float). This constant is used by `src/retrieval/query.py`.
- [X] T005 [P] Implement `src/utils/versioning.py` to compute SHA256 hashes for artifacts and update `state/projects/...yaml`
- [X] T006a [P] Create `data_sources.yaml` defining the canonical URLs/IDs **only** for the required datasets:
  1. `latent-skills/alfworld-weights` (HF Dataset ID: `latent-skills/alfworld-weights`)
  2. `latent-skills/searchqa-weights` (HF Dataset ID: `latent-skills/searchqa-weights`)
  3. `arXiv:2606.06087` (Supplementary URL: `https://arxiv.org/abs/2606.06087`)
- [X] T006 [P] Create `src/validate/citation_check.py` to verify dataset URLs listed in `data_sources.yaml`. **Implementation**: Perform HTTP 200 checks **and** validate the existence of weight files within the HF datasets. If the primary HF dataset is missing, the script must validate the existence of the arXiv source and prepare for fallback. (Depends on T006a, T004)
- [X] T006b [P] **Execute** `src/validate/citation_check.py` to verify all dataset sources before proceeding. **Output**: Save verification results to `data/processed/citation_verification.json`. If any critical source fails, log an error and halt. (Depends on T006, T004)
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
- [X] T010a [P] Add a contract file `specs/001-lattentskill-retrieval-geometry/contracts/latency_schema.json` defining keys `embedding_latency_ms`, `retrieval_latency_ms`, `interpolation_latency_ms`, `total_skill_selection_latency_ms` (all numbers). This will be used by T019.
- [X] T010b [P] Add a contract file `specs/001-lattentskill-retrieval-geometry/contracts/linearity_schema.json` defining keys `correlation_coefficient` (number), `linearity_valid` (boolean or null), `max_error` (number or null), `reconstruction_error` (object with `mean` and `max` numbers). Used by T030.
- [X] T067 [P] **Atomic write for weight downloads**: Ensure `src/ingestion/download_weights.py` writes each downloaded weight file to a temporary `.tmp` file, validates checksum (if available), then atomically renames to final destination. Delete the temp file on failure. (Depends on T004, T006b)
- [X] T068 [P] **Incremental index building**: Modify `src/retrieval/vector_db.py` to accept a streaming iterator of vectors (e.g., from `datasets.load_dataset(..., streaming=True)`) and append them to the index in chunks, producing the same final `.npz` index as batch mode. (Depends on T004, T013)
- [X] T026e1-revoked [P] **Verify baseline hypernetwork**: Check that `artifacts/baseline_adapter.pt` (original LatentSkill hypernetwork weights) exists. If missing, **raise a RuntimeError and abort the pipeline**. No proxy model will be created. This task guarantees that downstream latency and evaluation tasks have a valid baseline as required by SC‑001/SC‑003. (Depends on T004)
- [X] T055 [P] **Update Plan**: Edit `specs/001-lattentskill-retrieval-geometry/plan.md` to correct the 'Constitution Check' table (replace "Spearman correlation" with "Pearson correlation"). (Depends on T004)
- [X] T055c [P] **Execute Plan Update**: Verify and ensure `plan.md` contains "Pearson correlation" in the 'Constitution Check' table. If not, the task fails. **Note**: This task corrects a planning artifact error to align with spec.md (FR-007) before execution proceeds. (Depends on T055)
- [X] T055d [P] **Flag Plan Integrity**: If `plan.md` contains the "Python type hints" copy-paste error in the 'Technical Context' section, log a CRITICAL error and halt. This artifact must be corrected by the planning agent before tasks proceed. (Depends on T055c)

---


## Phase 3: User Story 1 - Constructing the Skill Vector Database (Priority: P1) 🎯 MVP

**Goal**: Ingest pre‑trained LoRA adapters (A and B matrices) from ALFWorld and Search‑QA, flatten them into normalized high‑dimensional vectors, and generate a static CPU‑compatible index.

**Independent Test**: System loads raw LoRA weights, normalizes them, and outputs a `.npy` or `.npz` index file with metadata without requiring GPU.

### Implementation for User Story 1

- [ ] T012a [US1] **Implement** `src/ingestion/download_weights.py` to fetch real LoRA weights. **Primary Source**: HuggingFace dataset `latent-skills/alfworld-weights` (`weights/alfworld/*.npz`) and `latent-skills/searchqa-weights` (`weights/searchqa/*.npz`). **Fallback 1**: If HF fails, attempt to download from the arXiv supplementary URL (`https://arxiv.org/abs/2606.06087`). **Fallback 2**: If arXiv fails, attempt to clone the original GitHub repository (`https://github.com/LatentSkill/weights.git`). **Strict Failure**: If **all** sources fail, write `data/processed/data_fetch_status.json` with `status: "failed"` and **exit with code 0** (do not halt pipeline). **Output**: Log the exact source used or the specific failure reason. (Depends on T006b, T004, T067)
- [ ] T012b [US1] **Execute** `src/ingestion/download_weights.py`. (Depends on T012a)
- [ ] T012c [US1] **Generate Synthetic Proxy** (Conditional). **Action**: Check `data/processed/data_fetch_status.json`. If `status == "failed"`, generate LoRA‑like weight matrices with dimensions matching the expected base model (TinyLlama: hidden_size=2048, rank=16, num_layers=16) using `seed=42`. **Constraint**: This is a fallback ONLY. Log `'SYNTHETIC DATA USED'` and save to `data/raw/synthetic_proxy_weights.npz`. If status is `"success"`, skip this task. (Depends on T012b)
- [ ] T013 [US1] Implement `src/ingestion/flatten_lora.py` (FR-001) to load A/B matrices from `data/raw/` (real from T012a **or** synthetic from T012c), flatten to 1D, and apply L2 normalization. (Depends on T012b, T012c)
- [ ] T014c [US1] Implement logic in `src/retrieval/vector_db.py` (FR-001) to load flattened vectors and prepare data for serialization. CLI must accept `--input <path>` `--output <path>` `--k <int>`. (Depends on T013, T068)
- [ ] T014d [US1] **Execute** `python src/retrieval/vector_db.py --input data/raw/weights.npz --output data/processed/skill_index.npz --k 5`. Verify file existence, checksum, and data type compatibility. (Depends on T014c)
- [ ] T015 [US1] Add validation in `src/ingestion/flatten_lora.py` to ensure consistent dimensions across all adapters.
- [ ] T016 [US1] Add logging for ingestion metrics (vectors processed, index size) in `src/ingestion/flatten_lora.py`.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for `src/ingestion/flatten_lora.py` to verify vector dimensionality matches A*B product (`tests/unit/test_ingestion.py`). (Depends on T013)
- [ ] T011 [P] [US1] Integration test for ingestion pipeline in `tests/integration/test_pipeline.py` verifying index generation on CPU. (Depends on T013)

---


## Phase 4: User Story 2 - Executing Retrieval and Interpolation Strategies (Priority: P2)

**Goal**: Query the Skill Vector Database using text embeddings, retrieve nearest neighbors, and synthesize LoRA adapters via unweighted mean and cosine‑weighted averaging.

**Independent Test**: System takes a novel task description, executes retrieval/interpolation, and outputs synthesized LoRA adapter files on CPU.

### Implementation for User Story 2

- [ ] T059a [US2] **Implement** `src/evaluation/verify_runner.py` to verify the runner's hardware constraints (standard 2‑core CPU). Save `runner_core_count` to `data/results/latency_metrics.json`. (Depends on T004)
- [ ] T019 [US2] Implement `src/retrieval/query.py` (FR-002) to generate query vectors using `all-MiniLM-L6-v2`. **Mandatory Latency Logging**: Measure and log `embedding_latency_ms`, `retrieval_latency_ms`, `interpolation_latency_ms`, and compute `total_skill_selection_latency_ms`. Output must conform to `latency_schema.json`. (Depends on T014c, T059a)
- [ ] T059 [US2] **Implement** `src/retrieval/query.py` to measure **baseline hypernetwork latency**. **Action**: Check for `artifacts/baseline_adapter.pt` (verified by T026e1-revoked). Load and time a single inference; if the file is missing the pipeline would have already aborted. Append `baseline_latency_ms` to `data/results/latency_metrics.json`. (Depends on T026e1-revoked, T059a)
- [ ] T059c [US2] **Implement** `src/retrieval/query.py` to calculate **computational savings**: `savings_ms = baseline_latency_ms - total_skill_selection_latency_ms`. If `baseline_latency_ms` is NaN, set `savings_ms` to NaN. Append `computational_savings_ms` to `latency_metrics.json`. (Depends on T019, T059)
- [ ] T022a [US2] Implement `src/retrieval/strategies.py` (FR-003) for:
   1. Single Nearest Neighbor selection
   2. Unweighted Arithmetic Mean of top‑k vectors
   3. Cosine‑Weighted Averaging (weights normalized). Include OOD check: if nearest‑neighbor distance > `OOD_THRESHOLD` (from config), raise `ValueError`. Raise `ValueError` for OOD queries. (Depends on T014c, T019)
- [ ] T022e [US2] Implement serialization in `src/retrieval/strategies.py` to save synthesized A/B matrices to `artifacts/synthesized_adapters/`. Verify dimensions and non‑NaN values. (Depends on T022a)
- [ ] T023a [US2] **Implement** `src/validation/generate_eval_tasks.py` to generate held‑out composite task descriptions and true composite weights (if available). Save `data/processed/true_composites.yaml` (or status `untestable`) and `data/processed/eval_tasks.yaml`. **Note**: If true weights are unavailable, the file must explicitly contain `status: untestable` to signal downstream tasks. (Depends on T014d)
- [ ] T022d [US2] **Implement** `src/validation/reconstruction_error.py` to calculate cosine distance between synthesized LoRA weights and true composite weights. Output `mean` and `max` error to `data/results/reconstruction_error.json`; flag if `max_error > 0.05`. (Depends on T022e, T023a)
- [ ] T030 [US2] **Implement** `src/validation/linearity_check.py` to compute Pearson correlation between text‑space and weight‑space distances, validate against SC‑005 (max_error < 0.05). Output must follow `linearity_schema.json`. If T023a returns 'untestable', output `null` for correlation and `false` for linearity_valid. (Depends on T023a, T019, T022d)
- [ ] T030b [US2] **Aggregate Linearity Validation**: Merge results from `reconstruction_error.json` and `linearity_validation.json` into a single `data/results/linearity_validation.json` with fields `linearity_valid`, `correlation_coefficient`, `max_error`, and include the full reconstruction error object. **Fallback**: If input from T030 is null, set `linearity_valid=false` and `correlation_coefficient=0.0` to ensure valid boolean output. (Depends on T023a, T030)

### Tests for User Story 2

- [ ] T017 [P] [US2] Unit test for `src/retrieval/strategies.py` verifying unweighted and weighted averaging math (`tests/unit/test_strategies.py`).
- [ ] T018 [P] [US2] Contract test for `src/retrieval/query.py` output format (`tests/contract/test_schemas.py`).

---


## Phase 5: User Story 3 - Validating Performance via Environment Logic (Priority: P3)

**Goal**: Evaluate synthesized adapters on composite tasks using environment logic, run multiple trials (N≥5), and perform statistical testing with BH correction.

**Independent Test**: System runs evaluation, outputs success/failure logs, and generates a statistical report with p‑values and BH correction.

### Implementation for User Story 3

- [ ] T026a1 [US3] Download and convert the base LLM to GGUF format (e.g., TinyLlama‑1B‑Chat). Verify size < 7 GB and perform a dry‑run inference to ensure memory fits. (Depends on T004)
- [ ] T026f [US3] **Implement** `src/evaluation/verify_memory_footprint.py` to run a dry‑run inference and log memory usage, ensuring compliance with the 7 GB limit. (Depends on T026a1)
- [ ] T026b [US3] Implement streaming/chunking logic in `src/evaluation/runner.py` to load the base LLM, apply an adapter, run the task, then unload. Log memory usage and pause if virtual memory > 90 %. (Depends on T026f)
- [ ] T025a [US3] **Implement** `src/evaluation/init_env_logic.py` to initialize ALFWorld environment and provide `run_task(adapter_path: str, task_id: str) -> bool`. Include a timeout wrapper (max 30 s) that logs a timeout failure and returns `False`. (Depends on T026a1)
- [ ] T026 [US3] **Implement** `src/evaluation/runner.py` (FR-004) to apply adapters (from T022e) to the frozen base LLM and execute environment logic. Use the baseline from `artifacts/baseline_adapter.pt` (verified earlier). (Depends on T026a1, T026e1-revoked, T022e, T025a)
- [ ] T027 [US3] **Implement** loop in `src/evaluation/runner.py` to execute N ≥ 5 independent runs per task (FR-008) and record binary outcomes, calculating the mean success rate. (Depends on T026)
- [ ] T031a [US3] **Implement** `src/evaluation/run_sensitivity_sweep.py` to perform descriptive analysis of sensitivity results for various k values; save plots and a `robustness_score` to `data/results/sensitivity.yaml`. (Depends on T022a)
- [ ] T058 [US3] **Implement** `src/evaluation/run_sensitivity_sweep.py` to calculate p‑values for differences between k values using paired t‑test or Wilcoxon (as appropriate). Save raw p‑values to `data/results/sensitivity_raw.json`. (Depends on T031a)
- [ ] T057 [US3] **Implement** `src/evaluation/stats.py` (FR-005, FR-006) to perform paired t‑test or Wilcoxon signed‑rank test on success rates between each strategy and the baseline. Save raw (uncorrected) p‑values to `data/results/stats_raw.json`. (Depends on T027)
- [ ] T032a [US3] **Implement** `src/evaluation/report_schema.py` defining `stats_report.json` schema with fields:
   - `mean_success_rate` (number)
   - `bh_corrected_primary` (object of corrected p‑values)
   - `bh_corrected_sensitivity` (object)
   - `linearity_correlation_coefficient` (number)
   - `reconstruction_error` (object with `mean` and `max`)
   - `memory_footprint` (number, MB)
   - `observed_success_rate_diff` (number, calculated as `mean(strategy_success) - mean(baseline_success)`, rounded to 4 dp)
   - `power_estimate` (number, 0‑1)
   - `bh_rejected_count` (int)
   - `bonferroni_rejected_count` (int) **(removed in later revision)**
- [ ] T032b [US3] **Implement** `src/evaluation/report_generator.py` to compile all result files into `data/results/stats_report.json`, applying Benjamini‑Hochberg correction separately for primary and sensitivity p‑values. (Depends on T032a, T057, T058, T022d, T030, T030b)
- [ ] T043 [US3] **Revise** `src/evaluation/stats.py` to include a power analysis check using `statsmodels.stats.power.TTestIndPower`. Read `observed_success_rate_diff` from `stats_report.json` (or default effect size 0.3). Assume `alpha=0.05`, desired power 0.8, effect size 0.5 if not available. Log warning if estimated power < 0.8 but continue. Output `power_estimate` into `stats_report.json`. (Depends on T032b)

### Tests for User Story 3

- [ ] T024 [P] [US3] Contract test for `src/evaluation/stats.py` output schema (`tests/contract/test_schemas.py`).
- [ ] T025 [P] [US3] Integration test for full evaluation loop (`tests/integration/test_pipeline.py`).

---


## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T033a [P] Create `README.md` template with sections: Installation, Usage, Data Sources, Results. (Depends on T032b)
- [X] T033b [P] Populate `README.md` with concrete content, code snippets, and data paths. (Depends on T033a)
- [X] T033c [P] Create `docs/api.md` with function signatures and module descriptions. (Depends on T033b)
- [X] T034 Code cleanup and refactoring of `src/retrieval/strategies.py`
- [X] T036 [P] Additional unit tests for edge cases in `tests/unit/`
- [X] T060 [P] **Re‑verify** `src/validate/citation_check.py` **only if** `data_sources.yaml` hash has changed since the last run. (Depends on T006b, T032b)

---


## Phase 7: Revision - Data Source & Execution Robustness

**Purpose**: Address specific review concerns regarding data source availability, execution failure handling, and memory constraints on the free runner.

- [X] T039 [US1] **Revise** `src/ingestion/download_weights.py` to implement strict streaming/fallback policy using `datasets.load_dataset(..., streaming=True)`. On streaming failure, raise `FileNotFoundError` and write status file; **do NOT** generate synthetic data here. (Depends on T012a, T006b)
- [X] T040 [US3] **Revise** `src/evaluation/runner.py` to enforce strict memory cleanup: call `torch.cuda.empty_cache()` (if applicable), `del adapter, model`, then `gc.collect()`. Pause and warn if `psutil.virtual_memory().percent > 90`. (Depends on T026b, T026f)
- [X] T041 [US3] **Revise** `src/evaluation/init_env_logic.py` to include timeout via `multiprocessing.Process`. Log timeout as failure and return `False`. (Depends on T025a)
- [X] T042 [US2] **Revise** `src/retrieval/query.py` to raise `ValueError` when OOD distance > `OOD_THRESHOLD` (config key defined in T004b). No default vector is returned. (Depends on T019, T022a)
- [X] T043 [US3] **Revise** `src/evaluation/stats.py` to include power analysis (as described in T043 above). (Depends on T032b)

---


## Phase 8: Revision - Execution Safety & Edge Case Handling

**Purpose**: Add missing safety checks and edge case handling for robust execution on constrained runners.

- [X] T047 [US3] **Implement** disk‑space check in `src/evaluation/runner.py` before writing adapters or logs (require ≥ 500 MB free). Raise `RuntimeError` if insufficient. (Depends on T026b)
- [X] T048 [US2] **Implement** handling of empty result sets in `src/retrieval/strategies.py`: if retrieved < k, log a warning and proceed with available items. (Depends on T022a)
- [X] T049 [US1] **Implement** checksum validation after download in `src/ingestion/download_weights.py`. Compare SHA256 against known hash in `data_sources.yaml` (if present); on mismatch delete file and raise `FileNotFoundError`. (Depends on T012a)
- [X] T050 [US3] **Implement** handling of zero‑variance groups in `src/evaluation/stats.py`: skip the statistical test, log warning, and output `NaN` for that p‑value. (Depends on T057)

---


## Phase 9: Final Validation & Reporting

**Purpose**: Finalize the report generation, ensure all metrics are correctly aggregated, and prepare for the final review.

- [ ] T061a [P] **Implement** `src/evaluation/final_report.py` to generate a complete Markdown `reports/final_report.md`. The report must contain:
   1. **Methodology** (sources from `data_sources.yaml`, base model from T026a1)
   2. **Results** table (read from `stats_report.json`)
   3. **Latency** table (read from `latency_metrics.json`)
   4. **Linearity Validation (SC‑005)** section: display PASS/FAIL/UNTESTABLE based on `linearity_valid` and `max_error`.
   5. **Statistical Significance** (BH‑corrected primary and sensitivity p‑values)
   6. **Limitations**: include power analysis result, OOD handling notes, and any warnings from earlier stages.
   The generator must also create a minimal **failure report** if any upstream task aborts, stating which phase failed. (Depends on T032b, T062, T026e1-revoked)
- [ ] T062 [P] **Implement** `src/utils/plotting.py` to produce static PNG plots for:
   1. Success Rate vs Top‑k
   2. Text‑Weight Pearson Correlation
   3. Latency breakdown (embedding, retrieval, interpolation, baseline)
   Save plots to `reports/plots/`. (Depends on T031a, T030, T019)
- [ ] T063a [P] **Execute** a dry‑run of the full pipeline with N = 1 per task to verify end‑to‑end flow without timeout. Log any errors to `reports/dry_run_log.txt`. (Depends on T061a, T062, T026)
- [ ] T064a [P] **Review** `reports/final_report.md` for completeness, correctness, and inclusion of all required SC metrics. Flag missing items; if any critical metric is absent, mark the pipeline as needing revision. (Depends on T063a)

---


## Phase 10: Data Integrity & Pipeline Resilience

**Purpose**: Address critical concerns regarding data integrity during streaming, ensuring the pipeline handles partial failures gracefully without corrupting the index, and verifying the statistical robustness of the final results.

- [X] T069 [US3] **Implement** retry mechanism in `src/evaluation/runner.py` for transient environment failures (max 2 retries with exponential backoff). Do not retry logical failures. (Depends on T026, T041)
- [X] T070 (removed) – the Bonferroni sensitivity analysis was eliminated as it was not required by the spec.
