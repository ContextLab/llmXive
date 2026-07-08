# Implementation Plan: Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy

**Branch**: `001-code-complexity-bug-prediction` | **Date**: 2024-05-21 | **Spec**: [link]
**Input**: Feature specification from `specs/001-code-complexity-bug-prediction/spec.md`

## Summary

This project investigates the predictive power of static code complexity metrics (Cyclomatic Complexity, Halstead Volume, Lines of Code) on bug presence within Java projects. The approach involves ingesting a subset of the Defects4J dataset using the canonical framework, extracting metrics via static analysis on the *bug-introduction* state, and performing statistical correlation analysis and baseline classification modeling (Logistic Regression, Random Forest) using Repeated 5-Fold Cross-Validation. The plan strictly adheres to the project constitution's requirements for reproducibility, data hygiene, and statistical validation, while ensuring all computational tasks fit within the free-tier CI constraints (CPU-only, ≤7 GB RAM).

**CRITICAL BLOCKER**: This plan currently contains a methodological conflict with Constitution Principle VI (Statistical Validation Protocol). The Constitution mandates Pearson correlation and McNemar's test, while the Spec (FR-004, FR-006) and scientific best practices require Point-Biserial/Spearman and Paired Permutation Tests. **Execution is BLOCKED** until a formal amendment to the Constitution or a signed waiver is processed. The plan below details the intended methodology *pending* this resolution.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `pandas`, `scikit-learn`, `scipy`, `defects4j` (via CLI wrapper), `tree-sitter-java` (for metrics), `matplotlib`/`seaborn`.  
**Storage**: Local filesystem (CSV, Parquet), GitHub Actions cache for intermediate artifacts.  
**Testing**: `pytest` (unit tests for metric extraction, integration tests for pipeline), `pytest-cov` for coverage.  
**Target Platform**: Linux (GitHub Actions Runner), CPU-only.  
**Project Type**: Data Science / Research Pipeline (CLI scripts).  
**Performance Goals**: End-to-end pipeline execution ≤ 6 hours; peak memory usage ≤ 7 GB.  
**Constraints**: No GPU usage; no external API calls during execution; strict adherence to DefectsJ v2.0+ structure; statistical tests must be reproducible with fixed seeds.  
**Scale/Scope**: A small subset of Java projects from Defects4J; A variable number of source files depending on project size; binary classification task.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan mandates fixed seeds, pinned dependencies (`requirements.txt`), and deterministic data fetching from canonical Defects4J sources. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` will be restricted to the verified dataset URLs provided in the spec (Defects4J official repo). |
| **III. Data Hygiene** | PASS | Plan includes checksumming of raw data, immutable derivations, and logging of exclusions. |
| **IV. Single Source of Truth** | PASS | All metrics and results will be derived from `data/` artifacts; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | PASS | Artifacts will be hashed; plan ensures `state` updates are triggered by code execution. |
| **VI. Statistical Validation** | **BLOCKED** | **CONSTITUTIONAL CONFLICT**: Principle VI mandates 'Pearson correlation' and 'McNemar's test'. **Spec FR-004** requires **Point-Biserial** and **Spearman**. **Spec FR-006** requires **Paired Permutation Test**. <br> **ACTION REQUIRED**: Execution is HALTED. A formal amendment to the Constitution or a signed waiver from the governing body is required to proceed with the Spec-compliant methods. The plan below assumes this amendment will be granted. |
| **VII. Dataset Scope** | PASS | Plan limits ingestion to 5-10 projects to ensure ≤7 GB RAM usage. |

## Pending Amendment Request

**Request ID**: AMEND-001-STATS
**Target**: Constitution Principle VI
**Proposed Change**: Replace "Pearson correlation tests" with "Point-Biserial and Spearman Rank Correlation tests" for binary/non-normal data. Replace "McNemar's test" with "Paired Permutation Test" for ROC-AUC comparison in Repeated CV.
**Justification**: Pearson is inappropriate for binary targets; McNemar's test is invalid for ROC-AUC comparisons across Repeated CV folds. The Spec mandates these scientifically superior methods.
**Status**: Pending Review.

## Project Structure

### Documentation (this feature)

```text
specs/001-code-complexity-bug-prediction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── raw/             # Downloaded Defects4J subset (via CLI)
│   ├── processed/       # features.csv, labels.csv
│   └── checksums.json   # Integrity verification
├── src/
│   ├── __init__.py
│   ├── ingest.py        # Data download and project selection (via defects4j CLI)
│   ├── metrics.py       # Static analysis (tree-sitter)
│   ├── labeling.py      # Bug label assignment logic (bug-introduction state)
│   ├── analysis.py      # Correlation and statistical tests
│   ├── modeling.py      # ML training and evaluation
│   └── viz.py           # Plot generation
├── tests/
│   ├── test_metrics.py
│   ├── test_labeling.py
│   └── test_pipeline.py
├── requirements.txt
└── run_pipeline.sh      # Orchestration script

data/
└── (symlink or copy to code/data for execution)
```

**Structure Decision**: Single project structure (`code/`) is selected to simplify the research pipeline execution and dependency management. The `data/` directory is kept distinct but accessible within the execution context.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Paired Permutation Test** | Required by Spec US-3 and FR-006 to validate statistical significance of model differences on the *same* test folds (ROC-AUC). | Standard t-test assumes normality; McNemar's is for confusion matrices, not ROC-AUC. |
| **Repeated 5-Fold CV** | Required by Spec US-2 to reduce variance in performance estimates. | Single 5-fold CV has high variance; Multiple repeats ensure stable baseline metrics. |
| **Static Analysis Toolchain** | Required by Spec FR-002 to compute Halstead and Cyclomatic complexity accurately. | Heuristic counting (e.g., regex) is unreliable for complex Java syntax. |
| **Nested CV for Metric Selection** | Required to prevent selection bias (double-dipping) when comparing 'Full' vs 'Single Best' models. | Selecting the 'best' metric on the full dataset before splitting invalidates the test. |