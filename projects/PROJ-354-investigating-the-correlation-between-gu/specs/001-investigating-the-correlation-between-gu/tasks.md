# Tasks: Gut Microbiome-Cognitive Correlation Study

**Input**: Design documents from `/specs/001-gut-microbiome-cognitive/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `results/`, `tests/`)
- [ ] T002 Initialize Python 3.10 project with `requirements.txt` (pinned versions: pandas, numpy, scikit-learn, statsmodels, seaborn, matplotlib, pyarrow, requests, zCompositions, huggingface_hub)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data validation gates and power analysis.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` with paths, random seeds, and constants. MUST include UK Biobank field IDs: microbiome-related fields, cognitive assessment fields, and confounder IDs (sex, age, BMI, etc.).
- [X] T005 [P] Setup data hygiene utilities (checksumming, PII masking helpers) in `code/utils/hygiene.py`
- [ ] T006 [P] Implement streaming/batch data loader utilities in `code/utils/streaming.py` to handle >14GB datasets within 7GB RAM limits
- [ ] T007 Create base data models/entities (Participant, MicrobiomeProfile, CognitiveScore) in `code/models/`
- [X] T008 Configure error handling and logging infrastructure in `code/utils/logging.py`
- [~] T009 Setup environment configuration management for credentials (UK Biobank token)
- [~] T019 [P] Implement `code/power_analysis.py` to generate synthetic dataset (beta=0.1), run power script, validate against theoretical values (SC-003), and **generate `results/power/power_report.md`** as the required evidence artifact. This task acts as a gate before statistical analysis.
- [X] T024a [P] **Execute Reference-Validator Agent** on cognitive instrument citations (FR-009) against primary sources. Generate `results/validation/instrument_citation_report.md` to satisfy the 'Verified Accuracy' gate.
- [X] T024b [P] Update `code/config.py` and metadata with validated citation IDs and enforce citation validity in `code/analysis.py` imports.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Download and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download UK Biobank microbiome 16S rRNA and cognitive data, filter cohort, and produce ILR-transformed data.

**Independent Test**: Run the pipeline on a subset; verify output contains ILR-transformed genus-level coordinates and matched cognitive scores with no missing participants.

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Unit test for ILR transformation with Bayesian zero-replacement in `tests/test_preprocess.py`
- [X] T011 [P] [US1] Unit test for cohort filtering logic (antibiotics, missingness) in `tests/test_preprocess.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/download.py` to fetch UK Biobank microbiome data and cognitive scores (fields 20400, 20002) using streaming batches <!-- ATOMIZE: requested -->
- [X] T013 [US1] Implement `code/preprocess.py` to filter cohort: exclude recent antibiotic users and participants missing either data type (log exclusion counts)
- [ ] T014 [US1] Apply **Bayesian-multiplicative zero-replacement** to raw microbiome counts (per Plan Complexity Tracking) to avoid log(0) bias. **Output**: `data/processed/zero_replaced_counts.parquet`.
- [ ] T015 [US1] Implement `code/preprocess.py` genus-level aggregation and **Isometric Log-Ratio (ILR)** transformation. Pipeline: Zero-replaced counts -> Centered Log-Ratio (CLR) -> ILR (orthonormal coordinates). **Output**: `data/processed/ilr_coordinates.parquet`. Satisfies Constitution Principle VI.
- [ ] T015.5 [US1] Derive `Age_Group` categorical variable from continuous age in `code/preprocess.py` using a **configurable cutoff**. **Output**: `data/processed/cohort_with_age_groups.parquet` and `results/validation/age_group_check.json`.
- [ ] T016 [US1] Generate `data/processed/cohort_retention_log.json` containing retention counts and rate (SC-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Association Analysis with Confounder Control (Priority: P2)

**Goal**: Fit linear models with confounders, apply Benjamini-Hochberg correction, and validate power.

**Independent Test**: Run analysis on validation subset; verify association statistics (beta, p-values, adj-p) are computed correctly with covariates.

### Tests for User Story 2 (OPTIONAL)

- [ ] T017 [P] [US2] Unit test for Benjamini-Hochberg correction logic in `tests/test_analysis.py`
- [ ] T018 [P] [US2] Unit test for power analysis script using synthetic beta=0.1 dataset in `tests/test_power.py`

### Implementation for User Story 2

- [ ] T020a [US2] Implement `code/analysis.py` to fit **Standard OLS** linear models for main effects (ILR coords vs. cognitive scores) with covariates (age, sex, BMI, diet, activity, medication). **Requires T019 completion** (Power Gate).
- [ ] T020b [US2] Implement `code/analysis.py` covariate handling logic and ensure all confounders from FR-004 are included.
- [ ] T021 [US2] Implement `code/analysis.py` Benjamini-Hochberg correction for all taxon-cognitive associations and report adjusted p-values (FR-005). **Output**: `results/associations/main_effects.parquet`.
- [ ] T022a [US2] Fit reduced models excluding diet/medication covariates to check for over-control bias (FR-010).
- [ ] T022b [US2] Generate over-control bias comparison report comparing effect sizes between full and reduced models. **Output**: `results/sensitivity/over_control_report.json`.
- [ ] T023 [US2] Update `results/associations/*.parquet` metadata columns to include `causality_claim: false` (FR-008).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interaction Analysis and Visualization (Priority: P3)

**Goal**: Validate findings via age-interaction analysis and generate Manhattan-style plots.

**Independent Test**: Run interaction analysis; verify interaction p-values are computed and plots are generated with correct annotations.

### Tests for User Story 3 (OPTIONAL)

- [ ] T025 [P] [US3] Unit test for interaction term construction (Age_Group * Taxon) in `tests/test_analysis.py`
- [ ] T026 [P] [US3] Unit test for Manhattan plot generation logic in `tests/test_visualize.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/analysis.py` interaction models: fit linear models with 'Age_Group * Taxon' term to assess age-dependent effects without splitting sample (FR-006). **Output**: `results/associations/interaction_effects.parquet`.
- [ ] T028 [US3] Implement `code/visualize.py` to generate Manhattan-style plots showing -log10(p-values) for each taxon-cognitive association with effect size annotations (FR-007). **Output**: `results/plots/manhattan_plot.png`.
- [ ] T029 [US3] Implement `code/visualize.py` threshold sweep sensitivity analysis (SC-005): sweep p-value cutoffs including conventional significance thresholds and report 'headline association rate' (count of taxa with adj-p < threshold). **Requires T027 completion**. **Output**: `results/sensitivity/threshold_sweep_report.json`.
- [ ] T030 [US3] Generate final reports: Aggregate Association results, Sensitivity analysis (Threshold Sweep, Over-control), and Power analysis reports in `results/`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T032 Code cleanup and refactoring
- [ ] T033 Performance optimization (ensure streaming logic keeps RAM < 7GB)
- [ ] T034 [P] Additional integration tests in `tests/test_integration.py`
- [ ] T035 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. Includes T019 (Power Gate) and T024 (Validation Gate).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 results output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
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
Task: "Unit test for ILR transformation with Bayesian zero-replacement in tests/test_preprocess.py"
Task: "Unit test for cohort filtering logic (antibiotics, missingness) in tests/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download.py to fetch UK Biobank 16S data..."
Task: "Implement code/preprocess.py to filter cohort..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Power & Validation gates)
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
- **Critical Constraint**: All data processing MUST respect CPU-only, constrained RAM, and limited disk space constraints. Use streaming/batching and sampling if necessary. No GPU/CUDA/8-bit quantization allowed.
- **Methodology Note**: ILR transformation is mandatory (Constitution Principle VI). Zero-replacement MUST use Bayesian-multiplicative method (Plan Complexity Tracking), not fixed pseudocounts.
- **Citation Gate**: T024a must pass before any analysis code consumes cognitive instrument definitions.
- **Power Gate**: T019 must pass (Power Report generated) before T020a (Statistical Analysis) begins.