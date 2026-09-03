# Tasks: llmXive follow-up: extending "BlockPilot: Instance-Adaptive Policy Learning for Diffusion-based Spec"

**Input**: Design documents from `/specs/001-llmxive-blockpilot-extension/`
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

- [X] T001a [P] Create project root directory structure: `projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/`
- [X] T001b [P] Create data and test subdirectories: `data/raw/`, `data/processed/`, `data/models/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`
- [X] T001c [P] Create `specs/001-llmxive-blockpilot-extension/` directory

- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` dependencies (`transformers`, `datasets`, `scikit-learn`, `xgboost`, `torch`, `pandas`, `numpy`, `pyyaml`, `pytest`, `statsmodels`) and **pin versions** to ensure reproducibility (Constitution Principle I)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils/data_loader.py` with streaming support for GSMK and HumanEval using `datasets.load_dataset(..., streaming=True)`
- [X] T005 [P] Implement `code/utils/metrics.py` for latency calculation, accuracy, and correlation coefficient functions
- [X] T006 [P] Implement `code/utils/collinearity.py` for VIF calculation and residualization/PCA logic
- [X] T007 [P] Create base schemas in `contracts/` for `FeatureVector`, `GroundTruth`, `Prediction`, and `ModelArtifact` (Files: `contracts/feature_vector.schema.yaml`, `contracts/ground_truth.schema.yaml`, etc.)
- [X] T008 [P] Configure error handling and logging infrastructure in `code/main.py`
- [X] T009 [P] Setup environment configuration management for dataset paths and model weights (File: `code/config.py`)
- [X] T009a [US1] **FEASIBILITY CHECK**: Implement and run a mini-sweep on a SINGLE sample with a simplified loop (2 block sizes) to validate the CI time limit assumption. **Dependency**: Must run AFTER T004 (data_loader) and T005 (metrics) to ensure data and metrics are available. **Note**: This task does NOT depend on T012 implementation; it uses a simplified manual loop to estimate runtime. **Status**: Verified.
- [X] T048 [US1] **Explicitly Define Sample Size Limits**: Update `code/config.py` to define `MAX_SAMPLES_PER_DATASET = 500`. **Behavior**: Instead of raising an error, the system must gracefully truncate the dataset to the first `MAX_SAMPLES_PER_DATASET` rows if the input exceeds this limit. Log a warning: "Dataset truncated to first {N} samples per limit." **Dependency**: Must be completed before T012 execution.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ground Truth Generation via Exhaustive Sweep (Priority: P1) 🎯 MVP

**Goal**: Execute a complete inference sweep across block sizes $\{1, 2, 4, 8, 16, 32\}$ for every input sample to establish ground-truth optimal block size ($B^*$).

**Independent Test**: The system can be tested by running the sweep on a single sample from the GSM8K dataset and verifying that the output includes a mapped block size for every tested value and a clear winner ($B^*$).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for sweep output schema in `tests/contract/test_sweep_output.py`
- [X] T011 [P] [US1] Integration test for sweep logic on a single GSM8K sample in `tests/integration/test_sweep_logic.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/sweep.py` to execute exhaustive block-size sweep on CPU. **Note**: For LlamaB, reduce sample set to a feasible count due to compute constraints (see plan.md Scale/Scope).
- [ ] T013 [US1] Implement deterministic tie-breaking rule (select smallest block size) in `code/sweep.py`
- [ ] T014 [US1] Implement checkpoint/resume mechanism in `code/sweep.py` to handle -hour CI limit. **Criteria**: Checkpoint format JSONL, frequency at regular intervals, resume logic skips completed sample IDs. **Status**: Verified.
- [X] T015 [US1] Add validation to ensure sweep results are written to `data/processed/ground_truth.jsonl`
- [X] T016 [US1] Add error handling for OOM errors on larger block sizes (e.g., 32) with graceful fallback to reduce batch size to 1 or skip sample.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Static Feature Extraction (Priority: P2)

**Goal**: Extract static prefilling features (prompt length, mean attention entropy, hidden state norms) from the model's initial forward pass for every sample.

**Independent Test**: The system can be tested by processing a single prompt and verifying that the output vector contains exactly three numeric values corresponding to the defined features, with no latency exceeding a minimal threshold.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for feature vector schema in `tests/contract/test_feature_vector.py`
- [X] T019 [P] [US2] Integration test for feature extraction latency in `tests/integration/test_feature_latency.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/features.py` to extract prompt length, **mean attention entropy** (formula: `mean(-sum(p * log(p)))` across all layers, where masked tokens have probability 0 before normalization), and hidden state norms. Ensure NaN/Inf detection and handling (log warning, drop row from DataFrame, write excluded sample IDs to `data/processed/excluded_samples.log`). **Reference**: See spec.md Edge Cases for the definition.
- [X] T021 [US2] Implement latency measurement logic to ensure extraction ≤ 1ms per sample on a 2-core CPU runner (Spec FR-005).
- [ ] T022 [US2] Integrate feature extraction with `code/utils/data_loader.py` to process streamed data. **Dependency**: Must wait for T012 (Sweep) to complete if attempting to join results; otherwise, can run independently. **Note**: T031 is the sole task for joining data.
- [X] T023 [US2] Write extracted features to `data/processed/features.jsonl` linked to sample IDs

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Lightweight Policy Training and Validation (Priority: P3)

**Goal**: Train non-neural **regression** models (XGBoost, Random Forest, Decision Trees) on the collected (Feature, $B^*$) pairs and evaluate alignment with the ground truth across domains.

**Independent Test**: The system can be tested by training a Random Forest on a standard train/test split of the GSM8K data and evaluating on the held-out test set, reporting the prediction accuracy against the exhaustive sweep results.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for model artifact schema in `tests/contract/test_model_artifact.py`
- [X] T026 [P] [US3] Integration test for cross-domain generalization in `tests/integration/test_generalization.py`

### Implementation for User Story 3

- [X] T027b [US3] Implement `code/train.py` to train **Regression models** (XGBoost, Random Forest, Decision Trees) using the raw integer $B^*$ as the target label. **No Binning**: Do NOT bin block sizes into classes. **Metrics**: Use Mean Squared Error (MSE), R², and Pearson/Spearman correlation coefficient between predicted $B^*$ and actual $B^*$. **Requirement**: Report all three metrics. **Verification**: Confirm that regression metrics are reported.
- [X] T027c [US3] Implement metric calculation logic in `code/train.py` to compute Pearson/Spearman correlation coefficients and log them to `data/processed/metrics.json`. **Verification**: Ensure correlation coefficients are calculated and logged.
- [X] T028 [US3] Implement VIF handling in `code/train.py` to decorrelate features if VIF > 5
- [ ] T029 [US3] Implement `code/evaluate.py` to calculate **regression metrics** (MSE, R²) on held-out data and generalization gap.
- [ ] T030 [US3] Implement cross-architecture validation in `code/evaluate.py` with **explicit bidirectional tests**: Train Qwen->Test Llama AND Train Llama->Test Qwen. **Verification**: Ensure metrics are reported for both directions and that a failure to generalize in either direction constitutes a rejection of the hypothesis per Constitution Principle VI.
- [X] T031 [US3] **Join Ground Truth and Features**: Implement logic to join `ground_truth.jsonl` and `features.jsonl` into a unified training dataset `data/processed/training_set.jsonl`. **Logic**: Filter for samples that have both Features and Ground Truth (excluding OOM sweep failures). **Dependency**: Must run AFTER T012 and T022. **Note**: T031 does NOT depend on T031a.
- [X] T031a [US3] **Implement Uncertainty Data Generation**: Implement `code/uncertainty.py` to run a separate greedy inference pass (temperature=0.0, top_p=1.0) using the same model architecture as T012. **Isolation**: Must run in a distinct process with `torch.no_grad()` and a distinct seed, reloading model weights to ensure no gradient sharing with the sweep process. Generate ground truth perplexity and output entropy for each sample, writing to `data/processed/uncertainty_metrics.jsonl`. **Output Schema**: {sample_id, perplexity, output_entropy}. **Verification**: Validate that the greedy pass uses a distinct seed and no gradient sharing to confirm independence from the sweep process. **Dependency**: Must run after T012 (Sweep) to ensure model compatibility, but does not depend on sweep results.
- [X] T031b [US3] **Orchestrate Uncertainty Pass**: Implement logic in `code/main.py` to invoke `code/uncertainty.py` as a distinct subprocess after T012 and T022 complete, ensuring the data is generated before T032.
- [ ] T031c [US3] **Verify Uncertainty Isolation**: Add a check in `code/main.py` or `code/evaluate.py` to confirm that `uncertainty_metrics.jsonl` was generated by a distinct process (e.g., check for distinct seed in log headers or process ID).
- [ ] T032 [US3] **Implement Correlation Calculation**: Implement correlation calculation between predicted $B^*$ and the **generated perplexity/output entropy data** (FR-006) in `code/evaluate.py`. **Verification**: Explicitly compute the Pearson/Spearman correlation coefficient and p-value. Log a pass/fail status based on statistical significance (p-value < 0.05) to satisfy SC-006. **Dependency**: Requires T031 (joined dataset) and T031a (uncertainty metrics).
- [X] T033 [US3] **Generate Feature Importance**: Generate feature importance scores and correlation coefficients for reporting.
- [X] T034 [US3] Write model artifacts to `data/models/` and evaluation results to `data/processed/results.json`
- [X] T035 [US3] **Generate Feature Importance Ranking**: Calculate feature importance scores from the trained regression model (T027b), rank features by importance, and perform a statistical comparison against the hypothesis that 'attention entropy' is the dominant predictor. Output the ranking and comparison analysis to `data/processed/feature_importance.json`. **Verification**: Assert that the analysis includes the rank of 'attention entropy' and a comparison to the baseline hypothesis, rather than just an assertion of the result. **Dependency**: Requires trained model from T027b and feature data availability (requires T031 completion).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Natural Language Domain Extension (Priority: P3)

**Goal**: Extend the pipeline to include the "natural language" domain (CommonCrawl/Dolly) to satisfy FR-004 and SC-002.

- [ ] T047 [US3] **Process Natural Language Domain**: Implement `code/sweep.py` and `code/features.py` logic for the CommonCrawl/Dolly dataset. **Steps**: Run sweep (T012 logic) and extract features (T020 logic) for the natural language domain. **Dependency**: Must run AFTER T012 and T020 are implemented and verified. **Output**: Append natural language data to `data/processed/ground_truth.jsonl` and `data/processed/features.jsonl`.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Documentation updates in `docs/` and `README.md`
- [X] T037 Code cleanup and refactoring
- [X] T038 Performance optimization across all stories (ensure CPU latency targets)
- [X] T039 [P] Additional unit tests in `tests/unit/`
- [X] T040 [P] Run `quickstart.md` validation and final contract checks
- [X] T041 Verify all metrics are labeled as "preliminary" or "exploratory" in the report

---

## Phase O: Review Resolution & Data Integrity (Revision Pass)

**Purpose**: Address specific reviewer concerns regarding data sourcing, failure modes, and execution order identified in the analysis phase.

- [ ] T042 [US1] **Enforce Real Data Source Only**: Update `code/utils/data_loader.py` to remove ANY `try/except` blocks or fallback logic that substitutes synthetic/mock data if a real fetch fails. Implement a strict `raise` on fetch failure to ensure the pipeline fails loudly rather than fabricating data.
- [ ] T043 [US1] **Implement Streaming for Large Datasets**: Update `code/utils/data_loader.py` to use `datasets.load_dataset(..., streaming=True)` for CommonCrawl or large subsets, ensuring processing happens in chunks to fit within 7GB RAM. **Log Schema**: Write `data/processed/streaming_config.log` as a JSON object with keys: `dataset`, `chunk_size`, `batch_size`, `streaming_mode`, `timestamp`. **Parameters**: Use `chunk_size=1000`, `batch_size=32`. **Verification**: Confirm the log file exists after the first run.
- [ ] T045 [US3] **Add Cross-Architecture Validation Task**: Explicitly add a task to `code/evaluate.py` to run the "Train Llama -> Test Qwen" validation path, ensuring the bidirectional requirement from Plan.md (Phase 3, Task T030) is executed and logged.
- [ ] T046 [US3] **Verify Uncertainty Correlation**: Ensure `code/evaluate.py` (T032) explicitly calculates the Pearson/Spearman correlation between the predicted block size and the perplexity from `uncertainty_metrics.jsonl`, logging the coefficient and p-value to `data/processed/correlation_report.json`.
- [ ] T049 [US2] **Add Explicit NaN/Inf Handling Logic**: In `code/features.py`, implement a specific fallback mechanism for attention entropy calculation that detects `NaN` or `Inf` values, logs a warning with the sample ID, and **drops the row from the DataFrame**, writing the excluded sample ID to `data/processed/excluded_samples.log`, ensuring data integrity per the "fail loudly" principle.
- [ ] T050 [US3] **Document Statistical Significance Thresholds**: Update `code/evaluate.py` to explicitly log the p-value threshold (0.05) used for correlation significance (FR-006) and the F1-score baseline used for generalization assessment, ensuring the "exploratory" nature of the results is clearly documented in the output reports.

## Phase P: Execution Order & Data Flow Correction (Revision Pass)

**Purpose**: Resolve critical data flow dependency issues where verification tasks were scheduled before data generation tasks.

- [X] T051a [US3] **Implement Main Orchestration**: Modify `code/main.py` to enforce the strict execution sequence: `Sweep (T012) -> Features (T020) -> Uncertainty (T031a) -> Join (T031) -> Train (T027b) -> Evaluate (T032)`. Ensure that T031a is invoked as a subprocess before T032 attempts to read its output.
- [X] T051b [US3] **Verify Execution Order**: Add a logging mechanism in `code/main.py` that writes the execution order to `data/processed/execution_log.json` and asserts that the order matches the required sequence.
- [ ] T052 [US3] **Validate Join Logic**: Modify `code/evaluate.py` to add a function `validate_uncertainty_input()` that checks for the existence and non-zero row count of `data/processed/uncertainty_metrics.jsonl` before attempting correlation calculations. If missing or empty, raise a `FileNotFoundError` with the message: "Uncertainty metrics missing. Ensure T031a (Uncertainty Data Generation) has completed successfully."
- [ ] T053 [US3] **Streamed Data Verification**: Add a unit test `tests/unit/test_data_loader.py::test_streaming_params_logged` which asserts that `datasets.load_dataset` is called with `streaming=True` and that `data/processed/streaming_config.log` contains the keys `chunk_size=1000` and `batch_size=32` after execution.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T009a (Feasibility)** must run after T004/T005 but before T012 execution.
 - **T048 (Sample Limit)** must be completed before T012 execution.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - **T031a (Uncertainty Data)** must run before **T032 (Correlation)**
 - **T031 (Join)** must run before **T032 (Correlation)** to provide the joined context.
 - **T047 (Natural Language)** depends on **T012** and **T020**.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for sweep output schema in tests/contract/test_sweep_output.py"
Task: "Integration test for sweep logic on a single GSM8K sample in tests/integration/test_sweep_logic.py"

# Launch all models for User Story 1 together:
Task: "Implement code/sweep.py to execute exhaustive block-size sweep on CPU"
Task: "Implement deterministic tie-breaking rule in code/sweep.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - **Run T009a (Feasibility)** before proceeding to T012 execution
 - **Ensure T048 (Sample Limit)** is implemented before T012 execution
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
