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

- [X] T000a [P] [US1] Implement `code/data_feasibility.py`: Check for a single verified public dataset containing both 16S rRNA data and PHQ-9/GAD-7 scores for the same sample IDs. **Logic**: Query verified sources (Qiita Study, HuggingFace).
- [X] T000b [P] [US1] Implement `code/data_feasibility.py`: If no linked dataset is found, **HALT** and generate a "Data Gap Report" at `results/data_gap_report.md`. **Schema**: JSON/Markdown containing `status: "DATA_GAP"`, `reason: "AGP 10317 missing/invalid"`, and `SC-001`, `SC-002`, `SC-003`, `SC-005` marked as "Not Applicable".
- [X] T000c [P] [US1] If a linked dataset is found, proceed to Phase 1. Log confirmation.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create data directories: `mkdir -p data/raw/ data/processed/`
- [X] T001b [P] Create code directories: `mkdir -p code/ code/models/ code/utils/`
- [X] T001c [P] Create test directories: `mkdir -p tests/unit/ tests/integration/ tests/contract/`
- [X] T002a [P] Create `requirements.txt` with pinned major/minor versions for core dependencies (pandas, scikit-learn, scipy, numpy, biom-format, skbio, matplotlib, seaborn, requests, pytest, statsmodels).
- [X] T002b [P] Implement `code/scripts/generate_lock.py`: Generate `requirements.lock` from `requirements.txt`. **Constraint**: `requirements.lock` is the Single Source of Truth for execution. `requirements.txt` defines dependencies. **Output**: `requirements.lock`.
- [X] T002c [P] Implement `code/seeds.py`: Generate a `seeds.yaml` file at runtime. **Schema**: Must include keys `random_seed`, `numpy_seed`, `torch_seed` (if applicable). Output to `state/seeds.yaml`.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Note on TDD Workflow**: Tasks T010 and T011 are "Write" tasks. They define the test contracts (TDD) *before* the implementation code exists. They are placed here to establish the interface. The "Execute" tasks (T010x, T011x) are placed in Phase 3 because they require the implementation (T013, T014) to be present to run. This is a valid TDD flow: define the contract first, then implement.

Examples of foundational tasks (adjust based on your project):

- [X] T004 Implement `code/config.py` with paths, random seeds, and thresholds (e.g., 0.1% prevalence, 20% rarefaction loss threshold, median sequencing depth calculation logic)
- [X] T005 [P] [Foundational] Setup logging infrastructure in `code/utils/logging.py` to write logs to `logs/pipeline.log` with rotation, using paths defined in T004.
- [X] T006 Create base data models/entities in `code/models.py` with specific schemas: `MicrobiomeSample` (sample_id, counts, metadata), `MentalHealthRecord` (phq9, gad7, age, bmi), `AssociationResult` (taxon, coef, pval, qval, direction)
- [X] T007 [P] Setup environment configuration management (`.env` loading if needed)
- [X] T008 [P] [US1] [FR-001] [SC-004] Implement `code/data_ingestion.py`: Enforce **STRICT STREAMING** for datasets exceeding 1GB. Use `datasets.load_dataset(..., streaming=True)` to process data in chunks. **Constraint**: The script MUST NOT attempt to load the full dataset into RAM. If a full load is attempted, raise a `MemoryError` immediately. **Implementation**: Provide a `streaming_merge_otu_metadata` function that iterates chunks and merges on `sample_id` without full materialization.
- [X] T009 [US1] [FR-001] Implement `code/data_ingestion.py`: **Hard Fail Logic**. Remove any `try/except` blocks that fall back to `generate_synthetic_*()` or `mock_*()` functions. Wrap the real data fetch in a try/except block. **If the real data fetch fails** (network error, 404, invalid URL), **invoke the Data Gap Report generation logic (T000b)** to generate `results/data_gap_report.md` and terminate gracefully. **Do NOT crash**. A placeholder or "toy" dataset is forbidden and must raise an exception if assigned. **Dependency**: T008 (Streaming logic must be implemented first to handle streaming-specific errors).
- [X] T010 [Write] [US1] Write unit tests for US1 in `tests/unit/`. **Scope**: `test_rarefaction_fallback_when_loss_gt_20_percent`, `test_median_depth_calculation`, `test_missing_phq9_filter`, `test_rate_limit_retry`. **Mock Data**: Define mock OTU table structure (dict of {sample_id: {taxon: count}}) and expected assertion values (e.g., `assert median == 5000`). (Write-first, execute after implementation in Phase 3).
- [X] T011 [Write] [US1] Write unit tests for streaming merge logic in `tests/unit/test_data_ingestion.py`. **Scope**: `test_streaming_merge_chunk_size`, `test_streaming_merge_memory_limit`. **Mock Data**: Define mock chunk generator yielding 1KB dicts. (Write-first, execute after implementation in Phase 3).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, merge, and preprocess AGP data to create a clean, analysis-ready dataset with valid samples and no missing key values.
**Trigger Logic**: If rarefaction results in >20% sample loss, apply Variance-Stabilizing Transformation (VST) instead.

**Independent Test**: The pipeline can be tested by running the data ingestion script and verifying that the output CSV contains ≥ 100 valid rows where both microbiome diversity metrics and mental health scores are present, with no missing values in the key predictor/outcome columns.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data_ingestion.py`: Download AGP data (Study ID) via Qiita API or verified HuggingFace mirror (handle rate-limiting with exponential backoff). **Feasibility Check**: Verify the dataset contains both 16S rRNA and PHQ-9/GAD-7 metadata for overlapping samples. Merge OTU table and metadata on `sample_id`. **Dependency**: Must use streaming logic from T008 if dataset > 1GB. If no linked data is found, log "Data Gap" and halt analysis (per Plan Phase 0).
- [X] T012b [US1] Implement `code/data_ingestion.py`: Compute SHA-256 checksums for all downloaded raw data files and record them in `data/raw/checksums.txt`. **Constraint**: Also update `state/projects/PROJ-215-.../state.yaml` with these checksums in the `artifact_hashes` map to satisfy Constitution Principle III (Data Hygiene). **Output**: `data/raw/checksums.txt` and updated `state.yaml`.
- [X] T013 [US1] Implement `code/data_ingestion.py`: Filter samples with missing PHQ-9/GAD-7 scores and log exclusion rate. **Input**: Merged raw data. **Output**: Filtered dataset (intermediate).
- [X] T014a [US1] Implement `code/preprocessing.py`: **Step 1**: Calculate median sequencing depth. **Input**: `data/raw/otu_table.biom` (filtered by T013). **Logic**: Calculate the **sum of counts per sample (row-wise, axis=1)**, filter non-zero, then take the median. **Output**: `data/interior/median_depth.json`.
- [X] T014b [US1] Implement `code/preprocessing.py`: **Step 2**: Estimate sample loss if rarefying to the median depth from T014a. **Input**: `data/interior/median_depth.json`. **Algorithm**: Simulate rarefaction to the median depth on the input OTU table, count samples with zero depth, and calculate loss rate = (zero_depth_samples / total_samples). **Output**: `data/interior/estimated_loss.json`.
- [X] T014c [US1] Implement `code/preprocessing.py`: **Step 3**: **If estimated loss > 20%** (strictly per FR-002), apply Variance-Stabilizing Transformation (VST) and log fallback; otherwise, apply rarefaction. **Dependency**: T014b. **Output**: Preprocessed OTU table to `data/processed/preprocessed_otu_table.biom`.
- [X] T015 [US1] Implement `code/preprocessing.py`: Filter taxa with <0.1% prevalence on the **preprocessed** table (output of T014c). **Output**: `data/processed/filtered_otu_table.biom`.
- [X] T016 [US1] Implement `code/preprocessing.py`: Calculate Alpha diversity metrics (Shannon, Simpson) on the **filtered** table (output of T015). **Dependency**: T014c, T015. **Output**: `data/processed/alpha_metrics.csv`.
- [X] T016b [US1] Implement `code/preprocessing.py`: Generate **beta diversity metrics** in a single execution flow: 1) Bray-Curtis distance matrix (always), 2) Weighted UniFrac (if phylogenetic tree present), 3) Unweighted UniFrac (if phylogenetic tree present). **Input**: `data/processed/filtered_otu_table.biom` and optional `data/raw/tree.nwk`. **Algorithm**: Use `skbio.diversity.beta.diversity_matrix` with metric=bray_curtis. **Conditional**: If tree missing, skip UniFrac, log warning "UniFrac skipped: No tree available", **create empty .npz files with a `skipped: true` flag** to prevent downstream crashes, and **mark SC-003 as Not Applicable**. Verify all **generated** files exist and have non-zero shape (or are empty with skipped flag). Output to `data/processed/bray_curtis.npz`, `data/processed/weighted_unifrac.npz` (if available), `data/processed/unweighted_unifrac.npz` (if available).
- [X] T016c [US1] Implement `code/preprocessing.py`: **Conditional Fallback**: If the phylogenetic tree is missing (detected in T016b), log a warning "UniFrac skipped: No tree available" and proceed to next tasks. **Dependency**: T016b.
- [X] T010x [Execute] [US1] Execute unit tests for rarefaction fallback logic in `tests/unit/test_preprocessing.py` (after T014 completion). **Dependency**: T010 (Write task).
- [X] T011x [Execute] [US1] Execute unit tests for missing value filtering in `tests/unit/test_data_ingestion.py` (after T013 completion). **Dependency**: T011 (Write task).
- [X] T017 [US1] Output `data/processed/cleaned_dataset.csv` (with alpha metrics) and verify ≥ 80% retention AND ≥ 100 valid rows with no missing key columns. **Dependency**: T013, T016. **Calculation**: Compute `retention_rate = (valid_rows / initial_download_rows) * 100`. Write `retention_rate` and `initial_rows` to `data/processed/metrics.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Association Analysis (Priority: P2)

**Goal**: Calculate diversity metrics, perform partial Spearman correlation analyses, and execute PERMANOVA tests with covariate adjustment to determine significant associations.

**Independent Test**: The analysis module can be tested by running it on the preprocessed dataset and verifying that it outputs a results table containing partial correlation coefficients, p-values, and effect sizes for the specified mental health variables.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/analysis.py`: Calculate **partial Spearman rank correlation (FR-004)** between alpha diversity (Shannon/Simpson) and PHQ-9/GAD-7 scores. **Implementation**: Read `data/processed/alpha_metrics.csv` (from T016) and metadata. **Algorithm**: Rank-transform diversity and scores, regress ranks against covariates (age, BMI) to obtain residuals, then calculate Spearman correlation on residuals using `scipy.stats.spearmanr`. Save unadjusted p-values to `data/interim/unadjusted_alpha_pvals.csv`.
- [X] T020a [US2] Implement `code/analysis.py`: Perform **Standard Spearman Correlation** for taxa abundance vs PHQ-9/GAD-7. **Input**: `data/processed/cleaned_dataset.csv`. **Logic**: Use **all columns except metadata columns** as taxa abundance. **Algorithm**: Rank-transform taxa counts and PHQ-9/GAD-7 scores, calculate Spearman correlation using `scipy.stats.spearmanr`. **Constraint**: Do NOT apply covariate residualization here (per FR-004, covariate adjustment is for diversity metrics, not taxa). **Note**: This is a **non-compliant baseline for comparison only** as FR-004 mandates partial correlation with covariates IF present. **Output**: Save results to `data/interim/unadjusted_taxa_pvals.csv` with columns `[taxon, rho, p_value]`.
- [X] T020b [US2] Implement `code/analysis.py`: Perform **Partial Spearman Correlation** for taxa abundance vs PHQ-9/GAD-7 **with Covariate Adjustment** (for comparison/SC-005). **Input**: `data/processed/cleaned_dataset.csv`. **Logic**: Same as T020a but apply rank-residualization against covariates (age, BMI) before correlation. **Output**: Save covariate-adjusted p-values to `data/interim/covariate_adjusted_pvals.csv`. **Note**: This is the primary method per FR-004.
- [X] T021a [US2] Implement `code/analysis.py`: **Generate Binary Grouping Variable**. **Input**: `data/processed/cleaned_dataset.csv`. **Logic**: Create a new column `depression_group` where `PHQ-9 >= 10` is "High" and `< 10` is "Low". Validate the distribution (non-empty groups). **Output**: `data/interim/grouping_variables.csv`.
- [X] T021 [US2] Implement `code/analysis.py`: Perform PERMANOVA on beta diversity (Bray-Curtis) between high-depression and low-depression groups, AND high-anxiety and low-anxiety groups. **Input**: `data/processed/bray_curtis.npz` (from T016b) and `data/interim/grouping_variables.csv` (from T021a). **Algorithm**: **Use sklearn.linear_model.LinearRegression to regress the distance matrix rows against covariates (age, BMI), extract residuals**, and pass residuals to `skbio.stats.distance.permanova`. Output results to `data/interim/permanova_results.csv`.
- [X] T021b [US2] Implement `code/analysis.py`: Perform PERMANOVA on **Weighted and Unweighted UniFrac** distance matrices (from T016b, if available) between high/low depression and anxiety groups. **Implementation**: **Conditional**: Check if `data/processed/weighted_unifrac.npz` and `data/processed/unweighted_unifrac.npz` exist. If missing (per T016c), log "Skip: UniFrac matrices not available" and mark SC-003 as "Not Applicable" for UniFrac. If present, use `skbio.stats.distance.permanova` on the residualized matrices. **Dependency**: T016b. Output results to `data/interim/permanova_unifrac_results.csv`.
- [X] T022a [US2] Implement `code/analysis.py`: Apply Benjamini-Hochberg correction to **all taxa and alpha diversity p-values** (vectors of hypotheses). **Constraint**: Explicitly **exclude** PERMANOVA p-values from this vector. Save to `data/interim/adjusted_pvals.csv` with columns: `feature`, `pval_raw`, `pval_adj`.
- [X] T022c [US2] Implement `code/analysis.py`: Output PERMANOVA p-values from T021 and T021b to `data/processed/permanova_final.csv` **without** Benjamini-Hochberg correction (as they are single global tests).
- [X] T023a [US2] **SC-005 Check (Covariate)**: Calculate `|p_covariate_adjusted - p_unadjusted|` for **each taxon**. **Input**: Read `data/interim/unadjusted_taxa_pvals.csv` (from T020a) AND `data/interim/covariate_adjusted_pvals.csv` (from T020b). Identify the maximum delta. Output a JSON file `results/covariate_delta.json` with keys: `max_delta` (float), `threshold_met` (boolean, true if max_delta > 0.01). **Dependency**: T020a, T020b.
- [X] T023b [US2] **SC-005 Check (BH)**: Calculate `|p_bh_adjusted - p_unadjusted|` for **each taxon**. **Input**: Read `data/interim/unadjusted_taxa_pvals.csv` and `data/interim/adjusted_pvals.csv`. Output `results/bh_delta.json`.
- [X] T024 [US2] **SC-002 Check**: If T022a yields no significant taxa (q < 0.05), perform Kolmogorov-Smirnov test on the distribution of unadjusted p-values (from `data/interim/unadjusted_taxa_pvals.csv` produced by T020a) using `scipy.stats.kstest` (vs uniform distribution). **Success Criteria**: If p-value < 0.05, mark SC-002 as PASS. Output `data/processed/ks_test_results.json` with keys: `statistic`, `p_value`, `result` (pass/fail).
- [X] T024b [US2] **SC-002 Reporting**: Read `data/processed/ks_test_results.json`. If `result` is "pass", update `results/summary_report.txt` and `state.yaml` to explicitly mark SC-002 as "PASS". If no KS test was performed (significant taxa found), mark SC-002 as "PASS (Significant taxa found)". **Dependency**: T024.
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
- [X] T029 [US3] Implement `code/report.py`: Generate summary report listing all significant associations (q < 0.05) with direction and magnitude. Include results from T023a (covariate check), T023b (BH check), and T024 (KS test) in the report. Output to `results/summary_report.txt`.
- [X] T030 [US3] Verify `results/plots/pcoa_plot.png`, `results/plots/taxa_heatmap.png`, and `results/summary_report.txt` exist and contain expected content.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Validation on Independent Cohort (Priority: P3)

**Goal**: Validate effect direction of significant taxa on an independent cohort if accessible.

**Independent Test**: The validation module can be tested by running it on a secondary dataset and verifying that it outputs a comparison table showing effect direction matches for significant taxa.

### Implementation for User Story 4

- [X] T030b [US3/US4] **Constitution Gate**: Run Reference-Validator Agent on external cohort URLs (e.g., UK Biobank, MetaHIT) to verify accessibility and accuracy. **Conditional**: If T031 resulted in a "SKIPPED" status (no cohort found), mark this task as "Not Applicable" and skip execution. Output verification status to `results/validation_urls_verified.json`.
- [X] T031 [US4] Implement `code/validation.py`: **Conditional Validation Logic**. **Step 1**: Check for accessible independent cohort. **Logic**: Search verified sources: 1) Qiita (Study ID 10317 or others), 2) HuggingFace Datasets (search for "gut microbiome mental health"), 3) UK Biobank (public API). **Accessibility Criteria**: HTTP 200 response, non-empty payload, valid metadata fields. **Constraint**: Verify Phase 0 feasibility gate passed before proceeding. **Step 2**: If accessible: Download secondary data, calculate correlations for top significant taxa (from T025), compute '% match' as (matching_directions / total_significant_taxa) scaled to a percentage. Compare against SC-003 threshold (≥ 80%). **Tie-breaking**: If correlation is exactly 0 or p-value > 0.05, count as "non-matching". Report pass/fail status and details in `results/validation_report.txt`. Output `data/processed/validation_results.csv` (if applicable). **Step 3**: If no accessible cohort found after exhaustive search: Log "Validation Skipped: No independent cohort available", write `results/validation_skip_report.md` with `status: "SKIPPED"`, `reason: "No accessible cohort"`, `SC-003: Not Applicable`, and **terminate this phase successfully**.
- [X] T034 [US4] Implement `code/validation.py`: Format and save validation results to `data/processed/validation_results.csv` (if applicable).

---

## Phase 7: Final Output & State Management

**Purpose**: Finalize artifacts and update project state

- [X] T035 Implement `code/state_manager.py`: Hash artifacts and update `state/projects/PROJ-215-.../state.yaml` with `updated_at` and artifact hashes.
- [X] T036 Implement `code/report.py`: Aggregate T023a, T023b, T032 results AND `results/validation_skip_report.md` (if present from T031) and generate final project report summarizing all findings, data gaps, and success criteria status.
- [X] T037a [P] Implement `code/timing.py`: Wrap the main pipeline execution with high-precision timers (e.g., `time.perf_counter()`) at the entry and exit points to capture the total runtime independent of log parsing. Output `total_runtime_seconds` to `results/timing.json`.
- [X] T037 Implement `code/timing.py`: Read `results/timing.json` (from T037a) to calculate total pipeline runtime. Verify against threshold ≤ 4 hours. Log `total_runtime_hours` to `results/metrics.json`. **Note**: Use T037a's explicit output as the primary source for SC-004.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Integrity (Phase 2)**: Tasks T008, T009, T010, T011 are **implemented in Phase 2** (Foundational) to ensure they are available before T012 (Data Ingestion) is executed in Phase 3.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (cleaned dataset)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (results)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (significant taxa)

### Within Each User Story

- Tests (T010) are written first (TDD) but executed after implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members
- Phase 2 tasks (T008-T011) are independent of specific user story logic and can run in parallel with Setup/Foundational.

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
- **Critical**: Phase 2 tasks (T008-T011) are mandatory to prevent "synthetic data fallback" violations and ensure streaming compliance.
- **Revised Ordering**: T014a (Preprocessing) now strictly follows T013 (Filtering) to ensure depth is calculated on valid samples. T020a/T020b clarified for statistical rigor. T031 generalized for cohort search. T030b moved to Phase 6.