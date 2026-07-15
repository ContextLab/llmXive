# Tasks: The Influence of Visual Complexity on Implicit Bias

**Input**: Design documents from `/specs/001-the-influence-of-visual-complexity-on-im/`
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

- [X] T001 Create project structure per implementation plan. Exact tree: `code/`, `data/raw/stimuli`, `data/raw/responses`, `data/processed`, `data/results`, `tests/`.
- [X] T002 Initialize Python 3.11 project with `code/requirements.txt`. Exact content: `numpy>=1.24.0`, `pandas>=2.0.0`, `scipy>=1.11.0`, `scikit-learn>=1.3.0`, `pillow>=10.0.0`, `opencv-python-headless>=4.8.0`, `matplotlib>=3.7.0`, `seaborn>=0.12.0`, `statsmodels>=0.14.0`, `pytest>=7.4.0`.
- [X] T003 [P] Configure pytest, linting (ruff/flake8), and formatting (black) tools. Create `pyproject.toml` with `[tool.black] line-length=88`, `.ruff.toml`, and `.black` config files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` to manage paths, random seeds, and constants
- [X] T005 [P] Implement `code/__init__.py` and package structure for `data`, `stimuli`, `analysis`, `viz`
- [X] T006 Setup directory structure for `data/raw/stimuli`, `data/raw/responses`, `data/processed`, `data/results`
- [X] T007 Create base data models/entities in `code/data/models.py`. Fields: `ImageStimulus` (path, edge_density, entropy, fractal_dim), `ParticipantResponse` (participant_id, session_id, reaction_time, is_correct, timestamp), `AggregatedScore` (participant_id, session_id, d_score, n_trials_valid, status). Implement as Pydantic BaseModel classes.
- [X] T008 Configure logging infrastructure in `code/utils/logging.py`
- [ ] T033a [P] [US3] Document the methodological shift from ANOVA to Permutation Test in `research.md`, including justification and citation of the plan's decision. This task must be completed before T033 to ensure implementation aligns with the chosen statistical method.
- [ ] T027a [P] [US2] Generate `data/processed/counterbalance_assignment.csv` mapping participant IDs to session orders (Low-High vs High-Low) using a seeded random shuffle (seed=42) to ensure a 50/50 split for each starting condition. This task generates a synthetic assignment map for CI/testing and does not depend on raw logs.
- [ ] T027b [US2] Log the specific counterbalancing assignment strategy used in `logs/counterbalance_strategy.log`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Stimulus Complexity Quantification (Priority: P1) 🎯 MVP

**Goal**: Compute objective visual complexity metrics (edge density, entropy, fractal dimension) for background images and categorize them.

**Independent Test**: Run the script on a solid color image and a noise image; verify noise scores are strictly higher.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for edge density calculation in `tests/test_stimuli/test_metrics.py`
- [ ] T010 [P] [US1] Unit test for entropy calculation in `tests/test_stimuli/test_metrics.py`
- [ ] T011 [P] [US1] Unit test for fractal dimension (box-counting) in `tests/test_stimuli/test_metrics.py`
- [~] T012 [P] [US1] Integration test for full pipeline on sample images in `tests/test_stimuli/test_pipeline.py`

### Implementation for User Story 1

- [~] T013 [P] [US1] Implement edge density (Canny) in `code/stimuli/metrics.py`
- [~] T014 [P] [US1] Implement entropy of grayscale histograms in `code/stimuli/metrics.py`
- [~] T015 [P] [US1] Implement fractal dimension via box-counting in `code/stimuli/metrics.py` (handle edge cases: clamp value to a bounded range or raise ValueError if out of bounds).
- [~] T016 [US1] Implement image validation and error handling in `code/stimuli/validate.py`. Validates *input images* for corruption before batch processing in T017. Skips corrupted files, logs filenames. Depends on T013-T015.
- [~] T017 [US1] Create `code/stimuli/process.py` to batch-process `data/raw/stimuli/` and output `data/processed/complexity_scores.csv`. Output schema: `filename, edge_density, entropy, fractal_dim, complexity_category`.
- [~] T018 [US1] Add logic to categorize images into Low/Medium/High complexity based on computed scores (use pandas.qcut with a specified number of bins).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Experimental Data Collection and D-Score Aggregation (Priority: P2)

**Goal**: Aggregate raw IAT response times into valid D-scores per session using Greenwald D2 algorithm.

**Independent Test**: Simulate two IAT sessions for a synthetic participant; verify D-scores match expected values within tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T019 [P] [US2] Unit test for D-score calculation (Greenwald D2) in `tests/test_data/test_process.py`
- [~] T020 [P] [US2] Unit test for trial filtering (latency <300ms, >10000ms, errors) in `tests/test_data/test_process.py`
- [~] T021 [P] [US2] Integration test for participant exclusion (<10 valid trials) in `tests/test_data/test_process.py`

### Implementation for User Story 2

- [~] T022 [P] [US2] Implement trial filtering logic (latency bounds, error handling) in `code/data/process.py`
- [~] T023 [P] [US2] Implement Greenwald D2 algorithm for D-score aggregation in `code/data/process.py`
- [~] T024 [US2] Implement logic to exclude participants with insufficient valid trials (<10) and flag as `NaN`
- [~] T025 [US2] Create `code/data/load.py` to load raw response logs (support synthetic `--null-effect` mode for CI)
- [~] T026 [US2] Create `code/data/process.py` to aggregate raw logs into `data/processed/aggregated_d_scores.csv`. Input: raw logs. Output schema: `participant_id, session_id, d_score, n_trials_valid, status`. Dependency: Requires T022 and T023.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**Goal**: Perform Permutation Test (with LOIO sensitivity) and generate publication-quality plots.

**Independent Test**: Run analysis on pre-generated dataset; verify p-value, effect size, and plots match expected values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T028 [P] [US3] Unit test for Permutation Test logic in `tests/test_analysis/test_permutation.py`
- [~] T029 [P] [US3] Unit test for Sensitivity Analysis (threshold sweep) in `tests/test_analysis/test_permutation.py`
- [~] T030 [P] [US3] Unit test for Leave-One-Image-Out (LOIO) logic in `tests/test_analysis/test_permutation.py`
- [~] T031 [P] [US3] Integration test for full analysis pipeline in `tests/test_analysis/test_pipeline.py`

### Implementation for User Story 3

- [~] T032 [P] [US3] Implement PCA dimensionality check in `code/analysis/pca.py` (verify metric construct validity)
- [~] T033 [US3] Implement Permutation Test in `code/analysis/permutation.py`. Parameters: A sufficient number of permutations to ensure stable p-value estimation, seed 42, metric = mean difference of D-scores. Note: This task implements FR-003 (amended).
- [~] T034 [US3] Calculate effect sizes: Report 'Permutation Effect Size' (Cohen's d) and 'Permutation p-value'. Explicitly note that 'partial η²' is not applicable; this satisfies FR-004 intent with the correct metric for the chosen test.
- [~] T034a [US3] Implement post-hoc power calculation in `code/analysis/permutation.py`. Parameters: Cohen's d = 0.5, alpha = 0.05, sample size = N. Use `statsmodels.stats.power.TTestIndPower`. Output: `data/results/power_analysis.json` with `power_value`, `target (a high value), `status` (pass/fail). Depends on T033, T034.
- [~] T035a [US3] Implement Sensitivity Analysis: Threshold sweep (±0.05, ±0.10, ±0.15 SD of the complexity metric distribution) AND LOIO in `code/analysis/permutation.py`. Logic: Exclude sweep points where n < 15 per condition.
- [~] T035b [US3] Generate LOIO sensitivity plot in `code/viz/plot.py`.
- [~] T036 [US3] Save results to `data/results/permutation_results.json` and `data/results/sensitivity_results.json`. Dependency: Requires T033, T034, T035a, and T035b.
- [~] T037 [US3] Implement publication-quality plotting (Seaborn boxplot, Standard confidence interval error bars, The text will be formatted using a standard, readable font size., viridis palette) in `code/viz/plot.py`.
- [~] T038 [US3] Create `code/main.py` to orchestrate the full pipeline (Load -> Process -> Analyze -> Plot).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T039 [P] Documentation updates in `docs/` (README, usage examples)
- [~] T040 Code cleanup and refactoring (remove debug prints, ensure type hints)
- [~] T043a Add CI workflow file (.github/workflows/analysis.yml) to run pipeline and assert duration < 6h.
- [ ] T043b Vectorize image processing loops if execution time exceeds target.
- [ ] T044 [P] Additional unit tests for edge cases (corrupted images, missing data) in `tests/`
- [ ] T045 Run `quickstart.md` validation to ensure reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on outputs from US1 (complexity scores) and US2 (D-scores)

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
Task: "Unit test for edge density calculation in tests/test_stimuli/test_metrics.py"
Task: "Unit test for entropy calculation in tests/test_stimuli/test_metrics.py"
Task: "Unit test for fractal dimension in tests/test_stimuli/test_metrics.py"

# Launch all implementation tasks for User Story 1 together:
Task: "Implement edge density in code/stimuli/metrics.py"
Task: "Implement entropy in code/stimuli/metrics.py"
Task: "Implement fractal dimension in code/stimuli/metrics.py"
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
 - Developer A: User Story 1 (Stimuli)
 - Developer B: User Story 2 (Data Processing)
 - Developer C: User Story 3 (Analysis)
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
- **Critical Constraint**: All image processing and statistical tasks must run on CPU-only free-tier runners (limited cores, constrained RAM). No GPU, no 8-bit/4-bit quantization, no large models.
- **Data Integrity**: Do not fabricate input data. Use real datasets or the `--null-effect` synthetic mode strictly for CI testing. Production analysis requires real, pre-manipulated stimuli.
- **Methodological Note**: The Permutation Test (T033) is implemented to handle stimulus-set confounds, replacing the ANOVA requirement in FR-003 as documented in `research.md` (T033a).