# Tasks: Predicting the Glass Forming Region of Metallic Glass Alloys Using Machine Learning

**Input**: Design documents from `/specs/001-gfr-ml-prediction/`
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `setup.sh` script to initialize project structure. **Deliverables**: Script must contain `mkdir -p projects/PROJ-451-predicting-the-glass-forming-region-of-m/{code,data,tests,docs,notebooks}` and `touch data/raw/.gitkeep data/processed/.gitkeep`. **Verification**: Run `bash setup.sh` and verify directories exist.
- [X] T001c [P] Initialize Python 3.11 project with `requirements.txt` (scikit-learn, xgboost, pandas, numpy, shap, scipy, requests, pytest)
- [ ] T002 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] [US1] Implement `utils/dedup.py` for deduplicating compositions by unique chemical formula. **Algorithm**: Normalize formula to Hill system (C first, then H, then alphabetical), sort elements, compare strings. **Output**: `data/processed/deduped_compositions.csv`. Retain records from primary source (Science Advances) if duplicates exist (FR-010). **Requires**: T001a.
- [X] T004 [P] Create `data/provenance.json` schema for tracking source URLs (Zenodo) and checksums. **Requires**: T001a.
- [ ] T006 [P] Configure environment configuration management. **Deliverables**: Create `.env.example` with placeholders for `MATERIALS_PROJECT_API_KEY` and `ZENO_DO_ID`; create `utils/config.py` to load and validate these keys (must be non-empty strings).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Load alloy composition data from Science Advances and Materials Project, compute atomic-scale descriptors, and output a structured dataset.

**Independent Test**: verify output dataset contains ≥1000 alloy compositions with ≥10 computed descriptors, and descriptor values fall within physically reasonable ranges (e.g., The atomic size mismatch is constrained to a non-negative range., electronegativity difference ∈ [non-negative, moderate]).

### Implementation for User Story 1

- [X] T007 [P] [US1] Write unit test for `features/descriptors.py` in `tests/unit/test_descriptors.py` (verify formula correctness for the specific descriptors: Atomic Radius, Electronegativity, Valence Electron Concentration, Atomic Size Mismatch, Mixing Enthalpy, etc.). **Note**: This is a TDD 'write test' task; expect initial failure.
- [X] T008 [P] [US1] Write unit test for `utils/dedup.py` in `tests/unit/test_dedup.py` (verify deduplication logic and source retention). **Note**: This is a TDD 'write test' task; expect initial failure.
- [X] T009 [P] [US1] Create `features/descriptors.py` to compute atomic descriptors. **MANDATORY**: Atomic Radius, Electronegativity, Valence Electron Concentration, Atomic Size Mismatch (δ), Mixing Enthalpy (ΔHmix). **Reference**: Use formulas and constants defined in `docs/thermodynamics.md`.
- [ ] T010a [US1] Implement data ingestion script `scripts/ingest_zenodo.py` to fetch from Zenodo DOI `10.1126/sciadv.aaq1566` (file: `alloy_data.csv`). **Constraint**: If the primary DOI source is unavailable (network error, 404, timeout), the script MUST catch the exception and immediately trigger the synthetic generator (T011) to generate sufficient data for CI reproducibility. **DO NOT raise ValueError**. **Requires**: T006.
- [ ] T010b [P] [US1] Implement data ingestion script `scripts/ingest_mp.py` to fetch from Materials Project API (v3, API Key via env, fields: composition, phase, elemental properties). **Constraint**: If the API returns a limited set or fails, log a warning and proceed with available data (do not halt). **Requires**: T006.
- [ ] T010c [US1] Implement merge and validation logic in `scripts/ingest.py` to combine Zenodo and Materials Project data. **Logic**: **Before merging**, add a 'source' column to each dataframe tagging rows as 'Science Advances' or 'Materials Project'. Deduplicate by chemical formula (retain Zenodo). Validate schema. Populate `provenance.json` with **per-record source metadata** (Science Advances vs. Materials Project) for every row, and output `data/raw/combined_raw.csv`. **Requires**: T004, T010a, T010b.
- [X] T011 [US1] Implement synthetic data generator `utils/synthetic.py` to generate valid alloy compositions with realistic descriptors for CI reproducibility fallback when the canonical DOI is inaccessible. **Constraint**: This is a VALID FALLBACK for the main pipeline. **Output**: `data/raw/synthetic_fallback.csv`. **Requires**: T006.
- [ ] T013 [US1] Implement label filtering in `scripts/ingest.py` or `utils/io.py` to exclude compositions lacking definitive phase labels (amorphous/crystalline) per FR-009. **Output**: `data/processed/filtered_labels.csv`.
- [ ] T017a [US1] Implement property filtering in `scripts/ingest.py` to drop compositions with missing elemental properties (e.g., unknown electronegativity). **Logic**: Drop rows with missing values, log count. **Output**: `data/processed/filtered_properties.csv`. **Requires**: T013.
- [ ] T017b [US1] Validate completeness: Ensure ≥95% of compositions have all required properties. **Output**: `data/processed/completeness_check.json`. **Requires**: T017a.
- [ ] T019 [P] [US1] Implement `features/alloy_system_mapper.py` to map compositions to 'alloy_system' strings (e.g., 'Zr-Cu-Al'). **Logic**: Identify most abundant element as base, append secondary elements in Hill order. **Output**: Add 'alloy_system' column to dataset. **Requires**: T017b.
- [ ] T014 [US1] Implement dataset capping logic in `scripts/ingest.py` to enforce ≤10,000 compositions limit per FR-007 using **stratified random sampling** by 'alloy_system' (from T019). **Priority**: Retain records from primary source (Science Advances) first (FR-010). **Requires**: T019, T017b.
- [ ] T016 [US1] Validate completeness and drop final missing rows: Ensure ≥95% descriptor completeness and drop compositions with missing elemental properties. **Output**: `data/processed/completeness_report.json` (Schema: { 'total_rows': int, 'missing_property_count': int, 'drop_count': int, 'remaining_rows': int }). **Requires**: T014.
- [ ] T014a [US1] Verify dataset size meets minimum threshold: Check that the dataset contains ≥1000 compositions after filtering and capping. **Logic**: If count < 1000, trigger T011 to generate additional synthetic data to meet the threshold, then re-verify. **Escalation**: If T011 fails to generate ≥1000 samples, the script MUST exit with a specific error code (e.g., `EXIT_CODE_MIN_SIZE_FAIL`) and log a clear error message, preventing silent pipeline failure. **Output**: `data/processed/size_verification.json`. **Requires**: T016, T011.
- [ ] T015 [US1] Generate `data/processed/engineered_dataset.csv` with all required descriptors, 'alloy_system', and metadata. **Verification**: File must contain columns: 'composition', 'phase', 'alloy_system', 'atomic_radius', 'electronegativity', 'vec', 'size_mismatch', 'electronegativity_diff', 'mixing_enthalpy', and a SHA256 checksum. **Requires**: T014a.
- [ ] T012 [US1] Integration test for data ingestion pipeline in `tests/integration/test_ingestion.py` (Requires T010a, T010b, T010c, T013, T017a, T017b, T019, T014, T016, T014a, T015 completion).

---

## Phase 4: User Story 2 - Model Training and Performance Validation (Priority: P2)

**Goal**: Train Random Forest and XGBoost classifiers with k-fold cross-validation, compare against logistic regression baseline, and perform statistical significance testing.

**Independent Test**: Verify system calculates balanced accuracy, precision, recall, F1-score for all models, and executes paired t-test to report p-values.

### Implementation for User Story 2

- [ ] T019a [P] [US2] Write unit test for model training loop in `tests/unit/test_training.py` (verify stratified split logic). **Note**: This is a TDD 'write test' task; expect initial failure. (Renumbered from duplicate T019).
- [ ] T020 [US2] Create `models/train.py` with stratified k-fold cross-validation logic. **Stratification Logic**: Use 'alloy_system' column (from T019). **Regex**: Extract base element via regex (e.g., `^([A-Z][a-z]*)`). **Fallback**: If <50 samples per system, use simple split. **Function**: `train_models(df, stratify_col='alloy_system')`.
- [ ] T021 [P] [US2] Implement Random Forest classifier training with hyperparameter optimization (grid search or randomized search) within `models/train.py`
- [ ] T022 [P] [US2] Implement XGBoost classifier training with hyperparameter optimization within `models/train.py`
- [ ] T023 [P] [US2] Implement Logistic Regression baseline training in `models/train.py`
- [ ] T024 [US2] Implement metrics calculation (balanced accuracy, precision, recall, F1) in `models/evaluate.py`
- [ ] T025a [US2] Implement **Nadeau & Bengio corrected t-test** logic for multiple hypothesis testing per plan.md summary in `utils/stats.py`. **Mandatory**: This logic must be available before T026.
- [ ] T025b [US2] Implement **Bonferroni correction** logic for multiple hypothesis testing per FR-008 in `utils/stats.py`. **Mandatory**: This logic must be available before T030.
- [ ] T027 [US2] Add logic to handle edge cases: insufficient samples per alloy system for stratification (fallback to simple split or warning). **Requires**: T020.
- [ ] T026 [US2] Implement **paired t-test** using **Nadeau & Bengio corrected t-test** (from T025a) to compare RF/XGBoost vs. baseline, reporting raw p-values. **Constraint**: **MUST call the function implemented in T025a**. **DO NOT use scipy.stats.ttest_rel**. **DO NOT implement inline**. **Input**: Fold-level scores from T027. **Output**: Append raw p-values to `data/results/raw_p_values.json`. **Requires**: T025a, T027.
- [ ] T029 [US2] Add logic to apply stratified train/test split in `models/train.py` (stratify by alloy system) to satisfy FR-003. **Logic**: Default split ratio 80/20 if not configured. **Requires**: T020, T027.
- [ ] T029a [US2] Generate and persist `data/processed/train.csv` and `data/processed/test.csv` artifacts from the split logic. **Verification**: Files must exist and contain the correct stratified splits. **Requires**: T020, T029.
- [ ] T030 [US2] Apply Bonferroni correction (from T025b) to raw p-values (from T026) and output corrected p-values. **Output**: `data/results/corrected_p_values.json`. **Requires**: T026, T025b.
- [ ] T031 [US2] Generate `data/results/model_performance_metrics.json` with all fold-level scores, aggregate metrics, and corrected p-values. **Schema**: { 'metrics': { 'rf': {...}, 'xgb': {...}, 'lr': {...} }, 'p_values': { 'rf_vs_lr':..., 'xgb_vs_lr':... }, 'corrected_p_values': {...} }. **Requires**: T030.
- [ ] T031a [US2] Verify stability: Calculate cross-validation standard deviation of balanced accuracy, compare against a predefined threshold (defined in `utils/config.py`, default 0.05), and log the **threshold_value** used and the **pass_fail_status** in the output JSON. **Output**: `data/results/stability_check.json` (Schema: { 'std_dev': float, 'threshold_value': float, 'pass_fail_status': 'PASS' | 'FAIL' }). **Requires**: T031, T006.
- [ ] T032 [US2] Integration test for full training pipeline in `tests/integration/test_training_pipeline.py`
- [ ] T033 [US2] Add explicit handling for the boundary condition where p = 0.05 exactly in `utils/stats.py`: the system MUST report the exact p-value and a specific status flag (e.g., "boundary_significance") rather than a binary pass/fail, ensuring scientific rigor per the edge case analysis in spec.md.
- [ ] T034 [US2] Ensure `models/train.py` enforces `device="cpu"` explicitly in all model initializations (RF, XGBoost, LR) to prevent accidental GPU usage and ensure compatibility with the 2-core CPU runner constraint.

---

## Phase 5: User Story 3 - Interpretability and Visualization (Priority: P3)

**Goal**: Extract permutation importance and generate SHAP plots to explain model predictions.

**Independent Test**: Verify SHAP plots are generated for the top-ranked descriptors and permutation importance scores are non-negative and sum to unity.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T035 [P] [US3] Unit test for SHAP value computation in `tests/unit/test_interpretability.py`
- [ ] T036 [P] [US3] Integration test for visualization generation in `tests/integration/test_viz.py`

### Implementation for User Story 3

- [ ] T037 [P] [US3] Implement permutation importance calculation in `models/evaluate.py`
- [ ] T038 [US3] Implement SHAP value computation for the trained Random Forest model in `models/evaluate.py`
- [ ] T039 [US3] Generate SHAP summary plot for top descriptors using `matplotlib`/`seaborn` and save to `data/results/shap_summary.png`
- [ ] T040 [US3] Generate feature importance bar chart (top descriptors) and save to `data/results/feature_importance.png`
- [ ] T041 [US3] Write interpretability report to `data/results/interpretability_report.md`. **Sections**: 1. Executive Summary, 2. Top 3 Physical Drivers (must include mean absolute SHAP value and p-value of correlation), 3. SHAP Analysis of Key Descriptors, 4. Implications for Alloy Design.
- [ ] T042 [US3] Implement validation logic in `models/evaluate.py` to verify that permutation importance scores are normalized (sum to 1.0) and non-negative before saving results, ensuring compliance with the acceptance criteria in US-3.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Documentation updates: `quickstart.md` (setup, run, data sources)
- [ ] T044 [P] Documentation updates: `research.md` (methodology, results, statistical tests)
- [ ] T045 Code cleanup and refactoring in `code/`
- [ ] T046 [P] Performance optimization for CPU-only execution (ensure no GPU calls, optimize memory usage)
- [ ] T047 [P] Run quickstart.md validation to ensure end-to-end reproducibility
- [ ] T048 [P] Verify all artifacts (datasets, models, plots) are checksummed in `data/provenance.json`. **Schema**: { 'file_path': str, 'checksum': str (sha256), 'timestamp': str }. **Command**: `python utils/checksums.py verify`. **Requires**: T004.

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
- **User Story 2 (P2)**: Depends on US1 completion (requires `data/processed/engineered_dataset.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (requires trained models from `models/train.py`)

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
Task: "Write unit test for features/descriptors.py in tests/unit/test_descriptors.py"
Task: "Write unit test for utils/dedup.py in tests/unit/test_dedup.py"

# Launch all models for User Story 1 together:
Task: "Create features/descriptors.py to compute atomic size mismatch..."
Task: "Implement data ingestion script scripts/ingest.py..."
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
 - Developer B: User Story 2 (waiting for US1 data)
 - Developer C: User Story 3 (waiting for US2 models)
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
- **Critical Constraint**: All data ingestion must use real sources (Zenodo DOI or Materials Project API); synthetic data is ONLY for CI fallback (T011) if the DOI is inaccessible.
- **Critical Constraint**: All models must run on CPU-only CI with limited cores and memory; no GPU/CUDA dependencies.
- **Critical Constraint**: Dataset must be capped using stratified random sampling to preserve statistical validity (T014), retaining primary source records first.
- **Critical Constraint**: All 5 descriptors (Radius, Electronegativity, VEC, Size Mismatch, Mixing Enthalpy) are mandatory per spec (T009).
- **Critical Constraint**: Paired t-test must be the primary statistical test; Bonferroni correction is mandatory for multiple comparisons (T025b, T026, T030).
- **Critical Constraint**: Bonferroni correction must be applied to final p-values before generating metrics (T030, T031).
- **Critical Constraint**: Data loaders must fail loudly on missing elemental properties (T017a) only if >5% missing, otherwise drop and log.
- **Critical Constraint**: Statistical tests must handle boundary conditions explicitly (T033).
- **Critical Constraint**: Alloy system mapping (T019) must occur before capping (T014) to enable stratification.
- **Critical Constraint**: T026 must use Nadeau & Bengio logic from T025a, not scipy.
- **Critical Constraint**: T029 must persist train/test artifacts (T029a).
- **Critical Constraint**: T014a must ensure minimum size via synthetic fallback, with explicit escalation if fallback fails.
- **Critical Constraint**: T031a must define and log the stability threshold value and pass/fail status.
- **Critical Constraint**: T010c must explicitly tag 'source' column before merge to ensure per-record provenance.
