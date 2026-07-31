# Tasks: llmXive Follow-up: Extending PerceptionDLM Parallel Region Perception

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-perceptiondl/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-833-llmxive-follow-up-extending-perceptiondl/`. **Execute**: `mkdir -p projects/PROJ-833-llmxive-follow-up-extending-perceptiondl/code/{synthetic,models,metrics,analysis} projects/PROJ-833-llmxive-follow-up-extending-perceptiondl/tests/{unit,contract} projects/PROJ-833-llmxive-follow-up-extending-perceptiondl/data/{raw,synthetic,processed} projects/PROJ-833-llmxive-follow-up-extending-perceptiondl/state`. Verify all directories exist.
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` at `projects/PROJ-833-llmxive-follow-up-extending-perceptiondl/code/requirements.txt`. **Execute**: Run `python -m venv venv && source venv/bin/activate && pip install --upgrade pip`. Then create `code/requirements.txt` containing pinned versions: `torch==2.1.0`, `transformers==4.36.0`, `diffusers==0.25.0`, `spacy==3.7.2`, `pandas==2.1.4`, `scikit-learn==1.3.2`, `matplotlib==3.8.2`, `datasets==2.16.1`, `huggingface_hub==0.20.1`, `psutil==5.9.7`. **Verify**: Run `pip install -r code/requirements.txt` successfully within the activated venv.
- [X] T003 [P] Configure linting (flake8/black) and formatting tools. **Deliverable**: Create `pyproject.toml` with `[tool.black] line-length=88` and `[tool.flake8] max-line-length=88`. Verify `black --check.` passes on the code directory.
- [X] T004 [P] Create configuration module `code/config.py` defining paths, random seeds (fixed), and hyperparameters for region counts (25, 30, 35, 40, 45, 50). **Document**: Insert the following comment block at the top of `code/config.py` to record the design decision: `# DESIGN DECISION: Sequential baseline uses SAME PerceptionDLM model with context-reset (not LLaVA) to avoid architectural confounds. This overrides Spec FR-003 per Plan Summary and Complexity Tracking. See docs/design_decisions.md for formal record.`
- [X] T004b [P] Document the Spec/Plan override formally. **Deliverable**: Create `docs/design_decisions.md` containing a section "Sequential Baseline Architecture" that explicitly states: "FR-003 originally specified LLaVA for sequential baseline. Plan and implementation use PerceptionDLM (context-reset) for both modes to ensure a controlled comparison of parallelism vs. fragmentation without architecture confounds. This decision supersedes FR-003."

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data generation logic, and statistical foundations that MUST be complete before ANY user story implementation or model runner execution.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Data generation logic (T046-T049, T024) is moved here to ensure data availability for runners.

- [ ] T042 [P] Define `contracts/synthetic_image.schema.yaml` and `contracts/regression_result.schema.yaml`. **Schema Details**: `synthetic_image.schema.yaml` must define properties: `image_path` (string), `bounding_boxes` (array of objects with `x`, `y`, `w`, `h`, `id`), `derived_relations` (array of strings). `regression_result.schema.yaml` must define `region_count` (int), `parallel_score` (float), `sequential_score` (float), `inference_time` (float), `corrected_p_value` (float), `is_significant` (boolean).
- [X] T023 [P] [US2] Contract test for synthetic image schema in `tests/contract/test_schemas.py` (depends on T042).
- [X] T006 [P] Implement `code/synthetic/validator.py` to check for overlapping bounding boxes using the schema defined in T042 and return boolean validation results.
- [X] T046 [P] Implement `code/synthetic/fetcher.py` to download a sampled subset of the dataset from HuggingFace. **Dataset**: Use `lvis/lvis-instances` or `coco/coco-stuff-164k` (verified to contain bounding boxes and segmentation masks). **Validation**: Verify the dataset contains image-caption pairs or bounding box annotations before proceeding. If the specific `paradlc-bench` is unavailable, use the closest verified alternative and document in `docs/design_decisions.md`.
- [X] T047 [P] Implement `code/synthetic/placer.py` to contain the core algorithm for placing non-overlapping bounding boxes on images, **including retry logic to reduce region count or skip images if placement fails**.
- [X] T048 [P] Implement `code/synthetic/deriver.py` to explicitly implement ground-truth relation derivation logic: deriving spatial prepositions (e.g., "left of", "above") from bounding box centroids as mandated by FR-004 and Spec Assumptions.
- [X] T048a [P] Unit test for `code/synthetic/deriver.py` in `tests/unit/test_deriver.py` to verify that derived relations (e.g., "left of") correctly match the geometric reality of the bounding box coordinates (e.g., centroid_x1 < centroid_x2).
- [X] T048b [P] Implement validation logic in `code/synthetic/validator.py` (or a new `code/synthetic/geometry_validator.py`) to verify that the `derived_relations` in generated JSONs match the geometric reality of the bounding box coordinates. **Execute**: Run a script that re-computes relations from saved coordinates and asserts they match the stored `derived_relations`. Fail if any mismatch is found.
- [X] T049 [P] Implement `code/synthetic/serializer.py` to save generated images and JSON annotation files (including derived geometric relations) to `data/synthetic/`.
- [X] T024 [US2] Implement `code/synthetic/generator.py` to orchestrate T046-T049: loop through a sampled subset of the dataset (n≥50 per bin) and generate images for region counts, 25, 30, 35, 40, 45, and 50, **ensuring JSON outputs include derived geometric relations**.
- [ ] T029a [P] Validate generated synthetic dataset. **Execute**: Run a script to re-compute geometric relations from the saved bounding box coordinates in `data/synthetic/*.json` and compare them against the stored `derived_relations` to ensure a complete match. Fail if any mismatch is found.
- [X] T025 [US2] Ensure `code/synthetic/generator.py` saves corresponding JSON annotation files with coordinates to `data/synthetic/`. (Note: Retry logic is in T047).
- [X] T026 [US2] Integrate `code/synthetic/validator.py` to validate every generated image before saving to disk.
- [X] T027 [US2] Add logging in `code/main.py` to track dataset generation progress and failure counts per image.
- [X] T051 [P] Implement `code/models/parallel_runner.py` to load PerceptionDLM from `code/config.py` (using the verified model ID, e.g., `USER/PERCEPTIONDLM-CHECKPOINT-ID`), run batched inference (batch size 8) without cross-batch context, **and include `time.perf_counter` instrumentation to capture wall-clock inference time**. **Note**: This task assumes dynamic quantization (T051a) is available if memory limits are approached.
- [X] T051a [P] Implement dynamic INT8 quantization and memory-swapping logic in `code/models/parallel_runner.py` to ensure Peak RSS < 7 GB. **Execute**: Use `torch.ao.quantization` or `bitsandbytes` (CPU-compatible) to quantize model layers dynamically if memory usage approaches a high magnitude.
- [X] T052 [P] Implement `code/models/sequential_runner.py` to load **PerceptionDLM (SAME model as T051)** and run sequential autoregressive inference with **context-reset** for each region to establish ground-truth baseline, **and include `time.perf_counter` instrumentation to capture wall-clock inference time**. **Note**: This overrides Spec FR-003 (LLaVA) per Plan Summary to avoid architectural confounds.
- [X] T052a [P] Implement dynamic INT8 quantization and memory-swapping logic in `code/models/sequential_runner.py` to ensure Peak RSS < 7 GB, mirroring T051a.
- [X] T053 [P] Implement **Bonferroni correction logic** in `code/analysis/regression.py` to apply family-wise error rate control to regression significance tests as mandated by Spec Assumptions. **Output**: The regression function must return a dictionary including `corrected_p_value` and `is_significant` (boolean) flags for the T022 consumer.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 2 - Synthetic Overflow Dataset Generation (Priority: P2)

**Goal**: Generate a robust dataset of region images to stress-test the overflow hypothesis.
**Note**: Logic is implemented in Phase 2; this phase focuses on execution and validation.

**Independent Test**: Run the generation script on multiple source images and verify output contains images with varying numbers of boxes with zero overlaps.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US2] Unit test for `code/synthetic/generator.py` in `tests/unit/test_synthetic.py` verifying non-overlap guarantee and retry logic.

### Implementation for User Story 2

- [X] T029 [US2] Execute `code/synthetic/generator.py` to generate the full synthetic dataset for all configured region count bins.
- [ ] T030 [US2] Verify generated dataset integrity (checksums, schema compliance) and log failure counts.

**Checkpoint**: Synthetic dataset generation logic is complete and robust

---

## Phase 4: User Story 1 - Parallel vs. Sequential Coherence Degradation Analysis (Priority: P1) 🎯 MVP

**Goal**: Execute the core comparative experiment to measure coherence degradation as region count exceeds context window.

**Independent Test**: Run the pipeline on a single synthetic image with multiple regions, generating parallel and sequential outputs, and verify JSON output files contain valid scores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [P] [US1] Unit test for `code/metrics/consistency.py` in `tests/unit/test_metrics.py` verifying relation extraction and derivation logic.

### Implementation for User Story 1

- [X] T018 [US1] Implement logic in `code/main.py` to **load** synthetic images with **specific region counts from the configured bins** from `data/synthetic/` (produced by T029). **Do NOT generate data here; assume T029 has completed.**
- [ ] T019 [US1] Implement logic in `code/main.py` to run parallel inference via `code/models/parallel_runner.py` (which now captures time) and save results to `data/processed/parallel_results.json` with a schema containing `captions`, `region_count`, `inference_time`, and `region_ids`.
- [ ] T020 [US1] Implement logic in `code/main.py` to run sequential inference via `code/models/sequential_runner.py` (**PerceptionDLM with context-reset**) and save results to `data/processed/sequential_results.json` with a schema containing `captions`, `region_count`, `inference_time`, and `region_ids`.
- [ ] T010 [P] [US1] Create `code/metrics/consistency.py` to extract spatial prepositional phrases via spaCy, **call `code/synthetic/deriver.py` (T048) to compute ground-truth relations**, and calculate Geometric Consistency Score. **Note: This task runs after data generation (T029) is complete. It depends on Phase 3 completion for data availability, but can run in parallel with other Phase 4 tasks once data is present.**
- [ ] T011 [P] [US1] Create `code/metrics/bleu.py` to calculate BLEU-4 scores for generated captions.
- [ ] T021 [US1] Implement logic in `code/main.py` to compute Semantic Coherence Score (using `consistency.py` which calls `deriver.py` for ground-truth) and BLEU-4 for both methods and write to `data/processed/metrics.json`.
- [ ] T022 [US1] Implement `code/analysis/regression.py` to process metrics and output `data/processed/degradation_curve.csv` containing region count, parallel score, sequential score, **Inference Time**, **corrected_p_value**, and **is_significant**. **Ensure Bonferroni correction (T053) is applied and the output columns are explicitly populated.**
- [ ] T054 [US1] Add error handling in `code/main.py` for memory limits (Peak RSS < 7GB) using the logic from T014b and graceful failure if model loading fails on CPU.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 5: User Story 3 - Pareto Frontier Visualization and Tipping Point Identification (Priority: P3)

**Goal**: Visualize the trade-off between inference time and semantic coherence to identify the tipping point.

**Independent Test**: Run the plotting script on the regression CSV and verify a PNG is generated with the tipping point marked.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Integration test for plotting output in `tests/integration/test_plotting.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement `code/analysis/plotting.py` to read `data/processed/degradation_curve.csv` and plot Inference Time (x) vs. Semantic Coherence Score (y).
- [ ] T033 [US3] Implement logic in `code/analysis/plotting.py` to **dynamically calculate** the "tipping point" by finding the first region count where the parallel coherence score drops below the configurable threshold (default 0.9 from `config.py`) of the sequential baseline score, and mark this point on the plot.
- [ ] T033a [P] Validate the tipping point calculation logic in `code/analysis/plotting.py` against the data distribution to ensure the threshold (0.9) is appropriate for the observed scores.
- [ ] T034 [US3] Generate `data/processed/pareto_frontier.png` with distinct lines for Parallel and Sequential methods.
- [ ] T035 [US3] Ensure `code/analysis/plotting.py` reads **Inference Time** data from the CSV (produced by T051/T052) to plot the Pareto frontier and handles missing time data gracefully.
- [ ] T036 [US3] Ensure `code/analysis/plotting.py` handles edge cases where data is insufficient to define a curve.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Orchestration & Polish

**Purpose**: Final integration, memory enforcement, and cross-cutting concerns

- [ ] T014 [P] Create `code/main.py` pipeline orchestration script to execute the full flow: fetch data → generate synthetic → run parallel/sequential inference → compute metrics → regression → plot. **Note**: This task orchestrates the flow by calling modules implemented in T024, T029, T030, T051, T052, T010, T022, T032. It runs after all components are implemented (Phases 2-5).
- [ ] T014b [P] Implement **runtime memory monitoring logic** in `code/main.py` (reading `/proc/self/status` or using `psutil`) and an **adaptive reduction mechanism**: if Peak RSS > 7 GB, **implement a retry loop that reduces the image count per bin by 5 images and retries inference**, failing only if the count drops below the minimum threshold (per FR-007).
- [ ] T037 [P] Update `research.md` with the final degradation curve data and tipping point analysis.
- [ ] T038 [P] Run `black --check` and `flake8` on `code/` and fix all violations to ensure code cleanliness.
- [ ] T039a [P] Run profiling script `code/analysis/profiler.py` with `cProfile` on `code/main.py` and output `data/processed/profile.out`.
- [ ] T039b [P] Analyze `data/processed/profile.out` to identify bottlenecks and determine optimal batch size.
- [ ] T039c [P] Update `code/config.py` with the empirically determined optimal batch size based on T039b analysis.
- [ ] T040 [P] Add unit tests for `code/analysis/regression.py` in `tests/unit/test_regression.py`.
- [ ] T041 Run `quickstart.md` validation to ensure the full pipeline executes end-to-end.
- [ ] T045 [P] Verify `state/projects/PROJ-833-llmxive-follow-up-extending-perceptiondl.yaml` contains checksums for **specifically** `data/synthetic/*.json` and `data/processed/*.csv` as mandated by the Constitution. **Execute**: Script to hash these specific patterns and update the state file.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 2 (Phase 3)**: Depends on Foundational - **Must complete before US1** to provide data
- **User Story 1 (Phase 4)**: Depends on Foundational and US2 (Data Availability)
- **User Story 3 (Phase 5)**: Depends on US1 (Data Availability)
- **Orchestration (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational AND US2 completion
- **User Story 2 (P2)**: Can start after Foundational - **Prerequisite for US1**
- **User Story 3 (P3)**: Can start after Foundational and US1

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 can start (data generation)
- Once US2 completes, US1 can start
- Once US1 completes, US3 can start
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (if dependencies allow)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for code/metrics/consistency.py in tests/unit/test_metrics.py"

# Launch all models for User Story 1 together:
Task: "Load existing synthetic images in code/main.py"
Task: "Run parallel inference via code/models/parallel_runner.py"
Task: "Run sequential inference via code/models/sequential_runner.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 2 (Data Generation - Prerequisite)
4. Complete Phase 4: User Story 1 (Synthetic gen + Parallel/Sequential run + Metrics)
5. **STOP and VALIDATE**: Test User Story 1 independently on a single sample
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 2 → Expand dataset generation → Test independently → Deploy/Demo
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 3 → Add visualization → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 2 (Dataset Scaling)
 - Developer B: User Story 1 (Core Experiment) - *Depends on A*
 - Developer C: User Story 3 (Visualization) - *Depends on B*
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
- **Constraint**: All model loading MUST use dynamic quantization (INT8) if needed to satisfy 7GB RAM limit on CPU.
- **Constraint**: Synthetic data generation MUST guarantee non-overlapping boxes; if generation fails, reduce count or skip, never fabricate fake data.
- **Constraint**: Sequential baseline MUST use PerceptionDLM with context-reset to avoid architectural confounds (resolving Spec/Plan conflict).
- **Constraint**: Region counts MUST include intermediate bins for non-linear regression.
- **Constraint**: Statistical analysis MUST include Bonferroni correction (T053) and output corrected p-values.
- **Constraint**: Memory management MUST include automatic sample reduction logic (T014b) with a fixed step size of 5 images.
- **Constraint**: Tipping point threshold MUST be configurable via `config.py` with a default of 0.9, but the calculation must dynamically find the first crossing point.