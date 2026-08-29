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

**Purpose**: Project initialization, basic structure, and plan integrity checks

- [X] T055d [P] **Update Spec for Amendment**: Edit `specs/001-lattentskill-retrieval-geometry/spec.md` to formally document the "Functional Linearity" amendment. Add a section "Amendment to FR-007/SC-005" stating that if ground-truth composite weights are missing from the dataset, the geometric reconstruction error metric is waived in favor of the "Functional Linearity" (success rate) metric, and the pipeline will report "UNTESTABLE" for geometric validation. (Depends on T004)
- [X] T055 [P] **Update Plan**: Edit `specs/001-lattentskill-retrieval-geometry/plan.md` to correct the 'Constitution Check' table (replace "Spearman correlation" with "Pearson correlation"). (Depends on T004)
- [X] T055c [P] **Execute Plan Update**: Verify and ensure `plan.md` contains "Pearson correlation" in the 'Constitution Check' table. If not, the task fails. **Note**: This task corrects a planning artifact error to align with spec.md (FR-007) before execution proceeds. (Depends on T055)
- [X] T001b [P] Create all `__init__.py` files for the following exact paths: `src/ingestion/__init__.py`, `src/retrieval/__init__.py`, `src/evaluation/__init__.py`, `src/validation/__init__.py`, `src/validate/__init__.py`, `src/utils/__init__.py`. (Empty or minimal docstring)
- [X] T002a Create `requirements.txt` with the following EXACT pinned versions: `torch==2.1.0`, `numpy==1.24.3`, `scikit-learn==1.3.0`, `sentence-transformers==2.2.2`, `transformers==4.35.0`, `pandas==2.1.0`, `scipy==1.11.0`, `llama-cpp-python==0.2.30`, `faiss-cpu==1.7.4`, `huggingface-hub==0.19.0`, `datasets==2.14.0`, `pytest==7.4.0`, `pyyaml==6.0.1`. **Do not rely on external files to verify this list; this task defines the definitive dependency set.**
- [X] T002b Run `pip install -r requirements.txt` to verify dependency resolution
- [X] T003a [P] Create `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections (line-length=88, target-version=py)
- [X] T003b [P] Create `.ruff.toml` with `line-length = 88` and `ignore = ["E501", "W605"]`
- [X] T001c [P] Ensure `data/`, `artifacts/`, `data/raw/`, `data/processed/`, `data/results/`, and **`artifacts/synthesized_adapters/`** directories exist in the repo. **Create nested subdirectories**: `artifacts/synthesized_adapters/`. Add these to `.gitignore`. Do NOT create `.gitkeep` files here.
- [X] T004 Setup `src/utils/config.py` for seed pinning, path resolution, and environment variable loading
- [X] T004b [P] Add default OOD threshold in `src/utils/config.py`: `OOD_THRESHOLD = 0.5` (float). This constant is used by `src/retrieval/query.py`.
- [X] T005 [P] Implement `src/utils/versioning.py` to compute SHA256 hashes for artifacts and update `state/projects/...yaml`
- [X] T006a [P] Create `data_sources.yaml` defining the canonical URLs/IDs **only** for the required sources:
 1. `arxiv_supplementary`: `https://arxiv.org/src/2606.06087v1/ancillary.zip`
 2. `github_weights`: `https://github.com/latent-skills/weights`
 3. `baseline_adapter_url`: `https://huggingface.co/latent-skills/baseline_adapter/resolve/main/baseline.pt` (or a verified proxy URL)
 4. **Note**: Do NOT use unverified HuggingFace dataset IDs. Use these verified sources only. (Depends on T004)
- [X] T006 [P] Create `src/validate/citation_check.py` to verify dataset URLs listed in `data_sources.yaml`. **Implementation**: Perform HTTP 200 checks **and** validate the existence of weight files within the arXiv/GitHub sources. If the primary source fails, validate the fallback. (Depends on T006a, T004)
- [X] T006b [P] **Execute** `src/validate/citation_check.py` to verify all dataset sources before proceeding. **Output**: Save verification results to `data/processed/citation_verification.json`. If any critical source fails, log an error and halt. (Depends on T006, T004, T055d)
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
- [X] T067b [P] **Organize Downloaded Weights**: Implement logic in `src/ingestion/download_weights.py` or a separate script to ensure all downloaded files are moved to `data/raw/lora_weights/`. If files are found in `data/raw/` root, move them to `data/raw/lora_weights/`. Verify the directory structure matches the plan. (Depends on T004, T012a)
- [X] T068 [P] **Incremental index building**: Modify `src/retrieval/vector_db.py` to accept a streaming iterator of vectors (e.g., from `datasets.load_dataset(..., streaming=True)`) and append them to the index in chunks, producing the same final `.npy` index as batch mode. (Depends on T004, T013)
- [X] T071 [P] **Revise** `src/ingestion/download_weights.py` to explicitly remove any `try/except` blocks that might catch `FileNotFoundError` and return a default/synthetic object. Ensure that any failure to download from the primary (arXiv/GitHub) or secondary sources raises a fatal exception that halts the script, writing only a failure status to `data/processed/data_fetch_status.json`. (Depends on T006b, T004)
- [X] T072 [P] **Implement** a strict "No Synthetic Data" guard in `src/ingestion/flatten_lora.py`. If the input directory `data/raw/lora_weights/` contains no files or only placeholder markers, the script must raise `RuntimeError` with the message "No real data found; pipeline halted to prevent fabrication." (Depends on T004, T071)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002c [P] **Verify Model and Constraints**: Add a check in `src/utils/config.py` or a separate script to verify that `all-MiniLM-L6-v2` is available and that no `synthetic-data` packages are installed. **Action**: Ensure `requirements.txt` does not contain synthetic packages. (Depends on T002a)
- [X] T067 [P] **Atomic write for weight downloads**: Ensure `src/ingestion/download_weights.py` writes each downloaded weight file to a temporary `.tmp` file, validates checksum (if available), then atomically renames to final destination. Delete the temp file on failure. (Depends on T004, T006b)
- [X] T067b [P] **Organize Downloaded Weights**: Implement logic in `src/ingestion/download_weights.py` or a separate script to ensure all downloaded files are moved to `data/raw/lora_weights/`. If files are found in `data/raw/` root, move them to `data/raw/lora_weights/`. Verify the directory structure matches the plan. (Depends on T004, T012a)
- [X] T068 [P] **Incremental index building**: Modify `src/retrieval/vector_db.py` to accept a streaming iterator of vectors (e.g., from `datasets.load_dataset(..., streaming=True)`) and append them to the index in chunks, producing the same final `.npy` index as batch mode. (Depends on T004, T013)
- [X] T071 [P] **Revise** `src/ingestion/download_weights.py` to explicitly remove any `try/except` blocks that might catch `FileNotFoundError` and return a default/synthetic object. Ensure that any failure to download from the primary (arXiv/GitHub) or secondary sources raises a fatal exception that halts the script, writing only a failure status to `data/processed/data_fetch_status.json`. (Depends on T006b, T004)
- [X] T072 [P] **Implement** a strict "No Synthetic Data" guard in `src/ingestion/flatten_lora.py`. If the input directory `data/raw/lora_weights/` contains no files or only placeholder markers, the script must raise `RuntimeError` with the message "No real data found; pipeline halted to prevent fabrication." (Depends on T004, T071)

---

## Phase 3: User Story 1 - Constructing the Skill Vector Database (Priority: P1) 🎯 MVP

**Goal**: Ingest pre‑trained LoRA adapters (A and B matrices) from ALFWorld and Search‑QA, flatten them into normalized high‑dimensional vectors, and generate a static CPU‑compatible index.

**Independent Test**: System loads raw LoRA weights, normalizes them, and outputs a `.npy` index file with metadata without requiring GPU.

### Implementation for User Story 1

- [X] T012a [US1] **Implement** `src/ingestion/download_weights.py` to fetch real LoRA weights. **Primary Source**: Use the URL under key `arxiv_supplementary` in `data_sources.yaml`. **Fallback**: Use the URL under key `github_weights` in `data_sources.yaml`. **Strict Failure**: If **all** sources fail, write `data/processed/data_fetch_status.json` with `status: "failed"` and **exit with code 1** (HALT pipeline). **Output**: Log the exact source used or the specific failure reason. **Target Directory**: Download files directly to `data/raw/lora_weights/`. (Depends on T006b, T004, T067, T071)
- [X] T012b [US1] **Execute** `src/ingestion/download_weights.py`. (Depends on T012a)
- [X] T013 [US1] Implement `src/ingestion/flatten_lora.py` (FR-001) to load A/B matrices from `data/raw/lora_weights/` (real from T012b), flatten to 1D, and apply L2 normalization. **Execution Logic**: This task runs if T012b succeeds. If T012b fails (exit code 1), the pipeline halts immediately. **Output**: Save flattened vectors to `data/processed/weights_flattened.npz`. (Depends on T012b, T072)
- [X] T014c [US1] Implement logic in `src/retrieval/vector_db.py` (FR-001) to load flattened vectors and prepare data for serialization. **Output Format**: Explicitly produce `data/processed/skill_index.npy` (NumPy format, not `.npz`). CLI must accept `--input <path>` `--output <path>` `--k <int>`. (Depends on T013, T068)
- [X] T014d [US1] **Execute** `python src/retrieval/vector_db.py --input data/processed/weights_flattened.npz --output data/processed/skill_index.npy --k 5`. Verify file existence, checksum, data type compatibility, and **confirm the file extension is `.npy`**. (Depends on T014c, T013)
- [X] T015 [US1] Add validation in `src/ingestion/flatten_lora.py` to ensure consistent dimensions across all adapters.
- [X] T016 [US1] Add logging for ingestion metrics (vectors processed, index size) in `src/ingestion/flatten_lora.py`.

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test for `src/ingestion/flatten_lora.py` to verify vector dimensionality matches A*B product (`tests/unit/test_ingestion.py`). (Depends on T013)
- [X] T011 [P] [US1] Integration test for ingestion pipeline in `tests/integration/test_pipeline.py` verifying index generation on CPU. (Depends on T013)

---


## Phase 4: User Story 2 - Executing Retrieval and Interpolation Strategies (Priority: P2)

**Goal**: Query the Skill Vector Database using text embeddings, retrieve nearest neighbors, and synthesize LoRA adapters via unweighted mean and cosine‑weighted averaging.

**Independent Test**: System takes a novel task description, executes retrieval/interpolation, and outputs synthesized LoRA adapter files on CPU.

### Implementation for User Story 2

- [X] T059a [US2] **Implement** `src/evaluation/verify_runner.py` to verify the runner's hardware constraints (standard 2-core CPU). Save `runner_core_count` to `data/results/latency_metrics.json`. (Depends on T004)
- [X] T059d [US2] **Acquire Baseline Adapter**: Implement `src/evaluation/acquire_baseline.py` to generate or download `artifacts/baseline_adapter.pt`. **Logic**: Check `data_sources.yaml` for `baseline_adapter_url`. If present and reachable, download. If missing or unreachable, generate a proxy baseline (e.g., random weights or a simple fine-tuned proxy if available in the repo) and log this action as "PROXY_GENERATED". **Output**: Save to `artifacts/baseline_adapter.pt`. (Depends on T006a, T004)
- [X] T019 [US2] Implement `src/retrieval/query.py` (FR-002) to generate query vectors using `sentence-transformers/all-MiniLM-L-v2`. **Mandatory Latency Logging**: Measure and log `embedding_latency_ms`, `retrieval_latency_ms`, `interpolation_latency_ms`, and compute `total_skill_selection_latency_ms`. Output must conform to `latency_schema.json`. **OOD Check**: If nearest-neighbor distance > `OOD_THRESHOLD`, raise `ValueError`. (Depends on T014c, T059a)
- [X] T059b [US2] **Implement** `src/retrieval/query.py` to measure **baseline latency**. **Action**: Load `artifacts/baseline_adapter.pt` (from T059d). If missing, the task fails. Time a single inference. Append `baseline_latency_ms` to `data/results/latency_metrics.json`. (Depends on T059a, T059d)
- [X] T059e [US2] **Synchronize Latency Measurements**: Implement a synchronization step that waits for both T019 (retrieval latency) and T059b (baseline latency) to complete and writes their outputs to `data/results/latency_metrics.json` before T059c runs. (Depends on T019, T059b)
- [X] T059c [US2] **Implement** `src/retrieval/query.py` to calculate **computational savings**: `savings_ms = baseline_latency_ms - total_skill_selection_latency_ms`. If `baseline_latency_ms` is NaN, set `savings_ms` to NaN. Append `computational_savings_ms` to `latency_metrics.json`. (Depends on T019, T059b, T059e)
- [X] T022a [US2] Implement `src/retrieval/strategies.py` (FR-003) for:
 1. Single Nearest Neighbor selection (Output: `artifacts/synthesized_adapters/nn_{task_id}.npz`)
 2. Unweighted Arithmetic Mean of top‑k vectors (Output: `artifacts/synthesized_adapters/mean_{task_id}.npz`)
 3. Cosine‑Weighted Averaging (Output: `artifacts/synthesized_adapters/weighted_{task_id}.npz`). Include OOD check: if nearest‑neighbor distance > `OOD_THRESHOLD` (from config), raise `ValueError`. (Depends on T014c, T019)
- [X] T022e [US2] Implement serialization in `src/retrieval/strategies.py` to save synthesized A/B matrices to `artifacts/synthesized_adapters/`. Verify dimensions and non‑NaN values. **Graceful Handling**: If `data/processed/untestable_marker.json` exists (indicating T023a failed to find true weights), write a `skipped_marker.json` to `artifacts/synthesized_adapters/` and exit with code 0. Do NOT attempt synthesis. (Depends on T022a)
- [X] T023a [US2] **Implement** `src/validation/generate_eval_tasks.py` to generate held‑out composite task descriptions. **Requirement**: Do NOT attempt to generate "true composite weights" for novel tasks (impossible). If `data/processed/cvs_status.json` (from T023b) indicates `status: 'missing_ground_truth'`, write `data/processed/untestable_marker.json` with `reason: "missing_ground_truth"` and **exit with code 0** (do NOT halt pipeline). **Output**: Save `data/processed/eval_tasks.yaml` (task descriptions) if successful. (Depends on T014d, T023b)
- [X] T022d [US2] **Implement** `src/validation/reconstruction_error.py` to calculate cosine distance between synthesized LoRA weights and true composite weights. **Logic**: If `artifacts/synthesized_adapters/skipped_marker.json` exists (from T022e) OR `data/processed/untestable_marker.json` exists (from T023a), write `data/results/reconstruction_error.json` with `status: "untestable"` and exit 0. Otherwise, compute error, output `mean` and `max` to `data/results/reconstruction_error.json`; flag if `max_error > 0.05`. (Depends on T022e, T023a)
- [X] T023b [US2] **Generate Composite Validation Subset (CVS)**: Implement `src/validation/generate_cv_set.py` to attempt loading known ground-truth task pairs from the verified dataset (e.g., `data/raw/lora_weights/cv_pairs.yaml` if present). **Logic**: If the dataset lacks these pairs (which is the expected case), write `data/processed/cvs_status.json` with `status: 'missing_ground_truth'`, `reason: 'dataset_lacks_cv_pairs'`, and **exit with code 0** (do NOT halt pipeline). If pairs exist, save them to `data/processed/cv_set_pairs.yaml`. (Depends on T006b, T004)
- [X] T030 [US2] **Implement** `src/validation/linearity_check.py` to compute Pearson correlation between text‑space and weight‑space distances, validate against SC‑005 (max_error < 0.05). Output must follow `linearity_schema.json`. **Logic**: Read `data/processed/cvs_status.json`. If `status: 'missing_ground_truth'`, write `data/results/linearity_validation.json` with `status: "UNTESTABLE"`, `correlation_coefficient: null`, `max_error: null`, and **exit with code 0**. Do NOT halt the pipeline. If pairs exist, compute correlation and error. (Depends on T023b, T019, T022d)
- [X] T030a [US2] **Execute** `src/validation/linearity_check.py` and generate `data/results/linearity_validation.json`. If the script outputs 'UNTESTABLE', report 'SC-005 FAILED: Missing Ground Truth' in the final report. (Depends on T030)
- [X] T030b [US2] **Aggregate Linearity Validation**: Merge results from `reconstruction_error.json` and `linearity_validation.json` into a single `data/results/linearity_validation.json` with fields `linearity_valid`, `correlation_coefficient`, `max_error`, and include the full reconstruction error object. **Fallback**: If upstream data is missing, set `linearity_valid=null`, `correlation_coefficient=null`, and status='UNTESTABLE' to preserve scientific accuracy. (Depends on T023b, T030a)

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for `src/retrieval/strategies.py` verifying unweighted and weighted averaging math (`tests/unit/test_strategies.py`).
- [X] T018 [P] [US2] Contract test for `src/retrieval/query.py` output format (`tests/contract/test_schemas.py`).

---


## Phase 5: User Story 3 - Validating Performance via Environment Logic (Priority: P3)

**Goal**: Evaluate synthesized adapters on composite tasks using environment logic, run multiple trials (N≥5), and perform statistical testing with BH correction.

**Independent Test**: System runs evaluation, outputs success/failure logs, and generates a statistical report with p‑values and BH correction.

### Implementation for User Story 3

- [X] T026a1 [US3] Download and convert the base LLM to GGUF format (e.g., TinyLlama‑1B‑Chat, Q4_K_M quantization). Verify size < 7 GB and perform a dry‑run inference to ensure memory fits. (Depends on T004)
- [X] T026f [US3] **Implement** `src/evaluation/verify_memory_footprint.py` to run a dry‑run inference and log memory usage, ensuring compliance with the 7 GB limit. (Depends on T026a1)
- [X] T026b [US3] Implement streaming/chunking logic in `src/evaluation/runner.py` to load the base LLM, apply an adapter, run the task, then unload. Log memory usage and pause if virtual memory > 90 %. (Depends on T026f)
- [X] T025a [US3] **Implement** `src/evaluation/init_env_logic.py` to initialize ALFWorld environment and provide `run_task(adapter_path: str, task_id: str) -> bool`. Include a timeout wrapper (max 30 s) that logs a timeout failure and returns `False`. (Depends on T026a1)
- [X] T026 [US3] **Implement** `src/evaluation/runner.py` (FR-004) to apply adapters (from T022e) to the frozen base LLM and execute environment logic. Use the baseline from `artifacts/baseline_adapter.pt` (verified earlier) or proxy. (Depends on T026a1, T022e, T025a)
- [X] T027 [US3] **Implement** loop in `src/evaluation/runner.py` to execute N ≥ 5 independent runs per task (FR-008) and record binary outcomes, calculating the mean success rate. (Depends on T026)
- [X] T027b [US3] **Verify N>=5**: Check the output of T027 to ensure at least 5 runs were performed per task. If not, halt with error. (Depends on T027)
- [X] T031a [US3] **Implement** `src/evaluation/run_sensitivity_sweep.py` to perform descriptive analysis of sensitivity results for various k values; save plots and a `robustness_score` to `data/results/sensitivity.yaml`. (Depends on T022a)
- [X] T058 [US3] **Implement** `src/evaluation/run_sensitivity_sweep.py` to calculate p‑values for differences between k values using paired t‑test or Wilcoxon (as appropriate). Save raw p‑values to `data/results/sensitivity_raw.json`. (Depends on T031a)
- [X] T058b [US3] **Execute** `src/evaluation/run_sensitivity_sweep.py` (sensitivity sweep) and verify output file `data/results/sensitivity_raw.json`. (Depends on T058)
- [X] T058c [US3] **Apply BH Correction to Sensitivity**: Implement `src/evaluation/stats.py` to apply Benjamini-Hochberg correction to the raw p-values in `data/results/sensitivity_raw.json`. Save corrected values to `data/results/sensitivity_bh_corrected.json`. (Depends on T058b)
- [X] T057 [US3] **Implement** `src/evaluation/stats.py` (FR-005, FR-006) to perform paired t‑test or Wilcoxon signed‑rank test on success rates between each strategy and the baseline. Save raw (uncorrected) p‑values to `data/results/stats_raw.json`. **Schema**: Output must conform to `specs/001-lattentskill-retrieval-geometry/contracts/stats_raw.schema.yaml`. (Depends on T027b, T057a)
- [X] T057b [US3] **Execute** `src/evaluation/stats.py` and verify output file `data/results/stats_raw.json`. (Depends on T057)
- [X] T057a [US3] **Define Stats Raw Schema**: Create `specs/001-lattentskill-retrieval-geometry/contracts/stats_raw.schema.yaml` defining the exact JSON structure for `stats_raw.json` (keys: `comparisons`, `p_values`). (Depends on T007b)
- [X] T057c [US3] **Verify Primary/Sensitivity Separation**: Implement `src/evaluation/stats.py` to validate that the raw p-value sets from T057 and T058 are disjoint and correctly labeled before BH correction. Output a `data/results/bh_separation_check.json` confirming the split. (Depends on T057b, T058b)
- [X] T057d [US3] **Verify BH Corrected Output**: Run a syntax check and schema validation on `data/results/stats_bh_corrected.json` and `data/results/sensitivity_bh_corrected.json` before T032b runs. Ensure the content is valid JSON and matches the expected schema. (Depends on T057c, T058c)
- [X] T075 [US3] **Fix Report Generator Syntax**: Implement `src/evaluation/report_generator.py` to ensure the Benjamini-Hochberg correction logic is correctly implemented and no syntax errors exist. **Action**: Verify the code runs without error and produces valid JSON. (Depends on T032a, T057, T058)
- [X] T032a [US3] **Implement** `src/evaluation/report_schema.py` defining `stats_report.json` schema with fields:
 - `mean_success_rate` (number)
 - `bh_corrected_primary` (object of corrected p‑values)
 - `bh_corrected_sensitivity` (object)
 - `linearity_correlation_coefficient` (number)
 - `reconstruction_error` (object with `mean` and `max`)
 - `memory_footprint` (number, MB)
 - `observed_success_rate_diff` (number, calculated as `mean(strategy_success) - mean(baseline_success)`, rounded to 4 dp)
 - `power_estimate` (number, 0‑1)
 - `bh_rejected_count` (int)
 - `status_linearity` (string: "PASS", "FAIL", "UNTESTABLE")
- [X] T032b [US3] **Implement** `src/evaluation/report_generator.py` to compile all result files into `data/results/stats_report.json`, applying Benjamini‑Hochberg correction separately for primary and sensitivity p-values. **Data Flow**: Read `stats_raw.json` (from T057) and `sensitivity_raw.json` (from T058), apply BH correction to each set of p-values, and write the results to the corresponding fields in `stats_report.json` as defined in T032a. **Logic**: Populate `bh_corrected_primary` from `stats_raw.json` and `bh_corrected_sensitivity` from `sensitivity_raw.json`. (Depends on T032a, T057, T058, T022d, T030a, T030b, T057b, T058b, T057c, T057d, T075)
- [X] T032c [US3] **Execute** `src/evaluation/report_generator.py` and verify `data/results/stats_report.json`. (Depends on T032b)
- [X] T043 [US3] **Revise** `src/evaluation/stats.py` to include a power analysis check using `statsmodels.stats.power.TTestIndPower`. Read `observed_success_rate_diff` from `stats_report.json` (or default effect size 0.3). Assume `alpha=0.05`, desired power 0.8, effect size 0.5 if not available. Log warning if estimated power < 0.8 but continue. Output `power_estimate` into `stats_report.json`. (Depends on T032c)

### Tests for User Story 3

- [X] T024 [P] [US3] Contract test for `src/evaluation/stats.py` output schema (`tests/contract/test_schemas.py`).
- [X] T025 [P] [US3] Integration test for full evaluation loop (`tests/integration/test_pipeline.py`).

---


## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T033a [P] Create `README.md` template with sections: Installation, Usage, Data Sources, Results. (Depends on T032c)
- [X] T033b [P] Populate `README.md` with concrete content, code snippets, and data paths. (Depends on T033a)
- [X] T033c [P] Create `docs/api.md` with function signatures and module descriptions. (Depends on T033b)
- [X] T034 Code cleanup and refactoring of `src/retrieval/strategies.py`
- [X] T036 [P] Additional unit tests for edge cases in `tests/unit/`

---


## Phase 7: Revision - Data Source & Execution Robustness

**Purpose**: Address specific review concerns regarding data source availability, execution failure handling, and memory constraints on the free runner.

- [X] T039 [US1] **Revise** `src/ingestion/download_weights.py` to implement strict streaming/fallback policy using `datasets.load_dataset(..., streaming=True)`. On streaming failure, raise `FileNotFoundError` and write status file; **do NOT** generate synthetic data here. (Depends on T012a, T006b)
- [X] T040 [US3] **Revise** `src/evaluation/runner.py` to enforce strict memory cleanup: call `torch.cuda.empty_cache()` (if applicable), `del adapter, model`, then `gc.collect()`. Pause and warn if `psutil.virtual_memory().percent > 90`. (Depends on T026b, T026f)
- [X] T041 [US3] **Revise** `src/evaluation/init_env_logic.py` to include timeout via `multiprocessing.Process`. Log timeout as failure and return `False`. (Depends on T025a)

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

- [X] T061a [P] **Implement** `src/evaluation/final_report.py` to generate a complete Markdown `reports/final_report.md`. The report must contain:
 1. **Methodology** (sources from `data_sources.yaml`, base model from T026a1)
 2. **Results** table (read from `stats_report.json`)
 3. **Latency** table (read from `latency_metrics.json`)
 4. **Linearity Validation (SC‑005)** section: display PASS/FAIL/UNTESTABLE based on `linearity_valid` and `max_error`.
 5. **Statistical Significance** (BH‑corrected primary and sensitivity p‑values)
 6. **Limitations**: include power analysis result, OOD handling notes, and any warnings from earlier stages.
 The generator must also create a minimal **failure report** if any upstream task aborts, stating which phase failed. (Depends on T032c, T062, T026a1)
- [X] T062 [P] **Implement** `src/utils/plotting.py` to produce static PNG plots for:
 1. Success Rate vs Top‑k
 2. Text‑Weight Pearson Correlation
 3. Latency breakdown (embedding, retrieval, interpolation, baseline)
 Save plots to `reports/plots/`. (Depends on T031a, T030a, T019)
- [X] T063a [P] **Execute** a dry‑run of the full pipeline with N = 1 per task to verify end‑to‑end flow without timeout. Log any errors to `reports/dry_run_log.txt`. (Depends on T061a, T062, T026)
- [X] T064a [P] **Review** `reports/final_report.md` for completeness, correctness, and inclusion of all required SC metrics. Flag missing items; if any critical metric is absent, mark the pipeline as needing revision. (Depends on T063a)

---

## Phase 10: Data Integrity & Pipeline Resilience

**Purpose**: Address critical concerns regarding data integrity during streaming, ensuring the pipeline handles partial failures gracefully without corrupting the index, and verifying the statistical robustness of the final results.

- [X] T069 [US3] **Implement** retry mechanism in `src/evaluation/runner.py` for transient environment failures (max 2 retries with exponential backoff). **Retryable Exceptions**: `ConnectionError`, `TimeoutError`, `NetworkError`. **Non-Retryable**: `AssertionError`, `ValueError`, `RuntimeError`. Do not retry logical failures. (Depends on T026, T041)

---

## Phase 11: Revision - Data Source Verification & Real Data Enforcement

**Purpose**: Address specific review concerns regarding the strict enforcement of real data sources and the prohibition of synthetic fallbacks.

- [X] T073 [US2] **Revise** `src/validation/generate_eval_tasks.py` (T023a) to ensure that if `data/processed/untestable_marker.json` is written, the pipeline does NOT proceed to synthesis (T022e) or evaluation (T026) with synthetic weights. The runner must detect this marker and skip the specific task, logging "SKIPPED: Missing Ground Truth" rather than generating a fake result. (Depends on T023a, T022e)
- [X] T074 [US1] **Update** `data_sources.yaml` to include explicit verification commands for each source (e.g., `huggingface-cli download...` or `curl -I...`) and ensure `src/validate/citation_check.py` (T006) executes these commands and fails the build if any source is unreachable, rather than marking them as "verified" based on URL syntax alone. (Depends on T006a, T006)

---

## Phase 12: Final Statistical Robustness & Reporting Completeness

**Purpose**: Ensure all statistical tests handle edge cases correctly and the final report is comprehensive, addressing the specific concerns about power analysis and zero-variance handling.

- [X] T075 [US3] **Implement** a comprehensive edge-case handler in `src/evaluation/stats.py` that:
 1. Detects zero-variance groups in success rates and logs a specific warning `stats_zero_variance_warning.log`.
 2. Skips the statistical test for that specific comparison and records `p_value: null` in `stats_raw.json`.
 3. Ensures the Benjamini-Hochberg correction logic in `report_generator.py` (T032b) correctly filters out `null` values before calculating FDR.
 4. Updates `stats_report.json` to include a `warnings` array listing all skipped tests and reasons. (Depends on T050, T057, T032c)
- [X] T076 [US3] **Execute** `src/evaluation/stats.py` with a synthetic zero-variance test case to verify the warning and null handling logic works as expected before the main pipeline run. (Depends on T075)
- [X] T077 [US3] **Finalize** `reports/final_report.md` generation in `src/evaluation/final_report.py` to explicitly include:
 1. A "Statistical Power" section detailing the `power_estimate` and whether it meets the 0.8 threshold, with a "Limitations" note if it does not.
 2. A "Zero-Variance Incidents" section listing any tasks or comparisons where statistical testing was skipped due to lack of variance, explaining the impact on the overall conclusion.
 3. A "Data Integrity" section confirming the absence of synthetic data and listing all real sources used with their verification status. (Depends on T075, T076, T061a)

---

## Phase 13: Final Execution & Verification

**Purpose**: Execute the final pipeline run with all safeguards and verify the output against the specification requirements.

- [ ] T078 [US3] **Execute** the full pipeline end-to-end using the `cli.py` entry point with `N=5` runs per task. Ensure all previous tasks (T001-T077) are completed and passing. (Depends on T077, T063a)
- [ ] T079 [US3] **Verify** `data/results/stats_report.json` contains all required fields, including `linearity_valid`, `power_estimate`, and `warnings` array. (Depends on T078)
- [ ] T080 [US3] **Validate** `reports/final_report.md` for completeness, ensuring it includes the "Statistical Power", "Zero-Variance Incidents", and "Data Integrity" sections as mandated by T077. (Depends on T079)
- [ ] T081 [US3] **Run** `tests/integration/test_pipeline.py` to confirm the entire pipeline (ingestion -> retrieval -> evaluation -> stats) executes correctly on the CPU-only runner. (Depends on T078)
- [ ] T082 [P] **Audit** `data/raw/` and `data/processed/` for any accidental synthetic data files or placeholders. Confirm all data originates from the verified sources in `data_sources.yaml`. (Depends on T078)
- [ ] T083 [P] **Finalize** `README.md` with the actual results from the final run, including the `stats_report.json` summary and links to generated plots. (Depends on T080)