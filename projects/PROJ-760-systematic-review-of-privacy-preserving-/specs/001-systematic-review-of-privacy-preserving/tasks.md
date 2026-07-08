# Tasks: Systematic Review of Privacy-Preserving Federated Learning Protocols

**Input**: Design documents from `/specs/001-systematic-review-privacy-fl/`
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

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-760-systematic-review-of-privacy-preserving-/code/`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` containing `requests`, `arxiv`, `pdfplumber`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` to define search strings, API rate limits, date ranges (recent years), and output paths (`data/raw`, `data/processed`)
- [ ] T005 [P] Implement `code/utils/logging.py` with structured JSON logging and `code/utils/checksums.py` for SHA256 file verification
- [ ] T006 [P] [US1/US2/US3] Implement `code/services/validator.py` implementing the Title-Token-Overlap check (threshold ≥ 0.7) against arXiv/SS API for citation verification AND statistical inputs (effect sizes, extracted metrics) to satisfy Constitution Principle II
- [ ] T007 Implement `code/services/categorizer.py` with strict rule-based logic to classify studies into DP, SecureAgg, FHE, or Hybrid categories
- [ ] T008 Setup `data/raw/` and `data/processed/` directories with `.gitignore` rules to exclude large binaries while tracking CSVs
- [ ] T009 Create `code/main.py` entry point that orchestrates the pipeline flow (Retrieve -> Parse -> Categorize -> Analyze -> Report)
- [ ] T019 [P] [US1] Integrate `code/services/validator.py` into the pipeline flow to verify citation metadata and statistical inputs BEFORE writing to `data/raw/literature_candidates.csv` (Dependency: T006)
- [ ] T054 [P] [US2] Implement a pre-processing step in `code/main.py` to verify that `data/raw/literature_candidates.csv` exists and contains valid PDF URLs before attempting to download or parse PDFs (Data Flow Dependency)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Literature Retrieval and Metadata Extraction (Priority: P1) 🎯 MVP

**Goal**: Retrieve peer-reviewed papers from arXiv and Semantic Scholar, filter by date, and extract structured metadata.

**Independent Test**: Run retrieval script against a fixed seed query; verify output CSV contains ≥10 records with valid metadata and no duplicates.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010a [P] [US1] Unit test for API query logic in `code/tests/test_retriever.py::test_query_logic_returns_valid_json` (mocked API responses)
- [ ] T010b [P] [US1] Unit test for rate-limit retry logic in `code/tests/test_retriever.py::test_rate_limit_retry_logic`
- [ ] T011a [P] [US1] Integration test for retry max attempts in `code/tests/test_retriever.py::test_retry_max_attempts`
- [ ] T012a [P] [US1] Validation test ensuring output CSV has ≥10 records and no duplicates in `code/tests/test_retriever.py::test_output_csv_validation`

### Implementation for User Story 1

- [ ] T015.5 [US1] Merge arXiv and Semantic Scholar result streams into a single list before deduplication
- [ ] T015 [US1] Implement deduplication logic in `code/services/retriever.py` using DOI or title-hash comparison
- [ ] T013 [P] [US1] Implement `code/services/retriever.py` to query arXiv API with search strings for "federated learning" + "differential privacy"
- [ ] T014 [P] [US1] Implement `code/services/retriever.py` to query Semantic Scholar API (custom wrapper) with same search strings
- [ ] T016 [US1] Implement metadata extraction (title, authors, abstract, PDF URL) and write to `data/raw/literature_candidates.csv`
- [ ] T017 [US1] Implement error handling for missing metadata fields: flag in `data/raw/review_needed.log` instead of dropping
- [ ] T018 [US1] Implement retry logic (max 3 attempts) for API rate limits/timeouts in `code/services/retriever.py`
- [ ] T052 [P] [US1] Implement `code/services/retriever.py` to explicitly handle and log "No Data Available" scenarios if search returns zero results for a specific mechanism (e.g., FHE) rather than crashing

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantitative Data Extraction from PDFs (Priority: P2)

**Goal**: Parse PDFs of selected papers to extract quantitative metrics (communication overhead, convergence rounds, accuracy drop, runtime) and map to privacy mechanism.

**Independent Test**: Run parser on a set of known PDFs with ground truth; verify output matches within 5% tolerance or flags discrepancies.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020a [P] [US2] Unit test for table extraction logic in `code/tests/test_parser.py::test_table_extraction_logic` (mocked PDF structures)
- [ ] T020b [P] [US2] Unit test for handling merged cells in `code/tests/test_parser.py::test_merged_cells_handling`
- [ ] T021a [P] [US2] Integration test for unit normalization (bytes, rounds, seconds) in `code/tests/test_parser.py::test_unit_normalization`
- [ ] T022a [P] [US2] Validation test comparing parser output against a pre-existing manually verified ground-truth dataset of a subset of papers in `code/tests/test_parser.py::test_ground_truth_validation`

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/services/parser.py` using `pdfplumber` to extract tables from PDFs in `data/raw/`
- [ ] T024 [US2] Implement logic to extract specific metrics (Communication Overhead, Convergence Speed, Accuracy Loss, Computational Cost) and detect absence of baseline for BOTH Accuracy Loss and Computational Cost to exclude records prior to normalization (FR-008)
- [ ] T025 [US2] Implement unit normalization: Convergence to 'rounds', Overhead to 'bytes', Cost to 'seconds' or 'relative overhead ratio'
- [ ] T026 [US2] Implement logic to handle non-standard tables (merged cells): log `parsing_error` and skip row, preserving rest of file
- [ ] T027 [US2] Implement `code/services/parser.py` to extract privacy budget (epsilon) and normalize Accuracy Loss by epsilon (formula: Loss / epsilon) ONLY if baseline is available; exclude studies lacking baseline from this specific normalization and store in column `normalized_accuracy_loss` (FR-008)
- [ ] T028 [US2] Implement logic to exclude studies lacking baseline for computational cost calculation (FR-008)
- [ ] T029 [US2] Write extracted data to `data/processed/extracted_metrics.csv` with mechanism tags (DP, SecureAgg, FHE, Hybrid)
- [ ] T030 [US2] Implement fallback logic: if a study uses Hybrid mechanism without disentanglement, categorize as "Hybrid" and flag for review
- [ ] T053 [US2] Implement strict validation in `code/services/parser.py` to reject any synthetic/fake data generation; ensure all input metrics are derived solely from extracted PDF tables or real API metadata
- [ ] T055 [US2] Implement a download manager in `code/services/parser.py` that verifies PDF integrity (SHA256 checksum) before parsing, logging failures to `data/raw/parsing_errors.log`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Meta-Analysis and Visualization Generation (Priority: P3)

**Goal**: Perform Multi-Level Meta-Analysis (MLMA), handle missing variance via descriptive fallback, and generate visualizations/reports.

**Independent Test**: Run analysis on synthetic dataset with known effect sizes; verify forest plots and confidence intervals are generated correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031a [P] [US3] Unit test for MLMA Hedges' g calculation in `code/tests/test_analyzer.py::test_hedges_g_calculation` (synthetic data)
- [ ] T032a [P] [US3] Integration test for fallback to descriptive statistics trigger in `code/tests/test_analyzer.py::test_fallback_to_descriptive_stats`
- [ ] T033a [P] [US3] Validation test for forest plot generation and CI calculation in `code/tests/test_analyzer.py::test_forest_plot_generation`

### Implementation for User Story 3

- [ ] T034 [US3] Implement `code/services/analyzer.py` to compute effect sizes (Hedges' g) and 95% CIs per mechanism type; if variance data is missing, FALL BACK to Descriptive Statistics/Vote Counting instead of skipping (FR-007)
- [ ] T034b [US3] Implement logic to identify studies lacking SD/SE and EXCLUDE them from random-effects models, but include them in the Descriptive Statistics/Vote Counting fallback
- [ ] T035 [US3] Implement Multi-Level Meta-Analysis (MLMA) using `statsmodels` or pure Python `scipy.optimize` (CPU only) to compare mechanism groups, explicitly replacing ANOVA/Kruskal-Wallis
- [ ] T036 [US3] Implement variance detection: identify studies lacking SD/SE and exclude them from random-effects models
- [ ] T037 [US3] Implement fallback logic: if >50% variance data missing, switch to Descriptive Statistics/Vote Counting (output: Vote Counting (positive/negative counts) OR Descriptive Statistics (median [IQR]) if individual effect sizes are available), explicitly excluding fixed-effects models (FR-004)
- [ ] T038 [US3] Implement Benjamini-Hochberg correction for multiple comparisons across mechanism groups (FR-006)
- [ ] T039 [US3] Implement forest plot generation for "Accuracy Loss vs. Privacy Mechanism" with 95% CIs in `data/processed/`
- [ ] T040 [US3] Implement bar chart generation for mean communication overhead per mechanism
- [ ] T041 [US3] Implement scatter plot generation for Accuracy vs. Privacy Budget (epsilon)
- [ ] T042 [US3] Implement logic to flag "Insufficient Data" (N < 3) for specific mechanisms in the report
- [ ] T056 [US3] [SC-001] Implement a "Descriptive Review" mode trigger in `code/services/analyzer.py` that automatically activates if N < 5 per category; output format: report raw counts and median if N>=3, else report 'Insufficient Data' (FR-004)
- [ ] T043 [US3] Generate `results_summary.md` programmatically from `data/processed/extracted_metrics.csv` including tables, figures, and findings
- [ ] T044 [US3] Create `run.sh` script to execute the full pipeline from retrieval to report generation

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure reproducibility

- [ ] T045 [P] Documentation updates: Add usage examples to `README.md` and `quickstart.md`
- [ ] T046 Code cleanup and refactoring of `code/services/` modules
- [ ] Ta [P] Generate a synthetic 200-paper dataset (JSON/CSV) with realistic metrics for performance testing
- [ ] T047b [P] Run the full pipeline (`run.sh`) against the synthetic 200-paper dataset
- [ ] T047c [P] Verify runtime < 6 hours and output checksums match for reproducibility (SC-004, SC-005)
- [ ] T048 [P] Add unit tests for `code/services/validator.py` and `code/services/categorizer.py`
- [ ] T049 Security hardening: Ensure no PII is logged and API keys are handled via environment variables
- [ ] T050 Run `run.sh` validation on a fresh runner to verify reproducibility (SC-005)
- [ ] T051 Verify `state/projects/PROJ-760-systematic-review-of-privacy-preserving-.yaml` is updated on pipeline completion

---

## Phase 7: Data Integrity & Reproducibility Safeguards (Critical)

**Purpose**: Ensure all data processing steps use real sources, avoid fabrication, and maintain strict data flow ordering.

- [ ] T057 [US3] Add a final validation step in `run.sh` to verify that `results_summary.md` contains no hardcoded numbers and that all figures are generated from `data/processed/extracted_metrics.csv` (Single Source of Truth)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Integrity (Phase 7)**: Interleaved with implementation; T054 blocks T023, T056 blocks T043

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T016 (retrieval) for PDF URLs
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T029 (extracted_metrics.csv) for analysis

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services
- Services before endpoints/analysis
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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for API query logic in code/tests/test_retriever.py::test_query_logic_returns_valid_json"
Task: "Unit test for rate-limit retry logic in code/tests/test_retriever.py::test_rate_limit_retry_logic"

# Launch implementation tasks for User Story 1 together:
Task: "Implement code/services/retriever.py to query arXiv API"
Task: "Implement code/services/retriever.py to query Semantic Scholar API"
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
   - Developer A: User Story 1 (Retrieval)
   - Developer B: User Story 2 (PDF Parsing)
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