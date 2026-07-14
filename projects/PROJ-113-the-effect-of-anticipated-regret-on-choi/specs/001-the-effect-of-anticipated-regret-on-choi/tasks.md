# Tasks: The Effect of Anticipated Regret on Choice Deferral

**Input**: Design documents from `/specs/001-the-effect-of-anticipated-regret-on-choi/`
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

- [ ] T001.1 Create project directories per implementation plan: `mkdir -p projects/PROJ-113-the-effect-of-anticipated-regret-on-choi/{data/raw,data/processed,code/tests/unit,code/tests/contract,code/utils,data/results}`
- [ ] T001.2 Create base `__init__.py` files for `code/` and `tests/` packages
- [ ] T002 Create `requirements.txt` based on plan.md dependencies (pandas, numpy, scikit-learn, statsmodels, pyyaml, requests, datasets)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites & Research Definitions)

**Purpose**: Core infrastructure and RESEARCH DEFINITIONS that MUST be complete before ANY user story can be implemented. This phase resolves all spec-plan deviations and defines the methodology.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes the "Kahneman Review" resolution as a core requirement.

- [ ] T004 Create data directories and schema for raw/processed files (`data/raw/`, `data/processed/`)
- [ ] T005 Initialize base ingestion utilities: Create `code/ingest.py` with `load_and_checksum(url)` function that outputs `data/raw/checksums.json`
- [ ] T006 [P] Setup logging infrastructure for data hygiene and PII scanning (`code/utils/logging.py`)
- [X] T007 Create base configuration management for dataset URLs and random seeds (`code/config.py`)

### Research Definitions & Spec Amendments (Must precede Implementation)

- [ ] T008.1 [Research] Verify original sources: Run a check to confirm the OpenML Task ID and the empty Kaggle URL are invalid or lack required variables. Log results to `research.md`.
- [ ] T008.2 [Research] Document Deprecation: Update `research.md` to explicitly state that OpenML/Kaggle sources are deprecated and replaced by HuggingFace datasets (`zhehuderek/textual_decisionmaking_data`, `PhillyMac/Decision_Making_Content_1`). Create a trace mapping FR-001 to these new sources.
- [ ] T008.3 [Research] Spec Amendment: Update `research.md` with a formal "Spec Amendment" section that justifies the deviation from FR-002 (SD of EU) to "Min-Max Regret" (opportunity cost) as the primary proxy, citing the circularity and psychological construct reasons.
- [ ] T008.4 [Research] Covariate Mapping: Update `research.md` to explicitly state that FR-003's "price variance" proxy applies to the `perceived_risk` COVARIATE in the regression model, not the `regret_proxy` calculation.
- [ ] T008.5 [Research] Sensitivity Scope: Update `research.md` to document that the sensitivity analysis (FR-005) now covers SIX variations (Spec: Utility Variance, Price Variance, Attribute Range; Plan: Min-Max, Price Variance, Attribute Entropy) to ensure comprehensive robustness.
- [ ] T008.6 [Research] SC-006 Conditionality: Update `research.md` to document that SC-006 (self-report validation) is conditional on data availability. If self-report data is missing, the check is marked "N/A" rather than failing.

### Core Feature Implementation (Kahneman Review Resolution)

- [ ] T044 [Foundational] Implement "Loss Aversion Control" feature in `code/features.py` that calculates a separate `potential_loss_magnitude` metric (max possible loss) independent of the regret proxy.
- [~] T045 [Foundational] Add `potential_loss_magnitude` as a mandatory covariate in the mixed-effects model formula (to be implemented in T024.1). <!-- FAILED: unspecified -->
- [~] T046 [Foundational] Add diagnostic logic to `code/features.py` to compare `regret_proxy` and `potential_loss_magnitude` correlation.
- [~] T047 [Foundational] Update `research.md` with a dedicated section "Distinguishing Regret from Loss Aversion" explaining the operational definitions and the statistical control strategy implemented in T044-T046.
- [~] T048 [Foundational] Ensure the sensitivity analysis explicitly tests if the effect holds when the proxy is defined purely by price variance (risk) vs. opportunity cost (regret).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Regret Proxy Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest verified HuggingFace datasets (as per plan substitution), filter for deferral events, and compute the "Min-Max Regret" proxy.

**Independent Test**: The pipeline runs on a static sample of `zhehuderek/textual_decisionmaking_data`, outputs a CSV with `regret_proxy` (Min-Max), and correctly flags `deferral=1` for timeouts.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T013 [P] [US1] Unit test for `regret_proxy` calculation with single-option edge case in `tests/unit/test_features.py`
- [~] T014 [P] [US1] Contract test for data schema validation (missing deferral flags excluded) in `tests/contract/test_schemas.py`

### Implementation for User Story 1

- [~] T015 [US1] Implement data loader for HuggingFace dataset `zhehuderek/textual_decisionmaking_data` (referencing T008.2 trace) in `code/ingest.py`
- [~] T016 [US1] Implement data loader for HuggingFace dataset `PhillyMac/Decision_Making_Content_1` (referencing T008.2 trace) in `code/ingest.py`
- [~] T017 [US1] Implement deferral flag logic (timeout without action) in `code/ingest.py`
- [~] T010 [US1] Implement the "Min-Max Regret" proxy calculation logic (opportunity cost) in `code/features.py` function `calculate_min_max_regret` (referencing T008.3 amendment)
- [ ] T010.5 [US1] Implement the Spec-mandated "SD of Normalized EU" calculation in `code/features.py` for comparison purposes only (referencing T008.3 amendment)
- [~] T011 [US1] Add validation to ensure `regret_proxy` is 0 when only one option exists (per FR-002)
- [~] T018 [US1] Implement fallback logic: If "perceived risk" scores are missing, calculate `price_variance` and use it as the `perceived_risk` COVARIATE in the model formula (referencing T008.4).
- [~] T019 [US1] Generate `data/processed/regret_proxy_v1.csv` with `regret_proxy` and `deferral` columns
- [ ] T020 [US1] Log number of rows excluded due to missing deferral flags or invalid options

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Mixed-Effects Logistic Regression Modeling (Priority: P2)

**Goal**: Fit the mixed-effects model with `regret_proxy`, `option_count`, and random intercepts, plus VIF and cross-validation.

**Independent Test**: Model outputs `coefficients.csv` with `regret_proxy` beta, VIF < 5 for all predictors, and 5-fold CV AUC.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for VIF calculation (flagging VIF > 5) in `tests/unit/test_modeling.py`
- [ ] T022 [P] [US2] Contract test for model output schema (beta, SE, p-value) in `tests/contract/test_schemas.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement residualization of `regret_proxy` against `option_count` for orthogonalization in `code/features.py` (referencing T008.3 logic)
- [ ] T024 [US2] Implement Base Mixed-Effects Logistic Regression using `statsmodels` with `participant` as random intercept in `code/modeling.py` (without Loss Aversion control)
- [ ] T024.1 [US2] Implement Extended Mixed-Effects Logistic Regression adding `potential_loss_magnitude` (from T044) as a covariate to control for loss aversion (referencing T045)
- [ ] T025 [US2] Implement interaction term `regret_proxy × option_count` in the model formula
- [ ] T026 [US2] Implement VIF calculation for all fixed effects in `code/modeling.py` and FLAG predictors with VIF > 5 (raise warning/error)
- [ ] T027 [US2] Implement k-fold cross-validation for AUC score in `code/modeling.py`
- [ ] T028 [US2] Handle edge case: Exclude participants with only one trial from random effect estimation and log to `data/processed/excluded_participants.csv`
- [ ] T029 [US2] Handle missing covariates: implement mean imputation or exclusion strategy and log affected rows
- [ ] T030 [US2] Generate `data/results/coefficients.csv` and `data/results/model_summary.txt`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Checks and Sensitivity Analysis (Priority: P3)

**Goal**: Replicate analysis on secondary dataset and sweep proxy definitions (6 variations: Spec + Plan).

**Independent Test**: Robustness script produces separate regression tables for the secondary dataset and a sensitivity report showing stability of the odds ratio.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_schemas.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement robustness check: replicate primary model on `PhillyMac/Decision_Making_Content_1` in `code/robustness.py`
- [ ] T033 [US3] Implement sensitivity sweep for Proxy Variation 1: Min-Max Regret (Opportunity Cost)
- [ ] T033.5 [US3] Implement sensitivity sweep for Proxy Variation 2 (Spec): Utility Variance (SD of Normalized EU)
- [ ] T034 [US3] Implement sensitivity sweep for Proxy Variation 3: Price Variance
- [ ] T034.5 [US3] Implement sensitivity sweep for Proxy Variation 4 (Spec): Price Variance (Duplicate for cross-check)
- [ ] T035 [US3] Implement sensitivity sweep for Proxy Variation 5: Attribute Entropy
- [ ] T035.5 [US3] Implement sensitivity sweep for Proxy Variation 6 (Spec): Attribute Range
- [ ] T036 [US3] Implement multiple-comparison correction (Bonferroni or BH) for main effect and interaction p-values
- [ ] T037 [US3] Validate proxy validity: Check for self-report data. If present, calculate correlation with `regret_proxy`; if correlation < 0.3, flag warning. If missing, log "N/A" and skip. Output `data/results/proxy_validity_report.md` (referencing T008.6)
- [ ] T038 [US3] Generate `data/results/robustness_report.md` comparing coefficient directions across datasets
- [ ] T039 [US3] Generate `data/results/sensitivity_analysis.csv` showing odds ratio variation across all 6 proxy definitions

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T049 [P] Documentation updates in `README.md` and `docs/quickstart.md`
- [ ] T050 Code cleanup and refactoring of `code/` modules
- [ ] T051 Configure CI timeout limit to a sufficient duration in `.github/workflows/ci.yml`
- [ ] T052 [P] Additional unit tests for edge cases (empty datasets, all-zero variance) in `tests/unit/`
- [ ] T053 Run `quickstart.md` validation to ensure reproducibility
- [ ] T054 Final verification: Ensure all tasks run on CPU-only free-tier (no CUDA/GPU dependencies)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes all research definitions and Kahneman resolution.**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (cleaned CSV)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US1 and US2

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
Task: "Unit test for regret_proxy calculation with single-option edge case in tests/unit/test_features.py"
Task: "Contract test for data schema validation in tests/contract/test_schemas.py"

# Launch all models for User Story 1 together:
Task: "Implement data loader for HuggingFace dataset in code/ingest.py"
Task: "Implement deferral flag logic in code/ingest.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes research definitions)
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
 - Developer A: User Story 1 (Ingestion)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Robustness)
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
- **Critical**: All tasks must run on CPU-only free-tier CI (limited CPU, 7GB RAM, 6h). No GPU/8-bit models.
- **Research Note**: Phase 2 includes all necessary spec amendments and research definitions (T008.1-T008.6) to resolve deviations and ensure traceability before any code is written.
- **Kahneman Note**: The "Loss Aversion Control" (T044-T048) is now a core part of the Foundational phase (Phase 2), not scope creep, ensuring the model in T024.1 can be implemented correctly.