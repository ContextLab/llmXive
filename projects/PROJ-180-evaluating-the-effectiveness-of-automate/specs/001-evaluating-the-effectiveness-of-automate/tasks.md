# Tasks: Evaluating Automated Code Review Tools Effectiveness

**Input**: Design documents from `/specs/001-evaluating-code-review-tools/`
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

- [ ] T001a [P] Create `code/`, `data/raw`, `data/processed`, `results`, and `specs/` directories
- [ ] T001b [P] Create empty `__init__.py` and `config.yaml` files in `code/` and `data/` subfolders
- [ ] T002a [P] Create `requirements.txt` with pinned dependencies: `requests`, `pandas`, `scikit-learn`, `statsmodels`, `pygithub`, `tqdm`, `sentence-transformers`, `networkx`, `pytest`
- [ ] T002b [P] Initialize git repository and virtual environment (venv) <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 [P] Create `code/versions.yaml` with pinned versions for SonarQube Scanner, DeepSource CLI, and CodeClimate Engine (as per Plan Constitution VI)
- [X] T004b [P] Update `code/versions.yaml` to pin the `sentence-transformers` model `all-MiniLM-L6-v2` with its specific commit hash or tag (Constitution Principle VI)
- [~] T005 [P] Implement `code/utils/hasher.py` for SHA-256 artifact hashing (Constitution Principle V)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T006 Implement `code/utils/github_client.py` with authenticated GitHub REST API client (handling rate limits and pagination)
- [~] T007 Create `code/utils/stats.py` containing utility functions for Wilcoxon tests, VIF calculation, and Mixed-Effects regression wrappers (scipy/statsmodels)
- [~] T008a [P] Implement skeleton/interface for AST-based diff matching logic in `code/utils/aligner.py`
- [~] T008b [P] Implement skeleton/interface for CPU-optimized embedding similarity function (using `all-MiniLM-L6-v2`) in `code/utils/aligner.py`
- [~] T009 Setup environment configuration management (load GitHub tokens, paths from `.env`)
- [~] T010 Implement data directory structure and checksum validation logic for `data/raw` and `data/processed`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection and Tool Execution Pipeline (Priority: P1) 🎯 MVP

**Goal**: Retrieve a representative set of open-source repositories, clone them, and execute static analysis tools to generate structured JSON reports.

**Independent Test**: Can be fully tested by running the pipeline on multiple sample repositories and verifying that JSON reports are generated for all tools without runtime errors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T011 [P] [US1] Create `tests/contract/test_repository_filter.py` with a failing test that asserts `filter_repos()` raises `ValueError` for invalid license types (Tests the *expected* interface defined in a stub file or module signature)
- [~] T012 [P] [US1] Integration test for Docker-based tool execution in `code/tests/test_acquisition.py` (mocked tool output)

### Implementation for User Story 1

- [~] T013 [US1] Implement `code/01_data_acquisition.py` to query GitHub API for a representative set of 30–40 repos stratified by language (Java, Python, JS, Go) and activity (FR-001)
- [~] T014 [US1] Implement PESTO filter logic (license, CI, issues) in `code/01_data_acquisition.py` before cloning (FR-002)
- [ ] T015 [US1] Implement repository cloning logic with error handling (retry 2x, log exclusion) in `code/01_data_acquisition.py`
- [ ] T016 [US1] Implement Docker wrappers in `code/01_data_acquisition.py` to execute SonarQube, DeepSource, CodeClimate (using `code/versions.yaml`)
- [ ] T017 [US1] Implement JSON report parsing and normalization for all three tools into a unified schema in `code/01_data_acquisition.py` (FR-003)
- [ ] T018 [US1] Add logic to handle repositories with no merged PRs (skip and log) and tool execution failures (FR-Edge Cases)
- [ ] T019 [US1] Save raw JSON reports to `data/raw/` with checksums and metadata (owner, language, commit hash)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Human Review Baseline and Issue Alignment (Priority: P2)

**Goal**: Extract defect annotations from PR comments, validate a sample to create a Gold Standard, and align tool issues with human annotations.

**Independent Test**: Can be fully tested by processing a single repository's PR comments, extracting defect tags, and verifying that at least 10% of comments are manually validated for annotation accuracy. This test must use mocked data simulating US1 output to ensure independence from the actual execution of US1.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Contract test for keyword heuristic extraction in `code/tests/test_baseline.py`
- [ ] T021 [P] [US2] Integration test for alignment logic (AST + semantic) in `code/tests/test_alignment.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/02_human_baseline.py` to fetch merged PR review comments via GitHub API
- [ ] T023 [US2] Implement keyword heuristics (bug, security, style) and semantic search (using `all-MiniLM-L6-v2`) to generate candidate defect set `data/processed/heuristic_candidates.json` (FR-004)
- [ ] T023b [US2] Implement expert manual validation logic for heuristic candidates: generate `data/processed/validated_heuristic_candidates.json` from `data/processed/heuristic_candidates.json` (FR-004, Plan Ground Truth Construction)
- [ ] T024a [US2] Implement 'Random Stream' sampling logic (independent of keywords) to select a stratified random sample of ≥500 code changes/comments from the full pool, generating `data/processed/validation_sample_ids.json` (SC-005, Plan Ground Truth Construction)
- [ ] T024b [US2] Implement expert manual validation for the random sample: generate `data/processed/validated_ground_truth.json` containing the ≥500 validated annotations (FR-004, SC-005)
- [ ] T025a [US2] Implement sensitivity analysis script `code/02_sensitivity.py` to sweep keyword thresholds (FR-012)
- [ ] T025b [US2] Execute `code/02_sensitivity.py` with range [0.1, 0.9] to generate `results/sensitivity_analysis.csv` (FR-012)
- [ ] T026 [US2] Implement Cohen's κ calculation on the expert-validated subset (from T023b and T024b) and save to `results/inter_rater_reliability.json` (schema: `{ "cohen_kappa": float }`) (FR-011)
- [ ] T028 [US2] Implement 'Union Ground Truth' construction: merge `data/processed/validated_heuristic_candidates.json` (T023b) and `data/processed/validated_ground_truth.json` (T024b) into `data/processed/ground_truth_union.json` (Plan Ground Truth Construction, FR-004)
- [ ] T027 [US2] Implement `code/03_alignment.py` to align tool issues (from T019) against `data/processed/ground_truth_union.json` (T028): Primary method is AST-based alignment; IF AST unavailable, fallback to diff-based or ±5 line tolerance as mandated by FR-005. (FR-005)
- [ ] T029a [US2] Generate validation status report for aligned pairs (matched/unmatched) and save to `data/processed/aligned_pairs.json` (FR-005)
- [ ] T029d [US2] Implement validation step to measure alignment accuracy on the expert-validated sample (T024b) using `data/processed/aligned_pairs.json` (T029a), generating `results/alignment_accuracy_report.json` (schema: `{ "accuracy": float }`) and verify ≥0.90 threshold (SC-005, FR-005). **BLOCKS T032**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Metrics Computation and Statistical Analysis (Priority: P3)

**Goal**: Compute precision, recall, and F1 scores, perform statistical tests, and fit regression models to identify project characteristic influences.

**Independent Test**: Can be fully tested by running the analysis on a sample dataset consisting strictly of mocked aligned pairs (no dependency on real US1/US2 execution) and verifying that precision/recall metrics and regression tables are generated as CSV/PNG artifacts.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Contract test for metrics calculation in `code/tests/test_metrics.py`
- [ ] T031 [P] [US3] Integration test for statistical analysis pipeline in `code/tests/test_metrics.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement `code/04_metrics.py` to calculate Precision, Recall, and F1 scores per tool/category by computing True Positives, False Positives, and False Negatives directly against `data/processed/ground_truth_union.json` (T028) (FR-006, SC-001)
- [ ] T033 [US3] Implement Wilcoxon signed-rank test for paired tool comparison within projects (FR-007)
- [ ] T033b [US3] Implement max-t permutation procedure to generate null distribution and calculate adjusted p-values for Family-Wise Error Rate (FWER) control across all hypothesis tests, saving to `results/fwer_adjusted_pvalues.csv` (schema: columns for all pairwise comparisons and p-values) (FR-008, FR-009)
- [ ] T034 [US3] Implement Mixed-Effects Linear Model (LMM) with project-level random effects (dependent variable: F1 score; independent variables: tool, language, project_size) to handle project-level clustering and avoid overfitting, generating `results/regression_summary.csv` (schema: coefficients, standard errors, p-values) (FR-008)
- [ ] T035 [US3] Implement VIF calculation for collinearity diagnostics (FR-008) and Ridge regression fallback if VIF > 5 (Plan Assumptions: Collinearity)
- [ ] T035b [US3] Apply FWER correction (from T033b) to the regression coefficients and Wilcoxon results, generating `results/corrected_statistical_summary.json` (FR-008, FR-009)
- [ ] T038 [US3] Generate CSV/PNG artifacts for metrics, regression tables, and plots (FR-010)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T040 [P] Update `README.md` with execution instructions and data flow diagram
- [ ] T041 Run `code/utils/hasher.py` to update `state/projects/PROJ-180-evaluating-the-effectiveness-of-automate.yaml` with current artifact hashes
- [ ] T042 Generate `results/verification_report.json` listing all checked CSV/PNG artifacts in `results/` and their status (PASS/FAIL) (FR-010)
- [ ] T043 {{claim:c_e2fb09cb}} (SC-003)
- [ ] T044 Verify memory usage of peak processes < 6 GB (SC-004)
- [ ] T045 Run quickstart.md validation (if exists)

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
- **Ground Truth**: The final ground truth is the UNION of validated heuristic candidates and validated random samples (T023b + T024b).