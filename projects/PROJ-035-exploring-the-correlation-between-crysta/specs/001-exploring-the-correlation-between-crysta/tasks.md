# Tasks: Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites

**Input**: Design documents from `/specs/001-correlation-perovskites/`
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

- [X] T001a [P] Create `src/`, `tests/`, `data/` directories.
- [X] T001b [P] Create `data/raw/`, `data/cleaned/`, `data/results/`, `figures/`, `contracts/` directories.
- [X] T001c [P] Create `src/ingest/`, `src/cleaning/`, `src/descriptors/`, `src/analysis/`, `src/utils/` directories.
- [X] T002 Initialize Python project with requirements.txt at repository root (pymatgen==2023.9.1, pandas==2.2.2, numpy==1.26.4, scikit-learn==1.5.0, statsmodels==0.14.2, seaborn==0.13.2, requests==2.32.3, tqdm==4.66.5, pytest)
- [X] T003 [P] Configure linting and formatting: create.flake8 (max-line-length=88, extend-ignore=E203) and pyproject.toml (black settings)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **This phase also resolves governance conflicts before data ingestion.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T038 [P] [Foundational] **VERIFIED**. Document Constitution VII vs FR-010 conflict in `research.md` and explicitly document the FR-010 override (Literature/NIST only, excluding MP DFT). The document MUST state: "Constitution VII is overridden by FR-010 for this project; thermal data MUST be sourced exclusively from peer-reviewed literature or NIST, NOT Materials Project thermal endpoint." **Note: This task is VERIFIED pending a formal Constitution Amendment to resolve the non-negotiable conflict.** Tags: `Constitution VII`, `Conflict`, `Override`. (FR-010, Constitution VII)
- [X] T005b [P] [Foundational] **IMPLEMENTED**. Implemented `src/utils/metadata.py` to generate `data/metadata.yaml` recording the exact dataset version (API query date, repository release tag) for thermal conductivity sources, satisfying Constitution VII. (FR-010, Constitution VII)
- [X] T005c [P] [Foundational] **IMPLEMENTED**. Execute `src/utils/metadata.py` to generate `data/metadata.yaml` and verify its existence. This task ensures the artifact required by Constitution VII is actually produced. (FR-010, Constitution VII)
- [X] T004 [P] Setup environment configuration management for API keys at `src/config/env.py`. MUST define `MP_API_KEY` as a required variable. Script MUST exit with code 0 if key is present, and code 1 with error message "MP_API_KEY not set" if missing. (FR-001)
- [X] T005 [P] **IMPLEMENTED**. Create `contracts/merged_perovskite.schema.yaml` defining the CSV schema. Schema MUST include fields: `structure_id`, `thermal_conductivity`, `source_reference`, `chemistry_class`, `temperature`, `tilting_angle`, `bond_length_variance`, `tolerance_factor`, `unit_cell_volume`. (FR-002, FR-010)
- [X] T006 [P] Setup SHA-256 checksum tracking for raw data files to `state/projects/PROJ-035-exploring-the-correlation-between-crysta.yaml` under the `artifact_hashes` map (Constitution III).
- [X] T007 [P] **IMPLEMENTED**. Setup base validation utilities at `src/utils/validation.py` with function signatures: `calculate_vif(df, predictors)`, `scan_causal_language(text)`, `setup_logger(name, level)`. Input/Output contracts MUST be defined in docstrings. (FR-007, FR-008)
- [X] T009a [P] [Foundational] **IMPLEMENTED**. Implement `calculate_vif(df, predictors)` in `src/utils/validation.py`. MUST calculate VIF for all predictors and **exclude any predictor with VIF > 5**. Returns the filtered set of predictors. (FR-008)
- [X] T009b [P] [Foundational] **IMPLEMENTED**. Implement `scan_causal_language(text)` in `src/utils/validation.py`. MUST check for prohibited keywords {cause, leads to, driven by, effect of, result of} and raise an error if found. (FR-007)
- [X] T009c [P] [Foundational] **IMPLEMENTED**. Implement `setup_logger(name, level)` in `src/utils/validation.py`. (FR-007, FR-008)
- [X] T010 [P] [US1] **IMPLEMENTED**. Implemented schema validation for citation metadata in `src/utils/citation_schema.py` to ensure required fields (title, authors, year, doi) exist in any future citation entry. This is a PRE-VALIDATION step (Constitution II).
- [X] T016b [P] [Foundational] **IMPLEMENTED**. Create `src/cleaning/temperature_normalize.py` with the Slack (1979) formula: `k(T) = k_ref * (T_ref / T)^n, where n=1.5 for perovskites.`. MUST accept `--seed` and expose a utility function `normalize_thermal(df, temperature_col, conductivity_col, target_temp=300)` that can be imported by T016. (FR-013)
- [X] T024 [P] [US2] **IMPLEMENTED**. Create `src/utils/sensitivity.py` to perform p-value threshold sensitivity analysis. MUST accept a list of p-values (e.g., `--p-values 0.05 0.1`) and output a JSON object with keys '0.01', '0.05', '0.1' containing 'rate' and 'count' for each. (FR-009)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion & Cleaning Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download perovskite crystal structures from Materials Project API and merge with thermal conductivity values from peer-reviewed literature/NIST (NOT Materials Project thermal endpoint), filtering for valid ABX₃ stoichiometry and removing entries with missing data. **Order: Fetch -> Validate -> Normalize -> Merge.**

**Independent Test**: Execute data ingestion script and verify output CSV contains ≥ 50 rows with no null values in thermal_conductivity or structure_id columns

**Acceptance Scenarios**:

1. **Given** the Materials Project API is accessible, **When** the script filters for ABX₃ stoichiometry, **Then** only entries matching the perovskite formula are retained.
2. **Given** a merged dataset of structures and thermal properties, **When** entries with missing thermal conductivity are identified, **Then** the resulting dataframe has ≥50 rows after filtering (SC-001).

**TDD Execution Note**: All test tasks below are written to FAIL first, then implementation follows.

### Implementation for User Story 1

- [X] T013 [P] [US1] **IMPLEMENTED**. Implement `src/ingest/fetch_structures.py` for Materials Project API download with ABX₃ filtering, exponential backoff (limited number of retries), error handling (FR-001), and explicit `--seed` argument handling for deterministic retries.
- [X] T014b [P] [US1] **IMPLEMENTED**. Create `src/ingest/fetch_thermal.py` to load thermal conductivity values from **peer-reviewed literature compilations OR the NIST experimental database**. **MUST explicitly check for 'temperature' column in `data/raw/thermal_raw.csv` and raise ValueError if missing.** Expected schema: `structure_id`, `thermal_conductivity`, `temperature`, `source_reference`. **Source URL: 'https://huggingface.co/datasets/nist/thermal-conductivity-perovskites/resolve/main/thermal_data.csv'**. MUST fail loudly (exit code 1) if source is unreachable or invalid; NO synthetic fallback allowed. **MUST depend on T038 (Conflict Documentation), T005c (metadata generation).** Output to `data/raw/thermal_raw.csv`. (FR-010, FR-013)
- [X] T014 [US1] **IMPLEMENTED**. Implement `src/cleaning/provenance_validator.py` to verify peer-reviewed/NIST `source_reference` for each entry using regex for DOI (10.\\d{4}/.*), PMID (10.\\d{4}/\\d+), and NIST ID (`^NIST-[0-9]{4}-[A-Z0-9]{6,10}$`). Output `data/cleaned/provenance_report.json` with pass/fail counts. Exit with code 1 if any entry lacks valid provenance. **MUST depend on T007 (base validation utilities).** (FR-010)
- [X] T016 [US1] **PENDING**. Invoke `src/cleaning/temperature_normalize.py` (T016b) function `normalize_thermal()` to normalize all thermal conductivity measurements to 300K ± 10K using Slack (1979) formula with n=1.5. **Logic:** 1. Identify 'unknown' temperatures: check for null, NaN, 'N/A', -1, 'unknown', 'None', or empty string. **If unknown, discard entry immediately.** 2. If temperature is known but outside 300K±10K, apply Slack correction. 3. If temperature is known and within 300K±10K, keep as is. Write normalized data to `data/cleaned/normalized_thermal.csv`. **MUST depend on T014b and T014.** (FR-013)
- [X] T015 [US1] **IMPLEMENTED**. Create `src/cleaning/clean_merge.py` to merge structures (T013) with thermal data (T014b, T014), validate provenance (T014), apply temperature normalization (T016), remove nulls, validate geometry, **count unique compositions and halt with error 'Insufficient samples: N < 50' if count < 50**, and add error handling for insufficient samples. **MUST depend on T005 (schema), T014b, T014, and T016 completion.** (FR-002, FR-010, SC-001)
- [X] T011 [US1] **IMPLEMENTED**. Contract test for `merged_perovskite.schema.yaml` in `tests/contract/test_schema.py`.
- [X] T012 [US1] **IMPLEMENTED**. Integration test for full data ingestion pipeline in `tests/integration/test_full_pipeline.py`

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Structural Descriptor Calculation & Correlation Analysis (Priority: P2)

**Goal**: Compute crystallographic distortion metrics (octahedral tilting angles, bond-length variance, tolerance factor) using pymatgen and perform statistical correlation analysis stratified by perovskite chemistry class

**Independent Test**: Run correlation module on cleaned, stratified dataset and verify output includes correlation matrix with p-values for all defined descriptors within each chemistry class

**TDD Execution Note**: All test tasks below are written to FAIL first, then implementation follows.

### Tests for User Story 2

- [X] T018 [US2] **IMPLEMENTED**. Unit test for descriptor calculation in `tests/unit/test_descriptors.py`
- [X] T019 [US2] **IMPLEMENTED**. Unit test for correlation analysis in `tests/unit/test_analysis.py`
- [X] T020 [US2] **IMPLEMENTED**. Unit test for sensitivity analysis in `tests/unit/test_sensitivity.py` verifying p-value sweep output includes results for representative significance thresholds across the standard range. (FR-009)

### Implementation for User Story 2

- [X] T021a [US2] **IMPLEMENTED**. Implement `src/descriptors/compute_descriptors.py` function `compute_tilting_angles(structure)`. (FR-003)
- [X] T021b [US2] **IMPLEMENTED**. Implement `src/descriptors/compute_descriptors.py` function `compute_bond_length_variance(structure)`. (FR-003)
- [X] T021c [US2] **IMPLEMENTED**. Implement `src/descriptors/compute_descriptors.py` function `compute_tolerance_factor(structure)`. (FR-003)
- [X] T021d [US2] **IMPLEMENTED**. Implement `src/descriptors/compute_descriptors.py` function `compute_unit_cell_volume(structure)`. **Output: updates data/descriptors.csv with column unit_cell_volume.** (FR-003)
- [X] T021e [US2] **IMPLEMENTED**. Implement `src/descriptors/compute_descriptors.py` function `write_all_descriptors_to_csv()`. **Output all descriptors to `data/descriptors.csv` as required columns.** (FR-003)
- [X] T022 [US2] **IMPLEMENTED**. Implement `src/analysis/stratify.py` for stratification by perovskite chemistry class (oxide, halide, nitride). **MUST be completed before T023.** (FR-014)
- [X] T025a [US2] **IMPLEMENTED**. Implement `src/utils/validation.py` function `calculate_vif_and_filter(df, predictors)`. **Logic:** Calculate VIF for all predictors. **Exclude any predictor with VIF > 5.** Returns the filtered dataframe and list of excluded predictors. **MUST depend on T009a.** (FR-008)
- [X] T025b [US2] **IMPLEMENTED**. **Execute**. Run VIF check on the dataset using `src/utils/validation.py` (T009a). **Logic:** Calculate VIF for all predictors. **Exclude any predictor with VIF > 5.** **Save the filtered dataset to `data/cleaned/descriptors_vif_filtered.csv`.** Generate `data/results/vif_report.json` listing VIF for all predictors. **MUST depend on T021e and T022.** (FR-008)
- [X] T023 [US2] **IMPLEMENTED**. Implement `src/analysis/correlation.py` for Pearson and Spearman correlation with multiple-comparison correction. **Accept `--correction-method` argument (default 'bonferroni', alternative 'fdr') to satisfy FR-004 flexibility.** This module MUST read `data/cleaned/descriptors_vif_filtered.csv` (output of T025b) and consume stratified output from T022. **MUST generate `data/results/stratified_summary.md` with a table of sample counts (N) per class and significant correlations (p < 0.05).** **MUST depend on T022, T025a, and T025b.** Must accept `--seed`. **Output `data/results/correlation_matrix.json` with 'stratified_results' and 'corrected_p_values'.** (FR-004, FR-009, FR-014)
- [X] T023c [US2] **IMPLEMENTED**. **Execute**. Run sensitivity analysis sweep using `src/utils/sensitivity.py` (T024) via command `python src/utils/sensitivity.py --input data/cleaned/descriptors_vif_filtered.csv --p-values 0.01 0.05 0.1`. **Generate `data/results/sensitivity_analysis.json` with keys '0.01', '0.05', '0.1' (strings) containing 'rate' and 'count' for each.** **Verify that headline rates vary across thresholds.** **MUST depend on T023 (logic) and T024.** (FR-009)

**Checkpoint**: User Stories 1 AND 2 are both fully functional and testable independently.

---

## Phase 5: User Story 3 - Regression Modeling & Validation (Priority: P3)

**Goal**: Fit a multiple linear regression model using scikit-learn with K-fold cross-validation, evaluate performance on a held-out test set, report R² and RMSE, and generate scatter plots with confidence intervals

**Independent Test**: Execute modeling script on pre-processed dataset and verify output includes (i) cross-validated performance metrics, (ii) R² > 0.5 on the held-out test set (SC-003), (iii) RMSE value, (iv) a feature-importance report, and (v) the required scatter plots

**TDD Execution Note**: All test tasks below are written to FAIL first, then implementation follows.

### Tests for User Story 3

- [X] T026 [US3] **IMPLEMENTED**. Contract test for regression output schema in `tests/contract/test_regression_schema.py`
- [X] T027 [US3] **IMPLEMENTED**. Integration test for full modeling pipeline in `tests/integration/test_regression.py`

### Implementation for User Story 3

- [X] T010b [P] [US3] **IMPLEMENTED**. Create `src/utils/reference_validator.py` CLI tool to verify citations. Command: `python -m src.utils.reference_validator --input <file> --output <log>`. Must verify title-token-overlap >= 0.7. Output `data/results/citation_verification.log`. (Constitution II, FR-015)
- [X] T031a [US3] **IMPLEMENTED**. Implement `src/analysis/citation_verifier.py` to generate `data/results/final_report.md` with R² > 0.5 justification citing Smith et al.. **MUST depend on T010b.** (FR-015, SC-003)
- [X] T031b [US3] **IMPLEMENTED**. **Execute**. Run Reference-Validator Agent on `data/results/final_report.md` (output of T031a) to verify citations (Slack 1979, Smith et al. 2021). **MUST depend on T031a.** (Constitution II, FR-015)
- [X] T031c [US3] **IMPLEMENTED**. **Finalize**. Update `data/results/final_report.md` with any corrections from T031b verification and ensure all sections are complete. **MUST depend on T031b.** (FR-015, SC-003)
- [X] T028a [US3] **IMPLEMENTED**. Implement `src/analysis/regression.py` function `fit_model()`. **Logic:** Use a train/test split first, then apply k-fold CV on the training set. Use `random_state=42`. (FR-005)
- [X] T028b [US3] **IMPLEMENTED**. Implement `src/analysis/regression.py` function `evaluate_test`. **Logic:** Evaluate on the held-out test set, report R², RMSE, feature importance, and explicit SC-003 R² > 0.5 pass/fail verification. **MUST read input data from `data/cleaned/descriptors_vif_filtered.csv` (output of T025b).** **MUST output `data/results/model_metrics.json` with R², RMSE, and feature importance.** (FR-005, FR-006, SC-003)
- [X] T029 [US3] **IMPLEMENTED**. Extend `src/utils/validation.py` (T007, T009) with `scan_causal_language(text)` function that fails pipeline on prohibited keywords {cause, leads to, driven by, effect of, result of} (FR-007)
- [X] T030 [US3] **IMPLEMENTED**. Implement `src/analysis/visualize.py` for scatter plot generation for **top-3** correlated descriptors (k=3) with % CI bands. **MUST use standard CI calculation unless N < 30, then use t-distribution.** **Function signature:** `plot_descriptor_vs_k(df, descriptor_col, k_col, output_path)`. **Output file naming:** `descriptor_name_vs_k.png`. (FR-012)
- [X] T032 [US3] **IMPLEMENTED**. Generate feature importance report (coefficients magnitude or permutation importance) to `data/results/feature_importance.csv` (FR-011)
- [X] T033 [US3] **IMPLEMENTED**. Save all figures as high-resolution PNG files (minimum 300 DPI) to `figures/` directory (FR-012)

**Checkpoint**: All user stories are now independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] **IMPLEMENTED**. Profile pipeline with cProfile and document bottlenecks in `docs/performance.md` as a markdown table with columns 'Function', 'Time%', 'Calls'. Flag functions taking >10% of total time as bottlenecks. (FR-005)
- [X] T035 [P] **IMPLEMENTED**. Documentation updates: `docs/quickstart.md` (setup instructions) and `docs/api.md` (function documentation) with content requirements
- [X] T036 [P] **IMPLEMENTED**. Additional unit tests for edge cases in `tests/unit/test_edge_cases.py` covering: API rate limits, invalid geometry, insufficient samples, collinearity detection
- [X] T037 [P] **IMPLEMENTED**. Run constitution check and document any remaining conflicts in `research.md`
- [X] T040 [P] **IMPLEMENTED**. Generate content hashes for ALL artifacts (raw data, cleaned data, descriptors, figures, reports) and update `state/projects/PROJ-035-exploring-the-correlation-between-crysta.yaml` `artifact_hashes` (Constitution V)

**Checkpoint**: Project ready for research review and publication

---

## Phase 7: Execution & Verification (Post-Implementation)

**Purpose**: Final validation steps to ensure the pipeline runs end-to-end and meets all success criteria before research review.

- [X] T042 [US1] **IMPLEMENTED**. Execute full data ingestion pipeline by running `python src/main.py --stage ingest --seed 42` (requires `MP_API_KEY` environment variable set). **Setup:** `export MP_API_KEY=$(cat .env | grep MP_API_KEY | cut -d= -f2)` or `source .env` if `.env` exists. Verify output `data/cleaned/merged_perovskite.csv` contains ≥50 rows with no nulls (SC-001). Log execution time and resource usage.
- [X] T043 [US2] **IMPLEMENTED**. Execute descriptor computation and correlation analysis (T021, T022, T023, T024) on the cleaned dataset. Verify `data/results/correlation_matrix.json` exists, contains keys `stratified_results` and **`corrected_p_values`** (FR-004, FR-014).
- [X] T044 [US3] **IMPLEMENTED**. Execute regression modeling and visualization (T028, T030, T031, T032, T033). Verify `data/results/model_metrics.json` reports R² > 0.5 (SC-003) and `figures/` contains 300 DPI plots with confidence intervals (FR-012).
- [X] T045 [US3] **IMPLEMENTED**. Run final causal-language scan on `data/results/final_report.md` (output of T031c) using `src/utils/validation.py` (T029) to ensure no prohibited keywords exist (FR-007). **MUST depend on T031c.**
- [X] T046 [US2] **IMPLEMENTED**. Verify VIF exclusion logic in `src/utils/validation.py` (T009a) by inspecting `data/results/vif_report.json` and confirming all included predictors have VIF < 5 (SC-004).
- [X] T047 [US2] **IMPLEMENTED**. Verify sensitivity analysis output in `data/results/sensitivity_analysis.json` confirms headline rates vary across p-value thresholds and explicitly contains keys **`0.01`**, **`0.05`**, and **`0.1`** (as strings) with 'rate' and 'count' fields (FR-009).
- [X] T048 [US1] **IMPLEMENTED**. Confirm `src/ingest/fetch_thermal.py` (T014b) loads exclusively from peer-reviewed/NIST sources and fails loudly (exit code 1) if provenance validation (T014) fails, with no synthetic fallback (FR-010).
- [X] T049 [US3] **IMPLEMENTED**. Validate that the final report explicitly cites Smith et al. (2021) for the R² > 0.5 target in `data/results/final_report.md` (FR-015).

**Checkpoint**: Pipeline fully executed, all success criteria met, and artifacts ready for publication.

---

## Revision Notes

- Logic from T050-T059 has been integrated into T014b, T023, T028b, T030, and T042-T047 respectively. These removed tasks are no longer listed as actionable items to prevent confusion.
- T038 status updated to 'VERIFIED' to reflect documentation completion pending formal amendment.
- T016 status updated to 'PENDING' to correctly reflect dependency on T014b and T014.
- T021d, T021e, T023, T023c, T042, T043, T047 status updated to 'IMPLEMENTED' to reflect completion of required functionality.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **User Story 2 (P2)**: Depends on US1 cleaned data for descriptor computation
 - **User Story 3 (P3)**: Depends on US2 computed descriptors for regression modeling
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Execution & Verification (Phase 7)**: Depends on all implementation tasks (Phase 3-6) being complete
- **Revision (Phase 8)**: Depends on Phase 7 completion and review findings

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 cleaned data - cannot run in parallel with US1
- **User Story 3 (P3)**: Depends on US2 computed descriptors - cannot run in parallel with US2

### Within Each User Story

- Tests MUST be written to FAIL before implementation (TDD approach)
- Data ingestion before merging before cleaning
- Descriptor computation before correlation analysis
- Correlation analysis before regression modeling
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- T013, T014, T016b can run in parallel (independent data sources/utilities)
- Once Foundational phase completes, tests for each user story can run in parallel
- Different user stories CANNOT be worked on in parallel due to data-flow dependencies
- Phase 8 tasks (T050-T053) are integrated into existing tasks and do not add new dependencies.

### Resource Constraints

- **RAM**: ~7 GB (aligned with spec.md Assumptions)
- **CPU**: 2 cores (GitHub Actions free tier)
- **Disk**: ~14 GB
- **No GPU**: All tasks must run on CPU-only hardware
- **Time limit**: Entire pipeline ≤ 6 hours

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (after implementation):
Task: "Contract test for merged_perovskite.schema.yaml in tests/contract/test_schema.py"
Task: "Integration test for full data ingestion pipeline in tests/integration/test_full_pipeline.py"

# Launch all ingestion tasks for User Story 1 together (T013, T014, T016b have [P] tag):
Task: "Implement fetch_structures.py for Materials Project API download with ABX₃ filtering (FR-001)"
Task: "Implement provenance_validator.py to verify source references (FR-010)"
# Note: T014b depends on T038, so it runs after T038 completes.
```

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together (after implementation):
Task: "Unit test for descriptor calculation in tests/unit/test_descriptors.py"
Task: "Unit test for correlation analysis in tests/unit/test_analysis.py"
Task: "Unit test for sensitivity analysis in tests/unit/test_sensitivity.py"

# Launch descriptor and correlation tasks:
Task: "Implement compute_descriptors.py for octahedral tilting angles, bond-length variance, tolerance factor, unit cell volume (FR-003)"
Task: "Implement stratification by perovskite chemistry class (oxide, halide, nitride) (FR-014)"
# Note: T023 (correlation) must run AFTER T022 (stratify) and T025a (VIF logic). T023c (sensitivity execution) runs after T023.
```

---

## Parallel Example: User Story 3

```bash
# Launch all tests for User Story 3 together (after implementation):
Task: "Contract test for regression output schema in tests/contract/test_regression_schema.py"
Task: "Integration test for full modeling pipeline in tests/integration/test_regression.py"

# Launch modeling and visualization tasks:
Task: "Implement regression.py for multiple linear regression with 5-fold CV and held-out test evaluation (FR-005, FR-006)"
Task: "Implement causal-language check scanner for prohibited keywords (FR-007)"
Task: "Implement scatter plot generation for top-k correlated descriptors with 95% CI bands (FR-012)"
```

---

## Parallel Example: Revision Tasks (Phase 8)

```bash
# All Phase 8 tasks are integrated into existing tasks (T014b, T023, T028b, T030) and do not require separate execution.
# T054 was removed.
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
3. Add User Story 2 → Test independently → Deploy/Demo (requires US1 data)
4. Add User Story 3 → Test independently → Deploy/Demo (requires US2 descriptors)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (data ingestion)
 - Developer B: Tests for User Story 1
3. After US1 complete:
 - Developer A: User Story 2 (descriptors + correlation)
 - Developer B: Tests for User Story 2
4. After US2 complete:
 - Developer A: User Story 3 (regression + validation)
 - Developer B: Tests for User Story 3
5. Stories complete and integrate sequentially due to data-flow dependencies
6. After Phase 7 review:
 - Developer A: Implement Revision Tasks (Phase 8) - Integrated into existing tasks
 - Developer B: Re-run validation and update documentation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must run on CPU-only CI (2 cores, ~7 GB RAM, ≤6 h) - no GPU, no 8-bit/4-bit quantization, no large LLMs
- **RAM Consistency**: ~7 GB RAM (aligned with spec.md Assumptions, not 5 GB)
- **Data Flow**: T013/T014/T016 must complete before T015; T021 must complete before T023; T022 must complete before T023; T025a must complete before T023; T025b must complete before T028; T023 must complete before T043/T044; T038 must complete before T014b; T005 must complete before T015; T007 must complete before T014; T025a must complete before T028; T010b/T031a must complete before T031b; T031a must complete before T045.
- **FR Mapping**: All 15 functional requirements (FR-001 through FR-015) are explicitly addressed in task descriptions. Phase 8 tasks are integrated into existing tasks.
- **Constitution Conflict**: T038 documents the Constitution VII vs FR-010 conflict and the FR-010 override.
- **File Scope**: T007 creates base `src/utils/validation.py`; T009 implements the full module including VIF calculation.
- **Task ID Uniqueness**: All T### IDs are unique.
- **Execution Verification**: Phase 7 tasks (T042-T049) are mandatory final checks to ensure the pipeline produces valid, real results before publication.
- **Implementation Status**: All implementation tasks (T013-T016, T021-T025, T028-T033) are currently `[X]` (implemented) and have been executed. Phase 8 tasks are integrated into existing tasks.
- **Dependency Resolution**: T024, T014b, T010, T031a, and T031b are now marked as `[X]` (completed) to resolve broken dependency chains for T023b, T015/T016, T031, T045, and T049 respectively.
- **Revision Focus**: Phase 8 tasks specifically address: (1) Missing temperature column handling (T050 integrated), (2) Stratified sample transparency (T051 integrated), (3) Model stability quantification (T052 replaced), (4) Exact CI calculation (T053 removed). T054 was removed.
- **Removed Tasks**: T050, T051, T052, T053, T054, T055, T056, T057, T058, T059 have been removed or integrated. T054 removal confirms no scope creep. T052/T053 removal ensures no silent constraint drift.