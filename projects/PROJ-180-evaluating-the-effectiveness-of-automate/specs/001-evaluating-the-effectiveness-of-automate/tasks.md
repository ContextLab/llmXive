# Tasks: Evaluating Automated Code Review Tools Effectiveness

**Input**: Design documents from `/specs/001-evaluating-the-effectiveness-of-automate/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `results/` at repository root (per plan.md)
- Paths shown below assume single project - adjusted based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a-1 [P] Create directory `code/` (FR-001, Plan Structure)
- [X] T001a-2 [P] Create directory `data/raw/` (FR-001, Plan Structure)
- [X] T001a-3 [P] Create directory `data/processed/` (FR-001, Plan Structure)
- [X] T001a-4 [P] Create directory `results/` (FR-001, Plan Structure)
- [X] T001a-5 [P] Create directory `specs/` (FR-001, Plan Structure)
- [X] T001b [P] Create `config.yaml` in `code/` with default paths and environment placeholders (Constitution Principle III)
- [X] T002a [P] Create `requirements.txt` with pinned dependencies: `requests==2.31.0`, `pandas==2.1.0`, `scikit-learn==1.3.0`, `statsmodels==0.14.0`, `pygithub==2.1.0`, `tqdm==4.66.0`, `sentence-transformers==2.2.2`, `networkx==3.1`, `pytest==7.4.0`
- [X] T002b [P] Initialize git repository and create virtual environment (venv) in `code/` (Constitution Principle I)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 [P] Create `code/versions.yaml` with pinned versions for SonarQube Scanner, DeepSource CLI, and CodeClimate Engine (as per Plan Constitution VI)
- [X] T004b [P] Update `code/versions.yaml` to pin the `sentence-transformers` model `all-MiniLM-L6-v2` with its specific commit hash or tag (Constitution Principle VI)
- [X] T005 [P] Implement `code/utils/hasher.py` for SHA-256 artifact hashing (Constitution Principle V)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement `code/utils/github_client.py` with authenticated GitHub REST API client (handling rate limits and pagination)
- [X] T007 Create `code/utils/stats.py` containing utility functions for Wilcoxon tests, VIF calculation, and Mixed-Effects regression wrappers (scipy/statsmodels)
- [X] T008a-1 [P] Implement `align_ast(file_a, file_b)` function signature in `code/utils/aligner.py`
- [X] T008a-2 [P] Implement `align_diff(file_a, file_b)` function signature in `code/utils/aligner.py`
- [X] T008b-1 [P] Implement `get_embedding(text, model="all-MiniLM-L6-v2")` function signature in `code/utils/aligner.py`
- [X] T008b-2 [P] Implement `compute_similarity(emb1, emb2)` function signature in `code/utils/aligner.py`
- [X] T009 [P] Setup environment configuration management (load GitHub tokens, paths from `.env` and `code/config.yaml`)
- [X] T010 Implement data directory structure and checksum validation logic for `data/raw` and `data/processed`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection and Tool Execution Pipeline (Priority: P1) 🎯 MVP

**Goal**: Retrieve a representative set of open-source repositories, clone them, and execute static analysis tools to generate structured JSON reports.

**Independent Test**: Can be fully tested by running the pipeline on multiple sample repositories and verifying that JSON reports are generated for all tools without runtime errors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T011 [P] [US1] Create `tests/contract/test_repository_filter.py` with a failing test that asserts `filter_repos()` raises `ValueError` for invalid license types (Tests the *expected* interface defined in a stub file or module signature)
- [X] T012 [P] [US1] Integration test for Docker-based tool execution in `code/tests/test_acquisition.py` (uses MOCKED tool output from `tests/fixtures/mock_tool_report.json` for unit testing; does NOT satisfy FR-003 real execution)

### Implementation for User Story 1

- [X] T013-1 [US1] Implement `query_github_repos()` in `code/01_data_acquisition.py` to query GitHub API for a representative set of repos stratified by language (Java, Python, JS, Go) and activity (FR-001)
- [X] T013-2 [US1] Implement `filter_repos()` in `code/01_data_acquisition.py` to apply PESTO criteria (license, CI, issues) (FR-002)
- [X] T013-3 [US1] Implement `clone_repos()` in `code/01_data_acquisition.py` to clone filtered repos to `data/raw/`
- [X] T013-4 [US1] Save filtered repo list to `data/raw/repo_list.json` with schema {owner, name, language, stars, license} (Input for T043)
- [X] T015 [US1] Implement repository cloning logic with error handling (retry 2x, log exclusion) in `code/01_data_acquisition.py`
- [X] T016-1 [US1] Implement Docker wrapper for SonarQube Scanner in `code/01_data_acquisition.py` (using `code/versions.yaml`)
- [X] T016-2 [US1] Implement Docker wrapper for DeepSource CLI in `code/01_data_acquisition.py` (using `code/versions.yaml`)
- [X] T016-3 [US1] Implement Docker wrapper for CodeClimate Engine in `code/01_data_acquisition.py` (using `code/versions.yaml`)
- [X] T017-1 [US1] Implement SonarQube JSON report parser in `code/01_data_acquisition.py`
- [X] T017-2 [US1] Implement DeepSource JSON report parser in `code/01_data_acquisition.py`
- [X] T017-3 [US1] Implement CodeClimate JSON report parser in `code/01_data_acquisition.py`
- [X] T018 [US1] Add logic to handle repositories with no merged PRs (skip and log) and tool execution failures; Generates `data/raw/exclusion_log.json` with reasons for skipped repos (FR-Edge Cases)
- [X] T019 [US1] Save raw JSON reports to `data/raw/` with checksums and metadata (owner, language, commit hash); Generates `data/raw/tool_reports.json` with unified schema {tool, repo, issues[]} (FR-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Human Review Baseline and Issue Alignment (Priority: P2)

**Goal**: Extract defect annotations from PR comments, validate a sample to create a Gold Standard, and align tool issues with human annotations.

**Independent Test**: Can be fully tested by processing a single repository's PR comments, extracting defect tags, and verifying that at least 10% of comments are manually validated for annotation accuracy. This test must use mocked data simulating US1 output to ensure independence from the actual execution of US1.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for keyword heuristic extraction in `code/tests/test_baseline.py`
- [X] T021 [P] [US2] Integration test for alignment logic (AST + semantic) in `code/tests/test_alignment.py`

### Implementation for User Story 2

- [X] T022-1 [US2] Implement `fetch_pr_comments()` in `code/02_human_baseline.py` to fetch merged PR review comments via GitHub API
- [X] T022-2 [US2] Implement `parse_pr_comments()` in `code/02_human_baseline.py` to extract comment text and metadata; Generates `data/raw/pr_comments.json` with schema {repo_id, comment_id, text, file, line, timestamp} (FR-004)
- [X] T023 [US2] Implement keyword heuristics (bug, security, style) and semantic search (using `all-MiniLM-L-v`) to generate candidate defect set; Generates `data/processed/heuristic_candidates.json` with schema {comment_id, text, predicted_type, file, line} (FR-004)
- [X] T023b-Export [US2] Export heuristic candidates to `data/processed/heuristic_review_candidates.csv` for manual review (FR-004)
- [X] T023b-Review [US2] **HUMAN TASK**: Perform expert manual validation on `data/processed/heuristic_review_candidates.csv` and save validated results to `data/processed/validated_heuristic_candidates.csv` (FR-004, SC-005). Note: This step requires human expert input and is not automated by code.
- [X] T023b-Ingest [US2] Implement ingestion logic to load validated `data/processed/validated_heuristic_candidates.csv` and generate `data/processed/validated_heuristic_candidates.json` (FR-004, Plan Ground Truth Construction)
- [X] T024a [US2] Implement 'Random Stream' sampling logic (independent of keywords) to select a stratified random sample of ≥500 code changes/comments from `data/raw/pr_comments.json` (produced by T022), generating `data/processed/validation_sample_ids.json` and the 'Random Stream' candidate pool (SC-005, Plan Ground Truth Construction)
- [X] T024b-Export [US2] Export random sample to `data/processed/random_review_candidates.csv` for manual review (FR-004, SC-005)
- [X] T024b-Review [US2] **HUMAN TASK**: Perform expert manual validation on `data/processed/random_review_candidates.csv` and save validated results to `data/processed/validated_random_samples.csv` (FR-004, SC-005). Note: This step requires human expert input and is not automated by code.
- [X] T024b-Ingest [US2] Implement ingestion logic to load validated `data/processed/validated_random_samples.csv` and generate `data/processed/validated_random_samples.json` (FR-004, SC-005)
- [X] T025a [US2] Implement sensitivity analysis script `code/02_sensitivity.py` to sweep keyword thresholds [0.1, 0.2,..., 0.9] and generate `results/sensitivity_analysis.csv` (FR-012)
- [X] T025b [US2] Execute `code/02_sensitivity.py` with range [0.1, 0.9] to generate `results/sensitivity_analysis.csv` (FR-012)
- [X] T026 [US2] Implement Cohen's κ calculation on the expert-validated subset (from T023b-Ingest and T024b-Ingest) and save to `results/inter_rater_reliability.json` (schema: `{ "cohen_kappa": float }`) (FR-011)
- [X] T028 [US2] **RESEARCH TASK**: Merge `data/processed/validated_heuristic_candidates.json` (T023b-Ingest) and `data/processed/validated_random_samples.json` (T024b-Ingest) into `data/processed/ground_truth_union.json` (Plan Ground Truth Construction, FR-004). **This task requires manual curation to ensure the Union is correctly constructed and free of duplicates.**
- [X] T027-1 [US2] Implement full logic of `align_ast()` in `code/03_alignment.py` to align tool issues (from T019) against `data/processed/ground_truth_union.json` (T028) using AST-based alignment (FR-005)
- [X] T027-2 [US2] Implement full logic of `align_diff()` in `code/03_alignment.py` to fallback to diff-based or ±5 line tolerance if AST unavailable (FR-005)
- [X] T027-3 [US2] Generate validation status report for aligned pairs (matched/unmatched) and save to `data/processed/aligned_pairs.json` (FR-005)
- [X] T029d [US2] Implement validation step to measure alignment accuracy on the expert-validated sample (T024b-Ingest) using `data/processed/aligned_pairs.json` (T027-3), Generates `results/alignment_accuracy_report.json` (schema: `{ "accuracy": float }` where accuracy = matches / total_aligned_pairs) and verify ≥0.90 threshold (SC-005, FR-005). **BLOCKS T032**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Metrics Computation and Statistical Analysis (Priority: P3)

**Goal**: Compute precision, recall, and F1 scores, perform statistical tests, and fit regression models to identify project characteristic influences.

**Independent Test**: Can be fully tested by running the analysis on a sample dataset consisting strictly of mocked aligned pairs (no dependency on real US1/US2 execution) and verifying that precision/recall metrics and regression tables are generated as CSV/PNG artifacts.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Contract test for metrics calculation in `code/tests/test_metrics.py`; function `test_metrics_calculation_returns_correct_f1` asserts F1 calculation against known mock values and fails initially (expected assertion failure)
- [X] T031 [P] [US3] Integration test for statistical analysis pipeline in `code/tests/test_metrics.py`

### Implementation for User Story 3

- [X] T032-1 [US3] Implement `calculate_precision_recall()` in `code/04_metrics.py` to compute True Positives, False Positives, and False Negatives directly against `data/processed/ground_truth_union.json` (T028) and `data/processed/aligned_pairs.json` (T029d) (FR-006, SC-001)
- [X] T032-2 [US3] Implement `calculate_f1()` in `code/04_metrics.py` to compute F1 scores per tool/category (FR-006)
- [X] T033-1 [US3] Implement Wilcoxon signed-rank test for paired tool comparison within projects in `code/04_metrics.py` (FR-007)
- [X] T033-2 [US3] Implement p-value calculation for Wilcoxon tests (FR-007)
- [X] T033b [US3] Implement max-t permutation procedure to generate null distribution and calculate adjusted p-values for Family-Wise Error Rate (FWER) control across all hypothesis tests, saving to `results/fwer_adjusted_pvalues.csv` (schema: columns for all pairwise comparisons and p-values) (FR-008, FR-009)
- [X] T034-1 [US3] Implement Mixed-Effects Linear Model (LMM) fitting in `code/05_regression.py` (dependent variable: F1 score; independent variables: tool, language, project_size) (FR-008)
- [X] T034-2 [US3] Extract coefficients, standard errors, and p-values from LMM; generating `results/regression_summary.csv` (FR-008)
- [X] T035-1 [US3] Implement VIF calculation for collinearity diagnostics in `code/05_regression.py` (FR-008)
- [X] T035-2 [US3] Implement Ridge regression fallback if VIF > 5 (Plan Assumptions: Collinearity)
- [X] T035b [US3] Apply Bonferroni correction to the regression coefficients and Wilcoxon results, generating `results/corrected_statistical_summary.json` (FR-008, FR-009)
- [X] T038-1 [US3] Generate CSV artifacts for metrics and regression tables (FR-010)
- [X] T038-2 [US3] Generate PNG plots for metrics and regression diagnostics (FR-010)
- [X] T038-3 [US3] Generate final `results/metrics_report.json` summarizing all findings (FR-010)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T040-1 [P] Update `README.md` with project introduction and data flow diagram (FR-010)
- [X] T040-2 [P] Update `README.md` with execution instructions (FR-010)
- [X] T041-1 [P] Run `code/utils/hasher.py` to hash files in `data/` (Constitution Principle V)
- [X] T041-2 [P] Run `code/utils/hasher.py` to hash files in `code/` (Constitution Principle V)
- [X] T041-3 [P] Update `state/projects/PROJ-180-evaluating-the-effectiveness-of-automate.yaml` with current artifact hashes (Constitution Principle V)
- [X] T042-1 [P] Check CSV artifacts in `results/` for validity (FR-010)
- [X] T042-2 [P] Check PNG artifacts in `results/` for validity (FR-010)
- [X] T042-3 [P] Generate `results/verification_report.json` listing all checked artifacts and their status (PASS/FAIL) (FR-010)
- [X] T043 [US1] Run pipeline on a representative sample set (5 specific repos from `data/raw/repo_list.json` from T013-4, first 5 alphabetically), measure wall-clock time using `time` module or `subprocess`, and save results to `results/runtime_benchmark.json` (schema: `{ "total_time_seconds": float, "threshold_seconds": 19800 }`) to verify SC-003 (≤ 5.5 hours)
- [X] T044a-1 [US1] Implement memory instrumentation in `code/01_data_acquisition.py` using `tracemalloc` or `psutil` to capture peak memory usage during execution
- [X] T044a-2 [US1] Execute pipeline with instrumentation enabled, capture peak memory, and generate `results/memory_usage_report.json` to verify SC-004 (≤ 6 GB peak)
- [X] T045 Run quickstart.md validation (if exists)
- [X] T046 Reconcile run-book vs implementation for `code/02_human_annotation.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/02_human_annotation.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data (JSON reports) for alignment
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 (aligned pairs) for metrics

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
Task: "Contract test for repository filtering in code/tests/test_acquisition.py"
Task: "Integration test for Docker execution in code/tests/test_acquisition.py"

# Launch all models for User Story 1 together:
Task: "Implement GitHub API client in code/utils/github_client.py"
Task: "Implement Docker wrapper in code/01_data_acquisition.py"
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
- **CPU Constraint**: All tasks must run on CPU-only runners (no GPU, no 8-bit models). Use `all-MiniLM-L6-v2` for embeddings, not large LLMs.
- **Data Integrity**: No synthetic data. All metrics must be derived from real GitHub data and real tool outputs.
- **Ground Truth**: The final ground truth is the UNION of validated heuristic candidates and validated random samples (T023b-Ingest + T024b-Ingest). Human-in-the-loop validation is mandatory.