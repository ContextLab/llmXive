# Tasks: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

**Input**: Design documents from `/specs/001-entropy-validity-prediction/`
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

## Phase 0: Research & Design

**Purpose**: Define core logic and model selection as per plan.md Phase 0

- [ ] T001 [P] [US1] Define Semantic Alignment logic for GSM8K/MiniGrid. **Deliverable**: Document `specs/001-entropy-validity-prediction/contracts/semantic_alignment.md` describing the logic for matching generated tokens to ground truth paths. **CRITICAL**: This task MUST also generate `data/ground_truth_paths.jsonl` containing a list of valid path strings for each `prompt_id` (or a mapping to a static file) to be used by T017. **Deliverable**: `contracts/semantic_alignment.md` AND `data/ground_truth_paths.jsonl` (or a script to generate it).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T004a [P] Create root project directory structure (Creation): Create `setup.sh` containing explicit `mkdir -p` commands for `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/`, `tests/`, `data/`, `docs/`, `scripts/`, `results/`, `specs/001-entropy-validity-prediction/contracts/`, and subdirectories `src/`, `data/raw/`, `data/processed/`, `artifacts/`, `state/`. **Deliverable**: `setup.sh` that creates all paths.
- [ ] T004b [P] Create root project directory structure (Verification): Create `scripts/verify_structure.py` that verifies all paths from T004a exist, exits with code 1 if any are missing, and generates `project_structure.log` containing a JSON list of absolute paths in the format `{'paths': [{'path': str, 'exists': bool}]}`. **Deliverable**: `scripts/verify_structure.py` and `project_structure.log`.
- [ ] T005 [P] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/requirements.txt` pinning versions for `transformers`, `torch`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `h5py`, `pytest`, `statsmodels`, `psutil`, `huggingface_hub`. **CRITICAL**: Must include Qwen1.5-0.5B model compatibility. **Deliverable**: Valid `requirements.txt` file.
- [ ] T006 [P] Configure linting (ruff) and formatting tools: Create `pyproject.toml` with black/ruff config, `.ruff.toml` for linter rules, and `.black.toml` for formatter settings. **Deliverable**: These three config files must exist and be valid.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/entropy_calc.py` with Shannon entropy logic ($-\sum p_i \log p_i$). **Input**: The function `calculate_entropy(probs)` MUST accept **softmax-normalized probability distributions (tensor)** of shape `[batch, vocab_size]` or `[vocab_size]` on **CPU**, clamp probability values < 1e-9 to 1e-9 *before* taking the logarithm to prevent log(0) errors, and return a float. **Semantic Test**: The function MUST correctly handle near-zero probability inputs by returning a finite value without crashing. **Deliverable**: Create `src/utils/entropy_calc.py` with function `calculate_entropy(probs)` and unit test `tests/unit/test_entropy_calc.py::test_clamp_prevents_log_zero` asserting the function returns a finite value for input probabilities resulting in p=0.0.
- [ ] T008 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/validators.py` for schema validation (TokenSequence, EntropyProfile, ValidityLabel). **Deliverable**: `src/utils/validators.py` with validation functions.
- [ ] T009a [P] [US1/US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` with dataset capping infrastructure. MUST implement `stream_batch` function to handle dataset loading in chunks. **CRITICAL**: This task MUST implement the logic to process dataset **examples** in batches of **500 examples** as required by FR-001. **Fallback Logic**: If a MemoryError is raised within the generator loop, the batch size MUST be halved. If the batch size drops below a minimal threshold, raise a RuntimeError. **Note**: This task handles the 500-example dataset cap ONLY. The 50-token batching for inference is handled in T009b. **Deliverable**: `src/data/preprocessing.py` with `stream_batch` function (including 500-example batching) and `tests/integration/test_preprocessing.py::test_memory_backoff` verifying the fallback.
- [ ] T009b [P] [US1/US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` with **token-level batching** infrastructure. MUST implement `token_batch_stream` function. **CRITICAL**: This task MUST implement the logic to process sequences in **batches of 50 tokens** as required by FR-007. **Initial Batch Size**: 50 tokens. **Fallback Logic**: If a MemoryError is raised, the batch size MUST be halved (50 -> 25 -> 12). **Minimal Threshold**: If the batch size drops below 8 tokens, raise a `RuntimeError` with message "Batch size too small". **Deliverable**: `src/data/preprocessing.py` with `token_batch_stream` function and `tests/integration/test_token_batching.py::test_fallback_logic` verifying the halving and threshold logic.
- [ ] T010 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` to fetch GSM8K and MiniGrid from HuggingFace Datasets. **CRITICAL**: This task MUST enforce the **500-example cap per task** (GSM8K and MiniGrid) as required by FR-001 by default using `itertools.islice` within the streaming logic. **Constraint**: MUST NOT use `try/except` blocks that fall back to `generate_synthetic_*()` or `mock_*()` data. If `datasets.load_dataset` fails, the script MUST raise a `ConnectionError` or `FileNotFoundError` immediately to let the run fail loudly. **Deliverable**: `src/data/download.py` with no synthetic fallbacks and explicit 500-example capping logic.
- [ ] T011 [P] [US1/US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/.env.example` with keys for `HF_TOKEN`, `DATA_PATH`, `MODEL_PATH` and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/config.py` to load them. **Deliverable**: `.env.example` and `src/config.py`.
- [ ] T012 [P] [US1/US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/dataset.schema.yaml` defining the schema for the merged dataset used in T016. **Deliverable**: `contracts/dataset.schema.yaml`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Generation and Ground Truth Labeling (Priority: P1) 🎯 MVP

**Goal**: Generate ground-truth token sequences for GSM8K and MiniGrid using a CPU-tractable model and label them with validity flags.

**Independent Test**: Run baseline generation on a subset of GSM8K problems; verify output log contains complete token sequences and binary validity flags against known solutions.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` model loading logic. **MUST** load **Qwen1.5-0.5B** model as per plan.md Technical Context and FR-002. **Deliverable**: `src/generation/generation.py` with `load_model` function.
- [ ] T014 [US1] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` baseline generation loop. **MUST** perform a **full autoregressive forward pass** with `temperature=0.0` using the loaded Qwen1.5-0.5B model. **Deliverable**: `src/generation/generation.py` with `generate_baseline` function.
- [ ] T015 [US1] Implement ground truth matching logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py`. **MUST** label validity by **deterministic comparison** against the ground-truth solution using the **Semantic Alignment logic** defined in T001. **Specifics**: For GSM8K, validity is determined by exact match with the dataset solution string. For MiniGrid, validity is determined by exact match with **any of the known valid ground-truth paths** (from `data/ground_truth_paths.jsonl` generated by T001). **Input**: Read from raw generation output `data/raw_generation.jsonl`. **Output**: Write validity labels to `data/validity_labels.jsonl`. **Deliverable**: `src/generation/generation.py` with `label_validity` function.
- [ ] T016 [US1] Create output writer for JSONL format in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` (TokenSequence, ValidityLabel). **Deliverable**: `src/generation/generation.py` with `write_jsonl` function.
- [ ] T017 [US1] Implement exception handling in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` for cases where no ground-truth path matches: **DO NOT** flag as 'ambiguous'. Instead, implement logic to label a token as "valid" if it matches *any* of the known valid ground-truth paths in `data/ground_truth_paths.jsonl`. **CRITICAL**: The logic MUST iterate through ALL known valid paths for the specific `prompt_id`. If a match is found with *any* path, the token is marked "valid". Only if *no* path matches after checking all options should the token be marked "invalid" and a warning logged to `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/logs/generation.log` with JSON format `{"prompt_id": "...", "reason": "no_match", "validity": false}`. **Log level**: WARNING. **Rotation**: Use `RotatingFileHandler` with `maxBytes=10MB` and path `logs/generation.log`. **Error handling**: raise RuntimeError if log file is locked. **Deliverable**: `src/generation/generation.py` with `label_validity` updated and logging verified. **Depends on T001**.
- [ ] T018 [US1] Configure `logging` in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to output JSON-formatted logs to `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/logs/generation.log` including **the complete sequence of tokens and a binary validity flag for each token position**. **Deliverable**: `logs/generation.log` with JSON entries.
- [ ] T019 [US1] Implement merging logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to combine generation outputs (T014) with ground truth labels (T015) into a single **intermediate dataset (US1 only)**. **Function Signature**: `merge_outputs(generation_data, label_data, join_keys=['prompt_id', 'token_index'])`. **Join Logic**: Align on `prompt_id` and `token_index` (0-based). Handle variable sequence lengths by aligning on these keys. **MUST** also handle merging of generation chunks (from T014) before final merge. **Input**: `data/raw_generation.jsonl` (chunks) and `data/validity_labels.jsonl`. **Output**: `data/merged_us1.jsonl`. **Deliverable**: Output file `data/merged_us1.jsonl` validating against `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/dataset.schema.yaml`. **Depends on T013, T014, T015, T016, T017, T018**.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US1] Contract test for dataset schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_dataset_schema.py`. **Deliverable**: `tests/contract/test_dataset_schema.py::test_schema_validation_fails_on_missing_field` that loads `contracts/dataset.schema.yaml` and asserts `ValueError` is raised for a record missing the `validity` field. **Depends on T012**.
- [ ] T021 [US1] Integration test for ground truth labeling in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_ground_truth_labeling.py`. **Deliverable**: `tests/integration/test_ground_truth_labeling.py` verifying multi-path matching. **Depends on T019** (Output Writer/Merging).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Intermediate State Extraction and Entropy Calculation (Priority: P2)

**Goal**: Re-run baseline sequences with instrumentation to capture probability distributions and calculate Shannon entropy at every intermediate layer.

**Independent Test**: Re-run a subset of sequences with instrumentation; verify output log contains entropy values for every layer and token position with no missing values.

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` hooks to capture layer-wise probability distributions. **Deliverable**: `src/generation/generation.py` with forward hooks.
- [ ] T023 [US2] Integrate `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/entropy_calc.py` to compute entropy vectors for each token position. **Implementation Detail**: Register a forward hook in `generation.py` that captures the output of each intermediate layer, passes the logits to `entropy_calc.calculate_entropy()` (after softmax normalization), and stores the result in the token's metadata. **Deliverable**: `src/generation/generation.py` updated.
- [ ] T024 [US2] Implement streaming/chunking logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to process sequences using **single-sequence streaming** (as per plan.md) with an internal **50-token batching loop** for memory safety during entropy extraction. **CRITICAL**: This task MUST implement a **dedicated 50-token batching loop** independent of T009b's logic, processing sequences **one at a time** and writing to disk immediately after each batch to stay within 7GB RAM limit. **Input**: MUST read from `data/merged_us1.jsonl` (output of T019). **File Format**: JSONL. **Naming Convention**: `temp_entropy_batch_{batch_id:04d}.jsonl` where `batch_id` is a **zero-padded sequential integer**. **Directory**: `data/processed/temp_batches/`. **Schema**: Each record MUST contain `prompt_id`, `token_index`, and `layer_entropy_map` (dict of layer_id: entropy_value). **CRITICAL**: This task MUST **strictly output temporary batch files** and MUST **NOT** perform the final merge; the merge is the **sole responsibility of T025**. **Note**: This task implements the 50-token internal batch constraint (FR-007) specifically for the entropy extraction step. Dataset row capping is handled in T010. **CRITICAL**: This task MUST handle **full sequences up to 512 tokens** in length, processing them in 50-token chunks. **Deliverable**: `src/generation/generation.py` with `process_batch` function and `tests/integration/test_entropy_extraction.py::test_50_token_batching` verifying the batching logic. **Depends on T019, T022, T023**.
- [ ] T025 [P] [US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` logic to merge entropy profiles (from T024 temp batches) with the labeled dataset (from T019) into a single EntropyProfile record. **CRITICAL**: This task MUST perform a **3-way join** using `prompt_id` and `token_index` as keys: (1) `data/merged_us1.jsonl` (T019), (2) `data/processed/temp_batches/temp_entropy_batch_*.jsonl` (T024), and (3) the original US1 context. **CRITICAL**: This task is the **sole owner** of the final merge logic for the artifact `data/entropy_profiles_merged.jsonl`. **CRITICAL**: This task MUST run **after all T024 instances complete**. **Deliverable**: Output file `data/entropy_profiles_merged.jsonl` validating against `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/entropy_profile.schema.yaml` and mandating preservation of layer-wise granularity. **Note: This task requires US1 (T019) and US2 (T024) to be complete. Explicitly depends on T019 and T024.**
- [ ] T025b [P] [US2] Implement cleanup logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` to delete `data/processed/temp_batches/` files after successful merge in T025. **Deliverable**: `src/data/preprocessing.py` with `cleanup_temp_batches` function.
- [ ] T026 [US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` function `validate_entropy_profile()` that references `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/entropy_profile.schema.yaml` and raises ValueError if any layer/token in an EntropyProfile record is None or missing entropy values. **Deliverable**: On success, write `results/validation_report.json` with summary stats; on failure, exit with code 1. **Note**: This is the canonical implementation of `validate_entropy_profile`; T009 only creates the file infrastructure. **Depends on T025.**
- [ ] T027 [P] [US2] Profile `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` using `cProfile` and verify RAM usage stays < 6.5GB for sequences up to **512 tokens** processed in batches of 50 tokens. **Deliverable**: Run `cProfile` on `src/generation/generation.py` with 512-token sequences, extract peak RSS using `tracemalloc`, and write `results/profile_report.txt` containing a **Markdown table** of `['Batch Size', 'Peak RSS (MB)', 'Avg Latency (s)']`. **Note**: This is a verification step integrated into T024 implementation. **Depends on T024**.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US2] Contract test for entropy profile schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_entropy_profile_schema.py`.
- [ ] T029 [P] [US2] Integration test for intermediate state extraction in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_entropy_extraction.py`.

**Checkpoint**: At this point, At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Signal Decay Analysis and Threshold Optimization (Priority: P3)

**Goal**: Fit logistic regression models to predict token validity from entropy values and identify optimal entropy thresholds.

**Independent Test**: Run analysis on combined dataset; verify logistic regression fit, AUC-ROC calculation, p-value reporting, and threshold optimization.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` using `statsmodels` for **Mixed-Effects Logistic Regression (GLMM)** to predict token validity from entropy values, stratified by task type (GSM8K vs MiniGrid), and using random intercepts for sequences to handle nested data. **CRITICAL**: The implementation MUST handle **layer index as a continuous covariate** (not just pooling) as required by FR-004. **Output**: MUST write results to `results/model_fitting.json` containing coefficients, p-values, and AUC-ROC. **Deliverable**: `src/analysis/logistic_model.py` with `fit_model` function that returns coefficients, p-values, and AUC-ROC.
- [ ] T031 [US3] Implement stratification logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` (GSM8K vs MiniGrid, early/mid/late layer pooling or continuous covariate). **Deliverable**: `src/analysis/logistic_model.py` with stratification support.
- [ ] T032 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/threshold_opt.py` to find optimal entropy threshold minimizing weighted false positive/negative sum. **Output**: Write optimal threshold to `results/optimal_threshold.json`. **Deliverable**: `src/analysis/threshold_opt.py` with `optimize_threshold` function.
- [ ] T033a [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/sensitivity.py` to **apply multiple-comparison correction (Bonferroni OR Benjamini-Hochberg)** to p-values derived from the model fitting process (T030, input `results/model_fitting.json`). **Requirement**: The task MUST NOT enforce a hard pass/fail gate; non-significant results (FDR > alpha) are valid empirical outcomes and must be recorded with a `significant` flag set to False. **Requirement**: MUST accept a `--correction-method` CLI argument (choices: `bonferroni`, `benjamini-hochberg`) to select the method, with **`benjamini-hochberg` as the default**. **Requirement**: The task MUST **fail loudly (raise RuntimeError)** if the input data is empty, contains only one class, or if the correction logic fails. **Input**: `results/model_fitting.json`. **Output**: `results/fdr_report.json` with schema `{'adjusted_p_values': [...], 'fdr': float, 'alpha': 0.05, 'significant': bool}`. **Deliverable**: `src/analysis/sensitivity.py` with `apply_correction` function. **Depends on T030**.
- [ ] T033b [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/sensitivity.py` to **perform the sensitivity sweep** across a range of entropy thresholds. **Requirement**: MUST read the optimal point from `results/optimal_threshold.json` (T032) and the corrected p-values from `results/fdr_report.json` (T033a). **Requirement**: Sweep range `[optimal - 0.1, optimal + 0.1]` with step size `0.01`, and **explicitly link the sweep results to the corrected p-values** to determine the optimal threshold under the corrected significance level (SC-003). **Output**: Write sweep results to `results/sensitivity_sweep.json`. **Deliverable**: `src/analysis/sensitivity.py` with `perform_sweep` function. **Depends on T032, T033a**.
- [ ] T034 [US3] Implement logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` to catch p >= 0.05, log a warning, and return a result object with `significant=False` instead of crashing. **Deliverable**: Robust handling in `logistic_model.py`.
- [ ] T035 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/decay_analysis.py` to split the dataset into "short" (sequence length <= 100 tokens) and "long" (sequence length > 100 tokens) subsets. **Requirement**: The task MUST ALSO stratify by **task type (GSM8K vs MiniGrid)** and calculate/compute AUC-ROC for both subsets and both task types to measure decay of predictive power (SC-004). **Requirement**: The task MUST **fail loudly (raise RuntimeError)** if the input dataset is empty, if either subset has zero samples, or if AUC calculation fails. **Deliverable**: `results/decay_analysis.json` containing AUC-ROC for short/long subsets, task types, and the difference metric. **Depends on T030**.
- [ ] T036 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/checksum_recorder.py` to generate local checksums for all files in `data/` and record them in `state/projects/PROJ-881-llmxive-follow-up-extending-efficientrol.yaml` under `artifact_hashes`. **Schema**: `artifact_hashes` is a flat map of `relative_path: sha256_hash`. **CRITICAL**: This task MUST **checksum the final merged artifact** (`data/entropy_profiles_merged.jsonl` from T025) directly. **Requirement**: The script MUST update the `updated_at` timestamp in `state/projects/PROJ-881-llmxive-follow-up-extending-efficientrol.yaml` immediately after recording checksums to satisfy Constitution Principle V. **Timestamp Format**: ISO 8601. **Deliverable**: `scripts/checksum_recorder.py` and updated `state/...yaml`. **Depends on T025**.
- [ ] T037 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/report.py` to write `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/results/final_report.json` containing AUC-ROC, p-values, the recommended threshold from `threshold_opt.py`, the **FDR metric** from `sensitivity.py` (T033a), the **sensitivity sweep metrics** from `sensitivity.py` (T033b), and the **decay analysis metrics** from `decay_analysis.py` (SC-004). **Requirement**: MUST check for existence of `results/fdr_report.json`, `results/sensitivity_sweep.json`, and `results/decay_analysis.json`. **Requirement**: MUST validate that these files contain **non-null, non-empty metric fields**. If files are missing OR contain invalid/empty metrics, **raise a RuntimeError**. **Requirement**: If files exist but contain valid non-significant results, the task MUST **accept them**. **Requirement**: MUST include a "Data Provenance" section with checksums from T036. **Deliverable**: `results/final_report.json` must contain all metrics required by SC-001 through SC-005. **Depends on T033a, T033b, T035, T036**.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T038 [P] [US3] Contract test for analysis result schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_analysis_result_schema.py`.
- [ ] T039 [P] [US3] Integration test for threshold optimization in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_threshold_optimization.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Update `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/README.md` with CLI usage examples.
- [ ] T041 [P] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/docs/api.md` with docstrings for `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py`.
- [ ] T042 [P] Run `ruff check --fix` and `black.` on the entire `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/` directory and resolve all linting errors.
- [ ] T043 [P] Add unit tests in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/unit/test_entropy_calc.py` covering edge cases (log(0), empty input) and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/unit/test_validators.py` for schema validation.
- [ ] T044 [P] Implement input validation in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` to reject non-HuggingFace URLs. **Deliverable**: `src/data/download.py` with URL validation.
- [ ] T045a [P] [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/main.py` CLI Argument Definition: Define `argparse` arguments `--dataset`, `--model`, `--seed`, `--correction-method`. **Note**: The `--sample-size` argument has been removed; the 500-example cap is enforced by T010. **Deliverable**: `main.py` with `parse_args` function returning `args` object.
- [ ] T045b [P] [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/main.py` Orchestration Logic: Implement `run_pipeline(args)` function that calls download, generation, and analysis modules sequentially based on `args`. **Deliverable**: `main.py` with `run_pipeline` function.
- [ ] T045c [P] [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/main.py` Error Handling: Implement `handle_errors` decorator or wrapper for `run_pipeline` to catch and log exceptions. **Deliverable**: `main.py` with `handle_errors` logic.
- [ ] T046 [P] Execute `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_quickstart.sh` to ensure all commands in `quickstart.md` run successfully in a fresh virtualenv.

---

## Phase 7: Data Integrity & Execution Safety (Revision Pass)

**Goal**: Address specific review concerns regarding data sourcing, streaming, and failure modes to prevent fabrication and ensure reproducibility.

- [ ] T047 [P] [US1/US2] Add a verification step in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_data_integrity.py` that compares the SHA-256 checksum of the downloaded dataset file against the hash recorded in `data/.checksums` (generated by T036), raising an error if they mismatch. **Note**: Do NOT attempt to fetch a dynamic "HuggingFace info hash" from the API; rely on the local manifest. **Deliverable**: `scripts/validate_data_integrity.py`.
- [ ] T048 [P] [US3] Update `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/report.py` to include a "Data Provenance" section in `results/final_report.json` that lists the exact dataset version, sample size, streaming parameters, and **checksums from T036**, ensuring traceability from result back to raw data. **Requirement**: MUST depend on T036. **Deliverable**: `results/final_report.json` with Data Provenance section.
- [ ] T049 [P] [US3] Modify `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/main.py` to ensure the `--sample-size` argument is removed and the 500-example cap is enforced solely by T010 (data loading). **Deliverable**: `main.py` updated.
- [ ] T050 [P] [US3] Modify `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` to explicitly check for and handle the case where the input dataset contains zero valid tokens or zero invalid tokens (perfect separation), logging a warning and skipping the logistic regression fit rather than crashing or returning NaNs. **Deliverable**: Robust handling in `logistic_model.py`.
- [ ] T051 [P] [US1/US2] Implement **streaming dataset loading** in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` using `datasets.load_dataset(..., streaming=True)` for GSM8K and MiniGrid to ensure the full dataset is processed without loading it entirely into RAM. **Requirement**: The implementation MUST iterate over the dataset in chunks (e.g., using `itertools.islice` or a custom generator) and write intermediate results to disk immediately. **Requirement**: If the full dataset cannot be processed within the compute budget (trigger: RAM usage > 6GB), the task MUST implement a well-defined **real sample** (e.g., `itertools.islice` the first N rows or a fixed-seed random sample) and explicitly state the sample size and its representativeness limitation in `results/final_report.json`. **Constraint**: Do NOT use synthetic or toy datasets as a fallback. **Deliverable**: `src/data/download.py` with streaming logic and `results/final_report.json` documenting the sampling strategy if applicable.
- [ ] T052 [P] [US3] Add a **verification step** in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_real_data.py` to ensure that all data used in the analysis originates from the verified real source (HuggingFace) and not from any synthetic or mock data. **Requirement**: The script MUST check the data files for any indicators of synthetic generation (e.g., specific patterns, checksums of known synthetic datasets) and raise an error if found. **Deliverable**: `scripts/validate_real_data.py` with validation logic and `results/validation_report.json` confirming data authenticity.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0**: No dependencies - can start immediately
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
Task: "Implement model loading logic in src/generation/generation.py"
Task: "Implement generation loop in src/generation/generation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research & Design
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
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