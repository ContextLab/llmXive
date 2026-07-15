# Tasks: Investigating Microbial Community Succession in Constructed Wetlands

**Input**: Design documents from `/specs/001-microbial-succession/`
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

- [ ] T001a [P] Create project directory structure per implementation plan (`projects/PROJ-280-investigating-microbial-community-succes/`) including specific subdirectories: `data/raw`, `data/processed`, `data/config`, `code`, `tests/unit`, `tests/contract`, `tests/integration`, `state/projects`, and `contracts`.
- [ ] T001b [P] Create `MANIFEST.txt` in `projects/PROJ-280-investigating-microbial-community-succes/` listing all expected files and directories created by T001a to verify structure completeness.
- [X] T002 [P] Initialize Python 3.11 project with pinned dependencies. Create `projects/PROJ-280-investigating-microbial-community-succes/code/requirements.txt` by using `pip-tools` (specifically `pip-compile` with a constraints file) to resolve compatible versions for `pandas`, `numpy`, `scipy`, `scikit-bio`, `networkx`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, and `pyyaml`. Alternatively, manually specify known compatible versions (e.g., `scikit-bio==0.5.8`, `pandas==2.0.3`) ensuring the file contains exact version pins (e.g., `package==version`). Do not use `pip freeze` on an existing environment; the file must be generated from scratch using `pip-compile` or manual entry of verified compatible versions.
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `projects/PROJ-280-investigating-microbial-community-succes/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `data/config/dataset_ids.json` schema validator and sample config file per `contracts/dataset-config.schema.yaml`.
- [ ] T005 [P] Implement `code/utils.py` with shared helpers: VIF calculation, Benjamini-Hochberg FDR correction, checksum generation, and power analysis stub.
- [X] T006 [P] Setup logging infrastructure in `code/utils.py` to handle "CRITICAL DATA GAP", "UNDERPOWERED", and "UNDER-DETERMINED" flags.
- [ ] T007 [P] Create base data models for `Sample` and `Taxon` in `code/data_models.py` (matching `contracts/feature-table.schema.yaml`). <!-- FAILED: unspecified -->
- [ ] T008 [P] Implement state tracking mechanism in `state/projects/PROJ-280-investigating-microbial-community-succes.yaml` to track artifact hashes.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Preprocess Public 16S Datasets (Priority: P1) 🎯 MVP

**Goal**: Retrieve pre-processed 16S rRNA feature tables and metadata from public repositories, filter for constructed wetlands with nutrient removal metrics, and subsample to uniform depth.

**Independent Test**: Execute `code/01_retrieve_data.py` and `code/02_preprocess.py` against a known public dataset ID; verify output files exist in `data/processed/` with ≥90% expected samples retained and uniform read depth.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_config.py`.
- [X] T010 [P] [US1] Integration test for data retrieval and filtering logic in `tests/integration/test_data_retrieval.py`.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/01_retrieve_data.py` to load `data/config/dataset_ids.json`, validate against verified sources (NCBI SRA/Zenodo), and download pre-processed 16S tables/metadata to `data/raw/`. Include "Data Gap" protocol to halt if no verified dataset found.
- [X] T012 [US1] Implement `code/02_preprocess.py` to filter `data/raw/` samples for constructed wetlands with N/P removal metrics, logging excluded sample counts.
- [X] T013 [US1] Implement subsampling logic in `code/02_preprocess.py` to exclude samples with <1,000 reads (conservative minimum) and log the count. This threshold ensures sufficient data remains for the sensitivity analysis in T014. Do not apply the final "medium" depth threshold here; only apply the hard minimum exclusion.
- [~] T014 [US1] Implement FR-015 Sensitivity Analysis in `code/02_preprocess.py`: perform subsampling depth sweep (low, medium, high) by re-subsampling from the filtered data produced in T013. Generate intermediate artifacts (`data/processed/low_depth_results.json`, `data/processed/medium_depth_results.json`, `data/processed/high_depth_results.json`) containing the subsampled feature tables. Aggregate results into `data/processed/sensitivity_sweep_results.json`. This final artifact MUST be a 'robustness verification report' containing a `spearman_rank_correlation` metric (float) comparing alpha diversity rankings across depths. The report must explicitly state if the correlation is > 0.9 (pass) or ≤ 0.9 (fail).
- [X] T015a [US1] Add validation and error handling for missing metadata fields (N/P rates) in `code/02_preprocess.py`.
- [ ] T015b [US1] Log the specific exclusion count of samples lacking N/P metadata to `data/processed/exclusion_log.json` as required by Edge Cases to ensure transparency.
- [ ] T016 [US1] Implement checksum recording for `data/processed/` files (including `low_depth_results.json`, `medium_depth_results.json`, `high_depth_results.json`, `sensitivity_sweep_results.json`, and `exclusion_log.json`) in `state/projects/PROJ-280-investigating-microbial-community-succes.yaml`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Calculate Diversity Metrics and Test Community Differences (Priority: P2)

**Goal**: Calculate alpha/beta diversity, perform power analysis, and run PERMANOVA with FDR correction to test for community differences between wetland stages.

**Independent Test**: Run `code/03_diversity.py` on a subset of samples; verify Shannon/Simpson indices are computed (no NaN), PERMANOVA p-values and effect sizes (R²) are generated, and FDR correction is applied.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for diversity output schema in `tests/contract/test_diversity_output.py`.
- [ ] T018 [P] [US2] Integration test for PERMANOVA power analysis gate in `tests/integration/test_permanova_gate.py`.

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/03_diversity.py` to calculate Alpha (Shannon, Simpson) and Beta (Bray-Curtis) diversity for all samples in `data/processed/`.
- [ ] T020 [US2] Implement FR-014 Power Analysis in `code/03_diversity.py`: estimate power for PERMANOVA (effect size R²=0.15) using `statsmodels.stats.power.FTestAnovaPower`. Write `data/processed/power_analysis_report.json` with schema `{power: float, n_per_group: int, effect_size: float, flag: "UNDERPOWERED"|"PASS"}`. Additionally, generate `data/processed/sample_size_validation.json` that explicitly compares the final retained sample count against the power analysis target (n_per_group) to satisfy SC-001. Log "UNDERPOWERED" and halt only after these files are written.
- [ ] T021 [US2] Implement PERMANOVA test in `code/03_diversity.py` to compare community composition between wetland establishment stages (early vs. mature).
- [ ] T022 [US2] Implement Benjamini-Hochberg FDR correction for pairwise PERMANOVA comparisons in `code/03_diversity.py` (FR-009).
- [ ] T023 [US2] Add logic to document small effect sizes (R² < 0.1) as statistically significant but ecologically weak in output reports.
- [ ] T024 [US2] Generate diversity metrics report to `data/processed/diversity_metrics.json` conforming to `contracts/output-metrics.schema.yaml`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Construct Co-occurrence Networks and Correlate Taxa with Nutrient Removal (Priority: P3)

**Goal**: Construct Spearman-based co-occurrence networks, calculate modularity, perform sensitivity analysis, and correlate taxa abundances with nutrient removal rates.

**Independent Test**: Run `code/04_network.py` and `code/05_correlation.py`; verify network edges meet threshold (|ρ|≥0.6, p≤0.01), modularity delta is calculated (or under-determined flag raised), and taxa-nutrient correlations with VIF checks are reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Contract test for network output schema in `tests/contract/test_network_output.py`.
- [ ] T026 [P] [US3] Integration test for VIF and correlation logic in `tests/integration/test_correlation.py`.

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/04_network.py` to calculate Spearman correlation matrix from `data/processed/` taxon abundance data.
- [ ] T028 [US3] Implement FR-013 Under-determined Check in `code/04_network.py`: if n_samples < n_taxa, flag as 'under-determined' and skip modularity calculation.
- [ ] T029 [US3] Apply edge retention threshold (|ρ|≥0.6, p≤0.01) and construct network graph using `networkx`.
- [ ] T030 [US3] Implement FR-013 Sensitivity Analysis in `code/04_network.py`: sweep correlation thresholds to assess modularity stability. Calculate and report the specific 'stability of modularity changes' metric, defined as the **variance of modularity scores across the swept thresholds**, in `data/processed/network_sensitivity_report.json`.
- [ ] T031 [US3] Calculate network modularity and signed delta (Δmodularity) between early vs. mature stages.
- [ ] T032 [US3] [Depends on: T011, T012, T013] Implement `code/05_correlation.py` to calculate Spearman correlation between taxon abundances and N/P removal rates using the filtered feature table from T013 and Stage metadata from T012. (Note: Does NOT depend on T019 diversity metrics).
- [ ] T033 [US3] [Depends on: T032] Implement VIF calculation in `code/05_correlation.py` to flag predictor taxa with VIF > 5 for collinearity (FR-010) using Stage metadata from T012.
- [ ] T034 [US3] [Depends on: T032] Implement k=3 cross-validation on the taxa-nutrient correlation model as required by FR-012. Output cross-validation metrics (mean R², std dev) to `data/processed/correlation_cv_results.json`. Generate final correlation report listing taxa with |r|≥0.5 and p≤0.05, or explicitly state if none met criteria. Output to `data/processed/correlation_results.json`. (Note: This task satisfies FR-012; ignore the contradictory note in plan.md Phase 4).
- [ ] T035 [US3] Generate network and correlation outputs to `data/processed/network_analysis.json` and `data/processed/correlation_results.json` conforming to `contracts/output-metrics.schema.yaml`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` (README, quickstart.md).
- [ ] T038 [P] Code cleanup and refactoring across `code/` scripts.
- [ ] T039 [P] Performance optimization to ensure pipeline completes within 6 hours on 2 CPU cores.
- [ ] T040 [P] Additional unit tests for edge cases (e.g., empty datasets, missing metadata) in `tests/unit/`.
- [ ] T041 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility.

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output; network construction (US3) requires sufficient sample size from US1

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
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_config.py"
Task: "Integration test for data retrieval and filtering logic in tests/integration/test_data_retrieval.py"

# Launch all implementation tasks for User Story 1 together (where dependencies allow):
Task: "Implement code/01_retrieve_data.py..."
Task: "Implement code/02_preprocess.py..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Data retrieval and filtering)
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
 - Developer A: User Story 1 (Data Retrieval)
 - Developer B: User Story 2 (Diversity Analysis)
 - Developer C: User Story 3 (Network & Correlation)
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