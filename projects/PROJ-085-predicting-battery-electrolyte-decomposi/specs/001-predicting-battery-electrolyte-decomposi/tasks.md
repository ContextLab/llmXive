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
 1. Dalton constant: `DALTON_KG = 1.66053906660e-27` (Source: NIST, https://physics.nist.gov/cgi-bin/cuu/Value?mud [CITATION: c_1a09f818])
 2. Faraday constant: `FARADAY_C = 96485.33212` C/mol
 3. Potentials list: `PHI_VALUES` will be evaluated across a range of non-negative voltage magnitudes.
 4. Create empty schema structure for `code/utils/reactions.yaml` with keys: `molecule_id`, `potential_v`, `reactants`, `products`, `n_electrons`, `energy_products`, `energy_reactants`. (Do not populate data yet).
- [X] T011a [P] Populate `code/utils/reactions.yaml` with hardcoded reference data for EC, DMC, LiPF6 at potentials 0V, 2V, 4V. **Strict Data**: Use these exact 3 sample rows for schema validation and unit tests ONLY (DO NOT use for full model training):
 - Row 1: `molecule_id: EC-0V`, `potential_v: 0`, `reactants: [EC]`, `products: [CO2, C2H4]`, `n_electrons: 2`, `energy_products: <reference_value>`, `energy_reactants: <reference_value>`
 - Row 2: `molecule_id: DMC-2V`, `potential_v: 2`, `reactants: [DMC]`, `products: [CH3OH, CO2]`, `n_electrons: 1`, `energy_products: -8.1`, `energy_reactants: [negative value]`
 - Row 3: `molecule_id: LiPF6-4V`, `potential_v: 4`, `reactants: [LiPF6]`, `products: [LiF, PF5]`, `n_electrons: 1`, `energy_products: -12.3`, `energy_reactants: <energy_products>`
 **Dependency**: T004 (Schema must exist first).
- [X] T011c [P] [US1] **CRITICAL**: Implement `code/utils/reaction_engine.py` to generate reaction stoichiometry and energy estimates for the FULL ingested dataset. **Algorithm**: Use RDKit to identify functional groups and apply a Group Contribution Method (GCM) or query a verified chemical database (e.g., PubChem via `pubchempy`) to determine decomposition products and stoichiometry for *any* molecule in the dataset, not just the 3 samples. This engine must be callable by T016. (FR-002, FR-008).
- [X] T005 [P] Implement data directory structure (`data/raw`, `data/processed`, `data/validation`) and checksum logic
- [X] T006 [P] Setup pytest configuration and contract validation schema loaders
- [X] T007 Create base `ElectrolyteMolecule` and `DecompositionEvent` dataclasses in `code/utils/models.py`
- [X] T008 [P] Configure logging infrastructure to capture warnings for missing geometric data and metallic behavior outliers
- [X] T009 [P] Setup environment configuration management for random seeds and dataset URLs

### Phase 2.5: External Data Verification (Moved from Phase 7)

**Purpose**: Resolve the critical data gap for external validation BEFORE modeling begins.

- [X] T050 [P] [US3] **CRITICAL**: Implement `code/data/external_search.py` to programmatically search for and validate access to experimental onset potentials. **Action**: Query verified sources (NOMAD API, Materials Project experimental logs, PubChem) using keywords 'electrolyte', 'onset potential', 'cyclic voltammetry'. Check specific DOIs cited in `research.md`. **Constraint**: If no real source is found, set `external_data_available = False` in `data/validation/data_status.json`. **DO NOT** generate synthetic data.
- [ ] T051 [P] [US3] **CRITICAL**: Update `code/models/evaluator.py` to read `data/validation/data_status.json`. **Logic**: If `external_data_available` is False, set `validation_mode = 'internal_fallback'` and log a warning. **DO NOT** halt the pipeline. (FR-006).
- [X] T052 [P] [US3] **Contingency**: If T050 fails to find a dataset, implement `code/reports/limitations.md` to formally document the data gap, citing the specific search methods and sources checked. **Action**: This report must be generated automatically if `validation_mode = 'internal_fallback'`.
- [X] T053 [P] [US3] Update `docs/research.md` to explicitly state the final status of the experimental data search (Found: [URL/DOI] OR Not Found: [Reason]). **Constraint**: This update is mandatory before any further modeling work.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-computed DFT structures from HuggingFace/NOMAD, filter for EC/DMC/LiPF6, and extract descriptors (HOMO, LUMO, geometry) to calculate decomposition energy.

**Independent Test**: Run extraction on a small fixed subset; verify output CSV columns, no missing features, and $E_{decomp}$ calculation matches manual formula within 0.01 eV.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for decomposition energy formula in `tests/unit/test_target_calc.py`
- [ ] T045 [P] [US1] Integration test for data ingestion pipeline on sample subset in `tests/integration/test_ingestion.py`. **Dependency**: T004 (constants), T011a (reactions.yaml), T011c (reaction engine). **Note**: Renumbered from duplicate T011 to resolve ID collision.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/data/ingestion.py` to fetch and filter DFT data from HuggingFace dataset ID: `materialsproject/mp-dft-electrolytes`. **STRICT**: If fetch fails, raise `DataNotFoundError` with a clear message. **DO NOT** use mock CSV or synthetic data. **Coverage Check**: Explicitly verify the dataset contains entries for EC, DMC, AND LiPF6; raise `CoverageError` if any are missing. (FR-001, FR-008).
- [ ] T013 [P] [US1] Implement deduplication logic in `code/data/ingestion.py` based on molecule ID and potential
- [ ] T014 [US1] Implement `code/data/descriptors.py` to extract HOMO, LUMO, band gap, bond lengths, angles, dihedrals using `pymatgen`/`RDKit` (FR-003)
- [ ] T015 [US1] Implement logic in `code/data/descriptors.py` to extract specific geometric features (including bond lengths, bond angles, and dihedral angles) to meet FR-003 minimum count. Flag/exclude metallic (zero/negative gap) outliers.
- [ ] T016 [US1] Implement `code/data/target_calc.py` to calculate $E_{decomp}$ using the **Reaction Stoichiometry Engine** (T011c) for $\phi \in \{0, 2, 4\}$ V (FR-002, FR-008). The engine generates reaction data for all ingested molecules, not just the hardcoded samples.
- [X] T017 [US1] Add validation logic to ensure feature matrix has no missing values before output
- [ ] T018 [US1] Split data into Train/Validation/Held-Out sets using a fixed random seed. **Ratios**: A majority proportion for Train, with smaller, equal proportions for Validation and Held-Out (standard split). Save processed feature matrix, targets, and the held-out set to `data/processed/electrolyte_features.csv` and `data/processed/electrolyte_heldout.csv`.
- [ ] T019 [US1] Implement stratification logic to split data into 'Low' (0-2V) and 'High' (3-5V) bins. **Note**: Explicitly map spec's '3-5V' range to the available 4V data point. Save bin assignments to `data/processed/bins.csv`.
- [X] T019b [US1] **CRITICAL**: Implement bin validity check. If the 'High' potential bin (mapped to a designated high voltage level) contains an insufficient number of samples, set `high_bin_valid = False`. in `data/validation/bin_statistics.json` and log a warning. **Action**: This flag will prevent invalid model training in T022/T023.
- [X] T019c [US1] **CRITICAL**: Implement 'Single-Point Analysis' logic. If `high_bin_valid` is False, the system must flag that statistical shift analysis is invalid and prepare to run models in a 'single-point' mode (no ranking comparison) rather than attempting a false statistical comparison.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Feature Importance Ranking (Priority: P2)

**Goal**: Train Random Forest Regressor on extracted data, generate permutation importance, and analyze ranking shifts across potential bins (0-2V vs 4V).

**Independent Test**: Train on a standard train-test split, verify R² score, and generate heatmap showing top features for low vs high potential bins.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for Random Forest training with 5-fold CV in `tests/unit/test_trainer.py`
- [X] T021 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/models/trainer.py` to train Random Forest with 5-fold CV and hyperparameter tuning using GridSearchCV. **Search Space**: `n_estimators=[100, 200, 500]`, `max_depth=[10, 20, None]`. **Bin Logic**: Explicitly map all requests for the 'High-potential (3-5V)' range to the available 4V data point. **Conditional**: If `high_bin_valid` is False (from T019b), run the model in 'single-point mode' (no cross-validation if n<3) and log a warning. (FR-004)
- [ ] T023 [US2] Implement `code/models/evaluator.py` to calculate permutation importance for each bin (FR-005). **Dependency**: Requires model artifact from T022. **Conditional**: If `high_bin_valid` is False, skip importance calculation for the 'High' bin or report "Insufficient data for ranking".
- [X] T024 [US2] Implement logic to identify descriptors entering top 3 in high-potential (4V) but absent in low-potential (0-2V). **Note**: Explicitly reference spec's 3-5V range and note the mapping to 4V data point as a known limitation. **Conditional**: If `high_bin_valid` is False, report "Insufficient data for high-potential comparison" in the final report.
- [X] T024b [US2] Perform 'Representativeness Check' on the single 4V data point. If the sample size for the high-potential bin is < 10, flag this as a statistical power limitation in `data/validation/bin_statistics.json` AND append a section to `docs/research.md`. **Action**: This flag must be visible in the final report.
- [X] T025 [US2] Generate heatmap visualization of top features per bin using `seaborn` and save to `data/validation/feature_importance_heatmap.png`. **Conditional**: If `high_bin_valid` is False, generate a heatmap showing only the 'Low' bin and annotate the missing 'High' bin.
- [ ] T026 [US2] Save model artifacts, R² scores, and importance maps to `data/processed/model_run.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Experimental Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Validate predictions against independent experimental onset potentials from literature and perform a sensitivity analysis on the decomposition energy threshold.

**Independent Test**: Calculate MAE against experimental set; verify top 3 descriptor ranks change by ≤1 position when threshold sweeps {0.45, 0.50, 0.55} eV.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for sensitivity analysis sweep logic in `tests/unit/test_sensitivity.py`
- [X] T028 [P] [US3] Integration test for internal validation pipeline in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [ ] T042 [US3] **STRICT GATE**: Implement external data validation logic in `code/models/evaluator.py`. **Action**: Check `data/validation/data_status.json`. If `external_data_available` is True, load external data and calculate MAE/R² (FR-006). If `external_data_available` is False, **PROCEED** to internal validation (T044), log a warning "External validation skipped: data not found; using internal fallback", and generate the limitation report. **DO NOT** raise a blocking error.
- [X] T043 [US3] Implement calculation of MAE and R² for the external experimental validation set. **Dependency**: Requires successful completion of T042 (external data present). **Note**: This task is skipped if T042 determines data is missing.
- [X] T044 [US3] **Fallback**: If external data is missing (T042), perform internal validation against held-out DFT data and calculate internal MAE/R². Log this as "Internal Validation (Fallback)".
- [X] T045 [US3] **Reporting**: Generate a `data/validation/validation_report.md` that explicitly states: "External Validation: [SUCCESS/FAILED]". If FAILED, include the limitation report from T052.
- [ ] T031 [US3] Implement `code/models/evaluator.py` sensitivity analysis: sweep 'decomposition energy stability cutoff' threshold across a representative range of values (FR-007)
- [X] T032 [US3] Implement rank stability check: Verify that the top 3 descriptors change by no more than 1 position across the sweep. **Logic**: Calculate the absolute difference in rank position for each of the top descriptors. between the baseline (0.50 eV) and the swept values (0.45, 0.55 eV). Assert that `max(abs(rank_diff)) <= 1`. (FR-007, SC-004)
- [X] T033 [US3] Generate sensitivity analysis report and save to `data/validation/sensitivity_report.md`

**Checkpoint**: All user stories should now be independently functional (pending external data)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035a [P] Update `docs/quickstart.md` with setup, data fetching, and run instructions
- [X] T035b [P] Update `docs/research.md` with methodology, data sources (HuggingFace ID), and the note regarding the external validation status (Found/Not Found).
- [X] T036 [P] Code cleanup and refactoring of `code/` modules
- [X] T037 [P] Performance optimization for data loading and model training on CPU
- [X] T039 [P] Update `docs/research.md` to reference the strict validation logic and the specific deviation notes in T019b, T022, T024, T042.
- [X] T040 [P] Additional unit tests for edge cases (duplicate handling, metallic outliers) in `tests/unit/`
- [X] T041 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Phase 2.5 (Data Verification)**: Depends on Phase 2. Must complete before Phase 5.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data output from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model output from US2 AND resolution of Phase 2.5 (Data Source)

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
3. Complete Phase 2.5: Data Verification
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

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
 - Developer C: User Story 3 (including Phase 2.5 data search)
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
- **Validation**: External experimental validation (FR-006) is MANDATORY. If data is missing, the pipeline performs internal validation and flags the limitation (T042, T044, T045).
- **Statistical Validity**: If the 'High' potential bin has <30 samples, modeling for that bin is skipped or run in single-point mode (T019b, T022, T023).
- **Reaction Data**: Reaction energies for the full dataset are generated using a Group Contribution Method (GCM) implemented in T011c.
