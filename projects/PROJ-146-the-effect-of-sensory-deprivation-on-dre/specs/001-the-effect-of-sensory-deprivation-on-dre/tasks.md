# Tasks: The Effect of Sensory Deprivation on Dream Recall and Bizarreness (Simulation Study)

**Input**: Design documents from `/specs/001-sensory-deprivation-dreams/`
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

- [X] T001 [P] Create project directory structure per implementation plan (`projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/`) including: `data/raw/`, `data/synthetic/`, `data/processed/`, `data/protocols/`, `data/ethics/`, `code/`, `results/models/`, `results/reports/`, `tests/unit/`, `tests/contract/`, `tests/integration/`.
- [X] T002 [P] Initialize Python 3.11 project with dependencies in `code/requirements.txt` (pandas, numpy, statsmodels, scikit-learn, seaborn, pyyaml, pytest).
- [X] T003 [P] Configure linting and formatting tools (ruff/black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `data/ethics/ethics-waiver.md` placeholder for synthetic data usage
- [X] T005 [P] Create `data/protocols/protocol.yaml` defining simulation parameters with EXACT machine-readable values for the three thresholds required by FR-004:
 - `strict_threshold_label: "strict (complete isolation)"`
 - `moderate_threshold_label: "moderate (partial sensory reduction)"`
 - `partial_threshold_label: "partial (minimal sensory reduction)"`
 - Also define: N=200, effect_sizes=[moderate positive, null, moderate negative] [UNRESOLVED-CLAIM: c_caa22019 — status=not_enough_info], ICC=0.3.
- [X] T006 Create `contracts/` directory with `dataset.schema.yaml` and `model-output.schema.yaml`
- [X] T007 Initialize `code/__init__.py` and set up logging infrastructure in `code/logging_config.py`
- [X] T008 Setup `pytest` configuration in `tests/conftest.py` and create empty test directory structure

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Data Ingestion and Synthetic Simulation Fallback (Priority: P1) 🎯 MVP

**Goal**: Implement a robust data pipeline that ingests real CSVs or generates statistically valid synthetic datasets with multiple ground truths (Positive, Null, Negative effects) to validate the analysis pipeline.

**Independent Test**: The pipeline can be tested by running `code/generate_data.py` and `code/ingest.py` against a mock CSV or generated synthetic CSV and verifying the output dataframe contains required columns (`condition`, `recall`, `bizarreness`, `participant_id`) with non-null values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for synthetic data schema in `tests/contract/test_synthetic_schema.py` <!-- FAILED: unspecified -->
- [ ] T010 [P] [US1] Unit test for data ingestion logic with missing metadata in `tests/unit/test_ingest.py` <!-- SKIPPED: non-mapping output -->

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `code/generate_data.py` to create synthetic datasets based on `data/protocols/protocol.yaml` (N=200, 3 scenarios: d=0.5, d=0.0, d=-0.2 [UNRESOLVED-CLAIM: c_7543fa71 — status=not_enough_info])
- [X] T012 [US1] Implement `code/ingest.py` to detect "sensory deprivation" tags in CSVs: check for column 'condition' containing 'sensory_deprivation' OR 'deprivation' string. If absent, auto-trigger `generate_data.py` with parameters from `protocol.yaml` (N=200, d=0.5).
- [ ] T013 [US1] Implement logic to save generated synthetic data to `data/synthetic/` with clear "Simulation-based" flags in metadata
- [~] T014 [US1] Implement logic to save processed data to `data/processed/` with derived `condition` column based on deprivation intensity thresholds (strict, moderate, partial)
- [~] T015 [US1] Add validation to ensure `recall` is binary (0/1) and `bizarreness` is integer 1-7 in the final dataframe
- [~] T016 [US1] Add logging for data generation parameters and ingestion source (real vs. synthetic)
- [~] T017 [US1] Implement logic to generate/iterate processed datasets for ALL three thresholds defined in `protocol.yaml` (strict, moderate, partial) and save them as distinct files: `data/processed/data_threshold_strict.csv`, `data/processed/data_threshold_moderate.csv`, `data/processed/data_threshold_partial.csv`. Each file must contain the `condition` column populated with the exact label from `protocol.yaml`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Data Pipeline Ready)

---

## Phase 4: User Story 2 - Mixed-Effects Statistical Modeling (Priority: P1)

**Goal**: Fit mixed-effects logistic regression for dream recall and linear mixed-effects models for dream bizarreness, treating participant ID as a random intercept.

**Independent Test**: The analysis script can be tested by running it on a small, hardcoded dataset with known effect sizes and verifying that the output JSON contains the correct model coefficients (within floating-point tolerance) and p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`
- [~] T019 [P] [US2] Unit test for logistic regression fit on known data in `tests/unit/test_models.py`

### Implementation for User Story 2

- [~] T020 [US2] Implement `code/models.py` with `fit_logistic_mixed` using `statsmodels` GLM with Firth correction (penalized likelihood) or a custom penalized likelihood wrapper to handle zero-count recall cases, as native mixed-effects Firth is unsupported.
- [~] T021 [US2] Implement `fit_linear_mixed` in `code/models.py` for `bizarreness` scores using `statsmodels` (approximation if necessary)
- [~] T022 [US2] Implement logic to handle `participant_id` as a random intercept (using `statsmodels` grouping) for logistic and linear models.
- [~] T022a [US2] **Design Waiver**: Document the deviation from FR-008 (Mixed-Effects Ordinal) due to lack of CPU-tractable mixed-effects ordinal libraries in Python. Define the fallback strategy: use Fixed-Effects OrderedModel (T024) and validate its accuracy against the known random-intercept ground truth of the synthetic data (T023).
- [~] T023 [US2] Implement `code/models.py` with `validate_ordinal_approx`: A routine that takes the synthetic data (with known random intercepts), fits the Fixed-Effects OrderedModel, and compares the recovered fixed effects against the known ground truth to quantify the approximation error. This satisfies the robustness intent of FR-008.
- [~] T024 [US2] Implement `fit_ordinal_approx` in `code/models.py` using `statsmodels.OrderedModel` as a FIXED-EFFECTS approximation for robustness check against the linear model, strictly following the Design Waiver (T022a) and using the validation routine (T023) to confirm validity.
- [~] T025 [US2] Implement result serialization to `results/models/` containing fixed effects estimates, standard errors, degrees of freedom, and p-values
- [~] T026 [US2] Add logic to detect sample size < 10 and issue a warning or fallback to fixed-effects model
- [~] T027 [US2] Ensure all results are framed as "associational" in the output metadata (no causal language)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Data + Modeling Ready)

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P2)

**Goal**: Perform sensitivity analysis by sweeping "sensory deprivation" definitions (strict, moderate, partial) and execute bootstrap validation to verify stability of effect estimates.

**Independent Test**: The script can be tested by manually altering a threshold parameter in the configuration and verifying the output logs show the recalculated p-values and effect sizes for the new threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T028 [P] [US3] Integration test for sensitivity sweep in `tests/integration/test_sensitivity.py`
- [~] T029 [P] [US3] Unit test for bootstrap resampling logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [~] T030 [US3] Implement `code/sensitivity.py` with `run_threshold_sweep` to iterate over the three distinct datasets generated in T017 (`data_threshold_strict.csv`, `data_threshold_moderate.csv`, `data_threshold_partial.csv`). Read the exact threshold labels from `protocol.yaml` and use them in the report.
- [~] T031 [US3] Implement `run_bootstrap` in `code/sensitivity.py` with a dynamic resample loop: start at 1,000, increase until the 95% CI width variance < 1% OR a hard cap of 5,000 resamples is reached [UNRESOLVED-CLAIM: c_8fc7da0a — status=not_enough_info]. If the cap is hit, use the last stable CI and log a warning.
- [~] T032 [US3] Implement logic to compare bootstrap CIs against original parametric CIs AND explicitly check if the confidence interval crosses zero.; flag as 'unstable' if it does, satisfying SC-003.
- [~] T033 [US3] Implement result aggregation to `results/models/` containing variation tables for odds ratios across thresholds
- [ ] T034 [US3] Add logic to generate a "Robustness" summary section in the final report data

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Reporting (Cross-Cutting)

**Purpose**: Generate the final report and ensure all constraints are met

- [ ] T035 [P] Implement `code/report.py` to compile model results, sensitivity analysis, and bootstrap findings into a final JSON/HTML report
- [ ] T036 [P] Ensure the report explicitly frames findings as "associational" and flags simulation-based results
- [ ] T037 [P] Add a "Data Hygiene" section in the report confirming synthetic data usage and protocol adherence
- [ ] T038 [P] Run full pipeline end-to-end test to verify completion within 6 hours on GitHub Actions free-tier runner. **CRITICAL**: This task MUST generate `results/timing_log.json` containing `total_duration_seconds` to serve as the artifact for SC-005.
- [ ] T039 [P] Update `quickstart.md` with instructions for running the simulation study
- [ ] T040 [P] Validate all output schemas against `contracts/` definitions
- [ ] T041 [P] Document the deviation from FR-008 in `docs/technical_constraints.md` and the final report, explicitly stating that `statsmodels.OrderedModel` (fixed-effects) was used as a proxy for the required ordinal mixed-effects model due to library limitations, and referencing the validation performed in T023.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **User Story 2 (P1)**: Can start after Foundational (Phase 2) - **MUST WAIT** for T017 (US1) to produce processed data with `condition` column for ALL three thresholds.
 - **User Story 3 (P2)**: Can start after Foundational (Phase 2) - **MUST WAIT** for T025 (US2) to produce model outputs.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Depends on US1 data output (specifically T017)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on US2 model outputs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **Note**: User stories CANNOT run in parallel with each other due to data flow dependencies (US1 -> US2 -> US3).
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories MUST be worked on sequentially or by different team members only after the upstream story is complete.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for synthetic data schema in tests/contract/test_synthetic_schema.py"
Task: "Unit test for data ingestion logic with missing metadata in tests/unit/test_ingest.py"

# Launch all models for User Story 1 together:
Task: "Implement code/generate_data.py to create synthetic datasets..."
Task: "Implement code/ingest.py to detect 'sensory deprivation' tags..."
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
3. Add User Story 2 → Test independently → Deploy/Demo (Depends on US1)
4. Add User Story 3 → Test independently → Deploy/Demo (Depends on US2)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - **WAIT** for Developer A to complete T017 before Developer B starts US2.
 - Developer B: User Story 2 (Modeling)
 - **WAIT** for Developer B to complete T025 before Developer C starts US3.
 - Developer C: User Story 3 (Sensitivity)
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
- **CRITICAL**: All statistical modeling must use CPU-tractable methods (no GPU, no 8-bit quantization).
- **CRITICAL**: Synthetic data must be generated with pinned seeds for reproducibility.
- **CRITICAL**: All findings must be framed as "associational" and clearly labeled as simulation-based.
- **CRITICAL**: User Stories 2 and 3 depend on the completion of upstream data/model tasks; they cannot start in parallel with US1.
- **CRITICAL**: The protocol.yaml (T005) MUST contain the exact, unique strings for the three thresholds to satisfy FR-004.
- **CRITICAL**: The ordinal model (T024) is a fixed-effects approximation validated by T023 against the random-intercept ground truth.