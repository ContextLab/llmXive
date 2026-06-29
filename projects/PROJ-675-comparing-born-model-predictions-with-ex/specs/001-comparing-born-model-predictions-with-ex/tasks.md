# Tasks: Comparing Born Model Predictions with Experimental Solvation Energies of Small Ions

**Input**: Design documents from `/specs/001-born-model-solvation-comparison/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `tests/` at repository root (per plan.md)
- Paths shown below assume single project - adjusted based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (code/, data/, tests/, state/)
- [ ] T002 Initialize Python 3.11 project with requirements.txt (pandas, numpy, scipy, matplotlib, scikit-learn, pyyaml)
- [ ] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data schema contracts in contracts/ (IonSolventPair, BornPrediction, ResidualAnalysis)
- [ ] T005 [P] Implement physical constants module in code/physical_constants.py (e, ε0, N_A, units)
- [ ] T006 [P] Setup environment configuration management in code/config.py
- [ ] T007 Create base data models/entities in code/data_models.py that all stories depend on
- [ ] T008 Configure error handling and logging infrastructure in code/utils/logging.py
- [ ] T009 [P] Setup state checksumming framework in state/ projects/PROJ-675-comparing-born-model-predictions-with-ex.yaml

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compile Experimental Solvation Energy Dataset (Priority: P1) 🎯 MVP

**Goal**: Compile a unified dataset containing experimental solvation free energies, solvent dielectric constants, and ionic radii from public chemistry databases with explicit uncertainty and metadata.

**Independent Test**: Can be fully tested by verifying the dataset contains ≥30 ion-solvent pairs with complete fields (experimental ΔG, ε, r, charge) and that each value includes an uncertainty estimate or documented source precision.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for IonSolventPair schema in tests/contract/test_schemas.py
- [ ] T011 [P] [US1] Unit test for data compiler precision in tests/unit/test_data_compiler.py

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement NIST/CRC data fetcher in code/data_compiler.py (URLs: https://webbook.nist.gov/chemistry/)
- [ ] T013 [US1] Implement Shannon radii extractor in code/data_compiler.py (source: Shannon 1976 database)
- [ ] T014 [US1] **Address Reviewer Concern (Pauling)**: Add radius_type field (crystal/hydrated) to dataset schema and extraction logic in code/data_compiler.py
- [ ] T015 [US1] **Address Reviewer Concern (Curie)**: Implement uncertainty column population (ΔG_uncertainty, ε_uncertainty) in data/experimental_solvation.csv
- [ ] T016 [US1] **Address Reviewer Concern (Franklin)**: Enforce 0.01 Å precision for ionic radii in code/data_compiler.py
- [ ] T017 [US1] **Address Reviewer Concern (Curie/Franklin)**: Record measurement temperature (±0.5°C) and instrument/source metadata for every entry in data/experimental_solvation.csv
- [ ] T018 [US1] Implement data validation script to ensure ≥30 complete ion-solvent pairs with uncertainty bounds in code/validate_data.py
- [ ] T019 [US1] Generate data dictionary documenting source citations for every value in data/metadata.json

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Implement and Validate Born Model Calculator (Priority: P2)

**Goal**: Implement the Born equation in Python and validate it against known reference cases before applying it to the full dataset, including radius-type selection.

**Independent Test**: Can be fully tested by computing Born predictions for a small reference set and verifying outputs match published analytical values within 1% tolerance (for formula implementation).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for Born equation constants in tests/unit/test_born_calculator.py
- [ ] T021 [P] [US2] Contract test for BornPrediction schema in tests/contract/test_schemas.py

### Implementation for User Story 2

- [ ] T022 [US2] Implement Born equation ΔG = -(z²e²)/(8πε₀r)(1 - 1/ε) in code/born_calculator.py
- [ ] T023 [US2] **Address Reviewer Concern (Pauling)**: Implement radius_type selector (crystal vs hydrated) in code/born_calculator.py to allow switching r input
- [ ] T024 [US2] **Address Reviewer Concern (Pauling)**: Add optional coordination_number_correction parameter in code/born_calculator.py (documented limitation)
- [ ] T025 [US2] Implement unit conversion utilities (Å to m, kcal/mol to J) with documented factors in code/born_calculator.py
- [ ] T026 [US2] Validate calculator against ≥5 reference ion-water pairs from independent data with ≤1% relative error tolerance in code/validate_born.py
- [ ] T027 [US2] Compute Born predictions for all dataset pairs and save to data/born_predictions.csv
- [ ] T028 [US2] Ensure computation completes in <10 minutes on 2 CPU cores without GPU dependencies

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Analysis and Breakdown Detection (Priority: P3)

**Goal**: Perform statistical regression of residuals against independent variables, identify systematic deviation patterns, and determine breakdown thresholds.

**Independent Test**: Can be fully tested by running the regression pipeline and verifying that RMSE, correlation coefficient, p-values, and diagnostic plots are computed with multiple-comparison correction applied.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Contract test for ResidualAnalysis schema in tests/contract/test_schemas.py
- [ ] T030 [P] [US3] Unit test for regression correction logic in tests/unit/test_regression_analysis.py

### Implementation for User Story 3

- [ ] T031 [US3] Calculate residuals (experimental - theoretical) and stratify by solvent class (water, alcohols, aprotic) in code/regression_analysis.py
- [ ] T032 [US3] **Address Reviewer Concern (Curie)**: Separate error analysis for dielectric constant measurement vs solvation energy determination in code/regression_analysis.py
- [ ] T033 [US3] Apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) to all hypothesis tests with p < 0.05 threshold in code/regression_analysis.py
- [ ] T034 [US3] Perform sensitivity analysis on RMSE threshold over {4.5, 5.0, 5.5} kcal/mol in code/regression_analysis.py
- [ ] T035 [US3] Generate diagnostic plots: (a) predicted vs. experimental scatter, (b) residual vs. ionic radius, (c) residual vs. dielectric constant in code/diagnostics.py
- [ ] T036 [US3] Save regression results to data/residual_analysis.csv with p-values and confidence intervals
- [ ] T037 [US3] Flag outliers (RMSE > 20 kcal/mol) for manual review in data/residual_analysis.csv

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address reviewer limitations

- [ ] T038 [P] **Address Reviewer Concern (Pauling)**: Document continuum dielectric limitation and hydration shell discrepancy in code/README.md and output reports
- [ ] T039 [P] Code cleanup and refactoring across code/
- [ ] T040 [P] Performance optimization across all scripts
- [ ] T041 [P] Additional unit tests in tests/unit/
- [ ] T042 [P] Security hardening (dependency scanning)
- [ ] T043 [P] Run quickstart.md validation
- [ ] T044 [P] Final state checksum update in state/projects/PROJ-675-comparing-born-model-predictions-with-ex.yaml

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
Task: "Contract test for IonSolventPair schema in tests/contract/test_schemas.py"
Task: "Unit test for data compiler precision in tests/unit/test_data_compiler.py"

# Launch all data tasks for User Story 1 together:
Task: "Implement NIST/CRC data fetcher in code/data_compiler.py"
Task: "Implement Shannon radii extractor in code/data_compiler.py"
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
- **Reviewer Concerns**: Tasks T014, T015, T016, T017, T023, T024, T032, T038 specifically address prior research-stage reviews regarding radius types, uncertainty, temperature, and continuum limitations.
