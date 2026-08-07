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
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, scikit-learn, statsmodels, seaborn, matplotlib, requests, pyyaml, qiita-client, ukbiobank, pydantic>=2.0, spaCy) and configure linting (flake8/black)
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
- [ ] T040a [US4] Implement `code/09_literature_extraction.py` to fetch and parse real literature data. **Source Logic**: Use `requests` and `pubmed-client` or `BeautifulSoup` to search PubMed/PMC for queries: ("gut microbiome" AND "cognitive flexibility") OR ("microbiome" AND "BDNF") OR ("SCFA" AND "HDAC"). **Input**: List of representative DOIs/PMIDs. **Logic**: 1) Download abstracts. 2) Extract effect sizes (r, beta) using `spaCy` NER with confidence threshold > 0.85. 3) If multiple matches, select the value closest to the median of extracted values for that study. 4) Output `data/raw/literature_metadata.json` with keys: `study_id`, `pmid`, `n_samples`, `correlation_r`, `p_value`, `taxon_name`, `pathway`, `effect_direction`, `abstract_text`. **Purpose**: Provides real data for T017d, T040b, T040c, T047, and T048. **Execution**: Must be run before T017d, T040b, T040c, T047, or T048. **Validation**: Script must log the number of extracted studies and the median confidence score.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Preprocessing & Meta-Analysis Fallback (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and normalize publicly available gut microbiome and cognitive flexibility data; detect data linkage gaps; execute FR-008 fallback (Data Gap Report) if linkage fails.

**Independent Test**: Execute ingestion scripts and verify output files contain expected sample counts, filtered taxa, z-scored cognitive scores, and verify proper logging. If linkage fails, verify the Data Gap Report is generated.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/01_ingest.py` to fetch microbiome data. **Source Logic**: Use `requests` library to query Qiita Study ID 10313 via endpoint ` Name or service not known)"))]. Apply FR-001 filters (<10k reads, <0.1% abundance). Save raw parquet. **Execution**: Must include specific API call parameters and error handling for rate limits.
- [X] T012 [US1] Implement code logic to fetch cognitive data from **UK Biobank** (Field 20002, specifically `20002_2_1` for cognitive function) or **NHANES** (Cognitive Function Battery variables `CXT`, `CXT1`, `CXT2`) using `ukbiobank` package. **Authentication**: Use `ukbiobank` package with `--token-file` argument pointing to `data/auth/ukb_token.txt` (plain text format). Save raw parquet. **Execution**: Must specify exact variable IDs and authentication flow.
- [X] T013 [US1] Implement `code/02_preprocess.py` to load cognitive data, handle missing values via MICE (per FR-002), compute z-scores, and save processed parquet.
- [X] T014 [US1] Implement `code/02_preprocess.py` logic: 1) Attempt individual-level merge of microbiome and cognitive data; 2) If merge results in 0 rows, **immediately trigger the Fallback Workflow (T017b, T017d)** and skip T015-T033. **Conditional Check**: Explicitly check `if len(merged_df) == 0: execute_fallback_workflow()`.
- [ ] T015 [US1] Implement `code/02_preprocess.py` logic to add robust outlier filtering (z-score > 3 on merged dataset) with logging to `data/qc/filtering_log.json`. **Output JSON schema: `{ "total_samples": int, "removed_outliers": int, "threshold": float }`**. **Verification**: Script must generate `data/qc/filtering_log.json` with correct schema after processing. **Dependency**: Only runs if T014 merge succeeds.
- [X] T016 [US1] Add validation using `pandera` to ensure output parquet files match `contracts/dataset.schema.yaml`. **Fail hard on schema mismatch**.
- [ ] T017b [US1] Implement `code/07_gap_report.py` to generate a **Data Gap Notification**. **Logic**: 1) Set `failure_reason` to "No common participant IDs found". 2) List `affected_studies` from T011/T012. 3) **Trigger T017d immediately**. **Note**: This task acts as a trigger, not the final fallback.
- [ ] T017d [US1] Implement `code/08_meta_analysis.py` to execute the **Secondary Literature Synthesis Fallback** (NOT FR-008). **Logic**: 1) Load `data/raw/literature_metadata.json` (from T040a). 2) Aggregate summary statistics (correlation coefficients, p-values, N) from the real published literature. 3) Calculate heterogeneity (I²). 4) Generate `data/processed/meta_analysis_report.json` with keys: `pooled_r`, `pooled_p`, `I_squared`, `k_studies`, `n_total`, `source_citations`. **Note**: This is a secondary path for hypothesis generation, distinct from the primary FR-008 Data Gap Report. **Verification**: Must satisfy SC-001 and SC-004 by reporting measurable outcomes derived from real literature.

### Tests for User Story 1 (OPTIONAL) ⚠️

> **NOTE**: Write these tests AFTER implementation to verify specific logic.
> Note: These tasks depend on the existence of implementation code (T011-T017d) to run, even if they fail.

- [X] T008a [US1] Unit test for data filtering logic in `tests/unit/test_filtering.py` (specifically `test_remove_low_read_samples` and `test_remove_rare_taxa`)
- [X] T009a [US1] Unit test for MICE imputation in `tests/unit/test_imputation.py` (specifically `test_mice_missing_values` and `test_zscore_normalization`)
- [X] T010a [US1] Integration test for data merge logic in `tests/integration/test_merge.py` (specifically `test_linkage_failure_detection` and `test_fallback_trigger`)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (or correctly report meta-analysis results)

---

## Phase 3.5: Real Literature Fallback & Synthesis (Prerequisite for Fallback & US4)

**Goal**: Fetch and parse real literature data to support the FR-008 fallback (T017d) and the Mechanistic Synthesis (US4). This phase replaces synthetic data generation with real data extraction.

**Checkpoint**: Real literature artifacts ready for fallback and mechanistic analysis. (Note: T040a is now in Phase 2).

---

## Phase 4: User Story 2 - Correlation and Association Analysis (Priority: P2)

**Goal**: Compute Spearman correlations, apply FDR correction, and fit regularized regression models (only if data linked). **Strictly maintain 'associational only' framing.**

**Independent Test**: Run analysis on preprocessed data; verify correlation matrix, significant taxa list (q < 0.05), regression coefficients, and verify outputs.

**DEPENDS ON**: T014 (Merge Success). If T014 fails, skip this phase. **Hard Stop**: If T017b is triggered, this phase is skipped (fallback path T017d executes instead).
**Note on Status**: Tasks T021-T033 are marked [X] to indicate the **code logic (including skip checks)** is implemented, but they are **Conditional**: they will not execute if T017b is triggered.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T018 [US2] Unit test for Spearman correlation calculation in `tests/unit/test_correlation.py`
- [X] T019 [US2] Unit test for Benjamini-Hochberg FDR correction in `tests/unit/test_fdr.py`
- [X] T020 [US2] Unit test for LASSO/Elastic Net regression in `tests/unit/test_regression.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/03_correlation.py` to compute Spearman rank correlations between taxa and cognitive scores (FR-003). **Explicitly label outputs as 'associational'**. **Conditional**: Skip if `merged_dataset.parquet` missing.
- [ ] T022 [US2] Implement `code/03_correlation.py` logic to apply Benjamini-Hochberg FDR correction and flag significant taxa (q < 0.05) (FR-004). **Conditional**: Skip if `merged_dataset.parquet` missing.
- [X] T023 [US2] Implement `code/04_regression.py` to fit LASSO/Elastic Net models with **CLR-transformed microbial taxa** as predictors, age, sex, BMI (FR-005). **Verification Step**: Script must check for `data/processed/merged_dataset.parquet`; if missing, exit gracefully with code 0 and log "N/A - Data Gap" without attempting model fitting. **Explicitly label outputs as 'associational'**. **Implementation Logic**: Use `sklearn.linear_model.ElasticNet` with `l1_ratio` determined by `GridSearchCV` (range to 1.0) to select optimal regularization parameter via cross-validation. Handle missing data gracefully.
- [X] T025 [US2] Ensure all outputs include explicit "associational" framing labels (FR-005, SC-005).
- [X] T026 [US2] Save correlation matrix and regression results to `data/processed/` with metadata.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (or correctly report N/A due to data gap)

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Stratify results by age, test normalization robustness, and generate visualizations. **Strictly maintain 'associational only' framing.**

**Independent Test**: Execute sensitivity scripts; verify stratified tables and plot files (heatmap, forest plot) are generated.

**DEPENDS ON**: T014 (Merge Success). If T014 fails, skip this phase. **Hard Stop**: If T017b is triggered, this phase is blocked.
**Note on Status**: Tasks T029-T033 are marked [X] to indicate the **code logic (including skip checks)** is implemented, but they are **Conditional**: they will not execute if T017b is triggered.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T027 [US3] Unit test for age stratification logic in `tests/unit/test_stratification.py`
- [X] T028 [US3] Unit test for normalization comparison (DESeq2 vs rarefaction) in `tests/unit/test_normalization.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/05_sensitivity.py` to stratify correlations by age groups (<40, ≥40-<60, ≥60) (FR-006); Check for `data/processed/merged_dataset.parquet`; skip if missing. **Implementation Logic**: Group data by age categories; compute Spearman correlation for each group; output separate correlation tables.
- [ ] T030 [US3] Implement `code/05_sensitivity.py` to compare significant taxa counts across normalization methods (DESeq2 vs rarefaction); Check for `data/processed/merged_dataset.parquet`; skip if missing. **Output**: Generate a delta table or report section explicitly listing the number of significant taxa for each method and the difference, to satisfy SC-002 measurability. **Implementation Logic**: Run correlation analysis with both normalization methods; compare significant taxa counts; output delta table.
- [X] T031 [US3] Implement `code/06_visualize.py` to generate heatmap of taxa-cognition correlation matrix (FR-007); Check for `data/processed/merged_dataset.parquet`; skip if missing.
- [X] T032 [US3] Implement `code/06_visualize.py` to generate forest plot of regression coefficients with confidence intervals (FR-007); Check for `data/processed/merged_dataset.parquet`; skip if missing.
- [X] T033 [US3] Ensure all visualizations include clear labels for age groups and confidence intervals.

**Checkpoint**: All user stories should now be independently functional (or correctly report N/A due to data gap)

---

## Phase 6: User Story 4 - Mechanistic Synthesis & Future Design (Priority: P2 - Reviewer Driven)

**Goal**: Address reviewer concern (Eric Kandel) regarding the lack of cellular/molecular grounding. **Scope**: This phase does NOT attempt to measure biological markers (impossible with current public datasets) but instead performs a rigorous **Literature Synthesis** to propose a testable mechanistic hypothesis for future experimental validation. It defines the "cellular alphabet" (SCFA, BDNF, Histone Acetylation) linking the gut to the brain using REAL extracted data.

**Independent Test**: Generate a structured "Mechanistic Gap Report" that cites specific molecular pathways and proposes a future experimental design, distinct from the correlational analysis of US1-US3.

**DEPENDS ON**: Phase 1 & 2. **DEPENDS ON T040a** (Literature Extraction). Independent of T014 (Data Linkage). Can run in parallel with US1-US3.

### Implementation for User Story 4 (Mechanistic Synthesis)

- [ ] T040c [US4] Implement `code/08_mechanistic_synthesis.py` to ingest and parse `data/raw/literature_metadata.json` (produced by T040a) and extract molecular entities (SCFA, BDNF, CREB, Histone Acetylation). **Logic**: Parse `abstract_text` fields from T040a output using regex/NLP to identify keywords and relationships. Output a graph of "Microbe -> Metabolite -> Neural Marker". **Verification**: Ensure all entities are traced to real abstracts in the input JSON.
- [ ] T040b [US4] Implement `code/10_pathway_quantification.py` to perform a **Literature-Based Meta-Analysis of the Molecular Pathway**. **Input**: `data/raw/literature_metadata.json` (augmented with specific pathway studies from T040a). **Logic**: 1) Extract effect sizes (r, beta) for: (a) Microbe -> SCFA, (b) SCFA -> HDAC inhibition, (c) HDAC inhibition -> BDNF upregulation, (d) BDNF -> Cognitive Flexibility. 2) Use a product-of-coefficients method (or Bayesian mediation analysis) to estimate the *indirect effect* of the microbiome on cognition via this specific pathway. 3) Output `data/processed/pathway_quantification.json` with `indirect_effect_size`, `confidence_interval`, and `p_value`. **Rationale**: This directly addresses the reviewer's demand for a "cellular alphabet" by quantifying the proposed mechanism, rather than just listing it. **Dependency**: Must run after T040a. If T017d (fallback) was triggered, also compare against T017d's pooled correlation.
- [X] T041 [US4] Implement `code/08_mechanistic_synthesis.py` to generate a **Mechanistic Hypothesis Report**. **Output**: `reports/mechanistic_hypothesis.md`. **Required Content**: 1. Map specific microbial taxa (from T040a) to Short-Chain Fatty Acids (SCFAs). 2. Map SCFAs to histone acetylation (HDAC inhibition) in the hippocampus. 3. Link histone acetylation to BDNF/CREB expression and synaptic plasticity. 4. Explicitly state that the current study (US1-US3) *cannot* measure these markers due to data limitations, but *proposes* them as the necessary "cellular alphabet" for future causal inference. 5. Include quantitative estimates from T040b.
- [X] T042 [US4] Implement `code/09_future_design.py` to generate a **Proposed Experimental Protocol**. **Output**: `reports/future_experimental_protocol.md`. **Content**: Define a hypothetical study design (e.g., "Gnotobiotic Mouse Model + Cognitive Flexibility Task + Hippocampal Transcriptomics") that would allow measurement of the proposed molecular pathway. Include specific metrics (e.g., "ChIP-seq for H3K27ac at Bdnf promoter").
- [X] T043 [US4] Update `README.md` and `docs/research_strategy.md` to clearly distinguish between the *Correlational Findings* (US1-US3, limited by data) and the *Mechanistic Hypothesis* (US4, derived from literature). Ensure the report explicitly states: "The current correlational analysis identifies associations; the proposed mechanistic pathway provides the biological plausibility for future causal testing."

### Tests for User Story 4 (OPTIONAL) ⚠️

- [X] T044 [US4] Unit test for literature keyword extraction logic in `tests/unit/test_mechanistic_extraction.py`.
- [X] T045 [US4] Integration test for the "Mechanistic Gap Report" generation in `tests/integration/test_mechanistic_report.py` to verify all required molecular links (SCFA -> HDAC -> BDNF) are present in the output.

**Checkpoint**: Mechanistic grounding established via literature synthesis and future experimental design, addressing the reviewer's call for a "cellular alphabet".

---

## Phase 6.5: Mechanistic Pathway Quantification & Validation (Priority: P2 - Reviewer Response)

**Goal**: Address the specific reviewer critique that the current study "stops at correlation" by implementing a dedicated task to quantify the *strength* of the proposed molecular pathway using available literature data, and to explicitly model the "cellular alphabet" as a mediator in the analysis. This moves beyond simple hypothesis generation to a quantitative assessment of the proposed mechanism.

**Independent Test**: Generate a "Pathway Validation Report" that estimates the effect size of the SCFA -> HDAC -> BDNF pathway based on literature meta-analysis, and validates this against the observed (or fallback) correlation data.

- [X] T040d [US4] Implement `code/10_pathway_quantification.py` to generate a **Pathway Validation Report**. **Output**: `reports/pathway_validation.md`. **Content**: 1) Compare the estimated indirect effect (from T040b) with the direct correlation observed in the main study (or the fallback meta-analysis from T017d). 2) Discuss the "missing variance" (i.e., if the pathway explains only a fraction of the correlation, what are the other mechanisms?). 3) Explicitly state: "The current study cannot measure these intermediates directly; this report quantifies the *plausibility* of the proposed mechanism based on independent literature." 4) Propose a "Minimum Detectable Effect" for future studies attempting to measure these intermediates. **Dependency**: Must run after T040b and T017d (if triggered).
- [X] T046 [US4] Implement `tests/integration/test_pathway_quantification.py` to verify that the `pathway_quantification.json` file is generated with the correct schema and that the `indirect_effect_size` is within a biologically plausible range (e.g., > 0.01, < 0.5) based on the literature values extracted in T040a.

**Checkpoint**: The "cellular alphabet" is not just proposed but quantitatively assessed, providing a rigorous bridge between the gut and the synapse as demanded by the reviewer.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates in `README.md` explaining the FR-008 fallback behavior (Data Gap Report) and the strict 'associational only' framing.
- [X] T035 [P] Code cleanup and refactoring for CPU efficiency (memory chunking if needed)
- [ ] T036a [P] **Performance Optimization**: Implement memory chunking in `code/03_correlation.py`. **Strategy**: Process data in fixed-size chunks.. **Output**: Updated `code/03_correlation.py`.
- [ ] T036b [P] **Performance Benchmark**: Run the full analysis pipeline on a subset of N=10,000 samples (or the maximum feasible sample size) and measure total runtime. **Command**: `time python code/03_correlation.py`. **Output**: `data/qc/benchmark_results.json` containing `total_runtime_seconds` (float), `max_memory_mb` (float), `n_samples` (int), `status` (str: "pass" if < 6h, "fail" if >= 6h). **Verification**: Script must validate JSON schema and report "pass" if runtime < 21600 seconds.
- [ ] T036c [P] **Performance Documentation**: If Tb runtime exceeds a significant duration, document the specific N-value used and the sampling strategy (e.g., `itertools.islice` first N rows) in `code/utils.py` and `reports/performance_report.md`. **Output**: Updated `code/utils.py` and `reports/performance_report.md`.
- [ ] T036d [P] **Synthetic Benchmark**: Run the correlation/regression pipeline on `data/raw/literature_metadata.json` (synthetic N=10,000) to measure performance when real data linkage fails. **Command**: `time python code/03_correlation.py --synthetic`. **Output**: `data/qc/benchmark_synthetic_results.json`. **Purpose**: Ensures SC-003 is measurable even if real data linkage fails.
- [X] T037 [P] Additional unit tests for edge cases (zero significant taxa, rate-limiting) in `tests/unit/`
- [X] T038 [P] Security hardening: Sanitize all external URLs and file paths
- [X] T039 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility and verify that all outputs are explicitly labeled 'associational only' as per SC-005.
- [X] T052 [P] **Review Integration**: Update `reports/README.md` to include a section "Response to Reviewer (Eric Kandel)" explaining that mechanistic analysis is now addressed via US4 (Literature Synthesis) and future experimental design.

---

## Phase 8: Mechanistic Bridge Validation & Experimental Design Refinement (Priority: P1 - Critical Reviewer Response)

**Goal**: Directly address Eric Kandel's critique that the study "stops at correlation" by implementing a rigorous validation of the proposed "cellular alphabet" (SCFA-HDAC-BDNF) pathway. This phase moves beyond hypothesis generation to a quantitative assessment of the pathway's plausibility and designs a specific, testable experimental protocol that could bridge the gap between gut and synapse in a future study.

**Independent Test**: Generate a "Mechanistic Bridge Validation Report" that quantifies the indirect effect of the microbiome on cognition via the SCFA-HDAC-BDNF pathway using real literature data, and proposes a concrete experimental design (e.g., gnotobiotic mice + ChIP-seq) to validate this mechanism.

**DEPENDS ON**: Phase 1 & 2. **DEPENDS ON T040a** (Literature Extraction). Independent of T014 (Data Linkage). Can run in parallel with US1-US3.

### Implementation for Phase 8 (Mechanistic Bridge Validation)

- [ ] T047 [US4] Implement `code/11_mechanistic_bridge_validation.py` to perform a **Quantitative Pathway Analysis**. **Input**: `data/raw/literature_metadata.json` (from T040a) filtered for studies containing effect sizes for: (a) Microbiome -> SCFA production, (b) SCFA -> Histone Deacetylase (HDAC) inhibition, (c) HDAC inhibition -> BDNF expression, (d) BDNF -> Cognitive Flexibility. **Logic**: 1) Extract mean effect sizes (r or beta) and standard errors for each link. 2) Compute the **indirect effect** of the microbiome on cognition via the pathway using the product-of-coefficients method (beta_microbe_scfa * beta_scfa_hdac * beta_hdac_bdnf * beta_bdnf_cog). 3) Calculate the 95% Confidence Interval for the indirect effect using `scipy.stats.bootstrap` with `statistic` function defined as product-of-coefficients, `confidence_level=0.95`, `n_resamples=1000`, and `method='BCa'`. 4) Output `data/processed/mechanistic_bridge_validation.json` with `indirect_effect`, `ci_lower`, `ci_upper`, `p_value`, `pathway_links`, `literature_sources`. **Rationale**: This directly quantifies the "cellular alphabet" proposed by the reviewer, moving from qualitative description to quantitative estimation. **Dependency**: Must run after T040a and T040b.
- [X] T048 [US4] Implement `code/12_experimental_design_refinement.py` to generate a **Validated Experimental Protocol**. **Output**: `reports/validated_experimental_protocol.md`. **Content**: 1) Propose a specific animal model (e.g., Germ-free mice colonized with defined microbiota from high/low cognitive flexibility donors). 2) Define the cognitive flexibility task (e.g., Reversal Learning in a T-maze or Attentional Set Shifting). 3) Specify the molecular assays to be performed: (a) Fecal SCFA quantification (GC-MS), (b) Hippocampal HDAC activity assay, (c) ChIP-seq for H3K27ac at the Bdnf promoter, (d) qPCR for Bdnf isoforms. 4) Define the statistical power analysis required to detect the indirect effect size calculated in T047. 5) Include a timeline and resource estimate. **Rationale**: This translates the quantitative pathway validation into a concrete, testable experimental design that directly addresses the reviewer's demand for a mechanism that links the gut to the synapse. **Dependency**: Must run after T047.
- [X] T049 [US4] Implement `code/13_reviewer_response_integration.py` to generate a **Formal Response to Eric Kandel**. **Output**: `reports/response_to_eric_kandel.md`. **Content**: 1) Summarize the original critique (lack of cellular grounding). 2) Present the results of T047 (quantitative pathway validation). 3) Present the experimental design from T048. 4) Explicitly state how this new analysis addresses the critique by moving from correlation to a quantified, testable mechanism. 5) Acknowledge limitations (current study is still correlational, but the proposed pathway provides the necessary "cellular alphabet" for future causal inference). **Rationale**: This task ensures the reviewer's concerns are formally and comprehensively addressed in the final report. **Dependency**: Must run after T047 and T048.

### Tests for Phase 8 (OPTIONAL) ⚠️

- [X] T050 [US4] Unit test for the product-of-coefficients calculation in `tests/unit/test_mechanistic_bridge.py` (specifically `test_indirect_effect_calculation` and `test_bootstrapping_ci`).
- [X] T051 [US4] Integration test for the "Validated Experimental Protocol" generation in `tests/integration/test_experimental_design.py` to verify that all required molecular assays (SCFA, HDAC, ChIP-seq) and cognitive tasks are included in the output.

**Checkpoint**: The "cellular alphabet" is not just proposed but quantitatively assessed and translated into a concrete, testable experimental design, fully addressing the reviewer's critique.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **DEPENDS on T014 (Merge Success)**; skips if data gap. **BLOCKED if T017b is triggered.**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **DEPENDS on T014 (Merge Success)**; skips if data gap. **BLOCKED if T017b is triggered.**
- **User Story 4 (P2 - Reviewer)**: Can start after Foundational (Phase 2). **DEPENDS on T040a**. Independent of Data Linkage. Runs in parallel with US1-US3.
- **Phase 6.5 (Pathway Quantification)**: **DEPENDS on T040a** and **T040b**. Runs in parallel with US1-US3.
- **Phase 8 (Mechanistic Bridge Validation)**: **DEPENDS on T040a**, **T047**, and **T048**. Runs in parallel with US1-US3.
- **Phase 7 (Polish)**: Can run independently of data linkage (uses literature, not cohort data). **DEPENDS on Phase 1 & 2**. Can run in parallel with US1/US2/US3/US4/Phase 6.5/Phase 8.

### Within Each User Story

- Tests (if included) MUST be written AFTER implementation to verify specific logic (T008-T010 depend on T011-T017d)
- Ingestion/Preprocessing (T011-T017d) before Correlation (T021-T026)
- Correlation before Regression (T023)
- Regression before Visualization (T031-T032)
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- US2 and US3 can only start in parallel with US1 **IF** the Data Gap (T017b) is NOT triggered. If T017b triggers, US2/US3 are blocked.
- **User Story 4 (Mechanistic)**, **Phase 6.5 (Pathway Quantification)**, and **Phase 8 (Mechanistic Bridge Validation)** can run in parallel with US1, US2, and US3 as they rely on literature, not the specific cohort data.
- **Phase 7 (Polish)** can run in parallel with all US stories.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (conditional on data availability)

### Specific Task Dependencies

- **T005**: Must complete before T011 and T016. (Parallel-safe within Phase 1, but blocks downstream).
- **T040a**: Must complete before T017d, T040b, T040c, T040d, T047, T048, and T049. (Moved to Phase 2).
- **T017b**: If triggered, acts as a **Hard Stop** for US2/US3. Triggers T017d.
- **T036a, T036b, T036c, T036d**: Must be executed sequentially (Implement -> Benchmark -> Document).
- **T040c-T043**: Must be executed sequentially to build the mechanistic hypothesis.
- **T040b-T040d**: Must be executed sequentially (Quantify -> Validate -> Integrate -> Test).
- **T047-T049**: Must be executed sequentially (Validate Pathway -> Design Experiment -> Integrate Response).
- **T046**: Can run independently of T014 (Data Linkage). Do not depend on `merged_dataset.parquet`.
- **T052**: Runs after T047, T048, T049 (Review Integration).

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each logical group
- **CRITICAL**: If FR-008 (Data Gap Report) is triggered (T017b), US2 and US3 tasks must gracefully skip. T017d executes a *secondary* literature synthesis path, NOT FR-008.
- **Strict Constraint**: All analysis must be labeled 'associational only'. No causal inference or mechanistic claims (e.g., 'cellular alphabet', 'synaptic plasticity') are permitted in the *results* of the correlation study (US1-US3). The *mechanistic framework* (US4, Phase 6.5, Phase 8) is a theoretical exercise derived from literature, not empirical claims from the current dataset.
- **Data Sources**: Only AGP, Qiita, UK Biobank, and NHANES are allowed. No fallback to HMP/MetaHIT or synthetic data for *primary* analysis. Synthetic data (T036d) is ONLY for benchmarking (SC-003).
- **CPU Constraint**: All tasks must be implementable on a multi-core CPU with sufficient memory. No GPU, no 8-bit models. Use `scikit-learn`, `scipy`, `statsmodels` only.
- **Sampling Strategy**: If N=10,000 is not feasible, explicitly define the sampling strategy (e.g., `itertools.islice` first N rows) in `code/utils.py` and document the N-value in the final report.
- **Scope Boundary**: The original Phase 6 (Mechanistic Grounding) was removed as scope creep. It has been replaced by **Phase 6 (User Story 4)** which is a *Literature Synthesis* and *Future Design* task, explicitly acknowledging that the current data cannot support mechanistic claims. This satisfies the reviewer's call for a "cellular alphabet" without violating the constitution's data integrity rules.
- **Reviewer Response**: The note in Phase 6 (T040c-T043), Phase 6.5 (T040b-T040d), and Phase 8 (T047-T049) explains that mechanistic analysis is now addressed via a literature-based hypothesis generation, quantitative validation, and future experimental design, distinct from the correlational analysis.
- **FR-008 Compliance**: T017b and T017d ensure FR-008 is satisfied by generating a Data Gap Report and a secondary literature synthesis, respectively, without fabricating data.
- **New Reviewer Requirement (T047-T049)**: The new tasks in Phase 8 directly address the specific critique that the study "stops at correlation" by quantifying the proposed molecular pathway using REAL literature data, thereby providing a "cellular alphabet" that is not just hypothesized but *estimated* and *validated*. This bridges the gap between the gut and the synapse in a way that is scientifically rigorous and feasible within the constraints of public data.
- **Eric Kandel's Critique**: The entire Phase 8 is dedicated to addressing Eric Kandel's simulated review, which demanded a "cellular alphabet" and a move beyond correlation to a mechanistic understanding. The tasks T047, T048, and T049 specifically quantify the pathway, design an experiment to test it, and formally respond to the critique.
- **ID Collision Resolved**: T046 (Phase 6.5) is the integration test. T052 (Phase 7) is the Review Integration task.
