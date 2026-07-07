# Tasks: Machine Learning Prediction of Fracture Toughness from Microstructure Images

**Input**: Design documents from `/specs/001-gene-regulation/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create code directories (`code/`, `code/data/`, `code/models/`, `code/train/`, `code/explain/`)
- [ ] T001b [P] Create data directories (`data/`, `data/raw/`, `data/processed/`, `data/explainability/`)
- [ ] T001c [P] Create test directories (`tests/`, `tests/unit/`, `tests/contract/`, `tests/integration/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (torch CPU, scikit-learn, opencv-python-headless, pandas, numpy, matplotlib, captum)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T009 [P] Create `research.md` artifact in `projects/PROJ-266-machine-learning-prediction-of-fracture-/` with content structure: Introduction, Methodology, Resolution Limits, Results, Discussion. (Required for T037)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes metadata schema definition and artifact creation.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T004a [P] Create data directory structure (`data/raw`, `data/processed`, `data/explainability`)
- [~] T004b [P] Implement checksum validation infrastructure in `code/data/ingest.py`
- [~] T005 [P] Implement synthetic microstructure generator in `code/data/synthetic_gen.py` to produce ≥2,000 images (Plan-driven correction to Spec's ≥500; see Plan 'Spec Assumption Correction' note) with physics-informed K_IC values. **Includes verification step to confirm count ≥2,000.**
- [~] T005b [P] Benchmark synthetic generator runtime for [deferred] images on 2-core CPU to verify ≤6h constraint (SC-004)
- [~] T006a [P] Create base data contracts in `contracts/` (dataset_schema, evaluation_schema)
- [ ] T006b [P] Create attribution schema contract `contracts/attribution_schema.schema.yaml` (required for T048)
- [ ] T007 Implement configuration management for random seeds (fixed 42 for splits, variable for training) in `code/utils/config.py`
- [ ] T008 Setup error handling and logging infrastructure in `code/utils/logger.py`
- [ ] T031 [P] Extend synthetic generator (`code/data/synthetic_gen.py`) to embed metadata schema: `magnification`, `resolution_um` (pixels/μm), and `preparation_protocol` (SEM/TEM simulation flags) into JSON sidecar files. **Schema defined here for use in Phase 3.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw images (synthetic or user), standardize to 128x128 grayscale, and split stratified by alloy family. **Validates metadata produced in Phase 2.**

**Independent Test**: Run preprocessing on a dummy dataset; verify output directory structure, file counts per split, and alloy family distribution matches input.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [ ] T011 [P] [US1] Integration test for stratified split logic in `tests/integration/test_stratified_split.py`

### Implementation for User Story 1

- [ ] T012a [P] [US1] Implement image loading and basic validation in `code/data/ingest.py` (handles missing K_IC, resolution warnings)
- [ ] T012b [US1] [P] Implement validation logic for missing K_IC **and metadata fields (magnification, resolution_um, preparation_protocol) defined in T031** in `code/data/ingest.py`. **Depends on T031.**
- [ ] T013 [US1] Implement preprocessing pipeline in `code/data/preprocess.py` (grayscale, resize 128x128, normalization, **resolution limit check using metadata 'resolution_um' from T031**)
- [ ] T014 [US1] Implement stratified split logic in `code/data/preprocess.py` (seed 42, steel/Al/Ti stratification)
- [ ] T015 [US1] Generate `split_metadata.csv` recording alloy family distribution per split
- [ ] T016 [US1] Add validation to ensure test set contains at least one sample per alloy family (fatal error if not)
- [ ] T017 [US1] Add logging for preprocessing steps and excluded samples

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight CNN Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train 3-block CNN, compare against Linear Regression/Random Forest baselines on handcrafted features, and run Permutation Test.

**Independent Test**: Run training on a subset of images for multiple seeds; verify log contains R², MAE for all models and p-value from Permutation Test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for evaluation metrics JSON in `tests/contract/test_evaluation_schema.py`
- [ ] T019 [P] [US2] Integration test for Permutation Test logic in `tests/integration/test_permutation_test.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement 3-block CNN architecture (Conv-ReLU-BN-MaxPool) in `code/models/cnn.py`
- [ ] T021 [P] [US2] Implement baseline models (Linear Regression, RandomForest) in `code/models/baselines.py`
- [ ] T022 [US2] [P] Implement texture feature extraction (GLCM, power spectra) **including bootstrap confidence intervals** in `code/data/features.py`
- [ ] T023a [P] [US2] Implement seed management utility in `code/utils/seeds.py`
- [ ] T023b [US2] Implement training loop with multiple independent seeds in `code/train/train_cnn.py`
- [ ] T024 [US2] Implement metric calculation (R², MAE, RMSE) and save to JSON in `code/train/evaluate.py`
- [ ] T025a [US2] Implement Permutation Test function in `code/train/stats.py` (authorized substitution for Wilcoxon per FR-005/SC-002)
- [ ] T025b [US2] Integrate Permutation Test call in `code/train/evaluate.py`
- [ ] T025c [US2] Format Permutation Test output JSON in `code/train/evaluate.py`
- [ ] T026 [US2] Add logging for training progress and final metrics comparison

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Attribution and Stability Reporting (Priority: P3)

**Goal**: Generate Grad-CAM heatmaps (per Spec FR-006/FR-007) and validate stability via IoU across augmented views.

**Independent Test**: Run attribution on a single test image with multiple augmentations.; verify heatmap generation and IoU calculation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T038 [P] [US3] Contract test for attribution schema in `tests/contract/test_attribution_schema.py`
- [ ] T039 [P] [US3] Integration test for IoU stability calculation in `tests/integration/test_stability.py`

### Implementation for User Story 3

- [ ] T042 [P] [US3] Implement Grad-CAM heatmap generation in `code/explain/gradcam.py` (Per Spec FR-006/FR-007 mandate. Note: This deviates from Plan's recommendation of InputXGrad; rationale documented in T042b)
- [ ] T042b [US3] Document the rationale for using Grad-CAM over InputXGrad in `research.md` (created in T009), citing FR-006 and Plan's 'Spec Contradiction Note' as the context for the decision.
- [ ] T043 [US3] Implement augmentation pipeline for stability testing in `code/explain/stability.py` (Strategy: rotation ±10°, Gaussian noise σ=0.01, brightness jitter ±10%)
- [ ] T044 [US3] Calculate IoU between heatmaps of augmented views in `code/explain/stability.py`
- [ ] T045 [US3] Generate stability report (`stability_report.json`) and save to `data/explainability/`
- [ ] T046 [US3] Implement validation script in `code/explain/validate.py` (exits 0 on success, 1 on failure, logs errors)
- [ ] T048 [US3] Validate attribution outputs against `contracts/attribution_schema.schema.yaml` (created in T006b) and check stability threshold (mean IoU > 0.5) per US-3 Acceptance Scenario 2

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Research Protocol & Reproducibility Enhancements (Priority: P1 - Reviewer Response)

**Goal**: Address Rosalind Franklin-simulated reviewer concerns regarding sample preparation metadata, resolution limits, and feature extraction confidence. **Depends on Phase 2/3/4 completion.**

**Independent Test**: Verify that generated datasets include a `metadata.json` with imaging parameters and that feature extraction reports include confidence intervals.

### Implementation for Reviewer Response

- [ ] T034a [US2] Implement bootstrap CI function in `code/utils/stats.py` (Logic already merged into T022; this task refines the utility)
- [ ] T036 [US3] Update stability report to include feature consistency metrics across different simulated preparation batches (if batch variance is simulated)
- [ ] T037 [US1] Update `research.md` (created in T009) to explicitly document the minimum resolvable feature size based on the *generated* `resolution_um` values from T005, analyzed via T013. **Depends on T009, T005, T012b, T013.**

**Checkpoint**: Research protocol is now fully specified and reproducible per reviewer standards.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T047 [P] Benchmark full pipeline runtime on 2-core CPU with [deferred] images to verify ≤6h constraint (SC-004)
- [ ] T049 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T050 Code cleanup and refactoring
- [ ] T051 Performance optimization to ensure <6h runtime on 2-core CPU
- [ ] T052 [P] Additional unit tests in `tests/unit/`
- [ ] T053 Run `quickstart.md` validation

**Note**: Phase N tasks renumbered to T049+ to avoid collision with Phase 5 tasks (T042-T048).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review Enhancements (Phase 6)**: Can run in parallel with US1/US2 implementation but must be complete before final validation. **T037 depends on T009, T005, T012b, T013.**
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Uses metadata from T031. T012b/T013 depend on T005.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires processed data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires trained model from US2
- **Phase 6 (Reviewer Response)**: Depends on US1 and US2 implementation to verify metadata and feature extraction logic. **T037 depends on T009, T005, T012b, T013.**

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
- Phase 6 tasks (except T037) can run in parallel with US1/US2 implementation

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Integration test for stratified split logic in tests/integration/test_stratified_split.py"

# Launch all models for User Story 1 together:
Task: "Implement image loading and validation in code/data/ingest.py"
Task: "Implement preprocessing pipeline in code/data/preprocess.py"
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
5. Add Phase 6 (Reviewer Response) → Verify metadata and confidence intervals
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 + Phase 6 (Metadata)
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
- **Critical Constraint**: All tasks must be executable on CPU-only CI (2 cores, 7GB RAM) within 6 hours. No GPU, no 8-bit quantization.
- **Data Integrity**: All data must be real (synthetic generator) or user-provided with strict validation. No fabrication of results.
- **Metadata Dependency**: Tasks in Phase 3 (T012b, T013) depend on metadata schema defined in Phase 2 (T031) and data generation (T005).
- **Artifact Dependency**: Task T037 depends on T009 (creation of research.md), T005 (data generation), T012b (validation), and T013 (preprocessing).