# Tasks: llmXive follow-up: extending "Guava: An Effective and Universal Harness for Embodied Manipulation"

**Input**: Design documents from `/specs/001-symbolic-guava-perception/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Methodological Alignment Notice**:
> **CRITICAL CONFLICT RESOLUTION**: The Spec (FR-004, SC-001) explicitly mandated a comparison between the Symbolic-Guava agent and the **Baseline-Guava (Visual)** agent as the **PRIMARY** research question. The Plan.md (Summary & Complexity Tracking) proposed a "Critical Methodological Shift" to use an "Oracle-Symbolic" agent as the primary baseline.
> **Resolution**: Per the Constitution (Single Source of Truth), the **Spec is the binding authority** for research success criteria. The Plan's proposed shift is a contradiction that invalidates the Spec's success criteria.
> **Implementation Directive**:
> 1. **Primary Baseline**: The **Baseline-Guava (Visual)** agent (T032a) is the **PRIMARY** comparison target. T036a (Permutation Test) compares Symbolic vs. Visual.
> 2. **Secondary Baseline**: The "Oracle-Symbolic" agent (T032b) is implemented as a **SECONDARY/DIAGNOSTIC** tool only.
> 3. **Plan Status**: The Plan.md is flagged for **KICKBACK** to align with the Spec. The implementation MUST follow the Spec's Visual Baseline requirement.
> 4. **Baseline Unavailable**: If the Visual Baseline model is missing, T032a logs a "SC-001 Failure" and sets `baseline_comparison_valid=false`. The project **does not halt**; the Symbolic agent is still evaluated, but SC-001 is marked as unmet.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
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

- [ ] T001a [P] Create `.gitignore` file in the root directory of the project. <!-- ATOMIZE: requested -->
- [ ] T001b [P] Run `git init` in the root directory of the project. <!-- ATOMIZE: requested -->
- [ ] T001c [P] Run `git add .` to stage all files. <!-- ATOMIZE: requested -->
- [ ] T001d [ ] Run `git add .gitignore` (or `git add .`) then `git commit -m "Initial commit"` to create the initial commit. <!-- FIXED: Added explicit add step; status corrected from [X] to [ ] -->
- [ ] T002a [P] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/requirements.txt` with dependencies: `opencv-python`, `onnxruntime`, `datasets`, `transformers`, `torch`, `scikit-learn`, `pandas`, `numpy`, `pytest`
- [ ] T002b [P] Add Python version check script to verify Python 3.11+ is available
- [ ] T003a [P] Create `.ruff.toml` configuration file with basic linting rules
- [X] T003b [P] Create `pyproject.toml` configuration for `black` formatting tool
- [ ] T004a [P] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/raw/` with `.gitkeep`
- [ ] T004b [P] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/processed/` with `.gitkeep`
- [ ] T004c [P] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/artifacts/` with `.gitkeep`
- [ ] T005 [P] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/state_manager.py` to update `state/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml` (repo root) with content hashes and timestamps. **Schema**: Must define `artifact_hashes` map and `updated_at` timestamp; use atomic write (write to temp, rename) to ensure consistency.
- [X] T006 [P] Setup `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/config.py` for seeds, paths, and hyperparameters
- [X] T007 [P] Create base data models (`SymbolicObservation`, `Trajectory`, `TaskOutcome`, `PerceptionLog`) in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/models.py`
- [ ] T008 [P] Configure error handling infrastructure and `DatasetUnavailableError` exception
- [ ] T009 [P] Setup environment configuration management for CPU-only runner constraints

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Symbolic Pipeline Construction & Dataset Transformation (Priority: P1) 🎯 MVP

**Goal**: Ingest Guava visual trajectories and transform them into a "Symbolic-Guava" dataset using a CPU-only perception module.

**Independent Test**: The pipeline runs on a subset of trajectories. Output JSON contains valid bounding boxes/class labels. Processing time ≤ 150ms/frame on CPU. No raw pixel data in output.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for `SymbolicObservation` schema validation in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/contract/test_symbolic_observation.py`
- [X] T011 [P] [US1] Integration test for full trajectory transformation in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/integration/test_transform_pipeline.py`
- [X] T012 [P] [US1] Unit test for YOLO-tiny inference latency (must be < 150ms) and -hour full dataset completion in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/unit/test_performance.py`

### Implementation for User Story 1

- [ ] T013a [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/download_guava.py` to fetch raw Guava data to `data/raw/guava/` and generate `data/raw/guava/checksums.json` (raise `DatasetUnavailableError` if fetch fails; NO synthetic fallback)
- [ ] T013b [US1] **Ground Truth Verification**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/verify_ground_truth.py` to search for existing ground-truth annotations in `data/raw/guava/`. **Logic**: Search for specific schema keys (`annotations`, `bboxes`, `objects`) in the raw data files.
   - **If found**: Copy to `data/raw/guava/ground_truth_annotations.json` and set global flag `PERCEPTION_GT_AVAILABLE=true`.
   - **If NOT found**: Log a specific error `GroundTruthMissing` and set global flag `PERCEPTION_GT_AVAILABLE=false`. **DO NOT HALT**. The pipeline proceeds in "Validation-Limited Mode". (FR-007, FR-008). **Depends on T013a**.
- [ ] T013c [US1] Verify `data/raw/guava/` integrity using `checksums.json` and log result. **Depends on T013a**.
- [X] T014 [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/transform_symbolic.py` to ingest raw frames and generate `SymbolicObservation` JSONs to `data/processed/symbolic_guava/{trajectory_id}.json` (FR-001, FR-002). **Depends on T013b** (must check `PERCEPTION_GT_AVAILABLE` flag).
- [X] T015 [US1] Integrate OpenCV + ONNX Runtime YOLO-tiny in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/transform_symbolic.py` for object detection (class, bbox, centroid, color histogram). **Depends on T013b**.
- [ ] T016 [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` function `log_perception_ground_truth` to generate a continuous 'Perception Ground-Truth Log' to `data/artifacts/perception_log.json`. Output JSON schema: `{"timestamp": float, "detected_objects": [{"class": str, "bbox": [int, int, int, int], "centroid": [float, float], "color_hist": [float,...]}], "confidence_scores": [float], "object_missing_if_visible": boolean|null}`.
   - **CRITICAL**: The `object_missing_if_visible` boolean MUST be derived by attempting to compare YOLO output against `data/raw/guava/ground_truth_annotations.json`.
   - **Logic**:
     1. Check if `data/raw/guava/ground_truth_annotations.json` exists.
     2. **If exists**: Perform comparison. If YOLO misses an object present in GT, set `object_missing_if_visible=true`. Else `false`.
     3. **If NOT exists**: Set `object_missing_if_visible=null` and log a warning "Ground Truth unavailable; perception failure categorization will be limited". (FR-007, FR-008).
   - **Dependency Note**: This task does **NOT** depend on T013b's successful completion of file creation. It handles the file's absence gracefully.
- [ ] T017 [US1] Implement logic in `transform_symbolic.py` to handle empty frames (empty object list or "scene_empty" flag)
- [X] T018 [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` function `log_latency` to add perception latency measurements to `PerceptionLog` in `code/utils/logger.py` (FR-007, FR-008)
- [X] T019 [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/validate_perception.py` to validate YOLO precision/recall and verify the completion time constraint for the full transformation (FR-001, FR-002). **Depends on T013b**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Re-distillation on Symbolic States (Priority: P2)

**Goal**: Fine-tune a compact LLM (Phi-3-mini) on the Symbolic-Guava dataset to reason over symbolic states.

**Independent Test**: Fine-tuning converges (loss decrease ≥15%) within 4 hours on CPU (or triggers GPU escape hatch). Model accepts symbolic JSON input without crashing.

### Implementation for User Story 2

- [X] T023 [US2] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/train_llm.py` to load Phi-3-mini, prepare symbolic dataset, and perform LoRA fine-tuning. **Sub-tasks integrated**:
 1. **Timing Check**: Measure training duration.
 2. **Hard Constraint Enforcement**: If CPU training time exceeds 4 hours OR loss decrease is <15% at the 4-hour mark, the script MUST **IMMEDIATELY TERMINATE** and raise a `ConvergenceTimeoutError`.
 3. **GPU Escape Logic**: **DO NOT** trigger GPU execution within this primary task. The GPU escape is a **separate, manual diagnostic step** (Task T023-GPU) that must be explicitly invoked if the primary CPU run fails. The primary task must not bypass the CPU constraint.
 4. **Constraint Verification**: If the task terminates due to timeout, log "CPU Constraint Violated" and set `cpu_constraint_violated=true` in `evaluation_results.json`. **DO NOT** proceed to generate primary metrics from a GPU run in this task. (FR-003, FR-004).
 5. **Logging**: Log loss decrease (target ≥15% in 4h) to `data/artifacts/training_metrics.json`.
 6. **Checkpointing**: Save partial checkpoints if interrupted.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5a: User Story 3 - Evaluation Execution (Priority: P3)

**Goal**: Execute the Symbolic-Guava agent and Baseline-Guava (visual) agent on held-out tasks.

**Independent Test**: Evaluation runs on a held-out set of tasks. Outputs success/failure logs.

### Implementation for User Story 3 (Execution)

- [X] T031 [US3] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/inference_symbolic.py` to run the fine-tuned Symbolic-Guava agent on a held-out set of tasks (FR-004). **Depends on T032a** (to ensure baseline availability check is done first).
- [ ] T032a [US3] **PRIMARY BASELINE**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/inference_baseline.py` to run the **Baseline-Guava (visual)** agent. **Logic**: Attempt to load pre-trained Guava visual model from `code/models/config.py` (Hugging Face ID or local path).
   - **CRITICAL**: If the model is NOT found, log a specific error `BaselineUnavailable` and set `baseline_comparison_valid=false` in `evaluation_results.json`. **DO NOT HALT**. The project continues to evaluate the Symbolic agent, but SC-001 is marked as unmet. (FR-004, SC-001 - PRIMARY). **Must run before T031 and T036a**.
- [ ] T032b [US3] **SECONDARY DIAGNOSTIC**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/inference_oracle.py` to run the **Oracle-Symbolic** agent using ground-truth action sequences from `data/raw/guava/ground_truth_actions.json` (produced by T013/T014) to simulate a perfect policy. This is a secondary diagnostic tool.

**Checkpoint**: Evaluation data generated for all agents

---

## Phase 5b: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Analyze evaluation results, perform statistical tests, and verify success criteria.

**Independent Test**: Analysis script produces p-value, success rates, and failure categories.

### Implementation for User Story 3 (Analysis)

- [ ] T033 [US3] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/analysis/failure_categorizer.py` to categorize failures (geometric, semantic, perception, latency) using `PerceptionLog` (FR-006, FR-007).
   - **Logic**:
     - If `object_missing_if_visible` is `true`: Categorize as "perception".
     - If `object_missing_if_visible` is `false`: Categorize as "geometric" or "semantic" based on other heuristics.
     - **CRITICAL**: If `object_missing_if_visible` is `null` (GT missing from T013b): Categorize as "semantic_unknown" and **exclude** from the SC-004 calculation to prevent false positives. **Depends on T034**.
- [ ] T034 [US3] Implement logic to flag "latency-induced failures" (>150ms) in `TaskOutcome` records.
   - **Logic**: Consume latency data from `data/artifacts/perception_log.json` (produced by T018). Aggregate per task. If any frame in a task exceeds 150ms, flag the task as "latency-induced failure". **Must run before T033 and T035**.
- [ ] T035 [US3] Implement logic to filter out latency-induced failures from the primary success rate calculation and write updated outcomes to `data/processed/evaluation_outcomes.json` (FR-008). **Depends on T034**.
- [ ] T035b [US3] Implement verification logic to assert the final success rate denominator equals `total_tasks - latency_failures` and write assertion result to `data/artifacts/latency_exclusion_verified.json` (FR-008 verification).
   - **Logic**: `total_tasks` MUST be sourced from the count of files in `data/processed/evaluation_outcomes.json`. If this count differs from the config, the file count is the canonical source. **Depends on T035**.
- [X] T036a [US3] **PRIMARY TASK**: Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/analysis/stats_test.py` to perform a Permutation Test with a sufficient number of iterations (configurable via `config.py`) for robust statistical inference using `scipy.stats.permutation_test`.
   - **Primary Comparison**: Symbolic-Guava vs. **Baseline-Guava (Visual)** (Spec-Required Baseline).
   - **Logic**: If `baseline_comparison_valid=false` (from T032a), log "SC-001 Failure: Visual Baseline unavailable" and skip the test. Otherwise, run the test. Null hypothesis: "No difference in success rates between Symbolic-Guava and Baseline-Guava". Report p-value and declare significance if p < 0.05. **Depends on T032a**. (FR-005, Spec Methodology).
- [ ] T036b [US3] **SECONDARY TASK**: Implement the Oracle-Symbolic comparison (Symbolic vs. Oracle) as a supplementary analysis. Tagged as secondary/diagnostic per Plan Methodology.
- [ ] T037 [US3] Implement output generation for success rate, step efficiency, p-value, and failure distribution to `data/artifacts/evaluation_results.json` (FR-005, SC-001, SC-002). **Primary Output**: Symbolic vs. Visual metrics.
- [ ] T038 [US3] Implement logic to calculate the ratio of semantic failures to total failures **excluding perception and latency failures**, and write the result to `data/artifacts/sc004_verification.json`.
   - **Logic**: Filter `TaskOutcome` list to exclude records where `failure_category` is in `[latency, perception, semantic_unknown]`. Calculate ratio on filtered list. If `semantic_ratio` < 0.40, log "Research Conclusion: SC-004 Not Met" to `data/artifacts/research_conclusions.json`. (FR-006, SC-004).
- [X] T039 [US3] Implement unit test for the semantic failure ratio calculation in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/unit/test_semantic_ratio.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040a [P] Identify high-complexity functions in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` using `radon` tool
- [X] T040b [P] Refactor identified functions in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` to reduce cyclomatic complexity to <10
- [ ] T041 [P] Update README.md with setup instructions
- [X] T042 [P] Create docs/quickstart.md with execution examples
- [X] T043 [P] Update docs/api.md with function signatures
- [ ] T044 [P] Run `state_manager.py` to finalize project state hashes at `state/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml`
- [ ] T045 [P] Run quickstart.md validation

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
- **Baseline Correction**: T032a implements the **Spec-Required Visual Baseline** as the PRIMARY comparison. T032b implements the **Oracle-Symbolic** baseline as a SECONDARY diagnostic tool. The primary evaluation compares Symbolic vs. Visual (T036a).
- **Statistical Robustness**: T036a uses [deferred] iterations as default AND includes a convergence check to ensure sufficiency.
- **Failure Logic**: T038 explicitly excludes perception, latency, and `semantic_unknown` failures from the semantic ratio calculation as per SC-004 and logs the conclusion.
- **Dynamic Environment Handling**: The system handles dynamic environments by logging latency-induced failures and excluding them from success rate calculations.
- **GPU Fallback Logic**: T023 enforces a hard 4-hour CPU limit. If exceeded, the task fails. GPU usage is a separate diagnostic step, not an automatic fallback, preserving the integrity of the CPU-only research constraint.
- **Permutation Test Robustness**: T036a uses `scipy.stats.permutation_test` with a defined null hypothesis (Symbolic vs. Visual) and a convergence check.
- **Semantic Failure Validation**: T038 calculates the ratio and logs the research conclusion (pass/fail) based on the 40% threshold.
- **Latency Threshold Enforcement**: T035b ensures that tasks exceeding 150ms latency are correctly flagged and excluded.
- **Primary vs. Secondary Comparison**: The **Spec's Visual Baseline** is the primary comparison (T036a). The **Plan's Oracle-Symbolic** baseline is secondary (T036b) and is used only for diagnostic purposes. The Plan is flagged for kickback to align with the Spec.
- **Ground Truth Dependency**: T016 handles missing ground truth by setting flags to null and logging warnings, ensuring the pipeline does not crash if GT is missing.
- **Latency Exclusion Verification**: T035b ensures that the primary success rate metric is calculated on a clean set of tasks, excluding those failed due to perception latency rather than reasoning capability.