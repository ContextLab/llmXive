# Tasks: llmXive follow-up: extending "LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing"

**Input**: Design documents from `/specs/001-optical-flow-temporal-coherence/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create project directory structure: `projects/PROJ-<ID>-llmxive-follow-up-extending-liveedit-tow/` with subdirectories `data/raw`, `data/flow`, `data/metrics`, `code`, `code/data`, `code/models`, `code/metrics`, `code/analysis`, `tests/contract`, `tests/unit`, `results`
- [X] T001b Create initial file scaffolding: `code/__init__.py`, `code/config.py`, `tests/__init__.py`, `results/.gitkeep`
- [X] T002 Create `code/requirements.txt` containing the following pinned dependencies: torch>=2.0.0 (cpu), diffusers, opencv-python, scikit-learn, pandas, numpy, datasets, ruptures
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `pyproject.toml` with explicit `[tool.ruff]` and `[tool.black]` sections; verify setup by running `ruff check.` and `black --check.` with successful exit status.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create base data models (VideoClip, MetricRecord, AnalysisResult) in `code/__init__.py` and `code/data/models.py`
- [X] T005 [P] Setup experiment configuration manager in `code/config.py` with explicit `SENSITIVITY_CUTOFFS` constant initialized to {0.01, 0.05, 0.1} (for FR-007 sensitivity analysis) and `STRATIFICATION_THRESHOLDS` constant initialized to {0.5, 5.0} (for Plan.md Dataset Strategy), plus random seeds
- [X] T006 Implement robust logging and checkpointing infrastructure in `code/utils/logger.py` and `code/utils/checkpoint.py` (handles CI limit, resume capability)
- [X] T007 Create schema validators for Dataset, Metrics, and Analysis outputs in `code/contracts/` using `pydantic`: create `dataset_schema.py`, `metric_schema.py`, `analysis_schema.py`; verify by validating a sample JSON record against each schema and raising an error on mismatch
- [X] T008 Implement memory profiling wrapper in `code/metrics/resource.py` to track peak RAM usage per clip
- [X] T009 [US2] Implement full optical flow computation in `code/data/flow.py` using RAFT-small or Farneback (CPU-optimized) for the Flow-Coherence model; output fields to `data/flow/`. **Note**: This task is for model warping (US2). It must complete after T009a to avoid CPU/RAM contention on the runner with constrained memory resources. **Depends on T009a**.
- [X] T009a [US1] Implement lightweight flow magnitude extraction in `code/data/flow.py` (or separate `code/data/flow_mag.py`) to compute mean flow magnitude for stratification; output to `data/flow/magnitudes.json`. **Note**: Must complete before T009 and T013 to avoid resource contention; NOT [P] due to heavy compute overlap with T009. **Depends on T012**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Replication and Metric Collection (Priority: P1) 🎯 MVP

**Goal**: Execute the CPU-optimized LiveEdit baseline model on a stratified dataset to establish ground-truth metrics (memory, latency, temporal consistency) before introducing modifications.

**Independent Test**: Running the baseline pipeline on a subset of clips generates a JSON report containing peak memory, inference time, and background SSIM scores without manual intervention.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for MetricRecord schema in `tests/contract/test_metric_schema.py`
- [X] T011 [P] [US1] Integration test for baseline inference pipeline in `tests/integration/test_baseline_pipeline.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement dataset downloader in `code/data/downloader.py` to fetch DAVIS/YouTube-VOS clips via `datasets.load_dataset` with streaming; ensure it fails loudly on missing sources (no synthetic fallback); **Depends on T005** (config availability)
- [X] T013 [US1] Implement video processor in `code/data/processor.py` to generate synthetic masks and stratify clips by motion complexity as defined in Plan.md Dataset Strategy; **Depends on T012, T009a** (reads `data/flow/magnitudes.json` for stratification logic)
- [X] T014 [US1] Implement baseline LiveEdit model wrapper in `code/models/baseline.py` with temporal attention layers ENABLED
- [X] T015 [US1] Implement baseline inference runner in `code/main.py` (baseline mode) that processes clips one-by-one to manage RAM
- [X] T016a [US1] Implement metric calculator for **Baseline** in `code/metrics/ssim.py`: Compute **Consecutive Frame SSIM** and **Temporal Gradient Variance** between **consecutive edited frames ($t$ and $t-1$) within the edited output video** to measure flickering (Source: Spec FR-005). **Note**: This task implements FR-005 specifically for the Baseline model. **Depends on T009a** (for flow magnitude context if needed). **Output**: `data/metrics/baseline_flicker.json`. **Verify**: JSON contains `consecutive_ssim` and `temporal_gradient_variance` keys.
- [X] T017 [US1] Implement report generator for baseline metrics in `code/analysis/reporter.py` (outputs JSON/Parquet to `data/metrics/baseline_results.json`)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Flow-Coherence Module Implementation and Execution (Priority: P2)

**Goal**: Replace region-tracking logic with a "Flow-Coherence" module using pre-computed optical flow, execute on the dataset, and measure memory reduction vs. artifact generation.

**Independent Test**: Running the modified pipeline on the same dataset subset generates a comparative metrics report showing memory reduction and SSIM scores, including handling of invalid flow vectors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for invalid_flow flag handling in `tests/contract/test_flow_coherence.py`
- [X] T019 [P] [US2] Integration test for flow-warping logic in `tests/integration/test_flow_warp.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement Flow-Coherence module in `code/models/flow_coherence.py`: replaces Mask Cache, warps latents using pre-computed flow (T009), removes attention layers
- [X] T021 [US2] Implement invalid flow handling in `code/models/flow_coherence.py`: fallback to identity warp for NaN/infinity vectors and set `invalid_flow` flag
- [X] T022 [US2] Implement flow-coherence inference runner in `code/main.py` (flow mode) with checkpointing support
- [X] T016b [US2] Implement unified metric calculator for **Flow-Coherence** in `code/metrics/ssim.py`: Compute **Consecutive Frame SSIM** (to satisfy Spec FR-005 for flickering) AND **Background Stability Score (BSS)** (to satisfy Plan.md "Critical Methodological Updates" by isolating background and comparing to GT). **Note**: This task explicitly implements BOTH requirements. **Depends on T009**. **Output**: `data/metrics/flow_flicker_bss.json`. **Verify**: JSON contains `consecutive_ssim`, `temporal_gradient_variance`, `bss`, and `flow_normalized_ssim` keys.
- [X] T023 [US2] Update metric calculator in `code/metrics/ssim.py` to record flow magnitude statistics and `invalid_flow` markers per frame (extending the BSS logic from T016b); **Depends on T016b**
- [X] T024 [US2] Implement comparative report generator in `code/analysis/reporter.py` (outputs JSON/Parquet to `data/metrics/flow_results.json`)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Boundary Analysis and Threshold Identification (Priority: P3)

**Goal**: Perform statistical analysis (K-S test, Piecewise Regression) to identify the specific optical flow magnitude threshold where artifact generation becomes significant.

**Independent Test**: Running the post-processing script on metric reports outputs a statistical summary identifying the correlation between flow magnitude and SSIM drop, and the significance of the memory reduction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for AnalysisResult schema in `tests/contract/test_analysis_schema.py`
- [X] T026 [P] [US3] Unit test for Piecewise Regression logic in `tests/unit/test_change_point_detection.py`

### Implementation for User Story 3

- [X] T027 [US3] Implement data aggregator in `code/analysis/stats.py` to merge baseline and flow metrics into paired datasets; **Depends on T017 (US1) and T024 (US2)**. **Note**: This task explicitly waits for both US1 and US2 completion. **No [P] tag**.
- [X] T028 [US3] Implement **Kolmogorov-Smirnov (K-S) test** in `code/analysis/stats.py` to compare error distributions between baseline and flow methods; **Note**: Per Plan.md "Critical Methodological Updates", this is the **SECONDARY** check for distribution differences. **Depends on T027**.
- [X] T029 [US3] Implement **Piecewise Regression (Change-Point Detection)** in `code/analysis/stats.py` using `ruptures` to identify flow-magnitude thresholds where SSIM degradation exceeds significance; **Note**: Per Plan.md "Critical Methodological Updates", this is the **PRIMARY** method for threshold identification (overrides Spec FR-006 primary method). **Depends on T027**.
- [X] T030 [US3] Implement sensitivity analysis script in `code/analysis/stats.py` sweeping the **specific set of cutoff values {0.01, 0.05, 0.1}** (as required by Spec FR-007 and SC-004) and reporting **inconsistency rates** across these values; **Depends on T029**.
- [X] T031 [US3] Generate final statistical summary report in `code/analysis/reporter.py` (outputs to `results/summary.md` and `data/metrics/analysis_results.json`)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Generate `results/summary.md` with required sections: Executive Summary, Methodology (Baseline vs Flow-Coherence), Results (Memory, BSS, Flickering), Statistical Boundary Analysis (Thresholds, K-S p-values, Sensitivity), and Conclusion.
- [X] T032b [P] Update `docs/` (README, quickstart.md) with execution instructions and data flow diagrams.
- [X] T033 [P] Code cleanup and refactoring: Remove unused imports, enforce line length < 88, verify with `ruff check.` with zero warnings
- [X] T034 [P] Performance optimization across all stories: Target peak RAM reduction to < 6GB; verify via memory profiler run on full pipeline and record peak usage
- [X] T035 [P] Run quickstart.md validation: Execute `bash docs/quickstart.sh`; success criteria: script completes without error and generates `results/summary.md`
- [X] T036 Final integration test: Run full pipeline (US1 + US2 + US3) on a small subset to verify end-to-end data flow

---

## Phase N+1: Research Validation & Data Integrity (Revision Concerns)

**Goal**: Ensure data sourcing is robust, stratification is scientifically valid, and the pilot phase accurately predicts CI feasibility.

### Implementation for Research Validation

- [ ] T037 [US1] Implement dataset stratification validator in `code/data/processor.py`: Add a post-download check that verifies the 50-clip subset contains at least 15 clips in each motion category (Static, Slow Rigid, Fast Non-Rigid) based on the quantitative flow thresholds defined in **Plan.md** (0.5, 5.0). **Source**: Plan.md Dataset Strategy (overrides Spec qualitative categories). **Logic**: Read `STRATIFICATION_THRESHOLDS` from `code/config.py`. **Output**: `data/metrics/stratification_report.json`. **Verification**: If `len(static) < 15` OR `len(slow) < 15` OR `len(fast) < 15`, raise `RuntimeError("Stratification failed: insufficient clips in category")`.
- [ ] T038 [US1] Implement "Pilot Run" script in `code/main.py` (pilot mode): Execute a subset of the full pipeline (Download -> Flow -> Inference -> Metrics) to measure `time_per_clip` and `peak_memory` empirically; write results to `data/metrics/pilot_report.json`. **Schema**: JSON must contain keys `time_per_clip` (float) and `peak_memory` (float). **Note**: This task is critical to resolve the Spec/Plan sample size conflict (Spec says a substantial quantity, Plan says 50). **Verify**: `time_per_clip > 0`.
- [ ] T039 [US3] Extend `code/analysis/stats.py` to consume `pilot_report.json` and dynamically calculate the maximum feasible `N` for the time limit using the formula `floor(time_budget / time_per_clip)`; update the main pipeline to abort or adjust `N` if the pilot suggests the full 50 clips will exceed the time budget. **Output**: Write adjusted `N` to `data/metrics/adjusted_n.json` and update `code/config.py` CLI arguments. **Note**: This ensures the Plan's N=50 is validated against the Spec's 6h constraint.
- [ ] T040 [US1] Implement "Flow Magnitude Distribution" plotter in `code/analysis/reporter.py`: Generate a histogram of the mean flow magnitudes for the 50 clips to visually confirm the stratification covers the required range (0.5 to >5.0) before analysis begins.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Research Validation (Phase N+1)**: Depends on Foundational and US1/US2 implementation to ensure data pipelines are ready for validation

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T009 (Flow computation) which is foundational for this story, but can run in parallel with US1 inference if flow is pre-computed
- **User Story 3 (P3)**: Depends on completion of US1 (T017) and US2 (T024) to have data to analyze

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) *except T009a which must precede T009 due to resource contention*
- Once Foundational phase completes, US1 and US2 can proceed in parallel (data download/flow prep can be parallelized)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for MetricRecord schema in tests/contract/test_metric_schema.py"
Task: "Integration test for baseline inference pipeline in tests/integration/test_baseline_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement dataset downloader in code/data/downloader.py"
Task: "Implement video processor in code/data/processor.py"
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
 - Developer A: User Story 1 (Baseline)
 - Developer B: User Story 2 (Flow-Coherence) - can start flow computation early
 - Developer C: User Story 3 (Analysis) - waits for data
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
- **Data Integrity**: All dataset downloads MUST fail loudly; no synthetic fallbacks allowed.
- **Compute Constraints**: All inference must be CPU-optimized; ensure N=50 clips fits within 6h limit.
- **Metric Validity**: Use Background Stability Score (BSS) and Flow-Normalized SSIM as defined in plan.md. BSS isolates background and compares to GT; Consecutive Frame SSIM measures flickering. **T016a implements Consecutive SSIM for Baseline; T016b implements Consecutive SSIM + BSS for Flow-Coherence (FR-005 + Plan).**
- **Threshold Identification**: Piecewise Regression is the PRIMARY method for threshold identification (Plan); K-S test is SECONDARY (Spec/Plan).
- **Stratification Thresholds**: Numeric thresholds (0.5, 5.0) are derived from Plan.md Dataset Strategy (overrides Spec); T037 defers to Plan definition and reads from config.
- **Sensitivity Analysis Cutoffs**: Must use {0.01, 0.05, 0.1} as per Spec FR-007.
- **Flow Computation**: T009a is for stratification (US1); T009 is for model warping (US2). T009a must complete before T009 to avoid resource contention.
- **Pilot Validation**: T038/T039 are critical to prevent CI timeout failures and resolve Spec/Plan sample size conflict; the pipeline must dynamically adjust N based on pilot results.
- **Stratification Verification**: T037 ensures the dataset is not biased towards "easy" clips; failure to stratify must abort the run.