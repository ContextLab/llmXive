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
- [X] T002 [P] Initialize Python project with `requirements.txt` (numpy, scipy, pandas, networkx, matplotlib, seaborn, nibabel, requests, reportlab, tqdm, joblib, dipy, statsmodels, weasyprint)
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
- [X] T014 [US1] Implement `code/preprocess.py` function `def parcellate_to_weighted(streamlines_path, atlas_path)` to apply Schaefer parcellation to DWI streamlines -> **Weighted Adjacency** (streamline count). Input: `.trk/.tck` (from T013), `.nii.gz` atlas. Output: `data/processed/weighted_adjacency.npy`. **Explicit Constraint**: This task produces the weighted matrix only. Binarization is handled in T014c. **Dependency**: T013.
- [X] T014c [US1] Implement `code/preprocess.py` function `def binarize_by_median_density(weighted_adj)` to compute the **median graph density** across all subjects' weighted matrices (cohort-level) and apply this threshold to binarize each subject's matrix. **Plan Compliance**: This task explicitly implements the "median graph density threshold" strategy required by Plan Phase 2, correcting the previous deviation (fixed [deferred]) found in T014. Input: `data/processed/weighted_adjacency.npy` (from T014). Output: `data/processed/canonical_binary_adj.npy` (binary) and `data/processed/structural_connectome_metadata.json` (status flags). **Dependency**: T014.
- [X] T015 [US1] Implement `code/preprocess.py` function `def compute_rsfc_and_efficiency(rsfmri_path, binary_adj_path)` to compute rsFC (Pearson correlation of BOLD time‑series) and **Global Efficiency** on the **binary structural connectome** (`data/processed/canonical_binary_adj.npy`). **Formula**: E = (1/(N*(N-1))) * sum(1/d_ij) for i!=j. Use `networkx.global_efficiency`. **Justification**: Global efficiency is calculated on the binary graph to maintain consistency with the motif analysis (FR-004) and FR-002's binary connectome requirement. **Schema**: `data/processed/global_efficiency.json` = `{'subject_id': str, 'global_efficiency': float}`. **Output**: `data/processed/rsfc.npy`, `data/processed/global_efficiency.json`. **Dependency**: T014c.
- [X] T016 [US1] Implement logging of all processing steps, warnings, and errors to `data/logs/pipeline.log`
- [X] T017 [US1] Save processed matrices (`structural.npy`, `rsfc.npy`) to `data/processed/` with provenance metadata. **Explicit Requirement**: Append the provenance metadata to `data/logs/pipeline.log` and generate a sidecar JSON `data/processed/<subject_id>_provenance.json` with schema: `{"subject_id": str, "source_files": [str], "processing_steps": [{"step": str, "timestamp": str, "params": dict}]}` to satisfy Spec FR-008 and Constitution Principle IV. **CRITICAL LOGGING REQUIREMENT**: This task MUST also log the following statistical parameters to `pipeline.log` to satisfy Constitution Principle VII (Statistical Transparency): Bonferroni alpha level (/ num_motifs), a sufficiently large number of permutations, random seed (a fixed value), and exact library versions (numpy, scipy, statsmodels) used in the analysis. **Dependency**: T014c, T015.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Motif Quantification (Priority: P2)

**Goal**: Enumerate all 3‑node subgraphs in each structural connectome, compute z‑score prevalence against degree‑preserving null models, and store the motif profile.

**Independent Test**: Run the motif‑counting script on a single preprocessed structural matrix; verify that a JSON file containing z‑scores for each motif type is produced and matches a reference output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for motif enumeration correctness in `tests/unit/test_motifs.py`: **Contract**: Verify `count_motifs(adj_matrix)` returns a dict with counts for all directed 3-node motifs; assert sum of counts equals the theoretical total number of directed 3-node subgraphs for a complete graph.
- [X] T020 [P] [US2] Unit test for null model generation (Maslov-Sneppen) in `tests/unit/test_motifs.py`: **Contract**: Verify `generate_null_model(adj_matrix, iterations=100)` preserves degree distribution; assert mean degree difference is < 1e-6.
- [X] T021 [P] [US2] Integration test for timeout handling on large graphs in `tests/integration/test_motifs.py`: **Contract**: Run on a large-scale graph with a predefined timeout threshold; assert function raises `TimeoutError` and logs "Timeout warning" to `pipeline.log`.

### Implementation for User Story 2

- [X] T025a_enum [US2] Implement `code/motifs.py` function `def count_motifs(adj_matrix)` to enumerate all possible directed subgraphs of a fixed small order for the binary connectome using `networkx.algorithms.motifs` or a custom DFS enumerator. **Algorithm**: Use `networkx.algorithms.motifs.subgraph_isomorphisms` or equivalent. **Dependency**: T014c.
- [X] T025a_timeout [US2] Implement `code/motifs.py` function `def count_motifs_with_timeout(adj_matrix, timeout=300)` to wrap T025a_enum using `multiprocessing` with a timeout. If timeout exceeded, raise `TimeoutError` and log warning. **Dependency**: T025a_enum.
- [X] T025b_zscore [US2] Implement `code/motifs.py` function `def compute_z_scores(counts, null_counts)` to compute z‑score prevalence: `z = (observed - mean_null) / std_null` for each of the 13 motifs. Input: counts from T025a_timeout, null counts (multiple iterations). Output: in-memory dict of z-scores per motif. **Dependency**: T025a_timeout.
- [X] T046_func [US2] Implement `code/motifs.py` function `def run_sensitivity_analysis(subject_id, thresholds=[, 2.0, 2.5])` to iterate over z-thresholds and compute motif profiles for each. **Logic**: Re-use null models where possible to optimize. **Dependency**: T025b_zscore.
- [X] T046_run [US2] Implement `code/motifs.py` orchestration to iterate T046_func for all subjects and save `data/processed/sensitivity_z<value>.json` for each threshold. **Constraint**: Ensure execution time is bounded to respect SC-002 (300s/subject). **Dependency**: T046_func.
- [X] T025c_agg [US2] Implement `code/motifs.py` to iterate T025a_timeout and T025b_zscore for each subject and aggregate z-scores into a single `data/processed/motif_profiles.json` containing the final aggregated scores (one profile per subject). **Schema**: `{'subject_id': {'motif_id': {'z_score': float, 'count': int}}}`. **Note**: This task must wait for T025a/T025b completion for *all* subjects before aggregating. **Dependency**: T025a_timeout, T025b_zscore, T046_run.
- [X] T026 [US2] Implement `code/motifs.py` to save `data/processed/motif_profiles.json` containing the final aggregated scores and a reference to the raw data file. **Dependency**: T025c_agg.

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

**Re-validated Tasks**: T032c (permutation test iteration) and T035b (PDF generation) are confirmed as active and mandatory tasks for FR-006 and FR-007. The previous "Removed Tasks" note was a false positive and has been deleted.

- [X] T039 [US3] Implement `code/stats.py` to aggregate `data/processed/global_efficiency.json`, `data/processed/rsfc.npy`, `data/processed/motif_profiles.json`, and `data/processed/canonical_binary_adj.npy` (to compute network density) into a single `data/processed/subject_metrics.csv`. **Success Rate Logic**: Read status flags from `data/processed/structural_connectome_metadata.json` (from T014c) and `data/processed/global_efficiency.json` (from T015). A subject is 'complete' if both files exist and contain valid data. Calculate `success_rate = complete / total`. **Output**: `data/processed/subject_metrics.csv` and `data/processed/success_rate.json`. **Columns**: [subject_id, motif_id, z_score, rsfc_strength, global_efficiency, node_degree, network_density]. **Explicit Definition**: `rsfc_strength` = mean of absolute values of the upper triangle of the rsfc matrix. `node_degree` = mean of row sums of the binary adjacency matrix. `network_density` = node_degree / (N-1). **Dependency**: T014c, T015, T025c_agg.
- [X] T030a [US3] Implement `code/stats.py` function `def check_vif_and_select_method(metrics)` to compute VIF for control variable (**global node degree**). **Explicit Definition**: `global_node_degree` = mean of row sums of the binary adjacency matrix. **Zero-Variance Logic**: Explicitly check if `std(z_scores) == 0` for any motif. **VIF Fallback**: If VIF > 5, switch to permutation-only analysis as per Plan Phase 2. **Output**: Save `data/processed/quality_flags.json` with schema: `{"zero_variance": bool, "vif_value": float, "method_selected": str}`. **Constraint**: The control variable MUST be 'global_node_degree' as per Spec FR-005. **Input**: Read from `data/processed/subject_metrics.csv`. **Dependency**: T039.
- [X] T030b [US3] Implement `code/stats.py` function `def compute_partial_correlations(metrics, control_var='global_node_degree')` to compute **both Pearson and Spearman** partial correlations between motif z-scores and rsFC metrics, controlling for `global_node_degree`. **Explicit Constraint**: The `control_var` parameter MUST be set to 'global_node_degree' as per Spec FR-005. Both methods must be computed and reported. **Dependency**: T030a.
- [X] T030c [US3] Implement `code/stats.py` to apply **Bonferroni correction** across all directed 3‑node motifs. **Strict Requirement**: Implement Bonferroni by multiplying each p-value by the total number of motifs tested (N_motifs). Use `statsmodels.stats.multitest.multipletests` with `method='bonferroni'`. Output: `results/correlation_results.json`. **Dependency**: T030b.
- [X] T032a [US3] Implement `code/stats.py` function `def identify_significant_motifs(results)` to filter motifs with corrected p < 0.05. Handle edge case: if no significant motifs, skip permutation test. **Dependency**: T030c, T030a.
- [X] T032b [US3] Implement `code/stats.py` function `def run_permutation_test(motif_data, n_perm=1000)` to run permutation test (≥1000 permutations) for a **single** significant motif. **Null Hypothesis**: No correlation. **Statistic**: Pearson r. **Output**: Empirical p-value. **Dependency**: T032a.
- [X] T032c [US3] Implement `code/stats.py` to **iterate** T032b over the list of significant motifs identified in T032a and aggregate the results into `results/permutation_results.json`. **Schema**: `[{"motif_id": str, "empirical_p": float, "original_r": float},...]`. **Explicit Requirement**: This task satisfies Spec FR-006's requirement to run a permutation test for *each* significant motif. **Dependency**: T032b, T032a.
- [X] T034 [US3] Implement `code/stats.py` power analysis module (N=50, α=0.05 **Bonferroni-adjusted**) using `statsmodels.stats.power` for approximation; **Explicit Requirement**: Log the exact `statsmodels` version and the random seed used for the calculation to `pipeline.log` and include them in `results/power_analysis.json`. **Assumption**: Assuming a standard level of statistical power (0.80) as per common practice. Output schema: `{"min_detectable_r": float, "power_level": 0.80, "adjusted_alpha": float, "n_subjects": int, "statsmodels_version": str, "seed": int}`. **Dependency**: T030c.
- [X] T035a [US3] Design PDF report layout in `docs/report_layout_template.json`: Create a JSON template file with schema: `{"pages": [{"type": str, "elements": [{"type": str, "source_field": str}]}]}`. Define page structure, library usage (reportlab), and data mapping from `results/correlation_results.json` to PDF elements. **Explicit Output**: `docs/report_layout_template.json` and `results/power_analysis.json` schema definition. **Dependency**: Spec FR-007, FR-009.
- [X] T035b [US3] Implement `code/report.py` to generate PDF based on T035a design. **Mapping**: Map fields from input JSONs to the layout template in `docs/report_layout_template.json`. **Validation**: Read the layout template from `docs/report_layout_template.json`; if missing or invalid, raise FileNotFoundError. Input: `results/correlation_results.json`, `results/permutation_results.json`, `results/power_analysis.json`, `docs/report_layout_template.json`. **Dependency**: T035a, T032c, T034.
- [X] T036 [US3] Add mandatory disclaimer string: "These findings are associational only and do not imply causation." to PDF. **Dependency**: T035b.
- [X] T037a [US3] Implement PDF generation logic in `code/report.py` ensuring layout, plots, and text are correctly rendered. **Dependency**: T035b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `docs/` (README, usage guide)
- [X] T041 [P] Performance optimization for `code/motifs.py` to verify SC-002 compliance (≤300s/subject)
- [X] T042 [P] Run `scripts/hash_artifacts.sh` to finalize versioning and update `state/...yaml`
- [ ] T043 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T044 [P] Run `quickstart.md` validation
- [X] T045 [P] [US1] Implement streaming download logic in `code/download.py` to handle subjects sequentially (download -> process -> delete raw) to respect CI disk limits, ensuring no raw NIfTI files accumulate. **Dependency**: T013. <!-- ATOMIZE: requested -->
- [X] T048 [P] [US3] Add a "Methods" section generator in `code/report.py` to programmatically extract statistical parameters (Bonferroni alpha, permutation count, seed, VIF threshold) from `pipeline.log` and embed them in the PDF, ensuring Statistical Transparency (Constitution Principle VII). **Dependency**: T035b.
- [X] T049 [P] [US1] Create a `scripts/verify_hcp_access.sh` script to pre-validate connectivity to the HCP S3 bucket and generate a `data/raw/.access_verified` flag before the main pipeline runs, reducing CI timeout risks. **Dependency**: T013.
- [X] T050 [P] [US2] Implement a `code/motifs.py` fallback to `igraph` if `networkx` motif enumeration exceeds the 300s timeout, logging the switch and ensuring SC-002 is met. **Dependency**: T025a_timeout.
- [X] T051 [P] [US3] Add a "Sensitivity Analysis" page to the PDF report in `code/report.py` to visualize how the number of significant motifs changes across the z-thresholds (, 2.0, 2.5), satisfying the Spec Edge Case requirement. **Dependency**: T046_run. <!-- ATOMIZE: requested -->
- [X] T052 [P] [US3] Implement a `code/stats.py` function `def report_insufficient_variance(motif_id)` to generate a specific entry in the PDF report for motifs with zero variance, explicitly stating "insufficient variance" instead of a p-value, as per Spec Edge Case. **Dependency**: T030a.

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
- **Spec vs Plan Conflict**: Where Spec FR-005 mandates Bonferroni and Plan suggests FDR, tasks follow the **Spec** (Bonferroni). Where Plan Phase 3 mandates controlling for 'network density' and Spec FR-005 says 'global node degree', tasks follow the **Spec** (global node degree).
- **Task Splitting**: T030 split into T030a (VIF/Method), T030b (Correlation), T030c (Correction). T025 split into T025a (Count), T025b (Z-score), T025c_agg (Aggregation). T014 consolidated into T014 (Weighted) and T014c (Median Binarization). T032 split into T032b (Function), T032c (Orchestration). T039a merged into T039.
- **Data Integrity**: T013 strictly enforces "FAIL LOUDLY" on real data fetch errors; no synthetic fallbacks are permitted per Constitution Principle III.
- **Compute Feasibility**: T025a_timeout includes a strict 300s timeout to ensure SC-002 compliance; if exceeded, the subject is skipped for that motif and logged.
- **Data Flow**: T039 explicitly uses `motif_profiles.json` as the canonical input for correlation analysis, resolving the raw vs. aggregated ambiguity. T039 now calculates the success rate internally.
- **Artifact Clarity**: T025c_agg defines the schema for aggregated motif profiles, and T026 saves the final output without duplicating raw data, resolving the previous ambiguity.
- **Redundancy Resolution**: Task T039a has been removed and its logic merged into T039 to eliminate the circular dependency. T039 now handles the aggregation and success rate calculation in a single step.
- **Control Variable Clarity**: T030a and T030b strictly enforce 'global_node_degree' as the control variable, rejecting 'network_density' for the partial correlation despite its presence in the metrics dataframe (which is used for other purposes like logging).
- **Data Source Verification**: T013 must strictly use the verified HCP S3 bucket ID and anonymous access method as defined in `research.md`. If the execution stage provides a "VERIFIED REAL DATA SOURCE" block, T013 must adopt that exact package/recipe and remove any hardcoded URL guesses.
- **Streaming Strategy**: If the HCP dataset size exceeds runner limits during execution, T013 must implement a streaming download pattern (e.g., `requests` with `stream=True` and chunked writing) rather than loading full files into memory, ensuring the "FAIL LOUDLY" rule is maintained without synthetic fallbacks.
- **Re-validated Tasks**: T032c (permutation test iteration) and T035b (PDF generation) are confirmed as active and mandatory tasks for FR-006 and FR-007. The previous "Removed Tasks" note was a false positive and has been deleted.
- **Success Rate Logic**: T039 calculates the end-to-end success rate by reading status flags from `structural_connectome_metadata.json` and `global_efficiency.json`, ensuring SC-001 is not inflated by ignoring later-stage failures.
- **Algorithm Clarity**: T014c uses the median graph density threshold (cohort-level) for binarization, correcting the previous fixed [deferred] logic. T025a uses a custom 3-node subgraph enumerator for all directed motifs. T030b computes both Pearson and Spearman correlations as required by FR-005.
- **Power Analysis**: T034 assumes a standard power level of sufficient statistical power as per common practice, since the spec does not mandate a specific value.
- **Single Source of Truth**: All tasks now strictly adhere to a single canonical binary connectome (median threshold) and a single motif profile per subject, eliminating unrequested multi-threshold analyses.
- **Statistical Transparency**: T017 explicitly mandates logging of all statistical parameters (Bonferroni alpha, permutation count, seed, library versions) to `pipeline.log`.
- **Global Efficiency Consistency**: T015 now computes global efficiency on the binary connectome, ensuring consistency with motif analysis.
- **Control Variable Enforcement**: T030a and T030b strictly enforce 'global_node_degree' as the control variable per Spec FR-005.
- **PDF Generation Robustness**: T035b includes explicit validation for the layout template file (created by T035a).
- **New Revision Tasks**: T045-T052 address specific review concerns regarding CI disk constraints, sensitivity analysis, power analysis modularity, statistical transparency in the report, HCP access validation, performance fallbacks, and zero-variance reporting.
- **Sensitivity Analysis**: T046_func and T046_run ensure the sensitivity analysis loop {1.5, 2.0, 2.5} is performed as part of the core path (Phase 4), satisfying Spec Edge Cases.
- **VIF Fallback**: T030a explicitly implements the Plan's fallback strategy (switch to permutation-only if VIF > 5).
- **Missing Tasks Restored**: T014c (Median Threshold) and T035a (Layout Design) have been restored to the list to match the Plan's requirements.
- **Circular Dependency Resolved**: T039a removed; T039 now handles success rate calculation internally.