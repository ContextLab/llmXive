# Tasks: The Impact of Visual Attention on False Memory Formation

**Input**: Design documents from `/specs/feature-visual-attention-false-memory/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/raw`, `data/processed`)
- [X] T002 Initialize a Python project with `requirements.txt` (torch-cpu, scikit-learn, pandas, numpy, statsmodels, datasets, opencv-python-headless, pillow)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites & Critical Validity Checks)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin, including critical validity checks that can invalidate the study.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/utils/logging.py` for exclusion logging per FR-011 (log exclusion reasons for ID mismatches)
- [X] T006 Create base data models (Image, Object, ParticipantRecall) in `src/data/models.py`
- [X] T007 Setup configuration management in `src/config.py` (paths, thresholds, model selection)
- [ ] T008a [P] Research task: Identify and verify URL for Visual Genome (subset). Document in `data/verified_sources.md`. BLOCKS T009 if invalid.
- [ ] T008b [P] Research task: Identify and verify URL for SALICON. Document in `data/verified_sources.md`. BLOCKS T021 if invalid.
- [ ] T008c Update `plan.md` and `spec.md` Constitution Check sections to change status from 'FAIL/Blocked' to 'PASS' once T008a/b are complete and verified.
- [ ] T009 [P] Implement `src/data/download.py` using verified URLs from T008a/b (blocking if URLs invalid)
- [ ] T010 Implement `src/data/linking.py` to align Visual Genome image IDs with recall transcripts (FR-011) with exclusion logic
- [ ] T018 [P] [US1] Implement power analysis script in `src/analysis/metrics.py` to calculate required sample size for r=0.30 (FR-010). **Parameters: alpha=0.01, power=0.80**. Output to `data/processed/power_analysis.json` including calculated sample size, power, and a flag documenting any shortfall against the image limit (SC-005).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Attention-False-Memory Relationship (Priority: P1) 🎯 MVP

**Goal**: Compute object-level saliency scores and corresponding false-memory rates to test the core hypothesis.

**Independent Test**: Run the end-to-end pipeline on a single image with its associated recall data and verify that a Pearson correlation coefficient and a mixed-effects regression output are produced.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T012 [P] [US1] Unit test for data linking logic in `tests/unit/test_linking.py` (verify exclusion on mismatch)
- [X] T013 [P] [US1] Integration test for end-to-end pipeline on single image in `tests/integration/test_us1_pipeline.py`

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `src/analysis/saliency.py` with CPU-compatible model loading (no CUDA, no 8-bit) and 224x224 downsampling
- [ ] T015 [US1] Implement false-memory pre-filtering logic in `src/data/preprocessing.py` (FR-005: transcript presence, VG absence). **Input**: Output of T010 (linked data). **Output**: `data/processed/candidate_false_memories.json`.
- [ ] T015a [US1] Implement **Human Consensus Workflow** in `src/utils/consensus.py`. **Input**: `data/processed/candidate_false_memories.json` (from T015). **Logic**: CLI interface to collect ratings from Multiple independent raters (simulated via JSON input for automation). **Output**: `data/processed/human_verification_results.json` with consensus flags.
- [ ] T005 [US1] Implement validation logic in `src/utils/validation.py` to calculate 'inconclusive' flag (SC-006) if failure rate > 10%. **Input**: `data/processed/human_verification_results.json` (from T015a). **Output**: `data/processed/validation_status.json`.
- [ ] T016 [US1] Implement `src/analysis/metrics.py` for Pearson correlation (r, p, CI) and mixed-effects logistic regression (FR-006, FR-007). **Input**: `data/processed/human_verification_results.json` (from T015a) and `data/processed/saliency_scores.json` (from T014). Output to `data/processed/correlation_results.json`.
- [ ] T017 [US1] Add Benjamini-Hochberg FDR correction logic in `src/analysis/metrics.py` (FR-008)
- [ ] T019 [US1] Implement `src/main.py` orchestration to run saliency -> flagging -> correlation on the sampled dataset.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Saliency Model (Priority: P2)

**Goal**: Confirm that the computational saliency model approximates human eye-fixation patterns on natural scenes.

**Independent Test**: Execute the model on the SALICON benchmark and check that the reported AUC meets the predefined threshold.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T020 [P] [US2] Unit test for AUC calculation logic in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `src/analysis/validate.py` to load SALICON test set and compute fixation map predictions
- [ ] T022 [US2] Implement AUC calculation and threshold check (AUC >= 0.70) in `src/analysis/validate.py` (FR-003)
- [~] T023 [US2] Log validation results to `data/processed/saliency_validation.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Assess Robustness of Findings (Priority: P3)

**Goal**: Examine how analysis choices (thresholds, alternative models) affect the observed relationship.

**Independent Test**: Run the pipeline with three different percentile thresholds and with an alternative Vision-Transformer CAM saliency map, then compare correlation signs and magnitudes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for sensitivity analysis logic in `tests/unit/test_robustness.py`

### Implementation for User Story 3

- [ ] T025 [P] [US3] Implement alternative saliency model wrapper (ViT-B/CAM) in `src/analysis/saliency.py` (CPU only, fallback if unavailable)
- [ ] T026 [US3] Implement `src/analysis/robustness.py` to iterate over a range of thresholds and re-run correlation (FR-009). **Input**: Output of T025 and correlation logic from T016.
- [ ] T027 [US3] Implement comparison logic to verify correlation sign stability and magnitude change <= 0.05 (SC-003). **Baseline**: Compare against result from `data/processed/correlation_results.json` (T016).
- [ ] T028 [US3] Generate robustness report in `data/processed/robustness_report.md` (Must include columns: threshold, correlation_r, p_value, sign_stable)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validity & Noise Checks (Blocking for Final Report)

**Purpose**: Final checks that must occur after analysis but before reporting.

- [ ] T011 [US1] Implement Noise Analysis: Correlate saliency with "VG annotation density" in `src/analysis/metrics.py`. **Input**: Output of T014 and VG metadata. **Logic**: Calculate correlation; if > configurable threshold, trigger invalidation.
- [ ] T011a [US1] Implement study invalidation logic in `src/utils/invalidation.py`. **Input**: Output of T011. **Logic**: If threshold exceeded, write `study_invalidated: true` to `data/processed/study_status.json` AND raise specific error `STUDY_INVALIDATED: Noise correlation threshold exceeded` with exit code 1.

**Checkpoint**: Validity checks complete. Study is either valid or invalidated.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `docs/` and `README.md`
- [ ] T030 Code cleanup and refactoring
- [ ] T031 [P] Run `quickstart.md` validation and ensure all paths resolve
- [ ] T032 [P] Implement `src/utils/ethics_check.py` script to verify presence of ethics artifacts.

---

## CI/CD & Ethics Gates

- [ ] T033 [CI/CD] Enforce Constitution VI: Create `.github/workflows/ethics_gate.yml`. **Logic**: Check if `data/ethics/source_dataset_ethics.md` exists, is not empty, AND contains a valid IRB approval number or statement (content validation). Halt pipeline if check fails.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Validity (Phase 6)**: Depends on User Story 1 completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - T015 depends on T010
 - T015a depends on T015
 - T005 depends on T015a
 - T016 depends on T014 and T015a
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Unit test for data linking logic in tests/unit/test_linking.py"
Task: "Integration test for end-to-end pipeline on single image in tests/integration/test_us1_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement src/analysis/saliency.py with CPU-compatible model loading"
Task: "Implement src/data/preprocessing.py for false-memory pre-filtering"
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
- **Critical Constraint**: All tasks must run on CPU-only (limited core count, constrained RAM). No GPU, no 8-bit/4-bit quantization, no large model training.
- **Data Constraint**: Visual Genome and SALICON URLs must be verified; if missing, tasks T008a/T008b must fail gracefully with clear error.
- **Ethics Constraint**: T033 will halt the pipeline if ethics artifacts are missing or invalid (content check).
- **Noise Constraint**: T011/T011a will invalidate the study if noise correlation exceeds configurable threshold.