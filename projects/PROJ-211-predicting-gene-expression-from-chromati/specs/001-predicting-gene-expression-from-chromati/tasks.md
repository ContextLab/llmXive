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

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data schema contracts in `specs/001-gene-regulation/contracts/` (`dataset_schema.schema.yaml`, `output_schema.schema.yaml`) by generating schema files based on `data-model.md` definitions.

- [X] T005 [P] Implement deterministic synthetic data generator in `code/generate_data.py` (seeded, schema-valid, CPU-feasible) to produce `data/raw/synthetic_counts.csv` and `data/raw/synthetic_peaks.bed` with Seed=42, dimensions [deferred] genes x cell lines x [deferred] peaks. **Deliverable**: `code/generate_data.py`.

- [X] T006 [P] Create base utility module `code/utils.py` for logging, checksumming, and config loading. **Function**: `checksum_file(path)` must be implemented and tested.

- [X] T008 Configure error handling and retry logic (multiple attempts, fixed time intervals) for data fetching in `code/utils.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and preprocess paired multiomic data (Priority: P1) 🎯 MVP

**Goal**: Download paired RNA-seq and DNase-seq/ATAC-seq count data for ≥5 human cell lines., Process accessibility signal within ±50kb windows., and filter genes.

**Independent Test**: Verify pipeline produces matching gene matrices (accessibility features and expression values) that fit within 7GB RAM.

### Tests for User Story 1 (OPTIONAL)

- [X] T009 [P] [US1] Contract test for synthetic data schema validation in `tests/contract/test_data_schema.py`
- [X] T010 [P] [US1] Integration test for data download and filtering pipeline in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T010 [US1] Implement ENCODE data download logic in `code/download_encode.py` to fetch paired RNA-seq and DNase-seq/ATAC-seq count data for a diverse panel of cell lines. **Input**: ENCODE API endpoints. **Deliverable**: `code/download_encode.py` and `data/raw/encode_counts.csv`, `data/raw/encode_peaks.bed`. **Note**: If ENCODE API fails, fall back to synthetic data generation (T011b) for CI validation only. **Checksum**: Run `utils.checksum_file()` on outputs. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->

- [ ] T011 [US1] Execute `generate_data.py` to produce paired RNA-seq and DNase-seq counts for GM12878, K562, HMEC, IMR90, and HepG2 with Seed=42 for CI validation if real data is unavailable. **Deliverable**: `data/raw/synthetic_counts.csv`, `data/raw/synthetic_peaks.bed`. **Checksum**: Run `utils.checksum_file()` on outputs and record in `logs/checksums.txt`.

- [ ] T012.0 [US1] Implement Python windowing logic in `code/preprocess.py` to aggregate accessibility signal within ±50kb of TSS using synthetic peak and gene coordinate files. **Input**: `data/raw/synthetic_peaks.bed`, `data/raw/synthetic_genes.bed`. **Deliverable**: `code/preprocess.py` function `aggregate_signal`.

- [ ] T012.1 [US1] Implement unit tests in `tests/unit/test_preprocess.py` to validate Python windowing logic against synthetic in-memory coordinates. **Input**: Synthetic coordinates. **Deliverable**: `tests/unit/test_preprocess.py`. **Dependency**: Must pass before T012.0 is considered production-ready.

- [ ] T012.5 [US1] Merge aggregated peak features with gene expression counts to form the joint matrix required for filtering. **Input**: `data/processed/tss_aggregated_features.csv`, `data/raw/encode_counts.csv` (or synthetic equivalent). **Deliverable**: `data/processed/merged_matrix.csv`. **Checksum**: Run `utils.checksum_file()` on output.

- [ ] T013 [US1] Implement gene filtering in `code/preprocess.py` to filter genes with zero expression in all samples and apply a logarithmic pseudocount transformation to handle zero values. **Input**: `data/processed/merged_matrix.csv`. **Deliverable**: `data/processed/filtered_expression.csv`. **Checksum**: Run `utils.checksum_file()` on output. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

- [ ] T014 [US1] Implement missing value imputation in `code/preprocess.py` using median imputation per peak. **Input**: `data/processed/filtered_expression.csv`. **Deliverable**: `data/processed/imputed_expression.csv`. **Checksum**: Run `utils.checksum_file()` on output. <!-- FAILED: unspecified -->

- [ ] T016 [US1] Define housekeeping genes in `code/preprocess.py` by calculating the coefficient of variation across all cell lines using a configurable threshold (default CV < 0.2). **Input**: `data/processed/imputed_expression.csv`. **Deliverable**: `data/processed/housekeeping_genes.csv`. **Checksum**: Run `utils.checksum_file()` on output.

- [ ] T016b [US1] Define cell-type-specific genes in `code/preprocess.py` by selecting genes with high coefficient of variation (CV > 0.5) across cell lines. **Input**: `data/processed/imputed_expression.csv`. **Deliverable**: `data/processed/cell_type_specific_genes.csv`. **Checksum**: Run `utils.checksum_file()` on output. <!-- FAILED: unspecified -->

- [ ] T016c [US1] Filter the feature matrix and target vector to only housekeeping genes in `code/preprocess.py` for specific metric calculation. **Input**: `data/processed/imputed_expression.csv`, `data/processed/housekeeping_genes.csv`. **Deliverable**: `data/processed/housekeeping_matrix.csv`. **Checksum**: Run `utils.checksum_file()` on output.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and validate interpretable regression models (Priority: P2)

**Goal**: Train Elastic Net models, perform cross-validation, and calculate correlation coefficients with statistical corrections.

**Independent Test**: Verify each cell line produces a trained model, cross-validation scores, and a correlation matrix with p-values.

### Tests for User Story 2 (OPTIONAL)

- [X] T019 [P] [US2] Contract test for model output schema in `tests/contract/test_model_schema.py`
- [X] T020 [P] [US2] Integration test for training and cross-validation loop in `tests/integration/test_training_loop.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement Elastic Net training in `code/train.py` (α=0.5, λ via internal k-fold cross-validation) for each cell line. **Input**: `data/processed/imputed_expression.csv`. **Deliverable**: `data/models/elastic_net_{cell_line}.pkl`, `data/processed/cv_scores.json`.

- [~] T023 [US2] Calculate Pearson correlation between predicted and actual expression in `code/evaluate.py`. **Deliverable**: Correlation matrix in `data/processed/correlations.csv`.

- [ ] T024 [US2] Apply Bonferroni correction to p-values in `code/evaluate.py` (FR-006) using `scipy.stats`. **Deliverable**: Corrected p-values in `data/processed/pvalues_corrected.csv`.

- [ ] T025 [US2] Calculate and report R² for housekeeping genes per cell line in `code/evaluate.py` (FR-009, SC-001) using the gene list from `data/processed/housekeeping_matrix.csv`. **Deliverable**: `data/processed/housekeeping_r2.csv`.

- [ ] T025b [US2] Calculate and report R² for cell-type-specific genes per cell line in `code/evaluate.py`. **Input**: `data/processed/cell_type_specific_genes.csv`. **Deliverable**: `data/processed/cell_type_specific_r2.csv`.

- [ ] T026 [US2] Implement external validation in `code/evaluate.py` (SC-006) by training on multiple cell lines (e.g., GM, K562, HMEC, IMR90) and testing on a held-out cell line (e.g., HepG2). **Inputs**: Full model, held-out cell line data. **Deliverable**: Report the R² for the held-out line in `data/processed/external_validation_r2.csv`.

- [ ] T027 [US2] Log memory usage and runtime to `logs/` to verify CPU/RAM constraints (SC-005). **Deliverable**: `logs/profiling.log`. **Success Criterion**: Verify runtime ≤ 2 hours per cell line and RAM ≤ 7GB.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze feature importance and report regulatory insights (Priority: P3)

**Goal**: Extract feature importance, map peaks to TSS, and compare model performance across gene categories.

**Independent Test**: Verify feature importance rankings are produced, TSS-proximal regions appear in top features, and performance gap is reported.

### Tests for User Story 3 (OPTIONAL)

- [X] T028 [P] [US3] Contract test for interpretation output schema in `tests/contract/test_interpretation_schema.py`
- [X] T029 [P] [US3] Integration test for feature importance and TSS mapping in `tests/integration/test_interpretation.py`

### Implementation for User Story 3

- [ ] T030 [US3] Extract non-zero coefficient features and rank by absolute magnitude in `code/interpret.py` (FR-007). **Input**: `data/models/elastic_net_{cell_line}.pkl`. **Deliverable**: `data/processed/feature_importance.csv` (Peak IDs).

- [ ] T031 [US3] Map peak coordinates to genomic location relative to nearest TSS in `code/interpret.py` (FR-008). **Input**: `data/processed/feature_importance.csv` (Peak IDs), `data/processed/tss_aggregated_features.csv`. **Deliverable**: `data/processed/peak_annotations.csv`.

- [ ] T032 [US3] Calculate percentage of top-100 features within ±10kb of TSS in `code/interpret.py` (SC-003). **Input**: `data/processed/peak_annotations.csv`. **Deliverable**: `data/processed/tss_proximity_stats.json`.

- [ ] T033 [US3] Calculate and report performance gap (ΔR²) between housekeeping and cell-type-specific genes in `code/interpret.py` (FR-010, SC-004). **Inputs**: R² values from T025 (`housekeeping_r2.csv`) and T025b (`cell_type_specific_r2.csv`). **Deliverable**: `data/processed/performance_gap.json`.

- [ ] T034 [US3] Generate summary report comparing model performance across cell types and gene categories in `code/interpret.py`. **Deliverable**: `docs/regulatory_insights_report.md`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Research & Documentation (Revision & Insights)

**Purpose**: Address reviewer concerns and document findings

- [ ] T047 [US3] Document the limitation of "unexplained variance" and lack of single-cell heterogeneity metrics in `docs/regulatory_insights_report.md` (FR-010, SC-001). Explicitly state that the model provides a "first-order approximation" and cannot capture cell-type heterogeneity due to bulk data constraints. **Deliverable**: Updated `docs/regulatory_insights_report.md`.

- [ ] T037 Run `quickstart.md` validation. **Pass/Fail**: Execute `quickstart.md`; verify exit code 0 and that all generated artifacts exist in `data/`.

---

## Phase 7: Review & Documentation (General)

**Purpose**: Final documentation and limitations

- [ ] T048 [US3] Add a dedicated section to `docs/regulatory_context.md` titled "Dappled Models vs. Unified Laws" that synthesizes the ENCODE consortium's findings on regulatory complexity. **Deliverable**: Updated `docs/regulatory_context.md`.

- [ ] T050 [US3] Add a subsection to `docs/regulatory_context.md` titled "Correlation vs. Causation" that clarifies the statistical nature of the Elastic Net findings and explicitly warns against inferring direct causal regulatory links from these bulk correlations. **Deliverable**: Updated `docs/regulatory_context.md`.

- [ ] T057 [US3] Update `docs/regulatory_context.md` to include a new subsection "The Bulk Averaging Artifact" that explicitly quantifies how bulk profiles smooth over single-cell heterogeneity, citing the ENCODE finding that regulatory landscapes are cell-state specific. **Deliverable**: Updated `docs/regulatory_context.md`.

- [ ] T058 [US3] Modify the final summary report generation in `code/interpret.py` to automatically prepend a "Causality Warning" header to any output file containing correlation metrics, stating that the model identifies statistical associations, not causal regulatory mechanisms. **Deliverable**: Updated `code/interpret.py` and example output in `docs/regulatory_insights_report.md`.

- [ ] T059 [US3] Add a validation task to `tests/integration/test_interpretation.py` that asserts the presence of the "first-order approximation" caveat in all generated report headers. **Deliverable**: Updated `tests/integration/test_interpretation.py`.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T051 [P] Documentation updates in `docs/` based on profiling results.

- [ ] T052 Refactor `code/preprocess.py` to reduce memory usage based on `logs/` profiling data.

- [ ] T053 Optimize cross-validation loop in `code/train.py` to reduce runtime based on `logs/` profiling data.

- [ ] T054 [P] Additional unit tests in `tests/unit/` for edge cases identified in integration tests.

- [ ] T055 Security hardening (PII scan verification).

- [ ] T056 Run `quickstart.md` validation again after optimizations.

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
Task: "Execute Python windowing to aggregate signal in data/processed/tss_aggregated_features.csv"
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
- **Constraint**: All data generation must use synthetic data with fixed seeds to ensure CPU-only CI feasibility (no external API dependencies) ONLY IF real data fetch fails.
- **Constraint**: No GPU/CUDA.
- **Revision Note**: Phase 7 tasks T057-T059 are now standard documentation tasks addressing "Bulk Averaging" and "Correlation vs Causation" as required by the spec, removing the fabricated "Freeman Dyson" review reference.
- **Revision Note**: T010 now implements real ENCODE data download, satisfying FR-001.
- **Revision Note**: T026 now correctly implements cell-line holdout validation for SC-006.