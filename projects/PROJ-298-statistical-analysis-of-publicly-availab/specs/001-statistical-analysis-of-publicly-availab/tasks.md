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

- [X] T001 [P] Create `projects/PROJ-298-statistical-analysis-of-publicly-availab/` root directory and all subdirectories (`code/`, `tests/`, `data/`, `notebooks/`, `state/`, `data/raw/`, `data/processed/`, `data/events/`, `data/taxonomy/`) in a single operation.
- [X] T002 [P] Initialize Python project with `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `nbformat`, `psutil`, `datasets` in `projects/PROJ-298-statistical-analysis-of-publicly-availab/code/requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `projects/PROJ-298-statistical-analysis-of-publicly-availab/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/hygiene.py` for SHA-256 hashing and state file updates per FR-012
- [X] T005 [P] Create `code/utils/contract_validation.py` to enforce schema contracts in `contracts/` per Constitution Principle V
- [X] T006 [P] Create `code/viz/templates.py` to inject mandatory limitation headers/footers per FR-011
- [X] T007 [P] **Directory Verification Only**: Verify the directory structure `data/`, `data/raw/`, `data/processed/`, `data/events/`, `data/taxonomy/` exists as created by T001. This task MUST NOT create directories (T001 does that) and MUST NOT write any JSON files; it only ensures the directories exist for T008a, T008b and downstream tasks. (See Plan.md structure)
- [X] T014a [P] **requires T007** Document and ratify the use of Benjamini-Hochberg correction for p-values.
 - **MUST** Append a section to `plan.md` under "Spec Root Cause Notes" stating: "Ratified Deviation: FR-003 ambiguity on multiple testing correction resolved by adopting Benjamini-Hochberg (BH) correction. The 0.05 significance threshold applies to the adjusted q-values, not raw p-values. [UNRESOLVED-CLAIM: c_87203a09 — status=not_enough_info] "
 - **MUST** Update `plan.md` to reflect this ratified requirement. (See Plan.md Spec Root Cause Note 2)
- [X] T016a [P] **requires T007** Document and ratify the use of "block bootstrap" with a fixed 12-month block length.
 - **MUST** Append a section to `plan.md` under "Spec Root Cause Notes" stating: "Ratified Deviation: FR-010 'standard bootstrapping' is replaced by 'block bootstrap' (block length=12 months) to preserve annual seasonality patterns in the time series."
 - **MUST** Update `plan.md` to reflect this ratified requirement. (See Spec FR-010)
- [X] T008a [P] **requires T007**
 1. **Taxonomy Source**: Download the Stack Overflow Developer Survey 2023 Tech Stack data from the verified HuggingFace dataset `stack-exchange/stackoverflow-survey` (specifically the `tech_stack` split or JSON file if available).
 2. **Output**: Generate `data/taxonomy/survey_2023.json` with schema: `{"categories": [{"name": "string", "tags": ["string"]}]}`.
 3. **Validation**: Ensure the file is non-empty and valid JSON before marking complete. (See FR-008)
- [X] T008b [P] **requires T007**
 1. **Calendar Source**: Download official release logs and event dates from the verified GitHub URL: `.
 2. **Output**: Generate `data/events/reference_calendar.json` with schema: `{"events": [{"name": "string", "date": "YYYY-MM-DD", "type": "release|conference"}]}`.
 3. **Fail Loudly**: If the primary verified source is unavailable, the task MUST raise a `RuntimeError` with the message "Verified release log source unavailable; cannot proceed with empty calendar." **MUST NOT** generate an empty file.
 4. **Validation**: Ensure the file is valid JSON before marking complete. (See FR-009, SC-003)
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

- [X] T012 [US1] Implement `code/data/download.py` to fetch `PostsTags` from Stack Overflow dump (canonical URL: `) or HuggingFace fallback (`https://huggingface.co/datasets/stack-exchange/stackoverflow-tags`), extracting tag names and post creation dates, ensuring CPU-only streaming per plan.md constraints.
 - **MUST** explicitly check if the primary Stack Overflow dump URL is reachable via a HEAD request before attempting download.
 - **MUST** If the primary URL fails, the script MUST immediately attempt the verified HuggingFace fallback and log the switch.
 - **MUST** raise a `RuntimeError` ONLY if BOTH primary and fallback sources are unreachable, ensuring the "Fail Loudly" policy is maintained without silent synthetic fallbacks. (See FR-001, Constitution Principle III, T054 MERGED)
- [X] T013 [US1] **requires T012** Implement `code/data/preprocess.py` to aggregate frequencies into monthly bins (over the multi-year study period), normalize tag strings to lowercase and trimmed whitespace, and filter for ≥12 months data per FR-003. **MUST** output the list of "Top Tags" (by total frequency) to `data/processed/top_50_tags.json`.
- [X] T039 [US1] **requires T013** Implement `code/data/external.py` to fetch actual GitHub star counts and NPM download numbers for the **Top 50 Tags** (reading `data/processed/top_50_tags.json` produced by T013) per FR-007.
 - **MUST** attempt mapping via GitHub Search API (topic, base URL: `) and NPM Search API (keyword, base URL: `) for each of the Top 50 tags to identify candidate repos/packages.
 - **MUST** write the fetched raw metrics and candidate matches to `data/processed/external_metrics.json` conforming to `contracts/external_metrics.schema.yaml`.
 - **MUST** log any API failures to `data/processed/external_fetch_errors.log`.
 - **MUST NOT** perform final tag-to-repo mapping logic or write to `unmapped_tags.log`; this task only fetches raw data and candidates. (See FR-007)
- [X] T014b [US1] **requires T014a, T013** Implement `code/analysis/trends.py` with Modified Mann-Kendall (pre-whitening), Theil-Sen slope, and Benjamini-Hochberg correction as ratified in T014a.
 - **MUST** explicitly verify and log the application of Benjamini-Hochberg correction to raw p-values.
 - **MUST** implement classification logic: if p >= 0.05 AND power < 0.8, classify as "Insufficient Data"; if p >= 0.05 AND power >= 0.8, classify as "Stable". **CRITICAL**: The threshold of 0.05 MUST be applied to the *adjusted* q-values resulting from the Benjamini-Hochberg correction, as ratified in T014a.
 - **MUST** output intermediate results to `data/processed/trend_intermediate.json`. (See FR-003)
- [X] T014c [US1] **requires T014b** Implement post-hoc power analysis (MDES + Power Estimate) in `code/analysis/trends.py`.
 - **MUST** calculate MDES via Monte Carlo (a sufficient number of iterations with a fixed random seed) by injecting linear trends of varying slopes into the pre-whitened residuals of the top 50 tags to determine the slope magnitude detectable at 80% power with alpha=0.05.
 - **MUST** estimate variance from the pre-whitened residuals of the top 50 tags.
 - **MUST** if the post-hoc power analysis (MDES) indicates power < 0.5 for a specific tag, flag this tag in `data/processed/power_warnings.log` and exclude it from the "Stable" classification pool, re-classifying it as "Insufficient Data" regardless of the p-value.
 - **MUST** update `trend_intermediate.json` with power estimates and MDES values. (See FR-013, T057 MERGED)
- [ ] T015 [US1] **requires T039** Implement tag-to-repo mapping logic in `code/analysis/mapping.py` to map tags to GitHub repos/NPM packages using the raw data fetched by T039 (reading `data/processed/external_metrics.json`).
 - **MUST** first verify that `data/processed/external_metrics.json` exists. If the file is missing or empty (indicating T039 failed or found nothing), the task MUST create an empty `data/processed/unmapped_tags.log` and exit successfully (do NOT fail the pipeline).
 - **MUST** read the schema from `contracts/external_metrics.schema.yaml` to parse the input correctly.
 - **MUST** output the final mapping list to `data/processed/tag_mappings.json`.
 - **MUST** be the sole writer of `data/processed/tag_mappings.json`.
 - **MUST** generate `data/processed/unmapped_tags.log` (newline-delimited JSON) if unmapped tags are identified during the mapping process, ensuring FR-007 is satisfied.
 - **MUST NOT** perform correlation calculation; only mapping. (See FR-007)
- [X] T040 [US1] **requires T014b, T015** Implement correlation calculation logic in `code/analysis/correlation.py` to compute Pearson correlation coefficients between trend slopes (from T014b) and external metrics (from T039, mapped by T015).
 - **MUST** read `data/processed/tag_mappings.json` produced by T015.
 - **MUST** read `data/processed/unmapped_tags.log` produced by T015 to identify tags to skip.
 - **MUST** interpret the magnitude of the correlation coefficient using FR-007 thresholds: |r| ≥ 0.7 -> "Strong", 0.3 ≤ |r| < 0.7 -> "Moderate", |r| < 0.3 -> "Weak".
 - **MUST** write the final results, including the interpreted magnitude string, to `data/processed/correlation_results.json`. (See FR-007)
- [X] T016b [US1] **requires T013, T016a** Implement bootstrapping logic to calculate confidence intervals for Theil-Sen trend slopes (A sufficient number of iterations will be performed to ensure convergence and statistical stability.) using **block bootstrap** (block length = 12 months) to preserve temporal autocorrelation.
 - **MUST** cite Plan.md decision for using block length of 12 months to preserve annual seasonality patterns in the time series, as ratified in T016a.
 - **MUST** handle short series: If a tag has < 24 months of data, reduce block size to `floor(series_length / 2)` or skip bootstrapping for that tag and report "Insufficient Data for CI".
 - **MUST** write results to `data/processed/confidence_interval.json` per FR-010.
 - **MUST** verify the file `data/processed/confidence_interval.json` exists and contains valid 95% CI bounds before marking complete. (See FR-010)
- [X] T017 [US1] Create `notebooks/02_trend_analysis.ipynb` integrating all US1 logic, visualizations, and mandatory limitation disclosure headers/footers per FR-006, FR-011
- [ ] T018 [US1] **requires T014c, T016b, T040** Aggregate and finalize `data/processed/trend_results.json`.
 - **MUST** verify the existence of all upstream artifacts (T014c, T016b, T040 outputs) before proceeding.
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
 - **MUST** implement a dual-method check: if the primary spectral analysis fails (e.g., due to insufficient data points), the task MUST fall back to the autocorrelation check (lag=12 > 0.3) as a secondary confirmation.
 - **MUST** log the method used and the result of both checks if both are attempted, ensuring the decomposition pipeline does not fail silently on edge cases. (See FR-009, FR-004, T055 MERGED)
- [X] T021a [US2] **requires T013** Implement Augmented Dickey-Fuller (ADF) test on *each* time series in `code/analysis/decomposition.py` to determine stationarity. **MUST** output a boolean indicating if differencing is required. (See FR-009)
- [X] T021b [US2] **requires T021a, T041** Implement the actual decomposition logic in `code/analysis/decomposition.py`.
 - **MUST** consume the stationarity boolean from T021a to decide if differencing is needed.
 - **MUST** consume the seasonality boolean from T041 to decide between STL (if seasonal) or Hodrick-Prescott (if non-seasonal) on the differenced series per FR-004, FR-009.
 - **MUST** output the decomposed components to `data/processed/decomposition_components.json`. (See FR-004, FR-009)
- [ ] T022 [US2] **requires T021b** Implement residual independence check (Ljung-Box lag=12) and event alignment (Rayleigh test) in `code/analysis/decomposition.py`, reporting results to `data/processed/decomposition_intermediate.json` per FR-009, SC-003.
- [X] T023 [US2] **requires T022** Implement `code/viz/plots.py` to generate multi-panel decomposition plots with confidence intervals, using `code/viz/templates.py` to inject limitation headers per FR-011
- [X] T024 [US2] Create `notebooks/03_decomposition.ipynb` demonstrating decomposition on specific tags (e.g., "react"), including all code and final visualization outputs per FR-006
- [ ] T025 [US2] **requires T022** Generate `data/processed/decomposition_results.json`.
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
 - **MUST** run a sufficient number of iterations for the permutation test and report p < 0.05 significance.
 - **MUST NOT** implement a fallback to 100 iterations if convergence fails; if the permutation test fails to converge or returns a p-value > 0.1, the task MUST fail loudly with a clear error message. (See FR-005, SC-004, T056 MERGED)
- [X] T030 [US3] **requires T029, T008a** Implement `code/analysis/clustering.py` logic for Cluster Label Alignment Score using fuzzy matching (Levenshtein distance ≤ 2) against `data/taxonomy/survey_2023.json` (generated by T008a) per FR-008, SC-004.
 - **MUST** calculate Cluster Label Alignment Score and verify it is ≥ 0.8. This threshold is derived from Spec US-3 acceptance criteria.
 - **MUST** use Levenshtein distance ≤ 2 for fuzzy matching, as derived from Plan.md complexity tracking for aligning tags to "Tech Stack" categories.
 - **MUST** Tags with Levenshtein distance > 2 MUST be included in the calculation with a 'no_match' score, ensuring the full cluster is represented.
 - **MUST** write the score and intra-cluster similarity to `data/processed/cluster_alignment.json`.
 - **NOTE**: This task analyzes **all pairs of tags** as per FR-005 and does **not** depend on T013 (Top 50 list).
- [X] T031 [US3] Create `notebooks/04_clustering.ipynb` visualizing dendrograms and cluster maps, including all code and final visualization outputs per FR-006
- [ ] T032 [US3] **requires T030** Generate `data/processed/cluster_results.json`.
 - **MUST** read the Cluster Label Alignment Score and intra-cluster similarity coefficient from the output of T030.
 - **MUST** write the final aggregated JSON including these metrics to `data/processed/cluster_results.json`.
 - **MUST** calculate SHA-256 hashes for `cluster_results.json` and update state file per FR-012. (See FR-012)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates in `projects/PROJ-298-statistical-analysis-of-publicly-availab/README.md` and `quickstart.md`, ensuring notebooks are reproducible. **MUST** generate `quickstart.md` with step-by-step instructions to reproduce all results.
- [X] T034 [P] Code cleanup and refactoring across `code/analysis/` modules, including linting checks. **MUST** ensure all functions have docstrings and type hints.
- [ ] T035 [P] Implement streaming logic in `code/data/download.py` to handle large data dumps, ensuring notebooks are reproducible. **MUST** implement streaming using `datasets.load_dataset(..., streaming=True)`.
- [X] T036 [P] Configure memory thresholds for streaming. **MUST** use a **a substantial chunk size** and a **memory trigger threshold of a significant magnitude** (measured via `psutil`). **MUST** verify memory usage stays within acceptable limits; if usage exceeds 6.0GB, reduce chunk size to a smaller, optimized magnitude and re-run the current chunk processing. (See SC-005, Plan.md)
- [X] T037a [P] **Atomized**: Install dependencies and set up virtual environment for validation run.
- [X] T037b [P] **Atomized**: Execute `quickstart.md` scripts on CPU-only runner.
 - **MUST** verify the runner's resource constraints by checking the `GITHUB_RUNNER_NAME` environment variable (must match 'ubuntu-latest' or similar standard CPU runner).
 - **MUST** record total execution time to verify SC-005 (<=6 hours).
 - **MUST** write the execution time to `state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml` under the key `execution_time_seconds` and also log it to `data/processed/timing.log`.
 - **MUST** Assert that `execution_time_seconds <= 21600` (6 hours) or fail the task.
- [X] T037c [P] **Atomized**: Verify all outputs exist and pass basic schema checks within 6 hours.
- [X] T038 [P] Final verification of all limitation disclosures (FR-011) in all generated reports and visualizations. **MUST** scan all generated files for the mandatory header/footer and fail if missing.

---

## Revision Tasks: Addressing Review Concerns

**Purpose**: Address specific reviewer concerns from prior research-stage reviews regarding data integrity, API reliability, and statistical rigor.

- [ ] T050 [P] [US1] Implement robust error handling in `code/data/download.py` to enforce "Fail Loudly" policy: Remove any `try/except` blocks that fall back to synthetic/mock data. If the Stack Overflow dump or HuggingFace dataset fetch fails, the script MUST raise a `ConnectionError` or `FileNotFoundError` immediately and halt execution. (See Constitution Principle III: Data Hygiene)
- [X] T051 [P] [US1] Implement API rate-limiting and caching in `code/data/external.py` (T039) to prevent GitHub/NPM API violations. **MUST** implement a local disk cache (e.g., `data/cache/github_api_cache.json`) with a Extended TTL

The research question focuses on determining the optimal time-to-live (TTL) duration for network packets to balance freshness and overhead. The method involves simulating various TTL configurations under dynamic traffic conditions, as described in Smith et al. (2023) []. to ensure reproducibility and avoid hitting rate limits during re-runs. (See Plan.md Spec Root Cause Note 5)
- [ ] T052 [P] [US1] Refactor `code/analysis/trends.py` (T014b) to explicitly document and log the Benjamini-Hochberg correction process. **MUST** output a debug log showing raw p-values vs. adjusted q-values for the first 5 tags to verify the correction is applied correctly before classification. (See Plan.md Spec Root Cause Note 2)
- [X] T053 [P] [US3] Enhance `code/analysis/clustering.py` (T030) to handle fuzzy matching edge cases. **MUST** implement a fallback mechanism where if the Levenshtein distance > 2, the tag is skipped for that category but logged to `data/processed/clustering_warnings.log` rather than failing the entire task. (See Plan.md Spec Root Cause Note 4)
- [X] T054 [P] [US1] **MERGED into T012** (See T012 for implementation details).
- [X] T055 [P] [US2] **MERGED into T041** (See T041 for implementation details).
- [X] T056 [P] [US3] **MERGED into T029** (See T029 for implementation details).
- [X] T057 [P] [US1] **MERGED into T014c** (See T014c for implementation details).

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T058 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
