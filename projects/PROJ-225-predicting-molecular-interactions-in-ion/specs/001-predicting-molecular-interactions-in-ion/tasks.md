# Tasks: Predicting Molecular Interactions in Ionic Liquids via Machine Learning

**Input**: Design documents from `/specs/001-predicting-molecular-interactions/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `models/`, `contracts/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (xgboost, optuna, rdkit, pandas, scikit-learn, pyarrow, requests, pyyaml, psi4, statsmodels)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `contracts/ion_pair.schema.yaml` and `contracts/validation_report.schema.yaml`
- [ ] T005 [P] Implement `code/config.py` for paths, seeds, and hyperparameter bounds
- [ ] T006 [P] Setup `code/utils.py` with RDKit descriptor helpers, logging, and Psi4 wrapper stub
- [ ] T007 Create base data directory structure (`data/raw/`, `data/processed/`, `data/validation/`)
- [ ] T008 Configure error handling and logging infrastructure in `code/utils.py`
- [ ] T009 Setup environment configuration management (`.env` or `config.py` overrides)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Ingest SPICE, IL-SAPT (or synthetic fallback), and ILThermo (for validation subset), engineer descriptors (including partial charges and polarizability), and produce a unified, schema-validated training dataset.

**Independent Test**: Run ingestion on a small subset of IonPairs. Verify `data/processed/unified_dataset.parquet` contains expected columns (cation_id, anion_id, electrostatic_energy, dispersion_energy, hbond_energy, tpsa, molecular_surface_area, hbond_count, graph_embedding, partial_charge, polarizability) with no null values in critical columns.

> **TDD Note**: The task list order reflects TDD workflow: Tests (T010, T011) are written FIRST, before implementation (T012-T019). This ensures tests fail initially and pass after implementation.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/data_ingestion.py` to download SPICE dataset via verified URL/package and save to `data/raw/spice.parquet`
- [ ] T013 [US1] Implement `code/data_ingestion.py` to download and parse ILThermo dataset (mandatory for validation subset per FR-007) and extract experimental enthalpy of mixing data; save to `data/raw/ilthermo_validation.parquet`
- [ ] T014 [US1] Implement `code/data_ingestion.py` to attempt IL-SAPT download; if missing, trigger "Verified Synthetic Generation" using `psi4` and `data/raw/il_structures.json`; save to `data/raw/sapt.parquet`
- [ ] T015 [P] [US1] Implement partial charge calculation in `code/data_ingestion.py` using Gasteiger method; if Gasteiger fails, attempt MMFF94; save calculated charges to the dataframe; flag rows where calculation fails.
- [ ] T016 [US1] Implement feature engineering in `code/data_ingestion.py`: parse SMILES, compute TPSA, Molecular Surface Area, H-bond counts, **polarizability**, and Morgan fingerprints (graph embeddings). **Include partial charges as input features** in the unified dataframe. Filter out rows with unreliable partial charges (magnitude > 5.0 or NaN) from the *training* set only (write to `data/processed/unified_dataset.parquet` with a `charge_reliability` column set to 'unreliable' for those rows, but retain the charge value as a feature).
- [ ] T017 [US1] Implement unified dataframe creation joining SPICE, IL-SAPT/Synthetic data by cation/anion IDs; write to `data/processed/unified_dataset.parquet`
- [ ] T018 [US1] Add validation step to validate `data/processed/unified_dataset.parquet` against `contracts/ion_pair.schema.yaml`
- [ ] T019 [US1] Add logging for ingestion steps and synthetic generation fallback

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Contract test for unified dataset schema in `tests/contract/test_ion_pair_schema.py`
- [ ] T011 [P] [US1] Integration test for data pipeline on 50 samples in `tests/integration/test_ingestion_small.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Hyperparameter Optimization (Priority: P2)

**Goal**: Train three XGBoost regressors (Electrostatic, Dispersion, H-bond) with Optuna tuning, respecting strict CPU time limits.

**Independent Test**: Run training on a toy dataset with a timeout mechanism. Verify three `.pkl` model artifacts are saved and logs show best hyperparameters and trial timeouts.

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement stratified split logic (70/15/15) by `StructuralFamily` in `code/model_training.py`; output train/val/test splits
- [ ] T022 [US2] Implement XGBoost training loop for **Electrostatic** energy component in `code/model_training.py`
- [ ] T023 [US2] Implement XGBoost training loop for **Dispersion** energy component in `code/model_training.py`
- [ ] T024 [US2] Implement XGBoost training loop for **Hydrogen-bonding** energy component in `code/model_training.py`
- [ ] T025 [US2] Implement Optuna integration in `code/model_training.py` with 5-minute per-trial timeout and fixed max trial count (60)
- [ ] T026 [US2] Implement saving of model artifacts (`models/electrostatic.pkl`, `models/dispersion.pkl`, `models/hbond.pkl`) and hyperparameter logs
- [ ] T027 [US2] Implement Total Energy Consistency Check: verify sum of predictions approximates total SAPT energy within tolerance; write result to `models/consistency_log.json` with pass/fail status and tolerance value
- [ ] T028 [US2] Add logging for MAE on validation set and trial convergence status

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Systematic Variation Analysis and Validation (Priority: P3)

**Goal**: Perform ANOVA on raw SAPT data by family, apply corrections, validate against Independent DFT dataset (per plan.md), and report results.

**Independent Test**: Run analysis on test set predictions and the Independent DFT set. Verify `contracts/validation_report.json` contains ANOVA p-values, Tukey HSD results, and DFT validation MAE.

> **Dependencies Note**: Tasks T029-T034 (ANOVA on raw data) are **independent** of US2 (models) and can run in parallel. Tasks T035-T040 (Model Validation) **depend** on US2 (models) and must wait for US2 completion.

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement ANOVA logic in `code/analysis.py` on *raw SAPT energy components* grouped by `StructuralFamily`
- [ ] T030 [US3] Perform One-way ANOVA for **Electrostatic** energy component (uncorrected p-value) and write to `analysis/anova_electrostatic.json`
- [ ] T031 [US3] Perform One-way ANOVA for **Dispersion** energy component (uncorrected p-value) and write to `analysis/anova_dispersion.json`
- [ ] T032 [US3] Perform One-way ANOVA for **Hydrogen-bond** energy component (uncorrected p-value) and write to `analysis/anova_hbond.json`
- [ ] T033 [US3] Implement global Bonferroni correction and Tukey HSD post-hoc tests across all three interaction terms; write corrected results to `analysis/anova_corrected.json` with explicit p-value threshold logic (targeting corrected p < 0.01/N_tests)
- [ ] T034 [US3] Implement effect size calculation (Cohen's d) for significant families
- [ ] T035 [US3] Implement Independent DFT Validation: compare model predictions against `data/validation/dft_validation_set.parquet` (per plan.md); calculate MAE and write to `analysis/dft_validation.json`
- [ ] T036 [US3] Implement Tautology Check: verify performance isn't driven solely by trivial descriptor correlations; write report to `analysis/tautology_report.json` with correlation matrix threshold and pass/fail status
- [ ] T037 [US3] Generate `contracts/validation_report.json` with ANOVA results, Tukey HSD, and DFT validation metrics
- [ ] T038 [US3] Add logging for p-values, effect sizes, and validation MAE

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T039 [P] [US3] Contract test for validation report schema in `tests/contract/test_validation_report_schema.py`
- [ ] T040 [P] [US3] Integration test for ANOVA and DFT validation in `tests/integration/test_analysis_validation.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `specs/001-predicting-molecular-interactions/` (update research.md with findings)
- [ ] T042 Code cleanup and refactoring
- [ ] T043 Performance optimization across all scripts (ensure < 6h runtime)
- [ ] T044 [P] Additional unit tests for RDKit descriptors in `tests/unit/test_descriptors.py`
- [ ] T045 Run `quickstart.md` validation (if generated)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (unified dataset)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (trained models) and US1 output (raw data for ANOVA)
  - **Note**: T029-T034 (ANOVA on raw data) are **independent** of US2 (models) and can run in parallel with US2.
  - **Note**: T035-T040 (Model Validation) **depend** on US2 (models) and must wait for US2 completion.

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
- **Specific Parallelism**: T030, T031, T032 (ANOVA per term) can run in parallel as they output intermediate uncorrected values.
- **Specific Parallelism**: T029-T034 (ANOVA on raw data) can run in parallel with T021-T028 (Model Training).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for unified dataset schema in tests/contract/test_ion_pair_schema.py"
Task: "Integration test for data pipeline on a representative sample set in tests/integration/test_ingestion_small.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_ingestion.py to download SPICE dataset"
Task: "Implement code/data_ingestion.py to download ILThermo dataset (validation subset)"
Task: "Implement code/data_ingestion.py to attempt IL-SAPT download or synthetic fallback"
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
   - Developer C: User Story 3 (ANOVA tasks T029-T034 can start immediately; Validation tasks T035+ wait for Developer B)
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
- **Critical**: T015 (Charge Generation) must precede T016 (Feature Engineering & Inclusion) to ensure charges are generated before being included in the dataset.
- **Critical**: T030-T032 (ANOVA per term) output uncorrected values; T033 performs global correction.
- **Critical**: T029-T034 (ANOVA on raw data) are independent of US2 (models).
- **Critical**: T035-T040 (Model Validation) depend on US2 (models).
- **Critical**: T036 (DFT Validation) is the mandated validation strategy per plan.md; experimental validation is superseded.