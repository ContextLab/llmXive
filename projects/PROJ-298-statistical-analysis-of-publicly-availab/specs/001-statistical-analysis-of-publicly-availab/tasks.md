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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create `projects/PROJ-298-statistical-analysis-of-publicly-availab/` root directory and all subdirectories (`code/`, `tests/`, `data/`, `notebooks/`, `state/`, `data/raw/`, `data/processed/`, `data/events/`, `data/taxonomy/`) in a single operation, verifying existence of all paths. <!-- ATOMIZED: Merged T001a-e -->
- [X] T002 [P] Initialize Python project with `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `nbformat`, `psutil`, `datasets` in `projects/PROJ-298-statistical-analysis-of-publicly-availab/code/requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `projects/PROJ-298-statistical-analysis-of-publicly-availab/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/hygiene.py` for SHA-256 hashing and state file updates per FR-012
- [X] T005 [P] Create `code/utils/contract_validation.py` to enforce schema contracts in `contracts/` per Constitution Principle V
- [X] T006 [P] Create `code/viz/templates.py` to inject mandatory limitation headers/footers per FR-011
- [X] T008 [P] **Directory Verification Only**: Verify the directory structure `data/`, `data/raw/`, `data/processed/`, `data/events/`, `data/taxonomy/` exists as created by T001. This task MUST NOT create directories (T001 does that) and MUST NOT write any JSON files; it only ensures the directories exist for T007 and downstream tasks. (See Plan.md structure)
- [X] T007 **requires T008**
 1. **Taxonomy Source**: Download the Stack Overflow Developer Survey 2023 Tech Stack data from the verified HuggingFace dataset `stack-exchange/stackoverflow-survey` (specifically the `tech_stack` split or JSON file if available, otherwise the raw CSV if the JSON is not present in that specific dataset ID, falling back to the verified URL ` ONLY if the HF dataset is missing the specific `tech_stack` key).
 2. **Calendar Source**: Download official release logs and event dates from the verified URL ` (or a verified canonical source like ` if the raw file is unavailable, but prioritize the static JSON).
 3. **Output**: Generate `data/taxonomy/survey_2023.json` with schema: `{"categories": [{"name": "string", "tags": ["string"]}]}` and `data/events/reference_calendar.json` with schema: `{"events": [{"name": "string", "date": "YYYY-MM-DD", "type": "release|conference"}]}`.
 4. **Validation**: Ensure both files are non-empty and valid JSON before marking complete. (See FR-008, FR-009, SC-003)
- [X] T009 [P] Initialize `state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml` with initial checksums, calculating hashes for initial artifacts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Quantify Technology Growth and Decline Trajectories (Priority: P1) 🎯 MVP

**Goal**: Identify statistically significant growth/decline trends in top-ranked tags using Modified Mann-Kendall test with external validation.

**Independent Test**: Verify output contains tags with p < 0.05 classified correctly, Theil-Sen slopes calculated, and correlation coefficients reported against GitHub/NPM metrics with magnitude interpretation.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for trend output schema in `tests/contract/test_trend_results.py`, validating Growth/Decline/Stable/Insufficient Data classifications
- [X] T011 [P] [US1] Integration test for Mann-Kendall pipeline end-to-end in `tests/integration/test_trend_pipeline.py`, validating pre-whitening step

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data/download.py` to fetch `PostsTags` from Stack Overflow dump (canonical URL: `) or HuggingFace fallback (`https://huggingface.co/datasets/stack-exchange/stackoverflow-tags`), extracting tag names and post creation dates, ensuring CPU-only streaming per plan.md constraints
- [X] T013 [US1] **requires T012** Implement `code/data/preprocess.py` to aggregate frequencies into monthly bins (over the multi-year study period), normalize tag strings to lowercase and trimmed whitespace, and filter for ≥12 months data per FR-003. **MUST** output the list of "Top 50 Tags" (by total frequency) to `data/processed/top_50_tags.json`.
- [X] T014 [US1] **requires T013** Implement `code/analysis/trends.py` with Modified Mann-Kendall (pre-whitening), Theil-Sen slope, Benjamini-Hochberg correction (per plan.md decision), and post-hoc power analysis (MDES + Power Estimate).
 - **MUST** explicitly verify and log the application of Benjamini-Hochberg correction to raw p-values.
 - **MUST** calculate MDES via Monte Carlo (1000 iterations, random seed 42) by injecting linear trends of varying slopes into the pre-whitened residuals of the top 50 tags to determine the slope magnitude detectable at 80% power with alpha=0.05.
 - **MUST** estimate variance from the pre-whitened residuals of the top 50 tags.
 - **MUST** implement classification logic: if p >= 0.05 AND power < 0.8, classify as "Insufficient Data" (report MDES); if p >= 0.05 AND power >= 0.8, classify as "Stable". **CRITICAL**: The threshold of 0.05 MUST be applied to the *adjusted* p-values (q-values) resulting from the Benjamini-Hochberg correction, not the raw p-values.
 - **MUST** output intermediate results to `data/processed/trend_intermediate.json`. (See FR-003, FR-013)
- [X] T039 [US1] **requires T013** Implement `code/data/external.py` to fetch actual GitHub star counts and NPM download numbers for the **Top 50 Tags** (from `data/processed/top_50_tags.json`) per FR-007.
 - **MUST** attempt mapping via GitHub Search API (topic) and NPM Search API (keyword) for each of the Top 50 tags to identify candidate repos/packages.
 - **MUST** write the fetched raw metrics and candidate matches to `data/processed/external_metrics.json` conforming to `contracts/external_metrics.schema.yaml`.
 - **MUST** log any API failures to `data/processed/external_fetch_errors.log`.
 - **MUST NOT** perform final tag-to-repo mapping logic or write to `unmapped_tags.log`; this task only fetches raw data and candidates. (See FR-007)
- [X] T015 [US1] **requires T039** Implement tag-to-repo mapping logic in `code/analysis/mapping.py` to map tags to GitHub repos/NPM packages using the raw data fetched by T039 (reading `data/processed/external_metrics.json`).
 - **MUST** first verify that `data/processed/external_metrics.json` exists and is non-empty. If the file is missing or empty (indicating T039 failed), the task MUST log a critical error and exit without proceeding.
 - **MUST** read the schema from `contracts/external_metrics.schema.yaml` to parse the input correctly.
 - **MUST** output the final mapping list to `data/processed/tag_mappings.json`.
 - **MUST** be the sole writer of `data/processed/tag_mappings.json`.
 - **MUST** generate `data/processed/unmapped_tags.log` (newline-delimited JSON) if unmapped tags are identified during the mapping process, ensuring FR-007 is satisfied.
 - **MUST NOT** perform correlation calculation; only mapping. (See FR-007)
- [X] T040 [US1] **requires T014, T015** Implement correlation calculation logic in `code/analysis/correlation.py` to compute Pearson correlation coefficients between trend slopes (from T014) and external metrics (from T039, mapped by T015).
 - **MUST** read `data/processed/tag_mappings.json` produced by T015.
 - **MUST** read `data/processed/unmapped_tags.log` produced by T015 to identify tags to skip.
 - **MUST** interpret the magnitude of the correlation coefficient using FR-007 thresholds: |r| ≥ 0.7 -> "Strong", 0.3 ≤ |r| < 0.7 -> "Moderate", |r| < 0.3 -> "Weak".
 - **MUST** write the final results, including the interpreted magnitude string, to `data/processed/correlation_results.json`. (See FR-007)
- [X] T016 [US1] **requires T014** Implement bootstrapping logic to calculate confidence intervals for Theil-Sen trend slopes (1000 iterations) using **block bootstrap** (block length = 12 months) to preserve temporal autocorrelation.
 - **MUST** cite Plan.md decision for using block length of 12 months to preserve annual seasonality patterns in the time series.
 - **MUST** handle short series: If a tag has < 24 months of data, reduce block size to `floor(series_length / 2)` or skip bootstrapping for that tag and report "Insufficient Data for CI".
 - **MUST** write results to `data/processed/confidence_interval.json` per FR-010.
 - **MUST** verify the file `data/processed/confidence_interval.json` exists and contains valid 95% CI bounds before marking complete. (See FR-010)
- [X] T017 [US1] Create `notebooks/02_trend_analysis.ipynb` integrating all US1 logic, visualizations, and mandatory limitation disclosure headers/footers per FR-006, FR-011
- [X] T018 [US1] **requires T014, T016, T040** Aggregate and finalize `data/processed/trend_results.json`.
 - **MUST** verify the existence of all upstream artifacts (T014, T016, T040 outputs) before proceeding.
 - **MUST** merge data from `trend_intermediate.json`, `confidence_interval.json`, and `correlation_results.json`.
 - **MUST** write the final aggregated JSON to `data/processed/trend_results.json`.
 - **MUST** calculate SHA-256 hashes for `trend_results.json` and `confidence_interval.json` and update the state file per FR-012. (See FR-012)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Visualize Time Series Decomposition and Seasonality (Priority: P2)

**Goal**: Decompose tag frequency series to identify seasonal patterns and validate against industry events.

**Independent Test**: Verify plots show Observed/Trend/Seasonal/Residual components, Ljung-Box test results, and Rayleigh test alignment with reference calendar.

### Tests for User Story 2

- [X] T019 [P] [US2] Contract test for decomposition output schema in `tests/contract/test_decomposition_results.py`, validating Ljung-Box result
- [X] T020 [P] [US2] Integration test for STL/Hodrick-Prescott pipeline in `tests/integration/test_decomposition_pipeline.py`, validating ADF and seasonality pre-tests

### Implementation for User Story 2

- [X] T041 [US2] **requires T013** Implement seasonality pre-test (spectral analysis or autocorrelation check) in `code/analysis/decomposition.py`, outputting a boolean for method selection per FR-009.
- [X] T021 [US2] **requires T013, T041** Implement `code/analysis/decomposition.py` with mandatory pre-condition: perform Augmented Dickey-Fuller (ADF) test on *each* time series BEFORE decomposition.
 - **MUST** consume the seasonality boolean from T041 to decide between STL (if seasonal) or Hodrick-Prescott (if non-seasonal) on the differenced series per FR-004, FR-009.
- [X] T022 [US2] **requires T021** Implement residual independence check (Ljung-Box lag=12) and event alignment (Rayleigh test) in `code/analysis/decomposition.py`, reporting results to `data/processed/decomposition_intermediate.json` per FR-009, SC-003.
- [X] T023 [US2] **requires T022** Implement `code/viz/plots.py` to generate multi-panel decomposition plots with confidence intervals, using `code/viz/templates.py` to inject limitation headers per FR-011
- [X] T024 [US2] Create `notebooks/03_decomposition.ipynb` demonstrating decomposition on specific tags (e.g., "react"), including all code and final visualization outputs per FR-006
- [X] T025 [US2] **requires T022** Generate `data/processed/decomposition_results.json`.
 - **MUST** read the Ljung-Box and Rayleigh test results from `data/processed/decomposition_intermediate.json` (produced by T022).
 - **MUST** write the final aggregated JSON including these results to `data/processed/decomposition_results.json`.
 - **MUST** calculate SHA-256 hashes for `decomposition_results.json` and update state file per FR-012. (See FR-012)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cluster Technologies via Co-occurrence Analysis (Priority: P3)

**Goal**: Identify clusters of related technologies based on tag co-occurrence and validate against SO Survey taxonomy.

**Independent Test**: Verify Jaccard matrix, hierarchical clustering, permutation test coherence (p < 0.05), and Cluster Label Alignment Score ≥ 0.8.

### Tests for User Story 3

- [X] T026 [P] [US3] Contract test for cluster output schema in `tests/contract/test_cluster_results.py`, validating Jaccard similarity, hierarchical clustering results, AND **permutation test results** for cluster coherence per FR-005
- [X] T027 [P] [US3] Integration test for clustering pipeline in `tests/integration/test_clustering_pipeline.py`, validating Jaccard and hierarchical clustering

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement `code/analysis/clustering.py` to compute Jaccard similarity matrix for all pairs of tags appearing on the same posts per FR-005
- [X] T029 [US3] **requires T028** Implement hierarchical clustering and permutation test for cluster coherence validation in `code/analysis/clustering.py` per FR-005.
 - **MUST** run 1000 iterations for the permutation test and report p < 0.05 significance.
- [X] T030 [US3] **requires T029, T007** Implement `code/analysis/clustering.py` logic for Cluster Label Alignment Score using fuzzy matching (Levenshtein distance ≤ 2) against `data/taxonomy/survey_2023.json` (generated by T007) per FR-008, SC-004.
 - **MUST** calculate Cluster Label Alignment Score and verify it is ≥ 0.8. This threshold is derived from Spec US-3 acceptance criteria.
 - **MUST** use Levenshtein distance ≤ 2 for fuzzy matching, as derived from Plan.md complexity tracking for aligning tags to "Tech Stack" categories.
 - **MUST** write the score and intra-cluster similarity to `data/processed/cluster_alignment.json`.
- [X] T031 [US3] Create `notebooks/04_clustering.ipynb` visualizing dendrograms and cluster maps, including all code and final visualization outputs per FR-006
- [X] T032 [US3] **requires T030** Generate `data/processed/cluster_results.json`.
 - **MUST** read the Cluster Label Alignment Score and intra-cluster similarity coefficient from the output of T030.
 - **MUST** write the final aggregated JSON including these metrics to `data/processed/cluster_results.json`.
 - **MUST** calculate SHA-256 hashes for `cluster_results.json` and update state file per FR-012. (See FR-012)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates in `projects/PROJ-298-statistical-analysis-of-publicly-availab/README.md` and `quickstart.md`, ensuring notebooks are reproducible. **MUST** generate `quickstart.md` with step-by-step instructions to reproduce all results.
- [X] T034 [P] Code cleanup and refactoring across `code/analysis/` modules, including linting checks. **MUST** ensure all functions have docstrings and type hints.
- [X] T035 [P] Performance optimization for streaming large data dumps to fit RAM constraint, ensuring notebooks are reproducible. **MUST** implement streaming using `datasets.load_dataset(..., streaming=True)` with a **chunk size of 10000 rows** and a **memory trigger threshold of 6.0GB** (measured via `psutil`). **MUST** verify memory usage stays below 7GB; if usage exceeds 6.0GB, reduce chunk size to 5000 rows and re-run the current chunk processing. (See SC-005, Plan.md)
- [X] T036 [P] Additional unit tests for statistical functions (Mann-Kendall, Jaccard, ADF) in `tests/unit/`, ensuring notebooks are reproducible
- [X] T037a [P] **Atomized**: Install dependencies and set up virtual environment for validation run.
- [X] T037b [P] **Atomized**: Execute `quickstart.md` scripts on CPU-only runner. **MUST** record total execution time to verify SC-005 (<=6 hours). **MUST** write the execution time to `state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml` under the key `execution_time_seconds` and also log it to `data/processed/timing.log`.
- [X] T037c [P] **Atomized**: Verify all outputs exist and pass basic schema checks within 6 hours.
- [X] T038 [P] Final verification of all limitation disclosures (FR-011) in all generated reports and visualizations. **MUST** scan all generated files for the mandatory header/footer and fail if missing.

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
- Data download (T012) and Taxonomy generation (T007) can run in parallel **ONLY AFTER** T008 completes.
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
- **Critical Constraint**: All tasks must run on CPU-only GitHub Actions runners (limited core count, GB RAM, 6h limit). No GPU, no low-bit quantization, no large model training.
- **Dependency Syntax**: Tasks marked with `requires T###` must wait for the completion of the specified task ID before execution.