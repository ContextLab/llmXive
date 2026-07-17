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

- [ ] T001 Create project directory structure: create directories `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/`, `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/`, `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/data/`, `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/docs/`, `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/`, `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/results/`, and `specs/001-entropy-validity-prediction/contracts/`
- [ ] T002 Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/requirements.txt` pinning versions for `transformers`, `torch`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `h5py`, `pytest`, `statsmodels`
- [ ] T003 Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/entropy_calc.py` with Shannon entropy logic ($-\sum p_i \log p_i$). MUST clamp probability values < 1e-9 to 1e-9 *before* taking the logarithm to prevent log(0) errors (high confidence error edge case).
- [X] T005 [P] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/validators.py` for schema validation (TokenSequence, EntropyProfile, ValidityLabel)
- [X] T006 [P] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` with batched streaming mechanism. MUST set default batch size to 50 tokens and include a validation check that rejects any batch size > 50 to enforce the 7GB RAM limit per FR-007.
- [X] T007 [P] Implement `projects/PROJ-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` to fetch GSM8K and MiniGrid from HuggingFace Datasets with a representative subset limit
- [X] T008 [P] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/.env.example` with keys for `HF_TOKEN`, `DATA_PATH`, `MODEL_PATH` and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/config.py` to load them

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Generation and Ground Truth Labeling (Priority: P1) 🎯 MVP

**Goal**: Generate ground-truth token sequences for GSM8K and MiniGrid using a CPU-tractable model and label them with validity flags.

**Independent Test**: Run baseline generation on a subset of GSM8K problems; verify output log contains complete token sequences and binary validity flags against known solutions.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Note: T009/T010 depend on T005 (Schema) and T016 (Merged Data) being conceptually complete.**

- [X] T009 [US1] Contract test for dataset schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_dataset_schema.py`. **Depends on T005** (Schema Validation).
- [X] T010 [US1] Integration test for ground truth labeling in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_ground_truth_labeling.py`. **Depends on T016** (Output Writer/Merging).

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` baseline generation logic (single-pass, no GPU, temperature 0.0)
- [X] T012 [US1] Implement ground truth matching logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` (handle multiple valid paths for MiniGrid)
- [X] T013 [US1] Create output writer for JSONL format in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` (TokenSequence, ValidityLabel)
- [X] T014 [US1] Implement exception handling in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` for cases where no ground-truth path matches: flag validity as 'ambiguous', log specific reason, and retain data point for analysis
- [X] T015 [US1] Configure `logging` in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to output JSON-formatted logs to `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/logs/generation.log` including token counts and validity distribution stats
- [ ] T016 [US1] Implement merging logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to combine generation outputs (T011) with ground truth labels (T012) into a single labeled dataset, explicitly referencing `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/dataset.schema.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Intermediate State Extraction and Entropy Calculation (Priority: P2)

**Goal**: Re-run baseline sequences with instrumentation to capture probability distributions and calculate Shannon entropy at every intermediate layer.

**Independent Test**: Re-run a subset of sequences with instrumentation; verify output log contains entropy values for every layer and token position with no missing values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for entropy profile schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_entropy_profile_schema.py`
- [X] T018 [P] [US2] Integration test for intermediate state extraction in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_entropy_extraction.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` hooks to capture layer-wise probability distributions
- [X] T020 [US2] Integrate `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/entropy_calc.py` to compute entropy vectors for each token position <!-- FAILED: unspecified -->
- [X] T021 [US2] Implement streaming/chunking logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` to process fixed-size token batches of 50 tokens and **write to disk immediately after each batch** to stay within 7GB RAM limit
- [ ] T022 [US2] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` logic to merge entropy profiles (from T021) with the labeled dataset (from T016) into a single EntropyProfile record, explicitly referencing `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/entropy_profile.schema.yaml` and mandating preservation of layer-wise granularity. **Note: This task requires US1 (T016) to be complete.**
- [ ] T023 [US2] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py` function `validate_entropy_profile()` that references `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/contracts/entropy_profile.schema.yaml` and raises ValueError if any layer/token in an EntropyProfile record is None or missing entropy values

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Signal Decay Analysis and Threshold Optimization (Priority: P3)

**Goal**: Fit logistic regression models to predict token validity from entropy values and identify optimal entropy thresholds.

**Independent Test**: Run analysis on combined dataset; verify logistic regression fit, AUC-ROC calculation, p-value reporting, and threshold optimization.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for analysis result schema in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/contract/test_analysis_result_schema.py`
- [X] T025 [P] [US3] Integration test for threshold optimization in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/integration/test_threshold_optimization.py`

### Implementation for User Story 3

- [X] T026 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` using `statsmodels` for **Mixed-Effects Logistic Regression (GLMM)** with random intercepts for sequences to handle nested data. **Depends on T022** (Merged Data) and **T023** (Validated EntropyProfile). **Note: This task requires T022 (Merged Data) to be complete.**
- [X] T027 [US3] Implement stratification logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` (GSM8K vs MiniGrid, early/mid/late layer pooling or continuous covariate)
- [X] T028 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/threshold_opt.py` to find optimal entropy threshold minimizing weighted false positive/negative sum
- [X] T029 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/sensitivity.py` to first **apply multiple-comparison correction (Bonferroni/BH)** to p-values, then calculate the resulting False Discovery Rate (FDR), and compare against nominal alpha level (0.05) to verify SC-005
- [X] T030 [US3] Implement logic in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py` to catch p >= 0.05, log a warning, and return a result object with `significant=False` instead of crashing
- [ ] T031 [US3] Implement `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/report.py` to write `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/results/final_report.json` containing AUC-ROC, p-values, and the recommended threshold from `threshold_opt.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Update `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/README.md` with CLI usage examples
- [ ] T033 [P] Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/docs/api.md` with docstrings for `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/logistic_model.py`
- [ ] T034 [P] Run `ruff check --fix` and `black.` on the entire `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/` directory and resolve all linting errors
- [ ] T035 Profile `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py` using `cProfile` and verify RAM usage stays < 6.5GB for sequences up to 500 tokens processed in batches of 50 tokens
- [ ] T036 [P] Add unit tests in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/unit/test_entropy_calc.py` covering edge cases (log(0), empty input) and `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/tests/unit/test_validators.py` for schema validation
- [ ] T037 Implement input validation in `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py` to reject non-HuggingFace URLs and add a PII scan script `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/pii_scan.py` that checks `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/data/` for regex patterns
- [ ] T038 Create `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/main.py` orchestration script with CLI arguments `--dataset`, `--model`, `--seed` and logic to call download, generation, and analysis modules sequentially
- [ ] T039 Execute `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/scripts/validate_quickstart.sh` to ensure all commands in `quickstart.md` run successfully in a fresh virtualenv

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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Integration test for ground truth labeling in tests/integration/test_ground_truth_labeling.py"

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