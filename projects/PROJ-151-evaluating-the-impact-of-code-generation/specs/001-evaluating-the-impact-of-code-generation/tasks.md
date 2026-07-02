# Tasks: Evaluating the Impact of Code Generation Models on Code Review Efficiency

**Input**: Design documents from `/specs/001-evaluating-code-generation-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included as requested by the specification's independent test requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story, strictly adhering to the data flow: Ingest → Generate → Metrics → Analyze.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-151-evaluating-code-generation/`
- **Structure**: `code/`, `data/`, `tests/` at project root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, environment configuration, and seed pinning (FR-009)

- [ ] T001 [P] Create project directory tree per `plan.md` (directories: `code/`, `data/raw/`, `data/processed/`, `data/generated/`, `data/validation/`, `tests/`)
- [ ] T002 [P] Initialize Python 3.11 environment and create `requirements.txt` pinning `datasets`, `transformers`, `torch` (CPU), `radon>=0.7.0`, `pylint`, `statsmodels>=0.14.0`, `pandas`, `numpy`, `scikit-learn`, `pwr`
- [ ] T003 [P] Create `.gitignore` to exclude `data/` (raw/processed/generated) and `__pycache__`
- [X] T004 [P] Implement `code/config.py` to define constants, paths, and global random seed `42` for `random`, `numpy`, and `torch`
- [ ] T005 [P] Create `state.yaml` skeleton for artifact hashing and version tracking

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure for reproducibility and data hygiene (Constitution Principles)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Implement `code/data/validation.py` with schema validation functions for `code_snippet`, `comment_count`, and `project_id`
- [ ] T007 [P] Implement `code/metrics/utils.py` for metric aggregation and checksum calculation utilities
- [ ] T008 Implement `code/generation/provenance.py` to log `model_id`, `prompt`, `seed`, `timestamp` to `data/generated_provenance.csv` (Note: Must run after T001 to ensure directory exists)
- [ ] T009 [P] Create base data model classes (Code Snippet, Review Record, ExperimentPair) in `code/data/models.py`
- [ ] T010 [P] Implement `tests/unit/test_config.py` to verify seed pinning and environment variables

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 0.5: Power Analysis (Prerequisite for Generation)

**Purpose**: Determine initial N based on cluster count and power constraints (FR-003). This task defines the *initial* sample size target but does NOT handle runtime OOM fallback logic.

- [ ] T031 [P] [US2/US3] Implement `code/analysis/power.py` to load raw data, count clusters, and calculate initial power; define initial target N (e.g., N=1000). Note: If clusters < 30 or power < 0.70, log a warning and suggest N=200, but the actual enforcement of N=200 occurs in T023 only upon OOM error per FR-003.

**Checkpoint**: Initial power constraints defined; generation target N established.

---

## Phase 3: User Story 1 - Data Acquisition & Filtering (Priority: P1) 🎯 MVP

**Goal**: Retrieve Gerrit Chromium proxy dataset, filter for Java/Python PRs ≤30 LOC, and validate effort metrics (FR-001, FR-002)

**Independent Test**: Run ingestion script; verify `data/processed/filtered_prs.parquet` exists with ≥1,000 rows, non-null `review_comment_count`, `code_snippet`, `project_id`.

### Tests for User Story 1

- [ ] T011 [P] [US1] Contract test for dataset schema in `tests/contract/test_data_ingestion.py` (verify expected columns exist; validates schema regardless of implementation order)
- [ ] T012 [P] [US1] Unit test for LOC filtering logic in `tests/unit/test_filter.py` (verify >30 lines excluded)
- [ ] T013 [P] [US1] Unit test for comment quality filter in `tests/unit/test_comment_filter.py` (verify <10 chars or 'LGTM' excluded)

### Implementation for User Story 1

- [ ] T014 [US1] Implement `code/data/ingest.py` to download `loubnabnl/prs-v2-sample` via `datasets.load_dataset`
- [ ] T015 [US1] Implement filtering logic in `code/data/ingest.py`: language in ["Java", "Python"], `diff_lines` ≤ 30
- [ ] T016 [US1] Implement `code/data/filter_comments.py` to exclude low-quality comments and calculate `filtered_comment_count`
- [ ] T017 [US1] Implement validation step in `code/data/validation.py` to ensure `code_snippet` and `filtered_comment_count` are present
- [ ] T018 [US1] Save filtered dataset to `data/processed/filtered_prs.parquet` with checksum recorded in `state.yaml`
- [ ] T019 [US1] Implement strict schema check in `code/data/ingest.py`: If `review_time` or `perceived_difficulty` fields are present in the dataset schema, raise a `ValueError` immediately with a message indicating these fields are forbidden per FR-001. Do NOT log a warning and proceed; the system must fail fast to ensure strict data hygiene.

**Checkpoint**: User Story 1 fully functional; data layer ready for generation.

---

## Phase 4: User Story 2 - Code Generation & Metric Computation (Priority: P2)

**Goal**: Generate code using CodeGen-350M (primary, CPU-optimized) with fallback to StarCoder-1B, compute static metrics, and track provenance (FR-002, FR-003, FR-004, FR-008, FR-009)

**Independent Test**: Run generation pipeline on sample; verify `data/generated/code_snippets.csv`, `data/processed/metrics.csv`, and `data/generated_provenance.csv` exist without CUDA errors.

### Tests for User Story 2

- [ ] T020 [P] [US2] Contract test for generated code schema in `tests/contract/test_generation.py`
- [ ] T021 [P] [US2] Unit test for metric computation (Radon/Pylint) in `tests/unit/test_metrics.py`
- [ ] T022 [P] [US2] Unit test for OOM fallback logic in `tests/unit/test_model_loader.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/generation/model_loader.py` to {{claim:c_10ca5a73}} (Wikidata Q117453145, https://www.wikidata.org/wiki/Q117453145). If an Out-of-Memory (OOM) error occurs during loading or inference, automatically fall back to StarCoder-1B. If StarCoder-1B also fails or OOM persists, enforce sample size reduction to N=200 pairsand trigger power recalculation logic (as per FR-003). Note: This task implements the runtime fallback logic; T031 only defines initial planning targets.
- [ ] T024 [US2] Implement `code/generation/generate.py` to extract problem statements from PR titles and generate code with seed=42
- [ ] T025 [US2] Implement symmetric prompting logic in `code/generation/generate.py` to ensure same prompt for Human and LLM comparison
- [ ] T026 [US2] Implement `code/generation/provenance.py` call in generation loop to log `model_id`, `prompt`, `seed`, `timestamp` to `data/generated_provenance.csv`
- [ ] T027 [US2] Implement syntax validation and "failed" marking for generated snippets in `code/generation/generate.py`
- [ ] T028 [US2] Save generated snippets to `data/generated/code_snippets.csv`
- [ ] T029 [US2] Implement `code/metrics/compute.py` to calculate Cyclomatic Complexity, Maintainability Index (Radon), Pylint Score, Checkstyle Score, Token Count
- [ ] T030 [US2] Run metrics computation on both human and generated code; save results to `data/processed/metrics.csv`

**Checkpoint**: Code generation and metrics pipeline complete; data ready for analysis.

---

## Phase 5: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Fit mixed-effects models, perform interaction tests, sensitivity analysis, and validation study (FR-005, FR-006, FR-007, FR-010, FR-011, FR-012, FR-013, FR-014)

**Independent Test**: Run analysis script; verify report contains p-values, R², sensitivity tables, and validation study results.

### Tests for User Story 3

- [ ] T032 [P] [US3] Unit test for mixed-effects model fitting in `tests/unit/test_model_fit.py`
- [ ] T033 [P] [US3] Unit test for multiple-comparison correction in `tests/unit/test_correction.py`
- [ ] T034 [P] [US3] Contract test for final report schema in `tests/contract/test_report.py`

### Implementation for User Story 3

- [ ] T035 [US3] Implement `code/analysis/collinearity.py` to perform KS-test on complexity distributions; implement Propensity Score Matching (PSM) if shift detected (Phase 3.5)
- [ ] T036 [US3] Implement `code/analysis/model_fit.py` to fit Linear Mixed-Effects model (Wikidata Q120282163, https://www.wikidata.org/wiki/Q120282163): `Effort ~ Complexity + Origin + (Complexity * Origin) + (1|Project_ID)`
- [ ] T037 [US3] Implement interaction test logic in `code/analysis/model_fit.py`: if `Origin * Complexity` p < 0.05, report stratified results (FR-013)
- [ ] T038 [US3] Implement `code/analysis/wilcoxon.py` to perform paired Wilcoxon signed-rank tests on matched pairs (FR-010)
- [ ] T039 [US3] Implement `code/analysis/correction.py` to apply Bonferroni/FDR correction to all p-values (FR-007)
- [ ] T040 [US3] Implement `code/analysis/sensitivity.py` to sweep LOC thresholds and compare results (FR-006)
- [ ] T041 [US3] Implement `code/analysis/validation.py` to load survey data (Likert, time) and calculate Cohen's Kappa; implement blinding protocol validation (reviewers unaware of origin). The task must produce a boolean `is_blinded` flag and a validation report confirming the blinding protocol was enforced.
- [ ] T042 [US3] Implement `code/analysis/validation.py` to compute MAE between predicted (historical) and actual (validation) effort (FR-014)
- [ ] T043 [US3] Implement final report generation in `code/main.py` with explicit disclaimer paragraph (FR-005)
- [ ] T044 [US3] Implement Success Criterion checks (SC-001 to SC-005) in `code/analysis/report.py` and output Pass/Fail status

### Validation Study Infrastructure (FR-011, FR-012)

- [ ] T052 [US3] Implement `code/validation/stopwatch_server.py` to serve a browser-based HTML/JS interface (file: `code/validation/static/index.html`) for the validation study. Implement the blinding protocol (FR-011/FR-012) via server-side masking of code origin labels and randomization of presentation order. Record actual review time (millisecond precision) and submit to `data/validation/survey_results.csv`.
- [ ] T053 [US3] Implement `code/validation/collect_survey_data.py` to manage the survey workflow, ensuring ≥3 reviewers and ≥50 snippets are processed

### Report Generation (Granular)

- [ ] T056 [US3] Implement `code/analysis/report_tables.py` to generate statistical summary tables (coefficients, p-values, R²)
- [ ] T057 [US3] Implement `code/analysis/report_plots.py` to render diagnostic plots (distributions, sensitivity curves)
- [ ] T058 [US3] Implement `code/analysis/report_assemble.py` to combine tables, plots, and text into `research.md`

**Checkpoint**: All user stories complete; research pipeline functional.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and validation

- [ ] T046 [P] Update `README.md` with quickstart instructions and environment setup
- [ ] T047 [P] Verify `requirements.txt` includes all pinned versions and comments
- [ ] T048 Run full pipeline end-to-end to verify checksums and `state.yaml` integrity
- [ ] T049 [P] Add docstrings and type hints to all `code/` modules
- [ ] T050 [P] Generate final `data-model.md` documenting all entities and relationships

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Power Analysis (Phase 0.5)**: Can run after Foundational; defines initial N for Generation
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - US1 (Data) must complete before US2 (Generation)
 - US2 (Metrics) must complete before US3 (Analysis)
 - US3 depends on US1 and US2 data outputs
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational. Must complete before US2.
- **User Story 2 (P2)**: Depends on US1 (needs `filtered_prs.parquet`). Must complete before US3.
- **User Story 3 (P3)**: Depends on US1 (historical data) and US2 (generated data/metrics).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (except T008 which depends on T001)
- Tests for each user story can run in parallel
- Within US3, sensitivity analysis, Wilcoxon, and validation analysis can run in parallel once data is ready

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Data Ingestion)
4. **STOP and VALIDATE**: Verify `filtered_prs.parquet` meets criteria
5. Proceed to Generation only if data is valid

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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Generation) - *Can start only after US1 data is available*
 - Developer C: User Story 3 (Analysis) - *Can start only after US1 and US2 data available*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: No task may load models requiring CUDA; all inference must be CPU-only with fallback logic (CodeGen-350M primary -> StarCoder-1B -> N=200).
- **Critical Constraint**: No fabrication of data; all analysis must use real data from `filtered_prs.parquet` and `code_snippets.csv`.
- **Critical Constraint**: Validation study (FR-012) MUST use the browser-based stopwatch tool (T052) for ground-truth effort measurement with blinding protocol enforced.