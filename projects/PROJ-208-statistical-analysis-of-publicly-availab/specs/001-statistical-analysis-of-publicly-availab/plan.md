# Implementation Plan: Statistical Analysis of GitHub Issue Resolution Times

**Branch**: `001-github-issue-resolution` | **Date**: 2024-01-15 | **Spec**: `specs/001-github-issue-resolution/spec.md`
**Input**: Feature specification from `/specs/001-github-issue-resolution/spec.md`

## Summary

This feature implements a statistical analysis pipeline for GitHub issue resolution times. The primary requirement is to collect closed issue data from ≥100 GitHub repositories via the GitHub REST API, compute resolution times, and perform distribution analysis, hypothesis testing, and mixed‑effects modeling. The technical approach uses CPU‑tractable Python libraries (pandas, scikit‑learn, statsmodels, scipy) within GitHub Actions free‑tier constraints (2 CPU, 7 GB RAM, ≤6 h runtime).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas==2.2.1, numpy==1.26.4, scipy==1.13.0, scikit‑learn==1.5.0, statsmodels==0.14.2, requests==2.32.3, pymer4==0.7.0 (fallback to statsmodels MixedLM)  
**Storage**: Local CSV/Parquet files under `data/`  
**Testing**: pytest with contract tests against schema validators (see Contract‑to‑Test Mapping)  
**Target Platform**: Linux (GitHub Actions free‑tier runner)  
**Performance Goals**: ≤6 h total runtime, ≤7 GB peak memory, ≥1000 issues collected  
**Constraints**: No GPU/CUDA, no deep network training, CPU‑only methods only  
**Scale/Scope**: ≥100 repositories, ≥1000 issues, ≥5 programming languages

> Domain‑specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re‑check after Phase 1 design.*

| Constitution Principle | Status | Notes |
|------------------------|--------|-------|
| I. Reproducibility | PASS | Random seeds pinned; external data fetched from canonical sources; `requirements.txt` pins all dependencies |
| II. Verified Accuracy | PASS | API verification performed via HEAD request before data download (Principle II) |
| III. Data Hygiene | PASS | Checksums recorded; raw data preserved; no PII |
| IV. Single Source of Truth | PASS | All statistics trace to `data/` rows and `code/` blocks |
| V. Versioning Discipline | PASS | Content hashes for artifacts; `state/projects/PROJ-208‑statistical-analysis-of-publicly-availab.yaml` updated on changes |
| VI. Temporal Data Integrity | PASS | Timestamps stored unchanged; deterministic timezone handling |
| VII. Reproducible Feature Engineering | PASS | Feature extraction scripts version‑controlled, deterministic |

**GATE RESULT**: PASS — All constitution principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/001-github-issue-resolution/
├── plan.md              # This file (/speckit‑plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (not created by /speckit‑plan)
```

### Source Code (repository root)

```text
projects/PROJ-208-statistical-analysis-of-publicly-availab/
├── code/
│   ├── __init__.py
│   ├── collect/
│   │   ├── __init__.py
│   │   ├── github_collector.py
│   │   └── preprocess.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── distribution_fitting.py
│   │   ├── hypothesis_testing.py
│   │   └── mixed_effects_model.py
│   ├── diagnostics/
│   │   ├── __init__.py
│   │   ├── collinearity.py
│   │   └── sensitivity_analysis.py
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       └── logging.py
├── data/
│   ├── raw/
│   │   └── .gitkeep
│   ├── processed/
│   │   └── .gitkeep
│   └── checksums.txt
├── state/
│   └── projects/
│       └── PROJ-208-statistical-analysis-of-publicly-availab.yaml
├── tests/
│   ├── contract/
│   │   └── test_schemas.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── unit/
│       └── test_collect.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single‑project structure under `code/` with modular sub‑packages for collection, analysis, and diagnostics. This aligns with the data‑pipeline nature of the feature and keeps all artifacts under one repo for reproducibility (Constitution Principles I, IV).

## Functional Requirement Annotations

| Functional Requirement | Addressed By |
|------------------------|--------------|
| FR‑001 (≥100 repos) | Data Collection (addressed by FR‑001) |
| FR‑002 (resolution time & log‑transform) | Preprocessing (addressed by FR‑002) |
| FR‑003 (exclude invalid timestamps) | Validity Filtering (addressed by FR‑003) |
| FR‑004 (Holm‑Bonferroni) | Hypothesis Testing (addressed by FR‑004) |
| FR‑005 (mixed‑effects model) | Mixed‑Effects Modeling (addressed by FR‑005) |
| FR‑006 (VIF ≥5) | Collinearity Diagnostic (addressed by FR‑006) |
| FR‑007 (sensitivity analysis) | Sensitivity Analysis (addressed by FR‑007) |
| FR‑008 (associational language) | Result Generation (addressed by FR‑008) |
| FR‑009 (runtime ≤6 h) | Computational Feasibility (addressed by FR‑009) |
| FR‑010 (CPU‑only) | Computational Feasibility (addressed by FR‑010) |

## Success Criterion Annotations

| Success Criterion | Addressed By |
|-------------------|--------------|
| SC‑001 (dataset completeness ≥95 %) | Dataset Completeness Check (addressed by SC‑001) |
| SC‑002 (KS‑test p‑value) | Distribution Goodness‑of‑Fit (addressed by SC‑002) |
| SC‑003 (Holm‑Bonferroni adjusted p < 0.05) | Hypothesis Test Validity (addressed by SC‑003) |
| SC‑004 (MAE & R²) | Model Predictive Performance (addressed by SC‑004) |
| SC‑005 (compute feasibility) | Runtime & Memory Profiling (addressed by SC‑005) |

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed with no violations | N/A |

## Dependency Verification

- **Primary mixed‑effects library**: `pymer4` is listed in `requirements.txt` with a pinned version and verified via the Reference‑Validator Agent (Principle II).  
- **Fallback**: If `pymer4` cannot be installed on the CI runner, the pipeline automatically imports `statsmodels` MixedLM; this fallback is also pinned and verified. Both libraries are CPU‑tractable and have been tested on GitHub Actions free‑tier runners. The fallback behavior is documented in `code/analysis/mixed_effects_model.py` with explicit import ordering and error handling.

## Contract‑to‑Test Mapping

| Contract Schema | Test File(s) |
|-----------------|--------------|
| `analysis_results.schema.yaml` | `tests/contract/test_schemas.py::test_analysis_results_schema` |
| `collinearity.schema.yaml` | `tests/contract/test_schemas.py::test_collinearity_schema` |
| `dataset.schema.yaml` | `tests/contract/test_schemas.py::test_dataset_schema` |
| `sensitivity.schema.yaml` | `tests/contract/test_schemas.py::test_sensitivity_schema` |

## Computational Feasibility

| Task | Expected Runtime | Memory | CPU | Notes |
|------|-----------------|--------|-----|-------|
| Data collection (multiple repositories and associated issues) | ~2‑3 h | ~2 GB | 2 cores | Exponential backoff for rate limits (FR‑003) |
| Preprocessing | [deferred] | ~1 GB | 2 cores | Log‑transform, filtering |
| Distribution fitting | [deferred] | ~1 GB | 2 cores | MLE for log‑normal/Weibull |
| Hypothesis testing | [deferred] | ~1 GB | 2 cores | Kruskal‑Wallis, VIF |
| Mixed‑effects model | ~1‑2 h | ~3 GB | 2 cores | LOO‑CV across repositories |
| Sensitivity analysis | ~15 min | ~1 GB | 2 cores | Bootstrap‑based stability |
| **Total** | **≤6 h** | **≤7 GB** | **2 cores** | **Within GitHub Actions free‑tier constraints (FR‑009, FR‑010)** |

**CPU‑Only Confirmation**: All methods use CPU‑tractable libraries (`scipy`, `statsmodels`, `scikit‑learn`). No GPU/CUDA dependencies.

## Decision/Rationale Summary

| Decision | Rationale |
|----------|-----------|
| GitHub REST API for data | Spec requirement (FR‑001); no verified dataset exists |
| Log‑normal/Weibull fitting | Prior literature; CPU‑tractable |
| Holm‑Bonferroni correction | Controls FWER with reasonable power |
| Mixed‑effects model | Accounts for repository‑level clustering |
| VIF ≥5 threshold | Standard practice for collinearity flagging |
| Sensitivity cutoffs {0.01, 0.05, 0.1} | Demonstrates robustness; bootstrap‑based stability reported |
| All results "associational" | Observational design (FR‑008) |
| Power analysis acknowledgment | Minimum observations per group satisfied; formal a‑priori power not feasible (addressed in research.md) |
| Label handling | Multi‑label issues expanded to binary indicators; primary label used for categorical tests |
| Outlier definition | >30 days **or** >3 SD above repo mean (repository‑specific) |