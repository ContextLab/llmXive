# Tasks: Investigating Microbial Community Succession in Constructed Wetlands

**Input**: Design documents from `/specs/001-microbial-succession/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [X] T001 [P] Initialize project structure and manifest. Create the following directories **relative to the existing project root**: `data/`, `code/`, `tests/`, `state/`, `contracts/`, `data/raw`, `data/processed`, `data/config`, `tests/unit`, `tests/contract`, `tests/integration`, `state/projects`. Immediately after creation, generate `projects/PROJ-280-investigating-microbial-community-succes/MANIFEST.txt` listing all created directories and expected files to verify structure completeness.
- [X] T001b [P] Verify MANIFEST.txt completeness. After T001, run a script to verify that all directories and files listed in `MANIFEST.txt` actually exist. The script MUST: 1) Check `os.path.isdir` for all listed directories; 2) Check `os.access` for write permissions on `data/` and `code/`; 3) Compare the line count of `MANIFEST.txt` against the actual file count in `data/raw` and `data/processed`. If any check fails, log a specific error and exit with code 1.
- [X] T002 [P] Initialize Python 3.11 project with pinned dependencies. Create `projects/PROJ-280-investigating-microbial-community-succes/code/requirements.txt` by manually specifying the following known-compatible versions to ensure deterministic execution: `pandas==2.0.3`, `numpy==1.24.3`, `scipy==1.11.1`, `scikit-bio==0.5.8`, `networkx==3.1`, `statsmodels==0.14.0`, `scikit-learn==1.3.0`, `seaborn==0.12.2`, `matplotlib==3.7.2`, `pyyaml==6.0.1`, `jsonschema==4.18.4`. Do not use `pip freeze`; the file must contain these exact pins.
- [X] T003a [P] Create `.flake8` configuration file in `projects/PROJ-280-investigating-microbial-community-succes/` with rules: `max-line-length=100`, `ignore=E203,W503`, `exclude=venv,build`.
- [X] T003b [P] Create `pyproject.toml` in `projects/PROJ-280-investigating-microbial-community-succes/` with `[tool.black]` section configured for `line-length=100` and `target-version=['py311']`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `contracts/dataset-config.schema.yaml` and a validation script stub. The schema MUST define the JSON structure for `data/config/dataset_ids.json` with fields: `datasets` (array of objects), where each object has `id` (string, required), `source` (enum: ["NCBI_SRA", "Zenodo"], required), `url` (string, required). The task must also create `code/validators.py` with a function `validate_dataset_config(config_path: str) -> bool` that loads the JSON and validates it against this schema, raising a `ValueError` if invalid. **Inline Schema Definition**: The task must include the exact YAML content for the schema:
 ```yaml
 type: object
 properties:
 datasets:
 type: array
 items:
 type: object
 properties:
 id: { type: string }
 source: { type: string, enum: ["NCBI_SRA", "Zenodo"] }
 url: { type: string }
 required: ["id", "source", "url"]
 required: ["datasets"]
 ```
 The validator script must use `jsonschema` to validate the loaded JSON against this schema. Additionally, the validator MUST check the `source` field against a hardcoded whitelist of verified URL patterns. **Inline Implementation**: The script must include the following Python code for validation:
 ```python
 import re
 VALID_SRA = re.compile(r'^(SRR|ERR)[0-9]+$')
 VALID_ZENDO = re.compile(r'^10\.5281/zenodo\.[0-9]+$')
 if source == "NCBI_SRA" and not VALID_SRA.match(id): raise ValueError("Invalid SRA ID");
 if source == "Zenodo" and not VALID_ZENDO.match(url): raise ValueError("Invalid Zenodo URL");
 ```
- [X] T005 [P] Implement `code/utils.py` with shared helpers: VIF calculation, Benjamini-Hochberg FDR correction, checksum generation, and power analysis stub.
- [X] T006 [P] Setup logging infrastructure in `code/utils.py` to handle "CRITICAL DATA GAP", "UNDERPOWERED", and "UNDER-DETERMINED" flags.
- [X] T007 [P] Create base data models for `Sample` and `Taxon` in `code/data_models.py` (matching `contracts/feature-table.schema.yaml`). **Explicit Requirement**: This task MUST fully implement the `Taxon` class with attributes for `id`, `abundance`, and `metadata`, and MUST create the file `contracts/feature-table.schema.yaml` defining the JSON schema for the feature table to unblock T012 and T013. **Inline Schema Definition**: The task must include the exact YAML content for the schema:
 ```yaml
 type: object
 properties:
 samples:
 type: array
 items:
 type: object
 properties:
 sample_id: { type: string }
 stage: { type: string, enum: ["early", "intermediate", "mature"] }
 n_removal: { type: number }
 p_removal: { type: number }
 read_count: { type: integer }
 feature_table:
 type: object
 additionalProperties: { type: integer }
 required: ["sample_id", "stage", "n_removal", "p_removal", "read_count", "feature_table"]
 required: ["samples"]
 ```
- [X] T008 [P] Implement state tracking mechanism in `state/projects/PROJ-280-investigating-microbial-community-succes.yaml` to track artifact hashes.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Preprocess Public 16S Datasets (Priority: P1) 🎯 MVP

**Goal**: Retrieve pre-processed 16S rRNA feature tables and metadata from public repositories, filter for constructed wetlands with nutrient removal metrics, and subsample to uniform depth.

**Independent Test**: Execute `code/01_retrieve_data.py` and `code/02_preprocess.py` against a known public dataset ID; verify output files exist in `data/processed/` with ≥90% expected samples retained and uniform read depth.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_config.py`.
- [X] T010 [P] [US1] Integration test for data retrieval and filtering logic in `tests/integration/test_data_retrieval.py`.

### Implementation for User Story 1

- [X] T011 [US1] [Depends on: T004] Implement `code/01_retrieve_data.py` to load `data/config/dataset_ids.json`, **invoke the validator created in T004** (`validate_dataset_config`) to validate it against verified sources (NCBI SRA/Zenodo), and download pre-processed 16S tables/metadata to `data/raw/`. **Critical Logic**: If the file is missing, malformed, or validation fails, the script MUST log a "CRITICAL DATA GAP" error and immediately halt execution (sys.exit(1)). Include "Data Gap" protocol to halt immediately if no verified dataset found or validation fails.
- [X] T012 [US1] Implement `code/02_preprocess.py` to filter `data/raw/` samples for constructed wetlands with N/P removal metrics, logging excluded sample counts.
- [X] T013 [US1] [Depends on: T012] Implement subsampling logic in `code/02_preprocess.py` to **exclude** samples with **<5,000** initial reads (as per spec Edge Cases) and **subsample** samples exceeding 5,000 reads to a uniform depth. Log the count of excluded samples. **CRITICAL**: If the count of samples drops below a minimum threshold after this exclusion (≥A subset of samples must remain), log "CRITICAL DATA GAP: Insufficient samples after read filtering" and immediately execute `sys.exit(1)`.
- [X] T013b [US1] [Depends on: T013] Validate Sample Pool Size. After filtering in T012 and read exclusion in T013, count the remaining samples. **Create file `data/processed/sample_pool_validation.json`** with schema `{total_samples: int, per_stage: {early: int, intermediate: int, mature: int}}`. **CRITICAL**: If `total_samples` < 30 OR any stage has < 10 samples, log a WARNING "UNDERPOWERED: Sample size below target (total, 10 per stage)" and proceed to the Power Analysis gate (T020) for formal evaluation. Do NOT halt the pipeline here.
- [X] T014 [US1] [Depends on: T013b] Implement FR-015 Sensitivity Analysis (Part 1): Perform subsampling depth sweep (low, medium, high) by re-subsampling from the filtered data produced in T013. Generate intermediate artifacts (`data/processed/low_depth_results.json`, `data/processed/medium_depth_results.json`, `data/processed/high_depth_results.json`) containing the subsampled feature tables.
- [X] T014b [US1] [Depends on: T014] Implement FR-015 Sensitivity Analysis (Part 2): Aggregate results into **`data/processed/robustness_verification_report.json`**. This final artifact MUST be a 'robustness verification report' containing:
 1. Alpha diversity rankings (Shannon) for each depth level.
 2. **Calculate Spearman correlation coefficients** between the rank vectors of (Low vs Medium), (Medium vs High), and (Low vs High).
 3. **Perform qualitative assessment**: Report the correlation coefficients and categorize robustness as 'robust' (coeff > 0.85), 'moderate' (0.7-0.85), or 'weak' (< 0.7). Do NOT use a hard pass/fail threshold like 0.9.
 This task verifies that alpha diversity *rankings* are robust to subsampling depth.
- [X] T015a [US1] Add validation and error handling for missing metadata fields (N/P rates) in `code/02_preprocess.py`.
- [X] T015b [US1] Log the specific exclusion count of samples lacking N/P metadata to `data/processed/exclusion_log.json` as required by Edge Cases to ensure transparency.
- [X] T016 [US1] Implement checksum recording for `data/processed/` files (including `robustness_verification_report.json`, `exclusion_log.json`, and intermediate depth results) in `state/projects/PROJ-280-investigating-microbial-community-succes.yaml`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Calculate Diversity Metrics and Test Community Differences (Priority: P2)

**Goal**: Calculate alpha/beta diversity, perform power analysis, and run PERMANOVA with FDR correction to test for community differences between wetland stages.

**Independent Test**: Run `code/03_diversity.py` on a subset of samples; verify Shannon/Simpson indices are computed (no NaN), PERMANOVA p-values and effect sizes (R²) are generated, and FDR correction is applied.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for diversity output schema in `tests/contract/test_diversity_output.py`.
- [X] T018 [P] [US2] Integration test for PERMANOVA power analysis gate in `tests/integration/test_permanova_gate.py`.

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/03_diversity.py` to calculate Alpha (Shannon, Simpson) and Beta (Bray-Curtis) diversity for all samples in `data/processed/`.
- [X] T020 [US2] [Depends on: T019] Implement FR-014 Power Analysis (Part 1): estimate power for PERMANOVA (effect size R²=0.15) using `statsmodels.stats.power.FTestAnovaPower`. **Read `data/processed/sample_pool_validation.json`** (created by T013b) to derive the final retained sample count for this analysis. **Create file `data/processed/power_analysis_report.json`** with schema `{power: float, n_per_group: int, effect_size: float, flag: "UNDERPOWERED"|"PASS"}`.
- [X] T020b [US2] [Depends on: T020] Implement FR-014 Power Analysis (Part 2): Create file `data/processed/sample_size_validation.json` that explicitly compares the *final retained* sample count against the *power analysis target* (n_per_group) to satisfy SC-001. **CRITICAL**: If `power < 0.8` OR `n_per_group < 10`, log "UNDERPOWERED" error, write the reports, and immediately **TERMINATE the pipeline** (sys.exit(1)). Do NOT proceed to T021 if this condition is met.
- [X] T021 [US2] [Depends on: T020b] **Conditional Execution**: Execute PERMANOVA test in `code/03_diversity.py` to compare community composition between wetland establishment stages (early vs. mature) ONLY if T020b passes (power >= 0.8 and n >= 10).
- [X] T022 [US2] Implement Benjamini-Hochberg FDR correction for pairwise PERMANOVA comparisons in `code/03_diversity.py` (FR-009).
- [X] T023 [US2] Add logic to document small effect sizes (R² < 0.1) as statistically significant but ecologically weak in output reports. Specifically, when calculating PERMANOVA results, if `p_value <= 0.05` AND `r_squared < 0.1`, set the field `ecological_flag` to `"statistically_significant_but_weak"` in the output artifact **`data/processed/diversity_metrics.json`**. **Also log this finding to `data/processed/audit_trail.json`** to ensure transparency as required by Edge Cases.
- [X] T024 [US2] Generate diversity metrics report to `data/processed/diversity_metrics.json` conforming to `contracts/output-metrics.schema.yaml`. **Explicit Requirement**: The output MUST include a field `correction_coverage` calculated as `(count of tests with FDR-adjusted p-values) / (total tests run) * 100` to satisfy SC-006.
- [ ] T045 [US2] [Depends on: T021] Implement PERMANOVA Pairwise Comparison Matrix. Extend `code/03_diversity.py` to perform PERMANOVA for **all** pairwise stage combinations (Early vs Intermediate, Intermediate vs Mature, Early vs Mature), not just Early vs Mature. Apply Benjamini-Hochberg FDR correction across the entire matrix of tests. Output the full pairwise matrix with p-values, R², and FDR-adjusted p-values to `data/processed/permanova_pairwise_matrix.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Construct Co-occurrence Networks and Correlate Taxa with Nutrient Removal (Priority: P3)

**Goal**: Construct Spearman-based co-occurrence networks, calculate modularity, perform sensitivity analysis, and correlate taxa abundances with nutrient removal rates.

**Independent Test**: Run `code/04_network.py` and `code/05_correlation.py`; verify network edges meet threshold (|ρ|≥0.6, p≤0.01), modularity delta is calculated (or under-determined flag raised), and taxa-nutrient correlations with VIF checks are reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for network output schema in `tests/contract/test_network_output.py`.
- [X] T026 [P] [US3] Integration test for VIF and correlation logic in `tests/integration/test_correlation.py`.

### Implementation for User Story 3

- [X] T027 [US3] Implement `code/04_network.py` to calculate Spearman correlation matrix from `data/processed/` taxon abundance data.
- [X] T028 [US3] Implement FR-013 Under-determined Check in `code/04_network.py`: if n_samples < n_taxa, flag as 'under-determined' and skip modularity calculation.
- [X] T031 [US3] [Depends on: T028] Calculate network modularity and signed delta (Δmodularity) between early vs. mature stages. **Output**: Generate **`data/processed/modularity_delta.json`** with schema `{modularity_early: float, modularity_mature: float, delta: float, flag: "UNDER-DETERMINED"|"PASS"}`. If under-determined, log the flag and set delta to null.
- [X] T030 [US3] [Depends on: T031] Implement FR-013 Sensitivity Analysis (Part 1): Sweep correlation thresholds to assess modularity stability. **Algorithm**: Sweep |ρ| from **a lower bound to 0.90** in **incremental steps of 0.05**. For each threshold, compute Δmodularity = modularity_early - modularity_mature. **CRITICAL**: If T031 flag is "UNDER-DETERMINED", skip the sweep, log "Sensitivity N/A: Network under-determined", and set stability variance to null. **Calculate the variance of these Δmodularity values** across the swept thresholds.
- [X] T030b [US3] [Depends on: T030] Implement FR-013 Sensitivity Analysis (Part 2): **Create file `data/processed/network_sensitivity_report.json`** containing the list of thresholds tested and the calculated variance of Δmodularity. **CRITICAL**: If T031 flag is "UNDER-DETERMINED", this task MUST generate a report with `status: "N/A"`, `thresholds: []`, and `variance: null` instead of attempting calculation. Report stability based on the variance (low variance = stable).
- [X] T032 [US3] Implement `code/05_correlation.py` to calculate Spearman correlation between taxon abundances and N/P removal rates using the filtered feature table from T013 and Stage metadata from T012. (Note: Does NOT depend on T019 diversity metrics). <!-- FAILED: unspecified -->
- [X] T033 [US3] [Depends on: T032] Implement VIF calculation in `code/05_correlation.py` to flag predictor taxa with VIF > 5 for collinearity (FR-010) using Stage metadata from T012.
- [X] T034 [US3] [Depends on: T032, T012] Implement **k=3 cross-validation** on the taxa-nutrient correlation model as required by FR-012. **Strict Requirement**: The task MUST perform k=3 cross-validation. If n_samples < 6 (making k=3 impossible), the script MUST log a FATAL error "CRITICAL: Insufficient samples for k=3 cross-validation (n < 6)" and immediately execute `sys.exit(1)`. Do NOT fallback to Leave-One-Out. **Create file `data/processed/correlation_cv_results.json`** containing mean R² and std dev from the CV. Generate final correlation report listing taxa with |r|≥0.5 and p≤0.05, or explicitly state if none met criteria. Output to **`data/processed/correlation_results.json`**.
- [X] T046 [US3] [Depends on: T032] Implement Taxon-Nutrient Correlation with VIF Diagnostics. In `code/05_correlation.py`, ensure that before running the final correlation against N/P removal rates, a Variance Inflation Factor (VIF) calculation is performed on the predictor taxa. If any taxa have VIF > 5, they must be flagged and reported in `data/processed/correlation_vif_flags.json`. The final correlation report must explicitly state which taxa were excluded or flagged due to collinearity to satisfy FR-010.
- [X] T035 [US3] [Depends on: T030b, T034, T031] Generate network and correlation outputs to `data/processed/network_analysis.json` and `data/processed/correlation_results.json` conforming to `contracts/output-metrics.schema.yaml`. **Aggregation Logic**:
 1. Load `data/processed/modularity_delta.json`, `data/processed/network_sensitivity_report.json`, and the list of significant edges from `code/04_network.py` (filtered by |ρ|≥0.6, p≤0.01).
 2. Merge these into `data/processed/network_analysis.json` with schema: `{modularity_delta: {...}, sensitivity: {...}, edges: [...]}`. **Handle 'UNDER-DETERMINED' flag**: If `modularity_delta.flag` is "UNDER-DETERMINED", set `sensitivity` to null and log this state in the report.
 3. Load `data/processed/correlation_results.json` and `data/processed/correlation_cv_results.json`.
 4. Merge these into `data/processed/correlation_results.json` (final) with schema: `{significant_taxa: [...], cv_results: {...}, vif_flags: [...]}`.
 This task aggregates the final results from the network and correlation phases.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `docs/` (README, quickstart.md).
- [X] T038a [P] Refactor VIF logic. Extract the Variance Inflation Factor calculation logic from `code/05_correlation.py` into a dedicated function `calculate_vif` in `code/utils.py`. Update `code/05_correlation.py` to import and use this function.
- [X] T038b [P] Standardize logging format. Refactor `code/02_preprocess.py`, `code/03_diversity.py`, and `code/04_network.py` to ensure all log messages follow the format `^[\\(INFO|WARN|ERROR|CRITICAL\\)] \\[\\w+\\] Message$`. Specifically, update any existing `print` or `logging.info` calls in these files to match this regex pattern.
- [X] T039 [P] Performance optimization to ensure pipeline completes within 6 hours on 2 CPU cores.
- [X] T040 [P] Additional unit tests for edge cases (e.g., empty datasets, missing metadata) in `tests/unit/`.
- [X] T041 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility.
- [X] T043 [US1] [Depends on: T012] Implement Strict Data Loader Failure Protocol. Refactor `code/01_retrieve_data.py` and `code/02_preprocess.py` to **REMOVE** any `try/except` blocks or `if download_failed:` logic that falls back to `generate_synthetic_*()`, `mock_*()`, or placeholder data. If a real fetch fails (network error, 404, schema mismatch), the script MUST raise a structured `sys.exit(1)` with a clear error message logged to `data/processed/audit_trail.json`. This ensures the execution stage discovers the real source issue rather than silently proceeding with fabricated data.
- [ ] T047 [US3] [Depends on: T035] Implement Final Report Aggregation with Data Lineage. Create a new aggregation script `code/99_generate_final_report.py` that merges all JSON artifacts from `data/processed/` (including `sample_pool_validation.json`, `power_analysis_report.json`, `modularity_delta.json`, `network_sensitivity_report.json`, `correlation_cv_results.json`) into a single `data/processed/final_analysis_report.json`. This report MUST include a `data_lineage` section tracing every metric back to its source file and the specific task ID that generated it, satisfying the "Single Source of Truth" constitution principle. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output; network construction (US3) requires sufficient sample size from US1

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
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_config.py"
Task: "Integration test for data retrieval and filtering logic in tests/integration/test_data_retrieval.py"

# Launch all implementation tasks for User Story 1 together (where dependencies allow):
Task: "Implement code/01_retrieve_data.py..."
Task: "Implement code/02_preprocess.py..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Data retrieval and filtering)
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
 - Developer A: User Story 1 (Data Retrieval)
 - Developer B: User Story 2 (Diversity Analysis)
 - Developer C: User Story 3 (Network & Correlation)
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

---

## Revision: Addressing Analyze Findings (New Tasks)

**Purpose**: Address specific gaps identified during analysis of the initial plan and spec, ensuring data flow correctness, robustness, and strict adherence to the "Real Data Only" constitution.

- [X] T043 [US1] [Depends on: T012] Implement Strict Data Loader Failure Protocol. Refactor `code/01_retrieve_data.py` and `code/02_preprocess.py` to **REMOVE** any `try/except` blocks or `if download_failed:` logic that falls back to `generate_synthetic_*()`, `mock_*()`, or placeholder data. If a real fetch fails (network error, 404, schema mismatch), the script MUST raise a structured `sys.exit(1)` with a clear error message logged to `data/processed/audit_trail.json`. This ensures the execution stage discovers the real source issue rather than silently proceeding with fabricated data.
- [ ] T045 [US2] [Depends on: T021] Implement PERMANOVA Pairwise Comparison Matrix. Extend `code/03_diversity.py` to perform PERMANOVA for **all** pairwise stage combinations (Early vs Intermediate, Intermediate vs Mature, Early vs Mature), not just Early vs Mature. Apply Benjamini-Hochberg FDR correction across the entire matrix of tests. Output the full pairwise matrix with p-values, R², and FDR-adjusted p-values to `data/processed/permanova_pairwise_matrix.json`.
- [ ] T046 [US3] [Depends on: T032] Implement Taxon-Nutrient Correlation with VIF Diagnostics. In `code/05_correlation.py`, ensure that before running the final correlation against N/P removal rates, a Variance Inflation Factor (VIF) calculation is performed on the predictor taxa. If any taxa have VIF > 5, they must be flagged and reported in `data/processed/correlation_vif_flags.json`. The final correlation report must explicitly state which taxa were excluded or flagged due to collinearity to satisfy FR-010.
- [ ] T047 [US3] [Depends on: T035] Implement Final Report Aggregation with Data Lineage. Create a new aggregation script `code/99_generate_final_report.py` that merges all JSON artifacts from `data/processed/` (including `sample_pool_validation.json`, `power_analysis_report.json`, `modularity_delta.json`, `network_sensitivity_report.json`, `correlation_cv_results.json`) into a single `data/processed/final_analysis_report.json`. This report MUST include a `data_lineage` section tracing every metric back to its source file and the specific task ID that generated it, satisfying the "Single Source of Truth" constitution principle. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
