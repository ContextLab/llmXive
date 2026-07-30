# Tasks: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

**Input**: Design documents from `/specs/001-entropy-validity-prediction/`
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

- [ ] T001 [P] Create root project directory structure: Create `setup.sh` containing explicit `mkdir -p` commands for `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/`, `tests/`, `data/`, `docs/`, `scripts/`, `results/`, `specs/001-entropy-validity-prediction/contracts/`, and subdirectories `src/`, `data/raw/`, `data/processed/`, `artifacts/`, `state/`. The script must verify all paths exist, exit with code 1 if any are missing, and generate `project_structure.log` containing a JSON list of absolute paths. **Deliverable**: `setup.sh` and `project_structure.log`.
- [ ] T002 [P] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/requirements.txt` pinning versions for `transformers`, `torch`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `h5py`, `pytest`, `statsmodels`, `psutil`, `huggingface_hub`. **CRITICAL**: Must include a 1.5B parameter model compatible with CPU (e.g., `Qwen1.5-1.5B` or equivalent). **Deliverable**: Valid `requirements.txt` file.
- [ ] T003 [P] Configure linting (ruff) and formatting tools: Create `pyproject.toml` with black/ruff config, `.ruff.toml` for linter rules, and `.black.toml` for formatter settings. **Deliverable**: These three config files must exist and be valid.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/entropy_calc.py` with Shannon entropy logic ($-\sum p_i \log p_i$). **Input**: The function `calculate_entropy(probs)` MUST accept **softmax-normalized probability distributions (tensor)** of shape `[batch, vocab_size]` or `[vocab_size]` on **CPU**, clamp probability values < 1e-9 to 1e-9 *before* taking the logarithm to prevent log(0) errors, and return a float. **Semantic Test**: The function MUST correctly handle near-zero probability inputs by returning a finite value without crashing. **Deliverable**: Create `src/utils/entropy_calc.py` with function `calculate_entropy(probs)` and unit test `tests/unit/test_entropy_calc.py::test_clamp_prevents_log_zero` asserting the function returns a finite value for input probabilities resulting in p=0.0.
- [ ] T005 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/validators.py` for schema validation (TokenSequence, EntropyProfile, ValidityLabel). **Deliverable**: `src/utils/validators.py` with validation functions.
- [ ] T006 [P] [US1/US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` with batched streaming infrastructure. MUST implement `stream_batch` function to handle dataset loading in chunks. The `stream_batch` function MUST define a trigger condition for memory backoff: "if a MemoryError is raised". **CRITICAL**: This task MUST implement the logic to process dataset **examples** in batches of **500 examples** as required by FR-001, slicing the dataset and validating each chunk before proceeding. **Fallback Logic**: If a MemoryError is raised, the batch size MUST be halved. [UNRESOLVED-CLAIM: c_b90a2c86 — status=not_enough_info] If the batch size drops below a minimal threshold, raise a RuntimeError. **Note**: This task handles the 500-example dataset cap ONLY. The 50-token batching for inference is handled in T021. **Deliverable**: `src/data/preprocessing.py` with `stream_batch` function (including 500-example batching) and `tests/integration/test_preprocessing.py::test_memory_backoff` verifying the fallback.
- [ ] T007 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` to fetch GSM8K and MiniGrid from HuggingFace Datasets with a representative subset limit. **CRITICAL**: This task MUST enforce the **500-example cap per task** (GSM8K and MiniGrid) as required by FR-001. **Constraint**: MUST NOT use `try/except` blocks that fall back to `generate_synthetic_*()` or `mock_*()` data. If `datasets.load_dataset` fails, the script MUST raise a `ConnectionError` or `FileNotFoundError` immediately to let the run fail loudly. **Deliverable**: `src/data/download.py` with no synthetic fallbacks and explicit 500-example capping.
- [ ] T008 [P] [US1/US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/.env.example` with keys for `HF_TOKEN`, `DATA_PATH`, `MODEL_PATH` and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/config.py` to load them. **Deliverable**: `.env.example` and `src/config.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Generation and Ground Truth Labeling (Priority: P1) 🎯 MVP

**Goal**: Generate ground-truth token sequences for GSM8K and MiniGrid using a CPU-tractable model and label them with validity flags.

**Independent Test**: Run baseline generation on a subset of GSM8K problems; verify output log contains complete token sequences and binary validity flags against known solutions.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` baseline generation logic. **MUST** perform a **full autoregressive forward pass** with `temperature=0.0` to ensure deterministic generation using a **1.5B parameter model** (e.g., Qwen1.5-1.5B) as per FR-002. **Deliverable**: `src/generation/generation.py` with `generate_baseline` function. <!-- ATOMIZE: requested -->
- [ ] T012 [US1] Implement ground truth matching logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py`. **MUST** label validity by **deterministic comparison** against the ground-truth solution. **Specifics**: For GSM8K, validity is determined by exact match with the dataset solution string. [UNRESOLVED-CLAIM: c_daddbacd — status=not_enough_info] For MiniGrid, validity is determined by exact match with **any of the known valid ground-truth paths** (e.g., from `minigrid` solver or pre-computed file) as required by the Spec's Edge Cases. **Input**: Read from raw generation output `data/raw_generation.jsonl`. **Output**: Write validity labels to `data/validity_labels.jsonl`. **Deliverable**: `src/generation/generation.py` with `label_validity` function.
- [ ] T013 [US1] Create output writer for JSONL format in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` (TokenSequence, ValidityLabel). **Deliverable**: `src/generation/generation.py` with `write_jsonl` function.
- [ ] T014 [US1] Implement exception handling in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` for cases where no ground-truth path matches: **DO NOT** flag as 'ambiguous'. Instead, implement logic to label a token as "valid" if it matches *any* of the known valid ground-truth paths. If no match is found after checking all paths, log a warning to `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/logs/generation.log` with JSON format `{"prompt_id": "...", "reason": "no_match", "validity": false}`. **Log level**: WARNING. **Rotation**: maxBytes=10MB. **Error handling**: raise RuntimeError if log file is locked. **Deliverable**: `src/generation/generation.py` with `label_validity` updated and logging verified.
- [ ] T015 [US1] Configure `logging` in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to output JSON-formatted logs to `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/logs/generation.log` including **the complete sequence of tokens and a binary validity flag for each token position**. **Deliverable**: `logs/generation.log` with JSON entries.
- [ ] T016 [US1] Implement merging logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to combine generation outputs (T011) with ground truth labels (T012) into a single **intermediate dataset (US1 only)**. **Function Signature**: `merge_outputs(generation_data, label_data, join_keys=['prompt_id', 'token_index'])`. **Join Logic**: Align on `prompt_id` and `token_index` (0-based). Handle variable sequence lengths by aligning on these keys. **MUST** also handle merging of generation chunks (from T011) before final merge. **Input**: `data/raw_generation.jsonl` (chunks) and `data/validity_labels.jsonl`. **Output**: `data/merged_us1.jsonl`. **Deliverable**: Output file `data/merged_us1.jsonl` validating against `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/dataset.schema.yaml`. **Depends on T011, T012, T013, T014, T015**.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Contract test for dataset schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_dataset_schema.py`. **Deliverable**: `tests/contract/test_dataset_schema.py::test_schema_validation_fails_on_missing_field` that loads `contracts/dataset.schema.yaml` and asserts `ValueError` is raised for a record missing the `validity` field. **Depends on T005**.
- [ ] T010 [US1] Integration test for ground truth labeling in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_ground_truth_labeling.py`. **Deliverable**: `tests/integration/test_ground_truth_labeling.py` verifying multi-path matching. **Depends on T016** (Output Writer/Merging).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Intermediate State Extraction and Entropy Calculation (Priority: P2)

**Goal**: Re-run baseline sequences with instrumentation to capture probability distributions and calculate Shannon entropy at every intermediate layer.

**Independent Test**: Re-run a subset of sequences with instrumentation; verify output log contains entropy values for every layer and token position with no missing values.

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` hooks to capture layer-wise probability distributions. **Deliverable**: `src/generation/generation.py` with forward hooks.
- [ ] T020 [US2] Integrate `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/entropy_calc.py` to compute entropy vectors for each token position. **Implementation Detail**: Register a forward hook in `generation.py` that captures the output of each intermediate layer, passes the logits to `entropy_calc.calculate_entropy()` (after softmax normalization), and stores the result in the token's metadata. **Deliverable**: `src/generation/generation.py` updated.
- [ ] T021 [US2] Implement streaming/chunking logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to process **fixed-size token batches of 50 tokens** (for memory safety during entropy extraction) and **write to disk immediately after each batch** to stay within 7GB RAM limit. **CRITICAL**: This task MUST implement a **dedicated 50-token batching loop** independent of T006's 500-example batching logic. **File Format**: JSONL. **Naming Convention**: `temp_entropy_batch_{batch_id:04d}.jsonl` where `batch_id` is a **zero-padded sequential integer**. **Directory**: `data/processed/temp_batches/`. **Schema**: Each record MUST contain `prompt_id`, `token_index`, and `layer_entropy_map` (dict of layer_id: entropy_value). **CRITICAL**: This task MUST **explicitly compute and record SHA-256 checksums** for every temporary batch file in a **temporary manifest** `state/temp_batch_manifests.json` (not the main state YAML) to avoid conflicts with T046. **CRITICAL**: This task MUST **strictly output temporary batch files** and MUST **NOT** perform the final merge; the merge is the **sole responsibility of T022**. **Note**: This task implements the 50-token internal batch constraint (FR-007) specifically for the entropy extraction step. Dataset row capping is handled in T007. **CRITICAL**: This task MUST handle **full sequences up to 512 tokens** in length, processing them in 50-token chunks. **Deliverable**: `src/generation/generation.py` with `process_batch` function and `tests/integration/test_entropy_extraction.py::test_50_token_batching` verifying the batching logic. **Depends on T016, T019, T020**.
- [ ] T022 [US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` logic to merge entropy profiles (from T021 temp batches) with the labeled dataset (from T016) into a single EntropyProfile record. **CRITICAL**: This task MUST perform a **3-way join** using `prompt_id` and `token_index` as keys: (1) `data/merged_us1.jsonl` (T016), (2) `data/processed/temp_batches/temp_entropy_batch_*.jsonl` (T021), and (3) the original US1 context (from T015b logic, now merged into T016). **CRITICAL**: This task is the **sole owner** of the final merge logic for the artifact `data/entropy_profiles_merged.jsonl`. **Deliverable**: Output file `data/entropy_profiles_merged.jsonl` validating against `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/entropy_profile.schema.yaml` and mandating preservation of layer-wise granularity. **Note: This task requires US1 (T016) and US2 (T021) to be complete. Explicitly depends on T016 and T021.**
- [ ] T023 [US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` function `validate_entropy_profile()` that references `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/entropy_profile.schema.yaml` and raises ValueError if any layer/token in an EntropyProfile record is None or missing entropy values. **Deliverable**: On success, write `results/validation_report.json` with summary stats; on failure, exit with code 1. **Note**: This is the canonical implementation of `validate_entropy_profile`; T006 only creates the file infrastructure. **Depends on T022.**
- [ ] T035 [P] [US2] Profile `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` using `cProfile` and verify RAM usage stays < 6.5GB for sequences up to **512 tokens** processed in batches of 50 tokens. **Deliverable**: Run `cProfile` on `src/generation/generation.py` with 512-token sequences, extract peak RSS using `tracemalloc`, and write `results/profile_report.txt` containing a **Markdown table** of `['Batch Size', 'Peak RSS (MB)', 'Avg Latency (s)']`. **Note**: This is a verification step integrated into T021 implementation. **Depends on T021**.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for entropy profile schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_entropy_profile_schema.py`.
- [ ] T018 [P] [US2] Integration test for intermediate state extraction in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_entropy_extraction.py`.

**Checkpoint**: At this point, At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Signal Decay Analysis and Threshold Optimization (Priority: P3)

**Goal**: Fit logistic regression models to predict token validity from entropy values and identify optimal entropy thresholds.

**Independent Test**: Run analysis on combined dataset; verify logistic regression fit, AUC-ROC calculation, p-value reporting, and threshold optimization.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` using `statsmodels` for **Mixed-Effects Logistic Regression (GLMM)** to predict token validity from entropy values, stratified by task type (GSM8K vs MiniGrid), and using random intercepts for sequences to handle nested data. **CRITICAL**: The implementation MUST handle **layer index as a continuous covariate** (not just pooling) as required by FR-004. **Deliverable**: `src/analysis/logistic_model.py` with `fit_model` function that returns coefficients, p-values, and AUC-ROC.
- [ ] T027 [US3] Implement stratification logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` (GSM8K vs MiniGrid, early/mid/late layer pooling or continuous covariate). **Deliverable**: `src/analysis/logistic_model.py` with stratification support.
- [ ] T028 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/threshold_opt.py` to find optimal entropy threshold minimizing weighted false positive/negative sum. **Deliverable**: `src/analysis/threshold_opt.py` with `optimize_threshold` function.
- [ ] T029 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/sensitivity.py` to first **apply multiple-comparison correction (Bonferroni OR Benjamini-Hochberg)** to p-values derived from the model fitting process (T026), then **calculate the resulting False Discovery Rate (FDR) and measure it against the nominal alpha level to report validity**. **Requirement**: The task MUST NOT enforce a hard pass/fail gate; non-significant results (FDR > alpha) are valid empirical outcomes and must be recorded with a `significant` flag set to False. **Requirement**: MUST accept a `--correction-method` CLI argument (choices: `bonferroni`, `benjamini-hochberg`) to select the method, with **`bonferroni` as the default** to satisfy FR-006's FWER requirement. **Requirement**: The task MUST **fail loudly (raise RuntimeError)** if the input data is empty, contains only one class, or if the correction logic fails (e.g., NaN generation), distinguishing this from a valid non-significant result. **Input**: List of p-values from T026. **Output**: `results/fdr_report.json` with schema `{'adjusted_p_values': [...], 'fdr': float, 'alpha': 0.05, 'significant': bool}`. **CRITICAL**: This task MUST **also perform the sensitivity analysis sweep** across a range of entropy thresholds (e.g., $\in \{0.05, 0.1\}$ around the optimal point) and **explicitly link the sweep results to the corrected p-values** to determine the optimal threshold under the corrected significance level (SC-003). **Deliverable**: `src/analysis/sensitivity.py` with `apply_correction` and `perform_sweep` functions. **Depends on T026**.
- [ ] T030 [US3] Implement logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` to catch p >= 0.05, log a warning, and return a result object with `significant=False` instead of crashing. **Deliverable**: Robust handling in `logistic_model.py`.
- [ ] T047 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/decay_analysis.py` to split the dataset into "short" (sequence length <= 100 tokens) and "long" (sequence length > 100 tokens) subsets. **Requirement**: The task MUST ALSO stratify by **task type (GSM8K vs MiniGrid)** and calculate/compute AUC-ROC for both subsets and both task types to measure decay of predictive power (SC-004). **Requirement**: The task MUST **fail loudly (raise RuntimeError)** if the input dataset is empty, if either subset has zero samples, or if AUC calculation fails (e.g., NaN), distinguishing this from a valid result. **Deliverable**: `results/decay_analysis.json` containing AUC-ROC for short/long subsets, task types, and the difference metric. **Depends on T026**.
- [ ] T046 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/checksum_recorder.py` to generate local checksums for all files in `data/` and record them in `state/projects/PROJ-881-llmxive-follow-up-extending-efficientrol.yaml` under `artifact_hashes`. **Schema**: `artifact_hashes` is a flat map of `relative_path: sha256_hash`. **CRITICAL**: This task MUST **checksum the final merged artifact** (`data/entropy_profiles_merged.jsonl` from T022) and **aggregate** checksums from `state/temp_batch_manifests.json` (generated by T021) into the final state file, ensuring all temporary batches are included. **Requirement**: The script MUST update the `updated_at` timestamp in `state/projects/PROJ-881-llmxive-follow-up-extending-efficientrol.yaml` immediately after recording checksums to satisfy Constitution Principle V. **Timestamp Format**: ISO 8601. **Deliverable**: `scripts/checksum_recorder.py` and updated `state/...yaml`. **Depends on T021, T022**.
- [ ] T031 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/report.py` to write `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/results/final_report.json` containing AUC-ROC, p-values, the recommended threshold from `threshold_opt.py`, the **FDR metric** from `sensitivity.py`, the **sensitivity sweep metrics** from `sensitivity.py` (T029), and the **decay analysis metrics** from `decay_analysis.py` (SC-004). **Requirement**: MUST check for existence of `results/fdr_report.json`, `results/sensitivity_sweep.json`, and `results/decay_analysis.json`. **Requirement**: MUST validate that these files contain **non-null, non-empty metric fields** (e.g., `fdr` is a number, `auc_short` is a number). If files are missing OR contain invalid/empty metrics, **raise a RuntimeError** (fail loudly) to prevent incomplete reports. **Requirement**: If files exist but contain valid non-significant results (e.g., `significant: false`), the task MUST **accept them** and include them in the report. **Requirement**: MUST include a "Data Provenance" section with checksums from T046. **Deliverable**: `results/final_report.json` must contain all metrics required by SC-001 through SC-005. **Depends on T029, T047, T046**.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for analysis result schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_analysis_result_schema.py`.
- [ ] T025 [P] [US3] Integration test for threshold optimization in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_threshold_optimization.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Update `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/README.md` with CLI usage examples.
- [ ] T033 [P] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/docs/api.md` with docstrings for `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py`.
- [ ] T034 [P] Run `ruff check --fix` and `black.` on the entire `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/` directory and resolve all linting errors.
- [ ] T036 [P] Add unit tests in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/unit/test_entropy_calc.py` covering edge cases (log(0), empty input) and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/unit/test_validators.py` for schema validation.
- [ ] T037 [P] Implement input validation in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` to reject non-HuggingFace URLs and add a PII scan script `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/pii_scan.py` that checks `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/data/` for regex patterns. **Requirement**: The script MUST **redact or remove** any PII found before the run completes. **Deliverable**: `scripts/pii_scan.py` must exit 0 if no PII found or after redaction, exit 1 if redaction fails, and must log the specific regex patterns used to ensure verifiability.
- [ ] T038 [P] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/main.py` orchestration script with CLI arguments `--dataset`, `--model`, `--seed` and logic to call download, generation, and analysis modules sequentially.
- [ ] T039 [P] Execute `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_quickstart.sh` to ensure all commands in `quickstart.md` run successfully in a fresh virtualenv.

---

## Phase 7: Data Integrity & Execution Safety (Revision Pass)

**Goal**: Address specific review concerns regarding data sourcing, streaming, and failure modes to prevent fabrication and ensure reproducibility.

- [ ] T040 [P] [US1/US2] Refactor `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` to remove ALL `try/except` blocks that fall back to `generate_synthetic_*()` or `mock_*()` data. If `datasets.load_dataset` or `hf_hub_download` fails, the script MUST raise a `ConnectionError` or `FileNotFoundError` immediately to let the run fail loudly. **Deliverable**: `src/data/download.py` with no fallbacks and `tests/unit/test_download.py::test_fail_loudly_on_network_error` asserting `ConnectionError` is raised when HuggingFace is unreachable.
- [ ] T044 [P] [US3] Add a verification step in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_data_integrity.py` that compares the SHA-256 checksum of the downloaded dataset file against the hash recorded in `data/.checksums` (generated by T046), raising an error if they mismatch. **Note**: Do NOT attempt to fetch a dynamic "HuggingFace info hash" from the API; rely on the local manifest. **Deliverable**: `scripts/validate_data_integrity.py`.
- [ ] T045 [P] [US3] Update `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/report.py` to include a "Data Provenance" section in `results/final_report.json` that lists the exact dataset version, sample size, streaming parameters, and **checksums from T046**, ensuring traceability from result back to raw data. **Requirement**: MUST depend on T046. **Deliverable**: `results/final_report.json` with Data Provenance section.
- [ ] T042 [US2] Add a `--sample-size` CLI argument to `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/main.py` that, if provided, uses `itertools.islice` to take a deterministic random sample from the streamed dataset, explicitly logging the sample size and seed in `results/final_report.json`. **Constraint**: The effective sample size MUST be `min(user_input, 500)` to enforce FR-001. **Deliverable**: `main.py` with `--sample-size` argument enforcing cap.
- [ ] T043 [P] [US3] Modify `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` to explicitly check for and handle the case where the input dataset contains zero valid tokens or zero invalid tokens (perfect separation), logging a warning and skipping the logistic regression fit rather than crashing or returning NaNs. **Deliverable**: Robust handling in `logistic_model.py`.

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
- Models/Utilities before services
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
# Launch all models for User Story 1 together:
Task: "Implement baseline generation logic in src/generation/generation.py"
Task: "Implement ground truth matching logic in src/generation/generation.py"
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