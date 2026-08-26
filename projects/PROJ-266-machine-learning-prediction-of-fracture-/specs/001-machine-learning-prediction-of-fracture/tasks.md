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

- [X] T001a [P] Create code directories and init files: `code/__init__.py`, `code/data/__init__.py`, `code/models/__init__.py`, `code/train/__init__.py`, `code/explain/__init__.py`, `code/utils/__init__.py`. **Verification**: Run `ls -R code` and confirm all 6 `__init__.py` files exist.
- [ ] T001b [P] Create data directories and keep files: `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/explainability/.gitkeep`. **Verification**: Run `ls -R data` and confirm all 3 `.gitkeep` files exist.
- [X] T001c [P] Create test directories and init files: `tests/__init__.py`, `tests/unit/__init__.py`, `tests/contract/__init__.py`, `tests/integration/__init__.py`. **Verification**: Run `ls -R tests` and confirm all 4 `__init__.py` files exist.
- [X] T002 [P] Initialize Python 3.11 project with `code/requirements.txt` containing exact pinned versions: `torch==2.1.0+cpu`, `scikit-learn==1.3.2`, `opencv-python-headless==4.8.1.78`, `pandas==2.1.3`, `numpy==1.26.2`, `matplotlib==3.8.2`, `captum==0.7.0`, `pytest==7.4.3`, `black==23.12.1`, `ruff==0.1.8`. **Verification**: Run `pip install -r code/requirements.txt` successfully.
- [X] T003 [P] Configure linting and formatting: Create `pyproject.toml` with `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (select=['E', 'F', 'W'], ignore=['E501']). **Verification**: Run `ruff check.` and `black --check.` successfully (exit code 0).
- [ ] T009 [P] Create `research.md` artifact in `projects/PROJ-266-machine-learning-prediction-of-fracture-/` with content structure: Introduction, Methodology, Resolution Limits, Results, Discussion. (Required for T037)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes metadata schema definition and artifact creation.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004a [P] Create data directory structure (`data/raw`, `data/processed`, `data/explainability`)
- [X] T004b [P] Implement checksum validation infrastructure in `code/data/ingest.py`
- [ ] T005 [P] Implement synthetic microstructure generator logic in `code/data/synthetic_gen.py` to produce ≥2,000 images (Plan-driven correction to Spec's ≥500; see Plan 'Spec Assumption Correction' note) with physics-informed K_IC values. **Output**: Generates images and K_IC values.
- [ ] T005b [P] Implement benchmark script in `code/utils/benchmark_gen.py` to measure generator runtime. **Output**: Write `data/benchmarks/generator_runtime.json` with fields `total_time_seconds` (float) and `images_per_second` (float).
- [ ] T005c [P] Run generator benchmark: Execute `python code/utils/benchmark_gen.py` with seed 42. **Verification**: Confirm `data/benchmarks/generator_runtime.json` is created and populated. **Depends on T005b and T005.**
- [ ] T005d [P] Validate dataset size assumption: Write a script to verify generator output ≥2,000 images and document the deviation from spec's ≥500 in `research.md` (Section: Resolution Limits). **Verification**: `research.md` contains explicit text: "Spec assumed ≥500; Plan corrected to ≥2,000 to reduce variance." **Depends on T005 and T009.**
- [ ] T005e [P] Update spec.md: Amend the "Assumptions" section in `spec.md` to explicitly state the target sample size is ≥2,000 images, replacing the original ≥500. **Verification**: `spec.md` contains "≥2,000 images". **Depends on T005d.**
- [ ] T006a [P] Create base data contracts in `contracts/`:
 1. `dataset_schema.schema.yaml`: Define fields `image_path` (string), `k_ic` (float), `alloy_family` (string), `magnification` (float), `resolution_um` (float), `section_thickness_um` (float), `preparation_protocol` (string).
 2. `evaluation_schema.schema.yaml`: Define fields `model_type` (string), `r2` (float), `mae` (float), `rmse` (float), `p_value` (float).
 **Verification**: Schema files exist with correct structure.
- [ ] T006b [P] Create attribution schema contract `contracts/attribution_schema.schema.yaml` (required for T048) with fields `image_id` (string), `heatmap_path` (string), `mean_iou` (float), `std_iou` (float).
- [ ] T006c [P] Update spec.md: Amend "FR-001" and "User Story 1" in `spec.md` to define the input schema as a CSV with image paths/K_IC AND a JSON sidecar file containing metadata fields (magnification, resolution_um, section_thickness_um, preparation_protocol) for each image. **Verification**: `spec.md` describes the JSON sidecar schema. **Depends on T006a.**
- [ ] T007 [P] Implement configuration management in `code/utils/config.py`: Define a Python dictionary `CONFIG` with keys `split_seed` (int, default 42), `train_seed` (int, default variable), `image_size` (tuple, default (128, 128)), `batch_size` (int, default 32). **Verification**: Import `CONFIG` and verify keys exist.
- [ ] T008 [P] Setup error handling and logging infrastructure in `code/utils/logger.py`: Implement `get_logger()` returning a logger that writes to `logs/app.log` with format `%(asctime)s - %(name)s - %(levelname)s - %(message)s`. **Verification**: Run a test script calling `logger.info("test")` and confirm `logs/app.log` contains the entry.
- [ ] T031 [P] Extend synthetic generator (`code/data/synthetic_gen.py`) to embed metadata schema: `magnification`, `resolution_um` (pixels/μm), `section_thickness_um` (for TEM simulation), and `preparation_protocol` (SEM/TEM flags) into JSON sidecar files (e.g., `image_001.png.json`). **Verification**: Run generator and confirm sidecar files exist with correct schema.
- [ ] T054 [P] Implement `calculate_resolution_limit` utility in `code/utils/metrics.py` to compute minimum resolvable feature size (Rayleigh criterion) based on `resolution_um` metadata from T031. **Addresses Rosalind Franklin review regarding minimum resolvable feature size.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw images (synthetic or user), standardize to 128x128 grayscale, and split stratified by alloy family. **Validates metadata produced in Phase 2.**

**Independent Test**: Run preprocessing on a dummy dataset; verify output directory structure, file counts per split, and alloy family distribution matches input.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`: Import `dataset_schema.schema.yaml`, load a sample CSV+JSON, and assert presence of all required fields (image_path, k_ic, alloy_family, magnification, etc.). **Verification**: Test passes on valid data, fails on missing fields.
- [ ] T011 [P] [US1] Integration test for stratified split logic in `tests/integration/test_stratified_split.py`.

### Implementation for User Story 1

- [ ] T012a [P] [US1] Implement image loading and basic validation in `code/data/ingest.py` (handles missing K_IC, resolution warnings).
- [ ] T012b [US1] Implement validation logic for missing K_IC **and metadata fields (magnification, resolution_um, section_thickness_um, preparation_protocol) defined in T031** in `code/data/ingest.py`. **Depends on T031.** **Verification**: Script exits with error if metadata missing.
- [ ] T013 [US1] Implement preprocessing pipeline in `code/data/preprocess.py` (grayscale, resize 128x128, normalization, **resolution limit check using metadata 'resolution_um' from T031 and T054**). **Depends on T054.** **Verification**: Output images are 128x128 grayscale.
- [ ] T014 [US1] Implement stratified split logic in `code/data/preprocess.py` (seed 42, steel/Al/Ti stratification).
- [ ] T015 [US1] Generate `split_metadata.csv` recording alloy family distribution per split. **Schema**: Columns `[split, alloy_family, count]`. **Verification**: Run `pandas.read_csv('data/processed/split_metadata.csv')` and confirm columns exist.
- [ ] T016 [US1] Add validation to ensure test set contains at least one sample per alloy family. **Error**: If failed, print "ERROR: Test set missing alloy family [X]" and exit with code 1. **Verification**: Run with imbalanced data and confirm exit code 1 and error message.
- [ ] T017 [US1] Add logging for preprocessing steps in `logs/preprocess.log`. **Format**: `%(asctime)s - PREPROCESS - %(message)s`. **Verification**: Run preprocessing and confirm `logs/preprocess.log` contains entries for each step.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight CNN Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train 3-block CNN, compare against Linear Regression/Random Forest baselines on handcrafted features, and run Permutation Test.

**Independent Test**: Run training on a subset of images for multiple seeds; verify log contains R², MAE for all models and p-value from Permutation Test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for evaluation metrics JSON in `tests/contract/test_evaluation_schema.py`: Import `evaluation_schema.schema.yaml`, load a sample JSON, and assert presence of `r2`, `mae`, `rmse`, `p_value`. **Verification**: Test passes on valid data, fails on missing fields.
- [ ] T019 [P] [US2] Integration test for Permutation Test logic in `tests/integration/test_permutation_test.py`.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement 3-block CNN architecture (Conv-ReLU-BN-MaxPool) in `code/models/cnn.py`.
- [ ] T021 [P] [US2] Implement baseline models (Linear Regression, RandomForest) in `code/models/baselines.py`.
- [ ] T022 [US2] [P] Implement texture feature extraction (GLCM, power spectra) in `code/data/features.py`. **Verification**: Output JSON contains extracted metrics.
- [ ] T023a [P] [US2] Implement seed management utility in `code/utils/seeds.py`.
- [ ] T023b [US2] Implement training loop with multiple independent seeds in `code/train/train_cnn.py`.
- [ ] T024 [US2] Implement metric calculation (R², MAE, RMSE) and save to JSON in `code/train/evaluate.py`.
- [ ] T025a [US2] Implement Permutation Test function in `code/train/stats.py`: Function `permutation_test(cnn_mae, baseline_mae, n_perm=10000)` returning `statistic` and `p_value`. **Note**: Substitutes Wilcoxon (FR-005) due to N=5; documented as authorized deviation in `research.md`. **Verification**: Function returns `statistic` and `p_value`.
- [ ] T025b [US2] Integrate Permutation Test call in `code/train/evaluate.py`.
- [ ] T025c [US2] Format Permutation Test output JSON in `code/train/evaluate.py`.
- [ ] T025d [US2] Document statistical justification: Update `research.md` (Section: Methodology) to explicitly state why Permutation Test replaces Wilcoxon (N=5 insufficient for Wilcoxon assumptions). **Verification**: `research.md` contains text: "Permutation Test used instead of Wilcoxon due to small sample size (N=5)."
- [ ] T025e [P] Update spec.md: Amend "FR-005" in `spec.md` to replace "Wilcoxon signed-rank test" with "Permutation Test (n_perm=10000) " and update "SC-002" accordingly. **Verification**: `spec.md` reflects Permutation Test. **Depends on T025d.**
- [ ] T026 [US2] Add logging for training progress in `logs/training.log`. **Format**: `%(asctime)s - TRAIN - Epoch {epoch} - Loss {loss}`. **Verification**: Run training and confirm `logs/training.log` contains epoch metrics.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Attribution and Stability Reporting (Priority: P3)

**Goal**: Generate InputXGrad heatmaps (Plan's scientific choice) and validate stability via IoU across augmented views.

**Independent Test**: Run attribution on a single test image with multiple augmentations.; verify heatmap generation and IoU calculation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T038 [P] [US3] Contract test for attribution schema in `tests/contract/test_attribution_schema.py`: Import `attribution_schema.schema.yaml`, load a sample JSON, and assert presence of `image_id`, `heatmap_path`, `mean_iou`, `std_iou`. **Verification**: Test passes on valid data, fails on missing fields.
- [ ] T039 [P] [US3] Integration test for IoU stability calculation in `tests/integration/test_stability.py`.

### Implementation for User Story 3

- [ ] T042 [P] [US3] Implement InputXGrad heatmap generation in `code/explain/inputxgrad.py` (Per Plan's scientific decision; overrides Spec FR-006/FR-007). **Verification**: Generates heatmap overlay for a test image.
- [ ] T042b [US3] Document rationale: Update `research.md` (Section: Methodology) to explain why InputXGrad (Integrated Gradients) is used instead of Grad-CAM (FR-006/007), citing Plan's 'Spec Contradiction Note' and regression task limitations. **Verification**: `research.md` contains text: "InputXGrad used as Grad-CAM is undefined for regression."
- [ ] T042c [P] Update spec.md: Amend "FR-006", "FR-007", and "SC-003" in `spec.md` to replace "Grad-CAM" with "InputXGrad (Integrated Gradients)". **Verification**: `spec.md` reflects InputXGrad. **Depends on T042b.**
- [ ] T043 [US3] Implement augmentation pipeline for stability testing in `code/explain/stability.py` (Strategy: rotation ±10°, Gaussian noise σ=0.01, brightness jitter ±10%). **Verification**: Generates multiple augmented views per image.
- [ ] T044 [US3] Calculate IoU between heatmaps of augmented views in `code/explain/stability.py`. **Verification**: Outputs mean IoU score.
- [ ] T045 [US3] Generate stability report (`stability_report.json`) and save to `data/explainability/`. **Schema**: `{ "mean_iou": float, "images_analyzed": int }`.
- [ ] T046 [US3] Implement validation script in `code/explain/validate.py`: Script loads `stability_report.json`, validates against `attribution_schema.schema.yaml`, and checks `mean_iou > 0.5 `. Exits 0 on success, 1 on failure. **Verification**: Script exits correctly based on IoU threshold.
- [ ] T048 [US3] Validate attribution outputs against `contracts/attribution_schema.schema.yaml` (created in T006b) and check stability threshold (mean IoU > 0.5) per US-3 Acceptance Scenario 2.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Research Protocol & Reproducibility Enhancements (Priority: P1 - Reviewer Response)

**Goal**: Address Rosalind Franklin-simulated reviewer concerns regarding sample preparation metadata, resolution limits, and feature extraction confidence. **Depends on Phase 2/3/4 completion.**

**Independent Test**: Verify that generated datasets include a `metadata.json` with imaging parameters and that feature extraction reports include confidence intervals.

**⚠️ NOTE**: Task T037 is strictly serial and must wait for US1 completion (T012b, T013). It cannot run in parallel with US1.

### Implementation for Reviewer Response

- [ ] T034a [US2] Implement bootstrap CI utility in `code/utils/stats.py`: Function `bootstrap_ci(data, n_boot=1000, alpha=0.05)` returning `(lower, upper)`. **Verification**: Run unit test confirming CI calculation.
- [ ] T056 [US2] Implement calculation: Update `code/data/features.py` to compute `bootstrap_ci` for each extracted metric (GLCM, power spectrum) and add to report. **Depends on T034a.**
- [ ] T056a [P] Update spec.md: Amend "SC-001" and "SC-002" in `spec.md` to include "% bootstrap confidence intervals for feature metrics" and "minimum resolvable feature size analysis" as success criteria. **Verification**: `spec.md` includes new success criteria. **Depends on T056.**
- [ ] T036a [US3] Define JSON schema change: Update `contracts/stability_schema.yaml` to include `feature_consistency_metrics` field (object with `mean_iou`, `std_iou`).
- [ ] T036b [US3] Implement calculation: Update `code/explain/stability.py` to compute `std_iou` across augmented views and add to report.
- [ ] T036c [US3] Update report generation: Modify `code/explain/stability.py` to output the new schema fields. **Verification**: `stability_report.json` contains `feature_consistency_metrics`.
- [ ] T037 [US1] Update `research.md` (created in T009) to explicitly document the minimum resolvable feature size based on the *generated* `resolution_um` values from T005, analyzed via T013 and T054. **Depends on T009, T005, T012b, T013, T054.** **Note**: Cannot run in parallel with US1/US2 if dependencies are incomplete.
- [ ] T055 [P] [US1] Implement `sample_preparation_protocol.md` documentation generator in `code/data/protocol_gen.py` that outputs a human-readable protocol based on the `preparation_protocol` and `section_thickness_um` metadata from T031. **Addresses Rosalind Franklin review regarding sample preparation method specification.**

**Checkpoint**: Research protocol is now fully specified and reproducible per reviewer standards.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T047a [P] Implement benchmark script in `code/utils/benchmark_pipeline.py` to measure full pipeline runtime. **Output**: Write `data/benchmarks/pipeline_runtime.json` with `total_time_seconds`.
- [ ] T047b [P] Run pipeline benchmark: Execute `python code/utils/benchmark_pipeline.py` with full dataset. **Verification**: Confirm `data/benchmarks/pipeline_runtime.json` exists.
- [ ] T047c [P] Verify constraint: Check `data/benchmarks/pipeline_runtime.json` and confirm `total_time_seconds` ≤ 21600 (6h). **Verification**: Exit 0 if ≤ 6h, exit 1 if > 6h.
- [ ] T049 [P] Documentation updates in `docs/` and `quickstart.md`: Add "Getting Started" section with steps: 1. Install deps, 2. Generate data, 3. Train model. **Verification**: `quickstart.md` contains these 3 steps.
- [ ] T050 [P] Code cleanup and refactoring: Remove unused imports (run `ruff check. --select=F401`), standardize variable naming (snake_case, no abbreviations like `img` -> `image`). **Verification**: `ruff check.` returns 0 errors.
- [ ] T051 [P] Performance optimization: Vectorize GLCM extraction using `skimage.feature.greycomatrix` batch processing; reduce CNN epochs to minimum required for convergence (target: maximum epochs sufficient for convergence). **Verification**: Benchmark (T047c) passes ≤ 6h.
- [ ] T052 [P] Unit tests: Write unit tests for `code/utils/stats.py` in `tests/unit/test_stats.py`. **Test Cases**: `test_bootstrap_ci_returns_tuple`, `test_bootstrap_ci_confidence_level`. **Verification**: Run `pytest tests/unit/test_stats.py` and achieve >80% coverage.
- [ ] T053 [P] Run quickstart.md validation: Execute `./validate_quickstart.sh` (script to parse `quickstart.md` and verify steps). **Verification**: Script exits 0.

**Note**: Phase N tasks renumbered to T049+ to avoid collision with Phase 5 tasks (T042-T048).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review Enhancements (Phase 6)**: Can run in parallel with US2/US3 but T037 is strictly serial after US1 completion. **T037 depends on T009, T005, T012b, T013, T054.**
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Uses metadata from T031. T012b/T013 depend on T005/T054.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires processed data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires trained model from US2
- **Phase 6 (Reviewer Response)**: Depends on US1 and US2 implementation to verify metadata and feature extraction logic. **T037 depends on T009, T005, T012b, T013, T054.**

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
- Phase 6 tasks (except T037) can run in parallel with US2/US3 implementation

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
- **Critical Constraint**: All tasks must be executable on CPU-only CI (cores, 7GB RAM) within 6 hours. No GPU, no 8-bit quantization.
- **Data Integrity**: All data must be real (synthetic generator) or user-provided with strict validation. No fabrication of results.
- **Metadata Dependency**: Tasks in Phase 3 (T012b, T013) depend on metadata schema defined in Phase 2 (T031) and data generation (T005).
- **Artifact Dependency**: Task T037 depends on T009 (creation of research.md), T005 (data generation), T012b (validation), T013 (preprocessing), and T054 (resolution limit calculation).
- **Reviewer Response**: Tasks T054, T055, T056, T056a, and T037 directly address the "Rosalind Franklin-simulated" review regarding resolution limits, sample preparation protocols, and statistical confidence intervals.
- **Spec Alignment**: Tasks T005e, T006c, T025e, T042c, and T056a ensure that all plan-driven deviations (sample size, attribution method, statistical test, input schema) are formally reflected in `spec.md` to maintain the Single Source of Truth.