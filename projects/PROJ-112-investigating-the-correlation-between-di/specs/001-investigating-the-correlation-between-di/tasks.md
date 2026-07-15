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
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` containing pinned versions:
 - `pandas==2.0.3`, `scikit-learn==1.3.0`, `scipy==1.11.1`, `numpy==1.24.3`, `requests==2.31.0`, `pyyaml==6.0.1`, `joblib==1.3.1`, `miceforest==5.3.3`, `rpy2==3.5.11`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Setup `pytest` configuration and test directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T005 Implement `src/utils/logger.py` for standardized logging
- [ ] T006 Implement `src/utils/power_analysis.py` for calculating statistical power and margin of error (CPU-tractable)
- [ ] T006b Execute Power Analysis: Run `src/utils/power_analysis.py` on the harmonized dataset (once available) to generate `data/processed/results/power_analysis_report.tsv` containing calculated power and margin of error. **Depends on**: T014 (data availability). <!-- FAILED: unspecified -->
- [ ] T007 Create `src/preprocessing/id_generator.py` to generate SHA256 sample IDs (cohort + original_id)
- [~] T008 Setup data directory structure (`data/raw/`, `data/processed/`, `data/processed/results/`)
- [ ] T009 [P] Implement `src/preprocessing/covariate_handler.py` for MICE imputation (using `miceforest`) and missing data exclusion logic (>20% missing); **Configure complete logging**: Setup `src/utils/logger.py` with handlers for all analysis steps, including specific formatters for MaAsLin2 execution status, convergence warnings, and R-package output capture.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and harmonize American Gut Project (AGP) and UK Biobank (UKBB) data into a unified dataset.

**Independent Test**: Verify that the pipeline successfully downloads both datasets, filters samples correctly (≥5,000 reads, 0–200 g/day fiber), and outputs a unified CSV/TSV file with consistent column names and units.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_schemas.py`
- [~] T011 [P] [US1] Integration test for ingestion pipeline in `tests/integration/test_pipeline.py` <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/ingestion/agp_loader.py` to download AGP data from Qiita (verify URL/ID first)
- [ ] T013 [P] [US1] Implement `src/ingestion/ukbb_loader.py` to download UKBB data from canonical sources (verify URL/ID first)
- [ ] T014 [US1] Implement `src/ingestion/harmonizer.py` to:
 - Convert all fiber units to g/day
 - Filter samples with <5,000 reads
 - Filter samples with fiber intake <0 or >200 g/day
 - Exclude samples with missing fiber data
 - Merge into `data/processed/merged_harmonized.tsv`
- [ ] T015 [US1] Add validation logic to ensure no PII leaks and checksums are recorded in `state/`
- [ ] T016 [US1] Add logging for ingestion steps (download status, filter counts, harmonization results)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compositional Transformation and Correlation Analysis (Priority: P2)

**Goal**: Apply CLR transformation and compute fiber-taxa associations using MaAsLin2 with FDR correction.

**Independent Test**: Run correlation analysis on a small synthetic dataset with known associations and covariates, verifying output matches expected coefficients and corrected p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for MaAsLin2 output schema in `tests/contract/test_maaslin2_schema.py`
- [ ] T019 [P] [US2] Integration test for CLR transformation in `tests/integration/test_clr.py`

### Implementation for User Story 2

- [ ] T023 [US2] Integrate with User Story 1 components: Ensure `data/processed/merged_harmonized.tsv` is available and validated as input for downstream tasks. **Depends on**: T014.
- [ ] T020 [P] [US2] Implement `src/preprocessing/clr_transform.py` to:
 - Add a pseudocount for zero-inflated taxa
 - Apply centered log-ratio (CLR) transformation
 - Output to `data/processed/clr_transformed.tsv`
- [ ] T020b [P] [US2] Generate Pseudocount Validation Report: Run a diagnostic test to verify the chosen pseudocount strategy satisfies Constitution Principle VI (e.g., check impact on zero-inflated taxa distribution) and output results to `data/processed/results/pseudocount_validation.txt`.
- [ ] T021 [US2] Implement `src/analysis/correlation_maaslin2.py` to:
 - Invoke MaAsLin2 (via `rpy2` or `subprocess`) on CLR data
 - Adjust for covariates (age, BMI, antibiotic use)
 - Output raw p-values, effect sizes (beta), and standard errors
- [ ] T021b [US2] Implement Spearman ρ calculation in `src/analysis/correlation_maaslin2.py`:
 - Compute Spearman correlation coefficients between fiber intake and CLR-transformed taxa abundances.
 - **Calculate Standard Error (SE)** for the Spearman coefficient (e.g., via Fisher's z-transformation).
 - Output `data/processed/results/spearman_correlations.tsv` containing: taxon, spearman_rho, standard_error.
- [ ] T022 [US2] Implement FDR correction (Benjamini-Hochberg) in `src/analysis/correlation_maaslin2.py`:
 - Calculate q-values
 - Filter and save results to `data/processed/results/association_results.tsv`
- [ ] T024 [US2] Integrate with User Story 1 components: Load harmonized data from `data/processed/merged_harmonized.tsv` as input for transformation and analysis.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Differential Abundance and Cross-Cohort Validation (Priority: P3)

**Goal**: Perform differential abundance testing (ANCOM-II/DESeq2 as robustness checks), evaluate replication via continuous beta-coefficients, and report summary statistics.

**Independent Test**: Run differential abundance pipeline on both datasets independently, verify output format, and confirm replication status is accurately flagged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for differential abundance output in `tests/contract/test_diff_abundance_schema.py`
- [ ] T027 [P] [US3] Integration test for cross-cohort validation in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `src/analysis/validation_cross_cohort.py` robustness checks:
 - Define high-fiber (top quartile) and low-fiber (bottom quartile) groups per cohort based on the harmonized dataset.
 - **Execute ANCOM-II and DESeq2**: Run on the full harmonized dataset. **If** RAM projection exceeds 7GB, automatically perform a random stratified downsampling (by cohort) *before* running the analysis to ensure feasibility, ensuring the sample is representative of all taxa.
 - Output `data/processed/results/diff_abundance_agp.tsv` and `data/processed/results/diff_abundance_ukbb.tsv` containing taxa, method, q-value, effect_size, direction (filtered for q < 0.05).
 - **Calculate Absolute Median Fiber Intake**: Compute and report the absolute median fiber intake (g/day) for the high-fiber and low-fiber groups in each cohort based on the dataset used for analysis.
- [ ] T029 [US3] Implement replication logic in `src/analysis/validation_cross_cohort.py`:
 - **Compare ANCOM-II/DESeq2 Results**: Evaluate replication status by comparing significant taxa (q < 0.05) from ANCOM-II and DESeq2 between the AGP and UKBB cohorts.
 - Flag consistent directionality (same sign of effect size) for taxa significant in both cohorts.
 - Mark non-replicable taxa as 'non-replicable' based on disagreement in ANCOM-II/DESeq2 results.
 - Calculate and report cross-cohort replication rate based on ANCOM-II/DESeq2 findings.
 - (Secondary) Compare continuous beta-coefficients from MaAsLin2 as an additional robustness check.
- [ ] T030 [US3] Generate final summary table in `data/processed/results/final_summary.tsv` containing:
 - Taxon, method, q-value, effect_size (beta), **Standard Error for Spearman ρ (if included)**, direction
 - **Replication status** (based on ANCOM-II/DESeq2 and MaAsLin2)
 - Median fiber intake for high/low groups
 - Confidence intervals (calculated as beta ± 1.96 * SE)
- [ ] T031 [US3] Integrate power analysis results (from T006/T006b) into final report to distinguish true null effects from underpowered results.
- [ ] T031b [US3] **Explicitly format and output** power analysis metrics:
 - Extract calculated statistical power and margin of error from `data/processed/results/power_analysis_report.tsv`.
 - Append these metrics to the final summary table or a dedicated `power_analysis_report.tsv`.

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
- **CRITICAL**: All statistical tests must run on CPU-only runners (no GPU, no 8-bit/4-bit quantization requiring CUDA).
- **CRITICAL**: Tasks must respect data flow: ingestion (US1) → transformation/analysis (US2) → validation (US3).
- **STRATEGY**: Primary analysis uses MaAsLin2 (continuous model). ANCOM-II/DESeq2 are executed on the full dataset (or a deterministic stratified sample if RAM constrained) as robustness checks to satisfy Spec requirements.