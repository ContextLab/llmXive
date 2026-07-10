# Tasks: Predicting Plant Secondary Metabolite Profiles from Genomic Data

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/raw`, `data/processed`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (scikit-learn, pandas, numpy, biopython, requests, dendropy, pyyaml, statsmodels, scipy)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `data/` directory structure and `checksums.txt` for data hygiene
- [ ] T005 [P] Implement `code/utils/phylogeny.py` for tree parsing (Newick) and PVR (Phylogenetic Eigenvector Regression) calculation using `statsmodels` (Plan deviation: replaces PIC)
- [X] T006 [P] Implement `code/utils/anti_smash_parser.py` for JSON parsing (handles mock/real BGC data)
- [~] T007 Create base data models/entities (Species, BGC Feature, Metabolite Profile) in `code/data_models.py`
- [~] T008 Configure environment configuration management (`.env` for API keys, paths, and `CI_MODE` flag)
- [~] T009 Setup pytest configuration and contract test schemas (`contracts/aligned_dataset.schema.yaml`, `contracts/model_results.schema.yaml`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Cross-Species Data Alignment & Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Construct a unified, analysis-ready dataset by aligning genomic and metabolomic data, loading mock BGC data (CI) or manual antiSMASH (non-CI), and harmonizing identifiers.

**Independent Test**: The pipeline can be fully tested by running it on a small, manually curated subset of species (e.g., *Arabidopsis*, *Rice*, *Maize*) and verifying that the output CSV contains a variable number of rows, with non-null values for both BGC counts and metabolite log-abundances.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Contract test for aligned dataset schema in `tests/contract/test_aligned_dataset.py`
- [~] T011 [P] [US1] Integration test for species-level join logic in `tests/integration/test_data_alignment.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download.py` to:
 1. Fetch genome assemblies from NCBI RefSeq (Entrez API) OR load mock data from `data/raw/mock_genomes.json` if `CI_MODE` is true (FR-001)
 2. Fetch metabolite abundance tables from MetaboLights API OR load mock data from `data/raw/mock_metabolites.csv` (FR-001)
 3. **Mock-first approach**: If `CI_MODE` is true, load `data/raw/mock_anti_smash.json` (Plan deviation: antiSMASH not run on CI). If `CI_MODE` is false, log that antiSMASH execution is manual and load pre-computed BGC data if available. (FR-002 deviation)
 4. Harmonize metabolite identifiers using InChIKeys and apply log-transformation (FR-003)
 5. Perform species-level join, excluding species missing either data type, and logging warnings (FR-003, Edge Case)
 6. Validate minimum species count (≥10) and abort pipeline (exit code 1) if insufficient for real data; allow CI mock fallback if `CI_MODE` is true (Edge Case)
 7. Add validation and error handling for missing data types and zero-BGC detections (FR-002, Edge Case)
 8. Add logging for data download, parsing, and alignment operations

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Regression Modeling & Hypothesis Testing (Priority: P2)

**Goal**: Quantify the relationship between BGC diversity and metabolite abundance using Standard CV and PVR to control for phylogeny, with permutation baselines.

**Independent Test**: The modeling step can be fully tested by running the training script on the aligned dataset, verifying that the Standard CV R² is calculated, and confirming that the PVR-adjusted p-value is < 0.05.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Contract test for model results schema in `tests/contract/test_model_results.py`
- [ ] T021 [P] [US2] Integration test for Standard CV + PVR + Permutation baseline in `tests/integration/test_model_validation.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `code/modeling/train.py` to train Random Forest and Elastic Net models (FR-005)
- [ ] T023 [US2] Implement `code/utils/phylogeny.py` to perform Phylogenetic Eigenvector Regression (PVR) using Felsenstein's method (Plan deviation: replaces PIC) on the parsed tree (FR-008 deviation, SC-006)
- [ ] T024 [US2] Implement `code/modeling/validate.py` to perform label-permutation baseline (multiple iterations) and calculate p-value (FR-005)
- [ ] T025 [US2] Implement `code/modeling/train.py` to evaluate model performance against hold-out test set and report R² (SC-001, SC-002)
- [ ] T026 [US2] Integrate PVR residuals into the modeling pipeline to ensure phylogenetic independence (FR-008 deviation)
- [ ] T027 [US2] Implement `code/modeling/train.py` to implement Standard 5-fold cross-validation (primary) with PVR integration. Explicitly note that LOCO-CV is rejected per Plan due to N<20 constraints (FR-004 deviation)
- [ ] T028 [US2] Add logging for model training, cross-validation, and permutation results

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis & Threshold Justification (Priority: P3)

**Goal**: Ensure conclusions are robust to arbitrary filtering thresholds and analyze feature importance with collinearity diagnostics.

**Independent Test**: The sensitivity analysis can be fully tested by running the analysis with three different relative abundance thresholds (e.g., 10th, 25th, 50th percentiles) and verifying that the output includes a table showing the R² variation across these thresholds.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_report.py`
- [ ] T030 [P] [US3] Integration test for threshold sweep logic in `tests/integration/test_sensitivity_analysis.py`

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement `code/modeling/sensitivity.py` to sweep minimum-abundance threshold across a range of percentiles (FR-006)
- [ ] T032 [US3] Implement `code/modeling/sensitivity.py` to re-run regression model for each threshold and record R² values (FR-006)
- [ ] T033 [US3] Implement `code/data/preprocess.py` to calculate collinearity diagnostics (VIF) for predictors (FR-007)
- [ ] T034 [US3] Implement `code/modeling/sensitivity.py` to generate sensitivity report showing R² variation and confirming qualitative conclusion (FR-006)
- [ ] T035 [US3] Implement feature importance ranking and output with collinearity notes (FR-007, SC-004)
- [ ] T036 [US3] Add logging for sensitivity sweep iterations and results

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `quickstart.md` and `README.md`
- [ ] T039 Code cleanup and refactoring
- [ ] T040 Performance optimization across all stories (ensure <6h runtime on CI)
- [ ] T041 [P] Additional unit tests in `tests/unit/`
- [ ] T042 Run quickstart.md validation to ensure end-to-end pipeline execution

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for aligned dataset
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for model results

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
Task: "Contract test for aligned dataset schema in tests/contract/test_aligned_dataset.py"
Task: "Integration test for species-level join logic in tests/integration/test_data_alignment.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py to fetch genome assemblies"
Task: "Implement code/utils/anti_smash_parser.py to parse antiSMASH output"
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
- **CRITICAL**: All data fetching tasks MUST use real, reachable URLs or Python package fetchers; no synthetic data generation for final results (mock data is only for CI fallback).
- **CRITICAL**: antiSMASH is not run on CI; tasks must handle mock data loading gracefully as per Plan.md.
- **CRITICAL**: LOCO-CV (FR-004) and PIC (FR-008) are deviated from in Plan.md. Tasks implement PVR and Standard CV as per Plan. Spec amendment required to align spec.md.
- **CRITICAL**: T017 (now part of T012) enforces abort on <10 species for Research; CI Mock Fallback allowed only if `CI_MODE` is true.