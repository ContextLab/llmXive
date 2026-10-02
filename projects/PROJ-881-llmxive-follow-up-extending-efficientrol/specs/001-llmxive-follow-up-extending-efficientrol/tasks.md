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

- [X] T001a [Plan] Define Semantic Alignment logic for GSM8K. **Deliverable**: Document `specs/001-entropy-validity-prediction/contracts/semantic_alignment_gsm8k.md` describing the logic for matching generated tokens to ground truth paths. **ALGORITHM**: Exact string match of the generated token sequence against the `canonical_solution`. **Depends on**: None.
- [X] T001b [Plan] Define Semantic Alignment logic for MiniGrid. **Deliverable**: Document `specs/001-entropy-validity-prediction/contracts/semantic_alignment_minigrid.md` describing the logic for matching generated paths to ground truth paths. **ALGORITHM**: Check if the generated path is a member of the set of `valid_paths` (BFS shortest paths) generated in T012b. **Depends on**: None.
- [X] T002 [Plan] Select model for CPU feasibility. **CRITICAL**: Select a primary candidate model, but MUST explicitly test and compare against a heavily quantized variant and a smaller-scale variant. **Deliverable**: `docs/model_selection.md` justifying the choice based on CPU memory footprint and inference speed benchmarks, explicitly comparing 1.5B vs 7B-quantized options as per FR-002. **Depends on**: None.
- [X] T003 [Plan] Design Mixed-Effects Logistic Regression (GLMM) structure with random intercepts for sequence_id. **Deliverable**: `docs/glmm_design.md` detailing the formula and stratification strategy. **Depends on**: T002.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T004a [P] Create root project directory structure. **Deliverable**: `setup.sh` containing explicit `mkdir -p` commands for `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/`, `tests/`, `data/`, `docs/`, `scripts/`, `results/`, `specs/001-entropy-validity-prediction/contracts/`, and subdirectories `src/`, `data/raw/`, `data/processed/`, `artifacts/`, `state/`. **Deliverable**: `setup.sh`.
- [X] T004b [P] Create verification script. **Deliverable**: `scripts/verify_structure.py` that checks all paths exist, exits with code 1 if missing. **Deliverable**: `scripts/verify_structure.py`.
- [X] T004c [P] Execute verification and generate log. **Deliverable**: `project_structure.log` containing a JSON array of objects: `[{"path": "str", "exists": bool, "timestamp": "ISO8601"}]`. **Deliverable**: `project_structure.log`. **Depends on**: T004a, T004b.
- [ ] T005 [P] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/requirements.txt` pinning versions for `transformers`, `torch`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `h5py`, `pytest`, `statsmodels`, `psutil`, `huggingface_hub`, `pymer4`, `minigrid`. **CRITICAL**: Must include Qwen1.5-1.5B and 7B-Int4 model compatibility. **Deliverable**: Valid `requirements.txt` file at `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/requirements.txt`.
- [ ] T006 [P] Configure linting (ruff) and formatting tools: Create `pyproject.toml` with black/ruff config, `.ruff.toml` for linter rules, and `.black.toml` for formatter settings. **Deliverable**: These three config files must exist and be valid.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007a [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/entropy_calc.py` with Shannon entropy logic ($-\sum p_i \log p_i$). **Input**: The function `calculate_entropy(probs)` MUST accept **softmax-normalized probability distributions (tensor)** of shape `[batch, vocab_size]` or `[vocab_size]` on **CPU**, clamp probability values < 1e-9 to 1e-9 *before* taking the logarithm to prevent log(0) errors, and return a float. **Semantic Test**: The function MUST correctly handle near-zero probability inputs by returning a finite value without crashing. **Deliverable**: Create `src/utils/entropy_calc.py` with function `calculate_entropy(probs)`.
- [X] T007b [P] [US1/US2] Create unit test `tests/unit/test_entropy_calc.py::test_clamp_prevents_log_zero` to verify the entropy calculation. **Test Input**: Use a tensor where one class has probability 0.0 (after softmax) and another has 1.0 (or near 1.0). **Expected Output**: Finite value. **Deliverable**: `tests/unit/test_entropy_calc.py` with the specific test case. **Depends on**: T007a.
- [ ] T008 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/validators.py` for schema validation (TokenSequence, EntropyProfile, ValidityLabel). **Deliverable**: `src/utils/validators.py` with validation functions.
- [ ] T009 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` with dataset capping and token batching functions. **CRITICAL**: This task implements `stream_batch(examples, max_examples=500)`. **Logic for `stream_batch`**: If `psutil.virtual_memory().percent > 90`, the function MUST **raise a RuntimeError** immediately to enforce single-sequence atomicity. **DO NOT** reduce batch size dynamically. The task MUST NOT attempt to adapt; it must fail loudly to force manual intervention or spec amendment. **Deliverable**: `src/data/preprocessing.py` with `stream_batch` function and `tests/integration/test_preprocessing.py` verifying the error handling.
- [ ] T010 [P] [US1/US2] [FR-001] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` to fetch GSM8K and MiniGrid from HuggingFace Datasets. **CRITICAL**: This task MUST enforce the **500-example cap per task** (GSM8K and MiniGrid) as required by FR-001 by default using `itertools.islice` within the streaming logic. **Constraint**: MUST NOT use `try/except` blocks that fall back to `generate_synthetic_*()` or `mock_*()` data. If `datasets.load_dataset` fails, the script MUST raise a `ConnectionError` or `FileNotFoundError` immediately to let the run fail loudly. **Dataset Config**: Must fetch 'train' split for GSMK and 'train' split for MiniGrid (specific subset). **Note**: The 500 cap is a maximum limit; if the source dataset is smaller, `islice` will return fewer examples. **Deliverable**: `src/data/download.py` with no synthetic fallbacks and explicit 500-example capping logic.
- [X] T011 [P] [US1/US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/.env.example` with keys for `HF_TOKEN`, `DATA_PATH`, `MODEL_PATH` and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/config.py` to load them. **Deliverable**: `.env.example` and `src/config.py`.
- [X] T012 [P] [US1/US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/dataset.schema.yaml` defining the schema for the merged dataset used in T019. **Deliverable**: `contracts/dataset.schema.yaml`.
- [ ] T012a [P] [Cross-Cut] Download Canonical Ground Truth (GSM8K/MiniGrid). **CRITICAL**: This task MUST fetch the *canonical* ground-truth solutions (GSM8K answer strings, MiniGrid goal states) from the HuggingFace datasets using `datasets.load_dataset`. It MUST NOT generate these from scratch. **Input**: HuggingFace dataset names. **Output**: `data/canonical_ground_truth.jsonl` with schema `{"prompt_id": str, "task_type": "gsm8k"|"minigrid", "canonical_solution": str, "start_state": str, "goal_state": str}`. **Constraint**: This task MUST run *before* T012b. **Deliverable**: `data/canonical_ground_truth.jsonl`. **Depends on**: T010.
- [ ] T012b [Cross-Cut] Generate BFS Paths for MiniGrid. **CRITICAL**: This task MUST use the `start_state` and `goal_state` from `data/canonical_ground_truth.jsonl` (T012a) to generate valid shortest paths for MiniGrid using Breadth-First Search (BFS) on the environment grid (version `minigrid>=2.3.0`). **Constraint**: This task MUST NOT generate ground truth for GSM8K (use canonical solution directly). **Output**: Append to `data/canonical_ground_truth.jsonl` with a new field `valid_paths: List[str]` for MiniGrid entries. **Deliverable**: Updated `data/canonical_ground_truth.jsonl`. **Depends on**: T012a.
- [ ] T012c [Cross-Cut] Verify Model Feasibility (1.5B, 7B-Int4). **CRITICAL**: This task MUST attempt to load the Qwen-1.5B model on CPU and measure peak RAM usage with a single forward pass of a fixed-length token sequence. **Criteria**: If peak RAM > 7GB, the task MUST **automatically switch** to Qwen1.5-7B-Int4 (heavily quantized). **CRITICAL**: If Qwen1.5-7B-Int4 also exceeds 7GB, the task MUST **raise a RuntimeError with code SPEC_VIOLATION** and abort. **DO NOT** switch to 0.5B. **Documentation**: MUST write `results/model_feasibility_report.json` with schema `{"model_used": str, "peak_ram_gb": float, "fallback_chain": ["1.5B", "7B-Int4"], "trigger_reason": "RAM > 7GB"}`. If the 0.5B model is mentioned, it MUST be flagged as "FORBIDDEN". **NO** manual spec amendment is required, but the task MUST abort. **Deliverable**: `results/model_feasibility_report.json`. **Depends on**: T005, T011. **Execution Note**: This task contains internal sequential logic (try 1.5B -> fallback -> abort) and MUST NOT run in parallel with other model-loading tasks. It is independent of T010 but must complete before T013.
- [ ] T012d [Cross-Cut] Diagnose Memory Failure Root Cause. **CRITICAL**: If T012c fails (raises SPEC_VIOLATION), this task MUST run a diagnostic to determine if the failure is due to intrinsic model size or a bug in the batching logic (T009/T024). **Input**: `results/model_feasibility_report.json`. **Output**: `results/memory_diagnosis.json` with root cause analysis. **Deliverable**: `results/memory_diagnosis.json`. **Depends on**: T012c (failure path).
- [ ] T012e [Cross-Cut] Handle Spec Violation (Abort). **CRITICAL**: If T012c aborts, this task MUST generate a `SPEC_VIOLATION_REPORT.md` detailing the inability to meet FR-002 constraints and flagging the project for manual review. **Deliverable**: `results/SPEC_VIOLATION_REPORT.md`. **Depends on**: T012c (failure path).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Generation and Ground Truth Labeling (Priority: P1) 🎯 MVP

**Goal**: Generate ground-truth token sequences for GSM8K and MiniGrid using a CPU-tractable model and label them with validity flags.

**Independent Test**: Run baseline generation on a subset of GSM8K problems; verify output log contains complete token sequences and binary validity flags against known solutions.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` model loading logic. **MUST** read `model_switch_flag.json` (from T012c). If `status: "pass"`, load **Qwen1.5-1.5B**. If `status: "fallback_7b_int4"`, load **Qwen1.5-7B-Int4**. If `status: "SPEC_VIOLATION"`, raise RuntimeError. **Deliverable**: `src/generation/generation.py` with `load_model` function. **Depends on**: T012c.
- [ ] T014 [US1] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` baseline generation loop. **MUST** perform a **full autoregressive forward pass** with `temperature=0.0` using the loaded model. **Deliverable**: `src/generation/generation.py` with `generate_baseline` function.
- [ ] T015 [US1] Implement ground truth matching logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py`. **MUST** label validity by **deterministic comparison** against the ground-truth solution using the **Semantic Alignment logic** defined in T001a/T001b. **Specifics**: Read `data/canonical_ground_truth.jsonl` (output of T012b). For GSM8K, validity is determined by **exact string match** with the `canonical_solution`. For MiniGrid, validity is determined by checking if the generated path is a **member of the `valid_paths` set** (BFS paths). **Input Schema**: `data/raw_generation.jsonl` (schema: `{"prompt_id": str, "tokens": List[str]}`); `data/canonical_ground_truth.jsonl`. **Output**: Write validity labels to `data/validity_labels.jsonl`. **CRITICAL**: `valid_paths` MUST be a JSON array of strings. **Deliverable**: `src/generation/generation.py` with `label_validity` function. **Depends on**: T012b, T014.
- [ ] T016 [US1] Create output writer for JSONL format in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` (TokenSequence, ValidityLabel). **Deliverable**: `src/generation/generation.py` with `write_jsonl` function.
- [ ] T017 [US1] Implement exception handling in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` for cases where no ground-truth path matches: **DO NOT** flag as 'ambiguous'. Instead, implement logic to label a token as "valid" if it matches *any* of the known valid ground-truth paths fetched dynamically from the T012b output. **CRITICAL**: The logic MUST iterate through ALL known valid paths for the specific `prompt_id`. If a match is found with *any* path, the token is marked "valid". Only if *no* path matches after checking all options should the token be marked "invalid" and a warning logged to `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/logs/generation.log` with JSON format `{"prompt_id": "...", "reason": "no_match", "validity": false, "timestamp": "..."}`. **Log level**: WARNING. **Rotation**: Use `RotatingFileHandler` with `maxBytes=10MB` and `backupCount=5` and path `logs/generation.log`. **Deliverable**: `src/generation/generation.py` with `label_validity` updated and logging verified. **Depends on**: T012b, T015.
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
- [ ] T024 [US2] Implement incremental token processing in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to process sequences **in chunks of 50 tokens** with an internal **50-token batching loop** for memory safety during entropy extraction. **CRITICAL**: This task MUST **reuse** the `token_batch_stream` function from T009 to ensure a single source of truth for memory management. **Input**: MUST read from `data/merged_us1.jsonl` (output of T019) and validate against `contracts/dataset.schema.yaml`. **Constraint**: MUST strictly output temporary batch files and MUST **NOT** perform the final merge. **File Format**: JSONL. **Naming Convention**: `temp_entropy_batch_{batch_id:04d}.jsonl` where `batch_id` is a **zero-padded sequential integer starting at 0**. **Directory**: `data/processed/temp_batches/` (create if missing). **Schema**: Each record MUST contain `prompt_id`, `token_index`, `sequence_length`, and `layer_entropy_map` (dict of layer_id: entropy_value) conforming to `contracts/entropy_profile.schema.yaml`. **CRITICAL**: This task MUST **strictly output temporary batch files** and MUST **NOT** perform the final merge; the merge is the **sole responsibility of T025**. **Note**: This task implements the 50-token internal batch constraint (FR-007) specifically for the entropy extraction step. Dataset row capping is handled in T010. **CRITICAL**: This task MUST handle **full sequences up to 512 tokens** in length, processing them in 50-token chunks **incrementally** (not loading full context). **Partial Batch Handling**: If a sequence length is not a multiple of a fixed chunk size, the last chunk MUST be processed as a smaller batch (e.g., a remainder of tokens) without error. **CRITICAL**: For each sequence processed, this task MUST write a `sequence_done_{prompt_id}.txt` marker file. **CRITICAL**: After all sequences are processed, this task MUST write a global `completion_marker.txt` file with content `DONE` (single line, no JSON). **Deliverable**: `src/generation/generation.py` with `process_batch` and `write_temp_batch` functions and `tests/integration/test_entropy_extraction.py::test_50_token_batching` verifying the batching logic. **Depends on**: T019, T022, T023.
- [ ] T025a [US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` logic to wait for completion. **CRITICAL**: This task MUST wait for the `data/processed/temp_batches/completion_marker.txt` file (created by T024) and verify that all expected `sequence_done_{prompt_id}.txt` markers exist before proceeding. **Deliverable**: `src/data/preprocessing.py` with `wait_for_completion` function. **Depends on**: T024.
- [ ] T025b [US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` logic to merge entropy profiles (from T024 temp batches) with the labeled dataset (from T019) into a single EntropyProfile record. **CRITICAL**: This task MUST perform a **3-way join** using `prompt_id` and `token_index` as keys: (1) `data/merged_us1.jsonl` (T019), (2) `data/processed/temp_batches/temp_entropy_batch_*.jsonl` (T024), and (3) the original US1 context. **CRITICAL**: This task is the **sole owner** of the final merge logic for the artifact `data/entropy_profiles_merged.jsonl`. **Deliverable**: Output file `data/entropy_profiles_merged.jsonl` validating against `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/entropy_profile.schema.yaml` and mandating preservation of layer-wise granularity. **Note: This task requires US1 (T019) and US2 (T024) to be complete. Explicitly depends on T025a.**
- [ ] T025c [US2] Implement cleanup logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` to delete `data/processed/temp_batches/` files after successful merge in T025b. **Deliverable**: `src/data/preprocessing.py` with `cleanup_temp_batches` function.
- [ ] T026 [US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` function `validate_entropy_profile()` that references `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/entropy_profile.schema.yaml` and raises ValueError if any layer/token in an EntropyProfile record is None or missing entropy values. **Deliverable**: On success, write `results/validation_report.json` with summary stats; on failure, exit with code 1. **Note**: This is the canonical implementation of `validate_entropy_profile`; T009 only creates the file infrastructure. **Depends on**: T025b.
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

- [ ] T030 [US3] [FR-004] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` using `pymer4` for **Mixed-Effects Logistic Regression (GLMM)** to predict token validity from entropy values, stratified by task type (GSM8K vs MiniGrid), and using **random intercepts for sequence_id** to handle nested data. **CRITICAL**: The implementation MUST support **BOTH** strategies: (1) `layer_index` as a continuous covariate, and (2) `layer_pooling` (early/mid/late). **Logic**: The code MUST check for layer sparsity. If **>50% of layers have <5 samples**, it MUST automatically switch to the pooling strategy (average early/mid/late layers). **Formula**: MUST be configurable via a `strategy` parameter. **Output**: MUST write results to `results/model_fitting.json` containing coefficients, p-values, and AUC-ROC. **Special Case**: If the dataset contains only one task type, the code MUST dynamically drop `task_type` from the formula to avoid `pymer4` errors. **CRITICAL**: If GLMM fails to converge (e.g., due to small dataset size), the code MUST fallback to a standard stratified logistic regression and log a warning, preserving the spec's methodological scope. **Deliverable**: `src/analysis/logistic_model.py` with `fit_model` function that returns coefficients, p-values, and AUC-ROC.
- [ ] T031 [US3] Implement stratification logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` (GSM8K vs MiniGrid, early/mid/late layer pooling or continuous covariate). **Deliverable**: `src/analysis/logistic_model.py` with stratification support.
- [ ] T032 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/threshold_opt.py` to find optimal entropy threshold minimizing weighted false positive/negative sum. **Output**: Write optimal threshold to `results/optimal_threshold.json`. **Deliverable**: `src/analysis/threshold_opt.py` with `optimize_threshold` function.
- [ ] T033 [US3] [FR-006] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/sensitivity.py` to **apply multiple-comparison correction (Bonferroni OR Benjamini-Hochberg)** and **perform the sensitivity sweep**. **Requirement**: The task MUST NOT enforce a hard pass/fail gate; non-significant results (FDR > alpha) are valid empirical outcomes and must be recorded with a `significant` flag set to False. **Requirement**: MUST accept a `--correction-method` CLI argument (choices: `bonferroni`, `benjamini-hochberg`) to select the method, with **`benjamini-hochberg` as the default**. **Requirement**: The task MUST **fail loudly (raise RuntimeError)** if the input data is empty, contains only one class, or if the correction logic fails. **Requirement**: Default `alpha` value for correction is set to a conventional significance level. **Input Structure**: `results/model_fitting.json` MUST be a list of dicts, each containing `p_value` and `hypothesis_id`. **Output Schema**: `results/fdr_report.json` with schema `{'adjusted_p_values': [{'hypothesis_id': str, 'p_value': float}], 'estimated_fdr': float, 'alpha': 0.05, 'significant': bool}`. **Metric Definition**: `estimated_fdr` is the proportion of rejected hypotheses expected to be false positives (calculated via BH procedure). **CRITICAL**: If `--correction-method=bonferroni` is selected, the `estimated_fdr` field MUST be set to `null` and a warning logged, as Bonferroni does not estimate FDR. **Sweep Logic**: MUST read the optimal point from `results/optimal_threshold.json` (T032) and the corrected p-values from `results/fdr_report.json` (T033). **Requirement**: Sweep range `[optimal - 0.1, optimal + 0.1]` with step size **0.01** (Citation: `arxiv.org/abs/2309.06305`), and **explicitly link the sweep results to the corrected p-values** to determine the optimal threshold under the corrected significance level (SC-003). **Output**: Write sweep results to `results/sensitivity_sweep.json`. **Deliverable**: `src/analysis/sensitivity.py` with `apply_correction` and `perform_sweep` functions. **Depends on**: T030, T032.
- [ ] T034 [US3] Implement logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` to catch p >= 0.05, log a warning, and return a result object with `significant=False` instead of crashing. **Deliverable**: Robust handling in `logistic_model.py`.
- [ ] T035 [US3] [SC-004] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/decay_analysis.py` to split the dataset into "short" and "long" subsets. **Requirement**: The task MUST implement a **decile-based split** (10th percentile vs 90th percentile) to ensure distinct regimes. If the 10th and 90th percentiles are too close (e.g., difference < 20 tokens), the task MUST fall back to a **fixed-threshold split** (<100 tokens vs >200 tokens). **Requirement**: The task MUST ALSO stratify by **task type (GSM8K vs MiniGrid)** and calculate/compute AUC-ROC for both subsets and both task types to measure decay of predictive power (SC-004). **Field**: MUST use the `sequence_length` field from the merged dataset. **Requirement**: The task MUST **fail loudly (raise RuntimeError)** if the input dataset is empty, if either subset has zero samples, or if AUC calculation fails. **Requirement**: If sequence length metadata is missing, raise an error. **Requirement**: The task MUST log the chosen split method (decile vs fixed) and justify it in the output report. **Deliverable**: `results/decay_analysis.json` containing AUC-ROC for short/long subsets, task types, and the difference metric. **Depends on**: T030.
- [ ] T036 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/checksum_recorder.py` to generate local checksums for all files in `data/` and record them in `state/projects/PROJ-881-llmxive-follow-up-extending-efficientrol.yaml` under `artifact_hashes`. **Schema**: `artifact_hashes` is a flat map of `relative_path: sha256_hash`. **`updated_at`**: ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`). **CRITICAL**: This task MUST **checksum the final merged artifact** (`data/entropy_profiles_merged.jsonl` from T025) directly. **Requirement**: The script MUST be **integrated into `main.py` as a post-pipeline hook** to run automatically after every pipeline stage, ensuring the `updated_at` timestamp is updated on every artifact change without manual intervention, satisfying Constitution Principle V. **Deliverable**: `scripts/checksum_recorder.py` and updated `state/...yaml`. **Depends on**: T025b.
- [ ] T037 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/report.py` to write `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/results/final_report.json` containing AUC-ROC, p-values, the recommended threshold from `threshold_opt.py`, the **estimated FDR** from `sensitivity.py` (T033), the **sensitivity sweep metrics** from `sensitivity.py` (T033), and the **decay analysis metrics** from `decay_analysis.py` (SC-004). **Requirement**: MUST check for existence of `results/fdr_report.json`, `results/sensitivity_sweep.json`, and `results/decay_analysis.json`. **Requirement**: MUST validate that these files contain **non-null, non-empty metric fields**. If files are missing OR contain invalid/empty metrics, **raise a RuntimeError**. **Requirement**: If files exist but contain valid non-significant results, the task MUST **accept them**. **Requirement**: MUST include a "Data Provenance" section with checksums from T036. **Deliverable**: `results/final_report.json` must contain all metrics required by SC-001 through SC-005. **Depends on**: T033, T035, T036.

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
- [ ] T045 [P] [US3] Implement `projects/llmxive-follow-up-extending-efficientrol/code/main.py` CLI and Pipeline: Define `argparse` arguments `--dataset`, `--model`, `--seed`, `--correction-method`, and **`--max-samples`** (default a substantial number). Implement `run_pipeline(args)` function that calls download, generation, and analysis modules sequentially based on `args`. Implement `handle_errors` decorator or wrapper for `run_pipeline` to catch and log exceptions. **Note**: The `--max-samples` argument allows testing the "maximum" constraint of FR-001 with different values. **Deliverable**: `main.py` with `parse_args`, `run_pipeline`, and `handle_errors` functions.
- [ ] T046 [P] Execute `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_quickstart.sh` to ensure all commands in `quickstart.md` run successfully in a fresh virtualenv.

---

## Phase 7: Data Integrity & Execution Safety (Revision Pass)

**Goal**: Address specific review concerns regarding data sourcing, streaming, and failure modes to prevent fabrication and ensure reproducibility.

- [ ] T047 [P] [Cross-Cut] Add a verification step in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_data_integrity.py` that compares the SHA-256 checksum of the downloaded dataset file against the hash recorded in `data/.checksums` (generated by T036), raising an error if they mismatch. **Note**: Do NOT attempt to fetch a dynamic "HuggingFace info hash" from the API; rely on the local manifest. **Deliverable**: `scripts/validate_data_integrity.py`.
- [ ] T048 [P] [Cross-Cut] Update `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/report.py` to include a "Data Provenance" section in `results/final_report.json` that lists the exact dataset version, sample size, streaming parameters, and **checksums from T036**, ensuring traceability from result back to raw data. **Requirement**: MUST depend on T036. **Deliverable**: `results/final_report.json` with Data Provenance section.
- [ ] T049 [P] [Cross-Cut] Modify `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/main.py` to ensure the `--max-samples` argument is passed to T010. **Note**: The cap is hardcoded to 500 by default in T010, but the CLI allows override for testing. **Deliverable**: `main.py` updated.
- [ ] T050 [P] [Cross-Cut] Modify `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` to explicitly check for and handle the case where the input dataset contains zero valid tokens or zero invalid tokens (perfect separation), logging a warning and skipping the logistic regression fit rather than crashing or returning NaNs. **Deliverable**: Robust handling in `logistic_model.py`.
- [ ] T051 [P] [Cross-Cut] [FR-001] Implement **streaming dataset loading** in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` using `datasets.load_dataset(..., streaming=True)` for GSM8K and MiniGrid to ensure the full dataset is processed without loading it entirely into RAM. **Requirement**: The implementation MUST iterate over the dataset in chunks (e.g., using `itertools.islice` or a custom generator) and write intermediate results to disk immediately. **Requirement**: If the full dataset cannot be processed within the compute budget (trigger: RAM usage > 7GB, detected via `psutil.virtual_memory().percent > 90`), the task MUST **raise a RuntimeError** and **require a formal amendment to the spec's scope** before proceeding. **CRITICAL**: Do NOT use synthetic or toy datasets as a fallback. **CRITICAL**: Do NOT implement a 'real sample' fallback that silently relaxes constraints. **Deliverable**: `src/data/download.py` with streaming logic and error handling that forces manual intervention on constraint violation.
- [ ] T052 [P] [Cross-Cut] Add a **verification step** in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_real_data.py` to ensure that all data used in the analysis originates from the verified real source (HuggingFace) and not from any synthetic or mock data. **Requirement**: The script MUST check the data files for any indicators of synthetic generation (e.g., specific patterns, checksums of known synthetic datasets) and raise an error if found. **Deliverable**: `scripts/validate_real_data.py` with validation logic and `results/validation_report.json` confirming data authenticity.
- [ ] T053 [P] [Cross-Cut] Implement **cap verification** in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/verify_cap.py` to run the download pipeline (T010) and verify that a representative set of examples is fetched per task (GSM8K, MiniGrid). **Requirement**: The script MUST also simulate a low-memory scenario (if possible) to verify the 'real sample' fallback logic triggers correctly when RAM > 7GB. **Deliverable**: `scripts/verify_cap.py` and `results/cap_verification_report.json`.
- [ ] T054 [P] [Cross-Cut] Document the model choice in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/docs/model_selection.md` explicitly stating that **Qwen1.5-1.5B** was chosen to match FR-002's 1.5B requirement (if feasible per T012c), and documenting any performance limitations observed on CPU. **Deliverable**: `docs/model_selection.md`.
- [ ] T055 [P] [Cross-Cut] Update `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/report.py` toexplicitly calculate and report the **estimated FDR** (proportion of rejected hypotheses expected to be false positives) in `results/final_report.json`, comparing it against the nominal alpha level (0.05 (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value)) as required by SC-005. **Deliverable**: `results/final_report.json` with explicit FDR comparison.
- [ ] T056 [P] [Cross-Cut] Implement **multi-path testing** in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_multi_path_labeling.py` to explicitly test the 'multiple valid paths' scenario for MiniGrid, ensuring the system correctly iterates through *all* known paths and does not prematurely flag a token as invalid. **Deliverable**: `tests/integration/test_multi_path_labeling.py`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0**: No dependencies - can start immediately (T001a, T001b are independent)
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