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

- [ ] T001 [P] Create project directory structure: Create `setup.sh` containing explicit `mkdir -p` commands for all listed paths (`projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/`, `tests/`, `data/`, `docs/`, `scripts/`, `results/`, `specs/001-entropy-validity-prediction/contracts/`). The script must check that all paths exist after creation; if any are missing, it must exit with code 1 and print "Structure creation failed". If all exist, it must print "Structure created" and generate `project_structure.log` confirming directory existence. **Deliverable**: `setup.sh` and `project_structure.log`.
- [ ] T002 [P] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/requirements.txt` pinning versions for `transformers`, `torch`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `h5py`, `pytest`, `statsmodels`, `psutil`, `huggingface_hub`. **Deliverable**: Valid `requirements.txt` file.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `pyproject.toml` with black/ruff config, `.ruff.toml` for linter rules, and `.black.toml` for formatter settings. **Deliverable**: These three config files must exist and be valid.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/entropy_calc.py` with Shannon entropy logic ($-\sum p_i \log p_i$). MUST clamp probability values < 1e-9 to 1e-9 *before* taking the logarithm to prevent log(0) errors. **Deliverable**: Create `src/utils/entropy_calc.py` with function `calculate_entropy(logits)` returning a float, and unit test `tests/unit/test_entropy_calc.py::test_clamp_prevents_log_zero` asserting the function returns a finite value for input logits resulting in p=0.0.
- [ ] T005 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/validators.py` for schema validation (TokenSequence, EntropyProfile, ValidityLabel). **Deliverable**: `src/utils/validators.py` with validation functions.
- [ ] T006 [P] [US1/US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` with batched streaming mechanism. MUST implement logic to process sequences in fixed batches of a manageable token count. If `MemoryError` is caught, the logic MUST reduce the batch size by a significant margin and retry. **Deliverable**: `src/data/preprocessing.py` with `stream_batch` function and `tests/integration/test_preprocessing.py::test_memory_backoff` verifying the fallback.
- [X] T007 [P] [US1] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` to fetch GSM8K and MiniGrid from HuggingFace Datasets with a representative subset limit. **Deliverable**: `src/data/download.py` with no synthetic fallbacks.
- [ ] T008 [P] [US1/US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/.env.example` with keys for `HF_TOKEN`, `DATA_PATH`, `MODEL_PATH` and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/config.py` to load them. **Deliverable**: `.env.example` and `src/config.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Generation and Ground Truth Labeling (Priority: P1) 🎯 MVP

**Goal**: Generate ground-truth token sequences for GSM8K and MiniGrid using a CPU-tractable model and label them with validity flags.

**Independent Test**: Run baseline generation on a subset of GSM8K problems; verify output log contains complete token sequences and binary validity flags against known solutions.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` baseline generation logic (single-pass, no GPU, temperature 0.0). **Deliverable**: `src/generation/generation.py` with `generate_baseline` function.
- [ ] T012 [US1] Implement ground truth matching logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` (handle multiple valid paths for MiniGrid). **Deliverable**: `src/generation/generation.py` with `label_validity` function.
- [~] T013 [US1] Create output writer for JSONL format in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` (TokenSequence, ValidityLabel). **Deliverable**: `src/generation/generation.py` with `write_jsonl` function.
- [~] T014 [US1] Implement exception handling in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` for cases where no ground-truth path matches: **DO NOT** flag as 'ambiguous'. Instead, implement logic to label a token as "valid" if it matches *any* of the known valid ground-truth paths. If no match is found after checking all paths, log a warning to `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/logs/generation.log` with JSON format `{"prompt_id": "...", "reason": "no_match"}` and retain the data point with `validity=false`. **Deliverable**: `src/generation/generation.py` with `label_validity` updated and logging verified.
- [X] T015 [US1] Configure `logging` in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to output JSON-formatted logs to `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/logs/generation.log` including token counts and validity distribution stats. **Deliverable**: `logs/generation.log` with JSON entries.
- [~] T016 [US1] Implement merging logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to combine generation outputs (T011) with ground truth labels (T012) into a single labeled dataset. **Deliverable**: Output file `data/merged_dataset.jsonl` with fields `['prompt_id', 'tokens', 'validity', 'entropy']` (entropy placeholder for now), validating against `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/dataset.schema.yaml`. **Depends on T011-T015**.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Note: T009/T010 depend on T005 (Schema) and T016 (Merged Data) being conceptually complete.**

- [~] T009 [P] [US1] Contract test for dataset schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_dataset_schema.py`. **Deliverable**: `tests/contract/test_dataset_schema.py::test_schema_validation_fails_on_missing_field` that loads `contracts/dataset.schema.yaml` and asserts `ValueError` is raised for a record missing the `validity` field. **Depends on T005**.
- [X] T010 [US1] Integration test for ground truth labeling in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_ground_truth_labeling.py`. **Deliverable**: `tests/integration/test_ground_truth_labeling.py` verifying multi-path matching. **Depends on T016** (Output Writer/Merging).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Intermediate State Extraction and Entropy Calculation (Priority: P2)

**Goal**: Re-run baseline sequences with instrumentation to capture probability distributions and calculate Shannon entropy at every intermediate layer.

**Independent Test**: Re-run a subset of sequences with instrumentation; verify output log contains entropy values for every layer and token position with no missing values.

### Implementation for User Story 2

- [~] T019 [P] [US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` hooks to capture layer-wise probability distributions. **Deliverable**: `src/generation/generation.py` with forward hooks.
- [~] T020 [US2] Integrate `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/entropy_calc.py` to compute entropy vectors for each token position. **Implementation Detail**: Register a forward hook in `generation.py` that captures the output of each intermediate layer, passes the logits to `entropy_calc.calculate_entropy()`, and stores the result in the token's metadata. **Deliverable**: `src/generation/generation.py` updated.
- [~] T021 [US2] Implement streaming/chunking logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to process fixed-size token batches of 50 tokens and **write to disk immediately after each batch** to stay within 7GB RAM limit. **Deliverable**: `src/generation/generation.py::process_batch` that appends JSONL records to `data/entropy_profiles.jsonl` after every 50 tokens using `json.dumps` with `newline` delimiter, verified by `tests/integration/test_generation.py::test_streaming_writes`.
- [~] T035 [P] Profile `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` using `cProfile` and verify RAM usage stays < 6.5GB for sequences up to 500 tokens processed in batches of 50 tokens. **Deliverable**: Run `cProfile` on `src/generation/generation.py` with 500-token sequences, extract peak RSS using `tracemalloc`, and write `results/profile_report.txt` containing a table of `['Batch Size', 'Peak RSS (MB)', 'Avg Latency (s)']`. **Depends on T021**.
- [~] T022 [US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` logic to merge entropy profiles (from T021) with the labeled dataset (from T016) into a single EntropyProfile record. **Deliverable**: Output file `data/entropy_profiles_merged.jsonl` validating against `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/entropy_profile.schema.yaml` and mandating preservation of layer-wise granularity. **Note: This task requires US1 (T016) to be complete.**
- [~] T023 [US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` function `validate_entropy_profile()` that references `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/entropy_profile.schema.yaml` and raises ValueError if any layer/token in an EntropyProfile record is None or missing entropy values. **Deliverable**: On success, write `results/validation_report.json` with summary stats; on failure, exit with code 1.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for entropy profile schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_entropy_profile_schema.py`.
- [X] T018 [P] [US2] Integration test for intermediate state extraction in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_entropy_extraction.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Signal Decay Analysis and Threshold Optimization (Priority: P3)

**Goal**: Fit logistic regression models to predict token validity from entropy values and identify optimal entropy thresholds.

**Independent Test**: Run analysis on combined dataset; verify logistic regression fit, AUC-ROC calculation, p-value reporting, and threshold optimization.

### Implementation for User Story 3

- [X] T026 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` using `statsmodels` for **Standard Logistic Regression** (NOT GLMM) to predict token validity from entropy values, stratified by task type (GSM8K vs MiniGrid), and pooling layers into early/mid/late groups or using layer index as a continuous covariate. **Note**: GLMM is deferred to future work if standard regression fails. **Depends on T022** (Merged Data) and **T023** (Validated EntropyProfile).
- [~] T027 [US3] Implement stratification logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` (GSM8K vs MiniGrid, early/mid/late layer pooling or continuous covariate). **Deliverable**: `src/analysis/logistic_model.py` with stratification support.
- [~] T028 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/threshold_opt.py` to find optimal entropy threshold minimizing weighted false positive/negative sum. **Deliverable**: `src/analysis/threshold_opt.py` with `optimize_threshold` function.
- [~] T029 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/sensitivity.py` to first **apply multiple-comparison correction (Benjamini-Hochberg method)** to p-values, then calculate the resulting False Discovery Rate (FDR), and compare against nominal alpha level (0.05) to verify SC-005. **Deliverable**: `src/analysis/sensitivity.py::apply_correction` using BH method, returning a dict `{'adjusted_p_values': [...], 'fdr': float}` and writing `results/fdr_report.json`.
- [X] T030 [US3] Implement logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` to catch p >= 0.05, log a warning, and return a result object with `significant=False` instead of crashing. **Deliverable**: Robust error handling in `logistic_model.py`.
- [ ] T031 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/report.py` to write `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/results/final_report.json` containing AUC-ROC, p-values, the recommended threshold from `threshold_opt.py`, and the **FDR metric** from `sensitivity.py`. **Deliverable**: `results/final_report.json` must contain all metrics required by SC-001 through SC-005.

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
- [ ] T037 [P] Implement input validation in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` to reject non-HuggingFace URLs and add a PII scan script `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/pii_scan.py` that checks `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/data/` for regex patterns.
- [ ] T038 [P] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/main.py` orchestration script with CLI arguments `--dataset`, `--model`, `--seed` and logic to call download, generation, and analysis modules sequentially.
- [ ] T039 [P] Execute `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_quickstart.sh` to ensure all commands in `quickstart.md` run successfully in a fresh virtualenv.

---

## Phase 7: Data Integrity & Execution Safety (Revision Pass)

**Goal**: Address specific review concerns regarding data sourcing, streaming, and failure modes to prevent fabrication and ensure reproducibility.

- [ ] T040 [P] [US1/US2] Refactor `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` to remove ALL `try/except` blocks that fall back to `generate_synthetic_*()` or `mock_*()` data. If `datasets.load_dataset` or `hf_hub_download` fails, the script MUST raise a `ConnectionError` or `FileNotFoundError` immediately to let the run fail loudly. **Deliverable**: `src/data/download.py` with no fallbacks and `tests/unit/test_download.py::test_fail_loudly_on_network_error` asserting `ConnectionError` is raised when HuggingFace is unreachable.
- [ ] T041 [P] [US2] Update `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to implement explicit streaming logic using `datasets.load_dataset(..., streaming=True)` for GSM8K and MiniGrid, processing data in chunks of 500 rows **with a hard stop after 500 total examples** to ensure compliance with FR-001. **Deliverable**: `src/generation/generation.py` with streaming logic enforcing 500-example cap.
- [ ] T042 [US2] Add a `--sample-size` CLI argument to `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/main.py` that, if provided, uses `itertools.islice` to take a deterministic random sample from the streamed dataset, explicitly logging the sample size and seed in `results/final_report.json`. **Constraint**: The effective sample size MUST be `min(user_input, 500)` to enforce FR-001. **Deliverable**: `main.py` with `--sample-size` argument enforcing cap.
- [ ] T043 [P] [US3] Modify `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` to explicitly check for and handle the case where the input dataset contains zero valid tokens or zero invalid tokens (perfect separation), logging a warning and skipping the logistic regression fit rather than crashing or returning NaNs. **Deliverable**: Robust handling in `logistic_model.py`.
- [ ] T044 [P] [US1/US2] Add a verification step in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_data_integrity.py` that compares the checksum of the downloaded dataset against the HuggingFace dataset info hash, raising an error if they mismatch. **Deliverable**: `scripts/validate_data_integrity.py`.
- [ ] T045 [P] [US3] Update `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/report.py` to include a "Data Provenance" section in `results/final_report.json` that lists the exact dataset version, sample size, and streaming parameters used, ensuring traceability from result back to raw data. **Deliverable**: `results/final_report.json` with Data Provenance section.
- [ ] T046 [P] [US1/US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/checksum_recorder.py` to generate local checksums for all files in `data/` and record them in `state/projects/PROJ-881-llmxive-follow-up-extending-efficientrol.yaml` under `artifact_hashes`. **Deliverable**: `scripts/checksum_recorder.py` and updated `state/...yaml`.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 for validation, but implementation is independent
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires data from US1 and US2, but implementation is independent

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