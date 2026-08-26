# Tasks: Predicting Reaction Mechanisms from Spectroscopic Data with Machine Learning

**Input**: Design documents from `/specs/001-predicting-reaction-mechanisms/`
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

- [ ] T001a [P] Create project directory structure: `src/`, `tests/`, `specs/001-predicting-reaction-mechanisms/`, `data/`, `state/projects/`
- [ ] T001b [P] Create `__init__.py` files for all `src/` and `tests/` subdirectories to establish Python packages
- [X] T002 Initialize a Python project with `requirements.txt` (scikit-learn, xgboost, pandas, numpy, datasets, pyyaml, pytest, pubchempy, psi4)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `src/utils/logging.py` for warning/flagging logic (edge case handling)
- [ ] T005 [P] Implement `src/utils/io.py` for checksum generation and file I/O helpers (Principle III)
- [ ] T006 Create base schema definitions in `specs/contracts/` (dataset.schema.yaml, output.schema.yaml). **CRITICAL**: This schema MUST explicitly define the 'provenance' field structure. **Exact Schema Snippet to Implement**:
 ```yaml
 provenance:
 type: string
 enum:
 - "kinetic_studies"
 - "validated_intermediate"
 ```
 **Logic**: The 'provenance' field must be a string enum containing ONLY these two values. Any data source providing other values or missing this field must be handled by the ingestion logic (T011/T012) by excluding the row. **Produces**: `specs/contracts/dataset.schema.yaml`.
- [X] T007 [P] Setup `src/ingestion/__init__.py` and `src/modeling/__init__.py` package structures
- [ ] T008 Configure random seed pinning utility in `src/utils/seed.py` (Reproducibility Principle I)
- [ ] T033a [Foundational] Create `src/research/fetch_literature_modes.py` to programmatically fetch known functional group frequencies (e.g., carbonyl, C-H stretch) from NIST WebBook and SDBS public APIs. **Produces**: `data/reference/literature_vibrational_modes.json`. This task replaces manual research with an executable script. <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw IR/NMR data, filter by provenance, merge into unified fingerprints, and verify labels.

**Independent Test**: Run `src/ingestion/preprocess.py` against a small NIST subset; verify output CSV has an appropriate number of bins, valid {SN, SN2, E1} labels, and zero NaNs in labels.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T009 [P] [US1] Contract test for fingerprint schema in `tests/contract/test_fingerprint_schema.py`
- [X] T010 [P] [US1] Integration test for end-to-end ingestion of a small NIST sample in `tests/integration/test_ingestion_flow.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `src/ingestion/load_nist.py` to fetch NIST WebBook JSONL (cm-1). **CRITICAL**: Parse the 'provenance' field. **Logic**: If `provenance` is missing, ambiguous, or not exactly 'kinetic_studies' or 'validated_intermediate', **EXCLUDE the row**. Do not attempt fallback. Strict URL validation.
- [ ] T012 [P] [US1] Implement `src/ingestion/load_pubchem.py` to fetch PubChem Parquet subsets (NMR chemical shift ranges). **CRITICAL**: Parse the 'provenance' field. **Logic**: If `provenance` is missing, ambiguous, or not exactly 'kinetic_studies' or 'validated_intermediate', **EXCLUDE the row**. Do not attempt fallback. Strict URL validation.
- [ ] T013c [US1] Implement `src/ingestion/bin_mapping.py` to generate `data/reference/bin_mapping.json`. **Sequential**: Must run before T013b. This file MUST explicitly define: 'Bins [variable range]: IR (linear interpolation)', 'Bins: NMR -12 ppm (linear interpolation)'.
- [ ] T013b [US1] Implement `src/ingestion/merge_spectra.py` to merge filtered IR (NIST) and NMR (PubChem) datasets. **Sequential**: Depends on T011, T012, T013c. **Logic**: Apply linear interpolation using `data/reference/bin_mapping.json` to create fixed-dimensional vectors. Output: `data/processed/fingerprints.parquet`.
- [ ] T015 [US1] Add outlier detection in `src/ingestion/merge_spectra.py` to exclude spectra with extreme variance or missing frequency ranges.
- [ ] T016a [US1] Implement `src/ingestion/metrics.py` to calculate class balance metrics (max/min ratio) for classes {SN1, SN2, E1}. **Produces**: Intermediate metrics object.
- [ ] T016b [US1] Implement `src/ingestion/reporting.py` to write `data/results/class_balance_report.json` (SC-005) using metrics from T016a.
- [ ] T016c [US1] Implement `src/ingestion/gates.py` to evaluate `data/results/class_balance_report.json`. **Logic**: If `max/min > 2` or any class < 50 samples, write `data/results/class_balance_gate.json` with status "FAIL" and raise a blocking error. **Sequential**: Runs after T016b.
- [ ] T017 [US1] Calculate checksums for all downloaded datasets and record them in `data/checksums.json` AND update `state/projects/PROJ-088-predicting-reaction-mechanisms-from-spec.yaml` `artifact_hashes` map. **Sequential**: Must run after T011/T012 complete to avoid race conditions.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest and XGBoost classifiers with stratified k-fold CV, ensuring no data leakage and strict associational reporting.

**Independent Test**: Run `src/modeling/train.py`; verify JSON report contains mean accuracy, std dev, and per-class F1-scores derived strictly from disjoint folds.

### Tests for User Story 2

- [ ] T018 [P] [US2] Contract test for training output schema in `tests/contract/test_training_report_schema.py`
- [ ] T019 [P] [US2] Integration test for stratified split disjointness in `tests/integration/test_cv_splitting.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `src/modeling/train.py` to train BOTH Random Forest and XGBoost classifiers using **Source-Stratified** k-fold cross-validation. **Algorithm**: Group data by 'data_source', then perform stratified split on 'mechanism_label' within each group to ensure disjoint source sets across folds. This single task handles both models.
- [ ] T022 [US2] Implement `src/modeling/metrics.py` to calculate accuracy, F1, and confusion matrices (SC-001)
- [ ] T024a [US2] Implement `src/utils/reporting.py` to generate JSON reports with explicit "associational" framing (FR-006). **CRITICAL**: Include a built-in filter to exclude causal terms ("cause", "drive", "determine", etc.) during generation.
- [ ] T024b [US2] Implement `src/utils/audit.py` to perform regex audit on generated reports for forbidden causal words and output `data/results/causal_language_audit.json` (FR-006 Independent Test). **Sequential**: Runs after T024a.
- [ ] T026 [US2] Add runtime and memory logging to `src/modeling/train.py` to verify <6h runtime and <7GB RAM (FR-005, SC-004). Output logs to `data/results/runtime_metrics.json`.
- [ ] T026b [US2] Implement `src/utils/efficiency_gate.py` to read `data/results/runtime_metrics.json`, compare against 6h/7GB thresholds (SC-004), and write `data/results/efficiency_gate.json` with a PASS/FAIL status. If FAIL, raise an error to stop the pipeline. **Sequential**: Runs after T026.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Statistical Significance (Priority: P3)

**Goal**: Extract feature importance, run per-bin permutation tests with BH correction, and validate top features against literature.

**Independent Test**: Run `src/analysis/permutation.py`; verify per-bin p-values are generated, BH correction is applied, and p-value < 0.05 is reported.

### Tests for User Story 3

- [ ] T027 [P] [US3] Contract test for importance report schema in `tests/contract/test_importance_report_schema.py`
- [ ] T028 [P] [US3] Unit test for Benjamini-Hochberg correction logic in `tests/unit/test_bh_correction.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `src/analysis/importance.py` to extract and rank feature importance scores from RF/XGBoost (FR-003)
- [ ] T030 [US3] Calculate the variance of feature importance scores across the 5 CV folds. Output a CSV file `data/results/stability_variance.csv` with columns: `bin_id, fold_1_score,..., fold_5_score, sample_variance` (SC-002). **Verification**: Add a check to ensure variance is calculated and reported; if variance > threshold, flag as unstable.
- [ ] T031 [US3] Implement `src/analysis/permutation.py` to run a **per-bin** permutation test (N=200) across the CV folds to assess statistical significance for **all spectral bins** (FR-004). **Constraint**: MUST use CPU-optimized vectorized operations (numpy/scipy) to complete within 6h. Do NOT offload to GPU. Output raw p-values for all bins to `data/results/per_bin_p_values.json`.
- [ ] T032 [US3] Implement Benjamini-Hochberg correction in `src/analysis/importance.py` using the p-values from T031. **CRITICAL**: Apply BH correction to the **full set** of bins to control the False Discovery Rate (FDR). Output `data/results/significant_bins.json`.
- [ ] T033b [US3] Implement `src/analysis/dft_validation.py` to generate `data/reference/reference_vibrational_modes.json`. **Method**: Use `Psi` library with a `BLYP` basis set. **Logic**: Generate input files for a representative set of unique molecular fragments. from the dataset, run DFT calculations to get vibrational modes. **Fallback**: If DFT fails, perform literature lookup and set `confidence_level: low` in the output JSON.
- [ ] T033c [US3] Implement `src/utils/schema_validator.py` to validate the schema of `data/reference/reference_vibrational_modes.json` (from T033b) and `data/reference/bin_mapping.json` (from T013c) before T033 consumes them. **Sequential**: Runs after T033b and T013c.
- [ ] T033 [US3] Implement `src/analysis/validation.py` to map top bins to known vibrational modes using `pubchempy`, `data/reference/literature_vibrational_modes.json` (from T033a), `data/reference/reference_vibrational_modes.json` (from T033b), and `data/reference/bin_mapping.json` (from T013c) (FR-010). **Match Rate Definition**: Calculate match rate as '% of top model bins matching literature peaks within ±10 cm-1 tolerance' (using BOTH T033a and T033b sources). **Sequential**: Depends on T033a, T033b, T013c, T033c.
- [ ] T034 [US3] Implement `src/analysis/validation.py` to verify top features are not proxies for product structure (FR-009) using **Partial Dependence Conditioning** as the specific method to decouple product structure effects.
- [ ] T035 [US3] Add logic to handle "marginally significant" p-values (e.g., 0.051) explicitly in reports (Edge Case)
- [ ] T036 [US3] Generate visualization helper in `src/analysis/validation.py` to map top bins back to frequency ranges (e.g., carbonyl stretch)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Run full end-to-end integration test on a small real dataset subset
- [ ] T038 Update `README.md` and `docs/quickstart.md` with execution instructions
- [ ] T039 [P] Code cleanup and refactoring (remove unused imports, optimize memory usage)
- [ ] T040 [P] Additional unit tests for edge cases (missing labels, noisy spectra) in `tests/unit/`
- [ ] T041 Validate `quickstart.md` executes successfully on a fresh runner
- [ ] T042 Verify all causal language is removed from generated reports (manual audit + automated check via T024b)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained models from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loaders/models before services
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
# Launch all tests for User Story 1 together:
Task: "Contract test for fingerprint schema in tests/contract/test_fingerprint_schema.py"
Task: "Integration test for end-to-end ingestion of a small NIST sample in tests/integration/test_ingestion_flow.py"

# Launch all ingestion tasks for User Story 1 together:
Task: "Implement src/ingestion/load_nist.py..."
Task: "Implement src/ingestion/load_pubchem.py..."
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
- **Data Integrity**: Never use synthetic fallbacks; if real data fetch fails or provenance is missing, the task must exclude the row and fail loudly.
- **Causal Language**: Strictly enforce FR-006 in all report generation logic (T024a/T024b).
- **Streaming**: For large datasets, use `streaming=True` in `datasets` library to stay within RAM limits.
- **Provenance Parsing**: T011/T012 must explicitly parse 'provenance' metadata to satisfy FR-008. If missing, EXCLUDE.
- **Merge Step**: T013b is critical to unify IR/NMR into the -bin fingerprint using linear interpolation defined in T013c.
- **Permutation Test**: T031 implements full permutation on a substantial number of bins using CPU-optimized vectorized operations. T032 applies correction to the full set.
- **Stability Reporting**: T030 calculates variance and outputs CSV directly.
- **Literature Validation**: T033a generates the static reference JSON. T033b generates the DFT reference JSON. T033c validates T033b. T033 consumes BOTH T033a and T033b.
- **State Update**: T017 must update the project state YAML file AND write `data/checksums.json`.
- **Partial Dependence**: T034 explicitly mandates Partial Dependence Conditioning for FR-009.
- **Bin Mapping**: T013c defines the exact bin-to-frequency mapping required for validation.
- **Efficiency Gate**: Tb enforces the 6h/7GB limit as a hard gate.
- **Class Balance Gate**: T016c enforces the max/min <= 2 threshold as a hard gate.
- **Source-Stratified CV**: T020 ensures batch effects are controlled via groupby-stratify logic.