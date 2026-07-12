# Tasks: Predicting Molecular Complexity Using Information Theory

**Input**: Design documents from `/specs/001-predict-molecular-complexity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
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

- [ ] T001 Create project structure: `mkdir -p code/ data/raw/ data/processed/ tests/unit tests/integration`
- [ ] T002 Create `code/requirements.txt` with pinned versions: `rdkit==2023.9.1`, `pandas==2.1.0`, `numpy==1.24.0`, `scipy==1.11.0`, `scikit-learn==1.3.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `requests==2.31.0`, `huggingface_hub==0.17.0`, `datasets==2.14.0`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**NOTE**: The following tasks are **Atomic File Creation Tasks**. Each task creates exactly ONE file. Do not combine these into a single implementation step.

- [ ] T004 [P] [Atomic] Create `code/config.py`: Define `{'SEED': 42, 'DATASET_ID': 'sagawa/pubchem-10m-canonicalized', 'CHUNK_SIZE': 500, 'TIMEOUT_SECONDS': 60, 'MAX_RETRIES': 3, 'MEMORY_LIMIT_GB': 'sufficient for the workload'}`. Ensure `DATASET_ID` reflects the Plan's override of the Spec's CID requirement. Note: This configuration supports the analysis of molecular complexity vs. chemical properties on a representative random sample of PubChem.

- [ ] T005 [P] [Atomic] Create `code/download.py`: Implement `fetch_molecules()` using `datasets.load_dataset` with streaming for `sagawa/pubchem-10m-canonicalized`. Implement retry logic (exponential backoff, max 3 retries) for network errors. Verify SHA-256 checksums. Output an iterator of dicts `{'cid': int, 'smiles': str}`. **Do not** implement PubChem API logic; use HuggingFace as per Plan.
- [ ] T006 [P] [Atomic] Create `code/metrics.py` with exact signatures:
  - `calculate_shannon_entropy(smiles: str) -> float`
  - `calculate_lzma_length(smiles: str) -> int`
  - `calculate_sa_score(smiles: str) -> float`
  - `calculate_qed_score(smiles: str) -> float`
  - `calculate_molecular_weight(smiles: str) -> float`
  - `calculate_atom_count(smiles: str) -> int`
- [ ] T007 [P] [Atomic] Create `code/main.py` orchestration skeleton: Load config, initialize logging, define `process_chunk` function.
- [ ] T008 [P] [Atomic] Configure logging in `code/main.py` to capture skipped molecules (invalid SMILES, timeouts) with specific format: `{"event": "skipped", "reason": "timeout" | "invalid_smiles", "cid": int}`.
- [ ] T009 [P] [Atomic] Create `code/setup_env.py` (or equivalent): Configure environment variables for CI runner constraints (CPU-only, memory limits) and validate `rdkit` installation.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Correlation Analysis (Priority: P1) 🎯 MVP

**Goal**: Download molecules, compute metrics, and output statistical report with Pearson correlations.

**Independent Test**: The system must successfully download molecules, compute all four metrics, and output a JSON report containing Pearson correlation coefficients and p-values for both metric pairs without crashing on invalid entries.

### Test Scaffolding for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these test scaffolds FIRST to define assertions for Phase 2 functions.

- [ ] T010 [P] [US1] Add `tests/unit/test_metrics.py::test_shannon_entropy_returns_positive_float` with assertion: Input `smiles="CCO"`, assert `result > 0` and `isinstance(result, float)`.
- [ ] T011 [P] [US1] Add `tests/unit/test_metrics.py::test_lzma_length_returns_integer` with assertion: Input `smiles="CCO"`, assert `isinstance(result, int)` and `result > 0`.
- [ ] T012 [P] [US1] Add `tests/unit/test_metrics.py::test_sa_and_qed_return_valid_range` with assertion: Input `smiles="CCO"`, assert `0.0 <= sa_score <= 10.0` and `0.0 <= qed_score <= 1.0`.
- [ ] T013 [P] [US1] Add `tests/integration/test_error_handling.py::test_invalid_smiles_skipped` with assertion: Input list `["CCO", "INVALID_SMILES_STRING", "CC"]`, assert `skipped_count == 1` and `valid_count == 2`.

### Implementation for User Story 1

- [ ] T014 [US1] **VERIFY DATA SOURCE**: Confirm `code/main.py` calls `code/download.py` (T005) which fetches from `sagawa/pubchem-10m-canonicalized`. Document in `code/main.py` comments that this overrides Spec FR-001 (CID 1-5000) per Plan, ensuring the sample is representative.
- [ ] T014B [US1] **Document Deviation**: Update `code/report.py` to include a `limitations` section in the final JSON/HTML report explicitly stating: "Analysis performed on HuggingFace dataset 'sagawa/pubchem-10m-canonicalized' (random sample) instead of Spec FR-001 (CID 1-5000) per Plan.md. Results are generalizable to chemical space but not strictly limited to the CID 1-5000 range."
- [ ] T015 [US1] Implement `code/main.py` chunked processing loop: Iterate `code/download.py` in batches of `CHUNK_SIZE`; call `code/metrics.py` functions; write results incrementally to `data/processed/metrics.csv` (columns: cid, smiles, entropy, lz, sa, qed, mw, atom_count).
- [ ] T016 [US1] Implement `code/analysis.py` function `calculate_pearson_correlations(df: pd.DataFrame) -> dict`: Input `df` columns; use `scipy.stats.pearsonr`; return dict `{'entropy_sa': (r, p), 'entropy_qed': (r, p), ...}`.
- [ ] T017 [US1] Implement `code/report.py` function `generate_initial_report(correlations: dict) -> None`: Write JSON to `data/processed/report.json` with keys `r`, `p`, `n`, and explicit label `type: "associational"`.
- [ ] T018 [US1] Implement timeout handling in `code/metrics.py` wrapper: Enforce `TIMEOUT_SECONDS` per molecule with a duration sufficient to complete the evaluation.; log skipped entries with `reason: "timeout"`; ensure no hanging processes.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Robustness & Sensitivity (Priority: P2)

**Goal**: Verify correlations via bootstrap resampling, apply multiple-comparison correction, and implement additional statistical methods per Plan.

**Independent Test**: The system must perform a sufficient number of bootstrap iterations to generate 95% confidence intervals., apply Bonferroni correction, and include Spearman/Partial correlations.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for bootstrap resampling logic in `tests/unit/test_analysis.py`: Input `data=[1, 2, 3, 4, 5]`, `n_iter=100`, assert `len(results) == 100` and `0 < mean(results) < 6`.
- [ ] T021 [P] [US2] Unit test for multiple-comparison correction (Bonferroni) in `tests/unit/test_analysis.py`: Input `p_values=[0.01, 0.04, 0.05, 0.06]`, `n_tests=4`, assert `adjusted[0] == 0.04` and `adjusted[3] == 1.0` (capped at 1).

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/analysis.py` function `calculate_bootstrap_stats(df: pd.DataFrame, metric_x: str, metric_y: str, n_iter: int=1000) -> dict`: Resample rows with replacement; calculate Pearson r for each iteration; compute 95% CI using percentile method; return `{'r_mean': float, 'ci_lower': float, 'ci_upper': float, 'std': float}`.
- [ ] T022B [US2] **Orchestrate Bootstrap**: Update `code/main.py` to call `calculate_bootstrap_stats` for all four metric pairs after Pearson calculation and pass results to `generate_final_report`.
- [ ] T023 [US2] Implement `code/analysis.py` function `apply_multiple_comparison_correction(p_values: dict) -> dict`: Apply Bonferroni correction to 4 p-values; return adjusted p-values.
- [ ] T037 [US2] Implement `code/analysis.py` function `calculate_spearman_correlations(df: pd.DataFrame) -> dict`: Use `scipy.stats.spearmanr`; return dict of r and p-values for same pairs as Pearson.
- [ ] T037B [US2] **Integrate Spearman**: Update `code/report.py` to include Spearman correlation results (r and p) in the final report table.
- [ ] T037C [US2] **Execute Spearman**: Update `code/main.py` to explicitly call `calculate_spearman_correlations` and pass results to `generate_final_report`.
- [ ] T038 [US2] Implement `code/analysis.py` function `calculate_partial_correlations(df: pd.DataFrame) -> dict`: Control for MW and Atom Count; return partial r and p-values for Entropy-SA and LZ-SA.
- [ ] T038B [US2] **Integrate Partial**: Update `code/report.py` to include Partial correlation results (r and p) in the final report table.
- [ ] T038C [US2] **Execute Partial**: Update `code/main.py` to explicitly call `calculate_partial_correlations` and pass results to `generate_final_report`.
- [ ] T040 [US2] **Load Data for Analysis**: Implement `code/main.py` step to load `data/processed/metrics.csv` into a pandas DataFrame (`df_full`) for analysis. Handle `FileNotFoundError` gracefully.
- [ ] T039 [US2] **Enforce Memory Limit**: Implement `code/analysis.py` function `enforce_memory_limit_bootstrap(df: pd.DataFrame) -> pd.DataFrame`:
    1. Check `df.memory_usage(deep=True)`.
    2. If `> 4GB`:
       a. Bin `atom_count` into 10 quantiles.
       b. Use `sklearn.model_selection.StratifiedShuffleSplit` with `n_splits=1`, `train_size` calculated to result in exactly `n=5000` rows.
       c. Return the subsampled DataFrame.
       d. Log a warning: "Dataset exceeded a substantial size threshold. Subsampled to a representative subset using stratified sampling by atom count for bootstrap stability."
       e. Pass a flag `subsampled=True` to the report generator.
    3. If `<= 4GB`, return `df` unchanged and log "Full dataset fits in memory; no subsampling required."
- [ ] T024 [US2] Update `code/report.py` to include:
    - Bootstrap statistics (CI lower/upper, SD) for all pairs.
    - Adjusted p-values.
    - Spearman r and p-values.
    - Partial r and p-values.
    - If `subsampled=True`, include a "Stability Note" in the report: "Confidence intervals derived from a stratified subsample (n=5000) due to memory constraints. Full dataset stability assumed based on representativeness."
- [ ] T025 [US2] Add logic to handle memory constraints during bootstrap (stratified subsample if necessary) and document in report.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization & Reporting (Priority: P3)

**Goal**: Generate scatter plots with regression lines, confidence intervals, and annotated statistics.

**Independent Test**: The system must generate four distinct scatter plots (Entropy-SA, Entropy-QED, LZ-SA, LZ-QED) with linear regression lines and annotated r, p, n values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for plot generation logic in `tests/unit/test_viz.py`: Input `df` with 10 rows, `x='entropy'`, `y='sa'`, assert `fig` is not None and `fig.axes` length >= 1.

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/viz.py` function `generate_scatter_plot(x: str, y: str, df: pd.DataFrame) -> Figure`: Use `seaborn.regplot`; figure size set to standard dimensions appropriate for publication.; include a confidence interval band; save to `data/processed/plots/{x}_{y}.png`.
- [ ] T028 [US3] Update `code/viz.py` to annotate each plot with Pearson r, p-value, and sample size (n) in the top-right corner.
- [ ] T029 [US3] Implement `code/report.py` to compile all plots and statistical tables into a single HTML report. Include the "Limitations" section from T014B and "Stability Note" from T024 if applicable.
- [ ] T030 [US3] Add validation to ensure plots are saved to `data/processed/plots/` directory.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation.

- [ ] T031 [P] Documentation updates in `README.md` and `docs/` explaining the associational nature of findings and the data source deviation (Plan vs Spec).
- [ ] T031B [P] **Clarify Data Source**: Update `README.md` "Data" section to explicitly state: "Data source: HuggingFace dataset 'sagawa/pubchemm-canonicalized' (random sample of a large number of molecules). This supersedes the Spec's original CID 1-5000 requirement as per Plan.md."
- [ ] T032 Code cleanup and refactoring to ensure memory efficiency.
- [ ] T041 [P] **Performance Optimization**: Run `python -m cProfile -o profile.out code/main.py`. Identify the top 3 bottleneck functions in `code/metrics.py` or `code/main.py` loop. Optimize using vectorization (pandas/numpy) or multiprocessing (if I/O bound). Verify `time python code/main.py` output ≤ 45 minutes (SC-005).
- [ ] T034 [P] Additional unit tests for edge cases (empty dataset, all invalid SMILES) in `tests/unit/`: Input `df_empty`, assert `result` is empty dict; Input `df_all_invalid`, assert `skipped_count == total`.
- [ ] T035 Run `quickstart.md` validation to ensure end-to-end pipeline works.
- [ ] T036A [P] **Verify Checksums**: Implement `code/download.py` to verify SHA-256 checksums of downloaded files against the HuggingFace manifest.
- [ ] T036B [P] **Record Checksums**: Implement `code/main.py` to write the verified SHA-256 checksums of `data/raw/*.parquet` into `state/projects/PROJ-425-predicting-molecular-complexity-using-in/artifact_hashes.yaml` in the format: `artifact: data/raw/...` -> `sha256: ...`.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1 for bootstrap
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US1 for plots

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Functions before orchestration
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for Shannon Entropy calculation in tests/unit/test_metrics.py"
Task: "Unit test for LZMA compression length in tests/unit/test_metrics.py"

# Launch all core functions for User Story 1 together:
Task: "Implement code/download.py chunked fetching..."
Task: "Implement code/metrics.py functions..."
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
- **Critical Constraint**: All tasks must run on CPU-only CI with a constrained number of cores and limited memory. No GPU, no 8-bit models, no large LLMs.
- **Data Integrity**: Only use real data from `sagawa/pubchem-10m-canonicalized`. No synthetic/fake data generation.
- **Spec Deviation Note**: Tasks T005 and T014 implement the Plan's override of the Spec's CID 1-5000 requirement, using the HuggingFace dataset `sagawa/pubchem-10m-canonicalized` instead. T014B is now a documentation task to ensure this deviation is recorded in the final report.