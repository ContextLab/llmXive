# Tasks: The Impact of Network Centrality on Neural Synchrony in Resting-State fMRI

**Input**: Design documents from `/specs/001-impact-of-network-centrality-on-neural-synchrony/`
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

- [ ] T001a [P] Create project directory structure: `projects/PROJ-268-the-impact-of-network-centrality-on-neur/`, `projects/PROJ-268-the-impact-of-network-centrality-on-neur/code/`, `projects/PROJ-268-the-impact-of-network-centrality-on-neur/data/`, `projects/PROJ-268-the-impact-of-network-centrality-on-neur/tests/`, `projects/PROJ-268-the-impact-of-network-centrality-on-neur/state/`. **Verify directories exist using `os.path.isdir` or `ls` command.**
- [X] T001b [P] Create `projects/PROJ-268-the-impact-of-network-centrality-on-neur/code/__init__.py` and `projects/PROJ-268-the-impact-of-network-centrality-on-neur/data/.gitkeep`
- [ ] T001c [P] Initialize Python 3.11 project with `projects/PROJ-268-the-impact-of-network-centrality-on-neur/code/requirements.txt` (nibabel, numpy, scipy, pandas, networkx, scikit-learn, matplotlib, seaborn, datasets, nilearn, brainsmash, tqdm). **Run `pip install -r requirements.txt` and verify no errors.**
- [ ] T001d [P] Configure linting (ruff/flake8) and formatting (black) tools in `projects/PROJ-268-the-impact-of-network-centrality-on-neur/code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `state/projects/PROJ-268-the-impact-of-network-centrality-on-neur.yaml` for checksums and timestamps
- [X] T005 [P] Implement `projects/PROJ-268-the-impact-of-network-centrality-on-neur/code/utils.py` with disk usage monitoring (halt if > 12 GB) and SHA256 checksum helpers
- [ ] T006 [P] Setup logging infrastructure writing to `projects/PROJ-268-the-impact-of-network-centrality-on-neur/data/results/processing.log`
- [ ] T007 [P] Create base schema definitions in `specs/001-impact-of-network-centrality-on-neural-synchrony/contracts/`. **Create `connectivity.schema.yaml` with fields `subject_id`, `matrix_type`, `dimensions`. Create `analysis-results.schema.yaml` with fields `rho`, `p_value`, `effect_size`, `stability_index`, `auc`.**
- [ ] T008 [P] Configure error handling to raise fatal errors on "Data Gap" or "Storage Limit Exceeded"

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download OpenNeuro matrix subset (a limited number of subjects) from the verified Parquet shard, **OR** process raw fMRI/dMRI data to generate connectivity matrices as required by FR-001/FR-002. **Primary path is raw processing; pre-computed is a fallback.**

**Independent Test**: The pipeline can be fully tested by verifying that for a **single subject**, the script outputs a valid 400x400 structural adjacency matrix and a functional correlation matrix in `data/processed`, with no missing values.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for disk usage monitor in `tests/test_utils.py` (**function: `test_disk_usage_halt`**)
- [X] T010 [P] [US1] Unit test for SHA256 checksum verification in `tests/test_utils.py` (**function: `test_sha256_match`**)
- [X] T011 [P] [US1] Integration test for data download failure handling in `tests/test_download_data.py` (**function: `test_download_failure`**)

### Implementation for User Story 1

- [X] T012 [US1] **Check Data Source**: Implement `code/download_data.py` to **fetch pre-computed SC/FC matrices from `huggingface_hub.load_dataset("openneuro-pub/ds000224-parquet")`**. **Explicitly check for columns `structural_matrix` and `functional_matrix`.** If raw NIfTI files are present (or if pre-computed columns are missing), **branch to T012b (Raw Processing)**. If pre-computed matrices are present, **proceed to T015**. If neither, **halt immediately with "Data Gap" error**.
- [ ] T012b [US1] **Depends on T012 (Raw Data Detected)**. **Implement raw fMRI/dMRI preprocessing pipeline** (MRtrix3/nilearn) to **generate** connectivity matrices. **This task runs ONLY if raw NIfTI files are detected in T012.** **Parcellate using Schaefer atlas and generate 400x400 matrices.**
- [X] T015 [US1] **Depends on T012 & T012b**. Implement matrix loading and validation in `code/utils.py` to ensure SC and FC matrices are 400x400 and aligned. **If raw data was processed (T012b), load generated matrices. If pre-computed, load from Parquet.** **Do not generate matrices; load them from the downloaded or generated files.**
- [X] T013 [US1] **Depends on T015**. Implement logic in `code/download_data.py` to skip corrupted subjects and log warnings; **proceed** with remaining downloads. **Only halt with a fatal error if the final count of valid subjects is < 10**.
- [X] T014 [US1] Implement checksum recording in `state/projects/PROJ-268-the-impact-of-network-centrality-on-neur.yaml` immediately after download
- [X] T016 [US1] Implement storage cleanup logic in `code/download_data.py` to remove raw files after processing to stay within 14 GB limit
- [ ] T017 [US1] Write `data/results/processing_summary.json` with `target`, `processed`, `skipped`, `proportion` fields

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Centrality and Synchrony Metric Computation (Priority: P2)

**Goal**: Compute node-level centrality metrics (degree, betweenness, eigenvector) from the **loaded** structural matrices and mean functional synchrony from the **loaded** functional matrices.

**Independent Test**: The computation can be fully tested by running the metric calculator on a small synthetic graph and verifying that the output matches known mathematical properties (e.g., a node with no edges has degree centrality of 0).

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for metric output schema in `tests/contract/test_metrics.py` (**function: `test_metric_schema`**)
- [X] T019 [P] [US2] Unit test for centrality calculation on synthetic graph in `tests/test_metrics.py` (**function: `test_centrality_zero_edges`**)

### Implementation for User Story 2

- [X] T020 [US2] **Depends on T015**. Create `code/compute_metrics.py` with functions for degree, betweenness, and eigenvector centrality using `networkx`. **Input: Loaded structural matrices. Do not generate matrices.**
- [X] T021 [US2] **Depends on T015**. Implement functional synchrony calculation (mean absolute correlation) in `code/compute_metrics.py`. **Input: Loaded functional matrices. Do not generate matrices.**
- [X] T022 [US2] **Depends on T020 & T021**. Implement loop in `code/compute_metrics.py` to process all subjects, aggregating node-level metrics per subject.
- [ ] T023 [US2] **Depends on T022**. Output per-subject CSV files to `data/processed/centrality_<subject_id>.csv` and `data/processed/synchrony_<subject_id>.csv`
- [ ] T024 [US2] Implement validation to ensure SC and FC matrices have matching dimensions before metric calculation; halt with error if mismatch

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**Goal**: Perform Spearman correlation, implement a **Spatial Null Model (BrainSMASH)** or handle discrete null distribution for subject-level permutation, perform sensitivity analysis, and generate visualization with explicit "associational" framing.

**Independent Test**: The analysis can be fully tested by running the script on a shuffled dataset and verifying that the p-value > 0.05 and the plot shows no significant trend.

### Tests for User Story 3

- [ ] T025 [P] [US3] Contract test for analysis JSON output in `tests/contract/test_analysis.py` (**function: `test_analysis_schema`**)
- [ ] T026 [P] [US3] Unit test for permutation test logic (shuffling subject IDs) in `tests/test_analysis.py` (**function: `test_analysis_shuffled_data`**)

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/analyze.py` to perform Spearman correlation between structural centrality and functional synchrony **across subjects (N=10), aggregating node-level metrics per subject as defined in Plan**. **Note: This is the subject-level aggregation required by the Plan, reconciling Spec FR-004's 'across all nodes' language with the N=10 unit of analysis.**
- [ ] T027b [US3] **Depends on T027**. Implement text generation logic to inject "preliminary and associational" framing into the analysis results and plot annotations, strictly adhering to FR-004.
- [ ] T028 [US3] **Depends on T027**. Implement **Spatial Null Model (BrainSMASH)** as the primary method for permutation testing. If BrainSMASH is unavailable, implement **Subject-level permutation (N=10) with n=1000 resamples**. **Explicitly handle the coarse resolution of the discrete null distribution: report the exact p-value and a warning about the discrete nature of N=10.**
- [ ] T028b [US3] **Depends on T028**. **Implement explicit warning logic** for the coarse null distribution (N=10) and ensure the output JSON includes a `null_distribution_warning` field explaining the p-value resolution limitation.
- [ ] T029 [US3] **Depends on T027**. Implement sensitivity analysis in `code/analyze.py` sweeping structural graph threshold density from **0.1 to 0.5 in steps of 0.05** using **proportional thresholding**. Calculate **Stability Index (std dev of rho values)** and **Area Under the Curve (AUC) (trapezoidal rule on rho vs density)**. **Explicitly write `stability_index` and `auc` to `analysis_results.json`.**
- [ ] T029b [US3] **Depends on T029**. **Document the threshold range (0.1 to 0.5) in code comments** as a sensitivity sweep per community standards, linking it back to FR-007.
- [ ] T030 [US3] **Depends on T027**. Implement VIF calculation for collinearity diagnostics among centrality metrics. **Input matrix structure: columns = [degree, betweenness, eigenvector]**. Define **VIF > 5** as high collinearity. Output VIF values as a JSON object in `analysis_results.json`.
- [ ] T031 [US3] **Depends on T027, T028, T029, T030, T027b**. Write `data/results/analysis_results.json` containing: rho, p-value (uncorrected and corrected), effect size, CI, **stability_index**, **auc**, collinearity diagnostics (VIF), **null_distribution_warning**, and the **"preliminary and associational" framing text**.
- [ ] T032 [US3] **Depends on T031, T027b**. Implement `code/visualize.py` to generate scatter plot with regression line, confidence interval, p-value annotation, and **"preliminary and associational" text**.
- [ ] T033 [US3] **Depends on T032**. Output high-resolution PNG plot to `data/results/centrality_synchrony_plot.png`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `docs/` (README, quickstart.md)
- [ ] T035a [P] Refactor imports in `code/download_data.py`: Remove unused imports.
- [ ] T035b [P] Refactor imports in `code/utils.py`: Remove unused imports.
- [ ] T035c [P] Standardize error messages across `code/` (e.g., "Data Gap", "Storage Limit Exceeded").
- [ ] T036a [P] Run `cProfile` on `code/download_data.py` and identify bottlenecks.
- [ ] T036b [P] Optimize chunking logic in `code/download_data.py` for memory efficiency.
- [ ] T036c [P] Verify full pipeline runtime < 6 hours on CI.
- [ ] T037 [P] Run full pipeline integration test on CI
- [ ] T038 [P] Security hardening (input validation)
- [ ] T039 [P] Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational.
 - **User Story 2 (P2)**: **Depends on US1 completion** (needs data output).
 - **User Story 3 (P3)**: **Depends on US2 completion** (needs metrics output).
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **Once Foundational phase completes**:
 - **User Story 1** must be completed first.
 - **User Story 2** and **User Story 3** setup (e.g., writing test files, scaffolding) can be done in parallel with US1 implementation, but their **execution** is strictly sequential (US1 -> US2 -> US3) due to data dependencies.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **only for setup/scaffolding**; data flow is sequential.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for disk usage monitor in tests/test_utils.py (test_disk_usage_halt)"
Task: "Unit test for SHA256 checksum verification in tests/test_utils.py (test_sha256_match)"
Task: "Integration test for data download failure handling in tests/test_download_data.py (test_download_failure)"

# Launch implementation tasks (sequential due to data flow):
Task: "Implement code/download_data.py..."
Task: "Implement checksum recording..."
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
 - Developer A: User Story 1 (Implementation)
 - Developer B: User Story 2 (Setup/Tests)
 - Developer C: User Story 3 (Setup/Tests)
3. Once US1 is done:
 - Developer A: Moves to US2 implementation
 - Developer B: Moves to US3 implementation
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Hygiene**: Never fall back to synthetic data; if real data fetch fails, the pipeline MUST halt.
- **Storage**: Monitor disk usage strictly; halt if > 12 GB to prevent runner failure.
- **Statistical Power**: Acknowledge N=10 limitation; frame results as preliminary and associational.
- **Pre-computed Mode**: Explicitly skip tractography ONLY if raw data is unavailable; otherwise, implement raw processing (T012b) to satisfy FR-001/FR-002.
- **Spatial Null**: Prioritize BrainSMASH for permutation testing; handle coarse null for N=10.