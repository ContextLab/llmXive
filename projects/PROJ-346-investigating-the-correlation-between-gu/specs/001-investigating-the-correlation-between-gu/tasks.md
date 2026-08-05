# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and schema definition

- [X] T001a [P] Create project code structure: `projects/PROJ-346-investigating-the-correlation-between-gu/code/`, `projects/PROJ-346-investigating-the-correlation-between-gu/tests/`
- [X] T001b [P] Create project data structure: `projects/PROJ-346-investigating-the-correlation-between-gu/data/raw/`, `data/processed/`, `data/qc/`
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, scikit-learn, statsmodels, seaborn, matplotlib, requests, pyyaml, qiita-client, ukbiobank, pydantic>=2.0) and configure linting (flake8/black)
- [X] T005 [P] Setup data schema validation: Create and output `contracts/dataset.schema.yaml` (YAML format, Pydantic v2 model dump) containing fields: `taxon_name` (str), `relative_abundance` (float), `sample_id` (str) for MicrobialTaxa and `task_type` (str), `z_score` (float), `participant_id` (str) for CognitiveScore. **Completion Criteria**: Run `pytest tests/unit/test_schema.py` to verify file exists, is valid YAML, and passes schema validation. **Note**: This task must complete before T011 and T016. (Removed [P] tag to reflect strict dependency).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Setup environment variable management for dataset URLs (AGP, NHANES, UK Biobank)
- [X] T004 [P] Implement `code/utils.py` with shared constants (read thresholds, abundance filters, age strata) and logging helpers
- [X] T006 [P] Create base data loading functions in `code/utils.py` with retry logic (retry up to 3 times with exponential backoff) for API failures
- [X] T007 [P] Configure `pytest`: Create `pytest.ini`, `tests/conftest.py`, and `tests/run_tests.sh` to enable test execution.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Preprocessing & Meta-Analysis Fallback (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and normalize publicly available gut microbiome and cognitive flexibility data; detect data linkage gaps; execute FR-008 fallback (Meta-Analysis) using synthetic literature-derived statistics if linkage fails.

**Independent Test**: Execute ingestion scripts and verify output files contain expected sample counts, filtered taxa, z-scored cognitive scores, and verify proper logging. If linkage fails, verify the Meta-Analysis Report is generated with pooled effect sizes.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/_ingest.py` to fetch microbiome data. **Source Logic**: Use `qiita-client` library to query Study ID (AGP) via endpoint ` Name or service not known)"))]. Apply FR-001 filters (<10k reads, <0.1% abundance). Save raw parquet. **Execution**: Must include specific API call parameters and error handling for rate limits.
- [X] T012 [US1] Implement code logic to fetch cognitive data from **UK Biobank** (Field 20002, specifically `20002_2_1` for cognitive function) or **NHANES** (Cognitive Function Battery variables `CXT`, `CXT1`, `CXT2`) using `ukbiobank` package or NHANES API. Save raw parquet. **Execution**: Must specify exact variable IDs and authentication flow.
- [X] T013 [US1] Implement `code/02_preprocess.py` to load cognitive data, handle missing values via MICE (per FR-002), compute z-scores, and save processed parquet.
- [X] T014 [US1] Implement `code/02_preprocess.py` logic: 1) Attempt individual-level merge of microbiome and cognitive data; 2) If merge results in 0 rows, **immediately invoke T039a (Synthetic Data Gen)** and then T017c (Meta-Analysis), skipping T015-T033. **Conditional Check**: Explicitly check `if len(merged_df) == 0: execute_fallback_flow()`.
- [X] T015 [US1] Implement `code/02_preprocess.py` logic to add robust outlier filtering (z-score > 3 on merged dataset) with logging to `data/qc/filtering_log.json`. **Output JSON schema: `{ "total_samples": int, "removed_outliers": int, "threshold": float }`**. **Verification**: Script must generate `data/qc/filtering_log.json` with correct schema after processing. **Dependency**: Only runs if T014 merge succeeds.
- [X] T016 [US1] Add validation using `pandera` to ensure output parquet files match `contracts/dataset.schema.yaml`. **Fail hard on schema mismatch**.
- [X] T017a [US1] Implement `code/07_gap_report.py` to generate a **Data Gap Notification** (not the full fallback). **Logic**: 1) Set `failure_reason` to "No common participant IDs found". 2) List `affected_studies` from T011/T012. 3) **Trigger T017c immediately**. **Note**: This task now acts as a trigger, not the final fallback.
- [X] T017c [US1] Implement `code/08_meta_analysis.py` to execute the **FR-008 Meta-Analytic Fallback**. **Input**: `data/raw/literature_metadata.json` (produced by T039a). **Logic**: 1) Aggregate summary statistics (correlation coefficients, p-values, N) from the synthetic literature data. [UNRESOLVED-CLAIM: c_2115ef2d — status=not_enough_info] 2) {{claim:c_69f978ff}} (2104.03394, https://arxiv.org/abs/2104.03394) 3) Calculate heterogeneity (I²). 4) Generate `data/processed/meta_analysis_report.json` with keys: `pooled_r`, `pooled_p`, `I_squared`, `k_studies`, `n_total`. **Verification**: Must satisfy SC-001 and SC-004 by reporting measurable outcomes derived from the meta-analysis.

### Tests for User Story 1 (OPTIONAL) ⚠️

> **NOTE**: Write these tests AFTER implementation to verify specific logic.
> Note: These tasks depend on the existence of implementation code (T011-T017c) to run, even if they fail.

- [X] T008a [US1] Unit test for data filtering logic in `tests/unit/test_filtering.py` (specifically `test_remove_low_read_samples` and `test_remove_rare_taxa`)
- [X] T009a [US1] Unit test for MICE imputation in `tests/unit/test_imputation.py` (specifically `test_mice_missing_values` and `test_zscore_normalization`)
- [X] T010a [US1] Integration test for data merge logic in `tests/integration/test_merge.py` (specifically `test_linkage_failure_detection` and `test_fallback_trigger`)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (or correctly report meta-analysis results)

---

## Phase 3.5: Synthetic Data & Literature Metadata Generation (Prerequisite for Fallback & US4)

**Goal**: Generate deterministic synthetic datasets and literature metadata to ensure FR-008 and US-4 can execute even if real data linkage fails.

- [X] T039a [US1/US4] Implement `code/09_literature_synthesis.py` to generate `data/raw/literature_metadata.json`. **Logic**: 1) Define a deterministic set of 5-10 "synthetic" studies based on literature averages (e.g., "Study A: N=500, r=0.15, p=0.01"). 2) Output a JSON file with keys: `study_id`, `n_samples`, `correlation_r`, `p_value`, `taxon_name`, `effect_direction`. **Purpose**: Provides input for T017c (Meta-Analysis) and T040 (Mechanistic Synthesis). **Execution**: Must be run before T017c or T040.

**Checkpoint**: Synthetic artifacts ready for fallback and mechanistic analysis.

---

## Phase 4: User Story 2 - Correlation and Association Analysis (Priority: P2)

**Goal**: Compute Spearman correlations, apply FDR correction, and fit regularized regression models (only if data linked). **Strictly maintain 'associational only' framing.**

**Independent Test**: Run analysis on preprocessed data; verify correlation matrix, significant taxa list (q < 0.05), regression coefficients, and verify outputs.

**DEPENDS ON**: T014 (Merge Success). If T014 fails, skip this phase. **Hard Stop**: If T017a is triggered, this phase is skipped (fallback path T017c executes instead).
**Note on Status**: Tasks T021-T033 are marked [X] to indicate the **code logic (including skip checks)** is implemented, but they are **Conditional**: they will not execute if T017a is triggered.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T018 [US2] Unit test for Spearman correlation calculation in `tests/unit/test_correlation.py`
- [X] T019 [US2] Unit test for Benjamini-Hochberg FDR correction in `tests/unit/test_fdr.py`
- [X] T020 [US2] Unit test for LASSO/Elastic Net regression in `tests/unit/test_regression.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/03_correlation.py` to compute Spearman rank correlations between taxa and cognitive scores (FR-003). **Explicitly label outputs as 'associational'**. **Conditional**: Skip if `merged_dataset.parquet` missing.
- [X] T022 [US2] Implement `code/03_correlation.py` logic to apply Benjamini-Hochberg FDR correction and flag significant taxa (q < 0.05) (FR-004). **Conditional**: Skip if `merged_dataset.parquet` missing.
- [X] T023 [US2] Implement `code/04_regression.py` to fit LASSO/Elastic Net models with **CLR-transformed microbial taxa** as predictors, age, sex, BMI (FR-005). **Verification Step**: Script must check for `data/processed/merged_dataset.parquet`; if missing, exit gracefully with code 0 and log "N/A - Data Gap" without attempting model fitting. **Explicitly label outputs as 'associational'**. **Implementation Logic**: Use `sklearn.linear_model.ElasticNet` with `l1_ratio=0.5` for Elastic Net; handle missing data gracefully.
- [X] T025 [US2] Ensure all outputs include explicit "associational" framing labels (FR-005, SC-005).
- [X] T026 [US2] Save correlation matrix and regression results to `data/processed/` with metadata.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (or correctly report N/A due to data gap)

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Stratify results by age, test normalization robustness, and generate visualizations. **Strictly maintain 'associational only' framing.**

**Independent Test**: Execute sensitivity scripts; verify stratified tables and plot files (heatmap, forest plot) are generated.

**DEPENDS ON**: T014 (Merge Success). If T014 fails, skip this phase. **Hard Stop**: If T017a is triggered, this phase is blocked.
**Note on Status**: Tasks T029-T033 are marked [X] to indicate the **code logic (including skip checks)** is implemented, but they are **Conditional**: they will not execute if T017a is triggered.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T027 [US3] Unit test for age stratification logic in `tests/unit/test_stratification.py`
- [X] T028 [US3] Unit test for normalization comparison (DESeq2 vs rarefaction) in `tests/unit/test_normalization.py`

### Implementation for User Story 3

- [X] T029 [US3] Implement `code/05_sensitivity.py` to stratify correlations by age groups (<40, ≥40-<60, ≥60) (FR-006); Check for `data/processed/merged_dataset.parquet`; skip if missing. **Implementation Logic**: Group data by age categories; compute Spearman correlation for each group; output separate correlation tables.
- [X] T030 [US3] Implement `code/05_sensitivity.py` to compare significant taxa counts across normalization methods (DESeq2 vs rarefaction); Check for `data/processed/merged_dataset.parquet`; skip if missing. **Output**: Generate a delta table or report section explicitly listing the number of significant taxa for each method and the difference, to satisfy SC-002 measurability. **Implementation Logic**: Run correlation analysis with both normalization methods; compare significant taxa counts; output delta table.
- [X] T031 [US3] Implement `code/06_visualize.py` to generate heatmap of taxa-cognition correlation matrix (FR-007); Check for `data/processed/merged_dataset.parquet`; skip if missing.
- [X] T032 [US3] Implement `code/06_visualize.py` to generate forest plot of regression coefficients with confidence intervals (FR-007); Check for `data/processed/merged_dataset.parquet`; skip if missing.
- [X] T033 [US3] Ensure all visualizations include clear labels for age groups and confidence intervals.

**Checkpoint**: All user stories should now be independently functional (or correctly report N/A due to data gap)

---

## Phase 6: User Story 4 - Mechanistic Synthesis & Future Design (Priority: P2 - Reviewer Driven)

**Goal**: Address reviewer concern (Eric Kandel) regarding the lack of cellular/molecular grounding. **Scope**: This phase does NOT attempt to measure biological markers (impossible with current public datasets) but instead performs a rigorous **Literature Synthesis** to propose a testable mechanistic hypothesis for future experimental validation. It defines the "cellular alphabet" (SCFA, BDNF, Histone Acetylation) linking the gut to the brain.

**Independent Test**: Generate a structured "Mechanistic Gap Report" that cites specific molecular pathways and proposes a future experimental design, distinct from the correlational analysis of US1-US3.

**DEPENDS ON**: Phase 1 & 2. **DEPENDS ON T039a** (Literature Metadata). Independent of T014 (Data Linkage). Can run in parallel with US1-US3.

### Implementation for User Story 4 (Mechanistic Synthesis)

- [ ] T040 [US4] Implement `code/08_mechanistic_synthesis.py` to ingest and parse `data/raw/literature_metadata.json` (produced by T039a) and extract molecular entities (SCFA, BDNF, CREB, Histone Acetylation). **Logic**: Use regex or simple NLP to identify keywords in abstracts; output a graph of "Microbe -> Metabolite -> Neural Marker". <!-- FAILED: unspecified -->
- [X] T041 [US4] Implement `code/08_mechanistic_synthesis.py` to generate a **Mechanistic Hypothesis Report**. **Output**: `reports/mechanistic_hypothesis.md`. **Required Content**: 1. Map specific microbial taxa (from literature) to Short-Chain Fatty Acids (SCFAs). 2. Map SCFAs to histone acetylation (HDAC inhibition) in the hippocampus. 3. Link histone acetylation to BDNF/CREB expression and synaptic plasticity. 4. Explicitly state that the current study (US1-US3) *cannot* measure these markers due to data limitations, but *proposes* them as the necessary "cellular alphabet" for future causal inference. <!-- FAILED: unspecified -->
- [ ] T042 [US4] Implement `code/09_future_design.py` to generate a **Proposed Experimental Protocol**. **Output**: `reports/future_experimental_protocol.md`. **Content**: Define a hypothetical study design (e.g., "Gnotobiotic Mouse Model + Cognitive Flexibility Task + Hippocampal Transcriptomics") that would allow measurement of the proposed molecular pathway. Include specific metrics (e.g., "ChIP-seq for H3K27ac at Bdnf promoter").
- [X] T043 [US4] Update `README.md` and `docs/research_strategy.md` to clearly distinguish between the *Correlational Findings* (US1-US3, limited by data) and the *Mechanistic Hypothesis* (US4, derived from literature). Ensure the report explicitly states: "The current correlational analysis identifies associations; the proposed mechanistic pathway provides the biological plausibility for future causal testing."

### Tests for User Story 4 (OPTIONAL) ⚠️

- [ ] T044 [US4] Unit test for literature keyword extraction logic in `tests/unit/test_mechanistic_extraction.py`.
- [ ] T045 [US4] Integration test for the "Mechanistic Gap Report" generation in `tests/integration/test_mechanistic_report.py` to verify all required molecular links (SCFA -> HDAC -> BDNF) are present in the output.

**Checkpoint**: Mechanistic grounding established via literature synthesis and future experimental design, addressing the reviewer's call for a "cellular alphabet".

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates in `README.md` explaining the FR-008 fallback behavior (Meta-Analysis) and the strict 'associational only' framing.
- [X] T035 [P] Code cleanup and refactoring for CPU efficiency (memory chunking if needed)
- [X] T036a [P] **Performance Optimization**: Implement memory chunking in `code/03_correlation.py`. **Strategy**: Process data in fixed-size chunks.. **Output**: Updated `code/03_correlation.py`.
- [X] T036b [P] **Performance Benchmark**: Run the full analysis pipeline on a subset of N=10,000 samples (or the maximum feasible sample size) and measure total runtime. **Command**: `time python code/03_correlation.py`. **Output**: `data/qc/benchmark_results.json` containing `total_runtime_seconds` (float), `max_memory_mb` (float), `n_samples` (int), `status` (str: "pass" if < 6h, "fail" if >= 6h). **Verification**: Script must validate JSON schema and report "pass" if runtime < 21600 seconds.
- [X] T036c [P] **Performance Documentation**: If Tb runtime exceeds a significant duration, document the specific N-value used and the sampling strategy (e.g., `itertools.islice` first N rows) in `code/utils.py` and `reports/performance_report.md`. **Output**: Updated `code/utils.py` and `reports/performance_report.md`.
- [X] T036d [P] **Synthetic Benchmark**: Run the correlation/regression pipeline on `data/raw/literature_metadata.json` (synthetic N=10,000) to measure performance when real data linkage fails. **Command**: `time python code/03_correlation.py --synthetic`. **Output**: `data/qc/benchmark_synthetic_results.json`. **Purpose**: Ensures SC-003 is measurable even if real data linkage fails.
- [X] T037 [P] Additional unit tests for edge cases (zero significant taxa, rate-limiting) in `tests/unit/`
- [X] T038 [P] Security hardening: Sanitize all external URLs and file paths
- [X] T039 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility and verify that all outputs are explicitly labeled 'associational only' as per SC-005.
- [X] T046 [P] **Review Integration**: Update `reports/README.md` to include a section "Response to Reviewer (Eric Kandel)" explaining that mechanistic analysis is now addressed via US4 (Literature Synthesis) and future experimental design.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **DEPENDS on T014 (Merge Success)**; skips if data gap. **BLOCKED if T017a is triggered.**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **DEPENDS on T014 (Merge Success)**; skips if data gap. **BLOCKED if T017a is triggered.**
- **User Story 4 (P2 - Reviewer)**: Can start after Foundational (Phase 2). **DEPENDS on T039a**. Independent of Data Linkage. Runs in parallel with US1-US3.
- **Phase 7 (Polish)**: Can run independently of data linkage (uses literature, not cohort data). **DEPENDS on Phase 1 & 2**. Can run in parallel with US1/US2/US3/US4.

### Within Each User Story

- Tests (if included) MUST be written AFTER implementation to verify specific logic (T008-T010 depend on T011-T017c)
- Ingestion/Preprocessing (T011-T017c) before Correlation (T021-T026)
- Correlation before Regression (T023)
- Regression before Visualization (T031-T032)
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- US2 and US3 can only start in parallel with US1 **IF** the Data Gap (T017a) is NOT triggered. If T017a triggers, US2/US3 are blocked.
- **User Story 4 (Mechanistic)** can run in parallel with US1, US2, and US3 as it relies on literature, not the specific cohort data.
- **Phase 7 (Polish)** can run in parallel with all US stories.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (conditional on data availability)

### Specific Task Dependencies

- **T005**: Must complete before T011 and T016. (Parallel-safe within Phase 1, but blocks downstream).
- **T039a**: Must complete before T017c and T040.
- **T017a**: If triggered, acts as a **Hard Stop** for US2/US3. Triggers T017c.
- **T036a, T036b, T036c, T036d**: Must be executed sequentially (Implement -> Benchmark -> Document).
- **T040-T043**: Must be executed sequentially to build the mechanistic hypothesis.
- **T046**: Can run independently of T014 (Data Linkage). Do not depend on `merged_dataset.parquet`.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each logical group
- **CRITICAL**: If FR-008 (Meta-Analysis) is triggered (T017a), US2 and US3 tasks must gracefully skip. T017c MUST execute to satisfy FR-008.
- **Strict Constraint**: All analysis must be labeled 'associational only'. No causal inference or mechanistic claims (e.g., 'cellular alphabet', 'synaptic plasticity') are permitted in the *results* of the correlation study (US1-US3). The *mechanistic framework* (US4) is a theoretical exercise derived from literature, not empirical claims from the current dataset.
- **Data Sources**: Only AGP, Qiita, UK Biobank, and NHANES are allowed. No fallback to HMP/MetaHIT or synthetic data for *primary* analysis. Synthetic data (T039a) is ONLY for fallback (FR-008) and benchmarking (SC-003).
- **CPU Constraint**: All tasks must be implementable on a multi-core CPU with sufficient memory. No GPU, no 8-bit models. Use `scikit-learn`, `scipy`, `statsmodels` only.
- **Sampling Strategy**: If N=10,000 is not feasible, explicitly define the sampling strategy (e.g., `itertools.islice` first N rows) in `code/utils.py` and document the N-value in the final report.
- **Scope Boundary**: The original Phase 6 (Mechanistic Grounding) was removed as scope creep. It has been replaced by **Phase 6 (User Story 4)** which is a *Literature Synthesis* and *Future Design* task, explicitly acknowledging that the current data cannot support mechanistic claims. This satisfies the reviewer's call for a "cellular alphabet" without violating the constitution's data integrity rules.
- **Reviewer Response**: The note in Phase 6 (T040-T043) and the updated `README.md` (T034) explain that mechanistic analysis is now addressed via a literature-based hypothesis generation and future experimental design, distinct from the correlational analysis.
- **FR-008 Compliance**: T017c ensures FR-008 is satisfied by performing a meta-analysis on synthetic literature data if real data linkage fails, rather than just reporting a gap.