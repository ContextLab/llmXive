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

## Phase 1: Setup & Data Contracts (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and defining data contracts (schemas) as required by Plan Phase 1.

- [ ] T001 [P] Create project directory structure: `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/logs/`, `results/`, `state/`
- [X] T002 [P] Initialize Python project with `requirements.txt` (numpy, scipy, pandas, networkx, matplotlib, seaborn, nibabel, requests, reportlab, tqdm, joblib, dipy, statsmodels, weasyprint)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools
- [ ] T009 [P] Validate and finalize `specs/feature/motif-rsfc/data-model.md` defining all data entities, their relationships, and file formats. **Deliverable**: `data-model.md`. **Dependency**: T001.
- [ ] T010 [P] Create `specs/feature/motif-rsfc/contracts/dataset.schema.yaml` defining the schema for raw input metadata. **Deliverable**: `dataset.schema.yaml`. **Dependency**: T009.
- [ ] T011 [P] Create `specs/feature/motif-rsfc/contracts/motif_profile.schema.yaml` defining the schema for motif z-scores. **Deliverable**: `motif_profile.schema.yaml`. **Dependency**: T009.
- [ ] T012 [P] Create `specs/feature/motif-rsfc/contracts/results.schema.yaml` defining the schema for correlation results. **Deliverable**: `results.schema.yaml`. **Dependency**: T009.
- [ ] T013 [P] Create `specs/feature/motif-rsfc/contracts/analysis_results.schema.yaml` defining the schema for statistical outputs (power analysis, permutation). **Deliverable**: `analysis_results.schema.yaml`. **Dependency**: T009.
- [ ] T014 [P] Create `specs/feature/motif-rsfc/contracts/structural_connectome.schema.yaml` defining the schema for subject processing status and derived matrices. **Deliverable**: `structural_connectome.schema.yaml`. **Dependency**: T009.
- [ ] T015 [P] [US1] Implement `quickstart.md` with step-by-step guide to run the full pipeline on a fresh environment. **Deliverable**: `quickstart.md`. **Content**: Include installation, configuration, execution command, and expected outputs. **Dependency**: T001, T002.
- [ ] T016 [P] [Docs] Implement `README.md` at repository root with project overview, installation instructions, and usage guide. **Deliverable**: `README.md`. **Content**: Include dependency list, quick start, and contribution guide. **Dependency**: T001, T002.
- [X] T004 [P] Implement `code/config.py` with paths, seeds, `EXPECTED_COHORT_SIZE`, and constants. **Add**: `N_MOTIF_NODES` (default 3) to allow configurable motif size per FR-004.
- [X] T005 [P] Implement `code/utils.py` for logging (to `pipeline.log`), error handling, and file I/O
- [X] T006 [P] Create `scripts/hash_artifacts.sh` to generate SHA checksums and update `state/...yaml`
- [X] T007 [P] Setup `tests/conftest.py` and mock data fixtures for CI-safe testing
- [ ] T008 [P] [US1] Implement `code/download.py` function `def load_subject_list(subject_ids_file)` to load the list of subject IDs, validate the file exists, and write `data/processed/subject_list_manifest.json` containing `{"total_subjects": int, "subject_ids": [str], "subjects_attempted": int}`. **Purpose**: Establish the denominator for SC-001 success rate verification. **Dependency**: T004.
- [ ] T008_validate [US1] Implement `code/download.py` function `def validate_subject_manifest(manifest_path)` to verify that the 'total_subjects' count in the manifest matches `config.EXPECTED_COHORT_SIZE`. **Output**: Raise an error if the manifest is invalid. **Dependency**: T008.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T017 [US1] Implement `code/utils.py` logging wrapper to ensure all processing steps, warnings, and errors are logged to `data/logs/pipeline.log` as per FR-008, including explicit validation that the log contains Bonferroni alpha, seed, library versions, permutation count, and VIF threshold as per Constitution Principle VII. **Dependency**: T005.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑End Data Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically retrieve, preprocess, and store structural and resting‑state functional data for a cohort of subjects.

**Independent Test**: Execute the pipeline on a fresh CI runner; verify that for each of the selected subjects a binary structural connectome (Schaefer‑parcellation) and an rsFC matrix are saved to the designated output folder.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T018 [P] [US1] Unit test for data download logic in `tests/unit/test_download.py`: **Contract**: Verify `download_subject_data(subject_id)` returns a dict with keys `{'dwi_path', 'rsfmri_path'}` or raises `FileNotFoundError` if missing; assert SHA checksums match `data/raw/.checksums.json` for valid files.
- [ ] T019 [P] [US1] Unit test for parcellation logic in `tests/unit/test_preprocess.py`: **Contract**: Verify `parcellate_connectome(streamlines_path, atlas_path)` returns a numpy array of shape (N, N) with a floating-point data type, where N corresponds to the number of regions in the specified atlas.; assert values are non-negative and density is within the expected valid range.
- [ ] T020 [P] [US1] Integration test for full pipeline on 2 subjects in `tests/integration/test_pipeline.py`: **Contract**: Run end-end on mock subjects; assert `data/processed/` contains `structural.npy` and `rsfc.npy` for each subject.; assert `data/logs/pipeline.log` contains "Processed all subjects" without errors.

### Implementation for User Story 1

- [ ] T013_stream [US1] Implement `code/download.py` function `def stream_and_process_subject(subject_id)` that:
 1. Downloads the subject's DWI data in chunks using `requests` with `stream=True`.
 2. **Retry Logic**: If HCP S3 is inaccessible (network error), retry up to 3 times with exponential backoff. If still inaccessible, log error and **skip subject** (do not fail pipeline).
 3. If data is missing (404), log warning and **skip subject**.
 4. **Persistence**: Store the raw file in `data/raw/` and generate a SHA checksum recorded in `data/raw/.checksums.json`. **Do NOT delete raw data**.
 5. Applies Schaefer parcellation to generate the weighted adjacency matrix.
 6. Saves the derived `.npy` to `data/processed/`.
 7. **FAIL LOUDLY** only on unrecoverable local errors (e.g., disk full, permission denied).
 **Constraint**: Ensure disk usage never exceeds runner limits. **Note**: Raw HCP data is persisted in `data/raw/` as per Constitution Principle VI; derived matrices are stored in `data/processed/`. **Dependency**: T008_validate.
- [ ] T014 [US1] Implement `code/preprocess.py` function `def parcellate_to_weighted(streamlines_path, atlas_path)` to apply Schaefer parcellation to DWI streamlines -> **Weighted Adjacency** (streamline count). Input: `.trk/.tck` (from T013_stream), `.nii.gz` atlas. Output: `data/processed/weighted_adjacency.npy`. **Explicit Constraint**: This task produces the weighted matrix only. Binarization is handled in T014_bin. **Dependency**: T013_stream.
- [ ] T014_agg [US1] Implement `code/preprocess.py` function `def aggregate_weighted_matrices()` to iterate over all `data/processed/*/weighted_adjacency.npy` files (using `glob.glob`) generated by T014 for **all subjects**, compute the **median graph density** across the entire cohort, and save the result to `data/processed/cohort_threshold.json` (`{"median_density": float}`). **Purpose**: Provide the cohort-level threshold required for T014_bin. **Constraint**: Ensure all weighted matrices generated by T014 are retained in `data/processed/` until this aggregation is complete; do not delete intermediates before this step. **Dependency**: T014 (execution for all subjects).
- [ ] T014_bin [US1] Implement `code/preprocess.py` function `def binarize_by_median_density()` to apply the cohort-level threshold from T014_agg to binarize **each subject's matrix**. **Plan Compliance**: This task explicitly implements the "median graph density threshold" strategy required by Plan Phase 2. **Clarification**: This threshold applies to structural binarization. The z-score sensitivity sweep (, 2.0, 2.5) applies to motif significance (T025c_loop), NOT structural binarization. **Orchestration**: This is a single task that iterates over all subjects' weighted matrices after T014_agg completes. **Input**: `data/processed/weighted_adjacency.npy` (for all subjects), `data/processed/cohort_threshold.json`. Output: `data/processed/canonical_binary_adj.npy` (binary) and `data/processed/structural_connectome_metadata.json` (status flags: 'complete', 'skipped'). **Dependency**: T014, T014_agg.
- [ ] T014_bin_validate [US1] Implement `code/preprocess.py` function `def validate_binary_connectome(binary_adj_path)` to verify the binary nature of the input for T015b against the weighted output of T014, ensuring **FR-002 compliance**. **Dependency**: T014_bin.
- [ ] T015b [US1] Implement `code/preprocess.py` function `def compute_global_efficiency(binary_adj_path)` to compute **Global Efficiency** on the **binary structural connectome** (`data/processed/canonical_binary_adj.npy`). **Formula**: E = (1/(N*(N-1))) * sum(1/d_ij) for i!=j. Use `networkx.global_efficiency`. **Justification**: Global efficiency is calculated on the binary graph to maintain consistency with the motif analysis (FR-004) and FR-002's binary connectome requirement. **Schema**: `data/processed/global_efficiency.json` = `{'subject_id': str, 'global_efficiency': float}`. **Output**: `data/processed/global_efficiency.json`. **Dependency**: T014_bin_validate, T014_agg.
- [ ] T015a [US1] Implement `code/preprocess.py` function `def compute_rsfc(rsfmri_path)` to compute rsFC (Pearson correlation of BOLD time‑series) and save `data/processed/rsfc.npy`. **Independent**: This task does NOT depend on structural data. **Dependency**: T013_stream.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Motif Quantification (Priority: P2)

**Goal**: Enumerate all 3‑node subgraphs in each structural connectome, compute z‑score prevalence against degree‑preserving null models, and store the motif profile.

**Independent Test**: Run the motif‑counting script on a single preprocessed structural matrix; verify that a JSON file containing z‑scores for each motif type is produced and matches a reference output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for motif enumeration correctness in `tests/unit/test_motifs.py`: **Contract**: Verify `count_motifs(adj_matrix, n=3)` returns a dict with counts for all directed 3-node motifs; assert sum of counts equals the theoretical total number of directed k-node subgraphs for a complete graph.
- [ ] T022 [P] [US2] Unit test for null model generation (Maslov-Sneppen) in `tests/unit/test_motifs.py`: **Contract**: Verify `generate_null_model(adj_matrix, iterations=100)` preserves degree distribution; assert mean degree difference is < 1e-6.
- [ ] T023 [P] [US2] Integration test for timeout handling on large graphs in `tests/integration/test_motifs.py`: **Contract**: Run on a large-scale graph with a predefined timeout threshold; assert function raises `TimeoutError` and logs "Timeout warning" to `pipeline.log`.

### Implementation for User Story 2

- [ ] T025_scope_doc [US2] Implement `code/motifs.py` function `def document_motif_scope()` to document and validate the 'n=3' scope decision against the general 'n-node' requirement of FR-004, explicitly linking it to the Spec's Assumptions section. **Output**: `data/processed/motif_scope_doc.json`. **Dependency**: T014_bin.
- [ ] T025a_enum [US2] Implement `code/motifs.py` function `def count_motifs_custom(adj_matrix, n=3)` to enumerate all possible **directed 3-node subgraphs** using a **specialized 3-node pattern matching algorithm** (e.g., `networkx.algorithms.motifs` or custom 3-node specific logic). **Algorithm**: Use a specialized 3-node enumerator, NOT a general n-node solver, to ensure SC-002 compliance. **Configurability**: The function MUST accept `n` as a parameter (default 3) to satisfy FR-004's "all n-node subgraphs" requirement. The default `n=3` is set per Spec Assumptions. **Dependency**: T025_scope_doc.
- [ ] T025a_validate [US2] Implement `code/motifs.py` function `def validate_motif_enumerator()` to verify that `count_motifs_custom` correctly identifies all directed 3-node isomorphism classes by running it against a set of synthetic graphs with known motif counts. **Constraint**: This task MUST run BEFORE T025a_timeout to ensure the custom implementation is valid. **Dependency**: T025a_enum.
- [ ] T025a_timeout [US2] Implement `code/motifs.py` function `def count_motifs_with_timeout(adj_matrix, timeout=300, n=3)` to wrap T025a_enum using `multiprocessing` with a timeout. If timeout exceeded, raise `TimeoutError` and log warning. **Constraint**: Must use the custom enumerator to ensure SC-002 compliance (≤300s/subject). **Dependency**: T025a_validate.
- [ ] T025b_zscore [US2] Implement `code/motifs.py` function `def compute_z_scores(counts, null_counts)` to compute z‑score prevalence: `z = (observed - mean_null) / std_null` for each motif. Input: counts from T025a_timeout, null counts (multiple iterations). Output: in-memory dict of z-scores per motif. **Dependency**: T025a_timeout.
- [ ] T025c_agg [US2] Implement `code/motifs.py` to iterate T025a_timeout and T025b_zscore for each subject (using subject manifest) and aggregate z-scores into a single `data/processed/motif_profiles.json` containing the final aggregated scores (one profile per subject). **Schema**: `{'subject_id': {'motif_id': {'z_score': float, 'count': int}}}`. **Note**: This task must wait for T025a/T025b completion for *all* subjects before aggregating. **Dependency**: T025a_timeout, T025b_zscore.
- [ ] T025c_loop [US2] Implement `code/motifs.py` function `def run_sensitivity_analysis(subject_id, thresholds=[, 2.0, 2.5])` to iterate over z-thresholds and compute motif profiles for each. **Logic**: Re-use null models where possible to optimize. **Output**: Save `data/processed/sensitivity_z{threshold:.1f}.json` for each threshold (e.g., `sensitivity_z1.5.json`). **Dependency**: T025b_zscore.
- [ ] T025c_loop_run [US2] Implement `code/motifs.py` orchestration to iterate T025c_loop for all subjects and save `data/processed/sensitivity_z<value>.json` for each threshold. **Constraint**: Ensure execution time is bounded to respect SC-002 (300s/subject). **Dependency**: T025c_agg, T025c_loop.
- [ ] T026 [US2] Implement `code/motifs.py` to save `data/processed/motif_profiles.json` containing the final aggregated scores and a reference to the raw data file. **Dependency**: T025c_agg.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation & Reporting (Priority: P3)

**Goal**: Correlate motif prevalence scores with rsFC strength and global efficiency across subjects, apply **Bonferroni correction**, perform a permutation test, and automatically generate a PDF report.

**Independent Test**: Execute the analysis script on the full set of subjects.; verify that a `results.pdf` is generated containing one page per motif type with a scatter plot, partial correlation coefficient, corrected p‑value, and a statement of significance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for partial correlation and Bonferroni correction in `tests/unit/test_stats.py`: **Contract**: Verify `partial_corr(x, y, z)` returns correct r and p-value; verify `bonferroni_correct(p_values)` returns adjusted p-values summing to <= 1.0.
- [ ] T029 [P] [US3] Unit test for permutation test implementation in `tests/unit/test_stats.py`: **Contract**: Verify `permutation_test(x, y, n_perm=1000)` returns empirical p-value; assert p-value is within 2*SE of analytical p-value for known distributions.
- [ ] T037b [P] [US3] Unit test for PDF generation layout and content in `tests/unit/test_report.py`: **Contract**: Verify `generate_pdf(results)` creates a file <= 5MB; assert presence of mandatory disclaimer string.
- [ ] T038 [US3] Integration test in `tests/integration/test_report.py` to verify PDF generation completes in ≤2 minutes and file size ≤5MB (SC-004)

### Implementation for User Story 3

**Re-validated Tasks**: T032c (permutation test iteration) and T035b (PDF generation) are confirmed as active and mandatory tasks for FR-006 and FR-007. The previous "Removed Tasks" note was a false positive and has been deleted.

- [ ] T039 [US3] Implement `code/stats.py` to aggregate `data/processed/global_efficiency.json`, `data/processed/rsfc.npy`, `data/processed/motif_profiles.json`, and `data/processed/canonical_binary_adj.npy` (to compute network density) into a single `data/processed/subject_metrics.csv`. **Success Rate Logic**: Read status flags from `data/processed/structural_connectome_metadata.json` (from T014_bin) and `data/processed/global_efficiency.json` (from T015b). A subject is 'complete' if both files exist and contain valid data. Calculate `success_rate = complete / subjects_attempted` (using `subjects_attempted` from `data/processed/subject_list_manifest.json` from T008_validate, NOT `EXPECTED_COHORT_SIZE`). **Output**: `data/processed/subject_metrics.csv` and `data/processed/success_rate.json`. **Columns**: [subject_id, motif_id, z_score, rsfc_strength, global_efficiency, node_degree, network_density]. **Explicit Definition**: `rsfc_strength` = mean of absolute values of the upper triangle of the rsfc matrix. `node_degree` = mean of row sums of the binary adjacency matrix. `network_density` = node_degree / (N-1). **Dependency**: T014_bin, T015a, T015b, T025c_agg, T008_validate.
- [ ] T030a [US3] Implement `code/stats.py` function `def check_vif_and_select_method(metrics)` to compute VIF for control variable (**global node degree**). **Explicit Definition**: `global_node_degree` = mean of row sums of the binary adjacency matrix. **Zero-Variance Logic**: Explicitly check if `std(z_scores) == 0` for any motif. **VIF Fallback**: If VIF > 5, switch to permutation-only analysis (permutation test for p-value, but **still compute partial correlation coefficient**) as per Plan Phase 2. **Output**: Save `data/processed/quality_flags.json` with schema: `{"zero_variance": bool, "vif_value": float, "method_selected": str, "zero_variance_motifs": [str]}`. **Constraint**: The control variable MUST be 'global_node_degree' as per Spec FR-005. **Input**: Read from `data/processed/subject_metrics.csv`. **Dependency**: T039.
- [ ] T030b [US3] Implement `code/stats.py` function `def compute_partial_correlations(metrics, control_var='global_node_degree')` to compute **both Pearson and Spearman** partial correlations between motif z-scores and rsFC metrics, controlling for `global_node_degree`. **Explicit Constraint**: The `control_var` parameter MUST be set to 'global_node_degree' as per Spec FR-005. Both methods must be computed and reported. **Output**: Save **BOTH** Pearson and Spearman results to `data/processed/partial_correlations.json` with schema: `{"motif_id": {"pearson": {"r": float, "p": float}, "spearman": {"r": float, "p": float}}}`. **Dependency**: T030a.
- [ ] T030c [US3] Implement `code/stats.py` to apply **Bonferroni correction** across all directed 3-node motifs for **both Pearson and Spearman** p-values generated in T030b. **Strict Requirement**: Implement Bonferroni by multiplying each p-value by the total number of motifs tested (N_motifs). Use `statsmodels.stats.multitest.multipletests` with `method='bonferroni'`. **Note**: This is the **sole** method for primary conclusions. Output: `results/correlation_results.json`. **Dependency**: T030b.
- [ ] T032a [US3] Implement `code/stats.py` function `def identify_significant_motifs(results)` to filter motifs with corrected p < 0.05. Handle edge case: if no significant motifs, skip permutation test. **Dependency**: T030c, T030a.
- [ ] T032b [US3] Implement `code/stats.py` function `def run_permutation_test(motif_data, n_perm=1000)` to run permutation test (≥1000 permutations) for a **single** significant motif. **Null Hypothesis**: No correlation. **Statistic**: Pearson r. **Output**: Empirical p-value. **Dependency**: T032a.
- [ ] T032c [US3] Implement `code/stats.py` to **iterate** T032b over the list of significant motifs identified in T032a and aggregate the results into `results/permutation_results.json`. **Schema**: `[{"motif_id": str, "empirical_p": float, "original_r": float},...]`. **Explicit Requirement**: This task satisfies Spec FR-006's requirement to run a permutation test for *each* significant motif. **Dependency**: T032b, T032a.
- [ ] T034 [US3] Implement `code/stats.py` power analysis module (N=50, α=0.05 **Bonferroni-adjusted**, **Power=0.80**) using `statsmodels.stats.power` for approximation. **Input**: Use fixed power=0.80. **Explicit Requirement**: Log the exact `statsmodels` version, the random seed, and the power level to `pipeline.log` and include them in `results/power_analysis.json`. Output schema: `{"min_detectable_r": float, "power_level": float, "adjusted_alpha": float, "n_subjects": int, "statsmodels_version": str, "seed": int}`. **Dependency**: T030c, T039.
- [ ] T035a [US3] Design PDF report layout in `docs/report_layout_template.json`: Create a JSON template file with schema: `{"pages": [{"type": str, "elements": [{"type": str, "source_field": str}]}]}`. Define page structure, library usage (reportlab), and data mapping from `results/correlation_results.json` to PDF elements. **Explicit Output**: `docs/report_layout_template.json` and `results/power_analysis.json` schema definition. **Requirement**: The template MUST include a specific placeholder element named `disclaimer_placeholder` intended to hold the exact string: "These findings are associational only and do not imply causation.". **Dependency**: Spec FR-007, FR-009.
- [ ] T052 [US3] Implement `code/report.py` function `def report_insufficient_variance(motif_id)` to generate a specific entry in the PDF report for motifs with zero variance, explicitly stating "insufficient variance" instead of a p-value, as per Spec Edge Case. **Input**: Read `quality_flags.json` (from T030a) to identify zero-variance motifs. **Dependency**: T030a, T039.
- [ ] T058 [US3] Implement `code/stats.py` function `def calculate_effect_size_confidence_interval(r, n, alpha)` to compute the % confidence interval for the Pearson correlation coefficient using Fisher's z-transformation, using the **Bonferroni-adjusted alpha**, and integrate this into the PDF report scatter plots as error bars. **Dependency**: T030b, T039.
- [ ] T055 [US3] Implement `code/report.py` function `def generate_power_analysis_plot(power_data)` to create a visual representation of the minimum detectable effect size curve (r vs N) for the Bonferroni-adjusted alpha, including this plot in the PDF's power analysis section. **Dependency**: T034, T039.
- [ ] T051 [US3] Add a "Sensitivity Analysis" section or page to the PDF report in `code/report.py` to visualize how the number of significant motifs changes across the z-thresholds, satisfying the Spec Edge Case requirement. **Dependency**: T025c_loop_run, T039.
- [ ] T056 [US3] Add a "Limitations" section to the PDF report in `code/report.py` that explicitly states the constraints of the study (e.g., cross-sectional data, associational nature, specific parcellation used), satisfying the requirement for scientific transparency. **Dependency**: T039.
- [ ] T035b [US3] Implement `code/report.py` to generate PDF based on T035a design. **Mapping**: Map fields from input JSONs to the layout template in `docs/report_layout_template.json`. **Validation**: Read the layout template from `docs/report_layout_template.json`; if missing or invalid, raise FileNotFoundError. **Pre-condition**: Verify all input JSON files (`results/correlation_results.json`, `results/permutation_results.json`, `results/power_analysis.json`, `data/processed/subject_metrics.csv`) exist and are non-empty; if not, raise FileNotFoundError with a list of missing files. Input: `results/correlation_results.json`, `results/permutation_results.json`, `results/power_analysis.json`, `docs/report_layout_template.json`, and outputs from T052, T058, T055, T051, T056. **Mandatory**: Insert the exact string "These findings are associational only and do not imply causation." into the `disclaimer_placeholder` defined in T035a. **Dependency**: T035a, T032c, T034, T039, T052, T058, T055, T051, T056, T017b.
- [ ] T017b [US3] Implement `code/utils.py` function `def validate_statistical_logging(log_path)` to verify that `pipeline.log` contains the required statistical parameters (Bonferroni alpha, seed, library versions, permutation count, VIF threshold) as per Constitution Principle VII. If missing, raise an error. **Dependency**: T030c, T032c, T034 (Pipeline completion and parameter generation). **Note**: Moved to Phase 5 to ensure parameters exist.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Performance optimization for `code/motifs.py` to verify SC-002 compliance (≤300s/subject)
- [ ] T042 [P] Run `scripts/hash_artifacts.sh` to finalize versioning and update `state/...yaml`
- [ ] T043a [P] [Testing] Implement `tests/unit/test_preprocess.py`, `tests/unit/test_motifs.py`, `tests/unit/test_stats.py`, and `tests/integration/test_pipeline.py` with contract tests against YAML schemas. **Deliverable**: Complete test suite in `tests/`.
- [ ] T044a [P] [Validation] Implement `scripts/validate_quickstart.sh` to run the `quickstart.md` steps in a clean environment and verify all outputs. **Deliverable**: `scripts/validate_quickstart.sh`.
- [ ] T048 [US3] (Merged into T035b) Methods section generator logic integrated into PDF generation to extract statistical parameters from `pipeline.log`. **Dependency**: T035b, T039.
- [ ] T049 [P] [US1] Create a `scripts/verify_hcp_access.sh` script to pre-validate connectivity to the HCP S3 bucket and generate a `data/raw/.access_verified` flag before the main pipeline runs, reducing CI timeout risks. **Dependency**: T013_stream.
- [ ] T050 [P] [US2] Implement a `code/motifs.py` fallback to `igraph` if `networkx` motif enumeration exceeds the 300s timeout, logging the switch and ensuring SC-002 is met. **Dependency**: T025a_timeout.
- [ ] T054 [P] [US2] Add a `code/motifs.py` function `def validate_null_model_preservation(original_adj, null_adj)` that asserts the degree distribution of the null model matches the original within a tolerance of a sufficiently small value, logging a warning if the preservation fails, to ensure the z-score calculation is statistically valid. **Dependency**: T020.
- [ ] T059 [P] [US2] Add a `code/motifs.py` function `def benchmark_motif_enumeration()` that runs the custom enumerator on a subset of subjects and logs the time taken per subject to `pipeline.log`, ensuring SC-002 is met and providing data for potential optimization. **Dependency**: T025a_timeout.

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
- **Task Splitting**: T030 split into T030a (VIF/Method), T030b (Correlation), T030c (Correction). T025 split into T025a (Count), T025b (Z-score), T025c_agg (Aggregation). T014 consolidated into T014 (Weighted) and T014_bin (Median Binarization). T032 split into T032b (Function), T032c (Orchestration). T039a merged into T039.
- **Data Integrity**: T013_stream strictly enforces "Store raw data and checksum" per Constitution Principle VI; no deletion of raw data is permitted. T013_persist removed as its logic is now in T013_stream.
- **Compute Feasibility**: T025a_timeout includes a strict 300s timeout to ensure SC-002 compliance; if exceeded, the subject is skipped for that motif and logged.
- **Data Flow**: T039 explicitly uses `motif_profiles.json` as the canonical input for correlation analysis, resolving the raw vs. aggregated ambiguity. T039 now calculates the success rate internally using the manifest from T008_validate (using `subjects_attempted`).
- **Artifact Clarity**: T025c_agg defines the schema for aggregated motif profiles, and T026 saves the final output without duplicating raw data, resolving the previous ambiguity.
- **Redundancy Resolution**: Task T039a has been removed and its logic merged into T039 to eliminate the circular dependency. T039 now handles the aggregation and success rate calculation in a single step.
- **Control Variable Clarity**: T030a and T030b strictly enforce 'global_node_degree' as the control variable, rejecting 'network_density' for the partial correlation despite its presence in the metrics dataframe (which is used for other purposes like logging).
- **Data Source Verification**: T013_stream must strictly use the verified HCP S3 bucket ID and anonymous access method as defined in `research.md`. If the execution stage provides a "VERIFIED REAL DATA SOURCE" block, T013_stream must adopt that exact package/recipe and remove any hardcoded URL guesses.
- **Streaming Strategy**: T013_stream implements a streaming download pattern (e.g., `requests` with `stream=True` and chunked writing) to ensure the "FAIL LOUDLY" rule is maintained without synthetic fallbacks, while preserving raw data.
- **Re-validated Tasks**: T032c (permutation test iteration) and T035b (PDF generation) are confirmed as active and mandatory tasks for FR-006 and FR-007. The previous "Removed Tasks" note was a false positive and has been deleted.
- **Success Rate Logic**: T039 calculates the end-to-end success rate by reading status flags from `structural_connectome_metadata.json` and `global_efficiency.json`, ensuring SC-001 is not inflated by ignoring later-stage failures. Uses `subjects_attempted` from manifest.
- **Algorithm Clarity**: T014_bin uses the median graph density threshold (cohort-level) for binarization, correcting the previous fixed [deferred] logic. T025a uses a custom n-node subgraph enumerator (default n=3) for all directed motifs. T030b computes both Pearson and Spearman correlations as required by FR-005.
- **Power Analysis**: T034 uses a fixed power of 0.80 as required by FR-010, removing the unrequested sensitivity sweep.
- **Single Source of Truth**: All tasks now strictly adhere to a single canonical binary connectome (median threshold) and a single motif profile per subject, eliminating unrequested multi-threshold analyses.
- **Statistical Transparency**: T017 explicitly mandates logging of all statistical parameters (Bonferroni alpha, permutation count, seed, library versions) to `pipeline.log`. T017b validates this (moved to Phase 5).
- **Global Efficiency Consistency**: T015b now computes global efficiency on the binary connectome, ensuring consistency with motif analysis.
- **Control Variable Enforcement**: T030a and T030b strictly enforce 'global_node_degree' as the control variable per Spec FR-005.
- **PDF Generation Robustness**: T035b includes explicit validation for the layout template file (created by T035a) and includes the mandatory disclaimer. T035a explicitly defines the disclaimer content.
- **New Revision Tasks**: T045-T056 address specific review concerns regarding CI disk constraints, sensitivity analysis, power analysis modularity, statistical transparency in the report, HCP access validation, performance fallbacks, zero-variance reporting, and explicit streaming implementation.
- **Sensitivity Analysis**: T025c_loop and T025c_loop_run ensure the sensitivity analysis loop {1.5, 2.0, 2.5} is performed as part of the core path (Phase 4), satisfying Spec Edge Cases. **Note**: T025c_loop_run is now decoupled from the main aggregation T026.
- **VIF Fallback**: T030a explicitly implements the Plan's fallback strategy (switch to permutation-only if VIF > 5).
- **Missing Tasks Restored**: T014_bin (Median Threshold) and T035a (Layout Design) have been restored to the list to match the Plan's requirements.
- **Circular Dependency Resolved**: T039a removed; T039 now handles success rate calculation internally.
- **Streaming Implementation**: T013_stream implements the unified 'stream, process, persist, checksum' strategy. Raw data is preserved.
- **Null Model Validation**: T054 adds a verification step for the null model generation to ensure the z-score calculation is statistically sound.
- **Ordering Fixes**: T014_agg dependency clarified to be on the *execution* of T014 for all subjects. T025c_agg no longer depends on T046_run. T039 depends only on T025c_agg. T017b moved to Phase 5.
- **Documentation Tasks**: T040, T043, T044 replaced with specific tasks T040a, T043a, T044a.
- **Constraint Preservation**: T030c strictly implements Bonferroni; T030d (FDR) removed. T017b validates statistical logging. T013_stream ensures checksumming and retention of raw data. T034 uses fixed power. T030a ensures partial correlation is computed even in fallback mode.
- **Motif Enumerator Validation**: T025a_validate added to explicitly validate the custom n-node enumerator against known reference sets, ensuring the 'all n-node subgraphs' requirement is met.
- **Scope Documentation**: T025_scope_doc added to document the 'n=3' scope decision against the general 'n-node' requirement of FR-004.
- **Manifest Validation**: T008_validate added to verify the subject manifest integrity against the expected cohort size.
- **Binary Validation**: T014_bin_validate added to verify the binary nature of the input for T015b.
- **Task Status Correction**: T040a, T040b, T043a, T044a corrected from [X] to [ ] to reflect pending implementation.
- **Streaming Correction**: T013_stream ensures raw data is persisted to `data/raw/` before any processing, satisfying Constitution Principle VI.
- **Ambiguity Resolution**: T014_agg dependency clarified to be on the *execution* of T014 for all subjects.
- **Algorithm Detail**: T025a_enum updated to include the algorithmic logic or reference a specific algorithm for the n-node motifs (default 3).
- **Granularity Clarification**: T014_bin clarified to run as a post-processing step after all T014 instances are complete.
- **Redundancy Resolution**: T017a and T017b merged into a single task T017 (with T017b moved to Phase 5).
- **Power Analysis Correction**: T034a removed; T034 uses fixed power=0.80.
- **Motif Scope Fix**: T025a_enum explicitly states 'n-node subgraphs' with default n=3.
- **Parallelization Fix**: T015b [P] tag removed; T008_validate dependency clarified.
- **Dependency Chain Fix**: T017b now depends on T030c, T032c, T034. T035a no longer depends on T039.
- **Logging Consolidation**: T048 merged into T035b.
- **Alpha Clarity**: T058 explicitly uses Bonferroni-adjusted alpha.
- **File Discovery**: T014_agg uses glob pattern.
- **Cohort Size Source**: T008_validate reads from `config.EXPECTED_COHORT_SIZE`.
- **Motif ID Mapping**: T025a_enum uses 'M1'-'M13' naming for n=3.
- **Disk Limit Fix**: T013_stream removes arbitrary 2GB limit, adhering to runner limits, but prioritizes raw data retention.
- **Final Review Compliance**: T051 added to address the specific requirement for a "Sensitivity Analysis" page/section in the PDF report, ensuring the z-threshold sweep is visualized.
- **Final Review Compliance**: T061 (renamed T056) added to address the requirement for a "Limitations" section in the PDF report, ensuring scientific transparency.
- **ID Collision Fix**: Duplicate task IDs T010, T011, T012 (used for tests) have been renumbered to T018, T019, T020 to resolve ambiguity.
- **Task T009 Fix**: Changed from "Implement" to "Validate and finalize" to respect the prerequisite nature of data-model.md.