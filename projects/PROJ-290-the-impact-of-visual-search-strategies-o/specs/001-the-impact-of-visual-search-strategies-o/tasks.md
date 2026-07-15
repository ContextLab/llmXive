# Tasks: The Impact of Visual Search Strategies on Attentional Capture by Emotional Faces

**Input**: Design documents from `/specs/001-visual-search-emotional-faces/`
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

- [X] T001a Create project directories per implementation plan (`projects/PROJ-290-the-impact-of-visual-search-strategies-o/`): `code/`, `data/raw/`, `data/processed/`, `results/`, `results/figures/`, `results/reports/`, `tests/`, `state/`.
- [X] T001b Create project files per implementation plan: `code/__init__.py`, `requirements.txt`, `pyproject.toml`, `README.md`, and `code/config.py` (managing environment variables and default paths).
- [X] T002 Initialize Python 3.11 project with dependencies in `requirements.txt` (pandas, numpy, scikit-learn, statsmodels, datasets, joblib, scipy, matplotlib, seaborn, pyyaml, requests)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup logging infrastructure in `code/utils/logging.py` with file handlers for `logs/`
- [X] T005 [P] Implement `code/utils/hash_artifacts.py` to generate SHA-256 hashes for `data/` and `code/` artifacts (Constitution Principle V)
- [X] T007 Implement generic ROI fallback logic: grid definition for face images in `code/features/extraction.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Verification (Priority: P1) 🎯 MVP

**Goal**: Successfully download and validate eye-tracking datasets with gaze coordinates and response times.

**Independent Test**: Can be fully tested by executing the data download script and verifying dataset integrity without running any statistical analysis.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T008 [P] [US1] Unit test for retry logic with exponential backoff in `tests/unit/test_download.py`
- [ ] T009 [P] [US1] Unit test for variable validation (missing critical vars) in `tests/unit/test_validate.py`

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/data/download.py` to search HuggingFace for 'eye-tracking', 'face', 'emotion' datasets; select the first dataset where schema validation passes (FR-009) and contains at least one valid record; if no valid dataset is found, halt with a clear error message. Do NOT use a hardcoded fallback dataset ID.
- [ ] T011 [US1] Implement retry logic with exponential backoff in `code/data/download.py` (FR-002) with explicit timings: 1s, 2s, 4s.
- [ ] T012 [US1] Implement `code/data/validate.py` to check for `gaze_coordinates`, `response_times`, `emotion_labels`, `roi_annotations`; write `data/validation_report.json` with status and missing variables list; HALT if critical vars missing (FR-009).
- [ ] T013 [US1] Implement logic to apply Generic ROI Fallback (3x3 grid) if `roi_annotations` are missing
- [~] T014 [US1] Implement participant exclusion logic: exclude if >20% missing gaze data; log exclusion rate
- [~] T015 [US1] Create `data/raw/` directory structure and save downloaded dataset checksums
- [~] T037a [US1] Run `hash_artifacts.py` to update `state/` with hashes after T015 (Data Download) <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Extraction and Strategy Classification (Priority: P2)

**Goal**: Compute fixation metrics, calculate continuous predictor, and perform exploratory clustering with robustness checks.

**Independent Test**: Can be tested by processing a subset of participant records and verifying that clustering produces interpretable results or correctly triggers a fallback.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for fixation metric calculation (eye/mouth duration) in `tests/unit/test_features.py`
- [X] T017 [P] [US2] Unit test for VIF calculation in `tests/unit/test_diagnostics.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement `code/features/extraction.py` to compute fixation duration (eye/mouth), saccade amplitude, dispersion (FR-003)
- [ ] T019 [US2] Save extracted features to `data/processed/features.csv`
- [~] T020 [US2] Implement `code/features/classification.py` to calculate **continuous ratio** of eye-to-mouth fixation time (Primary Predictor); append to `data/processed/features.csv`; if mean ratio is <= 0, log a warning and proceed with descriptive statistics only (no assertion failure).
- [X] T021 [US2] Implement k-means clustering (k=2) in `code/features/classification.py` with silhouette score calculation (FR-004)
- [~] T022 [US2] Implement warning logic: if silhouette < 0.25 or cluster size < 5, log warning and proceed with descriptive stats only
- [X] T023a [US2] [Plan-2.3] [FR-010] Implement **Bootstrap Stability Check** in `code/features/classification.py`: repeat clustering on multiple bootstrap samples (e.g., 100 iterations) to assess label stability; output stability metrics. This replaces k-fold CV which is invalid for unsupervised clustering.
- [X] T024a [US2] Implement VIF calculation for predictor pairs; flag VIF ≥5 in `code/utils/diagnostics.py` (FR-005)
- [ ] T024b [US2] Implement k-means clustering for k=2 and k=3 specifically to generate labels for sensitivity analysis; output `data/processed/labels_k2.csv` and `data/processed/labels_k3.csv`.
- [~] T037b [US2] Run `hash_artifacts.py` to update `state/` with hashes after T019, T024a, T024b, T023a (Features & Labels)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Power Validation (Priority: P3)

**Goal**: Fit LMM with continuous predictor, perform permutation test, and validate statistical power.

**Independent Test**: Can be tested by running the model on a mock dataset with known effect sizes and verifying that confidence intervals and p-values are correctly computed.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for LMM convergence and fallback logic in `tests/unit/test_lmm.py`
- [X] T028 [P] [US3] Unit test for multiple comparison correction (Bonferroni/BH) in `tests/unit/test_power.py`

### Implementation for User Story 3

- [~] T029a [US3] Implement `code/analysis/lmm.py` to fit Linear Mixed-Effects Model with detection time as outcome and **continuous fixation ratio** as fixed effect (Primary Analysis per Plan); output `results/lmm_continuous.csv`; assert model.converged. **If model fails to converge (max_iter=500), immediately fall back to a simpler linear model using the SAME predictor (Continuous Ratio).**
- [~] T029b [US3] [Descriptive Only] Implement `code/analysis/lmm.py` to fit Linear Mixed-Effects Model with detection time as outcome and **processing strategy (derived cluster label from T023a)** as fixed effect; **WARNING: This is Exploratory/Descriptive Only and NOT for primary inference due to circularity risks per Plan.** Output `results/lmm_cluster.csv`; assert model.converged. <!-- FAILED: unspecified -->
- [~] T030 [US3] Implement Permutation Test in `code/analysis/lmm.py`: permute detection times **1000 times** to establish null distribution; use same data prep as T029a; output `results/permutation_test.json`.
- [X] T031 [US3] Implement multiple-comparison correction (Bonferroni or Benjamini-Hochberg) at α=0.05 in `code/analysis/power.py` (FR-007)
- [X] T032 [US3] Implement a priori power analysis based on effect size d=0.5, **target power=0.80, alpha=0.05, two-tailed test** in `code/analysis/power.py`
- [~] T033 [US3] Implement post-hoc power analysis; document if power < 0.80 (FR-008)
- [~] T034 [US3] Generate statistical results table with estimates, SE, t-values, p-values, and adjusted p-values
- [ ] T025 [US3] [FR-010] Implement Sensitivity Analysis: sweep k over {2, 3}, run **secondary LMM using cluster labels** (from T024b) to report coefficient variance for the **descriptive model**; output `results/sensitivity_report.yaml`. This validates the stability of the exploratory cluster-based approach, not the primary continuous predictor.
- [ ] T026 [US3] Save sensitivity analysis report to `results/sensitivity_report.yaml` (SC-006)
- [ ] T037c [US3] Run `hash_artifacts.py` to update `state/` with hashes after T026, T034 (Final Results)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation.

- [ ] T035 [P] Implement `code/validation/reference_validator.py` to validate citations against primary sources (Title overlap ≥0.7)
- [ ] T038 Generate final report in `results/report.md` including sections: Data, Methods, Results (Continuous & Cluster), Sensitivity, Limitations; must include tables from T029a and T029b.
- [ ] T039 Create `results/figures/` directory and generate plots: `results/figures/fixation_dist.png`, `results/figures/model_coeffs.png`, `results/figures/power_curve.png`.
- [ ] T040 Run `quickstart.md` validation to ensure end-to-end pipeline execution succeeds within 6 hours

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data availability
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 feature extraction
- **Polish**: Depends on US1, US2, US3 completion

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data download (T010) before Validation (T012)
- Feature Extraction (T018) before Classification (T021, T023a, T024b)
- LMM Fitting (T029a, T029b) before Permutation Test (T030) and Sensitivity (T025)
- Power Analysis (T032) before Final Report (T038)

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
Task: "Unit test for retry logic with exponential backoff in tests/unit/test_download.py"
Task: "Unit test for variable validation (missing critical vars) in tests/unit/test_validate.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py to search HuggingFace"
Task: "Implement code/config.py to manage environment variables"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Download & Validation)
4. **STOP and VALIDATE**: Test Data Download script and verify dataset integrity
5. Deploy/demo if ready (Data Access MVP)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Feature Extraction)
4. Add User Story 3 → Test independently → Deploy/Demo (Statistical Results)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Features)
 - Developer C: User Story 3 (Analysis)
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
- **CRITICAL**: No task should load models requiring CUDA or quantization; all must run on CPU-only runners.
- **CRITICAL**: No task should synthesize fake data; all analysis must use real downloaded datasets.
- **Primary Analysis**: T029a (Continuous Ratio) is the primary analysis per Plan.
- **Spec-Fulfillment**: T029b (Cluster Label) satisfies FR-006 but is Descriptive Only.
- **Sensitivity**: T025 uses T024b (k=2/3 labels) and T029b (LMM logic) to satisfy FR-010 (Cluster Stability).
- **Stability**: T023a implements the Plan's Bootstrap Stability Check.
- **Hashing**: T037a/b/c ensure every transformation is checksummed immediately.