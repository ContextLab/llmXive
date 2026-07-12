# Tasks: Predicting Molecular Complexity Using Information Theory

**Input**: Design documents from `/specs/001-predicting-molecular-complexity/`
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

- [ ] T001 Create project structure per implementation plan by executing: `mkdir -p code/ data/raw/ data/processed/ reports/figures/ tests/unit/ tests/contract/`
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt`: `rdkit>=2023.09.0,<2024.0.0`, `pandas>=2.1.0,<3.0.0`, `numpy>=1.24.3,<2.0.0`, `scipy>=1.11.1,<2.0.0`, `scikit-learn>=1.3.0,<2.0.0`, `matplotlib>=3.7.2,<4.0.0`, `seaborn>=0.12.2,<1.0.0`, `requests>=2.31.0,<3.0.0`, `datasets>=2.14.0,<3.0.0`, `pytest>=7.4.0,<8.0.0`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes critical constraints (memory, time) that must be enforced during execution.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` to define paths, random seeds, `SAMPLE_SIZE=5000`, chunk sizes (for memory safety), and timeout parameters
- [ ] T005 [P] Implement `code/download.py` to load the specific HuggingFace dataset `sagawa/pubchemm-canonicalized` (columns: `canonical_smiles`, `cid`), validate that raw SMILES strings are present for LZ compression, apply stratified random sampling of `SAMPLE_SIZE` molecules immediately during load to prevent full dataset memory overflow, compute checksum, and save to `data/raw/`
- [X] T006 [P] Implement `code/metrics.py` skeleton defining function signatures for `compute_shannon_entropy`, `compute_lz_complexity`, `compute_sa_qed`, and a `@timeout` decorator wrapper structure with a configurable limit.
- [X] T007 Create `code/main.py` orchestration script that chains: Download -> Sample -> Compute Metrics -> Analysis -> Viz
- [ ] T008 Setup logging infrastructure in `code/` to record skipped molecules (invalid/timeout) and data loading stats
- [~] T023 [P] Implement **chunked processing logic** in `code/metrics.py` to iterate over the dataset in batches (e.g., 500 molecules/batch) to ensure peak memory usage remains ≤ 4GB during metric computation (FR-008)
- [~] T024 [P] Implement a **global timeout wrapper** in `code/main.py` to enforce the 45-minute execution limit (SC-005)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Correlation Analysis (Priority: P1) 🎯 MVP

**Goal**: Download molecules, compute all four metrics (Entropy, LZ, SA, QED), and output a statistical report with Pearson correlations.

**Independent Test**: The system must successfully download a stratified sample, compute metrics, and output a JSON report with correlation coefficients and p-values.

### Implementation for User Story 1

- [~] T009 [US1] Implement `code/metrics.py` function `compute_shannon_entropy(mol)` using vertex degree distribution from RDKit adjacency matrices (define signature and logic)
- [~] T010 [US1] Implement `code/metrics.py` function `compute_lz_complexity(smiles)` using Lempel-Ziv compression on canonical SMILES strings (define signature and logic)
- [~] T011 [US1] Implement `code/metrics.py` function `compute_sa_qed(mol)` using RDKit's `CalcSyntheticAccessibilityScore` and `CalcQED` (define signature and logic)
- [~] T012 [US1] Implement `code/metrics.py` pipeline to iterate through the sampled dataset, applying a fixed timeout, skipping invalid entries, and saving results to `data/processed/metrics.csv` **including the 'smiles' column** alongside computed metrics (Entropy, LZ, SA, QED) to satisfy Constitution Principle VI
- [~] T013 [US1] Implement `code/analysis.py` function `calculate_pearson_correlations(df)` to compute r and p-values for (Entropy vs SA), (Entropy vs QED), (LZ vs SA), (LZ vs QED), reading input explicitly from `data/processed/metrics.csv`
- [~] T014 [US1] Implement `code/analysis.py` to generate `reports/stats.json` containing correlation coefficients, p-values, and explicit "associational" labeling

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Robustness & Sensitivity (Priority: P2)

**Goal**: Verify correlations are not artifacts via bootstrap resampling and multiple-comparison correction.

**Independent Test**: The system must perform a sufficient number of bootstrap iterations to generate confidence intervals and apply Bonferroni correction to p-values.

### Implementation for User Story 2

- [~] T017 [US2] Implement `code/analysis.py` schema generation logic for `reports/stats.json` to include fields for `ci_lower`, `ci_upper`, `std_dev`, and `adjusted_p_value` (must precede data generation)
- [~] T015 [US2] Implement `code/analysis.py` function `bootstrap_correlations(df, n_iterations=1000)` to resample data and calculate confidence intervals for all four metric pairs, **with a hard enforcement/assertion that [deferred] iterations are executed** as per FR-005
- [~] T016 [US2] Implement `code/analysis.py` function `apply_multiple_comparison_correction(p_values)` using Bonferroni or Holm-Bonferroni method
- [~] T018 [US2] Implement `code/analysis.py` to report bootstrap confidence intervals and flag if zero is included for significant findings (SC-003)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization & Reporting (Priority: P3)

**Goal**: Generate scatter plots with regression lines, CIs, and annotated stats for human interpretation.

**Independent Test**: The system must generate four distinct scatter plots with linear regression lines and annotated statistical metrics.

### Implementation for User Story 3

- [~] T019 [US3] Implement `code/viz.py` function `plot_correlation_scatter(df, metric_x, metric_y)` to generate scatter plots with linear regression lines
- [~] T020 [US3] Implement `code/viz.py` to add confidence intervals (shaded regions) and annotate plots with r, p-value, and n
- [~] T021 [US3] Implement `code/viz.py` to generate four specific plots: (Entropy-SA), (Entropy-QED), (LZ-SA), (LZ-QED) and save to `reports/figures/`
- [~] T022 [US3] Implement `code/main.py` final reporting step to compile `reports/stats.json` and `reports/figures/` into a single HTML report or PDF

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T029 [P] Implement **memory profiling hooks** in `code/main.py` to log peak memory usage during chunked processing (complements T023)
- [~] T030 [P] Implement a **performance profiling** step in `code/main.py` to verify and log that the full pipeline completes within 45 minutes (validates SC-005)
- [~] T025 [P] Add unit tests in `tests/unit/test_metrics.py` with specific functions `test_compute_shannon_entropy`, `test_compute_lz_complexity`, `test_compute_sa_qed`
- [~] T026 [P] Add contract tests in `tests/contract/test_output_schema.py` using `jsonschema` to verify `reports/stats.json` schema and file existence
- [~] T027 [P] Documentation updates: Add installation steps to `README.md`, update `quickstart.md` with usage examples and environment setup
- [ ] T028 Run `quickstart.md` validation to ensure reproducibility on CI

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires data from US1/US2

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
# Launch metric computation tasks together (they operate on different data chunks or are independent functions):
Task: "Implement compute_shannon_entropy in code/metrics.py"
Task: "Implement compute_lz_complexity in code/metrics.py"
Task: "Implement compute_sa_qed in code/metrics.py"
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
 - Developer A: User Story 1 (Data & Metrics)
 - Developer B: User Story 2 (Statistics)
 - Developer C: User Story 3 (Visualization)
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