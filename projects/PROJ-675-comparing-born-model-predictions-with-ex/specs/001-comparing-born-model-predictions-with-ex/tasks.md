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

- **Single project**: `code/`, `data/`, `tests/` at repository root (per plan.md structure)
- Paths shown below assume single project - adjusted based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T002 Initialize Python 3.11 project with requirements.txt (pandas, numpy, scipy, matplotlib, scikit-learn, pyyaml, jsonschema, pydantic, pytest, flake8, black, pip-audit)
- [ ] T001a Create code/ directory with __init__.py
- [ ] T001b Create data/ directory with raw/ subdirectory and __init__.py
- [ ] T001c Create tests/ directory with unit/ and contract/ subdirectories and __init__.py
- [ ] T001d Create state/ directory with projects/ subdirectory and __init__.py
- [ ] T003 [P] Configure linting (flake8) and formatting (black) tools: create.flake8 config file at repo root and pyproject.toml with [tool.black] section; verify via `flake8 --version` and `black --version`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create base data models/entities in code/data_models.py using Pydantic for IonSolventPair, BornPrediction, ResidualAnalysis entities with all fields from spec (ion_identifier, solvent_identifier, experimental_deltaG, uncertainty, temperature, charge, radius, dielectric_constant)
- [ ] T004 Setup data schema contracts in contracts/ as JSON Schema files (IonSolventPair.json, BornPrediction.json, ResidualAnalysis.json); validate via jsonschema library; verify schema matches Pydantic models
- [ ] T005 [P] Implement physical constants module in code/physical_constants.py (fundamental physical constants and units) with NIST/CRC citations
- [ ] T005b [P] Pin random seeds in code/born_calculator.py and code/regression_analysis.py per Constitution Principle I (set numpy.random.seed and random.seed at module level)
- [ ] T005c [P] Create data/parameters.csv with physical parameters (e, ε0, ionic radii, dielectric constants) including source citations AND temperature conditions per Constitution Principle VI
- [ ] T006 [P] Setup environment configuration management in code/config.py with fields: data_path, code_path, random_seed, log_level in YAML format; verify via config loading test
- [ ] T008 Configure error handling and logging infrastructure in code/utils/logging.py with JSON log format (timestamp, level, module, message) and error handling patterns (try/except with logging); verify via log output test
- [ ] T009 [P] Setup state checksumming framework: generate hashlib.md5 checksums for ALL files under data/ and code/, save to state/projects/PROJ-675-comparing-born-model-predictions-with-ex.yaml per Constitution Principle V; verify checksums match on re-generation

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

- [ ] T012a [P] [US1] Implement NIST data fetcher in code/data_compiler.py (URL: https://webbook.nist.gov/chemistry/) with retry logic and timestamp logging
- [ ] T012b [P] [US1] Implement CRC Handbook data fetcher in code/data_compiler.py (URL:) with retry logic and timestamp logging; verify fetch completes
- [ ] T013 [US1] Implement Shannon radii extractor in code/data_compiler.py (source: Shannon database) with crystal radius values
- [ ] T014 [US1] **Address Reviewer Concern (Pauling)**: Add radius_type field (crystal/hydrated) to dataset schema AND extraction logic; create radius_type documentation in data/metadata.json with FR-002 traceability; verify documentation exists
- [ ] T015 [US1] **Address Reviewer Concern (Curie)**: Implement uncertainty column population (ΔG_uncertainty, ε_uncertainty) in data/experimental_solvation.csv AND document uncertainty sources in data/metadata.json; verify columns populated
- [ ] T016 [US1] **Address Reviewer Concern (Franklin)**: Enforce high precision for ionic radii in code/data_compiler.py with validation (≥0.01 Å precision); verify precision enforced
- [ ] T017 [US1] **Address Reviewer Concern (Curie/Franklin)**: Record measurement temperature (±0.5°C) and instrument/source metadata for every entry in data/experimental_solvation.csv AND document in data/metadata.json; verify metadata present
- [ ] T018 [US1] Implement data validation script in code/validate_data.py to verify ≥30 complete ion-solvent pairs with uncertainty bounds; assert count and log failures; verify ≥30 pairs exist
- [ ] T019a [US1] **Address SC-005**: Calculate uncertainty coverage percentage (pairs with documented uncertainty / total pairs) and report to data/metadata.json; verify percentage calculated
- [ ] T019b [US1] Generate data dictionary documenting source citations for every value in data/metadata.json; verify citations present

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Implement and Validate Born Model Calculator (Priority: P2)

**Goal**: Implement the Born equation in Python and validate it against known reference cases before applying it to the full dataset, including radius-type selection.

**Independent Test**: Can be fully tested by computing Born predictions for a small reference set and verifying outputs match published analytical values within 1% tolerance (for formula implementation).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for Born equation constants in tests/unit/test_born_calculator.py
- [ ] T021 [P] [US2] Contract test for BornPrediction schema in tests/contract/test_schemas.py

### Implementation for User Story 2

- [ ] T022 [US2] Implement Born equation in code/born_calculator.py with unit conversion utilities; verify formula correct
- [ ] T023 [US2] **Address Reviewer Concern (Pauling)**: Implement radius_type selector (crystal vs hydrated) in code/born_calculator.py; document in docstring and code/README.md; verify selector functional
- [ ] T024 [US2] **Address Reviewer Concern (Pauling)**: Add optional coordination_number_correction parameter in code/born_calculator.py; document limitation in docstring and code/README.md; verify parameter accepted
- [ ] T025 [US2] Implement unit conversion utilities (Å to m, kcal/mol to J) with documented factors in code/born_calculator.py; verify conversions correct
- [ ] T026 [US2] Validate calculator against ≥5 reference ion-water pairs from independent data with ≤1% relative error tolerance in code/validate_born.py; assert tolerance and log failures; verify ≤1% tolerance met
- [ ] T027 [US2] Compute Born predictions for all dataset pairs and save to data/born_predictions.csv; verify file created
- [ ] T028a [US2] [P] CPU-only execution verification test: create tests/unit/test_cpu_only.py that verifies no CUDA imports and completes timing benchmark on 2 CPU cores; verify no GPU dependencies
- [ ] T028b [US2] Performance benchmark: create code/benchmark.py that measures total computation time and asserts <10 minutes on 2 CPU cores without GPU dependencies; verify benchmark passes

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Analysis and Breakdown Detection (Priority: P3)

**Goal**: Perform statistical regression of residuals against independent variables, identify systematic deviation patterns, and determine breakdown thresholds.

**Independent Test**: Can be fully tested by running the regression pipeline and verifying that RMSE, correlation coefficient, p-values, and diagnostic plots are computed with multiple-comparison correction applied.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Contract test for ResidualAnalysis schema in tests/contract/test_schemas.py
- [ ] T030 [P] [US3] Unit test for regression correction logic in tests/unit/test_regression_analysis.py

### Implementation for User Story 3

- [ ] T031 [US3] Calculate residuals (experimental - theoretical) and stratify by solvent class (water, alcohols, aprotic) in code/regression_analysis.py; save stratified RMSE to data/residual_analysis.csv; verify stratification complete
- [ ] T032 [US3] **Address Reviewer Concern (Curie)**: Separate error analysis for dielectric constant measurement vs solvation energy determination in code/regression_analysis.py; output both analyses to data/residual_analysis.csv; verify separation in output
- [ ] T033 [US3] Apply Benjamini-Hochberg multiple-comparison correction to all hypothesis tests with p < 0.05 threshold in code/regression_analysis.py; flag p-value failures for paper documentation; verify correction applied
- [ ] T034a [US3] **Address FR-007**: Implement sensitivity analysis on RMSE threshold over a range of values in kcal/mol in code/regression_analysis.py; output classification rate variation to data/sensitivity_analysis.csv; verify all three thresholds tested
- [ ] T034b [US3] **Address SC-003**: Calculate and validate RMSE < 5 kcal/mol and correlation > 0.8 metrics with pass/fail reporting in code/regression_analysis.py; verify metrics computed
- [ ] T035a [US3] Generate all three diagnostic plots with specific output filenames: (a) data/plots/predicted_vs_experimental.png, (b) data/plots/residual_vs_radius.png, (c) data/plots/residual_vs_dielectric.png in code/diagnostics.py; verify all three plots exist
- [ ] T035b [US3] [P] Validate all three diagnostic plots exist and are non-empty; assert file existence and size > 1KB; verify plots non-empty
- [ ] T036a [US3] **Address SC-003**: Calculate correlation coefficient per solvent class and validate > 0.8 cutoff; report pass/fail to data/metrics_summary.csv; verify correlation validated
- [ ] T036b [US3] **Address Constitution Principle VII**: Flag p-value failures in paper draft (paper/limitations.md) with explicit limitation statements; verify flagging in paper
- [ ] T036c [US3] Save regression results to data/residual_analysis.csv with p-values, confidence intervals, and classification rates; verify all fields present
- [ ] T037 [US3] Flag outliers (RMSE > 20 kcal/mol) for manual review in data/residual_analysis.csv with review_required flag; verify outliers flagged

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address reviewer limitations

- [ ] T038 [P] **Address Reviewer Concern (Pauling)**: Document continuum dielectric limitation and hydration shell discrepancy in code/README.md and output reports; reference FR-002 explicitly; verify documentation created
- [ ] T039a [P] Remove unused imports across code/; verify via flake8 --select=F401
- [ ] T039b [P] Apply consistent naming conventions across code/; verify via black --check
- [ ] T039c [P] Achieve docstring coverage > 80% across code/; verify via pydocstyle
- [ ] T040a [P] Vectorize operations in code/regression_analysis.py using numpy; measure speedup
- [ ] T040b [P] Implement caching for repeated calculations in code/; measure memory/time savings
- [ ] T040c [P] Benchmark overall performance; verify <10 minutes total runtime on 2 CPU cores
- [ ] T041a [P] Achieve unit test coverage > 80% across code/; verify via pytest --cov
- [ ] T041b [P] Add edge case tests for NaN, infinity, empty inputs in tests/unit/
- [ ] T041c [P] Add integration tests for full pipeline in tests/integration/
- [ ] T042 [P] Security hardening: run pip-audit on requirements.txt and pip check for dependency conflicts; fix all vulnerabilities; verify no vulnerabilities remain
- [ ] T043 [P] Run quickstart.md validation: python -m code.born_calculator, python -m code.data_compiler, pytest tests/; verify all pass; verify quickstart passes
- [ ] T044 [P] Final state checksum update in state/projects/PROJ-675-comparing-born-model-predictions-with-ex.yaml; verify all artifacts checksummed

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
Task: "Implement NIST data fetcher in code/data_compiler.py"
Task: "Implement CRC Handbook data fetcher in code/data_compiler.py"
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
- **Reviewer Concerns**: Tasks T014, T015, T016, T017, T023, T024, T032, T038 specifically address prior research-stage reviews regarding radius types, uncertainty, temperature, and continuum limitations. T038 explicitly references FR-002.
- **Constitution Principles**: T005b addresses Principle I (Reproducibility), T009 addresses Principle V (Versioning Discipline), T005c addresses Principle VI (Thermodynamic Parameter Consistency), T033 and T036b address Principle VII (Statistical Significance Thresholds).