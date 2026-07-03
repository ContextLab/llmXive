# Tasks: Predicting Plant Defense Allocation from Publicly Available Transcriptomic Data

**Input**: Design documents from `/specs/001-plant-defense-allocation/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`src/data`, `src/analysis`, `src/utils`, `src/cli`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with pinned `requirements.txt` (including `rpy2`, `biopython`, `scikit-learn`, `ete3`, `pydantic`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement configuration management (`src/utils/config.py`) for paths, seeds, and thresholds
- [ ] T005 [P] Implement logging and provenance tracking (`src/utils/logger.py`, `src/utils/provenance.py`)
- [ ] T006 [P] Create base data schemas (`data-model.md` derived) using `pydantic` in `src/utils/schemas.py`
- [ ] T007 Setup directory structure for `data/raw`, `data/processed`, `data/traits`, `data/manifests`, and `data/synthetic`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Acquire public RNA-seq data, preprocess into normalized TPM matrices, and apply batch correction.

**Independent Test**: Verify output files match FASTA/TPM specs, batch correction reduces CV ≥20% for housekeeping genes, and low-coverage samples are flagged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T008 [P] [US1] Unit test for FASTQ download validation in `tests/unit/test_download.py`
- [ ] T009 [P] [US1] Unit test for batch correction metric calculation in `tests/unit/test_batch_correction.py`
- [ ] T010 [P] [US1] Integration test for full preprocessing pipeline on a single synthetic study in `tests/integration/test_preprocess.py`

### Implementation for User Story 1

- [ ] T015 [US1] Create `src/data/synthetic_generator.py` to generate structurally valid synthetic TPM matrices for prototype validation. **Must produce `data/synthetic/synthetic_manifest.json` with distinct provenance flags and checksums to satisfy Constitution Principle VI. Synthetic data must NEVER be written to `data/raw/`.**
- [ ] T011 [US1] Implement `src/data/download.py` to fetch FASTQ from NCBI GEO/SRA. **If real data fetch fails, trigger T015 to generate synthetic data in `data/synthetic/` (NOT `data/raw/`). Ensure distinct provenance logging for synthetic vs. real data in `data/manifests`. Real data must be archived in `data/raw/` with checksums.**
- [ ] T012 [US1] Implement `src/data/preprocess.py` wrappers for `fastp`, `HISAT2`, and `featureCounts` (CPU-optimized, streaming)
- [ ] T013 [US1] Implement `src/data/batch_correction.py` with ComBat-seq logic. **Use the full enumerated list of 53 genes from FR-003 (ACT2, ACT7, GAPDH, UBQ10, EF1a, TUB6, TUB1, PP2A, SAND, CYP79D16, CYP79D15, CYP79D17, CYP83A1, CYP83B1, CYP96A1, CYP96A2, CYP96A3, CYP71A1, CYP71A2, CYP71A3, CYP71A4, CYP71A5, CYP71A6, CYP71A7, CYP71A8, CYP71A9, CYP71A10, CYP71A11, CYP71A12, CYP71A13, CYP71A14, CYP71A15, CYP71A16, CYP71A17, CYP71A18, CYP71A19, CYP71A20, CYP71A21, CYP71A22, CYP71A23, CYP71A24, CYP71A25, CYP71A26, CYP71A27, CYP71A28, CYP71A29, CYP71A30, CYP71A31, CYP71A32) to select the most stable subset using GeNorm M-value.**
- [ ] T014 [US1] Implement QC logic to exclude studies with <2 replicates or missing tissue metadata

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Differential Expression and Feature Derivation (Priority: P2)

**Goal**: Compute differential expression, derive herbivore-response vectors, and perform pathway aggregation.

**Independent Test**: Verify DESeq2 identifies DE genes correctly, response vectors are consistent across folds, and pathway aggregation reduces features to ≤50.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for DE gene selection logic (FDR < 0.05, |log2FC| > 1) in `tests/unit/test_de_analysis.py`
- [ ] T017 [P] [US2] Unit test for pathway aggregation mapping in `tests/unit/test_feature_engineering.py`

### Implementation for User Story 2

- [ ] T018 [US2] Implement `src/analysis/de_analysis.py` to run DESeq2 (via `rpy2`) for each species-tissue pair
- [ ] T025 [US2] Implement `src/data/traits.py` to compile defense trait data from TRY/Phenoscape/GBIF. **Include fallback logic: if TRY lacks data for a species, query Phenoscape/GBIF. Calculate Defense Allocation Index (DAI) = (mean standardized chemical) / (mean standardized physical). This task MUST complete before T026 and T027. Requires: T014 (QC), T011 (Data availability).**
- [ ] T019 [US2] Implement `src/analysis/feature_engineering.py` to construct herbivore-response vectors (a subset of top-ranked genes, selected by -log10(p))
- [ ] T020 [US2] Add logic to exclude trait-synthesis genes (e.g., CYP79D16) from the predictor set to prevent circular validation
- [ ] T021 [US2] Implement KEGG/GO pathway aggregation to reduce features to ≤50 pathway-level scores. **Must be performed as a sub-routine to be called by T027 (Modeling). Must NOT be run as a standalone pre-processing step. Must be executed strictly within the LOSO training fold to prevent data leakage.**
- [ ] T022 [US2] Implement LOSO-aware feature selection to ensure no data leakage between folds. **Must be performed as a sub-routine to be called by T027 (Modeling). Must NOT be run as a standalone pre-processing step. Must be executed strictly within the LOSO training fold.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Statistical Evaluation (Priority: P3)

**Goal**: Train models, validate with LOSO/PGLS, and perform significance testing.

**Independent Test**: Verify LOSO CV execution, power analysis halts if N<15, permutation tests run, and metrics are reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for Power Analysis gate in `tests/unit/test_validation.py`
- [ ] T024 [P] [US3] Unit test for Phylogenetic Null Model generation in `tests/unit/test_validation.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/analysis/validation.py` for Power Analysis. **Halt execution and report error message: "Insufficient statistical power for reliable prediction" if available species N < 15.** **Requires: T025 (DAI compilation), T014 (QC).**
- [ ] T027 [US3] Implement `src/analysis/modeling.py` for Elastic Net and Random Forest with LOSO CV. **Requires: T025 (DAI compilation), T021 (Pathway Aggregation), T022 (Feature Selection).**
- [ ] T028 [US3] Implement Phylogenetic Generalized Least Squares (PGLS) and Phylogenetic Null Model (label shuffling) in `src/analysis/modeling.py`. **Input: phylogenetic tree in Newick format (fetch from Open Tree of Life API or load from data/processed/phylo_tree.nwk), trait matrix. Library: ete3 or caper via rpy2.**
- [ ] T029 [US3] Implement permutation testing (N=10,000) for Spearman correlation and Holm-Bonferroni correction
- [ ] T030 [US3] Implement sensitivity analysis (varying DE gene counts) and report R² variation
- [ ] T031 [US3] Create CLI entry point `src/cli/run_pipeline.py` to orchestrate the full pipeline (--mode synthetic|real)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T033 Code cleanup and refactoring for memory efficiency (streaming large files)
- [ ] T034 Run `quickstart.md` validation to ensure reproducibility on CPU-only runner
- [ ] T035 [P] Add contract tests for data schema compliance in `tests/contract/`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
  - **Note**: T025 (DAI compilation) is part of this phase and MUST complete before T026 and T027 in US3.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 features
  - **Note**: T026 and T027 explicitly require T025 completion. T021 and T022 are sub-routines called by T027.

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
Task: "Unit test for FASTQ download validation in tests/unit/test_download.py"
Task: "Unit test for batch correction metric calculation in tests/unit/test_batch_correction.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/download.py"
Task: "Implement src/data/preprocess.py"
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
- **Constraint**: All tasks must be feasible on a multi-core CPU with standard system memory, no GPU. No 8-bit models or large LLMs.
- **Data**: Real data required for final validation; synthetic data used for structural prototype. Synthetic data must be stored in `data/synthetic/` and never in `data/raw/`.