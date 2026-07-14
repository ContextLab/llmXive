---
description: "Task list template for feature implementation"
id: "TASKS-001"
---

# Tasks: Statistical Analysis of Code Complexity Metrics and Bug Prediction

**Input**: Design documents from `/specs/001-statistical-analysis-of-code-complexity/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: All user stories must have concrete, required test tasks (no OPTIONAL flag).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] T### [P?] [Story] Description (file path)`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 0: Contracts & Schemas (Foundational Artifacts)

- [X] T040 Create dataset contract schema (`contracts/dataset.schema.yaml`)
- [X] T041 Create model output contract schema (`contracts/model_output.schema.yaml`)
- [X] T042 Author data‑model design document (`data-model.md`)
- [X] T043 Write quickstart guide (`quickstart.md`)
- [X] T044 Update Implementation Strategy section to map high‑level steps to task IDs (`README.md` or `docs/implementation_strategy.md`)
- [X] T045 Contract test for bug‑label reliability validation script (`tests/contract/test_bug_label_validation.py`)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory layout (`code/`, `data/`, `tests/`, `requirements.txt`, `README.md`)
- [X] T002 Initialize a Python 3.11 project and add pinned dependencies (`requirements.txt`) – pandas, scikit‑learn, lizard, statsmodels, matplotlib, seaborn, pymer4, pytest, black, flake8
- [X] T003 [P] Configure linting and formatting tools (`pyproject.toml`, `.flake8`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004 Create configuration module with random seed handling (`code/utils/config.py`)
- [X] T005 [P] Implement a reusable logging utility (`code/utils/logging.py`)
- [X] T006 [P] Add a small helper for reproducible data‑hashing and checksum verification (`code/utils/checksum.py`)
- [X] T050 [US1] Implement fallback handling for lizard parse failures – skip unparsable files, log warnings, and continue (`code/data/extract_metrics.py`)
- [X] T051 [US1] Implement memory‑aware, chunked processing of source files to stay within a modest RAM limit (`code/data/extract_metrics.py`)

**Checkpoint**: Foundation ready – user story implementation can now begin

---

## Phase 3: User Story 1 – Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Build a reproducible pipeline that downloads ≥10 Java projects from GHTorrent, extracts code units, computes ≥5 complexity metrics with lizard, labels bug‑fix occurrences, cleans the data, and creates a stratified train/test split.

**Independent Test**: Verify {{claim:c_8e4fd4a9}}, {{claim:c_1e836ca4}}, a binary `bug_label` column, and that the train/test split respects project‑level stratification with a [deferred]/30 % split.

### Required Contract & Integration Tests

- [X] T008 [US1] Contract test for dataset schema (`tests/contract/test_dataset_schema.py`)
- [X] T009 [US1] Integration test for end‑to‑end data pipeline (`tests/integration/test_data_pipeline.py`)

### Implementation for User Story 1

- [X] T010 [US1] Download GHTorrent Java project list and archives, enforce ≥10 projects (`code/data/download_gh.py`)
- [X] T011 [US1] Extract Java source files and commit metadata (`code/data/extract_commits.py`)
- [X] T012 [US1] Compute complexity metrics with lizard (cyclomatic complexity, LOC, token count, nesting depth, Halstead volume) (`code/data/extract_metrics.py`)
- [X] T013 [US1] Label bug‑fix vs. non‑bug‑fix units using commit messages & issue IDs (`code/data/label_bug_fixes.py`)
- [X] T014 [US1] {{claim:c_56d7c5ab}} (`code/data/validate_bug_labels.py`)
- [X] T015 [US1] Preprocess: impute <5 % missing values, log‑transform metrics with skewness >2, remove rows with >5 % missing (`code/data/preprocess.py`)
- [X] T049 [US1] Integrate bug‑label reliability validation into the data pipeline and enforce precision ≥ 85 % (fail pipeline if precision < 85 %) (`code/data/preprocess.py`)
- [X] T052 [US1] Document split proportions ([deferred] train / [deferred] test) and embed in pipeline configuration (`code/data/split_dataset.py`)
- [X] T016 [US1] Perform project‑level stratified train/test split and save splits (`code/data/split_dataset.py`)
- [X] T017 [US1] Add validation that each project appears in only one split (assertion in `split_dataset.py`)

**Checkpoint**: User Story 1 fully functional and testable independently

---

## Phase 4: User Story 2 – Statistical Modeling and Metric Selection (Priority: P2)

**Goal**: Fit a primary predictive model (L1‑regularized logistic regression), an alternative model (Random Forest), extract variable importance, and compare model performance.

**Independent Test**: Primary model converges within 100 iterations and yields at least one non‑zero coefficient; alternative model achieves ROC‑AUC within ±0.05 of the primary model on the held‑out test set; Spearman rank correlation of feature rankings ≥ 0.7.

### Required Contract & Integration Tests

- [X] T018 [US2] Contract test for model output schema (`tests/contract/test_model_output_schema.py`)
- [X] T019 [US2] Integration test for training pipeline (`tests/integration/test_training_pipeline.py`)

### Implementation for User Story 2

- [X] T053 [US2] Perform collinearity diagnostics (e.g., VIF) on the metric set and drop/reduce highly collinear features before modeling (`code/modeling/collinearity.py`)
- [X] T054 [US2] Contract test for collinearity diagnostics output (`tests/contract/test_collinearity.yaml`)
- [X] T020 [US2] Train primary L1‑logistic regression on training split, enforce ≤100 iterations and assert at least one non‑zero coefficient (`code/modeling/train_primary.py`)
- [X] T021 [US2] Train alternative Random Forest (a sufficient number of trees, max depth 10) and assert ROC‑AUC within ±0.05 of primary (`code/modeling/train_alternative.py`)
- [X] T022 [US2] Extract and store coefficient vectors / feature importances (`code/modeling/importance.py`)
- [X] T023 [US2] Compare ROC‑AUC of both models, compute Spearman rank correlation ≥ 0.7, and assert the tolerance (`code/modeling/compare_models.py`)
- [X] T024 [US2] Persist model artifacts and evaluation metrics (`data/model/primary.pkl`, `data/model/alternative.pkl`)

**Checkpoint**: User Story 2 independently functional and testable

---

## Phase 5: User Story 3 – Evaluation, Inference, and Reporting (Priority: P3)

**Goal**: Evaluate model performance, apply multiple‑hypothesis correction, generate partial dependence plots for the top 3 metrics, and produce a threshold table for developers.

**Independent Test**: ROC‑AUC, PR‑AUC computed and ROC‑AUC ≥ 0.50 baseline; false‑discovery rate ≤ 0.05 after correction; PDPs for top‑3 metrics saved as PNG (Wikidata Q178051, https://www.wikidata.org/wiki/Q178051); thresholds CSV created; Spearman correlation already validated.

### Required Contract & Integration Tests

- [X] T025 [US3] Contract test for evaluation metrics (`tests/contract/test_evaluation_metrics.py`)
- [X] T026 [US3] Contract test asserting baseline ROC‑AUC ≥ 0.50 **and that model ROC‑AUC exceeds this baseline** (`tests/contract/test_baseline_roc_auc.py`)
- [X] T027 [US3] Contract test asserting FDR ≤ 0.05 **after Benjamini–Hochberg correction** (`tests/contract/test_fdr.py`)

### Implementation for User Story 3

- [X] T028 [US3] Evaluate ROC‑AUC, PR‑AUC, and calibration plots; assert ROC‑AUC ≥ 0.50 baseline (`code/modeling/evaluate.py`)
- [X] T029 [US3] Apply multiple‑hypothesis testing correction (Benjamini–Hochberg), output `data/model/corrected_pvalues.csv`, **record the resulting FDR and assert ≤ 0.05** (`code/modeling/correct_pvalues.py`)
- [X] T030 [US3] Generate partial dependence plots for the three most important metrics (`code/modeling/pdp.py`)
- [X] T031 [US3] Derive practical threshold values (predicted bug probability ≥ 0.5) and write `thresholds.csv` (`code/modeling/generate_thresholds.py`)
- [X] T032 [US3] Assemble a concise research report (PDF/HTML) with tables, plots, and interpretation (`code/report/generate_report.py`)

**Checkpoint**: All user stories now independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 Update README with usage instructions, data source citations, and reproducibility notes (`README.md`)
- [X] T034 Add detailed documentation for each pipeline stage (`docs/data_pipeline.md`, `docs/modeling.md`)
- [X] T035 Code cleanup and refactoring (see subtasks T055‑T057) (`code/`)
- [X] T055 Run black on the entire `code/` directory and verify no formatting violations (`code/`)
- [X] T056 Run flake8 on the entire `code/` directory and verify PEP8 compliance (`code/`)
- [X] T057 Manually remove dead code and verify no import errors (`code/`)
- [X] T036 Add additional unit tests for utility modules (`tests/unit/test_utils.py`)
- [X] T037 Performance optimization: cache lizard metric results to avoid re‑parsing unchanged files (`code/data/cache_metrics.py`)
- [X] T038 Security hardening: ensure downloaded archives are checksum‑verified before extraction (`code/data/download_gh.py`)
- [X] T039 Run full test suite and enforce coverage ≥ 85 % (`pytest`, `coverage`)

### Documentation & Deliverables

- [X] T040 (moved to Phase 0) <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
- [X] T041 (moved to Phase 0) <!-- FAILED: unspecified -->
- [X] T042 (moved to Phase 0) <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T043 (moved to Phase 0)
- [X] T044 (moved to Phase 0)
- [X] T045 (moved to Phase 0) <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

### New Tasks

- [X] T060 Update spec to replace “[deferred]” placeholders with concrete [deferred]/30 % train/test split proportions (`specs/001-statistical-analysis-of-code-complexity/spec.md`)
