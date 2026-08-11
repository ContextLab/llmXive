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

- [ ] T001 Create project structure per implementation plan: `data/raw/`, `data/processed/`, `code/`, `tests/`, `state/`, `results/figures/`
- [X] T002 Initialize Python 3.11 project with `pandas`, `scikit-learn`, `statsmodels`, `biopython`, `scipy`, `matplotlib`, `seaborn`, `skbio`, `qiime2` dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils.py` with logging infrastructure, outlier detection function (flags pH < 1.0 or > 10.0, flags edge ranges of low and high magnitude for review. per FR-006), and pH heterogeneity calculation (SD within ±15 min window per FR-001.1)
- [X] T005 Create `code/data_models.py` defining `Sample`, `OTU/ASV`, and `DiversityMetric` classes/entities with schema validation
- [ ] T006 Configure `pytest` environment and add `conftest.py` for shared fixtures
- [ ] T007 Create `data-model.md` and `contracts/` schema definitions: `contracts/sample_schema.schema.yaml`, `contracts/otu_table_schema.schema.yaml`, `contracts/analysis_results_schema.schema.yaml` based on Key Entities in spec.md

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw 16S rRNA FASTQ, pH, and temperature logs into a unified temporal-spatial index, handling temporal mismatches and outliers.

**Independent Test**: Provide a mock directory with FASTQ, pH CSV, and Temp CSV; run the pipeline; verify a single unified CSV output and a `rejected_samples.log`.

### Tests for User Story 1

- [X] T008 [P] [US1] Contract test for data ingestion schema in `tests/contract/test_ingestion_schema.py`
- [X] T009 [P] [US1] Integration test for temporal alignment and rejection logic in `tests/integration/test_ingestion_alignment.py`

### Implementation for User Story 1

- [X] T010 [US1] Implement `code/ingestion.py` to load pH CSV and Temp CSV, validate `deployment_event`, `sensor_id`, and `coordinates` fields (Constitution Principle VI), and calculate pH SD within ±15 min window using utility from T004
- [X] T011 [US1] Implement temporal alignment logic in `code/ingestion.py`: join samples within ±15 minute window; flag mismatches in `rejected_samples.log`
- [X] T012 [US1] Implement outlier filtering in `code/ingestion.py`: Call outlier detection function from T004 to exclude pH < 1.0 or > 10.0; flag edge ranges (lower bound to 2.0, 8.5–10.0)
- [X] T013 [US1] Enforce exclusion logic: Filter out samples where `pH_heterogeneous` (SD > 0.2) is True or pH is out of range; write `data/processed/filtered_unified_sample_table.csv` for downstream use
- [X] T014 [US1] Output unified `data/processed/unified_sample_table.csv` (before filtering) with columns: sample_id, timestamp, pH, temp, pH_sd, location, fastq_path, deployment_event, sensor_id, coordinates
- [X] T015 [US1] Extend logging configuration in `code/utils.py` to add handlers for ingestion steps, using infrastructure from T004

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (metadata only; sequence data handled in US2)

---

## Phase 4: User Story 2 - Diversity Analysis and pH Correlation (Priority: P2)

**Goal**: Calculate alpha diversity (Shannon, Simpson) on rarefied data and run Linear Mixed-Effects (LME) models to correlate diversity with pH.

**Independent Test**: Run analysis on pre-calculated diversity table and pH table; verify output includes regression coefficient, p-value, and metadata flag.

### Tests for User Story 2

- [X] T016 [P] [US2] Contract test for LME output schema in `tests/contract/test_lme_output.py`
- [X] T017 [P] [US2] Integration test for non-linearity detection and warning generation in `tests/integration/test_diversity_nonlinear.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement `code/preprocessing.py` to invoke version-locked QIIME2 pipeline (via CLI wrapper) on raw FASTQ files from T014 to generate denoised sequences and OTU/ASV table (replaces custom biopython parsing) <!-- FAILED: unspecified -->
- [X] T019 [US2] Implement rarefaction logic in `code/preprocessing.py`: rarefy the OTU table to fixed depths (SC-003) to generate multiple rarefied tables
- [X] T020 [US2] Calculate alpha diversity indices (Shannon, Simpson) for each rarefied sample in `code/preprocessing.py` (depends on T019)
- [X] T021 [US2] Implement GLMM/Transformation logic (CLR or log-transform) for non-normal diversity indices; output transformed data to `data/processed/diversity_transformed.csv` for T022
- [X] T022a [US2] Implement `code/analysis.py` LME function: `diversity ~ pH + (1|site)` using `statsmodels` (depends on T021); write results to `data/processed/lme_results.csv` with columns: estimate, se, p_value, model_type
- [ ] T022b [US2] Implement fallback logic: If < 2 sites, run fixed-effects linear regression; if N < 10, run Spearman correlation; write results to `data/processed/lme_results.csv` with `model_type` column
- [ ] T023 [US2] Add residual analysis in `code/analysis.py` to detect non-linearity; output warning and suggest polynomial term if detected (US-2)
- [ ] T024 [US2] Generate `data/processed/alpha_diversity_results.csv` with pH, diversity metrics, and LME stats (estimate, SE, p-value, model_type)
- [ ] T025 [US2] Add metadata flag in output explicitly stating "associational analysis of summary statistic" (FR-003.1)
- [ ] T026 [US2] Implement sensitivity analysis for rarefaction depth (SC-003): sweep {5000, 10000, 20000} and log stability of results across thresholds to `data/processed/sensitivity_analysis_log.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Multivariate Community Clustering (Priority: P3)

**Goal**: Perform PERMANOVA and ordination (PCoA/NMDS) to test community clustering by pH, controlling for dispersion and temperature.

**Independent Test**: Provide distance matrix and pH metadata; run PERMANOVA (after betadisper); verify R², F-stat, p-value, and dispersion flag.

### Tests for User Story 3

- [ ] T027 [P] [US3] Contract test for PERMANOVA output schema in `tests/contract/test_permanova_output.py`
- [ ] T028 [P] [US3] Integration test for dispersion control and rarefaction balancing in `tests/integration/test_beta_diversity_balance.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/analysis.py` to compute Bray-Curtis dissimilarity matrix from rarefied OTU table (depends on T019)
- [ ] T030 [US3] Implement `betadisper` test (homogeneity of dispersions) in `code/analysis.py`; if p < 0.05, flag the subsequent PERMANOVA result as `dispersion_confounded` in `data/processed/beta_diversity_results.csv` (FR-004); do NOT auto-correct data
- [ ] T031 [US3] Implement PERMANOVA test on Bray-Curtis matrix with pH as predictor; if groups are unbalanced (>2x difference), perform a subsampling step ONLY for the purpose of balancing the test (as per US-3), but log this as a data modification step; otherwise proceed without subsampling
- [ ] T032 [US3] Implement ordination logic: PCoA first; if stress > 0.2, fallback to NMDS (FR-005)
- [ ] T033 [US3] Implement VIF collinearity diagnostic for pH vs. temperature; if VIF > 5, perform dbRDA (variance partitioning) to isolate pH effect; log results and output `data/processed/dbRDA_results.csv` (SC-004)
- [ ] T034 [US3] Generate ordination plot (PCoA/NMDS) colored by pH levels using `matplotlib`/`seaborn`
- [ ] T035 [US3] Generate `data/processed/beta_diversity_results.csv` with PERMANOVA stats (R², F, p), dispersion flags, and dbRDA variance partitioning
- [ ] T036 [P] [US3] Generate `results/figures/` with all ordination plots and diversity vs. pH scatterplots

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Validation (Polish)

**Purpose**: Generate final reports, validate success criteria, and ensure reproducibility.

- [ ] T037 [P] Generate `results/summary_report.md` aggregating LME, PERMANOVA, and dbRDA results. Required sections: 1. LME Summary, 2. PERMANOVA Summary, 3. dbRDA Variance Partitioning, 4. Sensitivity Analysis
- [ ] T038 [P] Create `results/figures/` directory with all ordination plots and diversity vs. pH scatterplots
- [ ] T039 [P] Run full pipeline end-to-end on `tests/integration/mock_data/` to verify SC-005 (runtime < 6 hours on 2 CPU/7GB RAM); explicitly log runtime and memory usage to `state/runtime_log.json` and assert the <6h limit programmatically
- [ ] T040 [P] Validate all outputs against `contracts/` schemas and generate `state/` checksums
- [ ] T041 [P] Update `README.md` with usage instructions and data requirements

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

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
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence