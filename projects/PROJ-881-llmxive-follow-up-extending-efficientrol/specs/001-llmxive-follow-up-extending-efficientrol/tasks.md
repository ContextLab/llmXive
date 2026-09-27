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

- [ ] T001 [Plan] Define Semantic Alignment logic for GSM8K/MiniGrid. **Deliverable**: Document `specs/001-entropy-validity-prediction/contracts/semantic_alignment.md` describing the logic for matching generated tokens to ground truth paths. **Depends on**: None.
- [X] T002 [Plan] Select Qwen1.5-1.5B model for CPU feasibility based on spec assumptions. **Deliverable**: `docs/model_selection.md` justifying the choice. **Depends on**: T001.
- [X] T003 [Plan] Design Mixed-Effects Logistic Regression (GLMM) structure with random intercepts for sequence_id. **Deliverable**: `docs/glmm_design.md` detailing the formula and stratification strategy. **Depends on**: T002.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T004 [P] Create root project directory structure and verify: Create `setup.sh` containing explicit `mkdir -p` commands for `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/`, `tests/`, `data/`, `docs/`, `scripts/`, `results/`, `specs/001-entropy-validity-prediction/contracts/`, and subdirectories `src/`, `data/raw/`, `data/processed/`, `artifacts/`, `state/`. **CRITICAL**: This task MUST also include a verification step within `setup.sh` or a companion script `scripts/verify_structure.py` that checks all paths exist, exits with code 1 if missing, and generates `project_structure.log`. **Deliverable**: `setup.sh`, `scripts/verify_structure.py`, and `project_structure.log`.
- [ ] T005 [P] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/requirements.txt` pinning versions for `transformers`, `torch`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `h5py`, `pytest`, `statsmodels`, `psutil`, `huggingface_hub`, `pymer4`, `minigrid`. **CRITICAL**: Must include Qwen1.5-1.5B model compatibility. **Deliverable**: Valid `requirements.txt` file at `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/requirements.txt`.
- [ ] T006 [P] Configure linting (ruff) and formatting tools: Create `pyproject.toml` with black/ruff config, `.ruff.toml` for linter rules, and `.black.toml` for formatter settings. **Deliverable**: These three config files must exist and be valid.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007a [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/entropy_calc.py` with Shannon entropy logic ($-\sum p_i \log p_i$). **Input**: The function `calculate_entropy(probs)` MUST accept **softmax-normalized probability distributions (tensor)** of shape `[batch, vocab_size]` or `[vocab_size]` on **CPU**, clamp probability values < 1e-9 to 1e-9 *before* taking the logarithm to prevent log(0) errors, and return a float. **Semantic Test**: The function MUST correctly handle near-zero probability inputs by returning a finite value without crashing. **Deliverable**: Create `src/utils/entropy_calc.py` with function `calculate_entropy(probs)`.
- [ ] T007b [P] [US1/US2] Create unit test `tests/unit/test_entropy_calc.py::test_clamp_prevents_log_zero` to verify the entropy calculation. **Test Input**: Use a tensor where one class has probability 0.0 (after softmax) and another has 1.0 (or near 1.0). **Expected Output**: Finite value. **Deliverable**: `tests/unit/test_entropy_calc.py` with the specific test case. **Depends on**: T007a.
- [ ] T008 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/validators.py` for schema validation (TokenSequence, EntropyProfile, ValidityLabel). **Deliverable**: `src/utils/validators.py` with validation functions.
- [ ] T009 [P] [US1/US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` with dataset capping and token-level batching infrastructure. **CRITICAL**: This task MUST implement TWO distinct functions in the same file:
 1. `stream_batch(examples, max_examples=500)`: Handles dataset loading in chunks of **500 examples** (FR-001). **Input**: HuggingFace dataset iterator. **Fallback**: If `psutil.virtual_memory().percent > 90`, halve batch size. **Minimal Threshold**: Raise RuntimeError if batch size drops below **10 examples**.
 2. `token_batch_stream(tokens, max_tokens=50)`: Handles sequences in **batches of 50 tokens** (FR-007). **Input**: List of tokens. **Fallback**: If `psutil.virtual_memory().percent > 90`, halve batch size. **Minimal Threshold**: Do NOT raise an error if batch size drops below 8 tokens; instead, process the remaining tokens as a smaller final batch. **Deliverable**: `src/data/preprocessing.py` with both functions and `tests/integration/test_preprocessing.py` verifying both fallback logics.
- [ ] T010 [P] [US1/US2] [FR-001] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` to fetch GSM8K and MiniGrid from HuggingFace Datasets. **CRITICAL**: This task MUST enforce the **500-example cap per task** (GSM8K and MiniGrid) as required by FR-001 by default using `itertools.islice` within the streaming logic. **Constraint**: MUST NOT use `try/except` blocks that fall back to `generate_synthetic_*()` or `mock_*()` data. If `datasets.load_dataset` fails, the script MUST raise a `ConnectionError` or `FileNotFoundError` immediately to let the run fail loudly. **Dataset Config**: Must fetch 'train' split for GSM8K and 'train' split for MiniGrid (specific subset). **Note**: The 500 cap is a maximum limit; if the source dataset is smaller, `islice` will return fewer examples. **Deliverable**: `src/data/download.py` with no synthetic fallbacks and explicit 500-example capping logic.
- [ ] T011 [P] [US1/US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/.env.example` with keys for `HF_TOKEN`, `DATA_PATH`, `MODEL_PATH` and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/config.py` to load them. **Deliverable**: `.env.example` and `src/config.py`.
- [ ] T012 [P] [US1/US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/dataset.schema.yaml` defining the schema for the merged dataset used in T019. **Deliverable**: `contracts/dataset.schema.yaml`.
- [ ] T012a [P] [Cross-Cut] Download Canonical Ground Truth (GSM8K/MiniGrid). **CRITICAL**: This task MUST fetch the *canonical* ground-truth solutions (GSM8K answer strings, MiniGrid goal states) from the HuggingFace datasets using `datasets.load_dataset`. It MUST NOT generate these from scratch. **Input**: HuggingFace dataset names. **Output**: `data/canonical_ground_truth.jsonl` with schema `{"prompt_id": str, "task_type": "gsm8k"|"minigrid", "canonical_solution": str, "start_state": str, "goal_state": str}`. **Constraint**: This task MUST run *before* T012b. **Deliverable**: `data/canonical_ground_truth.jsonl`. **Depends on**: T010.
- [ ] T012b [P] [Cross-Cut] Generate BFS Paths for MiniGrid. **CRITICAL**: This task MUST use the `start_state` and `goal_state` from `data/canonical_ground_truth.jsonl` (T012a) to generate valid shortest paths for MiniGrid using Breadth-First Search (BFS) on the environment grid (version `minigrid>=2.3.0`). **Constraint**: This task MUST NOT generate ground truth for GSM8K (use canonical solution directly). **Output**: Append to `data/canonical_ground_truth.jsonl` with a new field `valid_paths: List[str]` for MiniGrid entries. **Deliverable**: Updated `data/canonical_ground_truth.jsonl`. **Depends on**: T012a.
- [ ] T012c [P] [Cross-Cut] Verify Model Feasibility (1.5B). **CRITICAL**: This task MUST attempt to load the Qwen-1.5B model on CPU and measure peak RAM usage with a single forward pass of a 512-token sequence. **Constraint**: If peak RAM > 7GB, the task MUST **NOT** automatically fall back to 0.5B. Instead, it MUST write a `spec_amendment_proposal.md` detailing the scope shift and create a `model_switch_flag.json` with `status: "fail"`. The pipeline MUST pause until the spec is amended. If the 1.5B model fits, it MUST write `model_switch_flag.json` with `status: "pass"`. **Deliverable**: `results/model_feasibility_report.json`, `spec_amendment_proposal.md` (if fail), `model_switch_flag.json`. **Depends on**: T005, T011.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Generation and Ground Truth Labeling (Priority: P1) 🎯 MVP

**Goal**: Generate ground-truth token sequences for GSM8K and MiniGrid using a CPU-tractable model and label them with validity flags.

**Independent Test**: Run baseline generation on a subset of GSM8K problems; verify output log contains complete token sequences and binary validity flags against known solutions.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` model loading logic. **MUST** read `model_switch_flag.json` (from T012c). If `status: "pass"`, load **Qwen1.5-1.5B**. If `status: "fail"`, load **Qwen1.5-0.5B** (only if spec amended). **Deliverable**: `src/generation/generation.py` with `load_model` function.
- [ ] T014 [US1] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` baseline generation loop. **MUST** perform a **full autoregressive forward pass** with `temperature=0.0` using the loaded model. **Deliverable**: `src/generation/generation.py` with `generate_baseline` function.
- [ ] T015 [US1] Implement ground truth matching logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py`. **MUST** label validity by **deterministic comparison** against the ground-truth solution using the **Semantic Alignment logic** defined in T001. **Specifics**: Read `data/canonical_ground_truth.jsonl` (output of T012b). For GSM8K, validity is determined by exact match with the `canonical_solution` string. For MiniGrid, validity is determined by exact match with *any of the known valid ground-truth paths* in `valid_paths`. **Input Schema**: `data/raw_generation.jsonl` (schema: `{"prompt_id": str, "tokens": List[str]}`); `data/canonical_ground_truth.jsonl`. **Output**: Write validity labels to `data/validity_labels.jsonl`. **Deliverable**: `src/generation/generation.py` with `label_validity` function. **Depends on**: T012b, T014.
- [ ] T016 [US1] Create output writer for JSONL format in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` (TokenSequence, ValidityLabel). **Deliverable**: `src/generation/generation.py` with `write_jsonl` function.
- [ ] T017 [US1] Implement exception handling in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` for cases where no ground-truth path matches: **DO NOT** flag as 'ambiguous'. Instead, implement logic to label a token as "valid" if it matches *any* of the known valid ground-truth paths fetched dynamically from the T012b output. **CRITICAL**: The logic MUST iterate through ALL known valid paths for the specific `prompt_id`. If a match is found with *any* path, the token is marked "valid". Only if *no* path matches after checking all options should the token be marked "invalid" and a warning logged to `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/logs/generation.log` with JSON format `{"prompt_id": "...", "reason": "no_match", "validity": false}`. **Log level**: WARNING. **Rotation**: Use `RotatingFileHandler` with `maxBytes=10MB` and `backupCount=5` and path `logs/generation.log`. **Error handling**: raise RuntimeError if log file is locked. **Deliverable**: `src/generation/generation.py` with `label_validity` updated and logging verified. **Depends on**: T012b, T015.
- [ ] T018 [US1] Configure `logging` in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to output JSON-formatted logs to `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/logs/generation.log` including **the complete sequence of tokens and a binary validity flag for each token position**. **Deliverable**: `logs/generation.log` with JSON entries.
- [ ] T019 [US1] Implement merging logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to combine generation outputs (T014) with ground truth labels (T015) into a single **intermediate dataset (US1 only)**. **Function Signature**: `merge_outputs(generation_data, label_data, join_keys=['prompt_id', 'token_index'])`. **Join Logic**: Align on `prompt_id` and `token_index` (0-based). Handle variable sequence lengths by aligning on these keys. **MUST** also handle merging of generation chunks (from T014) before final merge. **Input**: `data/raw_generation.jsonl` (chunks) and `data/validity_labels.jsonl`. **Output**: `data/merged_us1.jsonl`. **Deliverable**: Output file `data/merged_us1.jsonl` validating against `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/dataset.schema.yaml`. **Depends on**: T013, T014, T015, T016, T017, T018.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US1] Contract test for dataset schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_dataset_schema.py`. **Deliverable**: `tests/contract/test_dataset_schema.py::test_schema_validation_fails_on_missing_field` that loads `contracts/dataset.schema.yaml` and asserts `ValueError` is raised for a record missing the `validity` field. **Depends on**: T012.
- [ ] T021 [US1] Integration test for ground truth labeling in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_ground_truth_labeling.py`. **Deliverable**: `tests/integration/test_ground_truth_labeling.py` verifying multi-path matching. **Depends on**: T019 (Output Writer/Merging).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Intermediate State Extraction and Entropy Calculation (Priority: P2)

**Goal**: Re-run baseline sequences with instrumentation to capture probability distributions and calculate Shannon entropy at every intermediate layer.

**Independent Test**: Re-run a subset of sequences with instrumentation; verify output log contains entropy values for every layer and token position with no missing values.

### Implementation for User Story 2

- [ ] T022 [P] [US2] [FR-003] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` hooks to capture layer-wise probability distributions. **Deliverable**: `src/generation/generation.py` with forward hooks.
- [ ] T023 [US2] Integrate `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/entropy_calc.py` to compute entropy vectors for each token position. **Implementation Detail**: Register a forward hook in `generation.py` that captures the output of each intermediate layer, passes the logits to `entropy_calc.calculate_entropy()` (after softmax normalization), and stores the result in the token's metadata. **Deliverable**: `src/generation/generation.py` updated.
- [ ] T024a [US2] Implement incremental token processing in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to process sequences **in chunks of 50 tokens** with an internal **50-token batching loop** for memory safety during entropy extraction. **CRITICAL**: This task MUST **reuse** the `token_batch_stream` function from T009 to ensure a single source of truth for memory management. **Input**: MUST read from `data/merged_us1.jsonl` (output of T019) and validate against `contracts/dataset.schema.yaml`. **File Format**: JSONL. **Naming Convention**: `temp_entropy_batch_{batch_id:04d}.jsonl` where `batch_id` is a **zero-padded sequential integer starting at 0**. **Directory**: `data/processed/temp_batches/` (create if missing). **Schema**: Each record MUST contain `prompt_id`, `token_index`, `sequence_length`, and `layer_entropy_map` (dict of layer_id: entropy_value). **CRITICAL**: This task MUST **strictly output temporary batch files** and MUST **NOT** perform the final merge; the merge is the **sole responsibility of T025**. **Note**: This task implements the 50-token internal batch constraint (FR-007) specifically for the entropy extraction step. Dataset row capping is handled in T010. **CRITICAL**: This task MUST handle **full sequences up to 512 tokens** in length, processing them in 50-token chunks **incrementally** (not loading full context). **Partial Batch Handling**: If a sequence length is not a multiple of 50, the last chunk MUST be processed as a smaller batch (e.g., 12 tokens) without error. **Deliverable**: `src/generation/generation.py` with `process_batch` function and `tests/integration/test_entropy_extraction.py::test_50_token_batching` verifying the batching logic. **Depends on**: T019, T022, T023.
- [ ] T024b [P] [US2] Implement validation of temporary batch files in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py`. **Deliverable**: `src/data/preprocessing.py` with `validate_temp_batch` function.
- [ ] T025a [US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` logic to merge entropy profiles (from T024 temp batches) with the labeled dataset (from T019) into a single EntropyProfile record. **CRITICAL**: This task MUST perform a **3-way join** using `prompt_id` and `token_index` as keys: (1) `data/merged_us1.jsonl` (T019), (2) `data/processed/temp_batches/temp_entropy_batch_*.jsonl` (T024), and (3) the original US1 context. **CRITICAL**: This task is the **sole owner** of the final merge logic for the artifact `data/entropy_profiles_merged.jsonl`. **CRITICAL**: This task MUST run **after all T024 instances complete**. **Deliverable**: Output file `data/entropy_profiles_merged.jsonl` validating against `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/entropy_profile.schema.yaml` and mandating preservation of layer-wise granularity. **Note: This task requires US1 (T019) and US2 (T024) to be complete. Explicitly depends on T019 and T024.**
- [ ] T025b [P] [US2] Implement cleanup logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` to delete `data/processed/temp_batches/` files after successful merge in T025. **Deliverable**: `src/data/preprocessing.py` with `cleanup_temp_batches` function.
- [ ] T026 [US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` function `validate_entropy_profile()` that references `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/entropy_profile.schema.yaml` and raises ValueError if any layer/token in an EntropyProfile record is None or missing entropy values. **Deliverable**: On success, write `results/validation_report.json` with summary stats; on failure, exit with code 1. **Note**: This is the canonical implementation of `validate_entropy_profile`; T009 only creates the file infrastructure. **Depends on**: T025.
- [ ] T027 [P] [US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/profile_memory.py` that profiles `src/generation/generation.py` using `cProfile`, verifies RAM usage stays < 6.5GB for sequences up to **512 tokens** processed in batches of 50 tokens, and writes `results/profile_report.txt`. **Deliverable**: `scripts/profile_memory.py` and `results/profile_report.txt` containing a **Markdown table** of `['Batch Size', 'Peak RSS (MB)', 'Avg Latency (s)']`. **Note**: This is a verification step integrated into T024 implementation. **Depends on**: T024.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US2] Contract test for entropy profile schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_entropy_profile_schema.py`.
- [ ] T029 [P] [US2] Integration test for intermediate state extraction in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_entropy_extraction.py`.

**Checkpoint**: At this point, At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Signal Decay Analysis and Threshold Optimization (Priority: P3)

**Goal**: Fit logistic regression models to predict token validity from entropy values and identify optimal entropy thresholds.

**Independent Test**: Run analysis on combined dataset; verify logistic regression fit, AUC-ROC calculation, p-value reporting, and threshold optimization.

### Implementation for User Story 3

- [ ] T030 [US3] [FR-004] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` using `pymer4` for **Mixed-Effects Logistic Regression (GLMM)** to predict token validity from entropy values, stratified by task type (GSM8K vs MiniGrid), and using **random intercepts for sequence_id** to handle nested data. **CRITICAL**: The implementation MUST support **BOTH** strategies: (1) `layer_index` as a continuous covariate, and (2) `layer_pooling` (early/mid/late). **Logic**: The code MUST check for layer sparsity. If sparsity is high, it MUST automatically switch to the pooling strategy. **Formula**: MUST be configurable via a `strategy` parameter. **Output**: MUST write results to `results/model_fitting.json` containing coefficients, p-values, and AUC-ROC. **Special Case**: If the dataset contains only one task type, the code MUST dynamically drop `task_type` from the formula to avoid `pymer4` errors. **Deliverable**: `src/analysis/logistic_model.py` with `fit_model` function that returns coefficients, p-values, and AUC-ROC.
- [ ] T031 [US3] Implement stratification logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` (GSM8K vs MiniGrid, early/mid/late layer pooling or continuous covariate). **Deliverable**: `src/analysis/logistic_model.py` with stratification support.
- [ ] T032 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/threshold_opt.py` to find optimal entropy threshold minimizing weighted false positive/negative sum. **Output**: Write optimal threshold to `results/optimal_threshold.json`. **Deliverable**: `src/analysis/threshold_opt.py` with `optimize_threshold` function.
- [ ] T033a [US3] [FR-006] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/sensitivity.py` to **apply multiple-comparison correction (Bonferroni OR Benjamini-Hochberg)** to p-values derived from the model fitting process (T030, input `results/model_fitting.json`). **Input Structure**: `results/model_fitting.json` MUST be a list of dicts, each containing `p_value` and `hypothesis_id`. **Requirement**: The task MUST NOT enforce a hard pass/fail gate; non-significant results (FDR > alpha) are valid empirical outcomes and must be recorded with a `significant` flag set to False. **Requirement**: MUST accept a `--correction-method` CLI argument (choices: `bonferroni`, `benjamini-hochberg`) to select the method, with **`benjamini-hochberg` as the default**. **Requirement**: The task MUST **fail loudly (raise RuntimeError)** if the input data is empty, contains only one class, or if the correction logic fails. **Requirement**: Default `alpha` value for correction is **0.05**. **Output**: `results/fdr_report.json` with schema `{'adjusted_p_values': [...], 'estimated_fdr': float, 'alpha': 0.05, 'significant': bool}`. **Metric Definition**: `estimated_fdr` is the proportion of rejected hypotheses expected to be false positives (calculated via BH procedure). **Deliverable**: `src/analysis/sensitivity.py` with `apply_correction` function. **Depends on**: T030.
- [ ] T033b [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/sensitivity.py` to **perform the sensitivity sweep** across a range of entropy thresholds. **Requirement**: MUST read the optimal point from `results/optimal_threshold.json` (T032) and the corrected p-values from `results/fdr_report.json` (T033a). **Requirement**: Sweep range `[optimal - 0.1, optimal + 0.1]` with step size `0.01 (2309.06305, https://arxiv.org/abs/2309.06305)`, and **explicitly link the sweep results to the corrected p-values** to determine the optimal threshold under the corrected significance level (SC-003). **Output**: Write sweep results to `results/sensitivity_sweep.json`. **Deliverable**: `src/analysis/sensitivity.py` with `perform_sweep` function. **Depends on**: T032, T033a.
- [ ] T034 [US3] Implement logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` to catch p >= 0.05, log a warning, and return a result object with `significant=False` instead of crashing. **Deliverable**: Robust handling in `logistic_model.py`.
- [ ] T035 [US3] [SC-004] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/decay_analysis.py` to split the dataset into "short" and "long" subsets based on the **median sequence length** of the dataset (not a hardcoded 100). **Requirement**: The task MUST ALSO stratify by **task type (GSM8K vs MiniGrid)** and calculate/compute AUC-ROC for both subsets and both task types to measure decay of predictive power (SC-004). **Field**: MUST use the `sequence_length` field from the merged dataset. **Requirement**: The task MUST **fail loudly (raise RuntimeError)** if the input dataset is empty, if either subset has zero samples, or if AUC calculation fails. **Requirement**: If sequence length metadata is missing, raise an error. **Requirement**: The task MUST log the chosen median threshold and justify it in the output report. **Deliverable**: `results/decay_analysis.json` containing AUC-ROC for short/long subsets, task types, and the difference metric. **Depends on**: T030.
- [ ] T036 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/checksum_recorder.py` to generate local checksums for all files in `data/` and record them in `state/projects/PROJ-881-llmxive-follow-up-extending-efficientrol.yaml` under `artifact_hashes`. **Schema**: `artifact_hashes` is a flat map of `relative_path: sha256_hash`. **`updated_at`**: ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`). **CRITICAL**: This task MUST **checksum the final merged artifact** (`data/entropy_profiles_merged.jsonl` from T025) directly. **Requirement**: The script MUST update the `updated_at` timestamp in `state/projects/PROJ-881-llmxive-follow-up-extending-efficientrol.yaml` immediately after recording checksums to satisfy Constitution Principle V. **Deliverable**: `scripts/checksum_recorder.py` and updated `state/...yaml`. **Depends on**: T025.
- [ ] T037 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/report.py` to write `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/results/final_report.json` containing AUC-ROC, p-values, the recommended threshold from `threshold_opt.py`, the **estimated FDR** from `sensitivity.py` (T033a), the **sensitivity sweep metrics** from `sensitivity.py` (T033b), and the **decay analysis metrics** from `decay_analysis.py` (SC-004). **Requirement**: MUST check for existence of `results/fdr_report.json`, `results/sensitivity_sweep.json`, and `results/decay_analysis.json`. **Requirement**: MUST validate that these files contain **non-null, non-empty metric fields**. If files are missing OR contain invalid/empty metrics, **raise a RuntimeError**. **Requirement**: If files exist but contain valid non-significant results, the task MUST **accept them**. **Requirement**: MUST include a "Data Provenance" section with checksums from T036. **Deliverable**: `results/final_report.json` must contain all metrics required by SC-001 through SC-005. **Depends on**: T033a, T033b, T035, T036.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T038 [P] [US3] Contract test for analysis result schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_analysis_result_schema.py`.
- [ ] T039 [P] [US3] Integration test for threshold optimization in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_threshold_optimization.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Update `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/README.md` with CLI usage examples.
- [ ] T041 [P] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/docs/api.md` with docstrings for `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py`.
- [ ] T042 [P] [CI] Run `ruff check --fix` and `black.` on the entire `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/` directory and resolve all linting errors. **Note**: This task is a CI gate, not a manual pipeline step.
- [ ] T043 [P] Add unit tests in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/unit/test_entropy_calc.py` covering edge cases (log(0), empty input) and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/unit/test_validators.py` for schema validation.
- [ ] T044 [P] Implement input validation in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` to reject non-HuggingFace URLs. **Deliverable**: `src/data/download.py` with URL validation.
- [ ] T045 [P] [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/main.py` CLI and Pipeline: Define `argparse` arguments `--dataset`, `--model`, `--seed`, `--correction-method`. Implement `run_pipeline(args)` function that calls download, generation, and analysis modules sequentially based on `args`. Implement `handle_errors` decorator or wrapper for `run_pipeline` to catch and log exceptions. **Note**: The `--sample-size` argument is NOT defined; the 500-example cap is hardcoded in T010. **Deliverable**: `main.py` with `parse_args`, `run_pipeline`, and `handle_errors` functions.
- [ ] T046 [P] Execute `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_quickstart.sh` to ensure all commands in `quickstart.md` run successfully in a fresh virtualenv.

---

## Phase 7: Data Integrity & Execution Safety (Revision Pass)

**Goal**: Address specific review concerns regarding data sourcing, streaming, and failure modes to prevent fabrication and ensure reproducibility.

- [ ] T047 [P] [Cross-Cut] Add a verification step in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_data_integrity.py` that compares the SHA-256 checksum of the downloaded dataset file against the hash recorded in `data/.checksums` (generated by T036), raising an error if they mismatch. **Note**: Do NOT attempt to fetch a dynamic "HuggingFace info hash" from the API; rely on the local manifest. **Deliverable**: `scripts/validate_data_integrity.py`.
- [ ] T048 [P] [Cross-Cut] Update `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/report.py` to include a "Data Provenance" section in `results/final_report.json` that lists the exact dataset version, sample size, streaming parameters, and **checksums from T036**, ensuring traceability from result back to raw data. **Requirement**: MUST depend on T036. **Deliverable**: `results/final_report.json` with Data Provenance section.
- [ ] T049 [P] [Cross-Cut] Modify `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/main.py` to ensure the `--sample-size` argument is not defined and the 500-example cap is enforced solely by T010 (data loading). **Note**: The cap is hardcoded to 500 in T010; no CLI override is provided. **Deliverable**: `main.py` updated.
- [ ] T050 [P] [Cross-Cut] Modify `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` to explicitly check for and handle the case where the input dataset contains zero valid tokens or zero invalid tokens (perfect separation), logging a warning and skipping the logistic regression fit rather than crashing or returning NaNs. **Deliverable**: Robust handling in `logistic_model.py`.
- [ ] T051 [P] [Cross-Cut] [FR-001] Implement **streaming dataset loading** in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` using `datasets.load_dataset(..., streaming=True)` for GSM8K and MiniGrid to ensure the full dataset is processed without loading it entirely into RAM. **Requirement**: The implementation MUST iterate over the dataset in chunks (e.g., using `itertools.islice` or a custom generator) and write intermediate results to disk immediately. **Requirement**: If the full dataset cannot be processed within the compute budget (trigger: RAM usage > 7GB, detected via `psutil.virtual_memory().percent > 90`), the task MUST implement a well-defined **real sample** (e.g., `itertools.islice` the first N rows with `seed=42`) and explicitly state the sample size and its representativeness limitation in `results/final_report.json`. **CRITICAL**: If the sample size is less than 500, the task MUST set a `sample_deviation: true` flag in the final report and log a WARNING. **Constraint**: Do NOT use synthetic or toy datasets as a fallback. **Deliverable**: `src/data/download.py` with streaming logic and `results/final_report.json` documenting the sampling strategy if applicable.
- [ ] T052 [P] [Cross-Cut] Add a **verification step** in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_real_data.py` to ensure that all data used in the analysis originates from the verified real source (HuggingFace) and not from any synthetic or mock data. **Requirement**: The script MUST check the data files for any indicators of synthetic generation (e.g., specific patterns, checksums of known synthetic datasets) and raise an error if found. **Deliverable**: `scripts/validate_real_data.py` with validation logic and `results/validation_report.json` confirming data authenticity.
- [ ] T053 [P] [Cross-Cut] Implement **cap verification** in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/verify_cap.py` to run the download pipeline (T010) and verify that a representative set of examples is fetched per task (GSM8K, MiniGrid). **Requirement**: The script MUST also simulate a low-memory scenario (if possible) to verify the 'real sample' fallback logic triggers correctly when RAM > 7GB. **Deliverable**: `scripts/verify_cap.py` and `results/cap_verification_report.json`.
- [ ] T054 [P] [Cross-Cut] Document the model choice in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/docs/model_selection.md` explicitly stating that **Qwen1.5-1.5B** was chosen to match FR-002's 1.5B requirement (if feasible per T012b), and documenting any performance limitations observed on CPU. **Deliverable**: `docs/model_selection.md`.
- [ ] T055 [P] [Cross-Cut] Update `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/report.py` to explicitly calculate and report the **estimated FDR** (proportion of rejected hypotheses expected to be false positives) in `results/final_report.json`, comparing it against the nominal alpha level (0.05) as required by SC-005. **Deliverable**: `results/final_report.json` with explicit FDR comparison.
- [ ] T056 [P] [Cross-Cut] Implement **multi-path testing** in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_multi_path_labeling.py` to explicitly test the 'multiple valid paths' scenario for MiniGrid, ensuring the system correctly iterates through *all* known paths and does not prematurely flag a token as invalid. **Deliverable**: `tests/integration/test_multi_path_labeling.py`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0**: No dependencies - can start immediately (T001 is independent)
- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **User Story 2 (P2)**: **MUST wait for User Story 1** (T019) to produce `merged_us1.jsonl`.
 - **User Story 3 (P3)**: **MUST wait for User Story 2** (T025) to produce `entropy_profiles_merged.jsonl`.
 - Stories are **SERIALLY** dependent on data artifacts, not independent.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel

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
 - Developer B: User Story 2 (starts after US1)
 - Developer C: User Story 3 (starts after US2)
3. Stories complete and integrate sequentially

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence