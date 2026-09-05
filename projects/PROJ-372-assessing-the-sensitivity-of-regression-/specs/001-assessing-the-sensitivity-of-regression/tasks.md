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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] **Project Initialization & Configuration**: Create all required directories (`src/ingestion`, `src/resampling`, `src/analysis`, `src/utils`, `tests/unit`, `tests/integration`) and their `__init__.py` files. Create `requirements.txt` with pinned dependencies, `.ruff.toml`, `pyproject.toml` (black config), `.pre-commit-config.yaml`, and `.gitignore` with specific patterns for data/artifacts. **Deliverable**: All directories, config files, and init files exist and are tracked in git.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 [P] Create `.gitkeep` files to all newly created empty directories to ensure they are tracked.
- [X] T003 [P] Implement utility module for checksumming (MD5) and validation in `src/utils/validation.py`.
- [X] T004 [P] Setup environment configuration management (loading dataset lists, random seeds, sample size tiers) in `src/utils/config.py`. **Rule**: Sample size tiers must be read from config, not hardcoded, with the lowest tier representing a minimal cohort size.
- [X] T005 [P] Create base data models (Pydantic/TypedDict) for `DatasetProfile`, `StabilityResult`, `InteractionModel` in `src/models/data_models.py`.
- [X] T006 [P] Configure error handling and logging infrastructure (structured logs to `artifacts/run.log`) in `src/utils/logger.py`.
- [X] T007 [P] Implement checkpoint mechanism (save/load JSON state) in `src/utils/checkpoint.py` defining the **schema** for checkpoint state that T024 and T047 will consume to prevent schema drift. **Schema Fields**: Must include `dataset_id`, `tier`, `predictor`, `sd_value` to match T024 output.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Violation Profiling (Priority: P1) 🎯 MVP

**Goal**: Ingest verified numerical datasets, profile OLS assumption violations (Breusch-Pagan, Cook's Distance, Condition Number), and ensure memory compliance.

**Independent Test**: Run ingestion script on a single known dataset (e.g., `Auto` from UCI) and verify output JSON contains valid, non-null values for `breusch_pagan_stat`, `max_cooks_distance`, and `condition_number`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for `DatasetProfile` schema validation in `tests/unit/test_profiler.py` implementing function `test_dataset_profile_rejects_null_bp_stat` with assertion that `ValidationError` is raised with message 'breusch_pagan_stat cannot be null'.
- [X] T011 [P] [US1] Integration test for dataset download and checksum verification in `tests/integration/test_downloader.py` using the 'Auto' dataset from UCI. The test must compute the MD5 checksum of the downloaded file dynamically and assert it is a valid non-empty hex string, rather than hardcoding a specific value.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `downloader.py` in `src/ingestion/` to fetch datasets from verified HuggingFace/UCI URLs using `datasets.load_dataset(..., streaming=True)`. **Rule**: Fail loudly on fetch error; no synthetic fallback.
- [X] T014 [US1] Implement `profiler.py` in `src/ingestion/` to compute Condition Number, Breusch-Pagan statistic, and Cook's Distance on the full dataset (or streamed sample if >7GB). **Deliverable**: `DatasetProfile` JSON artifact.
- [X] T015 [US1] Implement logic in `src/ingestion/profiler.py` to classify violation severity (Low/Medium/High) based strictly on Breusch-Pagan p-values (Spec thresholds: Low > 0.10, Med 0.05-0.10, High <= 0.05). **Rule**: Maintain strict mapping to Spec thresholds. Do NOT mix collinearity severity into this classification.
- [X] T020 [P] [US1] Create `src/ingestion/__init__.py` to expose `ingest_and_profile` pipeline that outputs `DatasetProfile` JSON to `artifacts/profiles/`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Subset Resampling and Stability Estimation (Priority: P2)

**Goal**: Generate random observation subsets across 5 sample size tiers, fit OLS models, and compute empirical standard deviation of coefficients.

**Independent Test**: Run resampling module on a small fixed dataset (N=500) with fixed seed, verify multiple subsets generated (distributed across tiers), OLS fits complete, and coefficient variance is a positive float.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for singularity detection (skip fit if condition number infinite) in `tests/unit/test_resampling.py` using input data with a fixed two-dimensional shape and condition number > 1e15, expecting a specific `LinAlgError`.
- [X] T022 [P] [US2] Integration test for resampling loop completion and artifact generation in `tests/integration/test_resampling.py` verifying that 200 subsets are generated per tier, OLS models fit successfully, and `coefficient_sd.json` contains positive float values for standard deviations.

### Implementation for User Story 2

- [X] T023 [P] [US2] **Subset Generation**: Implement `engine.py` in `src/resampling/` to generate random subsets per dataset across multiple specific tiers [10, 25, 50, 75, 90] as defined in `spec.md`. **Deliverable**: Save subset indices to `artifacts/stability/subsets_{dataset_id}_{tier}.json`. **Constraint**: Read tiers from config; do NOT hardcode.
- [X] T024 [US2] **Resampling & Convergence (Blocking Gate)**: Implement robust OLS fitting loop in `src/resampling/engine.py` that:
    1. **Pre-flight Check**: Validates existence of `artifacts/profiles/{dataset_id}.json` (from T020) before proceeding. Fails if missing.
    2. Generates 200 subsets per tier.
    3. Fits OLS models, catching singular matrix errors.
    4. Computes empirical standard deviation of coefficients for each predictor across subsets per tier.
    5. Calculates Standard Error of the SD using the formula: $SE_{SD} = SD / \sqrt{2(N-1)}$ where $N=200$.
    6. **Blocking Gate**: Verifies convergence (SE < 5% of SD). If failed, logs 'FAIL' to `convergence.log` and **HALTS** further analysis for that tier. The system must NOT proceed to US3 for this dataset/tier if convergence fails.
    **Deliverables**:
    - `artifacts/stability/coefficient_sd.json` (schema: dataset_id, tier, predictor, sd_value)
    - `artifacts/stability/convergence_analysis.json` (schema: n_sd, m_sd, delta)
    - `artifacts/convergence.log` (format: 'SE_SD: <value>')
    - `artifacts/stability/convergence_status.json` (schema: pass/fail flag)
- [X] T028 [US2] **Pipeline Exposure**: Create `src/resampling/__init__.py` to expose `run_resampling_experiment` pipeline that outputs `StabilityResult` CSV/JSON to `artifacts/stability/`. **Note**: Pipeline exposed after T024 data production; convergence check (T024) is a blocking gate.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interaction Analysis and Sensitivity Visualization (Priority: P3)

**Goal**: Run multiple regression with interaction terms, visualize sensitivity effects, and frame findings associatively.

**Independent Test**: Run analysis script on aggregated results, verify regression model includes interaction term (Condition Number × Violation Severity), and plot is generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for interaction term calculation and p-value extraction in `tests/unit/test_regression_analysis.py` implementing function `test_interaction_term_pvalue_extraction` with expected p-value range within valid statistical bounds.
- [X] T030 [P] [US3] Integration test for full meta-analysis pipeline in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [X] T044 [US3] **Theoretical Baseline**: Implement function in `src/analysis/regression_analysis.py` to calculate theoretical variance predicted by condition number alone (homoscedastic OLS formula) for each dataset. **Input**: Requires `artifacts/stability/coefficient_sd.json` (from T028) and `artifacts/profiles/*.json` (from T020).
- [X] T045 [US3] **Baseline Comparison**: Implement function in `src/analysis/regression_analysis.py` to compare empirical variance (from T028) against theoretical variance (from T044) and log the ratio. **Input**: Requires `artifacts/stability/coefficient_sd.json` (from T028) and `artifacts/profiles/*.json` (from T020).
- [X] T031 [P] [US3] **Multiple Regression**: Implement `regression_analysis.py` in `src/analysis/` to perform **Multiple Regression** (per Spec FR-005) with `empirical_variance` as outcome and `condition_number`, `violation_severity`, and interaction as predictors. **Deliverable**: `InteractionModel` JSON. **Input**: Requires `artifacts/stability/coefficient_sd.json` (from T028) and `artifacts/profiles/*.json` (from T020).
- [X] T032 [US3] **Visualization**: Implement visualization module in `src/analysis/` to generate plot `artifacts/meta_analysis/stability_curves.png` using `matplotlib`, plotting `coefficient_std_dev` vs `condition_number` for each `violation_severity` group.
- [X] T033 [US3] **Report Generator**: Implement report generator in `src/analysis/` to generate `artifacts/meta_analysis/final_report.md` containing a summary of the interaction term p-value and an explicit statement of associational nature.
- [X] T034 [US3] Create `src/analysis/__init__.py` to expose `run_meta_analysis` pipeline that outputs `InteractionModel` JSON to `artifacts/meta_analysis/interaction_model.json` with schema validation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Convergence Verification & Polish

**Purpose**: Final verification of success criteria and cross-cutting improvements

- [X] T063 [P] Update `README.md` with CLI usage examples including `python -m src.cli --config test_config.yaml`.
- [X] T064 [P] Update `docs/quickstart.md` with detailed pipeline execution steps.
- [X] T065 [P] Verify `README.md` contains correct artifact paths for all outputs by comparing against generated artifacts.
- [X] T066 [P] Refactor error handling in `src/ingestion/downloader.py` to use custom exception classes.
- [X] T060 [P] **Plan Amendment Verification**: Verify that `plan.md` has been updated to reflect the change from HLM to Multiple Regression (as per Spec). **Deliverable**: Confirmation that `plan.md` Summary, Technical Context, and Complexity Tracking sections no longer reference HLM.
- [X] T060a [P] [Plan Alignment] **Edit Plan**: Execute the update to `plan.md` to replace all references to Hierarchical Linear Model (HLM) with Multiple Regression. **Deliverable**: `plan.md` text updated.
- [X] T060b [P] [Plan Alignment] **Add Section**: Add a 'Plan Amendment' section to `plan.md` documenting the change from HLM to Multiple Regression. **Deliverable**: `plan.md` updated with new section.
- [X] T060c [P] [Plan Alignment] **Verification**: Run a verification script to ensure `tasks.md` implementation (Multiple Regression) matches `plan.md` description (Multiple Regression). Fail if `plan.md` still mentions HLM. **Deliverable**: `artifacts/alignment_check.json` with status "PASS" or "FAIL".
- [X] T041 [P] Execute `python -m src.cli --config test_config.yaml` and verify completion time < 6 hours on a 4-core CPU runner.
- [X] T042 [P] Run `scripts/verify_hashes.py` to ensure all files in `artifacts/` have corresponding entries in `state.yaml` with matching MD5 hashes.

---

## Phase 7: Revision & Robustness Fixes (Addressing Analyze Findings)

**Purpose**: Address specific issues raised by `/speckit.analyze` regarding data flow, streaming robustness, and statistical rigor.

- [ ] T070a [US1] **Streaming Robustness Fix (Chunked Iterator)**: Refactor `src/ingestion/profiler.py` to explicitly handle `streaming=True` for datasets > 7GB. Implement a chunked iterator that processes data in blocks of a specified size to compute Condition Number and Breusch-Pagan statistics without loading the full dataset into RAM. **Constraint**: Must not use `try/except` to fall back to synthetic data. **Reference**: FR-030 (Constitution) - Real Data Only.
- [ ] T070b [US1] **Error Handling (Fail Loudly)**: Implement specific error handling in `src/ingestion/profiler.py` to raise `DataFetchError` if streaming fails or data is unavailable. **Constraint**: No synthetic fallback. **Reference**: FR-030 (Constitution) - Real Data Only; Execution Gate Rules.
- [ ] T072 [US2] **Convergence Logic Fix**: Update `src/resampling/engine.py` to correctly compute the Standard Error of the SD ($SE_{SD} = SD / \sqrt{2(N-1)}$) where $N=200$ subsets. Ensure the convergence check (SE < 5% of SD) is applied *per tier* and logs a distinct "FAIL" status in `convergence.log` if the threshold is not met, halting further analysis for that tier. **Reference**: Spec US2 AC: "System verifies convergence".
- [ ] T073 [US3] **Interaction Model Rigor**: Refactor `src/analysis/regression_analysis.py` to explicitly encode `violation_severity` as a categorical variable (Low, Medium, High) in the regression model, rather than a continuous proxy, to correctly test the interaction effect between severity groups and subset size. **Reference**: Spec US3 AC: "System performs multiple regression with interaction terms".
- [ ] T074 [US3] **Visualization Clarity**: Update `src/analysis/viz.py` to generate stability curves that clearly distinguish between the theoretical baseline (homoscedastic) and the empirical results, including confidence intervals derived from the 200 subsets. **Reference**: Spec US3 AC: "System generates stability curves".

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on completion of US1-US3 and analysis report

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T004 (Config) and US1 output (profiles) to proceed with resampling. **Explicit Dependency**: T024 requires `artifacts/profiles/{dataset_id}.json` (from T020).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (stability results) and US1 output (profiles) to proceed with meta-analysis. **Explicit Dependency**: T031, T044, T045 require `artifacts/stability/coefficient_sd.json` (from T028) and `artifacts/profiles/*.json` (from T020).

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
3. Complete Phase 3: User Story 1 (including T004 Config)
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
 - Developer A: User Story 1 (including T004 Config)
 - Developer B: User Story 2 (waiting for T004 Config)
 - Developer C: User Story 3 (waiting for US2)
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
- **Critical Data Rule**: All data loaders MUST fail loudly on fetch error; no synthetic fallbacks allowed. Subsampling for memory compliance is allowed (if >100k rows AND >7GB RAM) ONLY if explicitly stated in Spec.
- **Critical Compute Rule**: CPU-only execution is enforced. Streaming is mandatory for datasets > 7GB RAM; subsampling only if streaming fails, with explicit logging of sample size and limitations.
- **Critical Convergence Rule**: T024 must explicitly generate/access subsets and compare SD to verify SC-005. The check is a **Blocking Gate**.
- **Statistical Model Note**: Tasks implement Multiple Regression (Spec FR-005) as per plan update. Plan.md HLM reference is superseded by Spec.
- **Plan Amendment**: T060, T060a, T060b, T060c track the deviation from Plan.md (HLM) to Spec.md (Multiple Regression) and mandate plan.md update and verification.
- **Design Parameter Rule**: Sample size tiers and other research parameters MUST be defined in `spec.md` before implementation. Tasks must not hardcode these values.
- **Revision Note**: Phase 7 tasks (T070a, T070b, T072-T074) specifically address data flow, streaming robustness, and statistical rigor concerns raised in the analysis phase. T070a/b explicitly cite FR-030 Constitution for error handling.
