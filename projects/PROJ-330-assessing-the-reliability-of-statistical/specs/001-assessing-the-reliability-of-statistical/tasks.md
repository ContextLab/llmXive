# Tasks: Assessing the Reliability of Statistical Significance in Openly Available Genomic Datasets

**Input**: Design documents from `/specs/001-assess-significance-reliability/`
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

- [ ] T001 Create project structure per implementation plan (`code/src/`, `code/scripts/`, `code/tests/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scikit-learn, matplotlib, seaborn, pyyaml, requests, tqdm, statsmodels) and R 4.3 environment
- [ ] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/src/config.py` with random seeds, path constants, and runtime thresholds (6h limit, min 100 perms)
- [X] T005 [P] Implement `code/src/versioning.py` to compute SHA256 hashes of artifacts and update `state.yaml`
- [X] T006 [P] Create `code/scripts/setup_env.sh` to initialize R `renv` and Python `venv`
- [ ] T007 Create `code/src/data_loader.py` with functions to fetch datasets from verified URLs (GEO, TCGA, ENCODE) via a manifest file and verify checksums
- [~] T008 Create `code/src/preprocessing.py` to filter zero-count genes and handle missing batch metadata (default to random stratification)
- [~] T009 [P] Setup environment configuration management for R script paths and memory limits <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 9, column 3:
 - **R Script Paths**: `R_SCRIPT_DI...
 ^
expected alphabetic or numeric character, but found '*'
 in "<unicode string>", line 9, column 4:
 - **R Script Paths**: `R_SCRIPT_DIR...
 ^) -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Stability of Effect Size Calculation (Priority: P1) 🎯 MVP

**Goal**: Download a genomic dataset, partition it into stratified subsets, and calculate the Pearson correlation of log2 fold-changes between full and subset analyses.

**Independent Test**: Process a single small GEO dataset, verify subsets are created correctly, and output a correlation coefficient for effect sizes.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] [TDD] Write `test_stratification_handles_missing_batch` in `code/tests/test_preprocessing.py` asserting random fallback on missing metadata
- [~] T011 [P] [US1] [TDD] Write `test_pearson_correlation_all_genes_returns_valid_r` in `code/tests/test_metrics.py`

### Implementation for User Story 1

- [~] T016a [US1] **Spec Correction**: Update `spec.md` FR-006 to explicitly authorize calculating stability on "ALL genes" (overriding "significant genes") to avoid Winner's Curse, citing plan.md Spec Correction #1
- [~] T016 [US1] Implement `code/src/metrics.py` to calculate Pearson correlation of log2FC between full set and subsets for ALL genes (AUTHORIZED by T016a; see Spec Correction #1)
- [~] T012 [P] [US1] Configure `code/src/data_loader.py` usage in `main.py` to fetch a specific RNA-seq count matrix (e.g., from GEO) with ≥20 samples
- [~] T013 [P] [US1] Configure `code/src/preprocessing.py` usage in `main.py` to partition data into 5 stratified subsets (or random if no batch metadata)
- [~] T014 [US1] Create `code/scripts/run_r_script.R` to perform Differential Expression (DESeq2/edgeR) on the full dataset
- [~] T015 [US1] Implement Python orchestration in `code/main.py` to loop subset calls to `code/scripts/run_r_script.R` (T014)
- [~] T017 [US1] Add error handling in `code/src/main.py` to skip datasets with <20 samples and log warnings
- [~] T018 [US1] Implement logic to handle "Insufficient total genes" (replacing 'significant genes' check per T016) gracefully if <5 genes found across all categories

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Stratified Block Permutation Null Modeling (Priority: P2)

**Goal**: Generate a null distribution via stratified block permutations using the Fixed-Dispersion Wald Perturbation strategy and compare against parametric p-values.

**Independent Test**: Run multiple permutations on a small dataset, generate a uniform p-value histogram, and produce a Bland-Altman plot.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T019 [P] [US2] Write `test_stratified_shuffle_preserves_batch_counts` in `code/tests/test_permutation.py`
- [~] T020 [P] [US2] Write `test_ks_statistic_uniform_distribution_passes` and `test_bland_altman_plot_generation` in `code/tests/test_metrics.py`

### Implementation for User Story 2

- [~] T021a [US2] **Spec Correction**: Update `spec.md` FR-004 to explicitly authorize the "Fixed-Dispersion Wald Perturbation" approximation (skipping full DE re-run) to meet 6h runtime constraints, citing plan.md Spec Correction #3
- [~] T021 [P] [US2] Implement `code/src/de_analysis.py` (single-run wrapper) that calls `code/scripts/run_r_script.R` to extract and **save fixed-dispersion parameters** to a state file artifact (AUTHORIZED by T021a)
- [~] T022 [US2] Implement `code/src/permutation.py` to shuffle sample labels within batch groups and recompute Wald statistics using fixed dispersions from T021 artifact (AUTHORIZED by T021a)
- [ ] T023 [US2] Implement `code/src/permutation.py` dynamic iteration logic: estimate time per iter, cap at 6h, fallback to min 100 iterations with "low-confidence" flag
- [ ] T024b [US2] Implement `code/src/metrics.py` to compare parametric vs. empirical p-values: **KS test to verify p-value > 0.05** (correcting spec SC-002) and generate Bland-Altman plot
- [ ] T024c [US2] Update `plan.md`/`spec.md` with Spec Correction #2 (KS threshold: D < 0.05 -> p-value > 0.05)
- [ ] T024 [US2] Implement `code/src/metrics.py` to calculate and report p-value inflation metrics (median absolute deviation)
- [ ] T025 [US2] Add Benjamini-Hochberg correction to all reported p-values in `code/src/metrics.py` (per FR-008)
- [ ] T026 [US2] Implement `code/src/report.py` to visualize the Bland-Altman plot and save to `artifacts/`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Dataset Benchmarking (Priority: P3)

**Goal**: Aggregate results from multiple distinct datasets (TCGA, ENCODE, GEO) to determine if reliability varies by repository.

**Independent Test**: Process two distinct datasets and verify the final report correctly aggregates and contrasts their metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Write `test_aggregation_handles_missing_repo_gracefully` in `code/tests/test_integration.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Configure `code/src/data_loader.py` usage in `main.py` to fetch and cache 3-4 distinct datasets from verified sources (TCGA, ENCODE, GEO)
- [ ] T029 [P] [US3] Implement logic in `code/src/data_loader.py` to explicitly tag each dataset with its source (TCGA/ENCODE/GEO) for downstream aggregation
- [ ] T029a [US3] **Aggregation Logic**: Implement logic in `code/src/report.py` to aggregate stability correlations and inflation metrics into a summary table, **grouped by source tag** (TCGA vs ENCODE vs GEO) to validate repository-specific trends
- [ ] T030 [US3] Implement logic to handle missing data points for one repository without failing the entire analysis
- [ ] T031 [US3] Generate a comparative visualization (e.g., bar chart) of stability correlations across repositories in `artifacts/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `code/README.md` and `specs/001-assess-significance-reliability/quickstart.md`
- [ ] T033 Code cleanup and refactoring for memory efficiency (ensure <6GB usage)
- [ ] T034 Performance optimization: verify permutation loop overhead is minimal
- [ ] T035 [P] Run `specs/001-assess-significance-reliability/quickstart.md` validation
- [ ] T036a [P] Finalize `state.yaml` with all artifact hashes
- [ ] T036b [P] Finalize `plan.md` with any remaining spec corrections (e.g., Dispersion/Fixed-Dispersion if not fully documented in T021a)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1's data loading/preprocessing logic for consistency
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 implementations to aggregate results

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
Task: "Write test_stratification_handles_missing_batch in code/tests/test_preprocessing.py"

# Launch all data/DE tasks for User Story 1 together:
Task: "Configure data_loader.py usage in main.py to fetch a specific RNA-seq count matrix"
Task: "Configure preprocessing.py usage in main.py to partition data into 5 stratified subsets"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (stability metric on one dataset)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Null model validation)
4. Add User Story 3 → Test independently → Deploy/Demo (Cross-dataset context)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Core stability metric)
 - Developer B: User Story 2 (Permutation null model)
 - Developer C: User Story 3 (Aggregation logic)
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
- **Critical Constraint**: All permutation tasks MUST use the Fixed-Dispersion approximation to ensure CPU-only feasibility (Authorized by T021a).
- **Critical Constraint**: Effect size stability MUST be calculated on ALL genes, not just significant ones, to avoid Winner's Curse (Authorized by T016a).
- **Data Sources**: Tasks must explicitly support GEO, TCGA, and ENCODE via a manifest file mechanism.
- **Metric Logic**: KS test must verify p-value > 0.05 (not D < 0.05) as per Spec Correction #2.