# Tasks: llmXive follow-up: extending "Guava: An Effective and Universal Harness for Embodied Manipulation"

**Input**: Design documents from `/specs/001-symbolic-guava-perception/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Methodological Alignment Notice**:
> **CRITICAL RESOLUTION**: The Plan.md proposed a "Critical Methodological Shift" to use an "Oracle-Symbolic" agent as the primary baseline. The Spec (FR-004, SC-001) explicitly mandates a comparison against the **Baseline-Guava (Visual)** agent.
> **Resolution**: Per the Constitution (Single Source of Truth), the **Spec is the binding authority**. The Plan's proposed shift is **REJECTED**.
> **Implementation Directive**:
> 1. **Primary Baseline**: The **Baseline-Guava (Visual)** agent (T032b) is the **PRIMARY** comparison target. T036b compares Symbolic vs. Visual.
> 2. **Secondary Baseline**: The "Oracle-Symbolic" agent (T032c) is implemented as a **SECONDARY/DIAGNOSTIC** tool only.
> 3. **Plan Status**: The Plan.md is flagged for **KICKBACK** to align with the Spec. The implementation MUST follow the Spec's Visual Baseline requirement.
> 4. **Baseline Unavailable**: If the Visual Baseline model is missing, T032c logs `BaselineUnavailable`, sets `baseline_comparison_valid=false`, and **HALTS** (exit 1) to enforce FR-004.

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
- [ ] T002b [US0] [FR-000] Verify dependencies install successfully in a clean virtualenv. **Action**: Run `pip install -r requirements.txt` in a temporary venv. **Verify**: No errors, all packages listed in `pip freeze`. **Depends on**: T002a. (Note: T002b is NOT parallel-safe as it depends on T002a).

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
- [X] T008a [P] [US0] [FR-000] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/errors.py` with `DatasetUnavailableError`, `ConvergenceTimeoutError`, and `KaggleAuthError` exception classes. **Verify**: Import succeeds. **Depends on**: None.
- [X] T008b [P] [US0] [FR-000] Register exceptions in `code/utils/__init__.py`. **Depends on**: T008a.
- [X] T009a [P] [US0] [FR-000] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/env_config.py` with `check_cpu_constraints()` function. **Logic**: Verify `CUDA_VISIBLE_DEVICES` is empty or `--cpu-only` flag is set. Raise `RuntimeError` if GPU detected. **Depends on**: None.
- [X] T009b [P] [US0] [FR-000] Integrate `check_cpu_constraints()` into `code/models/train_llm.py` and `code/models/inference_symbolic.py`. **Depends on**: T009a.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Data Acquisition & Validation (new)

- [ ] T013a [US1] Download Guava raw dataset to `data/raw/guava/` and generate `checksums.json`. **Logic**: Raise `DatasetUnavailableError` only if the download fails; otherwise set a flag `DATASET_AVAILABLE=true`. **Depends on**: None.
- [ ] T013c [US1] Handle missing dataset gracefully: if `DATASET_AVAILABLE` is false, log the condition, set `DATASET_AVAILABLE=false`, and allow downstream tasks to skip or use mock data. **Depends on**: T013a.
- [ ] T013b [US1] **CI/CD Fallback**: Generate a validated mock Guava dataset (synthetic frames with known bounding boxes) when `DATASET_AVAILABLE` is false and the environment is CI. **Depends on**: T013c.
- [ ] T020 [US1] Download ground‑truth annotation file `data/raw/guava/ground_truth_annotations.json` from the official Guava release URL. **Verify**: File exists and checksum matches. **Depends on**: T013a.
- [ ] T021 [US1] Validate the integrity of `ground_truth_annotations.json` against its schema. **Depends on**: T020.

---

## Phase 3: User Story 1 - Symbolic Pipeline Construction & Dataset Transformation (Priority: P1) 🎯 MVP

**Goal**: Ingest Guava visual trajectories and transform them into a "Symbolic-Guava" dataset using a CPU‑only perception module.

**Independent Test**: The pipeline runs on a subset of trajectories. Output JSON contains valid bounding boxes/class labels. Processing time ≤ 150 ms/frame on CPU. No raw pixel data in output.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for `SymbolicObservation` schema validation in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/contract/test_symbolic_observation.py`.
- [X] T011 [P] [US1] Integration test for full trajectory transformation in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/integration/test_transform_pipeline.py`.
- [ ] T012 [P] [US1] Unit test for YOLO‑tiny inference latency (must be < 150 ms) and ‑hour full dataset completion in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/unit/test_performance.py`.

### Implementation for User Story 1

- [ ] T014 [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/transform_symbolic.py` to ingest raw frames, run YOLO‑tiny inference, and emit `SymbolicObservation` JSONs to `data/processed/symbolic_guava/{trajectory_id}.json`. **Depends on**: T013a (or T013b if mock), T015a (YOLO model), T016c (logger integration), T017 (empty‑frame handling), T019 (latency flagging).
- [ ] T015a [US1] **YOLO Model Download**: Download `yolov8n.onnx` from ` to `code/models/yolo_tiny.onnx`. **Verify**: File exists, SHA256 checksum matches. **Depends on**: T013a (requires raw data for later verification, but download itself has no data dependency).
- [ ] T015c [US1] **YOLO Latency Benchmark**: Run inference on the first 100 frames of the downloaded Guava dataset using a 2‑core 3.0 GHz CPU profile; assert average latency < 150 ms. **Depends on**: T015a, T013a.
- [ ] T016a [US1] Implement `run_yolo_inference` in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` to return class, bbox, centroid, color histogram.
- [ ] T016b [US1] Implement `compare_with_gt` in the same logger module to produce `object_missing_if_visible` boolean based on `ground_truth_annotations.json`.
- [ ] T016c [US1] **Integration**: Import and use `run_yolo_inference` and `compare_with_gt` within `transform_symbolic.py`, logging each frame's PerceptionLog via `log_perception_ground_truth`. **Depends on**: T016a, T016b.
- [ ] T017 [US1] Implement empty‑frame handling in `transform_symbolic.py` to emit an empty object list or `"scene_empty"` flag without error.
- [ ] T018 [US1] Add `log_latency` function in `logger.py` that records inference time per frame into `PerceptionLog`.
- [ ] T019 [US1] **Latency Flagging**: Within `transform_symbolic.py`, after each frame's processing, if latency > 150 ms, set a `latency_exceeded` flag in the corresponding `TaskOutcome`. **Depends on**: T018.
- [ ] T019b [US1] **Validation**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/validate_perception.py` to ensure YOLO precision/recall ≥ 90 % and total transformation completes ≤ 4 h. **Depends on**: T014, T016c.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Re‑distillation on Symbolic States (Priority: P2)

**Goal**: Fine‑tune a compact LLM (Phi‑3‑mini) on the Symbolic‑Guava dataset to reason over symbolic states.

**Independent Test**: Fine‑tuning converges (loss decrease ≥15 %) within 4 h on CPU. Model accepts symbolic JSON input without crashing.

### Implementation for User Story 2

- [ ] T023a [US2] **Training Loop**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/train_llm.py` main training loop. Load Phi‑3‑mini, prepare Symbolic‑Guava dataset, perform LoRA fine‑tuning, track epoch losses. **Depends on**: T014.
- [ ] T023b [US2] **Timeout Logic**: Within `train_llm.py`, if training exceeds 4 h or loss decrease < 15 %, raise `ConvergenceTimeoutError` and exit with code 1. **Depends on**: T023a.
- [ ] T023d [US2] **Kaggle Auth Check**: Verify presence of `KAGGLE_KEY`; if missing, raise `KaggleAuthError` with clear message. (Retained for optional future use but does not trigger GPU fallback.) **Depends on**: T023a.
- [ ] T023e [US2] **Logging & Checkpointing**: Log loss metrics to `data/artifacts/training_metrics.json` and save partial checkpoints after each epoch. **Depends on**: T023a.
- [ ] T023f [US2] **Model Source Logging**: Update `state_manager.py` to record `model_source: "cpu"` in the project state YAML after successful checkpoint. **Depends on**: T023e.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5a: User Story 3 - Evaluation Execution (Priority: P3)

**Goal**: Execute the Symbolic‑Guava agent and Baseline‑Guava (visual) agent on held‑out tasks.

**Independent Test**: Evaluation runs on a held‑out set of tasks. Outputs success/failure logs.

### Implementation for User Story 3 (Execution)

- [ ] T030 [US3] **Held‑Out Split Selection**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/select_split.py` to randomly select a subset of task IDs from the full dataset (seeded). **Verify**: Output file `data/processed/heldout_split.json` contains exactly 50 IDs. **Depends on**: T013a (or T013b if mock).
- [ ] T032a [US3] **Baseline Verification**: Check existence of the Hugging Face repo `guava/vision-base-v1`. If not found, raise `BaselineUnavailableError` and abort pipeline. **Depends on**: None.
- [ ] T032c [US3] **Baseline Abort**: If `BaselineUnavailableError` is raised, log `BaselineUnavailable`, set `baseline_comparison_valid=false` in state YAML, and exit with non‑zero code to enforce FR‑004. **Depends on**: T032a.
- [ ] T032b [US3] **Baseline Download**: After successful verification, download the Baseline‑Guava model to `code/models/baseline_guava/`. **Depends on**: T032a.
- [ ] T031 [US3] **Symbolic Inference**: Run the fine‑tuned Symbolic‑Guava agent on the held‑out split (uses `select_split.json`). **Depends on**: T023a, T014, T030, and assumes `baseline_comparison_valid=true` (enforced by T032c). Writes per‑task results to `data/processed/symbolic_outcomes.json`.
- [ ] T032d [US3] **Oracle‑Symbolic (Secondary Diagnostic)**: Download or generate Oracle‑Symbolic agent weights from `guava/oracle-symbolic` and run perfect‑policy inference for diagnostic purposes. **Depends on**: T014.

**Checkpoint**: Evaluation data generated for all agents

---

## Phase 5b: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Analyze evaluation results, perform statistical tests, and verify success criteria.

**Independent Test**: Analysis script produces p‑value, success rates, and failure categories.

### Implementation for User Story 3 (Analysis)

- [ ] T033a [US3] **Failure Categorization**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/analysis/failure_categorizer.py`. Use `PerceptionLog` fields: if `object_missing_if_visible` is true → "perception"; else if IoU < 0.3 → "geometric"; else if class mismatch → "semantic". **Depends on**: T016c.
- [ ] T033c [US3] **GT Filtering**: Exclude entries where ground truth is missing (`gt_missing=true`) from the denominator used for SC‑004. **Depends on**: T033a.
- [ ] T034 [US3] **Latency Filtering**: Implement logic to filter out tasks flagged as `latency_exceeded` from the primary success‑rate calculation; write filtered outcomes to `data/processed/evaluation_outcomes.json`. **Depends on**: T018, T019.
- [ ] T034b [US3] **Latency Exclusion Verification**: Verify that the denominator of the success‑rate equals `total_tasks - latency_failures` and record verification in `data/artifacts/latency_exclusion_verified.json`. **Depends on**: T034, T006.
- [ ] T035 [US3] **SC‑004 Ratio Calculation**: Using outputs from T033a (with T033c filtering) and T034 (latency‑filtered set), compute the semantic‑failure ratio. Write result to `data/artifacts/sc004_verification.json`. **Depends on**: T033c, T034.
- [ ] T036a [US3] **Baseline Check**: Verify `baseline_comparison_valid` flag; if false, abort further statistical analysis. **Depends on**: T032c.
- [ ] T036b [US3] **Permutation Test**: Perform a permutation test (1000 iterations, convergence std < 0.001) comparing Symbolic success rates vs. Visual baseline success rates using `scipy.stats.permutation_test`. Output p‑value to `data/artifacts/evaluation_results.json`. If baseline flag is false, write `"p_value": "N/A"` and log `BaselineUnavailable`. **Depends on**: T031, T032b, T036a.
- [ ] T050 [US3] **Metric Invalidation**: If `primary_metrics_valid` is false (from T023b), mark SC‑001, SC‑002 as `INVALID` in the final report. **Depends on**: T023b.
- [ ] T037 [US3] **Result Generation**: Consolidate success rate, step efficiency, p‑value, and failure distribution into `data/artifacts/evaluation_results.json`. Respect `primary_metrics_valid` flag (exclude compute‑time metrics if invalid). **Depends on**: T036b, T023b, T050.
- [ ] T038 [US3] **Research Conclusions**: Based on SC‑004 verification and SC‑001/SC‑002 outcomes, write a concise conclusion JSON to `data/artifacts/research_conclusions.json`. **Depends on**: T035, T037.
- [ ] T039 [US3] **Unit Test**: Add unit test for semantic‑failure ratio calculation in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/unit/test_semantic_ratio.py`. **Depends on**: T035.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040a [P] Identify high‑complexity functions in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` using `radon` tool.
- [X] T040b [P] Refactor identified functions in `logger.py` to reduce cyclomatic complexity to <10.
- [ ] T041 [P] Update README.md with setup instructions.
- [X] T042 [P] Create docs/quickstart.md with execution examples.
- [X] T043 [P] Update docs/api.md with function signatures.
- [ ] T044 [P] Run `state_manager.py` to finalize project state hashes at `state/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml`.
- [ ] T045 [P] Run quickstart.md validation.
- [ ] T051 [P] **SC‑005 Threshold**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/analysis/validate_compute.py` to verify total compute time ≤ 6 h. Read timestamps from training and evaluation logs; assert total ≤ 6 h. **Depends on**: T037.

---

## Phase 5c: Review & Reporting

- [X] T047 [US3] **Failure Drill‑down Report**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/analysis/failure_drilldown.py` to generate a CSV linking each "perception failure" case to its raw frame path and YOLO confidence scores, using `PerceptionLog`. **Depends on**: T033a, T018.
