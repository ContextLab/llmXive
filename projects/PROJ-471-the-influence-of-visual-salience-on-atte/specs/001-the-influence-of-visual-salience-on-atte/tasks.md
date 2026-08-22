# Tasks: The Influence of Visual Salience on Attentional Bias in Moral Judgements

**Input**: Design documents from `/specs/001-influence-of-visual-salience/`
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
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (torch, ultralytics, statsmodels, pandas, datasets, numpy, opencv-python, pyyaml, scipy, simr)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase AND Phase 2.5 (Scope Freeze) are complete

- [X] T004 Implement `code/config.py` for paths, seeds, and hyperparameters
- [X] T005 [P] Setup structured logging in `code/utils/logging.py`
- [X] T006 [P] Implement `code/utils/versioning.py` for SHA-256 artifact hashing and `state.yaml` updates (Constitution Principle V)
- [X] T007 [P] Implement `code/utils/reference_validator.py` for citation verification (Constitution Principle II)
- [X] T008 Create base data models (`StimulusImage`, `FixationTrial`) in `code/data_models.py` (Scope: Face only, per SCR-001)
- [ ] T009a [P] Create `.env.example` file listing required keys: `HF_TOKEN`, `DATA_PATH`, `SEED`, `GPU_DEVICE`
- [ ] T009b [P] Implement `code/config.py` to load `.env` using `python-dotenv` and validate required keys

**Checkpoint**: Foundation ready - Scope Freeze (Phase 2.5) must complete next

---

## Phase 2.5: Scope Freeze (Governance & SCR Application)

**Purpose**: Formalize and apply Spec Change Requests (SCR) to remove infeasible requirements (FR-008, FR-009) BEFORE implementation begins. This ensures all subsequent tasks operate on a stable, consistent spec.

- [X] T020a [US1] **Governance (SCR Draft)**: Create `docs/scr_001_weapons_exclusion.md` documenting the exclusion of FR-008 ("Weapons"). **Output Fields**: `reason` (lack of COCO class), `impact` (study scope reduced to Face vs Background), `alternative` (none), `status` (draft). **Action**: Write this file to `docs/`.
- [ ] T020c [US1] **Governance (SCR Apply)**: **Edit `spec.md` to REMOVE FR-008** from the Functional Requirements list and update User Stories to reflect "Face" ROIs only. **Edit `plan.md`** to explicitly state FR-008 is excluded. **Dependency**: Must complete after T020a.
- [X] T030c [US3] **Governance (SCR Draft)**: Create `docs/scr_002_lowlevel_covariates_exclusion.md` documenting the exclusion of FR-009 due to multicollinearity. **Action**: Write this file to `docs/`.
- [ ] T030e [US3] **Governance (SCR Apply)**: **Edit `spec.md` to REMOVE FR-009** from the Functional Requirements list. **Edit `plan.md`** to explicitly state FR-009 is excluded. **Dependency**: Must complete after T030c.

**Checkpoint**: Spec and Plan are now stable and consistent. Implementation can begin.

---

## Phase 3: User Story 1 - Data Ingestion and Salience Map Generation (Priority: P1) 🎯 MVP

**Goal**: Download an OpenNeuro dataset, extract a representative set of stimulus images, and generate CPU-compatible DeepGaze II salience maps.

**Independent Test**: Run ingestion on a subset of images; verify multiple `.npy`/`.png` maps generated with matching resolution; confirm no CUDA errors and RAM < 7GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for `code/ingestion/download_data.py` mocking Hugging Face fetch in `tests/unit/test_download_data.py`
- [X] T011 [P] [US1] Unit test for `code/ingestion/salience_gen.py` verifying CPU-only DeepGaze II initialization in `tests/unit/test_salience_gen.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/ingestion/download_data.py` to fetch a specific dataset via `datasets.load_dataset` (streaming=False for local cache) and verify checksums
- [ ] T013a [US1] Implement `code/ingestion/fallback_heuristic.py` to run GBVS (Graph-Based Visual Saliency) on an image if DeepGaze II fails. **Input**: Image path. **Output**: Salience map (`.npy`). **Error Handling**: If GBVS fails, raise an error to trigger exclusion.
- [ ] T013 [US1] Implement `code/ingestion/salience_gen.py` to load DeepGaze II in CPU mode. **Verification**: Must explicitly enforce `device='cpu'` in the model configuration. **Error Handling**: If DeepGaze II fails on a high-contrast image, **execute T013a (GBVS)**. If T013a also fails, **EXCLUDE the image** from the output. Log exclusion warnings. **Dependency**: T013a.
- [ ] T014 [US1] Add memory AND CPU time monitoring to `salience_gen.py` to enforce < 7GB RAM limit and log total execution duration (CPU time) to verify compliance with the 6-hour limit (SC-002). Log warnings if exceeded.
- [ ] T016a [US1] Implement `code/ingestion/metadata_writer.py` to create `data/processed/salience_maps/metadata.json` containing a list of processed image IDs and their map paths. **Output**: `data/processed/salience_maps/metadata.json`.
- [ ] T016 [US1] Append "correlational only" disclaimer to `data/processed/salience_maps/metadata.json`. **Mapping Logic**: Extract `StimulusID` from the source filename and write the map as `data/processed/salience_maps/{StimulusID}.npy`. **Dependency**: T016a.
- [ ] T018a [US1] Implement `code/ingestion/completion_validator.py` to aggregate the count of generated salience maps, compare against the source dataset count, and log a pass/fail status for SC-001. Output: `data/interim/salience_validation_report.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Attention Metric Extraction and Alignment (Priority: P2)

**Goal**: Parse eye-tracking data, extract fixation metrics for "Face" ROIs (excluding "weapons" due to SCR-001), and align with salience scores.

**Independent Test**: Process a single trial; verify output CSV contains trial ID, dwell time on "Face", and mean salience score for that region with no ID mismatches.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for `code/processing/eye_tracking.py` parsing a mock fixation file in `tests/unit/test_eye_tracking.py`
- [X] T020 [P] [US2] Unit test for `code/processing/segmentation.py` verifying YOLOv8 face mask generation in `tests/unit/test_segmentation.py`

### Implementation for User Story 2

- [X] T020d [US2] Implement `code/processing/segmentation.py` using YOLOv8 (COCO `face` class) to generate semantic masks for "Face" regions. **Logic**: First check if pre-segmented masks exist in the dataset; if missing, run YOLOv8. **Dependency**: Must wait for T020c (SCR Apply) to ensure "Weapons" are not attempted. **Note**: "Weapons" excluded per SCR-001.
- [X] T021 [US2] Implement `code/processing/eye_tracking.py` to parse raw eye-tracking files from `data/raw/[subject_id]/eyetracking.tsv`, filter for "Face" ROI, and calculate First-Fixation Probability, Dwell Time, and Latency. **Output**: Write to `data/interim/fixation_metrics.csv`. **Validation**: Verify column `first_fixation_prob` exists and is numeric.
- [X] T023 [US2] Handle missing fixation data: exclude trial from analysis and log warning (Edge Case)
- [X] T024 [US2] Implement `code/processing/alignment.py` to merge salience scores (from US1) with eye-tracking metrics on `TrialID`
- [X] T025 [US2] Validate alignment: ensure no trial ID mismatches and flag images with empty/invalid masks for manual review
- [X] T026 [US2] Write aligned dataset to `data/processed/aligned_metrics.csv` with "correlational only" disclaimer (FR-007)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Robustness Verification (Priority: P3)

**Goal**: Fit LMMs, apply FDR correction, perform sensitivity analysis, and verify power/collinearity.

**Independent Test**: Run analysis on aligned dataset; verify regression summary with p-values, sensitivity plot, and VIF diagnostics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for `code/analysis/lmm_fit.py` with mock dataframe in `tests/unit/test_lmm_fit.py`
- [X] T028 [P] [US3] Unit test for `code/analysis/robustness.py` verifying FDR calculation in `tests/unit/test_robustness.py`

### Implementation for User Story 3

- [X] T029a [US3] **LMM Power Analysis**: Implement `code/analysis/lmm_power.py` to estimate statistical power for the planned LMM using a simulation-based approach (e.g., `simr` package). **Assumption**: Use a medium effect size (d=0.5) for the pilot simulation if no pilot data exists. **Output**: `data/interim/power_analysis_report.json`. **Dependency**: Must run BEFORE T032 (LMM Fit).
- [X] T029b [US3] **Fallback Descriptive Stats**: Implement `code/analysis/descriptive_fallback.py` to generate summary statistics (mean, std, median) for all metrics if N < 30. **Trigger**: Activated by T029a failure or N < 30 check. **Output**: `data/processed/descriptive_stats.json`.
- [X] T029c [US3] **Enforce Power Gate**: Implement logic to halt the pipeline if T029a reports power < 0.8. **Action**: Write `data/interim/invalid_for_inference_flag.json` containing the reason and prevent T032 from executing. **Output**: This flag acts as a hard block for the study.
- [ ] T030b [US3] **Generate Low-Level Features**: Implement `code/analysis/feature_gen.py` to compute luminance (mean intensity), contrast (std dev), and edge density (Canny count) for all images in `data/raw`. **Output**: `data/interim/low_level_features.csv`. **Dependency**: Must run before T030.
- [ ] T030 [US3] **VIF Calculation**: Implement `code/analysis/vif_calc.py` to calculate Variance Inflation Factor (VIF) for the salience predictor against the **generated** low-level features (from T030b). **Output**: `data/interim/vif_verification.json`. **Dependency**: Must run AFTER T030b.
- [ ] T030a [US3] **VIF Interpretation**: Analyze `data/interim/vif_verification.json`. If VIF > 5, log justification for excluding FR-009. **Output**: Log entry in `data/interim/vif_report.txt`.
- [ ] T031 [US3] Apply FDR correction to all p-values (FR-006)
- [ ] T032 [US3] Implement `code/analysis/lmm_fit.py` to fit Model A (random intercepts) and Model B (random intercepts + slopes for salience) using `statsmodels`. **Dependency**: Must check T029c flag; if "Invalid", skip fitting and log error.
- [ ] T033 [US3] Implement sensitivity analysis in `code/analysis/robustness.py` comparing Model A vs. Model B effect significance
- [ ] T034 [US3] Generate sensitivity analysis plot and append "correlational only" disclaimer to all output artifacts (FR-007)
- [ ] T035 [US3] Log null results explicitly linked to "theories of attentional control hierarchy" (Constitution Principle VII)
- [ ] T036 [US3] Write final `AnalysisResult` JSON/CSV to `data/processed/results.json`. **Requirement**: Must append "correlational only" disclaimer to this file if p-values < 0.05 are present (FR-007).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T037 [P] Documentation updates in `README.md` and `docs/`
- [ ] T038 Code cleanup and refactoring
- [ ] T039 Performance optimization for salience generation (batching)
- [ ] T040 [P] Run full integration test suite in `tests/integration/test_pipeline.py`
- [ ] T041 Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Scope Freeze (Phase 2.5)**: **DEPENDS ON Phase 2**. **BLOCKS ALL User Stories**. Ensures spec/plan stability.
- **User Stories (Phase 3+)**: All depend on Phase 2.5 completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2.5 - No dependencies on other stories
- **User Story 2 (P2)**: **Strictly depends on US1 completion** (specifically T016 and T018a) to ensure salience maps exist before alignment (T024). US2 cannot start until US1 is complete.
- **User Story 3 (P3)**: **Strictly depends on US2 completion** (specifically T026) to ensure aligned metrics exist before LMM fitting (T032). US3 cannot start until US2 is complete.
- **Note**: US2 and US3 cannot run independently of US1/US2 data generation.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for download_data.py in tests/unit/test_download_data.py"
Task: "Unit test for salience_gen.py in tests/unit/test_salience_gen.py"

# Launch all models for User Story 1 together:
Task: "Implement download_data.py in code/ingestion/download_data.py"
Task: "Implement salience_gen.py in code/ingestion/salience_gen.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2.5: Scope Freeze (CRITICAL - stabilizes spec)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (Salience maps generated)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational + Scope Freeze → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (Alignment) → Deploy/Demo
4. Add User Story 3 → Test independently (Analysis) → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + Scope Freeze together
2. Once Scope Freeze is done:
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Eye Tracking & Alignment) - *Requires US1 mock data for dev*
 - Developer C: User Story 3 (Analysis) - *Requires US2 mock data for dev*
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
- **Spec Gap**: "Weapons" (FR-008) excluded; only "Face" ROIs implemented (see T020a-c, SCR-001).
- **Spec Contradiction**: Low-level covariates (FR-009) excluded to prevent multicollinearity with DeepGaze II (see T030c-e, SCR-002).
- **Data Integrity**: No synthetic data fallbacks; if real data fetch fails, the pipeline must fail loudly.
- **SCR Workflow**: Tasks T020a-c and T030c-e execute the formal SCR workflow to update `spec.md` and `plan.md` BEFORE implementation.
- **Power Gate**: T029c enforces SC-003; if power < 0.8, the study is halted and marked "Invalid for Inference".
- **Execution Gate Compliance**: Tasks T013 and T020d explicitly forbid synthetic fallbacks and enforce "fail loudly" behavior to satisfy the fabrication guard.
- **Compute Feasibility**: T013 enforces CPU-only DeepGaze II; if this fails on the free runner, the execution stage will detect the CUDA error and auto-offload to Kaggle GPU as per the "Compute Feasibility" rule.
- **Data Streaming**: T012 uses `datasets.load_dataset` with `streaming=True` logic where applicable to handle large files within RAM limits, avoiding synthetic substitution.
- **Fallback Logic**: T013a provides the required heuristic fallback; T013 excludes only if T013a fails.
- **VIF Logic**: T030b generates features; T030 calculates VIF on generated features.