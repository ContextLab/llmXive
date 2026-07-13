# Tasks: Uncovering Latent Relationships Between Molecular Descriptors and Antibiotic Resistance

**Input**: Design documents from `/specs/001-uncovering-latent-relationships/`
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

- [X] T001 Create project structure per implementation plan (`src/data`, `src/analysis`, `src/viz`, `tests/`, `data/`)
- [X] T002 Initialize Python 3 project with dependencies (`rdkit`, `scikit-learn`, `umap-learn`, `scipy`, `pandas`, `numpy`, `matplotlib`, `seaborn`) in `requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `src/config.py` with pinned random seeds (numpy, python, rdkit), file paths, and `PERMUTATION_ITERATIONS=1000`
- [X] T005 [P] Create `src/data/__init__.py` and `src/analysis/__init__.py` to expose module interfaces
- [X] T006 [P] Setup `tests/unit/test_config.py` to verify seed pinning and configuration loading
- [ ] T007a [P] Define `data_version.json` schema (fields: `source_url`, `checksum_sha256`, `timestamp`)
- [ ] T007b [P] Implement logging infrastructure in `src/main.py` to write to `data_version.json`
- [ ] T008 Implement error handling wrapper for API/FTP fetches (exponential backoff) in `src/data/utils.py`
- [ ] T009 Setup `contracts/` directory with `dataset.schema.yaml` and `output.schema.yaml` based on plan requirements

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Ingest antibiotic structures (ChEMBL/ZINC15) and resistance data (NCBI), merge on InChIKey, and compute RDKit descriptors.

**Independent Test**: Run ingestion script on a subset; verify `descriptors.csv` has correct columns, valid numerics, and matches expected InChIKey counts.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for SMILES canonicalization and invalid SMILES exclusion in `tests/unit/test_data.py`
- [ ] T011 [P] [US1] Unit test for merge logic on InChIKey (handling missing data/NaNs) in `tests/unit/test_data.py`
- [~] T012 [P] [US1] Integration test for end-to-end fetch and descriptor calculation on a small sample of compounds in `tests/integration/test_data.py`

### Implementation for User Story 1

- [~] T013 [US1] Implement `src/data/download.py` with functions to fetch ChEMBL/ZINC15 SMILES and NCBI Pathogen Detection frequencies (with backoff)
- [~] T014 [US1] Implement `src/data/process.py` to canonicalize SMILES, calculate standardized set of RDKit descriptors using `rdkit.Chem.Descriptors.descList`, and exclude invalid compounds
- [~] T015 [US1] Implement merge logic in `src/data/process.py` to join structure and resistance data on InChIKey, flagging missing resistance as NaN
- [~] T016 [US1] Generate `merge_metrics.json` in `data/processed/` reporting `total_requested`, `matches`, and `fraction` (SC-001)
- [~] T017 [P] [US1] Implement checksum verification (SHA256) for downloaded raw files in `src/data/download.py` and log to `data_version.json` using the schema fields defined in T007a (`source_url`, `checksum_sha256`, `timestamp`)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dimensionality Reduction and Cluster Enrichment (Priority: P2)

**Goal**: Apply UMAP for visualization, DBSCAN for clustering, and perform Fisher's exact test with permutation validation for enrichment.

**Independent Test**: Generate 2D UMAP plot; verify points colored by resistance; confirm Fisher's test runs (or logs "no clusters found") with p < 0.05 significance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [P] [US2] Unit test for UMAP parameter application (n_neighbors=15, min_dist=0.1) in `tests/unit/test_dimensionality.py`
- [~] T019 [P] [US2] Unit test for DBSCAN clustering logic and "noise" handling in `tests/unit/test_clustering.py`
- [~] T020 [P] [US2] Unit test for Fisher's exact test implementation and permutation validation in `tests/unit/test_permutation_validation.py`
- [~] T021 [P] [US2] Integration test for full UMAP -> DBSCAN -> Fisher pipeline in `tests/integration/test_clustering.py`

### Implementation for User Story 2

- [~] T022 [US2] Implement `src/analysis/dimensionality.py` to apply UMAP to the descriptor matrix and save 2D embedding to `data/processed/umap_embedding.csv`
- [~] T023 [US2] Implement `src/viz/plots.py` to generate UMAP scatter plot colored by resistance phenotype and save to `data/processed/umap_scatter.png`
- [~] T023b [US2] Calculate silhouette score for the UMAP embedding generated in T022 and log the score to `clustering_results.json` for internal verification (not a required output artifact)
- [~] T024 [US2] Implement `src/analysis/clustering.py` to run DBSCAN (eps=0.5, min_samples=10) on UMAP coordinates
- [~] T027 [US2] Add logic to exclude clusters with <10 samples from enrichment ranking (flag as "insufficient power")
- [~] T025 [US2] Implement Fisher's exact test in `src/analysis/clustering.py` to evaluate cluster enrichment for high-resistance compounds
- [~] T026 [US2] Implement `run_label_permutation_test` in `src/analysis/clustering.py` to validate enrichment is not a tautology; Run exactly 1000 iterations using the `PERMUTATION_ITERATIONS` value from `src/config.py` (T004)
- [~] T028 [US2] Generate `clustering_results.json` containing cluster IDs, enrichment p-values, permutation p-values, and diagnostic messages

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Association and Effect Size Ranking (Priority: P3)

**Goal**: Perform Mann-Whitney U tests, apply BH-FDR correction, rank by Cohen's d, and conduct sensitivity analysis (binary vs continuous).

**Independent Test**: Run analysis on mock data; verify ranking by Cohen's d, correct BH-FDR application, and sensitivity report generation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T029 [P] [US3] Unit test for Mann-Whitney U and Cohen's d calculation in `tests/unit/test_stats.py`
- [~] T030 [P] [US3] Unit test for Benjamini-Hochberg FDR correction logic in `tests/unit/test_stats.py`
- [~] T031 [P] [US3] Unit test for Hartigan's dip test and GMM bimodality assessment in `tests/unit/test_stats.py`
- [ ] T032 [P] [US3] Unit test for VIF filtering to remove collinear descriptors in `tests/unit/test_stats.py`
- [ ] T033 [P] [US3] Integration test for full statistical pipeline (Binary vs Continuous) in `tests/integration/test_stats.py`

### Implementation for User Story 3

- [ ] T034 [US3] Implement `src/analysis/statistics.py::assess_bimodality_and_fallback` (Hartigan's dip test -> GMM -> Continuous Spearman fallback)
- [ ] T034a [US3] Implement the binary resistance label derivation (High/Low) based on the lower/upper quartiles of resistance frequencies as defined in the Assumptions and FR-009, ensuring the binarization step is explicit before testing
- [ ] T034b [US3] Generate `data/processed/bimodality_histogram.png` and `data/processed/bimodality_report.json` as required by FR-009 to document the distribution analysis
- [ ] T036 [US3] Implement Mann-Whitney U tests for **each** descriptor against the binary resistance labels (or continuous if fallback is triggered) in `src/analysis/statistics.py`, ensuring no descriptors are filtered out prior to testing
- [ ] T037 [US3] Apply Benjamini-Hochberg FDR correction (α=0.05) to p-values and calculate Cohen's d effect sizes for the full set of descriptors
- [ ] T038 [US3] Generate `statistical_ranking.csv` sorted by |Cohen's d| (desc) and FDR-adjusted p-value (asc)
- [ ] T039 [US3] Implement sensitivity analysis comparing binary Mann-Whitney results against continuous Spearman correlation
- [ ] T040 [US3] Generate `sensitivity_analysis_report.json` comparing binary vs continuous model rankings
- [ ] T035 [US3] Perform VIF filtering in `src/analysis/statistics.py` for diagnostic/interpretability purposes ONLY after testing the full set, ensuring the initial statistical test in T036 used the full set
- [ ] T035b [US3] Generate `data/processed/vif_filtered_descriptors.json` listing descriptors filtered by VIF as a **diagnostic artifact** for traceability, noting it is not an input for downstream statistical steps

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Implement `src/main.py` orchestration script to run the full pipeline (Fetch -> Calc -> Reduce -> Cluster -> Test) with timing
- [ ] T042 [P] Generate `runtime_metrics.json` in `data/processed/` with fields `total_duration_seconds`, `cpu_usage_percent`, `peak_memory_mb` to verify SC-004
- [ ] T043 [P] Implement `tests/integration/test_pipeline.py` to run pipeline twice (fresh vs snapshot) and verify SC-005 reproducibility (hash match)
- [ ] T044 [P] Add documentation updates in `docs/` and `README.md` explaining the pipeline flow, CPU constraints, and flag Constitution Check gap for plan revision (Reference-Validator Agent)
- [ ] T045 [P] Code cleanup: ensure all random seeds are used, no hardcoded GPU flags, and all file paths are relative
- [ ] T046 [P] Run `quickstart.md` validation to ensure the pipeline executes successfully from a clean environment

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (descriptors)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US1 (descriptors)
 - *Note: US2 and US3 can run in parallel as they both consume US1 output but do not depend on each other*

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data fetch/calc (US1) before Analysis (US2/US3)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 and US3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for SMILES canonicalization in tests/unit/test_data.py"
Task: "Unit test for merge logic in tests/unit/test_data.py"
Task: "Integration test for fetch/calc in tests/integration/test_data.py"

# Launch all models for User Story 1 together:
Task: "Implement download.py"
Task: "Implement process.py"
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
- **CRITICAL**: All data fetches must use real URLs (ChEMBL, ZINC15, NCBI) and no synthetic data generation is allowed.
- **CRITICAL**: All computations must be CPU-only and fit within 6 hours on 2 vCPU/7GB RAM.
- **CRITICAL**: VIF filtering (T035) is for interpretability only and must NOT occur before testing the full set of descriptors (T036).
- **CRITICAL**: Bimodality assessment (T034) and label derivation (T034a) must occur BEFORE statistical testing (T036).