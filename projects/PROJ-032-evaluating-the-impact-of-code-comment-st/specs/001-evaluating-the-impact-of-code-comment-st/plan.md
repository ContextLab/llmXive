# Implementation Plan: Evaluating the Impact of Code Comment Style on Maintainability

**Branch**: `101-eval-comment-maintainability` | **Date**: 2024-05-24 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/101-eval-comment-maintainability/spec.md`

## Summary

This project evaluates the associational relationship between code comment style (readability, sentiment, density, and variance) and software maintainability proxies (code quality degradation, issue-linked bug rate) using a dataset of high-star Python repositories. The technical approach involves cloning repositories via identifiers, extracting comments using `tree-sitter`, computing metrics with `textstat` and `TextBlob`, analyzing git history for churn and a sampled `pylint`-based quality metric, and performing Multiple Linear Regression with robust controls. All operations are constrained to run on a CPU-only GitHub Actions free-tier runner (limited CPU, 7 GB RAM, 6 hours).

**CRITICAL STATUS**: The study is currently **BLOCKED** pending the addition of a verified URL for the `codeparrot/github-code` dataset to the project's `# Verified datasets` block. Execution cannot proceed until this gap is resolved.

## Technical Context

**Language/Version**: Python 3.9+  
**Primary Dependencies**: `datasets` (HuggingFace), `tree-sitter`, `tree-sitter-python`, `textstat`, `textblob`, `pylint`, `gitpython`, `scikit-learn`, `pandas`, `numpy`, `statsmodels` (for robust SE only)  
**Storage**: Local file system (temporary clones in `data/raw/`, processed CSVs in `data/processed/`)  
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Data analysis / Research pipeline  
**Performance Goals**: Complete 500-repo pipeline within 6 hours; peak RAM ≤ 7 GB  
**Constraints**: No GPU; no large model training; batch processing (max concurrent clones); strict memory limits; commit sampling for static analysis.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`; `requirements.txt` pins versions; dataset fetched from canonical HF source (once verified); full pipeline scripted. |
| **II. Verified Accuracy** | **BLOCKED** | The required dataset `codeparrot/github-code` is NOT in the `# Verified datasets` block. Execution cannot proceed until a verified URL is added or the spec is updated to use a verified dataset. |
| **III. Data Hygiene** | **PASS** | Raw data (clones) preserved; checksums recorded; derived data (metrics) written to new files; PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | All statistics traced to `data/processed/metrics.csv`; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | Content hashes used for artifacts; `state` YAML updated on changes. |
| **VI. Comment Quality Metrics** | **PASS** | `tree-sitter` for extraction, `textstat` for readability, `TextBlob` for sentiment as mandated. |
| **VII. Statistical Validity** | **PASS** | Multiple Linear Regression (via `scikit-learn`) with robust standard errors as mandated. Controls for LOC, Age, Complexity. FDR correction applied. |

## Project Structure

### Documentation (this feature)

```text
specs/101-eval-comment-maintainability/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── raw/             # Temporary git clones (deleted after processing)
│   └── processed/       # metrics.csv, analysis_results.json, validation_report.json
├── code/
│   ├── fetch.py         # Repository identification and cloning
│   ├── extract.py       # Comment extraction (tree-sitter)
│   ├── metrics.py       # Readability, sentiment, churn, quality metrics
│   ├── analysis.py      # Regression, correlation, sensitivity
│   └── utils.py         # Logging, batching, memory management, sampling
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt
```

**Structure Decision**: Single project structure with dedicated `data/` and `code/` directories to support the research pipeline flow (fetch -> extract -> metrics -> analyze).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Batch Cloning (Max)** | Required by FR-013 to stay under 7 GB RAM. | Parallel cloning of all samples would exceed memory and disk I/O limits. |
| **AST-based Extraction** | Required by FR-002 to avoid false positives from string literals. | Regex-based extraction is unreliable and fails the accuracy test (SC-002). |
| **Commit Sampling for Pylint** | Required to meet 6h runtime/7GB RAM constraints (scientific soundness). | Running full static analysis on all commits is computationally infeasible. |
| **Multiple Comparison Correction** | Required by FR-009 to control family-wise error rate. | Uncorrected p-values inflate false positives in multi-predictor analysis. |

## FR/SC Mapping

| ID | Requirement | Plan Phase/Step |
| :--- | :--- | :--- |
| **FR-001** | Fetch a substantial number of repositories and clone their history. | `fetch.py`: `get_candidates()` (HF ID), `clone_batch()` (git) |
| **FR-002** | Extract comments via tree-sitter | `extract.py`: `extract_comments_ast()` |
| **FR-003** | Flesch-Kincaid via textstat | `metrics.py`: `calc_readability()` |
| **FR-004** | Sentiment via TextBlob | `metrics.py`: `calc_sentiment()` |
| **FR-005** | Code churn via git log | `metrics.py`: `calc_churn()` |
| **FR-006** | Bug fix rate / Quality proxy | `metrics.py`: `calc_quality_rate()` (sampled pylint); `validate_metrics.py` (manual label N=50) |
| **FR-007** | Multiple Linear Regression | `analysis.py`: `run_regression()` (scikit-learn with robust SE) |
| **FR-008** | Associational framing | `analysis.py`: Report generation text; `report.md` |
| **FR-009** | Multiple-comparison correction | `analysis.py`: `apply_fdr_correction()` |
| **FR-010** | Sensitivity analysis (p=0.01, 0.05, 0.1) | `analysis.py`: `run_sensitivity()` (output to JSON array) |
| **FR-011** | Memory ≤ 7 GB | `fetch.py`: Batch size 10; `metrics.py`: Stream processing |
| **FR-012** | Runtime ≤ 6 hours | `ci.yml`: Timeout check; `metrics.py`: Commit sampling strategy |
| **FR-013** | Batch ≤ 10 clones | `fetch.py`: `clone_batch(limit=10)` |
| **FR-014** | Control for complexity | `analysis.py`: Include `cyclomatic_complexity`, `LOC`, `age` in model |
| **SC-001** | A set of repositories with history | `fetch.py`: `validate_count(target=500)` |
| **SC-002** | ≥95% metric accuracy | `validate_metrics.py`: Generate `validation_report.json` comparing automated vs. manual N=50 |
| **SC-003** | p < 0.05 (corrected) | `analysis.py`: `check_significance()` (neutral outcome allowed) |
| **SC-004** | Runtime ≤ 6h | `ci.yml`: Timeout check; `analysis.py`: `timeit` |
| **SC-005** | RAM ≤ 7 GB | `ci.yml`: Memory check; `fetch.py`: Batch control |

