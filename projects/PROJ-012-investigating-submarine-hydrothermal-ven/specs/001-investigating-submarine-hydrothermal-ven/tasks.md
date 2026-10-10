# Tasks: Submarine Hydrothermal Vent Microbial Communities as Indicators of Ocean Acidification

**Input**: Design documents from `/specs/001-submarine-hydrothermal-vent-microbial-communities/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: `data/raw/`, `data/processed/`, `code/`, `tests/`, `state/`, `results/figures/`
- [ ] T002 Initialize Python 3.11 project with `pandas`, `scikit-learn`, `statsmodels`, `biopython`, `scipy`, `matplotlib`, `seaborn`, `skbio`, `qiime2` dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils.py` with logging infrastructure, outlier detection function (flags pH < 1.0 or > 10.0, flags edge ranges of approximately unity to moderate values and 8.5–10.0 for review per FR-006), and pH heterogeneity calculation (SD within ±15 min window per FR-001.1)
- [X] T005 Create `code/data_models.py` defining `Sample`, `OTU/ASV`, and `DiversityMetric` classes/entities with schema validation
- [ ] T006 Configure `pytest` environment and add `conftest.py` for shared fixtures
- [ ] T007 Create `data-model.md` and `contracts/` schema definitions: `contracts/sample_schema.schema.yaml`, `contracts/otu_table_schema.schema.yaml`, `contracts/analysis_results_schema.schema.yaml` based on Key Entities in spec.md
- [ ] T002b [P] Install QIIME2 via Conda/Mamba and configure environment for CLI usage (required for T018)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw 16S rRNA FASTQ, pH, and temperature logs into a unified temporal-spatial index, handling temporal mismatches and outliers.

**Independent Test**: Provide a mock directory with FASTQ, pH CSV, and Temp CSV; run the pipeline; verify a single unified CSV output and a `rejected_samples.log`.

### Tests for User Story 1

- [~] T008 [P] [US1] Contract test for data ingestion schema in `tests/contract/test_ingestion_schema.py`
- [~] T009 [P] [US1] Integration test for temporal alignment and rejection logic in `tests/integration/test_ingestion_alignment.py`

### Implementation for User Story 1

- [~] T010 [US1] Implement `code/ingestion.py` to load pH CSV and Temp CSV, validate `deployment_event`, `sensor_id`, and `coordinates` fields (Constitution Principle VI), and calculate pH SD within ±15 min window using utility from T004 (depends on T004)
- [~] T011 [US1] Implement temporal alignment logic in `code/ingestion.py`: join samples within ±15 minute window; flag mismatches in `rejected_samples.log`
- [~] T012 [US1] Implement outlier filtering in `code/ingestion.py`: Call outlier detection function from T004 to exclude samples with pH < 1.0 or pH > 10.0. For samples with pH in the lower acidic or higher alkaline ranges, flag for manual review (do not exclude). Ensure the 8.5–10.0 range is explicitly handled per FR-006 (depends on T004)
- [ ] T013 [US1] Enforce exclusion logic: Filter out samples where `pH_heterogeneous` (SD > 0.2) is True or pH is out of range; write `data/processed/filtered_unified_sample_table.csv` for downstream use
- [ ] T014 [US1] Output unified `data/processed/unified_sample_table.csv` (before filtering) with columns: sample_id, timestamp, pH, temp, pH_sd, location, fastq_path, deployment_event, sensor_id, coordinates
- [~] T015 [US1] Extend logging configuration in `code/utils.py` to add handlers for ingestion steps, using infrastructure from T004 (depends on T004)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (metadata only; sequence data handled in US2)

---

## Phase 4: User Story 2 - Diversity Analysis and pH Correlation (Priority: P2)

**Goal**: Calculate alpha diversity (Shannon, Simpson) on rarefied data and run Linear Mixed-Effects (LME) models to correlate diversity with pH.

**Independent Test**: Run analysis on pre-calculated diversity table and pH table; verify output includes regression coefficient, p-value, and metadata flag.

### Tests for User Story 2

- [~] T016 [P] [US2] Contract test for LME output schema in `tests/contract/test_lme_output.py`
- [~] T017 [P] [US2] Integration test for non-linearity detection and warning generation in `tests/integration/test_diversity_nonlinear.py`

### Implementation for User Story 2

- [~] T018 [US2] Implement `code/preprocessing.py` to invoke version-locked QIIME2 pipeline (via CLI wrapper: `qiime demux summarize`, `qiime dada2 denoise-paired`) on raw FASTQ files from `data/raw/` (input) to generate denoised sequences and OTU/ASV table (output: `feature-table.qza` which is then extracted to `data/processed/otu_table.tsv`). (depends on T002b)
- [~] T019 [US2] Implement rarefaction logic in `code/preprocessing.py`: rarefy the OTU table to fixed depths (SC-003) to generate multiple rarefied tables using the depth specified in `data/processed/rarefaction_config.yaml` (determined by T020b)
- [~] T020 [US2] Calculate alpha diversity indices (Shannon, Simpson) for each rarefied sample in `code/preprocessing.py` (depends on T019)
- [ ] T021 [US2] Implement GLMM/Transformation logic (CLR or log-transform) for non-normal diversity indices; output transformed data to `data/processed/diversity_transformed.csv` for T022
- [~] T020b [US2] Determine optimal rarefaction depth via rarefaction curve analysis; if undetermined, set to '[deferred]' and document rationale in `data/processed/rarefaction_config.yaml` (required for T019/T026)
- [~] T022 [US2] Implement `code/analysis.py` LME function: `diversity ~ pH + (1|site)` using `statsmodels` (depends on T021); write results to `data/processed/lme_results.csv` with columns: estimate, se, p_value, model_type. Include fallback logic: if < 2 sites, run fixed-effects linear regression; if N < 10, run Spearman correlation. Output format: estimate, se, p_value, model_type.
- [~] T023 [US2] Add residual analysis in `code/analysis.py` to detect non-linearity; output warning and suggest polynomial term if detected (US-2)
- [ ] T024 [US2] Generate `data/processed/alpha_diversity_results.csv` with pH, diversity metrics, and LME stats (estimate, SE, p-value, model_type)
- [ ] T025 [US2] Add metadata flag in output `data/processed/alpha_diversity_results.csv` explicitly stating 'associational_analysis_of_summary_statistic: true' (FR-003.1)
- [ ] T026 [US2] Implement sensitivity analysis for rarefaction depth (SC-003): sweep {a range of magnitudes, [deferred]} and log stability of results across thresholds to `data/processed/sensitivity_analysis_log.json` (depends on T020b)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Multivariate Community Clustering (Priority: P3)

**Goal**: Perform PERMANOVA and ordination (PCoA/NMDS) to test community clustering by pH, controlling for dispersion and temperature.

**Independent Test**: Provide distance matrix and pH metadata; run PERMANOVA (after betadisper); verify R², F-stat, p-value, and dispersion flag.

### Tests for User Story 3

- [~] T027 [P] [US3] Contract test for PERMANOVA output schema in `tests/contract/test_permanova_output.py`
- [~] T028 [P] [US3] Integration test for dispersion control and rarefaction balancing in `tests/integration/test_beta_diversity_balance.py`

### Implementation for User Story 3

- [~] T029 [US3] Implement `code/analysis.py` to compute Bray-Curtis dissimilarity matrix from rarefied OTU table (depends on T019)
- [~] T030 [US3] Implement `betadisper` test (homogeneity of dispersions) in `code/analysis.py`; if p < 0.05, flag the subsequent PERMANOVA result as `dispersion_flag: 'confounded'` in `data/processed/beta_diversity_results.csv` (FR-004); otherwise 'ok'; do NOT auto-correct data
- [ ] T031 [US3] Implement PERMANOVA test on Bray-Curtis matrix with pH as predictor; if groups are unbalanced (>2x difference), perform a stratified random subsampling step (seed=42) ONLY for the purpose of balancing the test (as per US-3), writing the balanced subset to `data/processed/beta_balanced_subset.csv`; use this subset for the PERMANOVA calculation and downstream reporting; output `data/processed/beta_diversity_results.csv`
- [ ] T032 [US3] Implement ordination logic: PCoA first; if stress > 0.2, fallback to NMDS (FR-005); output ordination coordinates to `data/processed/ordination_coords.csv`
- [ ] T033 [US3] Implement VIF collinearity diagnostic for pH vs. temperature; if VIF > 5, perform dbRDA (variance partitioning) to isolate pH effect; output `data/processed/dbRDA_results.csv` with columns: source (pH, temp, residual), variance_explained, p_value (SC-004)
- [~] T034 [US3] Generate ordination coordinates and intermediate data for plotting (depends on T032)
- [~] T036 [US3] Generate `results/figures/` with all ordination plots (PCoA/NMDS) colored by pH levels, diversity vs. pH scatterplots, and dbRDA plots using `matplotlib`/`seaborn` (depends on T032, T034)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Validation (Polish)

**Purpose**: Generate final reports, validate success criteria, and ensure reproducibility.

- [ ] T037 [P] Generate `results/summary_report.md` aggregating LME, PERMANOVA, and dbRDA results. Required sections: 1. LME Summary, 2. PERMANOVA Summary, 3. dbRDA Variance Partitioning, 4. Sensitivity Analysis
- [ ] T039 [P] Run full pipeline end-to-end on `tests/integration/mock_data/` to verify SC-005 (runtime < 6 hours on 2 CPU/7GB RAM); implement `tests/integration/test_runtime_limit.py` to assert runtime < 21600 seconds; explicitly log runtime and memory usage to `state/runtime_log.json`
- [~] T040 [P] Validate all outputs against `contracts/` schemas and generate `state/` checksums
- [~] T041 [P] Update `README.md` with usage instructions and data requirements

---

## Phase 7: Optional/Deferred - Real Data Integration (Post-MVP)

**Purpose**: Replace mock data with verified real-world data sources (optional for MVP validation).

### Real Data Source Specification & Real Data Fetching (Addressing Review: "Real Data Source Missing")

- [ ] T049 [US1] Define and document the exact real-world data source URLs or package IDs in `research.md` (e.g., specific NCBI SRA Run IDs for vent 16S data, specific sensor log repositories) to replace generic placeholders.
- [ ] T050 [US1] Implement `code/data_loader.py` to stream the REAL 16S data using `datasets.load_dataset(..., streaming=True)` or chunked SRA download, ensuring no full dataset is loaded into RAM at once; explicitly state the sampling rule (e.g., "first 1000 reads per sample" or "full stream") in the task description.
- [ ] T051 [US1] Implement `code/data_loader.py` to fetch REAL pH/temperature sensor logs from the verified source defined in T049, ensuring the loader fails loudly (`raise FileNotFoundError`) if the real source is unreachable, with synthetic fallback permitted ONLY if real data is unavailable for validation purposes.

### Pipeline Integration & Verification (Addressing Review: "Unspecified Data Source")

- [ ] T052 [US1] Update `code/ingestion.py` to call the real data loader from T050/T051 instead of relying on mock data paths; ensure the pipeline fails immediately if real data is missing (unless synthetic fallback is enabled for validation).
- [ ] T053 [US2] Update `code/preprocessing.py` to handle the real OTU/ASV table format produced by the real data loader in T050, ensuring compatibility with QIIME2 artifacts or TSV exports.
- [ ] T054 [US3] Update `code/analysis.py` to accept the real metadata (pH, temp) from the real data loader in T051, ensuring the VIF and dbRDA calculations use real environmental variables.

### Documentation & Transparency (Addressing Review: "Data Source Transparency")

- [ ] T055 [P] Update `README.md` to explicitly list the real data sources used (URLs, accession numbers) and the exact streaming/sampling rules applied (e.g., "Streamed full 16S dataset, sampled first 5000 reads per sample for analysis").
- [ ] T056 [P] Add a `data_sources.md` file documenting the provenance, checksum, and access method for every real dataset used in the pipeline.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Real Data Integration (Phase 7)**: Optional; depends on Phase 3-5 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (metadata only)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for unified metadata input and US2 for sequence processing
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 for count tables and metadata

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
Task: "Contract test for ingestion schema in tests/contract/test_ingestion_schema.py"
Task: "Integration test for temporal alignment in tests/integration/test_ingestion_alignment.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingestion.py to load pH/Temp CSV and calculate pH SD"
Task: "Implement code/utils.py outlier detection function"
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
- Avoid: vague tasks, cross-story dependencies that break independence