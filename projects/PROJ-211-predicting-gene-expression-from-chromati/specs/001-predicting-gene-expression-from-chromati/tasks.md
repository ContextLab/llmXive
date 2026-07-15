# Tasks: Predicting Gene Expression from Chromatin Accessibility in Human Cells

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

- [X] T001 Create project structure per implementation plan in `projects/PROJ-211-predicting-gene-expression-from-chromati/` by creating directories: `code/`, `data/raw/`, `data/processed/`, `data/models/`, `logs/`, `tests/contract/`, `tests/integration/`, `tests/unit/`, `docs/`, `contracts/`.

- [X] T002 Initialize Python 3.11 project with `scikit-learn`, `pandas`, `numpy`, `requests`, `pyyaml` in `requirements.txt`

- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `.pre-commit-config.yaml`

- [ ] T004b [P] Fix corrupted SC-005 text in `spec.md` by replacing the unrelated text with the measurable resource thresholds (Several CPU, sufficient RAM, 6h) defined in the Constitution. **Deliverable**: Valid `spec.md` with corrected SC-005. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data schema contracts in `specs/001-gene-regulation/contracts/` (`dataset_schema.schema.yaml`, `output_schema.schema.yaml`) by generating schema files based on `data-model.md` definitions.

- [X] T005 [P] Implement deterministic synthetic data generator in `code/generate_data.py` (seeded, schema-valid, CPU-feasible) to produce `data/raw/synthetic_counts.csv` and `data/raw/synthetic_peaks.bed` with Seed=42, dimensions [deferred] genes x cell lines x [deferred] peaks. **Deliverable**: `code/generate_data.py`.

- [X] T006 [P] Create base utility module `code/utils.py` for logging, checksumming, and config loading. **Function**: `checksum_file(path)` must be implemented and tested.

- [ ] T007 Setup directory structure for `data/raw/`, `data/processed/`, `data/models/`, `logs/`

- [X] T008 Configure error handling and retry logic (multiple attempts, fixed time intervals) for data fetching in `code/utils.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and preprocess paired multiomic data (Priority: P1) 🎯 MVP

**Goal**: Download paired RNA-seq and DNase-seq/ATAC-seq count data for ≥5 human cell lines, preprocess accessibility signal within ±50kb windows, and filter genes.

**Independent Test**: Verify pipeline produces matching gene matrices (accessibility features and expression values) that fit within 7GB RAM.

### Tests for User Story 1 (OPTIONAL)

- [ ] T009 [P] [US1] Contract test for synthetic data schema validation in `tests/contract/test_data_schema.py`
- [ ] T010 [P] [US1] Integration test for data download and filtering pipeline in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T011 [US1] Execute `generate_data.py` to produce paired RNA-seq and DNase-seq counts for GM12878, K562, HMEC, IMR90, HepG2 with dimensions ≤10,000 peaks × 5 cell lines, ≥10,000 genes for CI validation. **Note**: This is for CI only. **Deliverable**: `data/raw/synthetic_counts.csv`, `data/raw/synthetic_peaks.bed`. **Checksum**: Run `utils.checksum_file()` on outputs and record in `logs/checksums.txt`.

- [~] T011b [US1] Implement FR-001: ENCODE download logic in `code/download_encode.py` to fetch real paired RNA-seq and DNase-seq/ATAC-seq count data for ≥5 human cell lines from the ENCODE portal. **Deliverable**: `code/download_encode.py` and `data/raw/encode_counts.csv`, `data/raw/encode_peaks.bed` (or equivalent). **Checksum**: Run `utils.checksum_file()` on outputs and record in `logs/checksums.txt`.

- [ ] T012.2 [US1] Validate Python implementation logic against a small synthetic bedtools test set to ensure the Python fallback matches `bedtools coverage` output. **Input**: Synthetic coordinates. **Deliverable**: `logs/validation_report.txt` confirming match. **Dependency**: Must pass before T012.1 is considered production-ready.

- [ ] T012.1 [US1] Execute `bedtools coverage` to aggregate accessibility signal within ±50kb of TSS using the synthetic peak and gene coordinate files. **Command**: `bedtools coverage -a genes.bed -b peaks.bed -f 0.01 -s`. **Deliverable**: `data/processed/tss_aggregated_features.csv`. **Checksum**: Run `utils.checksum_file()` on output and record in `logs/checksums.txt`. **Note**: This is the production artifact.

- [ ] T013 [US1] Implement gene filtering in `code/preprocess.py` to filter genes with zero expression in all samples and apply a logarithmic pseudocount transformation (log(counts + 1)) to handle zero values. **Input**: `data/processed/tss_aggregated_features.csv`. **Deliverable**: `data/processed/filtered_expression.csv`. **Checksum**: Run `utils.checksum_file()` on output.

- [ ] T014 [US1] Implement missing value imputation in `code/preprocess.py` using median imputation per peak. **Input**: `data/processed/filtered_expression.csv`. **Deliverable**: `data/processed/imputed_expression.csv`. **Checksum**: Run `utils.checksum_file()` on output.

- [~] T015 [US1] Select top N variable peaks based on variance across samples in `code/preprocess.py`, where N=1000 (configurable via CLI). **Input**: `data/processed/imputed_expression.csv`. **Deliverable**: `data/processed/variable_peaks.csv`. **Checksum**: Run `utils.checksum_file()` on output.

- [~] T016 [US1] {{claim:c_912ac751}} in `code/preprocess.py` by calculating the coefficient of variation across all cell lines. **Input**: `data/processed/imputed_expression.csv`. **Deliverable**: `data/processed/housekeeping_genes.csv`. **Checksum**: Run `utils.checksum_file()` on output.

- [~] T017 [US1] Define 500 cell-type-specific genes with variance > 0.5 in `code/preprocess.py` by calculating expression variance across cell lines. **Input**: `data/processed/imputed_expression.csv`. **Deliverable**: `data/processed/cell_type_specific_genes.csv`. **Checksum**: Run `utils.checksum_file()` on output.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and validate interpretable regression models (Priority: P2)

**Goal**: Train Elastic Net models, perform cross-validation, and calculate correlation coefficients with statistical corrections.

**Independent Test**: Verify each cell line produces a trained model, cross-validation scores, and a correlation matrix with p-values.

### Tests for User Story 2 (OPTIONAL)

- [X] T019 [P] [US2] Contract test for model output schema in `tests/contract/test_model_schema.py`
- [X] T020 [P] [US2] Integration test for training and cross-validation loop in `tests/integration/test_training_loop.py`

### Implementation for User Story 2

- [~] T021 [US2] Implement Elastic Net training in `code/train.py` (α=0.5, λ via CV) for each cell line. **Input**: `data/processed/variable_peaks.csv`. **Deliverable**: `data/models/elastic_net_{cell_line}.pkl`.

- [~] T022 [US2] Implement k-fold cross-validation loop in `code/train.py` with k=5 (document justification for k=5 being a 'reasonable number' in code comments). **Deliverable**: Cross-validation scores in `data/processed/cv_scores.json`.

- [~] T023 [US2] Calculate Pearson correlation between predicted and actual expression in `code/evaluate.py`. **Deliverable**: Correlation matrix in `data/processed/correlations.csv`.

- [~] T024 [US2] Implement Bonferroni correction for p-values in `code/evaluate.py` (FR-006). **Deliverable**: Corrected p-values in `data/processed/pvalues_corrected.csv`.

- [~] T025 [US2] Calculate and report R² for housekeeping genes per cell line in `code/evaluate.py` (FR-009, SC-001) using the gene list from `data/processed/housekeeping_genes.csv`. **Deliverable**: `data/processed/housekeeping_r2.csv`.

- [~] T026 [US2] Implement external validation (train on subset, test on held-out cell line) in `code/evaluate.py` (FR-014, SC-006). **Inputs**: gene lists from `data/processed/housekeeping_genes.csv` and `data/processed/cell_type_specific_genes.csv`. **Deliverable**: Report the R² for the held-out line in `data/processed/external_validation_r2.csv`.

- [~] T027 [US2] Log memory usage and runtime to `logs/` to verify CPU/RAM constraints (SC-005). **Deliverable**: `logs/profiling.log`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze feature importance and report regulatory insights (Priority: P3)

**Goal**: Extract feature importance, map peaks to TSS, and compare model performance across gene categories.

**Independent Test**: Verify feature importance rankings are produced, TSS-proximal regions appear in top features, and performance gap is reported.

### Tests for User Story 3 (OPTIONAL)

- [X] T028 [P] [US3] Contract test for interpretation output schema in `tests/contract/test_interpretation_schema.py`
- [X] T029 [P] [US3] Integration test for feature importance and TSS mapping in `tests/integration/test_interpretation.py`

### Implementation for User Story 3

- [~] T030 [US3] Extract non-zero coefficient features and rank by absolute magnitude in `code/interpret.py` (FR-007). **Deliverable**: `data/processed/feature_importance.csv`.

- [~] T031 [US3] Map peak coordinates to genomic location relative to nearest TSS in `code/interpret.py` (FR-008). **Deliverable**: `data/processed/peak_annotations.csv`.

- [~] T032 [US3] Calculate percentage of top-100 features within ±10kb of TSS in `code/interpret.py` (SC-003). **Deliverable**: `data/processed/tss_proximity_stats.json`.

- [~] T033 [US3] Calculate and report performance gap (ΔR²) between housekeeping and cell-type-specific genes in `code/interpret.py` (FR-010, SC-004). **Inputs**: R² values from T025 and gene lists from T016/T017. **Deliverable**: `data/processed/performance_gap.json`.

- [ ] T034 [US3] Generate summary report comparing model performance across cell types and gene categories in `code/interpret.py`. **Deliverable**: `docs/regulatory_insights_report.md`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Research & Documentation (Revision & Insights)

**Purpose**: Address reviewer concerns and document findings

- [ ] T035 [US1] Draft and apply text to `spec.md` and `plan.md` to include caveat that prediction is a "first-order approximation" and not a causal law, referencing bulk profile limitations. **Deliverable**: Updated `spec.md` and `plan.md`.

- [ ] T036 [US3] Draft text for `docs/regulatory_context.md` to document ENCODE consortium findings regarding regulatory genome complexity and discussion on "dappled models" vs. "unified laws". **Deliverable**: `docs/regulatory_context.md`.

- [ ] T037 Run `quickstart.md` validation. **Pass/Fail**: Execute `quickstart.md`; verify exit code 0 and that all generated artifacts exist in `data/`.

---

## Phase 7: Review & Documentation (General)

**Purpose**: Final documentation and limitations

- [ ] T045 [US1] Draft text for `docs/limitations.md` explicitly stating that bulk chromatin accessibility profiles provide a "first-order approximation" of gene regulation and do not capture single-cell heterogeneity. **Deliverable**: `docs/limitations.md`.

- [ ] T046 [US1] Apply drafted text to `docs/limitations.md`.

- [ ] T047 [US3] Implement analysis in `code/interpret.py` to calculate "unexplained variance" (1 - R²) and correlate with known measures of cell-type heterogeneity (if available) or explicitly report this limitation. **Deliverable**: Updated `data/processed/unexplained_variance.json`.

- [ ] T048 [US3] Add a dedicated section to `docs/regulatory_context.md` titled "Dappled Models vs. Unified Laws" that synthesizes the ENCODE consortium's findings on regulatory complexity. **Deliverable**: Updated `docs/regulatory_context.md`.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050 [P] Documentation updates in `docs/` based on profiling results.

- [ ] T051 Refactor `code/preprocess.py` to reduce memory usage based on `logs/` profiling data.

- [ ] T052 Optimize cross-validation loop in `code/train.py` to reduce runtime based on `logs/` profiling data.

- [ ] T053 [P] Additional unit tests in `tests/unit/` for edge cases identified in integration tests.

- [ ] T054 Security hardening (PII scan verification).

- [ ] T055 Run `quickstart.md` validation again after optimizations.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Integration test for data download and filtering pipeline in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Execute bedtools coverage to aggregate signal in data/processed/tss_aggregated_features.csv"
Task: "Implement gene filtering in code/preprocess.py"
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
- **Constraint**: All data generation must use synthetic data with fixed seeds to ensure CPU-only CI feasibility (no external API dependencies), but production pipeline must implement FR-001 (T011b).
- **Constraint**: No GPU/CUDA; All models run on 2 CPU cores, ≤7GB RAM.
- **Revision Note**: Phase 7 tasks are mandatory to address standard limitations and documentation, replacing the previous hallucinated reviewer tasks.