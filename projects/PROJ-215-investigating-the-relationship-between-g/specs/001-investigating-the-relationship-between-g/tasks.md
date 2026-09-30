# Tasks: Investigating the Relationship Between Gut Microbiome Composition and Mental Health in Public Datasets

**Input**: Design documents from `/specs/001-gut-microbiome-mental-health/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

## Phase 0: Data Feasibility Check (Blocking Gate)

**Purpose**: Verify data availability before any processing begins.

- [X] T000a [P] [US1] Implement `code/data_feasibility.py`: Check for a single verified public dataset containing both 16S rRNA data and PHQ-9/GAD-7 scores for the same sample IDs. **Logic**: Query verified sources (Qiita Study 10317, HuggingFace).
- [X] T000b [P] [US1] Implement `code/data_feasibility.py`: If no linked dataset is found, **HALT** and generate a "Data Gap Report" (`results/data_gap_report.md`). Mark SC-001, SC-002, SC-003, SC-005 as "Not Applicable".
- [X] T000c [P] [US1] If a linked dataset is found, proceed to Phase 1. Log confirmation.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create data directories: `mkdir -p data/raw/ data/processed/`
- [X] T001b [P] Create code directories: `mkdir -p code/ code/models/ code/utils/`
- [X] T001c [P] Create test directories: `mkdir -p tests/unit/ tests/integration/ tests/contract/`
- [X] T002 Create `requirements.txt` with pinned major/minor versions for core dependencies (pandas, scikit-learn, scipy, numpy, biom-format, skbio, matplotlib, seaborn, requests, pytest, statsmodels) and a script to generate a `requirements.lock` file for reproducibility.
- [X] T002a [P] Implement `code/seeds.py`: Generate a `seeds.yaml` file at runtime recording the specific random seeds used for all stochastic operations (sampling, shuffling, model initialization) to satisfy Constitution Principle I reproducibility. Output to `state/seeds.yaml`.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Note on TDD Workflow**: Tasks T010 and T011 are "Write" tasks. They define the test contracts (TDD) *before* the implementation code exists. They are placed here to establish the interface. The "Execute" tasks (T010x, T011x) are placed in Phase 3 because they require the implementation (T013, T014) to be present to run. This is a valid TDD flow: define the contract first, then implement.

Examples of foundational tasks (adjust based on your project):

- [X] T004 Implement `code/config.py` with paths, random seeds, and thresholds (e.g., 0.1% prevalence, 20% rarefaction loss threshold, median sequencing depth calculation logic)
- [X] T005 [Write] [Foundational] Setup logging infrastructure in `code/utils/logging.py` to write logs to `logs/pipeline.log` with rotation, using paths defined in T004.
- [X] T006 Create base data models/entities in `code/models.py` with specific schemas: `MicrobiomeSample` (sample_id, counts, metadata), `MentalHealthRecord` (phq9, gad7, age, bmi), `AssociationResult` (taxon, coef, pval, qval, direction)
- [X] T007 [P] Setup environment configuration management (`.env` loading if needed)
- [X] T010a [Write] [US1] Write unit test `test_rarefaction_fallback_when_loss_gt_20_percent` in `tests/unit/test_preprocessing.py` asserting that VST is triggered when estimated loss > 20%. (Write-first, execute after T014)
- [X] T010b [Write] [US1] Write unit test `test_median_depth_calculation` in `tests/unit/test_preprocessing.py` asserting correct median depth calculation logic. (Write-first, execute after T014)
- [X] T011a [Write] [US1] Write unit test `test_missing_phq9_filter` in `tests/unit/test_data_ingestion.py` asserting samples with missing PHQ-9 are removed and log rate is correct. (Write-first, execute after T013)
- [X] T011b [Write] [US1] Write unit test `test_rate_limit_retry` in `tests/unit/test_data_ingestion.py` asserting exponential backoff retry logic on 429 errors. (Write-first, execute after T012)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, merge, and preprocess AGP data to create a clean, analysis-ready dataset with valid samples and no missing key values.

**Independent Test**: The pipeline can be tested by running the data ingestion script and verifying that the output CSV contains ≥ 100 valid rows where both microbiome diversity metrics and mental health scores are present, with no missing values in the key predictor/outcome columns.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data_ingestion.py`: Download AGP data (Study ID) via Qiita API or verified HuggingFace mirror (handle rate-limiting with exponential backoff). **Feasibility Check**: Verify the dataset contains both 16S rRNA and PHQ-9/GAD-7 metadata for overlapping samples. Merge OTU table and metadata on `sample_id`. If no linked data is found, log "Data Gap" and halt analysis (per Plan Phase 0).
- [X] T012b [US1] Implement `code/data_ingestion.py`: Compute SHA-256 checksums for all downloaded raw data files and record them in `data/raw/checksums.txt`.
- [X] T013 [US1] Implement `code/data_ingestion.py`: Filter samples with missing PHQ-9/GAD-7 scores and log exclusion rate.
- [X] T014 [US1] Implement `code/preprocessing.py`: **Step 1**: Calculate median sequencing depth (median of non-zero column sums). **Step 2**: Estimate sample loss if rarefying to this depth. **Step 3**: If median < 1000 or estimated loss >20%, apply Variance-Stabilizing Transformation (VST) and log fallback; otherwise, apply rarefaction.
- [X] T015 [US1] Implement `code/preprocessing.py`: Filter taxa with <0.1% prevalence on the preprocessed table.
- [X] T016 [US1] Implement `code/preprocessing.py`: Calculate Alpha diversity metrics (Shannon, Simpson) on the **preprocessed** table (after rarefaction/VST and filtering). Output to `data/processed/alpha_metrics.csv`.
- [X] T016b [US1] Implement `code/preprocessing.py`: Generate **all required beta diversity metrics** in a single execution flow: 1) Bray-Curtis distance matrix, 2) Weighted UniFrac distance matrix, 3) Unweighted UniFrac distance matrix. Use `skbio` on the preprocessed table. Output to `data/processed/bray_curtis.npz`, `data/processed/weighted_unifrac.npz`, and `data/processed/unweighted_unifrac.npz` respectively. Verify all files exist and have non-zero shape.
- [X] T010x [Execute] [US1] Execute unit tests for rarefaction fallback logic in `tests/unit/test_preprocessing.py` (after T014 completion).
- [X] T011x [Execute] [US1] Execute unit tests for missing value filtering in `tests/unit/test_data_ingestion.py` (after T013 completion).
- [X] T017 [US1] Output `data/processed/cleaned_dataset.csv` (with alpha metrics) and verify ≥ 80% retention AND ≥ 100 valid rows with no missing key columns. **Calculation**: Compute `retention_rate = (valid_rows / initial_download_rows) * 100`. Write `retention_rate` and `initial_rows` to `data/processed/metrics.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Association Analysis (Priority: P2)

**Goal**: Calculate diversity metrics, perform partial Spearman correlation analyses, and execute PERMANOVA tests with covariate adjustment to determine significant associations.

**Independent Test**: The analysis module can be tested by running it on the preprocessed dataset and verifying that it outputs a results table containing partial correlation coefficients, p-values, and effect sizes for the specified mental health variables.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/analysis.py`: Calculate **partial Spearman rank correlation (FR-004)** between alpha diversity (Shannon/Simpson) and PHQ-9/GAD-7 scores. **Implementation**: Read `data/processed/alpha_metrics.csv` (from T016) and metadata. Regress diversity and scores against covariates (age, BMI) to obtain residuals, then calculate Spearman correlation on residuals using `scipy.stats.spearmanr`. Save unadjusted p-values to `data/interim/unadjusted_alpha_pvals.csv`.
- [X] T020a [US2] Implement `code/analysis.py`: Perform **MaAsLin2-style linear modeling** for taxa abundance vs PHQ-9/GAD-7. **Implementation**: Read `data/processed/cleaned_dataset.csv` and metadata. Use `skbio` or `statsmodels` to fit linear models with covariate adjustment (age, BMI). **Constraint**: If covariates are missing, fall back to partial Spearman. Save unadjusted p-values to `data/interim/unadjusted_taxa_pvals.csv`.
- [X] T021 [US2] Implement `code/analysis.py`: Perform PERMANOVA on beta diversity (Bray-Curtis) between high-depression (PHQ-9 ≥ 10, clinically defined per spec) and low-depression groups, AND high-anxiety (GAD-7 ≥ 10) and low-anxiety groups. **Implementation**: Read `data/processed/bray_curtis.npz` (from T016b). **Algorithm**: Residualize rows of the design matrix against covariates (age, BMI), then run `skbio.stats.distance.permanova` on the residualized matrix. Output results to `data/interim/permanova_results.csv`.
- [X] T021b [US2] Implement `code/analysis.py`: Perform PERMANOVA on **Weighted and Unweighted UniFrac** distance matrices (from T016b) between high/low depression and anxiety groups. **Implementation**: Use `skbio.stats.distance.permanova` on the residualized matrices. Output results to `data/interim/permanova_unifrac_results.csv`.
- [X] T022a [US2] Implement `code/analysis.py`: Apply Benjamini-Hochberg correction to **all p-values** (alpha diversity, taxa, and PERMANOVA) to report adjusted p-values (q-values). **Requirement**: Ensure correction covers alpha diversity correlations (FR-004) and PERMANOVA tests (US-2) in addition to taxa. Save to `data/interim/adjusted_pvals.csv`.
- [X] T022b [US2] Implement `code/analysis.py`: Output PERMANOVA p-values from T021 and T021b to `data/processed/permanova_final.csv` **with** Benjamini-Hochberg correction applied (as per FR-005).
- [X] T023 [US2] **SC-005 Check**: Calculate `|p_adjusted - p_unadjusted|` for **each taxon**. **Input**: Read `data/interim/unadjusted_taxa_pvals.csv` (from T020a) AND `data/interim/adjusted_pvals.csv` (from T022a). Identify the maximum delta. Output a JSON file `results/covariate_delta.json` with keys: `max_delta` (float), `threshold_met` (boolean, true if max_delta > 0.01).
- [X] T024 [US2] **SC-002 Check**: If T022a yields no significant taxa (q < 0.05), perform Kolmogorov-Smirnov test on the distribution of unadjusted p-values (from `data/interim/unadjusted_taxa_pvals.csv` produced by T020a) using `scipy.stats.kstest` (vs uniform distribution). **Success Criteria**: If p-value < 0.05, mark SC-002 as PASS. Output `data/processed/ks_test_results.json` with keys: `statistic`, `p_value`, `result` (pass/fail).
- [X] T025 [US2] Output `data/processed/association_results.csv` with correlation coefficients, unadjusted p-values, adjusted p-values (q-values), and effect directions for taxa.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-ready visualizations (PCoA, heatmaps) and a summary report highlighting significant associations.

**Independent Test**: The reporting module can be tested by executing the visualization script and verifying that output image files (PNG/SVG) and a summary text file are generated, containing the expected plots and key statistical findings.

### Implementation for User Story 3

- [X] T026 [Write] [US3] Write unit test cases for plot generation (mock data) in `tests/unit/test_visualization.py`.
- [X] T027 [US3] Implement `code/visualization.py`: Generate PCoA plot colored by mental health status (High vs. Low PHQ-9 and GAD-7) with group centroids. Output to `results/plots/pcoa_plot.png`.
- [X] T028 [US3] Implement `code/visualization.py`: Generate heatmap of top associated taxa with color intensity proportional to correlation coefficient. Output to `results/plots/taxa_heatmap.png`.
- [X] T029 [US3] Implement `code/report.py`: Generate summary report listing all significant associations (q < 0.05) with direction and magnitude. Include results from T023 (covariate check) and T024 (KS test) in the report. Output to `results/summary_report.txt`.
- [X] T030 [US3] Verify `results/plots/pcoa_plot.png`, `results/plots/taxa_heatmap.png`, and `results/summary_report.txt` exist and contain expected content.
- [X] T030b [US3] **Constitution Gate**: Run Reference-Validator Agent on external cohort URLs (e.g., UK Biobank, MetaHIT) to verify accessibility and accuracy before T031. Output verification status to `results/validation_urls_verified.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Validation on Independent Cohort (Priority: P3)

**Goal**: Validate effect direction of significant taxa on an independent cohort if accessible.

**Independent Test**: The validation module can be tested by running it on a secondary dataset and verifying that it outputs a comparison table showing effect direction matches for significant taxa.

### Implementation for User Story 4

- [X] T031 [US4] Implement `code/validation.py`: Check for accessible independent cohort. **Logic**: First, verify existence of the dataset via `datasets.get_dataset_config_names` or API check. If the dataset ID is missing, inaccessible (404/403), or yields no data, log "Validation Skipped: No independent cohort available" and proceed to T032b. If accessible, attempt `datasets.load_dataset` with streaming for known IDs (e.g., `ukbiobank-microbiome`, `metahit`) or local files matching `data/external/*.csv`. **Dependency**: Must run after T025 (results).
- [X] T032a [US4] **Conditional (Accessible)**: If accessible: Implement `code/validation.py`: Download secondary data, calculate correlations for top significant taxa (from T025), compute '% match' as (matching_directions / total_significant_taxa) scaled to a percentage. Compare against SC-003 threshold (≥ 80%). Report pass/fail status and details in `results/validation_report.txt`.
- [X] T032b [US4] **Conditional (Not Accessible)**: If not accessible: Implement `code/validation.py`: Add conditional block to log "Validation Skipped: No independent cohort available" and explicitly write this status to `results/validation_report.txt` to satisfy Single Source of Truth. Mark SC-003 as "Not Applicable".
- [X] T034 [US4] Implement `code/validation.py`: Format and save validation results to `data/processed/validation_results.csv` (if applicable).

---

## Phase 7: Final Output & State Management

**Purpose**: Finalize artifacts and update project state

- [X] T035 Implement `code/state_manager.py`: Hash artifacts and update `state/projects/PROJ-215-.../state.yaml` with `updated_at` and artifact hashes.
- [X] T036 Implement `code/report.py`: Aggregate T023 and T032 results and generate final project report summarizing all findings, data gaps, and success criteria status.
- [X] T037a [P] Implement `code/timing.py`: Wrap the main pipeline execution with high-precision timers (e.g., `time.perf_counter()`) at the entry and exit points to capture the total runtime independent of log parsing. Output `total_runtime_seconds` to `results/timing.json`.
- [X] T037 Implement `code/timing.py`: Parse `results/timing.json` (from T037a) to calculate total pipeline runtime. Verify against threshold ≤ 4 hours. Log `total_runtime_hours` to `results/metrics.json`. **Note**: Use T037a's explicit output as the primary source for SC-004.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (cleaned dataset)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (results)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (significant taxa)

### Within Each User Story

- Tests (T010, T011) are written first (TDD) but executed after implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement code/config.py"
Task: "Implement code/models.py"

# Launch all write-tests for User Story 1 together (after models):
Task: "Write unit test for rarefaction fallback logic in tests/unit/test_preprocessing.py"
Task: "Write unit test for missing value filtering in tests/unit/test_data_ingestion.py"
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
- [Write] tasks = Test writing (parallel safe)
- [Execute] tasks = Test execution (depends on implementation)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence