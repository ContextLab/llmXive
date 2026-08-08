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
- [X] T002 [P] Initialize Python project with `requirements.txt` (numpy, scipy, pandas, networkx, matplotlib, seaborn, nibabel, requests, reportlab, tqdm, joblib, dipy, statsmodels)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` with paths, seeds (42), and constants
- [X] T005 [P] Implement `code/utils.py` for logging (to `pipeline.log`), error handling, and file I/O
- [X] T006 [P] Create `scripts/hash_artifacts.sh` to generate SHA checksums and update `state/...yaml`
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
- [X] T012 [P] [US1] Integration test for full pipeline on 2 subjects in `tests/integration/test_pipeline.py`: **Contract**: Run end-end on mock subjects; assert `data/processed/` contains `structural.npy` and `rsfc.npy` for each subject.; assert `data/logs/pipeline.log` contains "Processed all subjects" without errors.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/download.py` to fetch HCP DWI (.trk/.tck) and rs-fMRI data (or verify pre-seeded data in `data/raw/`); include graceful handling for missing subjects (log warning, skip, continue); **FAIL LOUDLY** on real fetch errors (no synthetic fallback)
- [ ] T014a [P] [US1] Implement `code/preprocess.py` function `def parcellate_streamlines(streamlines_path, atlas_path)` to apply Schaefer parcellation to DWI streamlines -> **Weighted Adjacency** (streamline count, **unthresholded**). Input: .trk/.tck, .nii.gz atlas; Output: `data/processed/weighted_adjacency.npy`. **Dependency**: T013.
- [ ] T014b [US1] Implement `code/preprocess.py` function `def threshold_weighted_adjacency(weighted_path, thresholds=[0.1, 0.2, 0.3])` to generate **Binary Adjacencies** at varying density thresholds. **Explicit Constraint**: The `atlas_path` parameter MUST be explicitly set to the 'Schaefer et al.

The research question examines the relationship between [phenomenon] and [outcome], employing a [method] approach as outlined by Schaefer et al. (2023). This study aims to identify whether the observed trend aligns with theoretical predictions, without presuming specific quantitative magnitudes at this planning stage.' file defined in `code/config.py` to satisfy Spec FR-002. Input: `data/processed/weighted_adjacency.npy`; Output: `data/processed/binary_adj_10p.npy`, `data/processed/binary_adj_20p.npy`, `data/processed/binary_adj_30p.npy`. **Dependency**: T014a.
- [ ] T014c [US1] Implement `code/preprocess.py` to select the **canonical binary connectome** (threshold-based) for downstream Spec compliance. Output: `data/processed/canonical_binary_adj.npy`. **Dependency**: T014b.
- [ ] T015 [US1] Implement `code/preprocess.py` to compute rsFC (Pearson correlation of BOLD time‑series) and **Global Efficiency** (on the **unthresholded weighted adjacency matrix** `data/processed/weighted_adjacency.npy` from T014a). **Schema**: `data/processed/global_efficiency.json` = `{'subject_id': str, 'global_efficiency': float}` (formula: average of node-wise global efficiency). **Output**: `data/processed/rsfc.npy`, `data/processed/global_efficiency.json`. **Dependency**: T014a.
- [X] T016 [US1] Implement logging of all processing steps, warnings, and errors to `data/logs/pipeline.log`
- [ ] T017 [US1] Save processed matrices (`structural.npy`, `rsfc.npy`) to `data/processed/` with provenance metadata. **Explicit Requirement**: Append the provenance metadata (checksums, source files) to `data/logs/pipeline.log` as well to satisfy Spec FR-008 and Constitution Principle IV. **Dependency**: T014a, T015.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Motif Quantification (Priority: P2)

**Goal**: Enumerate all 3‑node subgraphs in each structural connectome, compute z‑score prevalence against degree‑preserving null models, and store the motif profile.

**Independent Test**: Run the motif‑counting script on a single preprocessed structural matrix; verify that a JSON file containing z‑scores for each motif type is produced and matches a reference output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for motif enumeration correctness in `tests/unit/test_motifs.py`: **Contract**: Verify `count_motifs(adj_matrix)` returns a dict with counts for all directed k-node motifs; assert sum of counts equals the theoretical total number of directed k-node subgraphs for a complete graph.
- [X] T020 [P] [US2] Unit test for null model generation (Maslov-Sneppen) in `tests/unit/test_motifs.py`: **Contract**: Verify `generate_null_model(adj_matrix, iterations=100)` preserves degree distribution; assert mean degree difference is < 1e-6.
- [X] T021 [P] [US2] Integration test for timeout handling on large graphs in `tests/integration/test_motifs.py`: **Contract**: Run on a large-scale graph with a predefined timeout threshold; assert function raises `TimeoutError` and logs "Timeout warning" to `pipeline.log`.

### Implementation for User Story 2

- [ ] T025a_count [US2] Implement `code/motifs.py` function `def count_motifs_with_timeout(adj_matrix, threshold, timeout=300)` to enumerate all 3‑node subgraphs for a **specific density threshold** using `networkx` **with a strict timeout wrapper**. If timeout exceeded, raise `TimeoutError` and log warning. **Dependency**: T014b.
- [ ] T025b_zscore [US2] Implement `code/motifs.py` function `def compute_z_scores(counts, null_counts)` to compute z‑score prevalence: `z = (observed - mean_null) / std_null` for a **specific density threshold**. Input: counts from T025a_count, null counts (multiple iterations). Output: in-memory dict of z-scores per motif. **Dependency**: T025a_count.
- [ ] T025c_loop [US2] Implement `code/motifs.py` to iterate Ta_count and T025b_zscore for **all three density thresholds** (10%, 20%, 30%) and store intermediate results. **Dependency**: T014b, T025a_count, T025b_zscore.
- [ ] T025d_raw [US2] Implement `code/motifs.py` to save raw z-scores for **every 3-node motif type** for **each threshold** to `data/processed/motif_z_raw.json`. **Schema**: `{'threshold_10p': {motif_id: float}, 'threshold_20p': {motif_id: float}, 'threshold_30p': {motif_id: float}}`. This file is the single source of truth for per-threshold data. **Dependency**: T025c_loop.
- [ ] T025c_aggregate [US2] Implement `code/motifs.py` to compute z-scores for **all three density thresholds** and aggregate using **median** value. **Note**: Extends Spec FR-004 per Plan Phase 2; raw outputs preserved in T025d_raw. Output: `data/processed/motif_z_aggregated.json`. **Dependency**: T025c_loop, T025b_zscore.
- [ ] T026 [US2] Implement `code/motifs.py` to aggregate z-scores from T025c_aggregate (median values) and save `data/processed/motif_profiles.json` containing the final aggregated scores and a reference to the raw data file `motif_z_raw.json`. **Dependency**: T025c_aggregate, T025d_raw.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation & Reporting (Priority: P3)

**Goal**: Correlate motif prevalence scores with rsFC strength and global efficiency across subjects, apply **Bonferroni correction**, perform a permutation test, and automatically generate a PDF report.

**Independent Test**: Execute the analysis script on the full set of subjects.; verify that a `results.pdf` is generated containing one page per motif type with a scatter plot, partial correlation coefficient, corrected p‑value, and a statement of significance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for partial correlation and Bonferroni correction in `tests/unit/test_stats.py`: **Contract**: Verify `partial_corr(x, y, z)` returns correct r and p-value; verify `bonferroni_correct(p_values)` returns adjusted p-values summing to <= 1.0.
- [X] T029 [P] [US3] Unit test for permutation test implementation in `tests/unit/test_stats.py`: **Contract**: Verify `permutation_test(x, y, n_perm=1000)` returns empirical p-value; assert p-value is within 2*SE of analytical p-value for known distributions.
- [X] T037b [P] [US3] Unit test for PDF generation layout and content in `tests/unit/test_report.py`: **Contract**: Verify `generate_pdf(results)` creates a file <= 5MB; assert presence of mandatory disclaimer string.
- [X] T038 [US3] Integration test in `tests/integration/test_report.py` to verify PDF generation completes in ≤2 minutes and file size ≤5MB (SC-004)

### Implementation for User Story 3

- [ ] T039 [US3] Implement `code/stats.py` to aggregate `data/processed/global_efficiency.json`, `data/processed/rsfc.npy`, `data/processed/motif_z_aggregated.json` (from T025c_aggregate, **canonical input**), and `data/processed/weighted_adjacency.npy` (to compute network density) into a single `data/processed/subject_metrics.csv`. **Note**: Handles subject list mismatch by inner-joining on available subjects. **Explicit Requirement**: The output CSV MUST include 'network_density' as a column to support T030a. **Dependency**: T014a, T015, T025c_aggregate, T025d_raw.
- [ ] T030a [US3] Implement `code/stats.py` function `def check_vif_and_select_method(metrics)` to compute VIF for control variable (**network density**). **Explicit Override**: This task explicitly overrides Spec FR-005's requirement to control for 'global node degree' with 'network density' based on the Plan's scientific rationale (avoiding statistical redundancy with the degree-preserving null model). If VIF > 5, flag `method_switched=True` and select Spearman; else Pearson. **Output**: `data/processed/quality_flags.json` with keys `{'zero_variance': bool, 'vif_value': float, 'method_switched': bool}`. **Dependency**: T039.
- [ ] T030b [US3] Implement `code/stats.py` function `def compute_partial_correlations(metrics, method)` to compute partial correlations between motif z-scores and rsFC metrics using the method selected in T030a. **Dependency**: T030a.
- [ ] T030c [US3] Implement `code/stats.py` to apply **Bonferroni correction** across all directed 3‑node motifs. **Explicit Override**: This task implements Bonferroni as mandated by Spec FR-005, overriding the Plan Phase 3 suggestion of FDR. The Plan's rationale for FDR is noted but the Spec requirement takes precedence. Output: `results/correlation_results.json`. **Dependency**: T030b.
- [ ] T032a [US3] Implement `code/stats.py` function `def identify_significant_motifs(results)` to filter motifs with corrected p < 0.05. Handle edge case: if no significant motifs, skip permutation test. **Dependency**: T030c, T030a.
- [ ] T032b [US3] Implement `code/stats.py` function `def run_permutation_test(motif_data, n_perm=1000)` to run permutation test (≥1000 permutations) for a **single** significant motif. **Null Hypothesis**: No correlation. **Statistic**: Pearson r. **Output**: Empirical p-value. **Dependency**: T032a.
- [ ] T032c [US3] Implement `code/stats.py` to **iterate** T032b over the list of significant motifs identified in T032a and aggregate the results into `results/permutation_results.json`. **Explicit Requirement**: This task satisfies Spec FR-006's requirement to run a permutation test for *each* significant motif. **Dependency**: T032b, T032a.
- [ ] T033 [US3] Implement zero-variance detection (skip test, flag in report) and VIF check for collinearity (if VIF > 5, report and switch to Spearman). **Output**: `data/processed/quality_flags.json`. **Dependency**: T039.
- [X] T034 [US3] Implement `code/stats.py` power analysis module (N=50, α=0.05 **Bonferroni-adjusted**) using `statsmodels.stats.power` for approximation; **Explicit Requirement**: Log the exact `statsmodels` version and the random seed used for the calculation to `pipeline.log` and include them in `results/power_analysis.json` to satisfy Constitution Principle VII. Output schema: `{"min_detectable_r": float, "power_level": 0.8, "adjusted_alpha": float, "n_subjects": 50, "statsmodels_version": str, "seed": int}`. **Dependency**: T030c.
- [ ] T035a [US3] Design PDF report layout in `docs/report_layout.md`: Define page structure, library usage (reportlab), and data mapping from `results/correlation_results.json` to PDF elements. **Dependency**: Spec FR-007, FR-009.
- [ ] T035b [US3] Implement `code/report.py` to generate PDF based on T035a design. Input: `results/correlation_results.json`, `results/permutation_results.json`, `results/power_analysis.json`. **Dependency**: T035a, T032c, T034.
- [ ] T036 [US3] Add mandatory disclaimer string: "These findings are associational only and do not imply causation." to PDF. **Dependency**: T035b.
- [ ] T037a [US3] Implement PDF generation logic in `code/report.py` ensuring layout, plots, and text are correctly rendered. **Dependency**: T035b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `docs/` (README, usage guide)
- [ ] T041 [P] Performance optimization for `code/motifs.py` to verify SC-002 compliance (≤300s/subject)
- [ ] T042 [P] Run `scripts/hash_artifacts.sh` to finalize versioning and update `state/...yaml`
- [ ] T043 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T044 [P] Run `quickstart.md` validation

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
- **Spec vs Plan Conflict**: Where Spec FR-005 mandates Bonferroni and Plan suggests FDR, tasks follow the **Spec** (Bonferroni) as documented in T030c. Where Plan Phase 3 mandates controlling for 'network density' and Spec FR-005 says 'global node degree', tasks follow the **Plan** (network density) for scientific rigor, with explicit override documentation in T030a.
- **Task Splitting**: T030 split into T030a (VIF/Method), T030b (Correlation), T030c (Correction). T025 split into T025a (Count per threshold), T025b (Z-score per threshold), T025c_loop (Iteration), T025c_aggregate (Median), T025d_raw (Raw storage). T014 split into T014a (Weighted), T014b (Binary), T014c (Canonical). T032 split into T032b (Function), T032c (Orchestration).
- **Data Integrity**: T013 strictly enforces "FAIL LOUDLY" on real data fetch errors; no synthetic fallbacks are permitted per Constitution Principle III.
- **Compute Feasibility**: T025a_count includes a strict 300s timeout to ensure SC-002 compliance; if exceeded, the subject is skipped for that motif and logged.
- **Data Flow**: T039 explicitly uses `motif_z_aggregated.json` as the canonical input for correlation analysis, resolving the raw vs. aggregated ambiguity.
- **Artifact Clarity**: T025d_raw defines the schema for raw per-threshold data (`motif_z_raw.json`), and T026 aggregates the median scores into `motif_profiles.json` without duplicating raw data, resolving the previous ambiguity.