# Tasks: The Role of Epigenetic Drift in Adaptive Landscape Exploration

**Input**: Design documents from `/specs/001-role-of-epigenetic-drift/`
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

- [ ] T001a Create `data/` and `data/raw/` directories
- [ ] T001b Create `code/`, `code/discovery/`, `code/preprocess/`, `code/analysis/`, `code/viz/` directories
- [ ] T001c Create `output/`, `output/figures/`, `tests/`, `tests/unit/`, `tests/contract/`, `logs/`, and `data/processed/` directories
- [ ] T002 Initialize Python 3.11 project with dependencies: `pandas`, `numpy`, `scipy`, `scikit-learn`, `requests`, `pyyaml`, `tqdm`, `pytest`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` for path management, random seeds, and environment variables
- [ ] T005 [P] Create `code/__init__.py` and module `__init__.py` files for package structure
- [ ] T006 Implement `code/discovery/__init__.py` and `code/preprocess/__init__.py`
- [ ] T007 Implement `code/analysis/__init__.py` and `code/viz/__init__.py`
- [ ] T008 Create `tests/unit/__init__.py` and `tests/contract/__init__.py`
- [ ] T008b Create `data/verified_datasets.yaml` as the local registry for verified accession titles (required by T010)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 0 - Data Discovery and Availability Check (Priority: P0) 🎯 MVP

**Goal**: Validate the existence of ≥3 matched multi-generational datasets (methylation + RNA-seq) in GEO/ENCODE before proceeding.

**Independent Test**: The discovery script runs against a hardcoded list of search queries; output is a list of valid accession IDs or a "Data Unavailable" failure message.

### Implementation for User Story 0

- [ ] T009 [US0] Implement `code/discovery/query_geno.py` with search logic for "multi-generational", "methylation", "RNA-seq", and "fluctuating" keywords. **Output**: `output/discovery_results.json`.
- [ ] T010 [US0] Implement `validate_reference(accession, title)` in `code/discovery/query_geno.py` performing title-token overlap check (threshold ≥ 0.7) against `data/verified_datasets.yaml`.
- [ ] T011 [US0] Implement logic to filter datasets by organism (mouse, C. elegans, Drosophila) and metadata completeness (fluctuation timescale/amplitude).
- [ ] T012 [US0] Implement logic to flag "Partial Match" datasets and write a `halt_signal` to `output/discovery_status.json` if <3 valid datasets are found. **Checkpoint**: Pipeline halts if this file contains `halt_signal`.
- [ ] T013 [US0] Create `tests/unit/test_discovery.py` with mock responses for GEO/ENCODE queries.

**Checkpoint**: Data availability confirmed or pipeline halted appropriately via `output/discovery_status.json`.

---

## Phase 4: User Story 1 - Data Acquisition, Preprocessing, and Quality Filtering (Priority: P1)

**Goal**: Download, filter, and normalize multi-generational omics datasets using LOGO jackknife to create a unified analysis-ready matrix.

**Independent Test**: Pipeline runs on a small public subset; output is a unified CSV/TSV with ≥95% non-missing gene pairs for variance metrics.

### Implementation for User Story 1

- [ ] T014 [US1] Implement `code/preprocess/rna_seq.py` for RNA-seq normalization (DESeq2-like approach using `scipy`/`sklearn` for CPU feasibility) and variance calculation.
- [ ] T015 [US1] Implement `code/preprocess/methyl.py` for methylation normalization (CpG-density adjustment) and variance calculation.
- [ ] T016 [US1] Implement **Leave-One-Generation-Out (LOGO)** jackknife logic in both `rna_seq.py` and `methyl.py` to ensure independent sample subsets for variance derivation.
- [ ] T017 [US1] Implement filtering logic to exclude genes with zero variance in both layers or missing data in either layer.
- [ ] T018 [US1] Implement global methylation level filter (<1% exclusion) and non-model organism exclusion.
- [ ] T019 [US1] Create `code/main.py` as an **initial/skeleton stateless orchestrator** that: (1) checks `output/discovery_status.json` for `halt_signal`, (2) creates `logs/` directory if missing, (3) invokes isolated modules `code/preprocess/rna_seq.py` and `code/preprocess/methyl.py` sequentially, (4) unifies results into `data/processed/variance_matrix.csv`, (5) logs execution to `logs/pipeline.log`, and (6) monitors runtime to fail if >6 hours (SC-004). **Note**: `main.py` must strictly forbid cross-contamination between streams.
- [ ] T020 [US1] Create `tests/unit/test_preprocess.py` to validate LOGO split and variance calculations on synthetic small datasets.

**Checkpoint**: Unified `data/processed/variance_matrix.csv` generated with valid LOGO-derived metrics.

---

## Phase 5: User Story 2 - Correlation Analysis and Environmental Stratification (Priority: P2)

**Goal**: Compute Spearman correlation between epigenetic and expression variance, stratified by environmental condition and stressor type.

**Independent Test**: Script produces Spearman's rho, p-value (theoretical and empirical), and a scatter plot.

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/analysis/correlation.py` to calculate Spearman's rho for "fluctuating" and "constant" subsets. **Output**: `output/correlation_results.json`.
- [ ] T023 [US2] Implement **iterative permutation test** in `correlation.py`. **Logic**: Start with a sufficient number of iterations. Calculate p-value. Check variance of p-value over the last [deferred] iterations. If variance > 0.001, increase iterations by [deferred] and repeat. **Hard Cap**: Stop at [deferred] iterations if stability not reached, then report the final p-value and a "convergence_warning" flag. **Output**: Updated `output/correlation_results.json`. **Dependency**: Requires T022.
- [ ] T024 [US2] Implement stressor stratification logic (e.g., temperature vs. nutrient) if metadata permits.
- [ ] T025 [US2] Implement `code/viz/plots.py` to generate scatter plots (x=epigenetic variance, y=expression variance) colored by condition.
- [ ] T026 [US2] Implement `Temporal Resolution Flag` logic: if N<3 generations or missing timescale, set `temporal_resolution_flag: "insufficient"` in `output/correlation_results.json` and exclude from final claim. **Dependency**: Requires T022 and metadata from T009/T010/T011.
- [ ] T027 [US2] Create `tests/unit/test_analysis.py` with unit tests for correlation math and permutation logic.

**Checkpoint**: `output/correlation_results.json` generated with rho, p-values, and flags.

---

## Phase 6: Revision - Timescale Alignment & Temporal Validation (Priority: P0)

**Goal**: Address reviewer concern to measure the timescale of epigenetic drift against the timescale of environmental change, strictly flagging alignment status without asserting causality (Constitution Principle VII).

**Independent Test**: The analysis script outputs a structured comparison of drift rates vs. environmental fluctuation frequencies, explicitly flagging cases where the timescales do not align.

### Implementation for Revision (Phase 6)

- [ ] T033 [P] [Revision] Implement `code/analysis/timescale_align.py` to extract "fluctuation timescale" from metadata. **Metadata Keys**: Check `fluctuation_timescale`, `fluctuation_period`, `env_period` in that order. **Calculation**: Compute "drift timescale" as the slope of variance vs. generation count (linear regression of variance on generation index). **Output**: `output/timescale_alignment.json` with raw values.
- [ ] T034 [P] [Revision] Implement logic to categorize the relationship as "Aligned" (drift rate matches environmental fluctuation frequency within 10%), "Mismatched" (drift is too slow/fast), or "Insufficient Data" (missing keys). **Output**: `output/timescale_alignment.json` with `alignment_status` field. **Dependency**: Requires T033.
- [ ] T035 [P] [Revision] Implement logic to set `temporal_validation_status` in `output/timescale_alignment.json` to "VALID" if "Aligned" or "Mismatched", and "INSUFFICIENT" if "Insufficient Data". Explicitly forbid any causal or "plausibility" scoring. **Dependency**: Requires T034.
- [ ] T036 [Revision] Update `code/main.py` to include `timescale_align.py` in the pipeline execution flow, ensuring it runs after `correlation.py` and before the final report merge. **Dependency**: Requires T035.
- [ ] T037 [P] [Revision] Create `tests/unit/test_timescale_align.py` to validate the comparison logic using mock data with known alignment/mismatch scenarios.

**Checkpoint**: `output/timescale_alignment.json` generated with alignment status and validation flag.

---

## Phase 7: User Story 3 - Threshold Sensitivity and Robustness Check (Priority: P3)

**Goal**: Verify correlation robustness across generation thresholds (3, 4, 5) and variance calculation parameters.

**Independent Test**: Sensitivity sweep runs; output shows correlation stability or flags instability (|Δrho| > 0.1).

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/analysis/sensitivity.py` to sweep minimum generation thresholds **specifically at values 3, 4, and 5 generations**.
- [ ] T029 [US3] Implement logic to report correlation coefficient variation across thresholds.
- [ ] T030 [US3] Implement stability check: flag result if correlation remains significant (p < 0.05) in <2 of 3 thresholds or if |Δrho| > 0.1. **Dependency**: Requires T023 (converged p-values) for empirical p-values.
- [ ] T031 [US3] Integrate sensitivity results into final report generation in `code/main.py`.
- [ ] T032 [US3] Create `tests/unit/test_sensitivity.py` to validate threshold sweep logic.

**Checkpoint**: Sensitivity analysis report appended to final results.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final verification

- [ ] T038 [P] Implement logic in `code/main.py` to merge `output/correlation_results.json`, `output/timescale_alignment.json`, and sensitivity results into a final `output/final_report.json`. **Dependency**: Requires T036.
- [ ] T039 [P] Create `tests/contract/test_schema.py` to validate final report structure against data-model.md.
- [ ] T040 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md` (specifically updating the hypothesis section to reflect the "timescale alignment" requirement).
- [ ] T041 Code cleanup and refactoring for memory efficiency (ensure <2GB RAM usage).
- [ ] T042 [P] Additional unit tests in `tests/unit/` for edge cases (zero variance, missing metadata, timescale mismatch).
- [ ] T043 Run `pytest` and verify all tests pass.
- [ ] T044 Run quickstart.md validation script.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 0 (P0) is the critical gate; if it fails, the project halts.
  - User Story 1 (P1) depends on valid data from US0.
  - User Story 2 (P2) depends on processed data from US1.
  - **Revision (Phase 6)**: Depends on US2 (T022) to access results for validation.
  - User Story 3 (P3) depends on results from US2 and Revision (Phase 6) to ensure sensitivity is applied to temporally validated data.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 0 (P0)**: No dependencies.
- **User Story 1 (P1)**: Depends on US0 (Data Availability).
- **User Story 2 (P2)**: Depends on US1 (Preprocessed Data).
- **Revision (Phase 6)**: Depends on US2 (T022) and US1 (T019).
- **User Story 3 (P3)**: Depends on Revision (Phase 6) to ensure sensitivity analysis uses temporally validated data.
- **Polish (Phase 8)**: Depends on all previous phases.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models/Config before Services/Logic.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel.
- Once Foundational phase completes, US0 can start.
- Revision tasks (Phase 6) T033, T034, T035 can run in parallel **after** T033 completes (T034, T035 depend on T033 output).
- Phase 8 tasks (T039-T044) can run in parallel after T038 completes.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for LOGO split in tests/unit/test_preprocess.py"

# Launch all models/logic for User Story 1 together:
Task: "Implement RNA-seq normalization in code/preprocess/rna_seq.py"
Task: "Implement Methylation normalization in code/preprocess/methyl.py"
```

---

## Implementation Strategy

### MVP First (User Story 0 & 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 0 (Data Discovery)
   - **STOP**: If <3 datasets found, halt.
4. Complete Phase 4: User Story 1 (Preprocessing)
   - **STOP**: Validate unified matrix.
5. Deploy/demo if ready (showing data availability and preprocessing).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready.
2. Add User Story 0 → Data gate validated.
3. Add User Story 1 → Preprocessed data ready.
4. Add User Story 2 → Correlation results generated.
5. Add Phase 6 (Revision) → Timescale alignment and temporal validation check (Reviewer Address).
6. Add User Story 3 → Sensitivity analysis added (using validated data).
7. Add Phase 8 → Final report generation and validation.
8. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
   - Developer A: User Story 0 & 1 (Data pipeline)
   - Developer B: User Story 2 (Correlation & Viz)
   - Developer C: Phase 6 (Timescale Alignment - Reviewer Focus)
   - Developer D: User Story 3 (Sensitivity - depends on B & C)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only (2 cores, 2GB RAM) within 6 hours. No GPU/8-bit models.
- **Data Integrity**: Use only real, verified datasets from GEO/ENCODE. No synthetic data for final analysis.
- **Observational Scope**: The study is strictly observational. No tasks should attempt to categorize drift as a "mechanism" or "cause".
- **Runtime Monitoring**: T019 must enforce the 6-hour limit; Phase 6 must only flag alignment/plausibility, not causality.
- **Reviewer Address**: Phase 6 specifically addresses the concern that "drift must be measured against environmental timescale" to distinguish noise from mechanism, strictly as a validation flag.