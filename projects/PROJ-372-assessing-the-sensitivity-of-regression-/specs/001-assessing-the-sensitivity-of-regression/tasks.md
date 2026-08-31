# Tasks: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

**Input**: Design documents from `/specs/001-sensitivity-regression-coefficients/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/

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

- [ ] T001a [P] Create `src/ingestion` directory and `__init__.py`
- [ ] T001b [P] Create `src/resampling` directory and `__init__.py`
- [ ] T001c [P] Create `src/analysis` directory and `__init__.py`
- [ ] T001d [P] Create `src/utils` directory and `__init__.py`
- [ ] T001e [P] Create `tests/unit` and `tests/integration` directories and `__init__.py` files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 [P] Create `requirements.txt` at repository root containing: `pandas>=2.0`, `numpy>=1.24`, `scipy>=1.10`, `statsmodels>=0.14`, `scikit-learn>=1.2`, `pyyaml>=6.0`, `datasets>=2.14`, `pytest>=7.4`, `linearmodels>=4.3`, `ruff>=0.1.0`, `black>=23.0`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Setup data directory structure (`data/raw`, `data/processed`, `artifacts`) and `.gitignore` for large files
- [X] T005 [P] Implement utility module for checksumming (MD5) and validation in `src/utils/validation.py`
- [X] T006 [P] Setup environment configuration management (loading dataset lists, random seeds) in `src/utils/config.py`
- [X] T007 [P] Create base data models (Pydantic/TypedDict) for `DatasetProfile`, `StabilityResult`, `InteractionModel` in `src/models/data_models.py`
- [X] T017 **Define Sample Size Tiers and Configuration**: Generate `research.md` in `specs/001-sensitivity-regression-coefficients/` explicitly documenting the rationale for the fixed sample size tier percentages `[10, 25, 50, 75, 90]`. **AND** Implement `src/utils/config.py` to define `SAMPLE_SIZE_TIERS` as a list of representative tiered values. and `VERIFIED_DATASETS = {'UCI:Auto': '...', 'HuggingFace:california_housing': '...'}`. This task is the single source of truth for tier values and dataset IDs. **Deliverable**: `research.md` with rationale and `src/utils/config.py` with constants.
- [X] T011a [P] **Populate Verified Dataset URLs**: Ensure `src/utils/config.py` contains the full list of verified dataset IDs and URLs (e.g., 'UCI:Auto', 'HuggingFace:california_housing', 'UCI:Concrete', 'HuggingFace:concrete_strength'). **Deliverable**: `src/utils/config.py` updated with `VERIFIED_DATASETS` dictionary.
- [ ] T008 [P] Configure error handling and logging infrastructure (structured logs to `artifacts/run.log`) in `src/utils/logger.py`
- [X] T009 [P] Implement checkpoint mechanism (save/load JSON state) in `src/utils/checkpoint.py` defining the **schema** for checkpoint state that T024 and T037 will consume to prevent schema drift.
- [ ] T017a [P] **DEPRECATED**: Merged into T017. Remove this task.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Violation Profiling (Priority: P1) 🎯 MVP

**Goal**: Ingest verified numerical datasets, profile OLS assumption violations (Breusch-Pagan, Cook's Distance, Condition Number), and ensure memory compliance.

**Independent Test**: Run ingestion script on a single known dataset (e.g., `Auto` from UCI) and verify output JSON contains valid, non-null values for `breusch_pagan_stat`, `max_cooks_distance`, and `condition_number`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for `DatasetProfile` schema validation in `tests/unit/test_profiler.py` implementing function `test_dataset_profile_rejects_null_bp_stat` with assertion that null BP stats raise ValidationError.
- [X] T011 [P] [US1] Integration test for dataset download and checksum verification in `tests/integration/test_downloader.py` using the 'Auto' dataset from UCI with a specific hardcoded checksum value.

### Implementation for User Story 1

- [ ] T012 [P] [US1] **Depends: T011a** Implement `downloader.py` in `src/ingestion/` to fetch datasets from verified HuggingFace/UCI URLs using `datasets.load_dataset(..., streaming=True)`. **Deliverable**: Save raw CSV to `data/raw/{dataset_id}.csv` and verify file exists and checksum matches. Use `VERIFIED_DATASETS` from `src/utils/config.py`.
- [X] T013 [US1] Implement strict data loader in `src/ingestion/downloader.py` that raises on failure. **Clarification**: "NO synthetic fallback" means no generation of fake data. **Rule**: If dataset > 100k rows, subsample to 100k rows; do not generate synthetic data. Raise error only if download fails or data is invalid.
- [ ] T014 [US1] Implement `profiler.py` in `src/ingestion/` to compute Condition Number, Breusch-Pagan statistic, and Cook's Distance on the full dataset (or streamed sample if >7GB). **Deliverable**: Write `artifacts/profiles/{dataset_id}.json` containing `breusch_pagan_stat`, `max_cooks_distance`, `condition_number`, and `violation_severity`.
- [X] T015 [US1] Implement logic in `src/ingestion/profiler.py` to classify violation severity (Low/Medium/High) based on computed statistics and handle multicollinearity (condition number > 30).
- [X] T016 [US1] Implement subsampling logic in `src/ingestion/profiler.py` for datasets > 100k rows to ensure CPU feasibility. **Reference**: Compare subsampled BP stat against the BP stat computed on the largest available sample (full dataset or streamed sample if >7GB) to verify stability (<5% deviation).
- [ ] T019 [US1] **Depends: T014** **Enforce Memory Constraint**: Implement logic in `src/ingestion/profiler.py` to immediately subsample datasets > 100k rows to exactly 100k rows using random sampling (seed=42) if the estimated RAM usage exceeds a substantial threshold. **Deliverable**: Log the reduction ratio and ensure profiling proceeds on the subsampled data. **Note**: This replaces the streaming fallback; subsampling is the primary constraint enforcement mechanism for >100k rows.
- [X] T020 [P] [US1] Create `src/ingestion/__init__.py` to expose `ingest_and_profile` pipeline that outputs `DatasetProfile` JSON to `artifacts/profiles/`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Subset Resampling and Stability Estimation (Priority: P2)

**Goal**: Generate random observation subsets across 5 sample size tiers, fit OLS models, and compute empirical standard deviation of coefficients.

**Independent Test**: Run resampling module on a small fixed dataset (N=500) with fixed seed, verify multiple subsets generated (distributed across tiers), OLS fits complete, and coefficient variance is a positive float.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for singularity detection (skip fit if condition number infinite) in `tests/unit/test_resampling.py` using input data with a fixed two-dimensional shape and condition number > 1e15, expecting a specific `LinAlgError`.
- [ ] T022 [US2] Integration test for resampling loop completion and artifact generation in `tests/integration/test_resampling.py`. **Deliverable**: Verify that the pipeline generates `artifacts/stability/{dataset_id}_sd.csv` and that OLS fits complete without crashing.

### Implementation for User Story 2

- [X] T023 [P] [US2] **Depends: T017** Implement `engine.py` in `src/resampling/` to generate random subsets per dataset across 5 tiers (percentages defined in `src/utils/config.py` by T017). **Deliverable**: Generate subsets for each tier.
- [X] T024 [US2] **Depends: T017** Implement robust OLS fitting loop in `src/resampling/engine.py` using `statsmodels` that catches singular matrix errors, skips invalid subsets, and logs warnings.
- [X] T025 [US2] **Depends: T017** Implement constraint check in `src/resampling/engine.py` to ensure subset size ≥ 10 × number of predictors before fitting.
- [ ] T026 [US2] **Depends: T023** Implement `aggregator.py` in `src/resampling/` to calculate empirical standard deviation of coefficients across the **initial** 200 valid subsets per tier. **Deliverable**: Generate `artifacts/stability/{dataset_id}_sd_initial.csv` with columns `dataset_id`, `sample_size_percent`, `coefficient_std_dev`, `n_valid_fits`. **Logic**: Generate a representative number of subsets per tier as the baseline.
- [X] T035 [US2] **Depends: T026** **Convergence Logic**: Implement function in `src/resampling/aggregator.py` to verify convergence (SE of SD < 5%). **Logic**: Start with the initial 200 subsets per tier from T026. If SE of SD >= 5%, generate **additional** subsets in increments per tier (up to a maximum of 500 subsets per tier) and re-calculate. **Deliverable**: Output `artifacts/convergence_result.json` with final subset count per tier and SE value.
- [ ] T035a [US2] **Depends: T035** **Convergence Artifact**: Generate `artifacts/convergence_result.json` containing the final subset count where SE < 5% was achieved (or the max reached).
- [ ] T036 [US2] **Depends: T035a** **Convergence Verification**: Implement a check in `src/resampling/aggregator.py` that raises an error or logs a warning if the Standard Error of the SD >= 5% after reaching the maximum subset limit (500 per tier).
- [ ] T027 [US2] **Depends: T023** Integrate checkpointing in `src/resampling/engine.py` to save intermediate results at regular intervals to prevent data loss on timeout.
- [ ] T028 [US2] **Depends: T023** Create `src/resampling/__init__.py` to expose `run_resampling_experiment` pipeline that outputs `StabilityResult` CSV/JSON to `artifacts/stability/`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interaction Analysis and Sensitivity Visualization (Priority: P3)

**Goal**: Run multiple regression with interaction terms, visualize sensitivity effects, and frame findings associatively.

**Independent Test**: Run analysis script on aggregated results, verify regression model includes interaction term (Condition Number × Violation Severity), and plot is generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for interaction term calculation and p-value extraction in `tests/unit/test_hlm_analysis.py` implementing function `test_interaction_term_pvalue_extraction` with expected p-value range within valid statistical bounds.
- [ ] T030 [P] [US3] Integration test for full meta-analysis pipeline in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [ ] T031 [P] [US3] **Depends: T028** Implement `hlm_analysis.py` in `src/analysis/` to perform **Multiple Regression** (per Spec FR-005) with `empirical_variance` as outcome and `condition_number`, `violation_severity`, and interaction as predictors. **Deliverable**: Generate `artifacts/meta_analysis_results.json` containing `interaction_coefficient`, `interaction_p_value`, `r_squared`.
- [ ] T043a [US3] **Depends: T028, T015** **Sensitivity Sweep Logic**: Implement sensitivity sweep in `src/analysis/hlm_analysis.py` to sweep Breusch-Pagan p-value cutoffs across standard significance levels (e.g., 0.01, 0.05, 0.10). Re-classify violation severity for each dataset based on the swept cutoffs and calculate the variance in classification rates. **Deliverable**: Generate `artifacts/sensitivity_sweep_raw.json` with classification rates per cutoff.
- [ ] T043b [US3] **Depends: T043a** **Sensitivity Sweep Reporting**: Implement report generator to summarize the sensitivity sweep results from T043a. **Deliverable**: Generate `artifacts/sensitivity_sweep.json` containing the variance in classification rates and final findings (FR-006).
- [ ] T032 [US3] **Depends: T028** Implement visualization module in `src/analysis/` to generate plots showing stability curves (variance vs. collinearity) for Low/Medium/High violation levels. **Deliverable**: Generate `artifacts/plots/stability_curve.png` using `matplotlib`.
- [ ] T033 [US3] **Depends: T028** Implement report generator in `src/analysis/` to explicitly state associational nature of findings and report interaction term significance. **Deliverable**: Generate `artifacts/report.md` containing the associational disclaimer and interaction significance results.
- [ ] T034 [US3] Create `src/analysis/__init__.py` to expose `run_meta_analysis` pipeline that outputs `InteractionModel` JSON to `artifacts/meta_analysis_results.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Convergence Verification & Polish

**Purpose**: Final verification of success criteria and cross-cutting improvements

- [ ] T037 [P] Documentation updates in `docs/` and `README.md`
- [ ] T038 Code cleanup and refactoring of error handling paths
- [ ] T039 Performance optimization for resampling loop (vectorization where possible)
- [ ] T040 [P] Additional unit tests for edge cases (empty subsets, missing values) in `tests/unit/`
- [ ] T041 [P] Run `quickstart.md` validation to ensure full pipeline executes within 6 hours on small dataset subset. **Deliverable**: Log wall-clock time and confirm ≤6h.
- [ ] T042 [P] Verify all artifacts include content hashes in `state.yaml`. **Deliverable**: Update `state/projects/PROJ-372-assessing-the-sensitivity-of-regression-.yaml` with artifact_hashes map.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T017 (Sample Size Tiers)** and US1 output (profiles) to proceed with resampling
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US2 output (stability results)** to proceed with meta-analysis

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
Task: "Unit test for DatasetProfile schema validation in tests/unit/test_profiler.py"
Task: "Integration test for dataset download and checksum verification in tests/integration/test_downloader.py"

# Launch all models for User Story 1 together:
Task: "Implement downloader.py in src/ingestion/"
Task: "Implement profiler.py in src/ingestion/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including T017)
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
 - Developer A: User Story 1 (including T017)
 - Developer B: User Story 2 (waiting for T017)
 - Developer C: User Story 3 (waiting on US2)
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
- **Critical Data Rule**: All data loaders MUST fail loudly on fetch error; no synthetic fallbacks allowed. Subsampling for memory compliance is allowed (if >100k rows).
- **Critical Compute Rule**: CPU-only execution is enforced. Streaming is mandatory for datasets > 7GB RAM; subsampling only if streaming fails, with explicit logging of sample size and limitations.
- **Critical Convergence Rule**: T035 and T036 must explicitly generate/access 200-subset results to verify SC-005, with expansion logic per tier.
- **Statistical Model Note**: Tasks implement Multiple Regression (Spec FR-005) despite Plan.md mentioning HLM. Plan.md requires update to align with Spec (out of scope for tasks).
- **Configuration Rule**: T017 is the single source of truth for sample size tiers and dataset IDs.