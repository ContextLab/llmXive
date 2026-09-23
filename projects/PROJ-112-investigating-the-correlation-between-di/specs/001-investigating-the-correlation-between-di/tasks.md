# Tasks: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [ ] T001 Create project structure per implementation plan:
 - Directories: `src/`, `src/ingestion/`, `src/preprocessing/`, `src/analysis/`, `src/utils/`, `tests/`, `tests/contract/`, `tests/integration/`, `tests/unit/`, `data/raw/`, `data/processed/`, `data/processed/results/`, `docs/`, `state/`
 - Files: `src/main.py`, `src/utils/logger.py`, `src/utils/power_analysis.py`, `tests/test_schemas.py`, `requirements.txt`, `README.md`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing pinned versions:
 - `pandas==2.0.3`, `scikit-learn==1.3.0`, `scipy==1.11.1`, `numpy==1.24.3`, `requests==2.31.0`, `pyyaml==6.0.1`, `joblib==1.3.1`, `miceforest==5.3.3`, `rpy2==3.5.11`
- [X] T003a [P] Create `ruff` configuration file at `pyproject.toml` or `.ruff.toml`
- [X] T003b [P] Create `black` configuration file at `pyproject.toml`
- [X] T004a [P] Create `pytest` configuration file (`pytest.ini` or `pyproject.toml`)
- [ ] T004b [P] Create `tests/conftest.py` for shared test fixtures

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T005 Implement `src/utils/logger.py` for standardized logging
- [X] T006 [P] Implement `src/utils/power_analysis.py` for calculating statistical power and margin of error (CPU-tractable). **Must accept**: sample size, effect size, alpha. **Must output**: power, margin of error. **Verification**: Run `tests/unit/test_power.py` to confirm correctness.
- [ ] T007 Create `src/preprocessing/id_generator.py` to generate SHA256 sample IDs (cohort + original_id)
- [ ] T008 Setup data directory structure (`data/raw/`, `data/processed/`, `data/processed/results/`)
- [X] T009 [P] Implement `src/preprocessing/covariate_handler.py` for MICE imputation (using `miceforest`) and missing data exclusion logic (>20% missing). **Must not** include logging configuration.
- [X] T009a [P] [US1] Generate Exclusion Log: Implement logic to write `data/processed/results/covariate_exclusion_log.txt` recording the count of samples excluded due to >20% missing covariate data. **Depends on**: T009.
- [X] T009b [P] [US1] Validate Covariate Exclusion: Verify `data/processed/results/covariate_exclusion_log.txt` exists and contains valid counts. **Depends on**: T009a.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and harmonize American Gut Project (AGP) and UK Biobank (UKBB) data into a unified dataset.

**Independent Test**: Verify that the pipeline successfully downloads both datasets, filters samples correctly (≥5,000 reads, 0–200 g/day fiber), and outputs a unified CSV/TSV file with consistent column names and units.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_schemas.py`
- [X] T011 [P] [US1] Integration test for ingestion pipeline in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/ingestion/agp_loader.py` to download AGP data from Qiita (verify URL/ID first)
 - **Output**: Must write raw data to `data/raw/agp_raw.tsv`.
 - **Constraint**: Must use `datasets.load_dataset` or `requests` with a verified real URL. **NO** synthetic fallback. If download fails, raise `RuntimeError`.
 - **Streaming**: If the dataset exceeds memory, implement streaming logic to process in chunks.
 - **Validation**: Generate checksum for `data/raw/agp_raw.tsv` and record in `state/artifact_hashes.json`.
- [ ] T013 [P] [US1] Implement `src/ingestion/ukbb_loader.py` to download UKBB data from canonical sources (verify URL/ID first)
 - **Output**: Must write raw data to `data/raw/ukbb_raw.tsv`.
 - **Constraint**: Must use verified UKBB access method (e.g., specific `datasets.load_dataset` ID or official UKBB API wrapper). **NO** synthetic fallback. If download fails, raise `RuntimeError`.
 - **Streaming**: Implement streaming/chunking if the full cohort exceeds available RAM.
 - **Validation**: Run `tests/contract/test_schemas.py` against `data/raw/ukbb_raw.tsv` to validate schema. Generate checksum and record in `state/artifact_hashes.json`.
- [ ] T014 [US1] Implement `src/ingestion/harmonizer.py` to:
 - Convert all fiber units to g/day
 - Filter samples with <5,000 reads
 - Filter samples with fiber intake <0 or >200 g/day
 - Exclude samples with missing fiber data
 - **Mandatory**: Preserve and include a `cohort_id` column (values: "AGP", "UKBB") in the output.
 - Merge into `data/processed/merged_harmonized.tsv`
 - **Logging**: Record counts of filtered samples and reasons for exclusion.
 - **Output Schema**: `sample_id`, `cohort_id`, `fiber_g_day`, `read_count`, `taxon_abundances...`, `covariates...`
- [ ] T015 [P] [US1] Generate PII Scan Report and Artifact Checksums:
 - **Input**: `data/raw/agp_raw.tsv`, `data/raw/ukbb_raw.tsv`, `data/processed/merged_harmonized.tsv`.
 - **Action**: Run PII scan on all data files. Calculate SHA256 checksums.
 - **Output**: Write `data/processed/results/pii_scan_report.json` (must contain zero PII matches) and update `state/artifact_hashes.json` with new checksums.
 - **Verification**: Verify `data/processed/results/pii_scan_report.json` exists and contains `{"pii_found": 0}`.
 - **Depends on**: T012, T013, T014.
- [ ] T016 [P] [US1] Generate Ingestion Log:
 - **Input**: Execution of T012, T013, T014.
 - **Action**: Capture download status, filter counts, and harmonization results.
 - **Output**: Write `logs/ingestion.log` containing entries for: "Download AGP: SUCCESS/FAIL", "Download UKBB: SUCCESS/FAIL", "Filtered Samples: <count>", "Harmonized Samples: <count>".
 - **Verification**: Verify `logs/ingestion.log` exists and contains all required log entries.
 - **Depends on**: T012, T013, T014.
- [ ] T006b_run [US1] Execute Power Analysis: Run `src/utils/power_analysis.py` (T006) on the **filtered** harmonized dataset (`data/processed/merged_harmonized.tsv`) to generate `data/processed/results/power_analysis_report.tsv` containing calculated power and margin of error. **Depends on**: T014, T009, T006.
- [X] T006b_validate [US1] Validate Power Analysis Output: Verify `data/processed/results/power_analysis_report.tsv` contains required columns (`power`, `margin_of_error`, `sample_size`) and that `sample_size` matches the count from T009b log. **Depends on**: T006b_run.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compositional Transformation and Correlation Analysis (Priority: P2)

**Goal**: Apply CLR transformation and compute fiber-taxa associations using MaAsLin2 with FDR correction.

**Independent Test**: Run correlation analysis on a small synthetic dataset with known associations and covariates, verifying output matches expected coefficients and corrected p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for MaAsLin2 output schema in `tests/contract/test_maaslin2_schema.py`
- [X] T019 [P] [US2] Integration test for CLR transformation in `tests/integration/test_clr.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `src/preprocessing/clr_transform.py` to:
 - Add a pseudocount for zero-inflated taxa.
 - Apply centered log-ratio (CLR) transformation.
 - Output to `data/processed/clr_transformed.tsv`.
 - **Validation**: Ensure no `NaN` or `Inf` values remain.
 - **Output Artifact**: Generate `data/processed/results/clr_validation_log.txt` documenting the check.
 - **Exit Code**: Exit with code 1 if validation fails.
 - **Depends on**: T014.
- [ ] T020b [US2] Generate Pseudocount Validation Report:
 - **Input**: `data/processed/clr_transformed.tsv`.
 - **Action**: Run a diagnostic test to verify the chosen pseudocount strategy satisfies Constitution Principle VI.
 - **Metric**: Check if median shift of zero-inflated taxa distributions < 0.01.
 - **Output**: Write `data/processed/results/pseudocount_validation.txt` with the calculated shift and pass/fail status.
 - **Depends on**: T020.
- [ ] T021 [US2] **Primary Task**: Implement `src/analysis/correlation_maaslin2.py` to:
 - **Primary**: Invoke MaAsLin2 (via `rpy2` or `subprocess`) on CLR data to adjust for covariates (age, BMI, antibiotic use).
 - **Secondary (Mandatory)**: Calculate Spearman ρ and Standard Error (SE) for fiber intake vs. CLR-transformed taxa abundances using `scipy.stats.spearmanr` and Fisher's z-transformation.
 - **Constraint**: If R/MaAsLin2 is unavailable, the script MUST fail loudly (exit code 1) rather than falling back to non-compliant methods (ALR/ILR or OLS).
 - **Output**: `data/processed/results/association_results.tsv`
 - **Schema**: Columns must be exactly `taxon`, `maaslin2_beta`, `maaslin2_se`, `maaslin2_p_value`, `maaslin2_q_value`, `spearman_rho`, `spearman_se`, `spearman_p_value`.
 - **Depends on**: T020.
- [ ] T022 [US2] Implement FDR correction (Benjamini-Hochberg) in `src/analysis/correlation_maaslin2.py`:
 - Calculate q-values (if not done by MaAsLin2)
 - Filter and save results to `data/processed/results/association_results.tsv`
 - **Depends on**: T021.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Differential Abundance and Cross-Cohort Validation (Priority: P3)

**Goal**: Perform differential abundance testing (ANCOM-II/DESeq2 as robustness checks), evaluate replication via continuous beta-coefficients, and report summary statistics.

**Independent Test**: Run differential abundance pipeline on both datasets independently, verify output format, and confirm replication status is accurately flagged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for differential abundance output in `tests/contract/test_diff_abundance_schema.py`
- [ ] T027 [P] [US3] Integration test for cross-cohort validation in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [ ] T028a1 [P] [US3] **AGP**: Filter and Downsample:
 - **Input**: `data/processed/merged_harmonized.tsv`.
 - **Logic**: Filter data where `cohort_id == "AGP"`. Project runtime for ANCOM-II/DESeq2. If projection > 5 hours, perform random stratified downsampling (by cohort) to ensure total runtime ≤ 6 hours.
 - **Output**: `data/processed/agp_processed.tsv` (filtered/downsampled).
 - **Depends on**: T014, T020.
- [ ] T028a2 [P] [US3] **AGP**: Run ANCOM-II:
 - **Input**: `data/processed/agp_processed.tsv`.
 - **Execution**: Run ANCOM-II on the AGP cohort.
 - **Output**: `data/processed/results/diff_abundance_agp_ancom.tsv` containing taxa, method, q-value, effect_size, direction (filtered for q < 0.05).
 - **Depends on**: T028a1.
- [ ] T028a3 [P] [US3] **AGP**: Run DESeq2:
 - **Input**: `data/processed/agp_processed.tsv`.
 - **Execution**: Run DESeq2 on the AGP cohort.
 - **Output**: `data/processed/results/diff_abundance_agp_deseq2.tsv` containing taxa, method, q-value, effect_size, direction (filtered for q < 0.05).
 - **Depends on**: T028a1.
- [ ] T028a4 [P] [US3] **AGP**: Calculate Metrics:
 - **Input**: `data/processed/agp_processed.tsv`.
 - **Metric**: Calculate and report absolute median fiber intake (g/day) for high/low groups in AGP.
 - **Output**: `data/processed/results/agp_fiber_metrics.tsv`.
 - **Depends on**: T028a1.

- [ ] T028b1 [P] [US3] **UKBB**: Filter and Downsample:
 - **Input**: `data/processed/merged_harmonized.tsv`.
 - **Logic**: Filter data where `cohort_id == "UKBB"`. Project runtime for ANCOM-II/DESeq2. If projection > 5 hours, perform random stratified downsampling (by cohort) to ensure total runtime ≤ 6 hours.
 - **Output**: `data/processed/ukbb_processed.tsv` (filtered/downsampled).
 - **Depends on**: T014, T020.
- [ ] T028b2 [P] [US3] **UKBB**: Run ANCOM-II:
 - **Input**: `data/processed/ukbb_processed.tsv`.
 - **Execution**: Run ANCOM-II on the UKBB cohort.
 - **Output**: `data/processed/results/diff_abundance_ukbb_ancom.tsv` containing taxa, method, q-value, effect_size, direction (filtered for q < 0.05).
 - **Depends on**: T028b1.
- [ ] T028b3 [P] [US3] **UKBB**: Run DESeq2:
 - **Input**: `data/processed/ukbb_processed.tsv`.
 - **Execution**: Run DESeq2 on the UKBB cohort.
 - **Output**: `data/processed/results/diff_abundance_ukbb_deseq2.tsv` containing taxa, method, q-value, effect_size, direction (filtered for q < 0.05).
 - **Depends on**: T028b1.
- [ ] T028b4 [P] [US3] **UKBB**: Calculate Metrics:
 - **Input**: `data/processed/ukbb_processed.tsv`.
 - **Metric**: Calculate and report absolute median fiber intake (g/day) for high/low groups in UKBB.
 - **Output**: `data/processed/results/ukbb_fiber_metrics.tsv`.
 - **Depends on**: T028b1.

- [ ] T029 [US3] Implement replication logic in `src/analysis/validation_cross_cohort.py`:
 - **Input**: `data/processed/results/association_results.tsv` (from T021) for both cohorts, and `diff_abundance_*.tsv` files (from T028a2, T028a3, T028b2, T028b3).
 - **Primary Logic**: Compare **MaAsLin2 beta-coefficients** (continuous model) for significant taxa between AGP and UKBB. Flag consistent directionality (same sign of effect size).
 - **Secondary Logic**: Compare ANCOM-II/DESeq2 results for significant taxa between AGP and UKBB. Flag consistent directionality.
 - **Output**: `data/processed/results/replication_status.tsv`
 - **Schema**: `taxon`, `method` (MaAsLin2/ANCOM/DESeq2), `agp_q_value`, `ukbb_q_value`, `agp_effect_size`, `ukbb_effect_size`, `replication_status` (values: 'replicated', 'non-replicable', 'cohort-specific'). **Must include 'diff_abundance_replicated' column for ANCOM/DESeq2 results.**
 - **Depends on**: T021, T028a2, T028a3, T028b2, T028b3.

- [ ] T033 [US3] Generate Final Summary Table:
 - **Input**: `data/processed/results/association_results.tsv` (T021), `diff_abundance_agp_ancom.tsv` (T028a2), `diff_abundance_agp_deseq2.tsv` (T028a3), `diff_abundance_ukbb_ancom.tsv` (T028b2), `diff_abundance_ukbb_deseq2.tsv` (T028b3), `replication_status.tsv` (T029), `agp_fiber_metrics.tsv` (T028a4), `ukbb_fiber_metrics.tsv` (T028b4), `data/processed/results/power_analysis_report.tsv` (T006b_run).
 - **Action**: Aggregate all results into a single comprehensive table.
 - **Output**: `data/processed/results/final_summary.tsv` containing:
   - Taxon, method, q-value, effect_size (beta), **Standard Error for Spearman ρ**, direction
   - **Replication status** (from T029)
   - **Median fiber intake for high/low groups** (from T028a4/T028b4) - **Mandatory for FR-009**
   - Confidence intervals (calculated as beta ± 1.96 * SE)
   - Statistical power and margin of error (from T006b_run).
 - **Depends on**: T021, T028a2, T028a3, T028b2, T028b3, T029, T028a4, T028b4, T006b_run.
- [ ] T031 [US3] Integrate power analysis results (from T006b/T006b_validate) into final report to distinguish true null effects from underpowered results. **Depends on**: T006b_run, T033.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `docs/` (README, quickstart)
- [ ] T033 Code cleanup and refactoring (remove unused imports, optimize memory usage)
- [ ] T034 Performance optimization to ensure ≤6h runtime on CPU-only runner (sample datasets if necessary)
- [ ] T035 [P] Additional unit tests in `tests/unit/` for edge cases (zero-inflation, missing covariates)
- [ ] T036 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T037 Verify all artifacts (CSV/TSV) are deterministic and reproducible (check random seeds)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires harmonized data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires results from US1 and US2 for validation

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
Task: "Contract test for data schema validation in tests/contract/test_schemas.py"
Task: "Integration test for ingestion pipeline in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement src/ingestion/agp_loader.py"
Task: "Implement src/ingestion/ukbb_loader.py"
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
- **CRITICAL**: All data downloads must use real, reachable URLs (Qiita, UKBB). No synthetic/fake data for input.
- **CRITICAL**: All statistical tests must run on CPU-only runners (no GPU, no low-bit quantization requiring CUDA).
- **CRITICAL**: Tasks must respect data flow: ingestion (US1) → transformation/analysis (US2) → validation (US3).
- **STRATEGY**: Primary analysis uses MaAsLin (continuous model). ANCOM-II/DESeq are executed on filtered/downsampled cohorts (AGP/UKBB) as robustness checks. Replication logic (T029) prioritizes MaAsLin2 beta-coefficient comparison but MUST also validate ANCOM-II/DESeq2 results.
- **FAIL LOUDLY**: If a data loader fails to fetch real data, it MUST raise an exception. Do not fall back to synthetic data.
- **COMPOSITIONAL CONSTRAINTS**: Python fallbacks for MaAsLin2 MUST fail loudly if R is unavailable; no ALR/ILR or OLS fallbacks allowed.
- **POWER ANALYSIS**: T006 (Implementation) must be completed before T006b_run (Execution).
- **TIME BUDGET**: ANCOM-II/DESeq2 tasks (T028a1/T028b1) MUST project runtime and downsample if > 5h to guarantee SC-004 (≤6h) compliance.