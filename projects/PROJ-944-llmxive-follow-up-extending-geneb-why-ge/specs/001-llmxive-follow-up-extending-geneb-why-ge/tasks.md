# Tasks: llmXive follow-up: extending "GENEB: Why Genomic Models Are Hard to Compare"

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001a Create project root directories: `projects/PROJ-944-llmxive-follow-up-extending-geneb-why-ge/`, `code/`, `data/`, `outputs/`, `tests/`
- [X] T001b Create `.gitignore` and `requirements.txt` stubs; initialize git repo
- [ ] T002 Initialize Python 3.11 project with dependencies: `pandas`, `numpy`, `scikit-learn`, `scipy`, `datasets`, `pyyaml`, `pytest`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004a Setup directory structure: `data/raw/`, `data/processed/`, `outputs/reports/`, `outputs/figures/`, `state/`
- [ ] T004b [P] Implement checksum generation utility: compute SHA-256 for files in `data/raw/` and `data/processed/` and prepare JSON/YAML snippet for `state/...yaml`
- [ ] T004c [P] Initialize `state/projects/PROJ-944-llmxive-follow-up-extending-geneb-why-ge.yaml` with `artifact_hashes` map structure if missing
- [X] T005 [P] Implement base logging configuration and error handling utilities (`code/utils/logging.py`)
- [ ] T006 [P] Create schema validation contracts based on `specs/001-gene-regulation/contracts/dataset.schema.yaml`
- [ ] T006a [P] Generate `specs/gene-regulation/contracts/dataset.schema.yaml` defining the **structure** for 15 sequence features. **Do NOT hardcode specific feature names here.** Instead, reference the `data-model.md` artifact (Phase 1 output) for the authoritative list of features. **Explicitly exclude `at_content`** due to perfect collinearity with GC-Content as per Plan.md (Constitution Check, Principle VII). The schema must allow for dynamic feature names as defined in `data-model.md`.
- [X] T007 Create base configuration loader for random seeds and path constants (`code/config.py`)
- [ ] T008 Setup retry mechanism with exponential backoff for network requests (GENEB/Zenodo access)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Sequence Feature Extraction and Benchmark Loading (Priority: P1) 🎯 MVP

**Goal**: Automatically download raw sequence data for GENEB benchmark tasks and compute 15 standardized low-dimensional sequence statistics (e.g., k-mer entropy, GC-content variance) for each task.

**Independent Test**: The pipeline can be fully tested by running the extraction script on a representative subset of tasks and verifying the output CSV contains the expected numeric columns with no null values and completes within a reasonable timeframe on a standard multi-core CPU.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Contract test verifying output CSV schema matches `SequenceFeatureSet` definition in `tests/contract/test_feature_schema.py` (uses `specs/001-gene-regulation/contracts/dataset.schema.yaml`)
- [~] T010 [P] [US1] Integration test for data download and feature extraction on a small subset in `tests/integration/test_download_extract.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/data/download.py`: Fetch GENEB raw sequences (FASTA/splits) using `datasets` library or direct HTTPS with retry logic. **Must fail loudly** if real data source is unreachable (no synthetic fallback).
- [~] T011b [US1] Implement `code/data/download.py` (extended): Fetch GENEB ground truth macro-MCC scores from the primary benchmark source (Zenodo/GENEB repo). **Identify the specific file** (e.g., `results.csv`, `benchmarks.json`) in the benchmark repository that contains the macro-MCC scores for all tasks, parse it, and save as `data/raw/geneb_scores.csv`. **Must fail loudly** if the specific score file is missing or the source is unreachable.
- [X] T012 [US1] Implement `code/data/extract_features.py`: Implement feature extraction logic. **Read the specific feature names and definitions from `data-model.md` (Phase 1 output)** or the schema generated by T006a (which references `data-model.md`). Compute the required sequence features (e.g., nucleotide entropy, k-mer entropy, GC-content variance) for each task. Handle edge cases (mononucleotide repeats) by flooring entropy to a small positive constant. **Validate output against the schema generated by T006a** before saving. **Ensure `at_content` is excluded**.
- [~] T013 [US1] Implement `code/data/preprocess.py`: Handle NaNs, outliers, validate output against `dataset.schema.yaml` (from T006a) before saving the final feature matrix to `data/processed/features.csv`. Ensure streaming/chunking logic if dataset is large to stay within 7GB RAM.
- [ ] T014 [US1] Add validation to ensure all computed features are floats within valid theoretical ranges (e.g., entropy >= 0.0).
- [ ] T015 [US1] Add logging for download progress and feature extraction stats (tasks processed, time taken).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Sparse Regression Model Training and Validation (Priority: P2)

**Goal**: Train sparse regression models (Lasso/Elastic Net) and a shallow Random Forest to predict macro-MCC scores using extracted sequence features, validated via 5-fold cross-validation.

**Independent Test**: The model training can be tested independently by running the training loop on a representative subset of tasks and verifying that the 5-fold cross-validation produces a Pearson correlation coefficient ($\rho$), Spearman rank correlation coefficient ($\rho_s$, and Mean Absolute Error (MAE).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Contract test verifying model output metrics format in `tests/contract/test_model_metrics.py`
- [ ] T017 [P] [US2] Integration test for 5-fold CV loop and metric calculation in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [ ] T018 [US2] Implement `code/models/train.py`: Train Lasso/Elastic Net and shallow Random Forest models using `code/data/processed/features.csv` as input. Use fixed random seeds.
- [ ] T019 [US2] Implement `code/models/validate.py`: Execute 5-fold cross-validation. Calculate and log Pearson $\rho$, Spearman $\rho_s$, and MAE for each fold and the aggregate.
- [ ] T020 [US2] Implement `code/models/predict.py`: Generate predictions for held-out tasks and ensure predicted values are clamped to the valid MCC range [-1, 1].
- [ ] T021 [US2] Add error handling for near-zero variance in target variable (skip permutation test for that fold if detected).
- [ ] T022 [US2] Add timing logs to ensure total training time stays within the designated sub-budget.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Architectural Niche Identification and Sensitivity Analysis (Priority: P3)

**Goal**: Analyze feature importance to identify sequence properties correlating with specific architectures and perform sensitivity analysis on prediction thresholds.

**Independent Test**: The analysis can be tested by generating a report that lists the top 3 predictive features for each architecture class and includes a table showing how prediction accuracy varies when the decision threshold is swept.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Contract test for sensitivity report structure in `tests/contract/test_sensitivity_report.py`
- [ ] T024 [P] [US3] Integration test for threshold sweep and permutation test in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T024a [US3] Join ground truth macro-MCC scores from `data/raw/geneb_scores.csv` (produced by T011b) with `data/processed/features.csv` and `outputs/predictions.csv` on `task_id` to create the evaluation dataset for sensitivity analysis.
- [ ] T025 [US3] Implement `code/analysis/feature_importance.py`: Rank top sequence features predicting performance for Transformer vs. Mamba architectures based on model coefficients/feature importances.
- [ ] T026 [US3] Implement `code/analysis/sensitivity.py`: Perform threshold sweep over a range of values. Calculate and report False Positive/Negative rates against the ground truth (actual MCC > 0.6). **Include a log entry documenting the rationale for this specific threshold set based on community standards.**
- [ ] T027 [US3] Implement `code/analysis/permutation.py`: Execute a permutation test with a **minimum of 1,000 iterations** on the final correlation coefficient to calculate p-value against the null hypothesis.
- [ ] T028 [US3] Generate final `SensitivityReport` and `FeatureImportanceReport` in `outputs/reports/`.
- [ ] T029 [US3] Add validation to ensure p-value calculation handles edge cases (e.g., if all permuted stats > observed, report `p < 1/N` where N is iterations, not `p=0.0`).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates: Update `quickstart.md` with pipeline execution instructions
- [ ] T031a Code cleanup: Remove unused imports from all modules
- [ ] T031b Refactor feature extraction logic to use generator expressions for memory efficiency
- [ ] T031c Add type hints to all public functions in `code/data/` and `code/models/`
- [ ] T032 Performance optimization: Ensure streaming logic handles large datasets without memory spikes
- [ ] T033 [P] Additional unit tests for edge cases (mononucleotide repeats, zero variance) in `tests/unit/`
- [ ] T034 Run `quickstart.md` validation to ensure end-to-end reproducibility on 2-core CPU

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces `data/processed/features.csv` and `data/raw/geneb_scores.csv`**.
- **User Story 2 (P2)**: Depends on US1 completion. **Consumes `data/processed/features.csv`**.
- **User Story 3 (P3)**: Depends on US2 completion. **Consumes model predictions and metrics**.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Download/Preprocessing before Feature Extraction
- Feature Extraction before Model Training
- Model Training before Analysis
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for feature schema in tests/contract/test_feature_schema.py"
Task: "Integration test for download/extract in tests/integration/test_download_extract.py"

# Launch implementation tasks for User Story 1:
Task: "Implement download.py with retry logic"
Task: "Implement extract_features.py with entropy calculation"
Task: "Implement preprocess.py with streaming support"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Download & Feature Extraction)
4. **STOP and VALIDATE**: Test US1 independently. Verify `features.csv` and `geneb_scores.csv` exist and are valid.
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model Training) - *Can start once T013 is done*
 - Developer C: User Story 3 (Analysis) - *Can start once T020 is done*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All data fetching must use real sources (GENEB/Zenodo). No synthetic fallbacks.
- **Critical Constraint**: `at_content` is explicitly excluded from the feature set due to collinearity with GC-Content.
- **Critical Constraint**: Entropy calculation must handle edge cases (floor to small positive constant).
- **Critical Constraint**: Pipeline must run within 6 hours on 2-core CPU.
- **Critical Constraint**: Checksums must be recorded in `state/...yaml` using SHA-256.
- **Critical Constraint**: P-values for permutation tests must follow standard convention (`p < 1/N` if all permuted > observed).
- **Critical Constraint**: Permutation test must use a minimum of 1,000 iterations.
- **Critical Constraint**: Feature names must be defined in `data-model.md` (Phase 1 output), not hardcoded in tasks.