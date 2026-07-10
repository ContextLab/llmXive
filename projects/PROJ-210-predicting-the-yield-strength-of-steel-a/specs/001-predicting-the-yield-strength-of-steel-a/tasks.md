# Tasks: Predicting the Yield Strength of Steel Alloys from Composition and Heat Treatment Parameters

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

- [ ] T001 Create project structure per implementation plan: Execute `mkdir -p src/data src/models src/utils tests/contract tests/integration tests/unit data/raw data/processed data/results docs`. Create `src/main.py`, `requirements.txt`, `.gitignore`, and `README.md`.
- [ ] T002 Initialize Python 3.11 project with dependencies: Create `requirements.txt` pinning versions of `scikit-learn`, `xgboost`, `shap`, `pygam`, `pandas`, `numpy`, `requests`, `beautifulsoup4`, `lxml`.
- [ ] T003 [P] Configure linting and formatting: Create `.flake8` config file and `pyproject.toml` with black configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `src/utils/config.py` for paths, random seeds, and threshold constants (0.01, 0.05, 0.10)
- [ ] T005 [P] Implement `src/utils/validators.py` for schema validation of raw and processed data
- [ ] T006 [P] Create `src/data/loader.py` utilities for CSV/Parquet loading and memory monitoring
- [ ] T007 Setup `data/raw/`, `data/processed/`, and `data/results/` directory structure with `.gitkeep` files in each (verify existence of `.gitkeep` files to mark complete).
- [ ] T008 Implement `src/main.py` orchestration script with CLI entry points for each pipeline stage
- [ ] T039 [P] **Amend `specs/001-predicting-the-yield-strength-of-steel-a/spec.md` Assumptions block**: Specifically edit the 'Assumptions' section in `specs/001-predicting-the-yield-strength-of-steel-a/spec.md` to align resource limits (≤4h runtime, ≤6GB RAM) with Constitution VI, resolving contradiction with Plan.md.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw data from NIST/Materials Project, clean, normalize, engineer features (ratios, interactions), and orthogonalize interactions against main effects.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script on a provided sample CSV and verifying the output DataFrame contains exactly the required columns (composition %, thermal params, derived interactions, orthogonalized interactions) with no null values in the target variable.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for data schema in `tests/contract/test_data_schema.py` validating against `contracts/dataset.schema.yaml`
- [ ] T010 [P] [US1] Integration test for full ingestion pipeline in `tests/integration/test_ingest_pipeline.py` validating against `contracts/dataset.schema.yaml`

### Implementation for User Story 1

- [ ] T011 [US1] Implement `src/data/ingest.py`: Fetch data from NIST/Materials Project URLs (real sources), remove rows with missing yield strength (FR-001)
- [ ] T012 [US1] Implement `src/data/ingest.py`: Normalize thermal parameters (temp, cooling rate) to [0.0, 1.0] and one-hot encode heat treatment types (FR-002)
- [ ] T013 [P] [US1] Implement `src/data/features.py`: Calculate elemental ratios (C/Mn, Cr/Ni) and pairwise interactions (specifically **cooling rate × holding time** and C × Cooling Rate) (FR-003)
- [ ] T014 [US1] Implement `src/data/features.py`: Orthogonalize interaction features against their constituent main effects using **non-linear orthogonalization (regressing interactions against a natural spline basis, degree=3, knots=5)**; implement helper function `orthogonalize_spline` within `src/data/features.py` (FR-010)
- [ ] T015 [US1] Implement fallback logic in `src/data/ingest.py` to trigger literature mining if <100 samples found; use **BeautifulSoup4 with lxml parser** to scrape open-access metallurgy journals (defined in `config.py`), extracting schema (Title: str, Composition: dict/str, Yield Strength: float, Heat Treatment: str) into `data/raw/literature_mined.csv` (FR-012, Assumptions)
- [ ] T016 [US1] Implement zero-variance detection in `src/data/features.py` to exclude collinear thermal features (Edge Case)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Interaction Detection (Priority: P2)

**Goal**: Train GAM, Linear Regression, RF, XGBoost models; perform nested permutation tests; generate SHAP and PDPs.

**Independent Test**: The training module can be tested by running it on a fixed subset of data and verifying the output includes feature importance rankings, interaction SHAP values, R² scores for all four model types, p-values from nested permutation tests, and PDPs for top interaction terms.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py` validating against `contracts/output.schema.yaml`
- [ ] T018 [P] [US2] Integration test for nested permutation test in `tests/integration/test_nested_permutation.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `src/models/train.py`: Train GAM with splines and Regularized Linear Regression; **Use 3-fold CV by default; if dataset size < 100, switch to 10-Fold Repeated CV** (Note: This deviates from FR-004 text to satisfy Plan.md Stability requirement). (FR-004)
- [ ] T020 [P] [US2] Implement `src/models/train.py`: Train Random Forest and XGBoost models; **Use 3-fold CV by default; if dataset size < 100, switch to 10-Fold Repeated CV** (CPU-only, no CUDA) (Note: This deviates from FR-004 text to satisfy Plan.md Stability requirement). (FR-004)
- [ ] T021a [US2] Implement `src/models/evaluate.py`: Compute SHAP interaction values and rank features by mean absolute SHAP (FR-005)
- [ ] T021b [US2] Implement `src/models/evaluate.py`: **Generate and save SHAP summary plot artifacts** in `.png` format with naming convention `model_<name>_shap_summary.png` to `data/results/shap_summary_plots/` (FR-005)
- [ ] T022 [US2] Implement `src/models/evaluate.py`: Perform nested permutation tests on top interaction terms (**perform feature selection on the training fold only, then test on the validation fold** to prevent leakage). **Specifically: shuffle the raw interaction term relative to the target to generate a null distribution; verify observed R² improvement exceeds the 95th percentile of this null distribution** (SC-002, FR-009)
- [ ] T023 [US2] Implement `src/models/evaluate.py`: Apply Benjamini-Hochberg FDR correction (alpha ≤ 0.05) to p-values (FR-008)
- [ ] T024 [US2] Implement `src/models/evaluate.py`: Compare R² of best model (XGBoost/RF) against GAM baseline to quantify interaction value (FR-004, US2)
- [ ] T025 [US2] Implement `src/models/evaluate.py`: Generate Partial Dependence Plots (PDPs) for top interaction terms (FR-011)
- [ ] T026 [US2] Add explicit associational framing in `src/models/evaluate.py` output (FR-007)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Perform sensitivity analysis on decision thresholds; validate robustness using Jaccard index and rank correlation.

**Independent Test**: The sensitivity module can be tested by running it with a specific threshold set to 0.05, 0.01, and 0.10, and verifying that the system reports how the feature selection stability (Jaccard index) and rank consistency vary across these values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_report.py` validating against `contracts/output.schema.yaml`
- [ ] T028 [P] [US3] Integration test for threshold sweep in `tests/integration/test_sensitivity_sweep.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `src/models/sensitivity.py`: Sweep thresholds over {0.01, 0.05, 0.10} and record feature selection counts (FR-006)
- [ ] T030 [US3] Implement `src/models/sensitivity.py`: Calculate **Jaccard index (primary validity metric per SC-003) and Spearman rank correlation** for A subset of top features will be identified to address the research question. The method involves feature selection analysis. References: [Citation]. across the sweep; also calculate **Kuncheva index as supplementary robustness metric** per Plan.md (FR-006, SC-003)
- [ ] T031 [US3] Implement `src/models/sensitivity.py`: Flag results as 'unstable' if Jaccard index < 0.8 (FR-006, SC-003)
- [ ] T032 [US3] Implement documentation generation in `src/models/sensitivity.py` citing community-standard basis for thresholds (e.g., IIW formula) with format **Author, Year, Title, DOI/URL**; append justification to `results/sensitivity_report.md` with headers: 'Threshold Sweep Results', 'Stability Metrics', 'Justification' (FR-006, SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `docs/` and `README.md`
- [ ] T034 Code cleanup and refactoring of `src/` modules
- [ ] T035 Performance optimization to ensure total runtime ≤4 hours and RAM ≤6 GB (Constitution VI)
- [ ] T036 [P] Additional unit tests in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation script
- [ ] T038 Verify all artifacts trace to `data/raw/` checksums and `code/` outputs (Constitution IV)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires processed data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires model outputs from US2

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
Task: "Contract test for data schema in tests/contract/test_data_schema.py"
Task: "Integration test for full ingestion pipeline in tests/integration/test_ingest_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/ingest.py: Fetch data..."
Task: "Implement src/data/features.py: Calculate elemental ratios..."
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
- **Resource Constraint**: All models must run on CPU only; no CUDA, 8-bit/4-bit quantization, or large LLMs.
- **Data Constraint**: Use real data sources only; no synthetic data for validation.