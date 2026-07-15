# Tasks: Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy

**Input**: Design documents from `/specs/001-code-complexity-bug-prediction/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, constitutional compliance, and basic structure

- [ ] T000a [S] Generate `methodology_rationale.md` artifact to document the conflict between Constitution Principle VI (Pearson/McNemar) and the Spec's required methods (Point-Biserial/Spearman/Paired Permutation), providing the scientific justification for the deviation as per the plan's 'Pending Amendment Request'. This task is a prerequisite for all statistical tasks and must be completed before Phase 2.
- [ ] T001a [P] Create project directory structure: `code/`, `code/src/`, `code/tests/`, `code/data/raw/`, `code/data/processed/`, `code/data/results/`, `specs/001-code-complexity-bug-prediction/`.
- [X] T001b [P] Create empty skeleton files: `code/src/__init__.py`, `code/tests/__init__.py`, `code/run_pipeline.sh`, `code/requirements.txt`, `code/pyproject.toml`.
- [ ] T001c [P] Initialize Python 3.11 virtual environment. <!-- FAILED: unspecified -->
- [X] T002a [P] Create `code/requirements.txt` with pinned versions: `pandas==2.1.0`, `scikit-learn==1.3.0`, `scipy==1.11.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `tree-sitter==0.20.0`, `tree-sitter-java==0.20.0`, `pytest==7.4.0`. (Note: `defects4j` CLI and PMD are installed separately in T002c).
- [X] T002b [P] Configure `code/pyproject.toml` with project metadata, entry points for scripts, and dependency groups.
- [X] T002c [P] Create `code/setup_cli.sh` script to install and configure the `defects4j` CLI tool and PMD (Java static analysis tool) via `apt` or `wget`, verifying availability via `defects4j --version` and `pmd --version`.
- [X] T002d [P] Configure linting (flake8) and formatting (black) tools in `code/pyproject.toml` or separate config files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Implement `code/src/config.py` to define environment variables for Defects4J path, fixed random seeds, and memory limits.
- [X] T004 [P] Implement `code/src/ingest.py` logic to download Defects4J v2.0+ subset via CLI wrapper, validating size < 7GB, and including dynamic subset validation logic to iteratively select projects until the RAM limit is reached.
- [X] T005 [P] Define metric extraction interface in `code/src/metrics.py`: Specify function signatures for calculating Cyclomatic Complexity (via PMD CLI), Halstead Volume (via custom JavaParser-based script), and LOC. The interface must support both tools.
- [~] T006 [P] Define labeling interface in `code/src/labeling.py`: Specify function signatures for mapping Defects4J bug-introduction commits to file-level binary labels.
- [X] T007 [P] Create `code/data/processed/features.csv` schema validator and checksum generator (`code/data/checksums.json`).
- [X] T008 [P] Create skeleton `code/run_pipeline.sh` orchestration script to enforce execution order (Ingest -> Metrics -> Labeling -> Analysis), noting that Analysis scripts are not yet implemented.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Metric Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest a subset of Defects4J Java projects and compute a labeled feature matrix (metrics + bug label).

**Independent Test**: The pipeline produces a `features.csv` where rows = valid Java files, columns include metrics and binary target, with no nulls in numeric columns.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/src/ingest.py` logic to clone a representative sample of projects, filter for `.java` files, and enforce a bounded RAM limit via dynamic subset validation.
- [X] T014 [US1] Implement `code/src/metrics.py` logic to traverse AST and compute LOC for every Java file.
- [~] T014b [US1] Implement Python wrapper script for PMD CLI integration to calculate Cyclomatic Complexity for every Java file.
- [ ] T014c [US1] Implement Python wrapper script for the custom JavaParser-based script to calculate Halstead Volume for every Java file.
- [ ] T015 [US1] Implement `code/src/labeling.py` logic to cross-reference commits with file changes to set `is_buggy` flag.
- [ ] T016 [US1] Implement exclusion logic in `code/src/ingest.py` for generated code/non-Java files with logging.
- [ ] T017 [US1] Generate `code/data/processed/features.csv` with columns: `file_path`, `cc`, `halstead`, `loc`, `is_buggy`.
- [ ] T018 [US1] Add validation step to ensure no NaN values in metric columns before saving CSV.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests AFTER implementation to verify the logic

- [ ] T010a [P] [US1] Unit test `test_cc_returns_int` in `code/tests/test_metrics.py` (mock Java file input).
- [ ] T010b [P] [US1] Unit test `test_halstead_returns_float` in `code/tests/test_metrics.py` (mock Java file input).
- [ ] T011a [P] [US1] Unit test `test_labeling_maps_commit_to_1` in `code/tests/test_labeling.py` (verify bug-introduction commit mapping).
- [ ] T012a [P] [US1] Integration test `test_pipeline_shape` in `code/tests/test_pipeline.py` (verify `features.csv` shape and content).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation Analysis and Baseline Modeling (Priority: P2)

**Goal**: Calculate correlations and train baseline models (Logistic Regression, Random Forest) using Repeated 5-Fold CV.

**Independent Test**: Analysis script outputs a report with Point-Biserial/Spearman correlations and mean ROC-AUC/F scores from multiple folds.

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/src/analysis.py` to compute Point-Biserial and Spearman correlations with p-values.
- [ ] T022 [US2] Implement `code/src/modeling.py` to train Logistic Regression with Repeated 5-Fold CV (10 repeats, seed=42), calculating ROC-AUC and F1-score.
- [ ] T023 [US2] Implement `code/src/modeling.py` to train Random Forest with Repeated 5-Fold CV (10 repeats, seed=42), calculating ROC-AUC and F1-score.
- [ ] T023a [US2] Implement `code/src/modeling.py` to train a 'Full Metric Set' Random Forest model specifically for the comparison in FR-006, ensuring it uses the same folds as the 'Single Best' model.
- [ ] T024 [US2] Implement aggregation logic to calculate mean ROC-AUC and F-score with standard deviation across 50 folds.
- [ ] T025 [US2] Handle class imbalance: Detect zero-buggy-file projects and log warnings/skip gracefully.
- [ ] T026 [US2] Generate `code/data/results/correlation_report.json` and `code/data/results/baseline_metrics.json`.
- [ ] T029 [US2] Implement `code/src/modeling.py` to extract feature importance weights from the trained Random Forest model (from T023) to identify the 'Single Best Metric'.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Statistical Significance (Priority: P3)

**Goal**: Identify feature importance and perform Paired Permutation Test to validate model differences.

**Independent Test**: Final report includes ranked feature importances and a p-value from the Paired Permutation Test.

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/src/modeling.py` to train a 'Single Best Metric' model (using only the top-ranked metric from T029) using Repeated 5-Fold CV to establish a baseline for comparison.
- [ ] T030 [US3] Implement `code/src/analysis.py` to collect predictions from 'Full Metric Set' model (T023a) and 'Single Best Metric' model (T027) on same folds.
- [ ] T031 [US3] Implement Paired Permutation Test in `code/src/analysis.py` comparing ROC-AUC distributions from T023a and T027 using a sufficient number of permutations to ensure statistical robustness.
- [ ] T032 [US3] Generate `code/data/results/feature_importance_ranking.json`.
- [ ] T033 [US3] Generate `code/data/results/statistical_significance_report.json` (including p-value).
- [ ] T034 [US3] Implement `code/src/viz.py` to create bar chart of ROC-AUC scores and table of correlations.
- [ ] T035 [US3] Compile final `code/results/final_report.md` summarizing all findings.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027b [P] [US3] Unit test for permutation test logic in `code/tests/test_analysis.py` (verify p-value calculation).
- [ ] T028 [P] [US3] Visualization test in `code/tests/test_viz.py` (verify bar chart generation).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates: Add `quickstart.md` with instructions to run `run_pipeline.sh`.
- [ ] T037 Code cleanup and refactoring (remove debug prints, ensure type hints).
- [ ] T039 [P] Additional unit tests for edge cases (empty projects, parsing errors) in `code/tests/unit/`.
- [ ] T040 Run quickstart.md validation to ensure end-to-end reproducibility.

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
- **User Story 2 (P2)**: Depends on US1 completion (needs `features.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (needs model predictions)

### Within Each User Story

- Implementation MUST be written BEFORE tests
- Ingestion/Labeling before Metrics
- Correlation before Modeling
- Modeling before Significance Testing

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (Metrics, Labeling) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement code/src/ingest.py logic..."
Task: "Implement code/src/metrics.py logic..."
Task: "Implement code/src/labeling.py logic..."

# Launch all tests for User Story 1 together (after implementation):
Task: "Unit test for metric extraction logic in code/tests/test_metrics.py"
Task: "Unit test for labeling logic in code/tests/test_labeling.py"
Task: "Integration test for full ingestion pipeline in code/tests/test_pipeline.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (including T000a Methodology Rationale)
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify `features.csv`)
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
 - Developer A: User Story 1 (Ingest/Metrics)
 - Developer B: User Story 2 (Correlation/Modeling)
 - Developer C: User Story 3 (Significance/Viz)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = sequential, must be done first
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint Check**: All tasks must run on CPU-only CI with a limited number of cores and memory.

The research question, method, and references remain unchanged as per the original planning document requirements. Do not use GPU-specific libraries or 8-bit quantization.
- **Statistical Note**: Execution is unblocked by T000a (Methodology Rationale) documenting the scientific justification for Point-Biserial/Spearman and Paired Permutation Tests.