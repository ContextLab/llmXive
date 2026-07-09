# Tasks: Statistical Analysis of Publicly Available Stack Overflow Question Tags

**Input**: Design documents from `/specs/001-stat-so-tag-trends/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [ ] T001a Create `projects/PROJ-298-statistical-analysis-of-publicly-availab/` root directory
- [ ] T001b Create `projects/PROJ-298-statistical-analysis-of-publicly-availab/code/` directory
- [ ] T001c Create `projects/PROJ-298-statistical-analysis-of-publicly-availab/tests/` directory
- [ ] T001d Create `projects/PROJ-298-statistical-analysis-of-publicly-availab/data/` directory
- [ ] T001e Create `projects/PROJ-298-statistical-analysis-of-publicly-availab/notebooks/` directory
- [ ] T002 Initialize Python 3.11 project with `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `nbformat` in `projects/PROJ-298-statistical-analysis-of-publicly-availab/code/requirements.txt`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `projects/PROJ-298-statistical-analysis-of-publicly-availab/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils/hygiene.py` for SHA-256 hashing and state file updates per FR-012
- [ ] T005 [P] Create `code/utils/contract_validation.py` to enforce schema contracts in `contracts/` per Constitution Principle V
- [ ] T006 [P] Create `code/viz/templates.py` to inject mandatory limitation headers/footers per FR-011
- [ ] T007 [P] Create `code/data/generate_taxonomies.py` to generate `data/events/reference_calendar.json` and `data/taxonomy/survey_2023.json` per FR-008, validating taxonomy structure against SO Survey 2023 source
- [ ] T008 [P] Setup `data/` directory structure: `raw/`, `processed/`, `events/`, `taxonomy/` per `plan.md`, creating `data/events/reference_calendar.json` and `data/taxonomy/survey_2023.json`
- [ ] T009 [P] Initialize `state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml` with initial checksums, calculating hashes for initial artifacts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Quantify Technology Growth and Decline Trajectories (Priority: P1) 🎯 MVP

**Goal**: Identify statistically significant growth/decline trends in top-ranked tags using Modified Mann-Kendall test with external validation.

**Independent Test**: Verify output contains tags with p < 0.05 classified correctly, Theil-Sen slopes calculated, and correlation coefficients reported against GitHub/NPM metrics.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for trend output schema in `tests/contract/test_trend_results.py`, validating Growth/Decline/Stable/Insufficient Data classifications
- [ ] T011 [P] [US1] Integration test for Mann-Kendall pipeline end-to-end in `tests/integration/test_trend_pipeline.py`, validating pre-whitening step

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download.py` to fetch `PostsTags` from Stack Overflow dump (canonical URL: `TODO: Replace with canonical URL`) or HuggingFace fallback (`https://huggingface.co/datasets/stack-exchange/stackoverflow-tags`), extracting tag names and post creation dates, ensuring CPU-only streaming per plan.md constraints
- [ ] T013 [US1] **requires T012** Implement `code/data/preprocess.py` to aggregate frequencies into monthly bins (over the multi-year study period), normalize tag strings to lowercase and trimmed whitespace, and filter for ≥12 months data per FR-003
- [ ] T014 [US1] **requires T013** Implement `code/analysis/trends.py` with Modified Mann-Kendall (pre-whitening), Theil-Sen slope, Benjamini-Hochberg correction (per plan.md decision), and post-hoc power analysis (MDES). MUST implement classification logic: if p >= 0.05 AND power < 0.8, classify as "Insufficient Data" (report MDES if power < 0.8); if p >= 0.05 AND power >= 0.8, classify as "Stable". Output schema MUST include "Insufficient Data" category per FR-003, FR-013.
- [ ] T015 [US1] **requires T014, T039** Implement `code/analysis/correlation.py` to map tags to GitHub repos via Search API (topic) and NPM via Search API (keyword), log tag as 'unmapped' if no match found after limited attempts per FR-007, and compute Pearson correlation coefficient using data from T039, storing results in trend_results.json.
- [ ] T039 [US1] **requires T015** Implement `code/data/external.py` to fetch actual GitHub star counts and NPM download numbers for mapped tags per FR-007.
- [ ] T040 [US1] **requires T039, T014** Implement correlation calculation logic in `code/analysis/correlation.py` to compute correlation coefficients between trend slopes and external metrics, storing results for T018.
- [ ] T016 [US1] **requires T014** Implement bootstrapping logic to calculate 95% confidence intervals for Theil-Sen trend slopes and write results to `data/processed/confidence_interval.json` per FR-010.
- [ ] T017 [US1] Create `notebooks/02_trend_analysis.ipynb` integrating all US1 logic, visualizations, and mandatory limitation disclosure headers/footers per FR-006, FR-011
- [ ] T018 [US1] **requires T016, T040** Generate `data/processed/trend_results.json` (aggregating trend, CI, and correlation data), calculate SHA-256 hashes for trend_results.json and confidence_interval.json, and update state file per FR-012.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Visualize Time Series Decomposition and Seasonality (Priority: P2)

**Goal**: Decompose tag frequency series to identify seasonal patterns and validate against industry events.

**Independent Test**: Verify plots show Observed/Trend/Seasonal/Residual components, Ljung-Box test results, and Rayleigh test alignment with reference calendar.

### Tests for User Story 2

- [ ] T019 [P] [US2] Contract test for decomposition output schema in `tests/contract/test_decomposition_results.py`, validating Ljung-Box result
- [ ] T020 [P] [US2] Integration test for STL/Hodrick-Prescott pipeline in `tests/integration/test_decomposition_pipeline.py`, validating ADF and seasonality pre-tests

### Implementation for User Story 2

- [ ] T021 [US2] **requires T013, T041** Implement `code/analysis/decomposition.py` with mandatory pre-condition: perform Augmented Dickey-Fuller (ADF) test on *each* time series BEFORE decomposition. If non-stationary (p < 0.05), apply first-order differencing. Then apply STL (if seasonal) or Hodrick-Prescott (if non-seasonal) to the differenced series per FR-004, FR-009.
- [ ] T041 [US2] **requires T013** Implement seasonality pre-test (spectral analysis or autocorrelation check) in `code/analysis/decomposition.py`, outputting a boolean for method selection per FR-009.
- [ ] T022 [US2] **requires T021** Implement residual independence check (Ljung-Box lag=12) and event alignment (Rayleigh test) in `code/analysis/decomposition.py`, reporting results per FR-009, SC-003.
- [ ] T023 [US2] **requires T022** Implement `code/viz/plots.py` to generate multi-panel decomposition plots with confidence intervals, using `code/viz/templates.py` to inject limitation headers per FR-011
- [ ] T024 [US2] Create `notebooks/03_decomposition.ipynb` demonstrating decomposition on specific tags (e.g., "react"), including all code and final visualization outputs per FR-006
- [ ] T025 [US2] Generate `data/processed/decomposition_results.json` including Ljung-Box and Rayleigh test results, calculate SHA-256 hashes for decomposition_results.json, and update state file per FR-012.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cluster Technologies via Co-occurrence Analysis (Priority: P3)

**Goal**: Identify clusters of related technologies based on tag co-occurrence and validate against SO Survey taxonomy.

**Independent Test**: Verify Jaccard matrix, hierarchical clustering, permutation test coherence (p < 0.05), and Cluster Label Alignment Score ≥ 0.8.

### Tests for User Story 3

- [ ] T026 [P] [US3] Contract test for cluster output schema in `tests/contract/test_cluster_results.py`, validating Jaccard similarity, hierarchical clustering results, AND **permutation test results** for cluster coherence per FR-005
- [ ] T027 [P] [US3] Integration test for clustering pipeline in `tests/integration/test_clustering_pipeline.py`, validating Jaccard and hierarchical clustering

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `code/analysis/clustering.py` to compute Jaccard similarity matrix for all pairs of tags appearing on the same posts per FR-005
- [ ] T029 [US3] **requires T028** Implement hierarchical clustering and permutation test for cluster coherence validation in `code/analysis/clustering.py` per FR-005
- [ ] T030 [US3] **requires T029** Implement `code/analysis/clustering.py` logic for Cluster Label Alignment Score using fuzzy matching (Levenshtein distance ≤ 2) against `data/taxonomy/survey_2023.json` per FR-008, SC-004
- [ ] T031 [US3] Create `notebooks/04_clustering.ipynb` visualizing dendrograms and cluster maps, including all code and final visualization outputs per FR-006
- [ ] T032 [US3] Generate `data/processed/cluster_results.json` including Cluster Label Alignment Score and intra-cluster similarity coefficient, calculate SHA-256 hashes for cluster_results.json, and update state file per FR-012.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `projects/PROJ-298-statistical-analysis-of-publicly-availab/README.md` and `quickstart.md`, ensuring notebooks are reproducible
- [ ] T034 Code cleanup and refactoring across `code/analysis/` modules, including linting checks
- [ ] T035 Performance optimization for streaming large data dumps to fit RAM constraint, ensuring notebooks are reproducible
- [ ] T036 [P] Additional unit tests for statistical functions (Mann-Kendall, Jaccard, ADF) in `tests/unit/`, ensuring notebooks are reproducible
- [ ] T037 Run `quickstart.md` validation to ensure all tasks execute successfully on CPU-only runner within 6 hours, ensuring notebooks are reproducible
- [ ] T038 Final verification of all limitation disclosures (FR-011) in all generated reports and visualizations

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data download/preprocessing before analysis
- Analysis before visualization
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Data download (T012) and Taxonomy generation (T007) can run in parallel as they do not depend on each other
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for trend output schema in tests/contract/test_trend_results.py"
Task: "Integration test for Mann-Kendall pipeline end-to-end in tests/integration/test_trend_pipeline.py"

# Launch data tasks for User Story 1 together:
Task: "Implement code/data/download.py to fetch PostsTags..."
Task: "Implement code/data/preprocess.py to aggregate frequencies..."
# Note: T014 (trends) requires T013 (preprocess) to complete first.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T012 -> T013 -> T014 -> T016 -> T018)
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
   - Developer A: User Story 1 (T012, T013, T014, T015, T039, T040, T016, T018)
   - Developer B: User Story 2 (T021, T041, T022, T023, T025)
   - Developer C: User Story 3 (T028, T029, T030, T032)
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
- **Critical Constraint**: All tasks must run on CPU-only GitHub Actions runners (limited core count, GB RAM, 6h limit). No GPU, no 8-bit quantization, no large model training.
- **Dependency Syntax**: Tasks marked with `requires T###` must wait for the completion of the specified task ID before execution.