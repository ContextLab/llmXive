# Tasks: The Impact of Perceived Control Over Digital Environments on Anxiety

**Input**: Design documents from `/specs/001-perceived-control-anxiety/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `specs/`)
- [X] T002 Initialize Python 3.10 project with `requirements.txt` (pinned versions for `datasets`, `transformers`, `scikit-learn`, `pandas`, `matplotlib`, `seaborn`, `pytest`)
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes critical schema validation and Plan/Spec alignment tasks.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` for global config, random seeds, and path constants. **ADD**: Define `SAMPLE_SIZE` (default 10000) and `RUNTIME_LIMIT_HOURS` (default 6).
- [X] T005 [P] Setup `code/__init__.py` and `tests/__init__.py`
- [X] T006 [P] Create `code/services/__init__.py`, `code/analysis/__init__.py`, `code/viz/__init__.py`
- [X] T045 [SC] **FIX PLAN DISCREPANCY**: Update `plan.md` Phase 2 Step 5 to explicitly state that normality checks are performed on **residuals** (per Spec US3-AC-008), not marginal distributions, to align the plan with the implemented code in T033a/T033b. **Dependency**: T008c. **Rationale**: Resolves the contradiction between Plan and Spec before implementation begins. **Note**: Moved to Phase 1 to ensure plan is correct before code generation.
- [X] T046b [US1] **UPDATE SPEC MODEL AUTHORIZATION**: Update `spec.md` US1-AC-001 to explicitly authorize the model `cardiffnlp/twitter-roberta-base-emotion` used in T015, ensuring the Spec matches the implementation and satisfies Verified Accuracy. **Dependency**: None (Foundational). **Note**: Moved to Phase 1 to remove dependency on T008c.
- [X] T008a [P] Generate **DRAFT** `contracts/dataset.schema.yaml` defining the schema for raw/processed data and configuration parameters. **Include provisional default values**: `filtering.min_text_length` (3). **Output**: Draft schema file.
- [X] T008a2 [P] Generate **DRAFT** `contracts/analysis.schema.yaml` defining the schema for analysis configuration parameters. **Include provisional default values**: `filtering.entropy_threshold` (0.7). **Include provisional placeholders**: `weights.weight_filter` and `weights.weight_regularity` (to be removed in T008a1). **Output**: Draft schema file.
- [X] T008a1 [SC] **SET MAPPING RULE**: Update `contracts/analysis.schema.yaml` (from T008a2) to **REMOVE** the orphaned `weights.weight_filter` and `weights.weight_regularity` keys. **ADD**: Define the `model_mapping.fear_to_anxiety` rule as a boolean configuration key with `description`: "If true, map 'fear' label to anxiety score". **Do NOT set a default value**. **Dependency**: T008a2. **Rationale**: Ensures the schema defines the mapping capability without enforcing an unverified assumption, and cleans up orphaned config keys. **Note**: T006a depends on this task.
- [X] T006a [SC] Perform 'Phase 0: Research & Dataset Validation' checks: Verify that `cardiffnlp/tweet_sentiment_extraction` contains required fields (`text`, `timestamp`, `user_id`, `filter_applied` or equivalent) against the *finalized* schema (T008a1). **Input**: `contracts/analysis.schema.yaml`. **Output**: Generate `state/validation_report.md` with schema: `dataset_id`, `field_check` (list of fields), `status` (pass/fail), `error_msg`. **Dependency**: T008a1. **Note**: This task must run AFTER T008a1.
- [X] T007 Create `code/main.py` pipeline orchestrator skeleton **WITH TIMEOUT ENFORCEMENT**: Implement the main loop to track elapsed time and raise `RuntimeLimitExceededError` if `config.RUNTIME_LIMIT_HOURS` (default 6) is exceeded. **ADD**: Implement a `signal`-based hard kill-switch (e.g., `signal.signal(signal.SIGALRM, handler)`) to enforce the 6-hour limit independently of any config file. **Dependency**: T004.
- [X] T004b [SC-004] Integrate runtime monitor into `code/main.py` (T007) to log elapsed time and enforce the 6-hour limit defined in `config.RUNTIME_LIMIT_HOURS`. **Dependency**: T007.
- [X] T008 Setup `data/raw/` and `data/processed/` directories with `.gitkeep`
- [X] T008c [P] **FINALIZE** `contracts/analysis.schema.yaml` and `contracts/dataset.schema.yaml` based on validation results from T006a. **Dependency**: T006a.
- [X] T008b [SC] Generate `data-model.md` artifact defining the data model and relationships. **Dependency**: T008c. **Note**: T008b is NOT [P] to ensure it runs after T008c.
- [X] T009 [P] Configure `pytest` with `pytest-cov` in `tests/`
- [ ] T013b [US1] **PRE-RUN SAMPLING**: Implement logic in `code/services/data_ingestion.py` to enforce `config.SAMPLE_SIZE` (default 10000) on the dataset *before* full ingestion. **Logic**: If dataset size > SAMPLE_SIZE, select a random subset using `datasets.load_dataset(..., split='train', streaming=True)` and `itertools.islice` to fetch exactly SAMPLE_SIZE rows. **Output**: A subset of the dataset ready for processing. **Dependency**: T004. **Rationale**: Ensures SC-004 (6-hour limit) is met by capping data volume upfront, eliminating the need for runtime profiling.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Anxiety Scoring (Priority: P1) 🎯 MVP

**Goal**: Download a public social media dataset, preprocess text, and assign anxiety scores using a CPU-tractable model.

**Independent Test**: The system can be fully tested by running the ingestion pipeline on a small, fixed sample of known posts and verifying that anxiety scores are generated for ≥95% of non-null rows, with no null values, and that the distribution of scores matches the expected range. Verification must confirm the existence and validity of `data/processed/coverage_report.json` generated by T018a.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for data ingestion in `tests/unit/test_data_ingestion.py` (use a fixed sample file for real-world constraints, or mock for logic only)
- [ ] T011 [P] [US1] Unit test for anxiety scoring in `tests/unit/test_anxiety_scoring.py` (mock model output)
- [X] T012 [P] [US1] Integration test for full ingestion pipeline in `tests/integration/test_ingestion_validation.py` (runs on a sample of rows)

### Implementation for User Story 1

**Note**: T021 requires T013 to be completed and verified before starting.

- [ ] T013 [US1] Implement `code/services/data_ingestion.py` to download dataset `cardiffnlp/tweet_sentiment_extraction` (split='train', revision='main') from HuggingFace to `data/raw/social_media.csv` using `datasets.load_dataset`. **Checksum**: Validate file integrity using `md5` (log hash) and fail loudly if mismatch. **Dependency**: T013b (Sampling). **Note**: T013 now assumes T013b has already prepared the data or will sample internally if T013b is skipped.
- [ ] T042 [US1] **FALLBACK**: If T013 fails (download error or OOM), implement streaming fallback in `code/services/data_ingestion.py` using `datasets.load_dataset(..., streaming=True)`. **Logic**: Process in chunks, accumulate statistics, and compute a final checksum by hashing concatenated chunks to satisfy T013 checksum requirement. **Dependency**: T013 (on failure).
- [ ] T014b [US1] [US1-AC-002] Implement Non-English text filtering in `code/services/anxiety_scoring.py` using `langdetect`. **Logic**: Read `data/raw/social_media.csv`, filter rows where language is not 'en' OR `langdetect` confidence < 0.8 OR detection fails. **Config**: Read `filtering.langdetect_threshold` (default 0.8) from `contracts/analysis.schema.yaml`. **Dependency**: T013. **Note**: T014b is NOT [P] to ensure sequential execution before T014c.
- [ ] T014c [US1] [US1-AC-002] Implement gibberish filtering logic in `code/services/anxiety_scoring.py` (e.g., text length < 3 or entropy-based heuristic). **Input**: `data/processed/preprocessed_text.csv` (produced by T014b). **Config**: Read `filtering.entropy_threshold` (default 0.7) and `filtering.min_text_length` (default 3) from `contracts/analysis.schema.yaml`. If missing, raise `ConfigurationError` with specific key names. **Dependency**: T014b, T008c.
- [X] T014d [US1] **FILTER SUFFICIENCY CHECK**: Verify that the row count after T014c filtering is sufficient to meet the ≥95% coverage target (AC-003). **Logic**: Compare `len(post-filtered rows)` against `len(original valid rows) * 0.95`. If insufficient, raise `DataInsufficientError` with a message suggesting to relax `filtering.langdetect_threshold` or `filtering.entropy_threshold` in config. **Dependency**: T014c. **Note**: Ensures AC-003 is checkable and actionable.
- [ ] T015a [US1] **MODEL LABEL VERIFICATION**: Implement a check in `code/services/anxiety_scoring.py` to dynamically inspect the label set of `cardiffnlp/twitter-roberta-base-emotion` at runtime. **Logic**: Load the model tokenizer, get `model.config.id2label`, and verify if 'fear' (or equivalent) exists. If absent, log a warning and set `model_mapping.fear_to_anxiety` to `False` (or halt if configured). **Output**: A boolean `has_fear_label` saved to `state/model_validation.json`. **Dependency**: T013. **Note**: Ensures Verified Accuracy before mapping logic runs.
- [ ] T015 [US1] Implement CPU-tractable anxiety model inference in `code/services/anxiety_scoring.py` (load `cardiffnlp/twitter-roberta-base-emotion` in default float32 precision). **Input**: `data/processed/preprocessed_text.csv` (produced by T014b). **Dependency**: T014b, T008c, T046b (Spec Authorization), T015a (Label Verification). **Logic**: **VERIFY** model outputs 'anxiety' or 'fear'. If 'fear' is present and `model_mapping.fear_to_anxiety` is configured (and verified by T015a), map it. **HALT** if 'fear' is not present but mapping is expected, logging the error. **Note**: T015 is NOT [P] to ensure sequential execution after T014b and T046b.
- [ ] T016 [US1] Implement confidence score filtering (threshold ≥ 0.6) in `code/services/anxiety_scoring.py` to exclude low-confidence predictions before saving
- [ ] T017 [US1] Save scored and filtered data to `data/processed/scoring_results.csv` with columns: `text`, `anxiety_score`, `confidence_score`
- [ ] T018 [US1] Add error handling for empty datasets or download failures in `code/services/data_ingestion.py`
- [ ] T018a [US1] Implement coverage validation logic to verify ≥95% scoring coverage by comparing row counts of `preprocessed_text.csv` (T014b) and `scoring_results.csv` (T017), generating `data/processed/coverage_report.json`. **Note**: Ensure the denominator is the count of 'valid' rows (post-filter) as defined in `contracts/analysis.schema.yaml`. **Dependency**: T014d.
- [X] T018b [US1] **ENFORCEMENT**: If T018a reports coverage <95%, raise `CoverageError` and halt the pipeline. **Dependency**: T018a.
- [X] T046 [US1] **ADD DATASET SOURCE DOCUMENTATION**: Create `specs/001-the-impact-of-perceived-control-over-dig/data-sources.md` documenting the exact HuggingFace dataset ID, split, revision, and field definitions used, including a direct link to the dataset card and a citation for the `cardiffnlp` collection. **Dependency**: T013 (start/definition). **Note**: Documents the values intended in T013.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Control Proxy Extraction (Priority: P2)

**Goal**: Extract metadata-based proxies representing "perceived control" from the same dataset, ensuring strict independence from text content.

**Independent Test**: The system can be tested by processing a subset of posts where the presence of control-related metadata flags (e.g., `filter_applied=true`) and timestamp patterns are manually verified against the extracted proxy values, ensuring a ≥95% match on a test set of a representative number of items. Verification must confirm the existence of `tests/integration/test_proxy_validation.py`.

### Tests for User Story 2

- [ ] T019 [P] [US2] Unit test for proxy extraction logic in `tests/unit/test_proxy_extractor.py`
- [X] T020 [P] [US2] Integration test for proxy extraction pipeline in `tests/integration/test_proxy_validation.py`

### Implementation for User Story 2

**Note**: T021 requires T013 to be completed and verified before starting.

- [ ] T021 [US2] Implement `code/services/proxy_extractor.py` to read `data/raw/social_media.csv` (produced by T013) and extract metadata fields (`filter_applied`, `timestamp`, `user_id`) strictly without accessing the `text` column. **DEFENSIVE**: Explicitly assert that the `text` column is never loaded or accessed; if accessed, raise `DataIndependenceError`. **Dependency**: T013.
- [X] T022 [US2] Implement logic to calculate `filter_applied` contribution to `control_proxy`. **Logic**: Binary flag (1 if `filter_applied` is true, 0 otherwise). **DEFENSIVE**: Assert no `text` column access; raise `DataIndependenceError` if violated. **Dependency**: T008c (Schema). **Note**: Removed `weights.weight_filter` from config as per T008a2.
- [ ] T023 [US2] Implement logic to calculate `timestamp_regularity` metric per user in `code/services/proxy_extractor.py`. **Logic**: Calculate standard deviation of inter-post intervals; normalize to [0,1] (lower std dev = higher regularity). **Note**: Removed `weights.weight_regularity` from config as per T008a2.
- [ ] T024a [US2] Verify the code logic in `code/services/proxy_extractor.py` that explicitly loads the CSV and excludes the `text` column from any processing, ensuring strict adherence to Constitution Principle VI. **Dependency**: T021 and T022.
- [X] T025 [US2] Handle missing metadata fields by defaulting to a baseline value of zero and logging a warning
- [ ] T026 [US2] Save extracted proxies to `data/processed/proxy_results.csv` with columns: `post_id`, `user_id`, `control_proxy`, `timestamp_regularity`
- [X] T050 [US2] **METADATA HEURISTIC VALIDATION**: Create `tests/unit/test_proxy_heuristics.py` to validate that `timestamp_regularity` correctly identifies irregular posting patterns (e.g., bursty vs. regular) using a synthetic time-series fixture. **Dependency**: T021/T022. **Note**: T050 is NOT [P] to ensure sequential execution.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Visualization (Priority: P3)

**Goal**: Perform statistical analysis to test correlation between control proxy and anxiety scores, including robustness checks, and generate a scatter plot.

**Independent Test**: {{claim:c_e63a79cb}} Verification must confirm the presence of the `is_significant` flag in `data/processed/analysis_results.json` and the existence of `tests/integration/test_synthetic_correlation.py`.

### Tests for User Story 3

- [ ] T027 [P] [US3] Unit test for statistical test logic in `tests/unit/test_statistical_test.py`
- [ ] T028 [P] [US3] Unit test for visualization generation in `tests/unit/test_plot_results.py`
- [X] T029 [P] [US3] Integration test for full analysis pipeline in `tests/integration/test_synthetic_correlation.py` (uses merged data)

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/main.py` pipeline logic to orchestrate the merge and save steps: Read from `data/processed/scoring_results.csv` (T017) and `data/processed/proxy_results.csv` (T026), join on `post_id`, and save to `data/processed/final_analysis.csv`. **Dependency**: T017 AND T026. **Note**: T030 replaces T031 and T032.
- [ ] T033a [US3] [US3-AC-008] Implement residual calculation in `code/analysis/statistical_test.py`: Calculate residuals (observed anxiety - predicted anxiety from preliminary linear fit) using data from `data/processed/final_analysis.csv`. **Variables**: X=`control_proxy`, y=`anxiety_score`. Use `statsmodels.OLS` for the preliminary fit. **Save residuals to `data/processed/residuals.csv`**. **Dependency**: T030.
- [ ] T033b [US3] [US3-AC-009] Implement Shapiro-Wilk test on the **residuals** (calculated in T033a) in `code/analysis/statistical_test.py`. **Logic**: Save residuals + normality p-value to `data/processed/normality_check.json`. **Branching**: If p < 0.05, set `method`='Spearman'; else `method`='Pearson'. **Dependency**: T033a.
- [X] T034b [US3] **ROBUSTNESS**: If T033b produces invalid normality check results (NaN/None), default to Spearman correlation. **Dependency**: T033b.
- [ ] T034 [US3] Implement logic in `code/analysis/statistical_test.py` to switch to Spearman correlation if normality violated (p < 0.05), otherwise use Pearson, and calculate correlation coefficient (r) and p-value, saving results to `data/processed/analysis_results.json` with an `is_significant` flag (true if p < 0.05). **Dependency**: T034b.
- [ ] T035 [US3] Implement `code/viz/plot_results.py` to generate scatter plot with regression line (OLS or rank-based) and axis labels
- [ ] T036 [US3] Save final visualization as `data/processed/correlation_plot.png`. **Note**: Ensure figure dimensions are appropriate for publication quality, DPI 300, and style `seaborn.darkgrid`.
- [X] T049 [US3] **NORMALITY TEST DOCUMENTATION**: Update `specs/001-the-impact-of-perceived-control-over-dig/research.md` to explicitly justify the choice of Shapiro-Wilk on residuals over marginal distributions, citing the specific statistical reasoning for this research design decision. **Dependency**: T033b. **Note**: T049 is NOT [P] to ensure sequential execution.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T044 [P] [US3] Implement a reproducibility audit script in `tests/integration/test_reproducibility.py` that re-runs the pipeline with fixed seeds and verifies that `data/processed/analysis_results.json` produces identical results.
- [ ] T048 [US1] **STREAMING DATA INTEGRATION**: Update `code/services/data_ingestion.py` to natively support `streaming=True` for the primary dataset load (enhancement to T013), accumulating a running hash for checksum validation without loading the full dataset into memory, ensuring compliance with SC-004 for large datasets. **Dependency**: T013. **Note**: This is an optimization, not a mandatory replacement. **Status**: OPTIONAL.
- [X] T052 [P] [US1/US2/US3] **FULL PIPELINE INTEGRATION TEST**: Create `tests/integration/test_full_pipeline.py` that executes the entire flow from raw data download to final visualization, asserting that all intermediate files exist and that the final `analysis_results.json` contains valid numeric values for `r`, `p_value`, and `is_significant`. **Dependency**: T030, T034, T036.
- [ ] T053 [P] [US3] **VISUALIZATION QUALITY AUDIT**: Implement a script in `tests/unit/test_plot_quality.py` to programmatically verify that `data/processed/correlation_plot.png` contains the regression line, axis labels, and title as specified in T036, and that the file size is reasonable (< 5MB). **Dependency**: T036.

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 outputs (merged data)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Services before endpoints/scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) - **EXCEPT T008a1, T006a, T008b, T045, T046, T046b which are sequential**
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (except US3 which depends on US1/US2 data)

**Critical Execution Note**: T030 (Merge) is strictly blocked until **BOTH** T017 (US1 Output) and T026 (US2 Output) are complete. Do not attempt T030 until both producers are verified.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (data ingestion + scoring)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo (final analysis)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Ingestion & Scoring)
 - Developer B: User Story 2 (Proxy Extraction)
 - Developer C: User Story 3 (Analysis & Viz) - *Note: Must wait for data from A & B*
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
- **Critical Constraint**: All model inference MUST run on CPU (no CUDA/8-bit quantization) to ensure feasibility on free-tier runners.
- **Critical Constraint**: `control_proxy` extraction MUST NOT access text content (Constitution Principle VI).
- **Note**: Plan.md Phase 2 Step 5 currently states "marginal distributions" which contradicts Spec US3-AC-008 "residuals". Tasks T033a/T033b follow Spec; Plan flagged for correction in T045 (Phase 1).
- **Note**: Confidence filtering (FR-006) is performed in T016 (`anxiety_scoring.py`) BEFORE data is saved in T017. T030 merges this pre-filtered data.
- **Note**: T021 explicitly restricts access to the `text` column to enforce data independence.
- **Note**: T014b implements `langdetect` for Non-English filtering; T014c implements gibberish filtering. **Sequential**: T014b must run before T014c.
- **Note**: Specific heuristic parameters (entropy, weights) are defined in `contracts/analysis.schema.yaml`, not hardcoded in tasks, to prevent silent drift. **UPDATE**: `weights` keys removed from schema as they were orphaned.
- **Note**: T043 (Loud Fail) has been removed as it was marked rejected; T042 (Streaming Fallback) handles download errors gracefully.
- **New**: T008a1 sets the default `model_mapping.fear_to_anxiety` to a configurable rule, not a hardcoded `true`, to prevent scope creep.
- **New**: T045 (Plan Fix) is moved to Phase 1 to resolve the Plan/Spec contradiction before implementation begins.
- **New**: T046b (Spec Model Authorization) is moved to Phase 1 to ensure authorization is in place before T015 runs.
- **New**: T050 (Metadata Heuristic Validation) is added to validate the timestamp regularity heuristic.
- **New**: T013b (Pre-run Sampling) replaces T051 to enforce sample size upfront, eliminating circular dependencies.
- **New**: T014d (Filter Sufficiency Check) ensures AC-003 is actionable.
- **New**: T015a (Model Label Verification) ensures Verified Accuracy for the 'fear' mapping.
- **Removed**: T051 (Performance Configuration) and T054 (Hard Timeout Enforcement) are removed as they created circular dependencies and were redundant with T007/T004b.
- **Removed**: T038, T039, T040a, T041, T043 are removed from the task list as they were marked rejected.
- **Removed**: T031 and T032 are merged into T030 (Merge & Save).
- **Removed**: T030 (Skeleton) is merged into T030 (Merge & Save).
- **New**: T052 (Full Pipeline Integration Test) ensures end-to-end correctness.
- **New**: T053 (Visualization Quality Audit) ensures output meets publication standards.
- **New**: T033a now explicitly saves residuals to `data/processed/residuals.csv`.
- **New**: T046 is moved to Phase 3 to document dataset parameters after T013 is defined.
