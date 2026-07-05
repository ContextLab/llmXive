# Tasks: Predicting Coral Resilience to Thermal Stress Using Publicly Available Genomic Data

**Input**: Design documents from `/specs/001-predict-coral-resilience/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001a [P] Create project directory structure: `code/`, `tests/`, `data/`, `results/`, `docs/`
- [ ] T001b [P] Create `__init__.py` files in `code/`, `code/data/`, `code/analysis/`, `code/viz/`, `tests/`, `tests/unit/`, `tests/contract/`, `tests/integration/`
- [ ] T002 Initialize Python 3.11 project with dependencies: plink2 (install via `apt-get install plink2` or conda-forge), scikit-learn, pandas, numpy, matplotlib, requests, pyyaml, pytest, memory-profiler
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Create `code/config.py` with paths, thresholds (MAF > 0.05, missingness < 10%), and random seeds
- [ ] T005 [P] Implement `code/utils.py` for logging, error handling, and checksum validation
- [~] T006 [P] Setup `tests/` directory structure (unit/, integration/, contract/)
- [~] T007 Create base data model definitions in `code/data/`
- [~] T008 Configure environment variable management for NCBI API keys (if required) or direct URL access

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Quality Filtering (Priority: P1) 🎯 MVP

**Goal**: Download *Acropora millepora* VCFs from NCBI PRJNA[project identifier], validate metadata, and produce a memory-tractable PLINK binary dataset.

**Independent Test**: The pipeline can be executed end-to-end starting from raw download links, producing a filtered PLINK binary file set (`.bed`, `.bim`, `.fam`) and a summary report, without requiring association testing logic.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Contract test for VCF parsing integrity in `tests/contract/test_vcf_parsing.py`
- [~] T011 [P] [US1] Integration test for download -> filter -> PLINK conversion flow in `tests/integration/test_ingest_flow.py` <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [~] T012 [US1] Implement `code/data/ingest.py` to download VCFs from NCBI BioProject (URL: `ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByStudy/sra/SRP/[Study_ID]/`) and verify checksums
- [ ] T013a [US1] Implement `code/data/phenotype.py` to parse metadata, check for the existence of `avg_temp_survival` column; if missing, halt with specific error "Missing required proxy column avg_temp_survival"; if present, derive population-level proxy using mean of `avg_temp_survival` (per plan.md "Critical Pivot")
- [ ] T013b [US1] Implement validation logic in `code/data/phenotype.py` to explicitly check for binary survival labels; if absent AND no valid proxy is derived, halt with specific error "No valid phenotype data found for GWAS" as per US-1 Scenario 3
- [ ] T014 [US1] Implement `code/data/filter.py` to apply MAF > 0.05 and missingness < 10% filters, outputting filtered PLINK binary files (`.bed`, `.bim`, `.fam`)
- [ ] T015 [US1] Implement error handling in `code/data/ingest.py` to halt on corrupted VCFs with specific file identification
- [ ] T016 [US1] Add validation logic to ensure output dataset size fits within 7 GB RAM constraint
- [ ] T017 [US1] Generate `data/reports/ingestion_summary.md` listing removed variants and filtering stats

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (subject to T013b validation)

---

## Phase 4: User Story 2 - Genome-Wide Association Analysis (Priority: P2)

**Goal**: Execute PCA for stratification correction and run PLINK regression to identify significant SNPs, applying FDR correction.

**Independent Test**: The analysis script can be run on the filtered dataset from User Story 1, producing a list of significant SNPs (p-values), a Manhattan plot, and a QQ-plot, independent of the pathway enrichment step.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for PCA covariate output in `tests/contract/test_pca_covariates.py`
- [ ] T019 [P] [US2] Integration test for GWAS -> FDR -> Plot generation flow in `tests/integration/test_gwas_flow.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/analysis/pca.py` to run PCA on filtered PLINK data and extract a subset of Principal Components as covariates (FR-009). **Note**: This task MUST complete before T021.
- [ ] T021 [US2] Implement `code/analysis/gwas.py` to run PLINK regression: detect phenotype type from `code/data/phenotype.py` (T013b); if binary labels exist, run `--logistic`; if population proxy exists, run `--linear`; if neither, halt with error. Apply FDR correction (FR-004) and generate results (FR-003). **Dependency**: Requires output from T013b and T020.
- [ ] T022 [US2] Implement FDR correction logic in `code/analysis/gwas.py` to calculate q-values and filter for q < 0.05 (FR-004)
- [ ] T023 [US2] Handle null result case: if no SNPs meet q < 0.05, generate "No significant associations found" report (FR-007)
- [ ] T024 [US2] Implement `code/viz/plots.py` to generate Manhattan plot and QQ-plot from GWAS results (FR-006)
- [ ] T025 [US2] Calculate genomic inflation factor (lambda) from GWAS results, record the value in `results/validation_report.md`, assert lambda <= 1.05, and halt the pipeline if exceeded; generate validation report for SC-002. **Requirement**: Must report the measured lambda value, not just halt.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (US2 depends on US1's phenotype validation)

---

## Phase 5: User Story 3 - Pathway Enrichment and Visualization (Priority: P3)

**Goal**: Map significant SNPs to genes, cross-reference with homologous species (*Nematostella vectensis*), and perform pathway enrichment analysis.

**Independent Test**: The enrichment script can be run on a pre-defined list of significant SNPs to produce the final visualization and biological interpretation report.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for pathway mapping confidence in `tests/contract/test_enrichment_mapping.py`
- [ ] T027 [P] [US3] Integration test for SNP -> Gene -> Pathway enrichment flow in `tests/integration/test_enrichment_flow.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/analysis/enrichment.py` to map significant SNPs to genes and query g:Profiler or homologous database (FR-005)
- [ ] T029 [US3] Implement cross-species validation logic in `code/analysis/enrichment.py` to map to *Nematostella vectensis* using BLASTp, calculate E-values, and compute a confidence score as `normalized(-log10(E-value))` (0-1 scale) to report annotation confidence (FR-008, SC-006). **Dependency**: Requires gene list from T028.
- [ ] T030 [US3] Calculate adjusted p-values for pathway enrichment and filter for p < 0.05
- [ ] T031 [US3] Handle null enrichment case: report "No significant pathway enrichment found" with unannotated SNPs (US-3 Scenario 2)
- [ ] T032 [US3] Generate `results/pathway_summary.md` with identified heat-shock/oxidative stress pathways and confidence scores
- [ ] T033 [US3] Generate `results/final_manhattan.png` using matplotlib to visualize Manhattan plot with pathway highlights

**Checkpoint**: All user stories should now be independently functional (subject to dependencies)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `docs/` and `README.md`
- [ ] T035 Refactor `code/data/ingest.py` to use streaming/chunking if `memory_profiler` indicates peak usage > 6GB (SC-001)
- [ ] T036 Performance optimization to ensure total runtime ≤ 5 hours (SC-004)
- [ ] T037 [P] Additional unit tests for filtering thresholds and PCA logic in `tests/unit/`
- [ ] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T039 Verify all artifacts have content hashes and `state/` is updated

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
- **User Story 2 (P2)**: Requires filtered PLINK output from US1 (T014), phenotype logic (T013a/T013b), and PCA covariates (T020)
- **User Story 3 (P3)**: Requires significant SNP list from US2 (T022)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, T010, T011, T012, T013a, T013b, T014, T015, T016, T017 can run in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **only after** their specific prerequisites are met.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for VCF parsing integrity in tests/contract/test_vcf_parsing.py"
Task: "Integration test for download -> filter -> PLINK conversion flow in tests/integration/test_ingest_flow.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/ingest.py to download VCFs..."
Task: "Implement code/data/phenotype.py to parse metadata..."
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
 - Developer B: User Story 2 (after US1 phenotype validation is ready)
 - Developer C: User Story 3 (after US2 is ready)
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
- **Critical Constraint**: All tasks must run on CPU-only CI (limited cores, 7 GB RAM, no GPU). Do not use 8-bit quantization or deep learning.
- **Data Integrity**: All datasets must be real (NCBI PRJNA); no synthetic data fabrication.
- **Dependency Correction**: T021 depends on T013b and T020; T029 depends on T028. These are NOT parallel tasks.
- **Validation**: T025 and T029 must produce measurable reports, not just pass/fail gates.