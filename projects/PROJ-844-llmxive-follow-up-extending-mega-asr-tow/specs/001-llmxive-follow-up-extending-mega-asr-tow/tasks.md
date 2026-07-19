# Tasks: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Input**: Design documents from `/specs/001-semantic-collapse-threshold/`
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

- [X] T001a [P] Create `code/` directory at repository root per plan.md
- [X] T001b [P] Create `data/raw/` directory at repository root per plan.md
- [X] T001c [P] Create `data/derived/` directory at repository root per plan.md
- [X] T001d [P] Create `tests/` directory at repository root per plan.md
- [X] T002a [P] Create `ruff.toml` configuration file with specific rules for linting
- [X] T002b [P] Create `pyproject.toml` configuration file with specific rules for black formatting
- [X] T003 [P] Implement `code/config.py` with paths, random seeds, and hyperparameters (thresholds, distortion counts)
- [X] T004 [P] Implement `code/monitor_resources.py` to track peak RSS and wall-clock time (SC-004)
- [X] T005 [P] Implement `code/hash_updater.py` to compute content hashes for `data/derived/` and update state YAML (Principle V)
- [X] T006 [P] Create base entity classes (`AudioClip`, `DistortionVector`, `StressCurve`) in `code/models.py` (or dataclasses)
- [X] T008 [P] Initialize `tests/unit/` directory with `__init__.py` and a basic pytest configuration file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data fetching, stratification, and distortion engine setup.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007a [P] Fetch and verify checksums for **LibriSpeech** subset in `code/data_loader.py`; implement stratified sampling by speaker ID and SNR bucket as per FR-001 (Plan deviation from Voices-in-the-Wild-2M to Verified Accuracy)
- [X] T007b [P] Fetch and verify checksums for **CORAA-MUPE-ASR** subset in `code/data_loader.py`; implement stratified sampling by speaker ID and SNR bucket as per FR-001 (Plan deviation from Voices-in-the-Wild-2M to Verified Accuracy)
- [X] T007c [P] Verify dataset coverage for multiple compound distortion scenarios in `code/data_loader.py`; log a warning and proceed with available subset if specific combinations are missing, as per FR-001 edge cases
- [X] T012 [P] Implement `code/distortion_engine.py` to apply multiple compound distortion vectors (SNR/RT60 combinations) incrementally per FR-002; logic must support variable count of scenarios

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Compound Distortion Stress Curves (Priority: P1) 🎯 MVP

**Goal**: Systematically apply a diverse range of compound acoustic distortions to a stratified subset of audio data to generate stress curves mapping distortion intensity to semantic integrity.

**Independent Test**: Run on a sample of audio clips; verify output CSV/JSON contains the expected number of rows per clip with acoustic parameters, ASR hypothesis, and Semantic Similarity Score (SSS).

### Implementation for User Story 1

- [X] T009 [P] [US1] Unit test for `code/distortion_engine.py` verifying that a comprehensive set of distinct vectors is generated from parameter ranges.
- [X] T010 [US1] Extend `code/data_loader.py` to add US1-specific stress-curve generation logic (building on T012 engine); Depends on T007a-c, T012
- [X] T011 [US1] Integration test for `code/data_loader.py` verifying stratified sampling and stress-curve generation workflow (Depends on T010)
- [X] T013 [US1] Implement `code/metrics.py` to compute SSS using `all-MiniLM-L6-v2` (CPU-only) per FR-003
- [X] T014 [US1] Implement `code/metrics.py` to compute WER using `jiwer` for baseline and distorted hypotheses per FR-009
- [X] T016 [US1] Implement validation logic in `code/metrics.py` to handle edge cases: oscillating SSS (hysteresis), empty ASR output, and missing distortion scenarios (FR-001 edge cases)
- [ ] T015 [US1] Implement `code/main.py` orchestration to generate stress curves and save to `data/derived/stress_curves.parquet`; CLI arguments: `--input-path`, `--output-path`, `--models-list` (Depends on T016 for edge case safety)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Identify Semantic Collapse Points (Priority: P2)

**Goal**: Automatically identify the precise "collapse intensity" for each model/scenario where SSS drops below a normalized threshold. AND WER spikes >2x baseline.

**Independent Test**: Provide a pre-calculated stress curve with a known drop; verify the system correctly identifies the interpolation point or step meeting both criteria.

### Implementation for User Story 2

- [X] T017 [P] [US2] Unit test for collapse detection logic with synthetic data (monotonic drop, no drop, oscillation)
- [X] T020b [US2] Explicitly calculate and store `baseline_sss.json` for each model/scenario as a prerequisite artifact for normalization (FR-010); Schema: `{"model_id": str, "scenario_id": str, "baseline_value": float}`; Logic: Average SSS of clean audio subset
- [X] T020c [US2] Explicitly calculate and store `baseline_wer.json` for each model/scenario as a prerequisite artifact for WER spike threshold (FR-004, FR-009); Schema: `{"model_id": str, "scenario_id": str, "baseline_value": float}`; Logic: Average WER of clean audio subset
- [X] T019 [US2] Extend `code/metrics.py` to add collapse detection: Identify intensity where SSS < 0.5 (normalized to baseline) AND WER > 2x baseline per FR-004, FR-009 (Depends on T015, T020b, T020c)
- [X] T018 [P] [US2] Integration test verifying WER spike confirmation logic in `code/metrics.py` (Depends on T019 implementation)
- [X] T021 [US2] Implement handling for "No Collapse" scenarios (record as "Max Tested") per US-2 Acceptance 2
- [X] T022 [US2] Generate `data/derived/collapse_points.parquet` containing the identified collapse intensity vectors per model/scenario

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Human Annotation & HVCM (Priority: P2 - Dependent on US1)

**Goal**: Generate human-annotated validation set and derive the Human-Validated Collapse Margin (HVCM) to break circularity.

**Independent Test**: Verify `data/validation/human_annotations.csv` exists with correct schema and `data/derived/hvcm_targets.parquet` is generated.

### Implementation for Human Annotation

- [ ] T030a [US1/US2] Generate a human-annotated transcript dataset for the validation subset: Implement script in `code/human_validation.py` to select a representative sample (using the same stratification logic as T007a/b), define annotation protocol (intelligibility score on a **0-5 Likert scale**, as defined by the research question and method outlined in the cited work (see research.md for full citation)), and generate `data/validation/human_annotations.csv`. Schema: `clip_id`, `distortion_vector_id`, `human_intelligibility_score_0_5`. (Mandatory per FR-011; Depends on T015) <!-- FAILED: unspecified -->
- [ ] T030b [US3] Implement Human-Validated Collapse Margin (HVCM) calculation in `code/metrics.py` to derive the primary regression target from `data/validation/human_annotations.csv` and `data/derived/stress_curves.parquet`, breaking circularity per plan.md. Logic: **HVCM = SSS-based collapse point - human-annotated collapse point (derived from 0-5 Likert scores)**. (Depends on T030a, T022) <!-- FAILED: unspecified -->

**Checkpoint**: HVCM target is now available for US3

---

## Phase 6: User Story 3 - Predict Collapse via Critical Interaction Vector (Priority: P3)

**Goal**: Train a lightweight regression model to predict collapse intensities using acoustic parameter vectors + interaction terms, and validate the "critical interaction vector" hypothesis.

**Independent Test**: Split data, train model, verify R² > 0.6 on test set and report coefficients.

### Implementation for User Story 3

- [X] T023 [P] [US3] Unit test for interaction term generation (SNR×RT60, SNR², RT60²)
- [X] T025a [US3] Implement `code/models.py` function `generate_interaction_terms` to explicitly create engineered interaction terms (SNR×RT60, SNR², RT60²) for feature input (Depends on T023)
- [X] T025b [US3] Verify that `generate_interaction_terms` output is explicitly passed as features to the model training function in `code/models.py` (T026) to prevent silent implementation failure (FR-005)
- [X] T024 [US3] Implement `code/statistics.py` for multiple-comparison correction (Bonferroni/FDR) on interaction effects per FR-008
- [X] T025 [US3] Generate `data/derived/corrected_pvalues.json` with corrected p-values and report statistical significance per SC-003
- [X] T026 [US3] Implement `code/models.py` to train CPU-tractable regression (Linear/Polynomial degree≤3 or DT max_depth≤5) using features from T025a and target HVCM from T030b per FR-005 (Depends on T030b)
- [X] T027 [US3] Implement `code/analysis.py` to perform sensitivity analysis: **sweep threshold from 0.40 to 0.60 in increments of 0.05** and report variance in critical interaction vector per FR-006
- [X] T028 [US3] Implement cross-model comparison logic to calculate cosine similarity of critical vectors across a set of small ASR models selected based on SC-004 (CPU-tractability) constraints; Output: `data/derived/cross_model_similarity.csv` with columns: `model_a`, `model_b`, `cosine_similarity`. (Depends on T026)
- [ ] T029 [US3] Implement validation against held-out human-annotated subset: Correlate SSS-based collapse with Human-Validated Collapse Margin (HVCM) from `data/validation/human_annotations.csv` per FR-011 (Depends on T026, T030b)
- [ ] T030 [US3] Generate final report artifacts in `data/derived/regression_results.json` and `data/derived/sensitivity_analysis.csv` <!-- FAILED: unspecified -->
- [X] T036 [US3] Generate final report section and code comments in `research.md` and `code/models.py` explicitly framing all predictive findings as ASSOCIATIONAL, avoiding causal claims per FR-007 (Depends on T030 for data availability)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Documentation updates in `docs/` including `research.md` citations for LibriSpeech/CORAA-MUPE-ASR
- [X] T032 Generate `data/derived/resource_monitoring_report.json` and Verify peak RSS < 7GB as a gate before proceeding (SC-004)
- [X] T033 Performance optimization: Parallelize ASR inference and distortion application where safe
- [X] T034 [P] Additional unit tests in `tests/unit/` for edge cases and statistical corrections
- [X] T035 Run `quickstart.md` validation to ensure end-to-end reproducibility on GitHub Actions

---

## Phase 7: Execution Verification & Safety Gates (Revision Response)

**Purpose**: Address execution feedback regarding CPU feasibility, data integrity, and statistical rigor. These tasks ensure the pipeline runs successfully on the free tier without fabrication.

- [X] T037 [P] [US1/US2/US3] Implement **Defensive CPU Enforcement** in `code/metrics.py` and `code/models.py` to **raise `RuntimeError` immediately** if any CUDA device is detected or if GPU libraries are inadvertently imported (Ensures "Fail Loudly" principle; prevents silent GPU fallback)
- [X] T038 [P] [US1] Add a pre-flight check in `code/main.py` that validates the real dataset (LibriSpeech/CORAA) is fully downloadable and accessible before initiating the distortion loop; if download fails, raise an exception rather than falling back to synthetic data (Enforces "Fail Loudly" rule)
- [X] T039 [US3] Implement a memory-streaming wrapper in `code/data_loader.py` that processes the stress curve data in chunks (e.g., 1000 rows at a time) to ensure peak RSS never exceeds 7GB during the regression training phase (Addresses SC-004 memory constraint)
- [X] T040 [P] [US3] Add a unit test in `tests/unit/test_statistics.py` that verifies the Bonferroni correction factor is correctly applied based on the exact number of interaction terms tested, ensuring p-values are not artificially inflated
- [X] T041 [US3] Add a "Causality Warning" check in `code/models.py` that asserts the regression target (HVCM) is derived from human annotations and not from the SSS metric itself, raising an error if `human_intelligibility_score` is missing from the training data (Enforces FR-011 and breaks circularity)
- [X] T042 [P] [US1/US2] Implement a "Distortion Coverage" validator in `code/distortion_engine.py` that logs a detailed report of which **applied distortion scenarios** were successfully applied to the sample and which were skipped, ensuring the "missing scenarios" edge case is handled transparently (FR-001)
- [X] T043 [US3] Implement a "Threshold Stability" check in `code/analysis.py` that verifies the critical interaction vector does not change sign or magnitude by >10% when the collapse threshold is swept from 0.40 to 0.60 (Validates FR-006 and SC-002) <!-- FAILED: unspecified -->

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Execution Verification (Phase 7)**: Must be completed before final deployment to ensure CPU feasibility and data integrity

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (requires stress curve data)
- **User Story 3 (P3)**: Depends on US2 (requires collapse points) and Human Annotation (Phase 5)
- **Phase 7 Tasks**: Can run in parallel with Phase 6 implementation but must pass before final report generation

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
- Phase 7 safety checks can run in parallel with Phase 6 implementation

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for distortion engine"
Task: "Integration test for data loader"

# Launch all models for User Story 1 together:
Task: "Implement data loader"
Task: "Implement distortion engine"
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
 - Developer D: Phase 7 Safety Gates (Execution Verification)
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
- **Critical Constraint**: All ASR and embedding models MUST run on CPU (no CUDA/GPU). Use `whisper-tiny` and `all-MiniLM-L-v2`.
- **Data Integrity**: Use real data from LibriSpeech/CORAA-MUPE-ASR. No synthetic data fabrication.
- **Statistical Rigor**: Apply multiple-comparison correction and associational framing strictly.
- **Human Validation**: FR-011 requires generating human annotations (T030a) with a **0-5 Likert scale** before US2/US3 validation.
- **Methodology**: HVCM (T030b) is the primary regression target to break circularity.
- **Revision Update**: Phase 7 tasks added to address execution feedback regarding CPU feasibility, data integrity, and statistical rigor (T037-T043).
