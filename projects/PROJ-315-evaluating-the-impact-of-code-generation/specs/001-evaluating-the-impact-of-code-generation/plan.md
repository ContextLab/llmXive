# Implementation Plan: Evaluating the Impact of Code Generation on Code Review Quality

**Branch**: `001-evaluating-llm-code-review-impact` | **Date**: 2025-01-15 | **Spec**: `spec.md`

## Summary

This project implements a statistical analysis pipeline to evaluate whether **Pull Requests (PRs) containing LLM-associated keywords** in commit messages receive different code review feedback (comment depth, sentiment, merge time) compared to PRs without such keywords. 

**Critical Scope Adjustment**: Due to the lack of ground-truth labels for "LLM-generated" code in available public datasets, the analysis targets "Keyword-Associated" PRs as a proxy. The plan includes a **Manual Audit & Calibration** phase to quantify misclassification rates and adjust power calculations accordingly. 

**Methodological Note on Complexity**: While code complexity is theoretically a mediator (mechanism of effect) and controlling for it statistically can introduce collider bias, **FR-010 explicitly mandates** the execution of a linear regression model controlling for complexity metrics and reporting VIFs. To satisfy the Spec while maintaining statistical integrity, the pipeline will:
1. Perform the **Mann-Whitney U tests** as the primary analysis (non-parametric, robust).
2. Execute the **Linear Regression with VIF diagnostics** as a **Spec-Compliance Step** to satisfy FR-010.
3. In the final report, present the regression results but explicitly frame the interpretation with the caveat that complexity is a mediator, ensuring findings are not over-interpreted as causal effects of code origin alone.

The approach involves loading a verified GitHub PR dataset, classifying PRs using commit message heuristics, computing code complexity metrics, and performing the required statistical tests with family-wise error correction. All analysis is designed to run on CPU-only CI (2 cores, 7 GB RAM) within 6 hours.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scikit-learn, scipy, radon, textblob, matplotlib, seaborn, datasets (HuggingFace), pyyaml  
**Random Seeds**: Pinned to **42** in **numpy, pandas, and scikit-learn** libraries to ensure reproducibility.  
**Storage**: Local parquet files in `data/`, processed CSV/parquet in `data/processed/`  
**Testing**: pytest (unit tests for classification logic, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data analysis / Research pipeline  
**Performance Goals**: Complete analysis of up to 50,000 PRs in ≤6 hours; memory usage ≤7 GB  
**Constraints**: No GPU, no deep learning training, no external API calls during analysis (except dataset fetch), deterministic random seeds  
**Scale/Scope**: Up to 50,000 PRs; requires ≥500 Keyword-Associated and ≥500 Human PRs for statistical power (adjusted for expected label noise).

**Pipeline Components**:
1. **Data Fetch**: `code/data/fetch.py` - Downloads dataset.
2. **Preprocessing**: `code/data/preprocess.py` - Cleans and computes metrics.
3. **Classification**: `code/labeling/classify.py` - Applies keyword heuristics to assign "Keyword-Associated" or "Human" labels.
4. **Hashing**: `code/utils/hash_artifacts.py` - **Invoked automatically** after `preprocess.py` and `stats.py` to compute and record content hashes in the state file (Constitution Principle V).
5. **Analysis**: `code/analysis/stats.py` - Mann-Whitney U tests, **Linear Regression with VIF diagnostics (Spec Compliance)**, descriptive complexity stats.
6. **Visualization**: `code/analysis/viz.py` - Boxplots, sensitivity analysis.
7. **Reporting**: `code/report/generate.py` - Final report.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| I. Reproducibility | ✅ | Random seeds pinned to **42** in **numpy, pandas, scikit-learn**; dataset fetch from canonical HuggingFace URLs; `requirements.txt` pins versions. |
| II. Verified Accuracy | ✅ | All dataset URLs cited are from the verified list; no external citations added without validation. |
| III. Data Hygiene | ✅ | Raw data checksummed; derivations written to new files; PII scan enabled. |
| IV. Single Source of Truth | ✅ | All statistics trace to `data/processed/` rows; no hand-typed numbers in reports. |
| V. Versioning Discipline | ✅ | **`code/utils/hash_artifacts.py` is invoked** after data and stats steps to record content hashes in state file; artifact changes trigger timestamp updates. |
| VI. Provenance & Labeling Accuracy | ✅ | Labeling logic is stored in **`code/labeling/classify.py`** and invoked as a primary step in the pipeline; keyword thresholds (≥2) documented and reproducible. |
| VII. Statistical Rigor | ✅ | Mann-Whitney U tests (primary); Benjamini-Hochberg correction; **Linear Regression with VIF executed for FR-010 compliance** (with mediator bias caveat in interpretation); Power analysis adjusted for label noise. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-llm-code-review-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── fetch.py           # Downloads dataset from HuggingFace
│   └── preprocess.py      # Cleans, classifies, computes metrics
├── labeling/
│   └── classify.py        # Heuristic classification (keyword matching)
├── analysis/
│   ├── stats.py           # Mann-Whitney U, Linear Regression (VIF), descriptive stats
│   └── viz.py             # Boxplots, sensitivity analysis
├── report/
│   └── generate.py        # Final report generation
├── utils/
│   └── hash_artifacts.py  # Computes and records checksums (Constitution V)
├── tests/
│   ├── test_classify.py
│   └── test_stats.py
└── requirements.txt

data/
├── raw/                   # Original parquet files
└── processed/             # Cleaned, classified, metric-enriched data

docs/
└── reports/               # Final PDF/HTML reports
```

**Structure Decision**: Single-project structure chosen to simplify data flow and reproducibility. All code resides under `code/`, data under `data/`, and reports under `docs/`. This aligns with the constitution’s requirement for traceability and checksummed artifacts.

## Complexity Tracking

No violations detected. The plan adheres to all constitutional principles without requiring unjustified complexity.