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

- [ ] T001a [P] Create project root directory structure (`code/`, `data/raw/`, `data/derived/`, `tests/`) at repository root per plan.md
- [ ] T001b [P] Initialize `code/` directory with `__init__.py` and `requirements.txt` (pinned `scikit-learn`, `transformers`, `torch`, `librosa`, `pandas`, `numpy`, `datasets`, `sentence-transformers`, `jiwer`)
- [ ] T001c [P] Initialize `data/` directories (`raw/`, `derived/`, `validation/`) with `.gitkeep` files
- [ ] T002 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data fetching, stratification, and human annotation generation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Implement `code/config.py` with paths, random seeds, and hyperparameters (thresholds, distortion counts)
- [ ] T004 [P] Implement `code/monitor_resources.py` to track peak RSS and wall-clock time (SC-004)
- [ ] T005 [P] Implement `code/hash_updater.py` to compute content hashes for `data/derived/` and update state YAML (Principle V)
- [ ] T006 [P] Create base entity classes (`AudioClip`, `DistortionVector`, `StressCurve`) in `code/models.py` (or dataclasses)
- [ ] T007a [P] Fetch and verify checksums for LibriSpeech subset in `code/data_loader.py`; implement stratified sampling by speaker ID and SNR bucket as per FR-001 (Plan deviation from Voices-in-the-Wild-2M)
- [ ] T007b [P] Fetch and verify checksums for CORAA-MUPE-ASR subset in `code/data_loader.py`; implement stratified sampling by speaker ID and SNR bucket as per FR-001 (Plan deviation from Voices-in-the-Wild-2M)
- [ ] T007c [P] Document dataset substitution rationale in `docs/dataset_substitution.md` and verify support for 54 compound distortion scenarios per FR-002
- [ ] T008 [P] Implement unit test framework structure in `tests/unit/`
- [ ] T030a [P] [US1/US2/US3] Generate a human-annotated corpus of transcripts for the validation subset.: Implement script in `code/human_validation.py` to select a representative sample of clips, define annotation protocol (intelligibility score 0-1), and generate `data/validation/human_annotations.csv` (Mandatory per FR-011)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Compound Distortion Stress Curves (Priority: P1) 🎯 MVP

**Goal**: Systematically apply 54 compound acoustic distortions to a stratified subset of audio data to generate stress curves mapping distortion intensity to semantic integrity.

**Independent Test**: Run on a sample of audio clips; verify output CSV/JSON contains the expected number of rows per clip with acoustic parameters, ASR hypothesis, and Semantic Similarity Score (SSS).

### Implementation for User Story 1

- [ ] T009 [P] [US1] Unit test for `code/distortion_engine.py` verifying 54 distinct vectors are generated from parameter ranges
- [ ] T010 [P] [US1] Extend `code/data_loader.py` to add US1-specific stress-curve generation logic (building on T007a/b stratified subset)
- [ ] T011 [US1] Integration test for `code/data_loader.py` verifying stratified sampling and stress-curve generation workflow (Depends on T010)
- [ ] T012 [US1] Implement `code/distortion_engine.py` to apply 54 compound distortion vectors (SNR/RT60 combinations) incrementally per FR-002
- [ ] T013 [US1] Implement `code/metrics.py` to compute SSS using `all-MiniLM-L6-v2` (CPU-only) per FR-003
- [ ] T014 [US1] Implement `code/metrics.py` to compute WER using `jiwer` for baseline and distorted hypotheses per FR-009
- [ ] T015 [US1] Implement `code/main.py` orchestration to generate stress curves and save to `data/derived/stress_curves.parquet`
- [ ] T016 [US1] Implement validation logic in `code/metrics.py` to handle edge cases: oscillating SSS (hysteresis), empty ASR output, and missing distortion scenarios (FR-001 edge cases)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Identify Semantic Collapse Points (Priority: P2)

**Goal**: Automatically identify the precise "collapse intensity" for each model/scenario where SSS drops below a normalized threshold. AND WER spikes >2x baseline.

**Independent Test**: Provide a pre-calculated stress curve with a known drop; verify the system correctly identifies the interpolation point or step meeting both criteria.

### Implementation for User Story 2

- [ ] T017 [P] [US2] Unit test for collapse detection logic with synthetic data (monotonic drop, no drop, oscillation)
- [ ] T018 [P] [US2] Integration test verifying WER spike confirmation logic in `code/metrics.py`
- [ ] T019 [US2] Extend `code/metrics.py` to add collapse detection: Identify intensity where SSS < 0.5 (normalized to baseline) AND WER > 2x baseline per FR-004, FR-009
- [ ] T020a [US2] Extend `code/metrics.py` to add normalization logic: Calculate baseline SSS for each model and normalize the 0.5 threshold per FR-010
- [ ] T020b [US2] Explicitly calculate and store `baseline_sss.json` for each model/scenario as a prerequisite artifact for normalization (FR-010)
- [ ] T021 [US2] Implement handling for "No Collapse" scenarios (record as "Max Tested") per US-2 Acceptance 2
- [ ] T022 [US2] Generate `data/derived/collapse_points.parquet` containing the identified collapse intensity vectors per model/scenario

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predict Collapse via Critical Interaction Vector (Priority: P3)

**Goal**: Train a lightweight regression model to predict collapse intensities using acoustic parameter vectors + interaction terms, and validate the "critical interaction vector" hypothesis.

**Independent Test**: Split data, train model, verify R² > 0.6 on test set and report coefficients.

### Implementation for User Story 3

- [ ] T023 [P] [US3] Unit test for interaction term generation (SNR×RT60, SNR², RT60²)
- [ ] T024 [US3] Implement `code/statistics.py` for multiple-comparison correction (Bonferroni/FDR) on interaction effects per FR-008
- [ ] T025 [US3] Generate `data/derived/corrected_pvalues.json` with corrected p-values and report statistical significance per SC-003
- [ ] T026 [US3] Implement `code/models.py` to train CPU-tractable regression (Linear/Polynomial degree≤3 or DT max_depth≤5) with engineered interaction terms per FR-005
- [ ] T027 [US3] Implement `code/analysis.py` to perform sensitivity analysis: sweep threshold over a moderate range in fixed increments and report variance in critical interaction vector per FR-006
- [ ] T028 [US3] Implement cross-model comparison logic to calculate cosine similarity of critical vectors across a set of small ASR models: whisper-tiny, whisper-small, distil-whisper-base, stt-small-en, wavvec2-base-960h (Depends on T026)
- [ ] T029 [US3] Implement validation against held-out human-annotated subset: Correlate SSS-based collapse with Human-Validated Collapse Margin (HVCM) from `data/validation/human_annotations.csv` per FR-007, FR-011
- [ ] T030 [US3] Generate final report artifacts in `data/derived/regression_results.json` and `data/derived/sensitivity_analysis.csv`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` including `research.md` citations for LibriSpeech/CORAA-MUPE-ASR
- [ ] T032 Generate `data/derived/resource_monitoring_report.json` and verify peak RSS < 7GB as a gate before proceeding (SC-004)
- [ ] T033 Performance optimization: Parallelize ASR inference and distortion application where safe
- [ ] T034 [P] Additional unit tests in `tests/unit/` for edge cases and statistical corrections
- [ ] T035 Run `quickstart.md` validation to ensure end-to-end reproducibility on GitHub Actions

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
- **User Story 2 (P2)**: Depends on US1 (requires stress curve data)
- **User Story 3 (P3)**: Depends on US2 (requires collapse points)

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
- **Human Validation**: FR-011 requires generating 500 human annotations (T030a) before US2/US3 validation.
