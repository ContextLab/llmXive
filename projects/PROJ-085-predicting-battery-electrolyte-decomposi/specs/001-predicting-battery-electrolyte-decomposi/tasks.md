# Tasks: Predicting Battery Electrolyte Decomposition Products via DFT and Machine Learning

**Input**: Design documents from `/specs/001-battery-electrolyte-decomposition/`
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

- [X] T001a [P] Create project directories: `code/`, `code/data/`, `code/models/`, `code/utils/`, `data/raw/`, `data/processed/`, `data/validation/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`
- [X] T001b [P] Create key files: `code/__init__.py`, `code/utils/__init__.py`, `data/.gitkeep`, `tests/__init__.py`

- [X] T002 Initialize Python 3.10 project with `requirements.txt` (pandas>=2.0.0, scikit-learn>=1.3.0, rdkit, pymatgen, datasets, numpy, matplotlib, seaborn)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/utils/constants.py` with:
 1. {{claim:c_1a09f818}} (Wikipedia: Dalton (unit), https://en.wikipedia.org/wiki/Dalton_(unit))
 2. Potentials list: `PHI_VALUES = [0, 2, 4]` (V)
 3. Create empty schema structure for `code/utils/reactions.yaml` with keys: `molecule_id`, `potential_v`, `reactants`, `products`, `n_electrons`, `energy_products`, `energy_reactants`. (Do not populate data yet).
- [X] T011 [P] Populate `code/utils/reactions.yaml` with hardcoded reaction data for EC, DMC, LiPF6 at potentials 0V, 2V, 4V. Include at least 3 sample rows with defined `n_electrons` and energy values to ensure T016 has data to read.
- [X] T005 [P] Implement data directory structure (`data/raw`, `data/processed`, `data/validation`) and checksum logic
- [X] T006 [P] Setup pytest configuration and contract validation schema loaders
- [X] T007 Create base `ElectrolyteMolecule` and `DecompositionEvent` dataclasses in `code/utils/models.py`
- [ ] T008 Configure logging infrastructure to capture warnings for missing geometric data and metallic behavior outliers
- [ ] T009 Setup environment configuration management for random seeds and dataset URLs

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-computed DFT structures from HuggingFace/NOMAD, filter for EC/DMC/LiPF6, and extract descriptors (HOMO, LUMO, geometry) to calculate decomposition energy.

**Independent Test**: Run extraction on a small fixed subset; verify output CSV columns, no missing features, and $E_{decomp}$ calculation matches manual formula within 0.01 eV.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for decomposition energy formula in `tests/unit/test_target_calc.py`
- [~] T011 [P] [US1] Integration test for data ingestion pipeline on sample subset in `tests/integration/test_ingestion.py` <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement `code/data/ingestion.py` to fetch and filter DFT data from HuggingFace dataset ID: `materialsproject/mp-dft-electrolytes`. **Fallback**: If fetch fails, use local mock CSV `data/raw/mock_electrolytes.csv` with schema matching the expected DFT output (FR-001, FR-008). <!-- FAILED: unspecified -->
- [~] T013 [P] [US1] Implement deduplication logic in `code/data/ingestion.py` based on molecule ID and potential
- [~] T014 [US1] Implement `code/data/descriptors.py` to extract HOMO, LUMO, band gap, bond lengths, angles, dihedrals using `pymatgen`/`RDKit` (FR-003)
- [~] T015 [US1] Implement logic in `code/data/descriptors.py` to extract specific geometric features (including bond lengths, bond angles, and dihedral angles) to meet FR-003 minimum count. Flag/exclude metallic (zero/negative gap) outliers.
- [~] T016 [US1] Implement `code/data/target_calc.py` to calculate $E_{decomp}$ using `code/utils/reactions.yaml` (populated in T011) and stoichiometry heuristic for $\phi \in \{0, 2, 4\}$ V (FR-002, FR-008). The heuristic selects the correct reaction entry from the YAML based on molecule ID and potential. <!-- FAILED: unspecified -->
- [~] T017 [US1] Add validation logic to ensure feature matrix has no missing values before output
- [~] T018 [US1] Split data into Train/Validation/Held-Out sets (e.g., a majority portion for training with smaller portions for validation and held-out evaluation) and save processed feature matrix, targets, and the held-out set to `data/processed/electrolyte_features.csv` and `data/processed/electrolyte_heldout.csv`
- [~] T019 [US1] Implement stratification logic to split data into 'Low' (using low-voltage data) and 'High' (using high-voltage data) bins. **Deviation**: Explicitly map the spec's '3-5V' range requirement to the available 4V data point due to data constraints. Save bin assignments to `data/processed/bins.csv`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Feature Importance Ranking (Priority: P2)

**Goal**: Train Random Forest Regressor on extracted data, generate permutation importance, and analyze ranking shifts across potential bins (0-2V vs 4V).

**Independent Test**: Train on a standard train-test split, verify R² score, and generate heatmap showing top features for low vs high potential bins.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T020 [P] [US2] Unit test for Random Forest training with 5-fold CV in `tests/unit/test_trainer.py`
- [~] T021 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`

### Implementation for User Story 2

- [~] T022 [P] [US2] Implement `code/models/trainer.py` to train Random Forest with 5-fold CV and hyperparameter tuning using GridSearchCV (search space: n_estimators=[low, medium, high], max_depth=[10, 20, None]). **Bin Logic**: Explicitly map all requests for the 'High-potential (3-5V)' range to the available 4V data point by filtering data where `potential == 4`. **Deviation**: Note that the spec's 3-5V range is approximated by the single 4V point due to data constraints. (FR-004)
- [~] T023 [US2] Implement `code/models/evaluator.py` to calculate permutation importance for each bin (FR-005). **Dependency**: Requires model artifact from T022.
- [~] T024 [US2] Implement logic to identify descriptors entering top 3 in high-potential (4V) but absent in low-potential (0-2V). **Deviation**: Explicitly reference spec's 3-5V range and note the mapping to 4V data point as a known limitation.
- [~] T025 [US2] Generate heatmap visualization of top features per bin using `seaborn` and save to `data/validation/feature_importance_heatmap.png`
- [~] T026 [US2] Save model artifacts, R² scores, and importance maps to `data/processed/model_run.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Experimental Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Validate predictions against held-out DFT data (internal consistency due to lack of external experimental data) and perform sensitivity analysis on decomposition energy threshold.

**Independent Test**: Calculate MAE against held-out DFT set; verify top 3 descriptor ranks change by ≤1 position when threshold sweeps {0.45, 0.50, 0.55} eV.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T027 [P] [US3] Unit test for sensitivity analysis sweep logic in `tests/unit/test_sensitivity.py`
- [~] T028 [P] [US3] Integration test for internal validation pipeline in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [~] T029 [P] [US3] Implement internal validation logic in `code/models/evaluator.py` to compare predictions against held-out DFT data (FR-006 Fallback). **Deviation**: Explicitly log that FR-006 (External Validation) is unmet due to missing experimental dataset (Plan Check: Data Gap).
- [~] T030 [US3] Implement calculation of MAE and R² for the internal validation set. **Deviation**: Label metric as 'Internal Consistency MAE' and flag that SC-003 (Experimental MAE) is unmet due to data gap. **Dependency**: Read model artifact from `data/processed/model_run.json` generated in T026.
- [~] T031 [US3] Implement `code/models/evaluator.py` sensitivity analysis: sweep 'decomposition energy stability cutoff' threshold $\{0.45, 0.50, 0.55\}$ eV (FR-007)
- [~] T032 [US3] Implement rank stability check: verify top 3 descriptors change by no more than 1 position across the sweep
- [~] T033 [US3] Generate sensitivity analysis report and save to `data/validation/sensitivity_report.md`
- [~] T034 [US3] Add warning flag to final report stating: "FR-006 and SC-003 (External Validation) could not be fulfilled due to unavailability of experimental onset potential datasets. Internal DFT validation was used as a fallback."

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T035a [P] Update `docs/quickstart.md` with setup, data fetching, and run instructions
- [~] T035b [P] Update `docs/research.md` with methodology, data sources (HuggingFace ID), and the deviation note regarding FR-006/SC-003 <!-- FAILED: unspecified -->
- [~] T036 Code cleanup and refactoring of `code/` modules
- [ ] T037 Performance optimization for data loading and model training on CPU
- [ ] T038 [P] Update `specs/001-battery-electrolyte-decomposition/spec.md` to explicitly remove FR-006 and SC-003, and update Constitution Check to reflect the fallback to internal validation. This formally amends the spec to match the implementation plan.
- [ ] T039 [P] Update `docs/research.md` to reference the spec amendment (T038) and the specific deviation notes in T024, T029, T030.
- [ ] T040 [P] Additional unit tests for edge cases (duplicate handling, metallic outliers) in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data output from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model output from US2

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
Task: "Unit test for decomposition energy formula in tests/unit/test_target_calc.py"
Task: "Integration test for data ingestion pipeline on sample subset in tests/integration/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/ingestion.py to fetch and filter DFT data"
Task: "Implement code/data/descriptors.py to extract HOMO/LUMO/geometry"
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
- **Constraint**: All tasks must run on CPU-only CI with limited computational resources; no GPU or 8-bit quantization.
- **Data**: Use only real, verified HuggingFace/NOMAD datasets; no synthetic data fabrication.
- **Deviation Note**: External experimental validation (FR-006, SC-003) is unfulfillable due to missing data. Internal DFT validation is used as a fallback. Spec amendment (T038) is required to formally remove these requirements.