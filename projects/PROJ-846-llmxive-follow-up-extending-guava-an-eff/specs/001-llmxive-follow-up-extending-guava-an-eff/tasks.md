# Tasks: llmXive follow-up: extending "Guava: An Effective and Universal Harness for Embodied Manipulation"

**Input**: Design documents from `/specs/001-symbolic-guava-perception/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Methodological Alignment Notice**:
> **CRITICAL CONFLICT RESOLUTION**: The Spec (FR-004, SC-001) explicitly mandated a comparison between the Symbolic-Guava agent and the **Baseline-Guava (Visual)** agent as the **PRIMARY** research question. The Plan.md (Summary & Complexity Tracking) proposed a "Critical Methodological Shift" to use an "Oracle-Symbolic" agent as the primary baseline.
> **Resolution**: Per the Constitution (Single Source of Truth), the **Spec is the binding authority** for research success criteria. The Plan's proposed shift is a contradiction that invalidates the Spec's success criteria.
> **Implementation Directive**:
> 1. **Primary Baseline**: The **Baseline-Guava (Visual)** agent (T032b) is the **PRIMARY** comparison target. T036b (Permutation Test) compares Symbolic vs. Visual.
> 2. **Secondary Baseline**: The "Oracle-Symbolic" agent (T032c) is implemented as a **SECONDARY/DIAGNOSTIC** tool only.
> 3. **Plan Status**: The Plan.md is flagged for **KICKBACK** to align with the Spec. The implementation MUST follow the Spec's Visual Baseline requirement.
> 4. **Baseline Unavailable**: If the Visual Baseline model is missing, T032b **HALTS** the project with exit code 1. The research question cannot be answered without the baseline.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] [US0] [FR-000] [Constitution-I] [Constitution-V] Initialize Git Repository. **Action**: Create `.gitignore` (patterns: `*.pyc`, `__pycache__`, `.env`, `data/raw/*`, `data/artifacts/*`, `*.log`, `*.pth`), run `git init`, `git add.`, `git commit -m "Initial commit"`. **Verify**: `.git` directory exists and commit history contains one entry. **Depends on**: None.

- [ ] T002a [P] [US0] [FR-000] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/requirements.txt` with pinned dependencies: `opencv-python==4.8.0.74`, `onnxruntime==1.16.0`, `datasets==2.14.0`, `transformers==4.35.0`, `torch==2.1.0`, `scikit-learn==1.3.0`, `pandas==2.1.0`, `numpy==1.26.0`, `pytest==7.4.0`, `radon==6.0.1`, `huggingface_hub==0.19.0`. **Depends on**: None.
- [ ] T002b [P] [US0] [FR-000] Verify dependencies install successfully in a clean virtualenv. **Action**: Run `pip install -r requirements.txt` in a temporary venv. **Verify**: No errors, all packages listed in `pip freeze`. **Depends on**: T002a.

- [ ] T003a [P] [US0] [FR-000] Create `.ruff.toml` configuration file with content: `max-line-length = 100`, `select = ["E", "F", "I"]`. **Verify**: Run `ruff check --exit-zero` successfully. **Depends on**: None.
- [X] T003b [P] [US0] [FR-000] Create `pyproject.toml` configuration for `black` formatting tool.

- [ ] T004a [P] [US0] [FR-000] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/raw/` with `.gitkeep`.
- [ ] T004b [P] [US0] [FR-000] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/processed/` with `.gitkeep`.
- [ ] T004c [P] [US0] [FR-000] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/artifacts/` with `.gitkeep`.

- [ ] T005a [P] [US0] [FR-000] Create `state/` directory in repository root. **Verify**: Directory exists. **Depends on**: None.
- [X] T005b [P] [US0] [FR-000] Define `state/projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml` schema: `artifact_hashes` (map), `updated_at` (timestamp).
- [X] T005c [P] [US0] [FR-000] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/state_manager.py`. **Logic**: Atomic write (temp file + rename) to update YAML with content hashes and `updated_at`. **Depends on**: T005a, T005b.

- [X] T006 [P] [US0] [FR-000] Setup `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/config.py` for seeds, paths, and hyperparameters.
- [X] T007 [P] [US0] [FR-000] Create base data models (`SymbolicObservation`, `Trajectory`, `TaskOutcome`, `PerceptionLog`) in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/models.py`.
- [ ] T008a [P] [US0] [FR-000] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/errors.py` with `DatasetUnavailableError` and `ConvergenceTimeoutError` exception classes. **Verify**: Import succeeds. **Depends on**: None.
- [ ] T008b [P] [US0] [FR-000] Register exceptions in `code/utils/__init__.py`. **Depends on**: T008a.
- [ ] T009a [P] [US0] [FR-000] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/env_config.py` with `check_cpu_constraints()` function. **Logic**: Verify `CUDA_VISIBLE_DEVICES` is empty or `--cpu-only` flag is set. Raise `RuntimeError` if GPU detected. **Depends on**: None.
- [ ] T009b [P] [US0] [FR-000] Integrate `check_cpu_constraints()` into `code/models/train_llm.py` and `code/models/inference_symbolic.py`. **Depends on**: T009a.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Symbolic Pipeline Construction & Dataset Transformation (Priority: P1) 🎯 MVP

**Goal**: Ingest Guava visual trajectories and transform them into a "Symbolic-Guava" dataset using a CPU-only perception module.

**Independent Test**: The pipeline runs on a subset of trajectories. Output JSON contains valid bounding boxes/class labels. Processing time ≤ 150ms/frame on CPU. No raw pixel data in output.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for `SymbolicObservation` schema validation in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/contract/test_symbolic_observation.py`.
- [X] T011 [P] [US1] Integration test for full trajectory transformation in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/integration/test_transform_pipeline.py`.
- [X] T012 [P] [US1] Unit test for YOLO-tiny inference latency (must be < 150ms) and -hour full dataset completion in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/unit/test_performance.py`.

### Implementation for User Story 1

- [ ] T013a [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/download_guava.py` to fetch raw Guava data to `data/raw/guava/` and generate `data/raw/guava/checksums.json` (raise `DatasetUnavailableError` if fetch fails; NO synthetic fallback). **Depends on**: None.
- [ ] T013b [US1] **Ground Truth Download**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/download_gt_annotations.py` to fetch Ground Truth annotations (bboxes/objects) from a verified source (e.g., ` or Hugging Face dataset `guava/annotations`). **Logic**: If fetch fails, raise `DatasetUnavailableError`. **Output**: `data/raw/guava/ground_truth_annotations.json`. **Depends on**: T013a.
- [ ] T013c [US1] **Ground Truth Verification**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/verify_gt.py` to verify the integrity of `ground_truth_annotations.json`. **Logic**: Check for required keys (`annotations`, `bboxes`). If valid, generate `data/raw/guava/gt_verified.json` with `status: "valid"`. If invalid, generate `gt_verified.json` with `status: "missing"`. **Depends on**: T013b.
- [ ] T014 [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/transform_symbolic.py` to ingest raw frames and generate `SymbolicObservation` JSONs to `data/processed/symbolic_guava/{trajectory_id}.json` (FR-001, FR-002). **Depends on**: T013a, T013c.
- [ ] T015a [US1] **YOLO Model Download**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/download_yolo.py` to download `yolov5n.onnx` (or equivalent YOLO-tiny) from ` to `code/models/yolo_tiny.onnx`. **Verify**: File exists and checksum matches. **Depends on**: None.
- [ ] T015b [US1] **Inference Integration**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/transform_symbolic.py` function `run_yolo_inference(frame)` using ONNX Runtime. **Logic**: Load `code/models/yolo_tiny.onnx`, run inference, return class, bbox, centroid, color histogram. **Depends on**: T015a.
- [ ] T016a [US1] **GT Comparison Logic**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` function `compare_with_gt`. **Logic**: If `gt_verified.json` status is "valid", compare YOLO output vs GT using IoU threshold (standard threshold) and greedy matching. Return `object_missing_if_visible` (boolean: true if GT object has no match). If status is "missing", return `object_missing_if_visible=false` and set `gt_missing=true`. **Depends on**: T013c.
- [ ] T016b [US1] **Log Generation**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` function `log_perception_ground_truth`. **Output JSON**: `{"timestamp": float, "detected_objects": [...], "confidence_scores": [...], "object_missing_if_visible": boolean, "gt_missing": boolean}`. **Depends on**: T016a.
- [ ] T016c [US1] **Integration**: Integrate T016a and T016b into `transform_symbolic.py`. **Depends on**: T016b.
- [ ] T017 [US1] Implement logic in `transform_symbolic.py` to handle empty frames (empty object list or "scene_empty" flag).
- [ ] T018 [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` function `log_latency` to add perception latency measurements to `PerceptionLog` (FR-007, FR-008). **Depends on**: T016c.
- [ ] T019 [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/validate_perception.py` to validate YOLO precision/recall and verify the completion time constraint for the full transformation (FR-001, FR-002). **Depends on**: T013c, T016c.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Re-distillation on Symbolic States (Priority: P2)

**Goal**: Fine-tune a compact LLM (Phi-3-mini) on the Symbolic-Guava dataset to reason over symbolic states.

**Independent Test**: Fine-tuning converges (loss decrease ≥15%) within 4 hours on CPU (or triggers GPU escape hatch). Model accepts symbolic JSON input without crashing.

### Implementation for User Story 2

- [ ] T023a [US2] **Training Loop**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/train_llm.py` main training loop. **Logic**: Load Phi-3-mini, prepare symbolic dataset, perform LoRA fine-tuning. **Metric**: Track average loss of Epoch 0 vs average loss of final epoch. **Depends on**: T014.
- [ ] T023b [US2] **Timeout Logic**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/train_llm.py` timeout check. **Logic**: If training time > 4 hours OR loss decrease < 15%, raise `ConvergenceTimeoutError`. **Depends on**: T023a.
- [ ] T023c [US2] **GPU Escape Hatch**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/train_llm.py` GPU escape logic. **Logic**: If `ConvergenceTimeoutError` is raised, set `training_on_gpu=true` in `data/artifacts/training_metrics.json` and `state/...yaml`. Invoke `kaggle kernels push` with `--cpu` flag false, `--environment` "Python 3.10", `--dataset` "guava/symbolic". **Verify**: Kaggle run ID is logged. **Depends on**: T023b.
- [ ] T023d [US2] **Logging & Checkpointing**: Implement logging of loss metrics to `data/artifacts/training_metrics.json` and saving partial checkpoints. **Depends on**: T023a.
- [ ] T023e [US2] **Model Source Logging**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/state_manager.py` update to log `model_source: "cpu"` or `model_source: "gpu"` to `state/projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml`. **Depends on**: T023c.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5a: User Story 3 - Evaluation Execution (Priority: P3)

**Goal**: Execute the Symbolic-Guava agent and Baseline-Guava (visual) agent on held-out tasks.

**Independent Test**: Evaluation runs on a held-out set of tasks. Outputs success/failure logs.

### Implementation for User Story 3 (Execution)

- [ ] T032a [US3] **Download Baseline-Guava Visual Agent**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/download_baseline.py` to fetch the `Baseline-Guava (Visual)` agent from Hugging Face ID `guava/vision-base` or local path `code/models/guava_vision.pth`. **Logic**: If fetch fails, raise `DatasetUnavailableError`. **Verify**: Model weights are present and checksum matches. **Depends on**: None.
- [ ] T032b [US3] **PRIMARY BASELINE**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/inference_baseline.py` to run the **Baseline-Guava (visual)** agent. **Logic**: Load model from T032a. If model NOT found, log `BaselineUnavailable` error, set `baseline_comparison_valid=false` in `evaluation_results.json`, and **EXIT WITH CODE 1** (halt project). **Depends on**: T032a.
- [ ] T031 [US3] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/inference_symbolic.py` to run the fine-tuned Symbolic-Guava agent on a held-out set of tasks (FR-004). **Logic**: Check `baseline_comparison_valid` flag from T032b. If false, skip evaluation. **Depends on**: T032b, T023a.
- [ ] T032c [US3] **SECONDARY DIAGNOSTIC**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/download_oracle.py` to fetch the **Oracle-Symbolic** agent weights from `guava/oracle-symbolic` (if available) or generate a perfect policy script. **Depends on**: T013c.
- [ ] T032d [US3] **Oracle Inference**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/inference_oracle.py` to run the **Oracle-Symbolic** agent using ground-truth action sequences from `data/raw/guava/ground_truth_actions.json` (produced by T013/T014) to simulate a perfect policy. This is a secondary diagnostic tool. **Depends on**: T032c.

**Checkpoint**: Evaluation data generated for all agents

---

## Phase 5b: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Analyze evaluation results, perform statistical tests, and verify success criteria.

**Independent Test**: Analysis script produces p-value, success rates, and failure categories.

### Implementation for User Story 3 (Analysis)

- [ ] T034 [US3] Implement logic to flag "latency-induced failures" (>150ms) in `TaskOutcome` records. **Logic**: Consume latency data from `data/artifacts/perception_log.json` (produced by T018). Aggregate per task. If any frame in a task exceeds a predefined latency threshold, flag the task as "latency-induced failure". **Depends on**: T018.
- [ ] T035 [US3] Implement logic to filter out latency-induced failures from the primary success rate calculation and write updated outcomes to `data/processed/evaluation_outcomes.json` (FR-008). **Depends on**: T034.
- [ ] T035b [US3] Implement verification logic to assert the final success rate denominator equals `total_tasks - latency_failures` and write assertion result to `data/artifacts/latency_exclusion_verified.json` (FR-008 verification). **Logic**: `total_tasks` MUST be sourced from the count of files in `data/processed/evaluation_outcomes.json`. If this count differs from the config, the file count is the canonical source. **Depends on**: T034, T035.
- [ ] T033a [US3] **Failure Categorization**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/analysis/failure_categorizer.py` to categorize failures. **Logic**:
 - If `object_missing_if_visible` is `true`: Categorize as "perception".
 - If `object_missing_if_visible` is `false` AND `gt_missing` is `true`: Categorize as "semantic_unknown".
 - If `object_missing_if_visible` is `false` AND `gt_missing` is `false`:
 - If IoU < 0.3: Categorize as "geometric".
 - If class mismatch: Categorize as "semantic".
 **Depends on**: T016c, T034.
- [ ] T033b [US3] **SC-004 Calculation**: Implement logic to calculate the ratio of semantic failures to total failures. **Logic**: Include "semantic", "semantic_unknown", and "geometric" in the numerator. Include "perception" and "latency" in the denominator (excluded). **CRITICAL**: "semantic_unknown" IS INCLUDED in the denominator to prevent artificial inflation. **Depends on**: T033a.
- [ ] T036a [US3] **Baseline Check**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/analysis/check_baseline.py` to verify `baseline_comparison_valid`. **Logic**: If false, log "SC-001 Failure: Visual Baseline unavailable" and skip test. **Depends on**: T032b.
- [ ] T036b [US3] **PRIMARY TASK**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/analysis/stats_test.py` to perform a Permutation Test with **1000 iterations** and a convergence check (std_dev < 0.001) to ensure robust statistical inference. **Implementation**: Use `scipy.stats.permutation_test` to compare success rates of the Symbolic-Guava agent (from T031) against the Baseline-Guava (Visual) agent (from T032b). **Logic**: Null hypothesis: "No difference in success rates". Report p-value and declare significance if p < 0.05. **Note**: Explicitly disable Oracle-Symbolic as primary baseline logic; compare Symbolic vs. Visual. **Depends on**: T031, T032b, T036a.
- [ ] T037 [US3] Implement output generation for success rate, step efficiency, p-value, and failure distribution to `data/artifacts/evaluation_results.json` (FR-005, SC-001, SC-002). **Primary Output**: Symbolic vs. Visual metrics. **Logic**: If `training_on_gpu=true` (from T023c), exclude training time metrics from SC-005 and mark model as "GPU-Only Baseline". **Depends on**: T036b, T023c.
- [ ] T038 [US3] Implement logic to calculate the ratio of semantic failures to total failures **excluding perception and latency failures**, and write the result to `data/artifacts/sc004_verification.json`. **Logic**: Filter `TaskOutcome` list to exclude records where `failure_category` is in `[latency, perception]`. Calculate ratio on filtered list. If `semantic_ratio` < 0.40, log "Research Conclusion: SC-004 Not Met" to `data/artifacts/research_conclusions.json`. (FR-006, SC-004). **Depends on**: T033b.
- [X] T039 [US3] Implement unit test for the semantic failure ratio calculation in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/unit/test_semantic_ratio.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040a [P] Identify high-complexity functions in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` using `radon` tool.
- [X] T040b [P] Refactor identified functions in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` to reduce cyclomatic complexity to <10.
- [ ] T041 [P] Update README.md with setup instructions.
- [X] T042 [P] Create docs/quickstart.md with execution examples.
- [X] T043 [P] Update docs/api.md with function signatures.
- [ ] T044 [P] Run `state_manager.py` to finalize project state hashes at `state/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml`.
- [ ] T045 [P] Run quickstart.md validation.

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **CRITICAL**: Must complete before US2 and US3 as it produces the dataset.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (Symbolic-Guava dataset).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (dataset) and US2 (trained model).

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for SymbolicObservation schema validation in tests/contract/test_symbolic_observation.py"
Task: "Integration test for full trajectory transformation in tests/integration/test_transform_pipeline.py"
Task: "Unit test for YOLO-tiny inference latency in tests/unit/test_perception_latency.py"

# Launch implementation tasks for User Story 1 together:
Task: "Implement code/data/download_guava.py"
Task: "Implement code/data/transform_symbolic.py"
Task: "Implement code/utils/logger.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Dataset Generation)
4. **STOP and VALIDATE**: Verify Symbolic-Guava dataset is valid and YOLO precision/recall meets thresholds.
5. Deploy/demo if ready.

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
 - Developer A: User Story 1 (Dataset)
 - Developer B: User Story 2 (Model Training) - *Note: Can start partially but depends on US1 data*
 - Developer C: User Story 3 (Evaluation) - *Note: Can start partially but depends on US1 & US2*
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: All data loading tasks MUST fail loudly if real data is unavailable. No synthetic fallbacks.
- **Compute Constraints**: Adhere to CPU-only limits unless GPU escape hatch is triggered for training. If GPU is used, CPU constraint is considered failed and primary metrics are voided.
- **Baseline Correction**: T032a/T032b implement the **Spec-Required Visual Baseline** as the primary comparison. T032c/T032d implement the **Oracle-Symbolic** baseline as a secondary diagnostic tool. The primary evaluation compares Symbolic vs. Visual (T036b).
- **Statistical Robustness**: T036b uses 1000 iterations as default AND includes a convergence check to ensure sufficiency.
- **Failure Logic**: T038 explicitly excludes perception and latency failures from the semantic ratio calculation as per SC-004 and logs the conclusion.
- **Dynamic Environment Handling**: The system handles dynamic environments by logging latency-induced failures and excluding them from success rate calculations.
- **GPU Fallback Logic**: T023c enforces a hard 4-hour CPU limit. If exceeded, the task triggers an automatic Kaggle GPU run via API. The model source is logged to `state/...yaml`.
- **Permutation Test Robustness**: T036b uses `scipy.stats.permutation_test` with a defined null hypothesis (Symbolic vs. Visual) and a convergence check.
- **Semantic Failure Validation**: T038 calculates the ratio and logs the research conclusion (pass/fail) based on the 40% threshold.
- **Latency Threshold Enforcement**: T035b ensures that tasks exceeding 150ms latency are correctly flagged and excluded.
- **Primary vs. Secondary Comparison**: The **Spec's Visual Baseline** is the primary comparison (T036b). The **Plan's Oracle-Symbolic** baseline is secondary (T032d) and is used only for diagnostic purposes. The Plan is flagged for kickback to align with the Spec.
- **Ground Truth Dependency**: T016 handles missing ground truth by setting `gt_missing=true` and `object_missing_if_visible=false`, ensuring the boolean contract is preserved.
- **Latency Exclusion Verification**: T035b ensures that the primary success rate metric is calculated on a clean set of tasks, excluding those failed due to perception latency rather than reasoning capability.
- **Execution Order**: T034 runs before T033; T032a runs before T032b; T032b runs before T031; T031 and T032b run before T036b.

- [ ] T046 [US3] [Review-Resolve] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/analysis/permutation_convergence.py` to dynamically determine the minimum number of iterations required for the Permutation Test (T036b) to achieve a stable p-value (std_dev < 0.001). **Logic**: Run iterative batches of permutations until convergence criteria are met, logging the final iteration count to `data/artifacts/permutation_stats.json`. **Depends on**: T036b.
- [ ] T047 [US3] [Review-Resolve] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/analysis/failure_drilldown.py` to generate a detailed report linking specific "perception failure" cases (from T033a) to their corresponding raw frames and YOLO confidence scores. **Logic**: Cross-reference `PerceptionLog` with `TaskOutcome` to output a CSV of failure cases for manual review. **Depends on**: T033a, T018.
- [ ] T048 [US2] [Review-Resolve] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/train_llm.py` logic to log a "GPU Escape Triggered" event to `state/projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml` if the training duration exceeds 4 hours, ensuring the state manager reflects the compute deviation. **Depends on**: T023b.
- [ ] T049 [US1] [Review-Resolve] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/validate_perception.py` to explicitly verify that the transformed `SymbolicObservation` JSONs contain NO raw pixel data (byte arrays) and strictly adhere to the `class`, `bbox`, `centroid`, `color_histogram` schema. **Depends on**: T014.