# Implementation Strategy

This document maps the high‑level phases and steps of the **Statistical Analysis of Code Complexity** project to the concrete task identifiers defined in `tasks.md`. It serves as a navigation aid for developers and reviewers to understand which tasks implement each part of the overall workflow.

## Phase 0 – Contracts & Schemas (Foundational Artifacts)

| Step | Description | Task ID |
|------|-------------|---------|
| Create dataset contract schema | Defines the JSON/YAML schema for the processed dataset. | **T040** |
| Create model output contract schema | Defines the schema for model artifacts and evaluation results. | **T041** |
| Author data‑model design document | High‑level data model description. | **T042** |
| Write quickstart guide | Minimal guide to run the pipeline. | **T043** |

## Phase 1 – Project Setup (Shared Infrastructure)

| Step | Description | Task ID |
|------|-------------|---------|
| Create project directory layout (`code/`, `data/`, `tests/`, etc.) | Basic repo scaffolding. | **T001** |
| Initialise `requirements.txt` with pinned dependencies | pandas, scikit‑learn, lizard, statsmodels, matplotlib, seaborn, pymer4, pytest, black, flake8. | **T002** |
| Configure linting and formatting tools | `pyproject.toml`, `.flake8`. | **T003** |

## Phase 2 – Foundational (Blocking Prerequisites)

| Step | Description | Task ID |
|------|-------------|---------|
| Configuration module with random seed handling | `code/utils/config.py`. | **T004** |
| Reusable logging utility | `code/utils/logging.py`. | **T005** |
| Helper for reproducible data‑hashing & checksum verification | `code/utils/checksum.py`. | **T006** |
| Fallback handling for lizard parse failures | Skip unparsable files, log warnings. | **T050** |
| Memory‑aware, chunked processing of source files | Ensure modest RAM usage. | **T051** |

## Phase 3 – User Story 1: Data Acquisition & Pre‑processing

| Step | Description | Task ID |
|------|-------------|---------|
| Contract test for dataset schema | `tests/contract/test_dataset_schema.py`. | **T008** |
| Integration test for end‑to‑end data pipeline | `tests/integration/test_data_pipeline.py`. | **T009** |
| Download GHTorrent Java project list & archives | `code/data/download_gh.py`. | **T010** |
| Extract Java source files & commit metadata | `code/data/extract_commits.py`. | **T011** |
| Compute complexity metrics with lizard | `code/data/extract_metrics.py`. | **T012** |
| Label bug‑fix vs. non‑bug‑fix units | `code/data/label_bug_fixes.py`. | **T013** |
| Validate bug‑label reliability (precision ≥ 85 %) | `code/data/validate_bug_labels.py`. | **T014** |
| Preprocess: impute missing values, log‑transform, clean rows | `code/data/preprocess.py`. | **T015** |
| Integrate bug‑label reliability validation into pipeline | `code/data/preprocess.py`. | **T049** |
| Document split proportions & embed in config | `code/data/split_dataset.py`. | **T052** |
| Perform project‑level stratified train/test split | `code/data/split_dataset.py`. | **T016** |
| Validate each project appears in only one split | Assertion in `split_dataset.py`. | **T017** |

## Phase 4 – User Story 2: Statistical Modeling & Metric Selection

| Step | Description | Task ID |
|------|-------------|---------|
| Contract test for model output schema | `tests/contract/test_model_output_schema.py`. | **T018** |
| Integration test for training pipeline | `tests/integration/test_training_pipeline.py`. | **T019** |
| Collinearity diagnostics (VIF) and feature reduction | `code/modeling/collinearity.py`. | **T053** |
| Contract test for collinearity diagnostics output | `tests/contract/test_collinearity.yaml`. | **T054** |
| Train primary L1‑logistic regression | `code/modeling/train_primary.py`. | **T020** |
| Train alternative Random Forest model | `code/modeling/train_alternative.py`. | **T021** |
| Extract coefficient vectors / feature importances | `code/modeling/importance.py`. | **T022** |
| Compare ROC‑AUC of both models & compute Spearman rank correlation | `code/modeling/compare_models.py`. | **T023** |
| Persist model artifacts and evaluation metrics | `data/model/primary.pkl`, `data/model/alternative.pkl`. | **T024** |

## Phase 5 – User Story 3: Evaluation, Inference & Reporting

| Step | Description | Task ID |
|------|-------------|---------|
| Contract test for evaluation metrics | `tests/contract/test_evaluation_metrics.py`. | **T025** |
| Contract test asserting baseline ROC‑AUC ≥ 0.50 and improvement | `tests/contract/test_baseline_roc_auc.py`. | **T026** |
| Contract test asserting FDR ≤ 0.05 after BH correction | `tests/contract/test_fdr.py`. | **T027** |
| Evaluate ROC‑AUC, PR‑AUC, calibration plots | `code/modeling/evaluate.py`. | **T028** |
| Apply Benjamini–Hochberg correction & output corrected p‑values | `code/modeling/correct_pvalues.py`. | **T029** |
| Generate partial dependence plots for top‑3 metrics | `code/modeling/pdp.py`. | **T030** |
| Derive practical threshold values & write CSV | `code/modeling/generate_thresholds.py`. | **T031** |
| Assemble research report (PDF/HTML) with tables & plots | `code/report/generate_report.py`. | **T032** |

## Phase N – Polish & Cross‑Cutting Concerns

| Step | Description | Task ID |
|------|-------------|---------|
| Update README with usage instructions & reproducibility notes | `README.md`. | **T033** |
| Add detailed documentation for each pipeline stage | `docs/data_pipeline.md`, `docs/modeling.md`. | **T034** |
| Code cleanup & refactoring | `code/` (various). | **T035** |
| Run black on `code/` and verify no violations | `code/`. | **T055** |
| Run flake8 on `code/` and verify PEP8 compliance | `code/`. | **T056** |
| Remove dead code & verify no import errors | `code/`. | **T057** |
| Add additional unit tests for utility modules | `tests/unit/test_utils.py`. | **T036** |
| Cache lizard metric results to avoid re‑parsing unchanged files | `code/data/cache_metrics.py`. | **T037** |
| Verify downloaded archives via checksum before extraction | `code/data/download_gh.py`. | **T038** |
| Run full test suite & enforce coverage ≥ 85 % | `pytest`, `coverage`. | **T039** |

## Future Work

- Update spec to replace “[deferred]” placeholders with concrete train/test split proportions (`specs/001-statistical-analysis-of-code-complexity/spec.md`). **Task ID:** **T060**.

---

*This Implementation Strategy document is kept up‑to‑date as tasks are completed. The mapping provides a clear traceability matrix linking high‑level project milestones to the concrete development tasks defined in the project backlog.*