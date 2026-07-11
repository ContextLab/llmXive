# Tasks: The Impact of Self‑Compassion on Resilience to Negative Feedback

**Input**: Design documents from `/specs/001-self-compassion-feedback/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-167-the-impact-of-self-compassion-on-resilie/`)
- [ ] T002 Initialize Python 3.10+ project with pinned dependencies in `requirements.txt` (pandas, statsmodels, seaborn, matplotlib, scikit-learn, requests, pyyaml, jinja2)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/__init__.py` and establish package structure (`code/download_data.py`, `code/clean_data.py`, `code/analyze.py`, `code/visualize.py`, `code/report.py`, `code/main.py`)
- [ ] T005 [P] Implement `state/projects/PROJ-167-the-impact-of-self-compassion-on-resilie.yaml` schema and initialization logic for storing checksums and run metadata
- [ ] T006 [P] Create `contracts/` directory and define `dataset.schema.yaml`, `output.schema.yaml`, `report.schema.yaml`, `analysis_result.schema.yaml` per plan.md
- [ ] T007 Implement `code/utils.py` with helper functions: `hash_artifact` (SHA-256), `verify_citations` (title overlap/source reachability), `check_random_seed`
- [ ] T008 Setup `data/raw/` (read-only) and `data/clean/` directories; add `.gitignore` rules for raw data and large artifacts
- [ ] T009 Implement `code/config.py` to load environment variables and default paths (OSF ID `3k9r2`, output dirs, random seed `42`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Test Buffering Effect (Priority: P1) 🎯 MVP

**Goal**: Implement the core ANCOVA pipeline to test if self-compassion moderates the impact of negative feedback on anxiety, rumination, and self-efficacy.

**Independent Test**: Run the pipeline on the verified dataset; verify regression tables include `C(feedback)[T.2]:SCS_z` interaction term, Holm-Bonferroni adjusted p-values, and 95% CI. If data is missing or N < 92, verify pipeline logs warnings and continues (does not abort).

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**
> **Note**: T010-T012 are unit tests for specific modules. The "Independent Test" for the story is the full pipeline validation.

- [ ] T010 [P] [US1] Unit test `test_download_data.py` for OSF URL reachability, column verification, and checksum generation
- [ ] T011 [P] [US1] Unit test `test_clean_data.py` for listwise deletion logic, N < 92 warning condition, and z-scoring accuracy
- [ ] T012 [P] [US1] Unit test `test_analyze.py` for ANCOVA model fitting, interaction term extraction, and Holm-Bonferroni correction logic

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/download_data.py`: Fetch OSF CSV, verify columns (`scf_total`, `scf_self_judgment`, `scf_self_kindness`, `stai_pre`, `stai_post`, `rrs_pre`, `rrs_post`, `gse_pre`, `gse_post`, `feedback_cond`, `age`, `gender`), compute SHA-256 hash. If N < 92 after listwise deletion, log `[POWER_INSUFFICIENT: Sample size (N) is less than the required 92 for adequate power (f²=0.02, α=0.05, power=0.80). Results are reported with caution.]` and **CONTINUE** execution (do NOT abort). If required columns are missing, abort with `[DATA_UNAVAILABLE: Required columns missing from dataset. Expected: [list of missing columns]]`.
- [ ] T013b [US1] Implement `code/download_data.py` state update: Write the computed SHA-256 checksum into `state/projects/PROJ-167-the-impact-of-self-compassion-on-resilie.yaml` at the key path `artifact_hashes.dataset` to satisfy FR-016.
- [ ] T014 [US1] Implement `code/download_data.py` metadata check: Verify participant well-being protocols (debriefing, pre-screening). If unconfirmed, log `[ETHICAL_GAP: Participant well-being protocols (pre-screening, debriefing) not confirmed in dataset metadata. Findings will be framed as associational.]`, set `is_causal = False`, and **CONTINUE** execution (do NOT abort).
- [ ] T014b [US1] Implement `code/download_data.py` randomization check: Read dataset metadata for 'experimental randomization' flag. If absent, set `is_causal = False`; otherwise `is_causal = True`. This flag will be used by T020 to frame results.
- [ ] T015 [US1] Implement `code/clean_data.py`: Perform MCAR test (custom or `pingouin`), handle missing data (listwise deletion), log exclusion counts, z-score continuous predictors (SCS, baselines), encode `feedback_cond` (0=Positive, 1=Neutral, 2=Negative) with 'Positive Feedback' as reference. Log warning if N < 92 but continue.
- [ ] T016 [US1] Implement `code/clean_data.py` Big Five check: If personality traits exist, include them as covariates; otherwise log warning and proceed.
- [ ] T017 [US1] Implement `code/analyze.py`: Fit ANCOVA models (statsmodels OLS) for `stai_post`, `rrs_post`, `gse_post` with covariates (baseline, age, gender, SCS_z, Big Five if present) and interaction `C(feedback)[T.2]:SCS_z`.
- [ ] T018 [US1] Implement `code/analyze.py`: Extract interaction stats (coef, SE, p-value, CI, partial η²) and compute robust HC3 standard errors.
- [ ] T019 [US1] Implement `code/analyze.py`: Apply Holm-Bonferroni correction **across the three primary outcomes only** (anxiety, rumination, self-efficacy) and report adjusted p-values. Do NOT include robustness tests in this correction family.
- [ ] T020 [US1] Implement `code/analyze.py`: Add logic to frame results as "associational" if `is_causal` is False (from T014b); otherwise frame as causal.
- [ ] T021 [US1] Implement `code/analyze.py`: Perform Breusch-Pagan test for heteroskedasticity; flag in report if p < 0.10.
- [ ] T039 [US1] Implement `code/analyze.py`: Fit the homogeneity of slopes model (interaction between `feedback_cond` and baseline outcome). If p < 0.10, flag the model as "Potentially Biased" and log the specific violation. This must run before report generation.
- [ ] T040 [US1] Implement `code/analyze.py`: If homogeneity is violated, prepare data for Johnson-Neyman interval calculation (or log the recommendation if full implementation is deferred to a future phase).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Visualize Simple Slopes (Priority: P2)

**Goal**: Generate clear plots showing the interaction effect at low, mean, and high levels of self-compassion.

**Independent Test**: Execute visualization module; verify three PNG files (`anxiety_simple_slopes.png`, `rumination_simple_slopes.png`, `self_efficacy_simple_slopes.png`) exist, render correctly, and display three distinct lines (-1 SD, mean, +1 SD SCS).

### Tests for User Story 2

- [ ] T022 [P] [US2] Unit test `test_visualize.py` for correct line plotting, labeling, and file saving logic

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/visualize.py`: Load analysis results and cleaned data. Calculate SCS values at low, mean, and high levels of the predictor.
- [ ] T024 [US2] Implement `code/visualize.py`: Generate Matplotlib/Seaborn plots for each outcome (`stai_post`, `rrs_post`, `gse_post`) showing the relationship between feedback condition and outcome, with separate lines for Low, Mean, and High SCS.
- [ ] T025 [US2] Implement `code/visualize.py`: Add confidence bands, axis labels, legends, and titles. Ensure the "Negative Feedback" line is visually distinct.
- [ ] T026 [US2] Implement `code/visualize.py`: Save plots to `outputs/plots/` as `<outcome>_simple_slopes.png`. Verify file size > 0.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Checks (Priority: P3)

**Goal**: Confirm findings are robust to alternative moderators, collinearity, and threshold sensitivity.

**Independent Test**: Run robustness checks; verify report includes VIF values, Self-Kindness subscale results, and sensitivity analysis across α ∈ {0.01, 0.05, 0.10}.

### Tests for User Story 3

- [ ] T027 [P] [US3] Unit test `test_analyze.py` for VIF calculation, bootstrap convergence, and sensitivity analysis logic

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/analyze.py`: Compute Variance Inflation Factors (VIF) for all predictors. Flag if VIF > 5.
- [ ] T029 [US3] Implement `code/analyze.py`: Re-run primary moderation analysis using `scf_self_kindness` as the moderator. Output same statistics as primary model.
- [ ] T030 [US3] Implement `code/analyze.py`: Perform bootstrap for interaction coefficient. Assess convergence by stability of the 95% CI width (change < 0.01 over last 1,000 resamples). If convergence is not achieved within 10,000 total resamples, **MUST NOT abort** but MUST report the exact caveat: `[BOOTSTRAP_CONVERGENCE_CAVEAT: Bootstrap did not converge within 10,000 resamples. Results reported with caution.]`.
- [ ] T031 [US3] Implement `code/analyze.py`: Apply Holm-Bonferroni correction **separately** to the robustness tests (3 outcomes using Self-Kindness) distinct from the primary tests. Report two separate sets of adjusted p-values.
- [ ] T032 [US3] Implement `code/analyze.py`: Run sensitivity analysis sweeping α across a range of small significance thresholds and count significant findings for each threshold.
- [ ] T033 [US3] Implement `code/analyze.py`: Compare bootstrap CI and parametric CI; add methodological caveat if they do not overlap.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Generate HTML Report (Priority: P2)

**Goal**: Consolidate all results, visualizations, and caveats into a single shareable HTML report.

**Independent Test**: Run reporting module; verify `report.html` exists, renders in Chrome/Firefox, and contains all required sections (Data Cleaning, Descriptive Stats, Model Results, Robustness, Visualizations, Caveats).

### Tests for User Story 4

- [ ] T034 [P] [US4] Integration test `test_report.py` to verify HTML generation and content inclusion

### Implementation for User Story 4

- [ ] T035 [US4] Implement `code/report.py`: Create Jinja2 template with sections for Data Cleaning, Descriptive Statistics, Model Results (tables), Robustness Checks, Visualizations (embedded PNGs), and Methodological Caveats.
- [ ] T036 [US4] Implement `code/report.py`: Dynamically populate template with `AnalysisResult` object data (no hard-coded numbers).
- [ ] T037 [US4] Implement `code/report.py`: Inject "Methodological Caveats" section that explicitly states causal vs. associational framing based on `is_causal` flag (from T014b), flags VIF > 5, and includes homogeneity of slopes flags (from T039).
- [ ] T038 [US4] Implement `code/main.py`: Orchestrate the full pipeline (Download → Clean → Analyze → Visualize → Report) and ensure exit code 0 on success or specific error codes on failure.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `docs/` and `README.md`
- [ ] T042 Code cleanup and refactoring (remove unused imports, optimize memory usage)
- [ ] T043 Performance optimization (ensure analysis completes within 6 hours on 2 CPU/7GB RAM)
- [ ] T044 [P] Additional unit tests in `tests/unit/` for edge cases (missing columns, N < 92, non-convergence)
- [ ] T045 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 results for plotting
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 models for robustness
- **User Story 4 (P2)**: Depends on US1, US2, and US3 completion to generate the final report
- **Phase 7 (Homogeneity)**: Moved to Phase 3. T039/T040 must run after T017/T018 but before T035 (Report Generation) to ensure the report contains accurate bias flags.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before Services/Analysis
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
# Launch all tests for User Story 1 together:
Task: "Unit test test_download_data.py for OSF URL reachability"
Task: "Unit test test_clean_data.py for listwise deletion logic"
Task: "Unit test test_analyze.py for ANCOVA model fitting"

# Launch all models/utilities for User Story 1 together:
Task: "Implement code/download_data.py: Fetch OSF CSV and verify columns"
Task: "Implement code/clean_data.py: Perform MCAR test and listwise deletion"
Task: "Implement code/analyze.py: Fit ANCOVA models and extract stats"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Download, Clean, ANCOVA, Primary Stats, Homogeneity Check)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify interaction term, CI, error handling, homogeneity flags)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Visualizations)
4. Add User Story 3 → Test independently → Deploy/Demo (Robustness)
5. Add User Story 4 → Test independently → Deploy/Demo (Final Report)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Core Analysis + Homogeneity Check)
   - Developer B: User Story 2 (Visualization)
   - Developer C: User Story 3 (Robustness)
3. Stories complete and integrate into User Story 4 (Report)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All analysis tasks MUST run on CPU-only CI (2 CPU, 7GB RAM). No GPU, no 8-bit quantization, no large LLMs. Use `statsmodels` and `scikit-learn` only.
- **Data Integrity**: Never fabricate data. If OSF dataset is missing required columns, the pipeline MUST abort with the specified error message. If N < 92, the pipeline MUST NOT abort but must warn and continue.
- **Ordering**: Task T039 (Homogeneity Check) MUST run after T017 (Model Fitting) but before T035 (Report Generation) to ensure the report contains accurate bias flags.