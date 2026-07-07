# Tasks: Quantifying the Impact of Transposable Element Activity on Gene Expression Variation in Drosophila

**Input**: Design documents from `/specs/001-quantifying-the-impact-of-transposable-e/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-173-quantifying-the-impact-of-transposable-e/`)
- [ ] T002 Initialize Python project with `requirements.txt` (pandas, scikit-learn, statsmodels, numpy, scipy, requests, biopython, pyyaml, lxml, matplotlib, shapely)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**CRITICAL**: This phase now implements the Mock Data Generator required by FR-001. No real data downloads are permitted.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Note on Execution**: Tasks T004-T008 all write to `code/data_generator.py`. They must be implemented **sequentially** (not in parallel) to avoid file conflicts and respect internal dependencies (e.g., T006A depends on T006).

- [ ] T004 [P] Implement `code/data_generator.py` function to generate Mock TE genotypes CSV. Must simulate a substantial number of lines with TE presence frequencies between **0.05 and 0.95** (to ensure sufficient power and exclude monomorphic TEs per FR-008). The function must generate **raw data including monomorphic TEs**; filtering is handled by T008. (FR-001, FR-008)
- [ ] T004A [P] Implement `code/data_generator.py` function to generate Mock gene expression TPM matrix CSV. Must simulate expression values for multiple lines with realistic variance, and handle zero/near-zero values by adding a small constant (e.g., 1e-6). (FR-001)
- [ ] T004B [P] Implement `code/data_generator.py` function to generate Mock population PCs CSV and set `quantification_method: TEaware` in the mock dataset metadata/schema. This task ensures the Mock data satisfies Constitution Principle VII. (FR-001, Constitution Principle VII)
- [ ] T005 [P] Implement `code/utils.py` for logging, checksumming, and random seed management (ensure reproducibility)
- [ ] T006 [P] Implement `code/data_generator.py` function to generate Mock gene models CSV with Drosophila release 6 TSS/TES coordinates. Must simulate a **distribution of TE insertions across the genome, ensuring a mix of proximal (≤5kb) and distal (>5kb) insertions** to provide necessary negative controls for filtering logic. (FR-002, FR-011)
- [ ] T006A [P] Implement `code/data_generator.py` function to simulate TE-Gene pairing logic and ensure ambiguous pairs are flagged in the generated metadata.
- [ ] T006B [P] Implement `code/data_generator.py` function to simulate missing expression data for specific lines to test exclusion logic (FR-009).
- [ ] T007 [P] Implement `code/data_generator.py` function to generate Mock population structure PCs (PC1, PC2, PC3) derived from simulated genome-wide SNPs. These PCs must be independent of specific TE insertions to allow non-tautological validation. (FR-003)
- [ ] T008 [P] Implement `code/data_generator.py` function to filter monomorphic TEs (freq < 5% or > 95%) in the generated dataset and log exclusions. Ensure the final output CSV only contains polymorphic TEs. (FR-008)
- [ ] T009 [P] Implement `code/preprocessing.py` function to calculate Variance Inflation Factor (VIF) for TE presence vs PCs (for use in association testing).
- [ ] T010 [P] Implement `code/association.py` skeleton for linear model fitting (`log2(expr) ~ TE + PC1 + PC2 + PC3`)
- [ ] T011 [P] Implement `code/association.py` function to apply Benjamini-Hochberg correction and filter FDR < 0.05
- [ ] T012 [P] Implement `code/association.py` function to compute R² reduction with/without PCs for population structure control metric. **Must write the output table to `data/results/population_structure_control_metrics.csv` with columns: `r2_with_pcs`, `r2_without_pcs`, `reduction_percent`. Must handle the edge case where `r2_without_pcs` is 0 by setting `reduction_percent` to `0.0` to prevent division-by-zero errors.** (FR-012, SC-004)
- [ ] T013 [P] Implement `code/permutation.py` skeleton for null distribution generation
- [ ] T014 [P] Implement `code/replication.py` skeleton for independent dataset validation logic

**Checkpoint**: Foundation ready - Mock data generator and basic analysis skeleton complete. User story implementation can now begin.

---

## Phase 3: User Story 1 - Core TE-Gene Association Analysis Pipeline (Priority: P1) 🎯 MVP

**Goal**: Run the association analysis pipeline on the Mock/Synthetic Dataset and produce a table of TE-gene pairs with effect sizes, FDR-corrected p-values, and diagnostic flags.

**Independent Test**: Run pipeline on the generated Mock Dataset; verify output table contains TE-gene pairs with proper statistical metrics (effect size, CI, p-value, adj-p-value) and handles missing data/monomorphic TEs gracefully.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [P] [US1] Unit test for TE-Gene pairing logic and monomorphic filtering in `tests/test_preprocessing.py` (verify distance calculation and frequency thresholding on mock data)
- [ ] T015A [P] [US1] Unit test for missing data exclusion logic in `tests/test_preprocessing.py` (verify line exclusion per test)
- [ ] T015B [P] [US1] Contract test for `quantification_method` flag in `tests/test_data_schema.py`. **Verify that the mock data metadata schema correctly declares `quantification_method: TEaware` as a simulated metadata field (not a tool usage flag) to satisfy Constitution Principle VII intent.**
- [ ] T016 [P] [US1] Integration test for full US1 pipeline on mock data in `tests/integration/test_us1_pipeline.py`

### Implementation for User Story 1

- [ ] T019 [US1] Implement `code/preprocessing.py` logic to map TE coordinates to gene TSS/TES (Drosophila release 6) and define proximal pairs (≤5kb) using the Mock gene models. (FR-002)
- [ ] T020 [US1] Implement `code/preprocessing.py` logic to handle missing expression values by excluding affected lines per test (FR-009)
- [ ] T020A [US1] Implement `code/preprocessing.py` logic for ambiguous TE-gene proximity resolution: if a TE is within 5kb of multiple genes, flag these pairs with 'ambiguous_flag' = true and exclude them from primary association testing (FR-011).
- [ ] T021 [US1] Implement `code/association.py` to fit `log2(expression) ~ TE_presence + PC1 + PC2 + PC3` for each pair (FR-004)
- [ ] T022 [US1] Implement `code/association.py` to calculate VIF and flag pairs with VIF > 5 for descriptive-only reporting (FR-007). **Output must include a 'vif_flag' column.**
- [ ] T023 [US1] Implement `code/association.py` to generate final output table with effect size, confidence intervals, unadjusted p-value, and BH adjusted p-value, **including integration of VIF flags** from T022 (FR-005). **Must append 'vif_flag' column to final results.**
- [ ] T024 [US1] Add error handling in `code/data_generator.py` to raise `DataGenerationError` if mock data generation fails or violates schema constraints (Assumptions)
- [ ] T025 [US1] Add error handling in `code/association.py` to handle cases where no significant pairs are found (output empty table with correct schema).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Independent Dataset Replication (Priority: P2)

**Goal**: Validate significant TE-gene associations by testing them on a second Mock dataset (simulating a different tissue/stage) and calculate replication concordance.

**Independent Test**: Run association analysis on a second Mock dataset for ≥10 significant pairs; verify output table includes original effect size, replication effect size, direction concordance, and replication p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US2] Contract test for replication output schema in `tests/contract/test_replication_schema.py`
- [ ] T030 [P] [US2] Integration test for replication pipeline with missing data scenarios in `tests/integration/test_us2_replication.py`

### Implementation for User Story 2

- [ ] T031 [US2] Implement `code/replication.py` to load a second independent Mock expression dataset (generated with different seeds) and align gene IDs. (US-2)
- [ ] T032 [US2] Implement `code/replication.py` to filter the set of significant pairs from US1 for testing on the replication dataset. **(Depends on T023 completion artifact)**
- [ ] T033 [US2] Implement `code/replication.py` to fit the same linear model on the replication data for the selected pairs (handling missing lines per FR-009).
- [ ] T034 [US2] Implement `code/replication.py` to calculate direction concordance and replication p-values.
- [ ] T035 [US2] Implement `code/replication.py` to generate the comparison table (original effect, replication effect, concordance flag, rep p-value) (FR-010).
- [ ] T036 [US2] Implement `code/replication.py` to compute replication concordance rate and perform binomial test against null hypothesis of equal probability (SC-002, FR-016).
- [ ] T037 [US2] Write unit tests in `tests/test_replication.py` for concordance calculation and missing data exclusion logic.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Permutation Testing for Robustness Validation (Priority: P3)

**Goal**: Perform residual-based permutation testing (up to 1000 iterations with fallback) to confirm observed associations exceed random expectation and generate null distribution plots.

**Independent Test**: Run a sufficient number of permutations; verify observed raw t-statistic for significant pairs exceeds the critical threshold of the null distribution.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T038 [P] [US3] Unit test for residual permutation logic in `tests/test_permutation.py` (verify null distribution generation)
- [ ] T039 [P] [US3] Integration test for time-limit handling in `tests/integration/test_us3_permutation_timeout.py`

### Implementation for User Story 3

- [ ] T040 [US3] Implement `code/permutation.py` to perform **residual-based permutation** (shuffle residuals of the null model `gene_expression ~ PC1 + PC2 + PC3` while preserving PC structure) to generate a valid null distribution. **Explicitly do NOT shuffle TE labels directly.** (FR-006)
- [ ] T041 [US3] Implement `code/permutation.py` to run **up to 1000 iterations** of the Freedman-Lane procedure with a **timeout-aware loop**. If the CI limit is approached, stop early, save intermediate results, and report the partial count. (FR-006, SC-005, Plan: Dynamic Fallback)
- [ ] T042 [US3] Implement `code/permutation.py` to calculate a statistically significant percentile threshold of the null distribution and compare observed raw t-statistics against it (SC-005).
- [ ] T043 [US3] Implement timeout handling in `code/permutation.py` to save intermediate results and report partial p-values if >6h (US-3 Acceptance Scenario 3).
- [ ] T044 [US3] Implement `code/viz.py` to generate a **null_distribution_plot** visualization showing the observed statistic as a vertical line and the 95th percentile threshold clearly marked with a **red dashed vertical line**. **Output must be saved to `data/results/null_distribution_plot.png`.** (FR-014, SC-005)
- [ ] T045 [US3] Write unit tests in `tests/test_permutation.py` for timeout handling and intermediate result saving.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Documentation updates in `README.md` and `docs/` (include quickstart instructions)
- [ ] T047 Code cleanup and refactoring of `code/` modules for consistency
- [ ] T048 Performance optimization for large-scale TE-Gene pair iteration (vectorization where possible)
- [ ] T049 [P] Additional unit tests for edge cases (monomorphic TEs, zero expression, collinearity) in `tests/unit/`
- [ ] T050 [P] Run `quickstart.md` validation to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 results (significant pairs list)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 results (observed statistics)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks (T005-T014) marked [P] can run in parallel **except T004-T008 which must be sequential due to shared file writes**.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for TE-Gene pairing logic and monomorphic filtering in tests/test_preprocessing.py"
Task: "Unit test for missing data exclusion logic in tests/test_preprocessing.py"

# Launch implementation tasks that are independent:
Task: "Implement code/preprocessing.py logic to map TE coordinates..."
Task: "Implement code/association.py to fit log2(expression) ~ TE..."
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
- **CPU Constraint**: All tasks must run on a limited CPU core allocation, constrained RAM, no GPU.. No 8-bit/4-bit quantization or large model training.
- **Data Integrity**: All data is Mock/Synthetic as per FR-001. No real data downloads.
- **TE-Aware Quantification**: Constitution Principle VII requires TE-aware tools; tasks T004B and T015B ensure the Mock data includes the `quantification_method: TEaware` flag in metadata (simulated).
- **Ambiguous Proximity**: Task T020A handles edge cases for overlapping TE-gene assignments.
- **Residual Permutation**: Task T040 explicitly implements residual-based permutation to preserve LD structure.
- **Output Verification**: Tasks T012 and T044 ensure specific output formats and paths are generated as required by Success Criteria.
- **Iteration Count**: Task T041 enforces up to 1000 permutations with timeout fallback as per FR-006 and Plan assumptions.
- **Sequential Execution**: Tasks T004-T008 must be implemented sequentially as they all modify `code/data_generator.py`.