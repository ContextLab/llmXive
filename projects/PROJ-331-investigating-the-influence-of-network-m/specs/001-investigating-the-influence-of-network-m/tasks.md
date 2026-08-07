# Tasks: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

**Input**: Design documents from `/specs/feature/motif-rsfc/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

- [X] T001 [P] Create project directory structure: `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/logs/`, `results/`, `state/`
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (numpy, scipy, pandas, networkx, matplotlib, seaborn, nibabel, requests, reportlab, tqdm, joblib, dipy)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` with paths, seeds (42), and constants
- [X] T005 [P] Implement `code/utils.py` for logging (to `pipeline.log`), error handling, and file I/O
- [X] T006 [P] Create `scripts/hash_artifacts.sh` to generate SHA256 checksums and update `state/...yaml`
- [X] T007 [P] Setup `tests/conftest.py` and mock data fixtures for CI-safe testing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑End Data Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically retrieve, preprocess, and store structural and resting‑state functional data for a cohort of subjects.

**Independent Test**: Execute the pipeline on a fresh CI runner; verify that for each of the selected subjects a binary structural connectome (Schaefer‑parcellation) and an rsFC matrix are saved to the designated output folder.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for data download logic in `tests/unit/test_download.py`: **Contract**: Verify `download_subject_data(subject_id)` returns a dict with keys `{'dwi_path', 'rsfmri_path'}` or raises `FileNotFoundError` if missing; assert SHA256 checksums match `data/raw/.checksums.json` for valid files.
- [X] T011 [P] [US1] Unit test for parcellation logic in `tests/unit/test_preprocess.py`: **Contract**: Verify `parcellate_connectome(streamlines_path, atlas_path)` returns a numpy array of shape (N, N) with a floating-point data type, where N corresponds to the number of regions in the specified atlas.; assert values are non-negative and density is within the expected valid range.
- [X] T012 [P] [US1] Integration test for full pipeline on 2 subjects in `tests/integration/test_pipeline.py`: **Contract**: Run end-to-end on 2 mock subjects; assert `data/processed/` contains `structural.npy` and `rsfc.npy` for both; assert `data/logs/pipeline.log` contains "Processed 2/2 subjects" without errors.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/download.py` to fetch HCP DWI (.trk/.tck) and rs-fMRI data (or verify pre-seeded data in `data/raw/`); include graceful handling for missing subjects (log warning, skip, continue); **FAIL LOUDLY** on real fetch errors (no synthetic fallback)
- [ ] T014 [US1] Implement `code/preprocess.py` to apply Schaefer‑100 parcellation to DWI streamlines -> **Weighted Adjacency** (streamline count, **unthresholded**); input: .trk/.tck streamlines, .nii.gz atlas; output: `data/processed/weighted_adjacency.npy`
- [ ] T014a [US1] Implement `code/preprocess.py` to apply Schaefer‑100 parcellation to DWI streamlines -> **Binary Adjacency (10% density threshold)**; input: `data/processed/weighted_adjacency.npy`; output: `data/processed/binary_adj_10p.npy`
- [ ] T014b [US1] Implement `code/preprocess.py` to apply Schaefer‑100 parcellation to DWI streamlines -> **Binary Adjacency (20% density threshold)**; input: `data/processed/weighted_adjacency.npy`; output: `data/processed/binary_adj_20p.npy`
- [ ] T014c [US1] Implement `code/preprocess.py` to apply Schaefer‑100 parcellation to DWI streamlines -> **Binary Adjacency (30% density threshold)**; input: `data/processed/weighted_adjacency.npy`; output: `data/processed/binary_adj_30p.npy`
- [ ] T015 [US1] Implement `code/preprocess.py` to compute rsFC (Pearson correlation of BOLD time‑series) and **Global Efficiency** (on the **unthresholded weighted adjacency matrix** `data/processed/weighted_adjacency.npy` from T014); input: `data/processed/weighted_adjacency.npy`; output: `data/processed/rsfc.npy`, `data/processed/global_efficiency.json`
- [ ] T016 [US1] Implement logging of all processing steps, warnings, and errors to `data/logs/pipeline.log`
- [ ] T017 [US1] Save processed matrices (`structural.npy`, `rsfc.npy`) to `data/processed/` with provenance metadata

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Motif Quantification (Priority: P2)

**Goal**: Enumerate all 3-node subgraphs in each structural connectome, compute z‑score prevalence against degree‑preserving null models, and store the motif profile.

**Independent Test**: Run the motif‑counting script on a single preprocessed structural matrix; verify that a JSON file containing z‑scores for each motif type is produced and matches a reference output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for motif enumeration correctness in `tests/unit/test_motifs.py`: **Contract**: Verify `count_motifs(adj_matrix)` returns a dict with counts for all directed k-node motifs; assert sum of counts equals the theoretical total number of directed k-node subgraphs for a complete graph.
- [X] T020 [P] [US2] Unit test for null model generation (Maslov-Sneppen) in `tests/unit/test_motifs.py`: **Contract**: Verify `generate_null_model(adj_matrix, iterations=100)` preserves degree distribution; assert mean degree difference is < 1e-6.
- [X] T021 [P] [US2] Integration test for timeout handling on large graphs in `tests/integration/test_motifs.py`: **Contract**: Run on a large-scale graph with a predefined timeout threshold; assert function raises `TimeoutError` and logs "Timeout warning" to `pipeline.log`.

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/motifs.py` to enumerate all 3‑node subgraphs using `networkx`; generate degree‑preserving null networks using Maslov-Sneppen algorithm; enforce strict 300s timeout per subject to satisfy SC-002
- [ ] T023 [US2] Implement `code/motifs.py` to compute z‑score prevalence for every 3‑node motif type: `z = (observed - mean_null) / std_null`
- [ ] T024 [US2] Implement timeout wrapper (time limit) for motif enumeration; abort gracefully and log warning if exceeded
- [ ] T025 [US2] Compute z-scores for **all three density thresholds** (10%, 20%, 30%) in a **single optimized loop** to ensure SC-002 compliance (total time <= 300s); input: `data/processed/binary_adj_10p.npy`, `binary_adj_20p.npy`, `binary_adj_30p.npy`; output: `data/processed/motif_z_10p.json`, `motif_z_20p.json`, `motif_z_30p.json`
- [ ] T026 [US2] Aggregate z-scores from T025 using **median** value across thresholds; output `data/processed/motif_profiles.json` with raw per-threshold scores
- [ ] T027 [US2] Save motif profiles to `data/processed/motif_profiles.json` with raw per-threshold scores

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation & Reporting (Priority: P3)

**Goal**: Correlate motif prevalence scores with rsFC strength and global efficiency across subjects, apply **Bonferroni correction**, perform a permutation test, and automatically generate a PDF report.

**Independent Test**: Execute the analysis script on the full set of subjects.; verify that a `results.pdf` is generated containing one page per motif type with a scatter plot, partial correlation coefficient, corrected p‑value, and a statement of significance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for partial correlation and Bonferroni correction in `tests/unit/test_stats.py`: **Contract**: Verify `partial_corr(x, y, z)` returns correct r and p-value; verify `bonferroni_correct(p_values)` returns adjusted p-values summing to <= 1.0.
- [ ] T029 [P] [US3] Unit test for permutation test implementation in `tests/unit/test_stats.py`: **Contract**: Verify `permutation_test(x, y, n_perm=1000)` returns empirical p-value; assert p-value is within 2*SE of analytical p-value for known distributions.
- [ ] T037b [P] [US3] Unit test for PDF generation layout and content in `tests/unit/test_report.py`: **Contract**: Verify `generate_pdf(results)` creates a file <= 5MB; assert presence of mandatory disclaimer string.
- [X] T037b [US3] Integration test in `tests/integration/test_report.py` to verify PDF generation completes in ≤2 minutes and file size ≤5MB (SC-004)

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/stats.py` to aggregate `data/processed/global_efficiency.json`, `data/processed/rsfc.npy`, and `data/processed/motif_profiles.json` into a single `data/processed/subject_metrics.csv` for downstream analysis; input: outputs from US1 and US2; output: `data/processed/subject_metrics.csv`
- [ ] T030 [US3] Implement `code/stats.py` to compute partial Pearson/Spearman correlations between each motif's z-score and each rsFC metric (strength and global efficiency) across subjects, **controlling for network density** (as per Plan Phase 3 strategy to avoid redundancy); input: `data/processed/motif_profiles.json`, `data/processed/subject_metrics.csv`; reference [FR-005], [Plan Phase 3]
- [ ] T031 [US3] Implement `code/stats.py` to apply **Bonferroni correction** across all directed 3‑node motifs (Strictly implements Spec FR-005; overrides Plan's FDR suggestion); output corrected p-values in `results/correlation_results.json`
- [ ] T032 [US3] Implement `code/stats.py` to run permutation test (≥1000 permutations) for significant motifs (corrected p < 0.05)
- [ ] T033 [US3] Implement zero-variance detection (skip test, flag in report) and VIF check for collinearity (if VIF > 5, report and switch to Spearman)
- [ ] T034 [US3] Implement `code/stats.py` power analysis module (N=50, α=0.05 **Bonferroni-adjusted**) using G*Power approximation; output schema: `{"min_detectable_r": float, "power_level": 0.8, "adjusted_alpha": float, "n_subjects": 50}` to `results/power_analysis.json`
- [ ] T035 [US3] Implement `code/report.py` to generate PDF with scatter plots, CIs, p-values, and permutation results per motif; input: `results/correlation_results.json`
- [ ] T036 [US3] Add mandatory disclaimer string: "These findings are associational only and do not imply causation." to PDF
- [ ] T037a [US3] Implement PDF generation logic in `code/report.py` ensuring layout, plots, and text are correctly rendered

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` (README, usage guide)
- [ ] T039 [P] Performance optimization for `code/motifs.py` to verify SC-002 compliance (≤300s/subject)
- [ ] T040 [P] Run `scripts/hash_artifacts.sh` to finalize versioning and update `state/...yaml`
- [ ] T041 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T042 [P] Run `quickstart.md` validation

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data output

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
Task: "Unit test for data download logic in tests/unit/test_download.py"
Task: "Unit test for parcellation logic in tests/unit/test_preprocess.py"

# Launch all implementation tasks for User Story 1 together (where independent):
Task: "Implement code/download.py"
Task: "Implement code/preprocess.py (parcellation logic)"
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
- **Spec vs Plan Conflict**: Where Spec FR-005 mandates Bonferroni and Plan suggests FDR, tasks follow the **Spec** (Bonferroni). Where Plan Phase 3 mandates controlling for 'network density' and Spec FR-005 says 'global node degree', tasks follow the **Plan** (network density) for scientific rigor, while still applying the Spec's correction method.