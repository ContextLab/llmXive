---
description: "Task list template for feature implementation"
---

# Tasks: Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

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

- [X] T001 [P] **Create Project Directory Structure**: Create `code/`, `data/`, `contracts/`, `tests/` directories and subdirectories as defined in the Plan (`data/raw`, `data/derived`, `data/logs`, `contracts/`, `code/`, `tests/unit`, `tests/integration`). Verify structure exists.
- [X] T002 Create `requirements.txt` pinning all dependencies (nilearn, networkx, scikit-learn, pandas, numpy, statsmodels, scipy, pyyaml>=6.0).
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black) tools in `pyproject.toml` or `.pre-commit-config.yaml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Create `code/config.py` structure for paths and seeds.
- [X] T004b [P] Define hyperparameters in `code/config.py`: `WINDOW_LENGTH_BASELINE = 30` (in TRs), `WINDOW_LENGTH_VALIDATION = [20]` (in TRs), `WINDOW_STEP = 1` (in TRs), `K_MEANS_K = 5`. **Constraint**: Define `BASELINE_DENSITY` (to be derived or set, e.g., 0.1). **Logic**: `DENSITY_THRESHOLD_VARIATIONS = [BASELINE_DENSITY minus a small offset, BASELINE_DENSITY, BASELINE_DENSITY plus a small offset]`. **Rationale**: FR-008 specifies '±5%' perturbation; variations must be explicit numeric offsets, not vague heuristics.
- [X] T005 [P] Create `code/__init__.py` and data loading utilities for HCP OpenNeuro data (dMRI/fMRI).
- [X] T006 [P] Implement `code/structural.py` skeleton with placeholder for graph metric calculation.
- [X] T007 [P] Implement `code/functional.py` skeleton for sliding-window and state extraction.
- [X] T008 [P] Create `code/correlation.py` skeleton for statistical testing.
- [X] T009 [P] Create `code/reports/generate_report.py` skeleton for final output.
- [X] T009a [P] **Create Documentation**: Write `docs/quickstart.md` with instructions to run the full pipeline end-to-end, including environment setup and data fetching.
- [X] T010 [P] Setup `data/` directory structure (raw, derived, logs) and `contracts/` schema files (`dataset.schema.yaml`, `output.schema.yaml`).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Structural and Dynamic Graph Metrics (Priority: P1) 🎯 MVP

**Goal**: Derive quantitative topological metrics (global efficiency, average clustering, modularity) from dMRI and dynamic functional states (dwell time, visited states) from fMRI for a cohort using Leave-One-Subject-Out (LOSO) to ensure independence.

**Independent Test**: Run pipeline on a single subject's preprocessed HCP data; verify output JSON contains non-null values for structural global efficiency, clustering, modularity, and dynamic state dwell times.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Unit test for `code/structural.py` graph metric calculation in `tests/unit/test_structural.py`.
- [X] T013 [P] [US1] Unit test for `code/functional.py` LOSO k-means state extraction in `tests/unit/test_functional.py`.
- [X] T013b [P] [US1] **CRITICAL**: Unit test for LOSO Independence Constraint in `tests/unit/test_functional.py`. Verify that for any subject `i`, the generated centroids are computed *exclusively* from the data of subjects `j != i`. Assert that subject `i`'s data is never included in the centroid generation step.
- [X] T014 [P] [US1] Integration test for single-subject pipeline in `tests/integration/test_single_subject.py`.

*Note on [P] tags: Tests T012-T014 are marked [P] meaning they can run in parallel once the code skeletons (T006, T007) exist. They must be written to FAIL first (TDD) before implementation tasks T015+ are run.*

### Implementation for User Story 1

- [X] T015a [US1] Implement structural graph metric calculation (global efficiency, clustering, modularity) in `code/structural.py` using NetworkX. **Constraint**: MUST consume `DENSITY_THRESHOLD_BASELINE` from `code/config.py`. **Logic**: If `DENSITY_THRESHOLD_BASELINE` is `None`, derive the value dynamically (e.g., median degree of the cohort) and log the derived value. **Dependency**: T004b.
- [X] T015b [US1] **Mandatory Sensitivity Analysis (Graph Density)**: Implement a loop in `code/structural.py` that iterates through `DENSITY_THRESHOLD_VARIATIONS` (defined as `BASELINE ± 0.05`). For each threshold, apply it to the adjacency matrix, compute graph metrics, and save results. **Output**: Save `data/derived/structural_density_sensitivity.csv` containing metrics for each density level. **Schema**: `subject_id, density_threshold, global_efficiency, clustering, modularity`. **Dependency**: T004b, T015a.
- [X] T016 [US1] Implement **Leave-One-Subject-Out (LOSO) K-Means Centroid Generation** in `code/functional.py`. **Logic**: For each subject `i` in the cohort:
 1. Compute sliding-window correlations (window_length=30 TR, step=1 TR) for all OTHER subjects (N-1).
 2. Concatenate these matrices and apply k-means (k=5) to generate **Subject-Specific LOSO Centroids**.
 3. **Output**: Save a structured file `data/derived/loo_centroids_all_subjects.npz` where keys are strictly named `f"centroids_{subject_id}"` and values are the `(5, 200)` centroid arrays derived *only* from `j != i`.
 4. **Constraint**: Must strictly enforce independence (subject `i` is never used to generate centroids for subject `i`).
 5. **Deviation Note**: This implements the Plan's LOSO strategy, deviating from FR-002's "common set" requirement. **Constitution Override**: Explicitly authorized by **Constitution Principle VI** (Structural-Functional Independence) to prevent circular correlation. This is a **Spec Amendment** to FR-002.
 6. **Mandatory Traceability**: Upon successful generation, the script MUST write an entry to `data/logs/methodology_deviations.json` explicitly stating: "FR-002 deviation: Replaced 'common set of recurrent states' with 'subject-specific LOSO centroids' per Constitution Principle VI."
 7. **Intermediate Output**: Also save `data/derived/state_assignments_per_subject.csv` containing the state assignments for each subject during the loop (columns: `subject_id, window_index, state_id`) to facilitate T017.
- [X] T017 [US1] Implement **LOSO State Assignment** in `code/functional.py`. **Logic**: Load `data/derived/loo_centroids_all_subjects.npz`. For each subject `i`:
 1. Retrieve the LOSO Centroids generated specifically for subject `i` (key: `f"centroids_{subject_id}"`).
 2. Assign windowed matrices of subject `i` to these centroids to determine state sequences (list of state IDs per time window).
 3. Calculate per-subject dynamic metrics: **Mean Dwell Time** and **Number of Visited States**.
 4. **Output**: Save per-subject state assignments and metrics to `data/derived/state_assignments.csv` and `data/derived/dynamic_metrics.csv`. **Schema for state_assignments.csv**: `subject_id, window_index, state_id`. **Schema for dynamic_metrics.csv**: `subject_id, state_id, mean_dwell_time, num_visits`.
 5. **Logging**: Log exclusion events (convergence failure, sparsity >90%) to `data/logs/exclusion_log.json` immediately upon detection.
- [X] T018 [US1] **Batch Processing and Aggregation**: Implement batch processing logic in `code/main.py` to aggregate metrics into `data/derived/structural_metrics.csv` and `data/derived/dynamic_metrics.csv`. **Logic**: Read `data/logs/exclusion_log.json` (from T017) to identify excluded subjects. Filter the raw metrics to exclude these subjects before aggregation. **Dependency**: T017 (for exclusion log), T015b (for structural metrics logic). **Verification**: Ensure subjects listed in `exclusion_log.json` are **absent** from `structural_metrics.csv` and `dynamic_metrics.csv`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.5: Data Completeness Aggregation

**Purpose**: Aggregate exclusion logs from all phases to satisfy SC-005.

- [X] T001a [P] **Data Acquisition & Validation**: Fetch datasets using `datasets.load_dataset` or direct BIDS download from OpenNeuro ds000224. Validate schema. Compute checksums. Log exclusions to `data/logs/exclusion_log.json`. **Output**: `data/raw/verified_manifest.json`.
- [X] T019a [US1] **Data Completeness Aggregation**: Implement a script in `code/analysis/` to read `data/logs/exclusion_log.json` (from T001a, T017, T018). **Logic**: Aggregate all exclusions into a single file `data/derived/exclusion_log.json`. Categorize exclusion reasons (e.g., "convergence failure", "sparsity >90%", "missing data"). **Output**: Save `data/derived/exclusion_log.json`. **Dependency**: T001a, T017, T018.
- [X] T019b [US1] **Data Completeness Report**: Implement a script in `code/analysis/` to read `data/derived/exclusion_log.json` (from T019a) and `data/derived/structural_metrics.csv` (from T018). Calculate the percentage of processed subjects against the **total available cohort size** (count of subjects in `data/raw/`). Categorize exclusion reasons. **Output**: Save `data/derived/completeness_report.json` to satisfy SC-005. **Dependency**: T019a, T018.

---

## Phase 4: User Story 2 - Perform Structure-Function Correlation Analysis (Priority: P2)

**Goal**: Statistically correlate structural topological metrics with dynamic functional metrics, applying FDR correction.

**Independent Test**: Run correlation script on aggregated CSV; verify output includes correlation matrix (r, p-values) and FDR-corrected flags.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for normality check (Shapiro-Wilk) and correlation selection in `tests/unit/test_correlation.py`.
- [X] T022 [P] [US2] Unit test for Benjamini-Hochberg FDR correction in `tests/unit/test_correlation.py`.
- [X] T023 [P] [US2] Integration test for end-to-end correlation analysis in `tests/integration/test_correlation.py`.

### Implementation for User Story 2

- [X] T024 [US2] Implement normality testing (Shapiro-Wilk, α=0.05) in `code/correlation.py`. **Constraint**: Must implement conditional logic: **If** Shapiro-Wilk p < 0.05, **Then** use Spearman's rank correlation; **Else** use Pearson's correlation.
- [X] T025 [US2] Implement correlation calculation between structural and dynamic metrics across the cohort in `code/correlation.py`.
- [X] T026 [US2] Implement Benjamini-Hochberg FDR correction (q=0.05) on all p-values in `code/correlation.py`.
- [X] T027 [US2] Generate `data/derived/correlation_results.csv` containing r-values, raw p-values, and FDR-corrected p-values.
- [X] T028 [US2] Handle edge case: If FDR correction yields zero significant findings, ensure report explicitly states this rather than omitting results.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Robustness and Methodological Reports (Priority: P3)

**Goal**: Verify robustness to parameter choices (window length, threshold density, tractography confidence) and ensure "associational" framing.

**Independent Test**: Compare primary report with robustness report; verify "associational" labels, sensitivity tables, and tractography noise analysis are present.

**⚠️ Phase 5 Execution Order**: Tasks T031, T032, T040-T043 (Sensitivity Generation) MUST complete BEFORE Task T034 (Report Generation). The Report Task depends on all sensitivity artifacts.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for sensitivity analysis logic in `tests/unit/test_robustness.py`.
- [X] T030 [P] [US3] Integration test for full robustness report generation in `tests/integration/test_robustness.py`. **Scenario**: Run the full pipeline on a single subject with varying TR windows; verify the output CSV contains the absolute difference in correlation coefficients for all metric pairs.

### Implementation for User Story 3

- [X] T031 [US3] **Mandatory 20 TR Validation - Full Cohort Execution**: Implement a full re-run of the dynamic metric extraction (T016/T017 logic) and correlation analysis (T025) for **window_length=20 TR** on the **full cohort**. **Requirement**: This is a mandatory validation of metric stability (Constitution Principle VII) and FR-006. **Logic**: Use streaming to process the full cohort in chunks to stay within RAM limits. Do NOT use a subset or abort strategy. **Output**: Save `data/derived/sensitivity_window.csv` containing the absolute difference in correlation coefficients for all metric pairs between 30 TR and 20 TR. **Dependency**: `code/functional.py` (T016/T017 logic), `code/correlation.py` (T025 logic), `data/raw/` (input data).
- [X] T032 [US3] **Mandatory Density Sensitivity - Correlation Level**: Implement a script in `code/analysis/` that re-runs the correlation analysis (T025) using the structural metrics generated at varying density thresholds (from `data/derived/structural_density_sensitivity.csv` via T015b). **Logic**: Iterate through each density threshold, pair the structural metrics with the dynamic metrics (from T018), and compute correlation coefficients (r) and p-values. **Output**: Save `data/derived/density_correlation_sensitivity.csv` showing how the association between structure and function changes across density thresholds. **Dependency**: T015b, T018, T025. **FR-008 Compliance**: This task explicitly verifies result robustness (SC-002) by testing the stability of the statistical association across thresholds.
- [X] T033a [US3] **Resource Usage Monitoring**: Implement resource usage monitoring (peak RAM, runtime) in `code/main.py` to verify CPU-only constraints (limited memory and time).
- [X] T033b [US3] **Resource Usage Report Generation**: Implement a script to aggregate the monitoring data from T033a and output a specific artifact `artifacts/resource_usage_report.json` containing peak RAM, total runtime, and a pass/fail status against the 7GB/6h constraints. **Dependency**: T033a.
- [X] T034 [US3] Generate final report in `code/reports/generate_report.py` with explicit "associational" framing (FR-007) and sensitivity tables. **Requirement**: The report MUST explicitly calculate and display:
 1. The "absolute difference between 30 TR and 20 TR correlation coefficients" (from `data/derived/sensitivity_window.csv` generated in T031).
 2. A table or plot showing how statistical power changes across the **graph density thresholds** (from `data/derived/density_correlation_sensitivity.csv` generated in T032).
 3. A table showing the change in correlation coefficients across **tractography confidence thresholds** (from `data/derived/tractography_correlation_sensitivity.csv` generated in T043).
 **Dependency**: T031, T032, T043, T033b.
- [X] T035 [US3] Validate report against `contracts/output.schema.yaml` to ensure all required fields (r, p, FDR, sensitivity, absolute difference, density analysis) are present.

### Implementation for Revision Concerns (Tractography Noise Sensitivity)

**Context**: Address the specific concern raised by `john-von-neumann-simulated` regarding tractography false-positive rates (Yeh et al.) and the potential for noise to drive spurious correlations. This analysis is mapped to **FR-008** (Threshold Sensitivity) and **SC-002** (Robustness of findings) as a specific instantiation of threshold variation (confidence vs density). **Scope Extension**: This task set is a reviewer-mandated extension of FR-008, formally authorized as a Spec Amendment.

- [X] T040 [P] [Rev] Unit test for tractography confidence thresholding logic in `tests/unit/test_tractography.py`. Verify that the thresholding function correctly filters edges based on confidence scores and that the graph topology changes as expected.
- [X] T041 [Rev] **Tractography Confidence Thresholding - Setup**: Extend `code/config.py` to define a range of tractography confidence thresholds spanning from the minimum to the maximum possible values. Ensure the structural data loader in `code/structural.py` accepts a `confidence_threshold` parameter. **FR-008 Mapping**: This implements the "thresholding strategy" sensitivity required by FR-008, applied to confidence scores.
- [X] T042a [Rev] **Tractography Thresholding Loop**: Implement a loop in `code/analysis/tractography_sensitivity.py` that iterates through the defined confidence thresholds. For each threshold, reload the raw dMRI data and apply the confidence filter. **Output**: Intermediate filtered matrices. **Dependency**: T041.
- [X] T042b [Rev] **Graph Metric Recalculation**: For each confidence threshold (from T042a), recalculate the structural connectivity matrices and compute graph metrics (global efficiency, clustering, modularity). **Output**: Save `data/derived/tractography_sensitivity_metrics.csv` containing metrics for each subject at each confidence level. **Dependency**: T042a, T015a.
- [X] T043 [Rev] **Tractography-Function Correlation Sensitivity**: Implement a script in `code/analysis/` that re-runs the correlation analysis (US2) for each tractography confidence threshold.
 1. Load `data/derived/tractography_sensitivity_metrics.csv` (from T042b) and `data/derived/dynamic_metrics.csv` (from T018).
 2. For each confidence threshold, pair the structural metrics with the dynamic metrics and compute correlation coefficients (r) and p-values using the logic from T025.
 3. Apply FDR correction (T026) for each threshold set.
 4. **Output**: Save `data/derived/tractography_correlation_sensitivity.csv` showing how the association between structure and function changes as the structural data becomes "cleaner" (higher confidence).
 5. **FR-008/SC-002 Compliance**: This task is critical for verifying that the "associational" findings are not artifacts of false-positive tractography edges.
 6. **Dependency**: T042b (structural metrics), T024-T027 (US2 completion). **Output Dependency**: This task produces the artifact required by T034.
- [X] T044 [Rev] **Robustness Report Integration**: Update `code/reports/generate_report.py` to include a dedicated section on "Tractography Noise Sensitivity".
 1. Explicitly state the false-positive rate concern (citing Yeh et al.).
 2. Present a table/plot showing the change in statistical power (or significance) across the confidence thresholds using data from `data/derived/tractography_correlation_sensitivity.csv` (generated in T043).
 3. **Conclusion**: If the findings vanish at high confidence thresholds, the report must explicitly state that the original findings may be driven by tractography artifacts.
 4. **Dependency**: T043 (correlation sensitivity data).

**Checkpoint**: All user stories and revision concerns should now be independently functional

---

## Phase 6: Final Validation & Handoff

**Purpose**: Ensure the project is ready for execution and validation against all constraints.

- [X] T060 [P] **Final Data Source Verification**: Run a dry-run of `code/structural.py` and `code/functional.py` against the real OpenNeuro dataset (ds000224) to confirm the data loader fails loudly if the URL is unreachable, without falling back to synthetic data. **Verification**: Assert exit code 1 and log contains "URL unreachable" or "Connection refused". **Output**: Save `data/logs/data_source_verification.json` with pass/fail status and checksums.
- [X] T061 [P] **Resource Budget Simulation**: Execute a single-subject full pipeline on a local CPU environment to estimate peak RAM and runtime, ensuring it scales linearly to the full cohort within the specified time and memory constraints. **Output**: Save `data/logs/resource_budget_estimate.json` with peak RAM and runtime estimates.
- [X] T062 [P] **Final Report Schema Check**: Run `code/reports/generate_report.py` against a mock dataset to verify the JSON/CSV outputs match `contracts/output.schema.yaml` exactly, including the new tractography sensitivity fields.
- [X] T063 [P] **Constitution Principle Audit**: Generate a checklist report confirming compliance with all Constitution Principles (I-VII), specifically highlighting the "Associational Only" framing and "LOSO Independence" implementation. **Output**: Save `docs/constitution_audit.md`.
- [X] T064 [P] **Handoff Documentation**: Update `README.md` to explicitly state the "Tractography Noise Sensitivity" results as a key finding, and provide instructions for reproducing the full analysis including the reviewer-mandated sensitivity checks. **Specific Content**: Add a section header "## Reproducibility & Tractography Sensitivity" with the required instructions.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Revision (Phase 5)**: Depends on US1 and US2 completion (requires structural and dynamic metrics to perform correlation sensitivity).
- **Polish (Final Phase)**: Depends on all desired user stories and revisions being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data output
- **Revision (Phase 5)**: Depends on US1 (structural metrics) and US2 (correlation logic) being functional.
- **Polish (Final Phase)**: Depends on all desired user stories and revisions being complete

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
- Revision tasks (T040-T044) can run in parallel with US3 (T031-T035) as they both depend on US1/US2 completion.
- **Note**: T015b (Setup+Execute) is a single task. T031 (Full Cohort) is a single task. T041, T042a, T042b, T043, T044 must be sequential.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T050 [P] **Documentation Updates**: Update `README.md` with full pipeline description, installation instructions, and usage examples. Ensure `docs/quickstart.md` is comprehensive. **Constitution Principle I (Reproducibility)**: This task ensures the project is reproducible by external parties.
- [X] T051 Code cleanup and refactoring for CPU efficiency (ensure no GPU calls).
- [X] T052 Run `docs/quickstart.md` validation to ensure full pipeline reproducibility.
- [X] T053 **Final Review of Reports**: Perform a manual or automated review of all generated reports (T034) to ensure explicit "associational" language compliance (FR-007, SC-004) and absence of causal language. **Constitution Principle II (Verified Accuracy)**: This task ensures the final deliverable meets accuracy and framing requirements.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability to specific user story
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only (cores, ~7GB RAM). No GPU, no 8-bit quantization, no large LLMs.
- **Data Integrity**: No fake data. All metrics must come from real HCP data fetched via OpenNeuro/URL.
- **Scope Constraint**: Only implement features explicitly mandated by FR-001 through FR-008 AND the reviewer-mandated tractography sensitivity analysis (which has been determined to be **IN SCOPE** for this revision).
- **Methodological Note**: Tasks T016 and T017 implement the Plan-mandated "Leave-One-Subject-Out (LOSO)" K-Means strategy to ensure statistical independence. T013b explicitly verifies this constraint.
- **Revision Note**: Tractography Noise Sensitivity (T040-T044) has been **ADDED** to Phase 5 to address the `john-von-neumann-simulated` review concern regarding false-positive rates in diffusion MRI tractography (Yeh et al.,). This analysis is now mandatory and mapped to FR-008/SC-002. T043 is explicitly defined to generate the correlation sensitivity data required by T034.
- **Runtime Constraint**: T031 mandates full cohort processing via streaming; no subset or abort strategies are permitted.

---

## Phase 8: Final Validation & Handoff

**Purpose**: Ensure the project is ready for execution and validation against all constraints.

(Phase 8 has been merged into Phase 6. Tasks T060-T064 are located in Phase 6.)