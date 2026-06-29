# Implementation Plan: Statistical Analysis of Code Complexity Metrics and Bug Prediction

**Branch**: `001-code-complexity-bug-prediction` | **Date**: 2025-01-15 | **Spec**: `specs/001-statistical-analysis-of-code-complexity/spec.md`
**Input**: Feature specification from `/specs/001-statistical-analysis-of-code-complexity/spec.md`

**Note**: This plan is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

This feature implements a statistical pipeline to analyze the relationship between code complexity metrics (cyclomatic complexity, LOC, etc.) and bug-fix occurrences in Java projects. The approach involves downloading source code from GHTorrent, computing metrics via `lizard`, labeling bug-fixes via commit history (using pre-fix snapshots), fitting predictive models (Logistic Regression L1, Random Forest, Mixed-Effects), and evaluating statistical significance with multiple hypothesis testing correction.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `lizard`, `statsmodels`, `matplotlib`, `seaborn`, `pymer4`  
**Storage**: Local CSV/Parquet files under `data/`  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier)  
**Project Type**: Data Analysis Pipeline  
**Performance Goals**: Complete pipeline ≤6h on 2 CPU / 7GB RAM  
**Constraints**: No GPU; CPU-only model training; data subset to fit RAM  
**Scale/Scope**: ≥10 Java projects, ≥10,000 code units, Multiple complexity metrics

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; external datasets fetched from canonical sources (GHTorrent mirrors); `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS (with caveat) | All citations validated; GHTorrent is unverified but checksummed (Principle III); alternative verified sources explored (research.md). |
| **III. Data Hygiene** | PASS | Raw data checksummed in `state/`; transformations produce new files; PII scan on commit. |
| **IV. Single Source of Truth** | PASS | Figures/statistics trace to `data/` rows and `code/` blocks; no hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | PASS | Artifacts carry content hashes; `state/` updated on artifact change. |
| **VI. Metric Computation Consistency** | PASS | `lizard` version pinned in `requirements.txt`; uniform CLI options applied to all codebases. |
| **VII. Bug‑Label Reliability** | PASS | Validation script cross-checks random samples against repo history; commit message parsing procedure documented. |

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-analysis-of-code-complexity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-148-statistical-analysis-of-code-complexity-/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download_gh.py          # FR-001
│   │   ├── extract_metrics.py      # FR-002
│   │   └── preprocess.py           # FR-003, FR-004
│   ├── modeling/
│   │   ├── train.py                # FR-005, FR-006
│   │   └── evaluate.py             # FR-007, FR-008, FR-009
│   └── utils/
│       ├── config.py               # Seeds, paths
│       └── logging.py
├── data/
│   ├── raw/                        # Downloaded archives (checksummed)
│   ├── processed/                  # Cleaned CSV/Parquet
│   └── splits/                     # Train/Test splits
├── tests/
│   ├── contract/                   # Validates contracts/dataset.schema.yaml, contracts/model_output.schema.yaml
│   ├── integration/
│   └── unit/
└── requirements.txt                # Pinned dependencies
```

**Structure Decision**: Single Python project under `code/` with separate `data/` for artifacts. This supports reproducibility (Principle I) and data hygiene (Principle III) by separating raw inputs from processed outputs.

## Data Flow (with Entity References)

1.  **Raw Ingestion**: Download GHTorrent archives to `data/raw/`.
2.  **Extraction**: Parse archives to extract code files and commit metadata → **CodeUnit** entity populated.
3.  **Metric Computation**: Run `lizard` on code files (pre-fix snapshots) → **ComplexityMetrics** entity populated.
4.  **Labeling**: Match commits to files; extract source attribution (commit/issue) → **BugLabel** entity populated.
5.  **Preprocessing**: Impute missing values (<5%), log-transform skewness >2, apply project-level stratification (ALL files from a project in one split) → FR-003, FR-004.
6.  **Model Input**: Join **CodeUnit**, **ComplexityMetrics**, **BugLabel** → `processed/dataset.csv`.
7.  **Output**: Model coefficients, importance scores, evaluation metrics → `data/output/`.

**Temporal Clarification**: Complexity metrics are computed on code snapshots BEFORE bug-fix commits to ensure predictor independence from outcome (addressing scientific_soundness-43382233).

**Stratification Clarification**: Project-level stratification means ALL files from a project go to either train OR test (not split within project) to prevent data leakage (addressing scientific_soundness-b45e165f).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **GHTorrent Data Fetch** | Spec requires ≥10 Java projects from GHTorrent. | No verified source in dataset block; requires external fetch logic which adds complexity but is mandated by spec. |
| **Dual Modeling Strategy** | Spec requires primary (L1 LogReg) + alternative (RF) for robustness. | Single model would fail FR-006 and SC-003 (stability check). |
| **Hypothesis Testing Correction** | Spec requires FDR control (FR-008). | Uncorrected p-values would violate statistical rigor (Assumptions). |
| **Mixed-Effects Model** | Code units within projects are correlated (methodology-a5c0e953). | Standard LogReg would inflate Type I error rates; mixed-effects required for valid inference. |
| **Label Validation** | Constitution Principle VII requires label reliability validation. | Manual audit of 100 samples required to confirm ≥85% precision assumption. |
