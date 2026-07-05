# Tasks: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Input**: Design documents from `/specs/001-statistical-evaluation-of-dimensionality/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

## Phase 0: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: `mkdir -p projects/001-statistical-evaluation-of-dimensionality/{data/raw,data/processed,results,code,tests}`

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Create `environment.yml` with pinned Python dependencies (scanpy, umap-learn, leidenalg, statsmodels, snakemake, scikit-misc, requests, pandas, numpy) compatible with the selected major version.
- [X] T002b [P] Create `code/scripts/generate_requirements.py` to automatically convert `environment.yml` to `requirements.txt` to enforce 'Single Source of Truth' (DEPENDS: T002)
- [X] T004 [P] Implement `code/config.py` to load configuration, define paths (`data/raw`, `data/processed`, `results`), set global random seeds, and define dataset accessions (GSE, GSE111322, GSE150728)
- [ ] T003 [P] Configure `Snakefile` workflow skeleton and `code/__init__.py` (DEPENDS: T004 to ensure valid paths; Define skeleton rules: download, preprocess, geometry, embeddings, cluster, fidelity, stats)
- [ ] T005 [P] Implement `code/download.py` with fetching logic using `requests` for verified GEO raw count URLs (no R/GEOquery) and checksum validation
- [ ] T006 [P] Implement `code/preprocess.py` for QC (filter genes <5% cells), HVG selection (top variable genes), and deterministic cell sampling (hash-based `random_state`) ONLY IF cell count > 10,000
- [~] T020 [P] Implement `/usr/bin/time -v` wrapper in `code/utils.py` to log wall-clock time and peak RAM
- [~] T008a [P] Implement `code/embeddings.py` to generate PCA with a configurable number of principal components and built-in resource abort logic using T020 wrapper (DEPENDS: T020)
- [~] T008b [P] Extend `code/embeddings.py` to generate t-SNE (perplexity=30, n_iter=1000, CPU-only) and UMAP (n_neighbors=15, min_dist=0.1) with built-in resource abort logic (DEPENDS: T008a)
- [~] T009a [P] Implement `code/clustering.py` with Leiden clustering engine (generic resolution input) and fidelity metrics (ARI, NMI) calculation (DEPENDS: T006)
- [~] T010 [P] Implement `code/stats.py` for Mixed-Effects Model fitting (dataset as random intercept) and fallback to Fixed-Effects ANOVA (DEPENDS: T023.5)
- [~] T011 Implement `code/main.py` as the Snakemake wrapper entry point to orchestrate the full pipeline
- [~] T029 [P] Implement resource abort logic wrapper in `code/utils.py` to check RAM usage during execution and abort if > 7GB, logging metrics per step to `results/monitoring.csv` (FR-010)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Data-Gap Resolution (Critical Blocker)

**Purpose**: Verify availability of raw count matrices for required datasets (GSE131907, GSE111322, GSE150728) and implement fallback logic.

**⚠️ CRITICAL**: No user story work can begin until this phase completes. If NO datasets are found, pipeline aborts. If SOME are found, pipeline proceeds in "Case Study" mode.

- [~] T050 [US1] Implement Phase 0 verification in `code/download.py`: Attempt to fetch raw counts for GSE131907, GSE111322, GSE150728. If ALL are missing, log "No Data" and exit code 1. If SOME are missing, log warnings, set `CASE_STUDY_MODE=True` in `code/config.py`, and continue with available datasets. (DEPENDS: T005)
- [~] T051 [US1] Implement `code/main.py` logic to detect `CASE_STUDY_MODE`. If True, switch statistical model to "Single Dataset Mode" (Fixed-Effects ANOVA) and update `results/summary.json` header to "Descriptive Case Study".
- [~] T052 [US1] Create `code/validators.py` to enforce the "Real Data Only" constraint: reject any task that attempts to generate synthetic counts or use placeholder data; raise an error if `data/raw` contains simulated values.
- [~] T053 [US1] Update `code/config.py` to include a dynamic list of "Verified Sources" and a "Fallback Sources" list; prioritize verified GEO URLs but allow fallback to `ucimlrepo` if the primary list fails.
- [~] T054 [US1] Add a `Snakefile` rule `verify_data_availability` that runs before `download` and halts the workflow if no valid raw count source is found for the required accessions.

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download three specific public scRNA-seq datasets, apply QC, and retain top HVGs.

**Independent Test**: The pipeline can be tested by running the Snakemake workflow on a single dataset and verifying that the output matrix contains a substantial number of genes and that the row/column counts match the expected post-filtering dimensions.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create `Snakefile` rule `download` to fetch raw count matrices for GSE131907, GSE111322, GSE150728 using `code/download.py`
- [ ] T013 [P] [US1] Create `Snakefile` rule `preprocess` to apply QC (<5% gene filter) and HVG selection (top-ranked) via `code/preprocess.py`
- [ ] T014 [US1] Implement deterministic sampling logic in `code/preprocess.py` (sample down to a reduced subset of cells if needed) using `random_state=hash(accession)`
- [ ] T014b [US1] Configure sampling threshold (10,000 cells) in `code/config.py`
- [ ] T015 [US1] Add error handling in `code/download.py` to **abort fidelity calculation** for datasets with missing ground-truth labels and **write a specific error record** to `results/fidelity_errors.json` (DO NOT skip; Spec Edge Cases require distinct failure state).
- [ ] T015b [US1] Implement global fallback check in `code/main.py` to switch to 'Descriptive Mode' if <2 valid datasets remain after download/preprocess (aligns with T050 logic)
- [ ] T016 [US1] Add validation in `code/preprocess.py` to flag datasets with insufficient genes after filtering and skip them

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Geometric Diagnostics and Embedding Generation (Priority: P2)

**Goal**: Compute global linearity and local density metrics, and generate PCA, t-SNE, and UMAP embeddings.

**Independent Test**: The system can be tested by running the diagnostics on a synthetic dataset with known geometry and verifying that the linearity score is high for a linear manifold and low for a curved one.

### Implementation for User Story 2

- [ ] T017 [P] [US2] Create `Snakefile` rule `embeddings` to generate PCA, t-SNE, and UMAP embeddings using `code/embeddings.py` (DEPENDS: T008a, T008b)
- [ ] T018 [P] [US2] Create `Snakefile` rule `geometry` to compute Global Linearity (Trustworthiness) and Local Continuity (LCA) on the **RAW high-dimensional space (pre-log-CPM)** using `code/geometry.py` (DEPENDS: T007, T006)
- [ ] T019 [US2] Ensure `code/embeddings.py` uses `n_jobs=1` and CPU-only parameters to prevent CUDA/GPU errors
- [ ] T021 [US2] Implement parser in `code/utils.py` to read `/usr/bin/time` logs and record metrics into `results/monitoring.csv` per embedding step
- [ ] T007 [P] [US2] Implement `code/geometry.py` to compute Global Linearity (Trustworthiness metric, k=15) and Local Continuity (LCA metric, k=15) on the **RAW high-dimensional space (pre-log-CPM)**. **Must perform deterministic sampling with seed=hash(accession) if n_cells > 10,000** (DEPENDS: T006; **NOTE**: Computed on RAW space, NOT preprocessed or PC space)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fidelity Assessment and Statistical Modeling (Priority: P3)

**Goal**: Cluster embeddings, calculate ARI/NMI, and fit the mixed-effects model to test interaction effects.

**Independent Test**: The system can be tested by running the full statistical model on a small subset of data and verifying that the linear model converges and outputs valid p-values.

### Implementation for User Story 3

- [ ] T009b [P] [US2] Implement `code/clustering.py` function `optimize_resolution()` that sweeps resolutions (0.1->1.0), computes Silhouette Score, and **saves the optimal resolution to `results/optimal_resolution.json`**. (DEPENDS: T009a)
- [ ] T022 [P] [US3] Create `Snakefile` rule `cluster` to apply Leiden clustering using the **optimal resolution from `results/optimal_resolution.json`** via `code/clustering.py` (DEPENDS: T009b)
- [ ] T023 [P] [US3] Create `Snakefile` rule `fidelity` to calculate ARI and NMI against ground-truth labels using `code/clustering.py`
- [ ] T023.5 [US3] Implement aggregation script in `code/aggregate.py` to join geometry metrics (from T018) and fidelity metrics (from T023) by cell/dataset ID into a single dataset for modeling
- [ ] T045 [US3] Implement `code/stats.py` function `run_sensitivity_sweep()` that iterates over **Silhouette thresholds across a representative range**, re-optimizes Leiden resolution for each, and records the variance in ARI/NMI. (Matches Spec FR-007/SC-001)
- [ ] T046 [US3] Update `code/aggregate.py` to include the sensitivity sweep results in the final report, calculating the variance metric and comparing it against the SC-001 threshold (variance < 0.05).
- [ ] T047 [US3] Implement Benjamini-Hochberg correction in `code/stats.py` for all p-values generated during the sensitivity sweep and the primary Mixed-Effects test, ensuring FDR < 0.05 is reported.
- [ ] T048 [US3] Add VIF (Variance Inflation Factor) calculation in `code/stats.py` to check for collinearity (SC-005); abort if VIF >= 5 and log the specific predictors causing the issue.
- [ ] T024 [US3] Implement Mixed-Effects Model fitting in `code/stats.py` with formula `fidelity ~ method + (1|dataset)` to test the fixed effect of the dimensionality reduction method on fidelity, with dataset as a random intercept. Include fallback to Fixed-Effects ANOVA if N=1 dataset (DEPENDS: T023.5, T045) (**NOTE**: Matches Spec FR-006; If N<3, explicitly raise 'blocked' state or 'spec violation' rather than silent downgrade)
- [ ] T025 [US3] Implement fallback logic in `code/stats.py` to switch to Descriptive Stratified Analysis if <2 verified datasets are available (or if Mixed-Effects model fails due to convergence)
- [ ] T026 [US3] Implement ANOVA F-tests in `code/stats.py` to evaluate interaction terms with α=0.05
- [ ] T027 [US3] Add error handling in `code/stats.py` to catch convergence errors, attempt simplified models, and record failures in the report

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - CI Resource Constraint Compliance (Priority: P4)

**Goal**: Ensure the analysis pipeline completes within GitHub Actions free-tier limits (h, GB RAM).

**Independent Test**: The pipeline can be tested by running the full workflow on a GitHub Actions free-tier runner and verifying runtime and RAM usage.

### Implementation for User Story 4

- [ ] T028 [P] [US4] Create `Snakefile` rule `resource_monitor` to aggregate `/usr/bin/time -v` logs for all embedding steps (DEPENDS: T021)
- [ ] T030 [US4] Create GitHub Actions workflow file `.github/workflows/research.yml` to run `snakemake --cores <parallelism>` on `ubuntu-latest`
- [ ] T031 [US4] Add CI step to verify `environment.yml` installation completes within 30 minutes
- [ ] T032 [US4] Add CI step to verify total pipeline runtime < 6 hours and peak RAM < 7GB

**Checkpoint**: User Story 4 ensures the research workflow is sustainable and reproducible within standard open-source constraints

---

## Phase 7: Revision - Statistical Model Consistency & Sensitivity (Priority: P3)

**Goal**: Resolve the contradiction between Plan (LMM) and Spec (Mixed-Effects) and implement the required sensitivity analysis for Silhouette thresholds.

**Independent Test**: The statistical report must clearly state the model used (Mixed-Effects or Single Dataset) and include a sensitivity plot showing ARI/NMI variance across Silhouette thresholds.

### Implementation for User Story 8 (Statistical Consistency)

- [ ] T044 [US3] Refactor `code/stats.py` to ensure Mixed-Effects Model is the primary implementation (Spec FR-006) and robustly handles the fallback to Fixed-Effects ANOVA if N=1. Verify Benjamini-Hochberg correction is applied to all p-values. (DEPENDS: T024)
- [ ] T049 [US3] Update `plan.md` to reflect the adoption of the Mixed-Effects Model (Spec FR-006) and the Silhouette Threshold sweep (Spec FR-007), resolving the "Plan Inconsistency" noted in T007 and T024.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates: Update `README.md` with Installation and Usage sections; add `docs/quickstart.md` with step-by-step guide
- [ ] T034 Code cleanup and refactoring in `code/`: Extract validation logic into `code/validators.py`; reduce cyclomatic complexity of `code/preprocess.py` to < 10
- [ ] T035 [P] Performance optimization for t-SNE/UMAP: Implement batching logic to target < 30 min runtime per embedding step or **implement batching logic to reduce peak RSS by [deferred] if >7GB**
- [ ] T036 [P] Additional unit tests in `tests/`: Add `tests/test_geometry.py::test_linearity_on_synthetic_linear_data`, `tests/test_preprocess.py::test_hvg_selection`, `tests/test_stats.py::test_mixed_effects_model`
- [ ] T037 [P] Validate quickstart.md: Execute `snakemake --cores 2 --dry-run` from the project root, verify the exit code is **0**, and confirm `docs/quickstart.md` exists and is non-empty
- [ ] T038 [P] Generate final `research.md` and `data-model.md` artifacts: Use `results/` data and `research_template.md` to populate content

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Setup)**: No dependencies - must run FIRST.
- **Phase 1 (Foundational)**: No dependencies - can start immediately.
- **Phase 2.5 (Data-Gap)**: Depends on Phase 1 (T005) - BLOCKS all user stories.
- **Phase 3-6 (User Stories)**: All depend on Foundational phase completion.
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 1) - Depends on US1 data output.
- **User Story 3 (P3)**: Can start after Foundational (Phase 1) - Depends on US2 embedding output; requires T009b (Optimizer) before T022; requires T045 (Sensitivity) before T024.
- **User Story 4 (P4)**: Can start after Foundational (Phase 1) - Integrates with all stories for monitoring.

### Within Each User Story

- Models/Scripts before services/workflow rules
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (except T003 which depends on T004)
- All Foundational tasks marked [P] can run in parallel (within Phase 1, respecting T007->T008a order)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2.5: Data-Gap Resolution
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
- **SPEC OVERRIDES PLAN**: Tasks follow Spec FR-002/003 (Trustworthiness/LCA on RAW space) and FR-006 (Mixed-Effects Model) over Plan's conflicting descriptions. Plan requires formal update (kickback) to align with Spec.
- **DATA GAP LOGIC**: Pipeline aborts only if ZERO datasets are found. If >=1 dataset is found, it proceeds in "Case Study" mode.
- **SENSITIVITY SWEEP**: Explicitly uses {0.4, 0.5, 0.6} as per SC-001.