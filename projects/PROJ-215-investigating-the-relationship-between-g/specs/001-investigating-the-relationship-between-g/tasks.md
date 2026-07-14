# Tasks: Investigating the Relationship Between Gut Microbiome Composition and Mental Health in Public Datasets

**Input**: Design documents from `/specs/001-gut-microbiome-mental-health/`
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

- [X] T001a [P] Create data directories: `mkdir -p data/raw/ data/processed/`
- [X] T001b [P] Create code directories: `mkdir -p code/ code/models/ code/utils/`
- [X] T001c [P] Create test directories: `mkdir -p tests/unit/ tests/integration/ tests/contract/`
- [X] T002 Create `requirements.txt` with pinned major/minor versions for core dependencies (pandas, scikit-learn, scipy, numpy, biom-format, skbio, matplotlib, seaborn, requests, pytest, statsmodels) and a script to generate a `requirements.lock` file for reproducibility.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Implement `code/config.py` with paths, random seeds, and thresholds (e.g., 0.1% prevalence, 20% rarefaction loss threshold, median sequencing depth calculation logic)
- [X] T005 [P] Setup logging infrastructure in `code/__init__.py` or `code/utils/logging.py` <!-- SKIPPED: YAML+regex parse failed (while scanning a simple key
 in "<unicode string>", line 7, column 1:
 1. **`code/utils/__init__.py`**...
 ^
could not find expected ':'
 in "<unicode string>", line 8, column 1:
 2. **`code/utils/logging.py`** -...
 ^) -->
- [ ] T006 Create base data models/entities in `code/models.py` with specific schemas: `MicrobiomeSample` (sample_id, counts, metadata), `MentalHealthRecord` (phq9, gad7, age, bmi), `AssociationResult` (taxon, coef, pval, qval, direction)
- [ ] T007 [P] Setup environment configuration management (`.env` loading if needed)
- [ ] T010 [Write] [US1] Write unit test cases for rarefaction fallback logic in `tests/unit/test_preprocessing.py` (write-first, execute after T014)
- [ ] T011 [Write] [US1] Write unit test cases for missing value filtering in `tests/unit/test_data_ingestion.py` (write-first, execute after T013)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, merge, and preprocess AGP data to create a clean, analysis-ready dataset with valid samples and no missing key values.

**Independent Test**: The pipeline can be tested by running the data ingestion script and verifying that the output CSV contains ≥ 100 valid rows where both microbiome diversity metrics and mental health scores are present, with no missing values in the key predictor/outcome columns.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data_ingestion.py`: Download AGP data (Study ID 10317) via Qiita API or verified HuggingFace mirror (handle rate-limiting with exponential backoff). **Feasibility Check**: Verify the dataset contains both S rRNA and PHQ-9/GAD-7 metadata for overlapping samples. Merge OTU table and metadata on `sample_id`. If no linked data is found, log "Data Gap" and halt analysis (per Plan Phase 0).
- [~] T013 [US1] Implement `code/data_ingestion.py`: Filter samples with missing PHQ-9/GAD-7 scores and log exclusion rate.
- [~] T014 [US1] Implement `code/preprocessing.py`: **Step 1**: Calculate median sequencing depth (median of non-zero column sums). **Step 2**: Estimate sample loss if rarefying to this depth. **Step 3**: If median < 1000 or estimated loss >20%, apply Variance-Stabilizing Transformation (VST) and log fallback; otherwise, apply rarefaction.
- [~] T015 [US1] Implement `code/preprocessing.py`: Filter taxa with <0.1% prevalence on the preprocessed table.
- [~] T016 [US1] Implement `code/preprocessing.py`: Calculate Alpha diversity metrics (Shannon, Simpson) on the **preprocessed** table (after rarefaction/VST and filtering).
- [~] T016b [US1] Implement `code/preprocessing.py`: Generate Beta diversity distance matrices (Bray-Curtis, UniFrac weighted, UniFrac unweighted) on the **preprocessed** table using `skbio`. Output as `data/processed/beta_distance_matrices.npz` or similar.
- [~] T017 [US1] Output `data/processed/cleaned_dataset.csv` (with alpha metrics) and verify ≥ 80% retention AND ≥ 100 valid rows with no missing key columns.
- [~] T010x [Execute] [US1] Execute unit tests for rarefaction fallback logic in `tests/unit/test_preprocessing.py` (after T014 completion).
- [~] T011x [Execute] [US1] Execute unit tests for missing value filtering in `tests/unit/test_data_ingestion.py` (after T013 completion).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Association Analysis (Priority: P2)

**Goal**: Calculate diversity metrics, perform partial Spearman correlation analyses, and execute PERMANOVA tests with covariate adjustment to determine significant associations.

**Independent Test**: The analysis module can be tested by running it on the preprocessed dataset and verifying that it outputs a results table containing partial correlation coefficients, p-values, and effect sizes for the specified mental health variables.

### Implementation for User Story 2

- [~] T020 [US2] Implement `code/analysis.py`: Calculate partial Spearman rank correlation between alpha diversity (Shannon/Simpson) and PHQ-9/GAD-7 scores. **Implementation**: Regress diversity and scores against covariates (age, BMI) to obtain residuals, then calculate Spearman correlation on residuals using `scipy.stats.spearmanr`. Save unadjusted p-values to `data/interim/unadjusted_alpha_pvals.csv`.
- [~] T020a [US2] Implement `code/analysis.py`: Perform partial Spearman correlation for taxa abundance vs PHQ-9/GAD-7. **Implementation**: Regress taxa and scores against covariates (age, BMI) to obtain residuals, then calculate Spearman correlation on residuals using `scipy.stats.spearmanr`. **Constraint**: Do NOT use linear modeling (MaAsLin2) here; strictly follow the partial Spearman requirement. Save unadjusted p-values to `data/interim/unadjusted_taxa_pvals.csv`.
- [~] T021 [US2] Implement `code/analysis.py`: Perform PERMANOVA on beta diversity (Bray-Curtis) between high-depression (PHQ-9 ≥ 10 (2606.17973, https://arxiv.org/abs/2606.17973)) and low-depression groups, AND high-anxiety (GAD-7 ≥ 10) and low-anxiety groups. Use `skbio.stats.distance.permanova` for the permutation-based test, adjusting for covariates via distance matrix residualization.
- [~] T022 [US2] Implement `code/analysis.py`: Apply Benjamini-Hochberg correction to all unadjusted p-values (from T020, T020a, T021) and report adjusted p-values (q-values).
- [~] T023 [US2] **SC-005 Check**: Calculate `|p_adjusted - p_unadjusted|` for each taxon. Identify the maximum delta. Report in `results/temp_covariate_check.txt`: "Max Delta: X.XX. Threshold Met: [True/False]". Do not log a binary 'FAIL' if the threshold is not met; report the actual finding.
- [ ] T024 [US2] **SC-002 Check**: If no significant taxa (q < 0.05), perform Kolmogorov-Smirnov test on p-value distribution.
- [ ] T025 [US2] Output `data/processed/association_results.csv` with correlation coefficients, unadjusted p-values, adjusted p-values (q-values), and effect directions.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-ready visualizations (PCoA, heatmaps) and a summary report highlighting significant associations.

**Independent Test**: The reporting module can be tested by executing the visualization script and verifying that output image files (PNG/SVG) and a summary text file are generated, containing the expected plots and key statistical findings.

### Implementation for User Story 3

- [ ] T026 [Write] [US3] Write unit test cases for plot generation (mock data) in `tests/unit/test_visualization.py`.
- [ ] T027 [US3] Implement `code/visualization.py`: Generate PCoA plot colored by mental health status (High vs. Low PHQ-9 and GAD-7) with group centroids.
- [ ] T028 [US3] Implement `code/visualization.py`: Generate heatmap of top associated taxa with color intensity proportional to correlation coefficient.
- [ ] T029 [US3] Implement `code/report.py`: Generate summary report listing all significant associations (q < 0.05) with direction and magnitude. Include results from T023 (covariate check) and T024 (KS test) in the report.
- [ ] T030 [US3] Output `results/plots/pcoa_plot.png`, `results/plots/taxa_heatmap.png`, and `results/summary_report.txt`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Validation on Independent Cohort (Priority: P3)

**Goal**: Validate effect direction of significant taxa on an independent cohort if accessible.

**Independent Test**: The validation module can be tested by running it on a secondary dataset and verifying that it outputs a comparison table showing effect direction matches for significant taxa.

### Implementation for User Story 4

- [ ] T031 [US4] Implement `code/analysis.py`: Check for accessible independent cohort (e.g., HuggingFace datasets `ukbiobank-microbiome`, `metahit`, or local files matching `data/external/*.csv`).
- [ ] T032 [US4] **Conditional**:
 - **If accessible**: Download secondary data, calculate correlations for top significant taxa, compute '% match' as (matching_directions / total_significant_taxa) scaled to a percentage.. Compare against SC-003 threshold (≥ 80%). Report pass/fail status in `results/validation_report.txt`.
 - **If not accessible**: Log "Validation Skipped: No independent cohort available" and explicitly write this status to `results/validation_report.txt` to satisfy Single Source of Truth. Mark SC-003 as "Not Applicable".
- [ ] T034 [US4] Output `data/processed/validation_results.csv` (if applicable).

---

## Phase 7: Final Output & State Management

**Purpose**: Finalize artifacts and update project state

- [ ] T035 Update `state/projects/PROJ-215-.../state.yaml` with `updated_at` and artifact hashes
- [ ] T036 Generate final project report summarizing all findings, data gaps, and success criteria status (incorporating T023 and T032 results)

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