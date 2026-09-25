# Implementation Plan: Investigating the Correlation Between Code Churn and Technical Debt

**Branch**: `089-code-churn-debt` | **Date**: 2026-06-27 | **Spec**: [link]
**Input**: Feature specification from `specs/089-code-churn-debt/spec.md`

## Summary

This project investigates the statistical correlation between **code churn** (lines changed) and **technical debt** (static analysis scores) across open-source repositories. The primary technical approach involves cloning a curated set of Python, Java, and JavaScript/TypeScript repositories, extracting git history for churn metrics, running **Semgrep v1.30.0** for debt metrics, and performing a **Meta-analysis of Fisher-transformed slope coefficients** to aggregate results. 

**Methodological Correction**: To address statistical flaws regarding file size bias (spurious correlation), this study uses a **Log-Log Linear Model** (log(debt) ~ log(churn) + log(avg_loc)) as the primary analysis, with **Density Metrics** (debt/loc vs churn/loc) as a robustness check. This explicitly diverges from the Constitution's default Principle VI (Metric Normalization) and Principle VII (Static Analysis Consistency). A formal **Constitution Exception** is recorded in `data/logs/constitution_exception.log`.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `semgrep==1.30.0`, `pandas`, `scipy`, `statsmodels`, `gitpython`, `tqdm`, `pyyaml`  
**Storage**: Local file system (`data/raw`, `data/processed`); No external database.  
**Testing**: `pytest` (unit tests for metric extraction logic); Integration tests via `main.py` mock run.  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, ~7 GB RAM).  
**Project Type**: Data Pipeline / Statistical Analysis CLI.  
**Performance Goals**: Complete full pipeline (clone, analyze, aggregate) within 6 hours.  
**Constraints**: 
- CPU-first execution; no GPU required for statistical analysis.
- Memory usage < 7 GB (streaming git log and semgrep output).
- Strict adherence to Spec FR-001 (Raw Metrics) and FR-002 (Semgrep v1.30.0).
- **Sampling**: Limited to 30 repositories to guarantee 6h timeout.
**Scale/Scope**: 30 repositories (selected to fit 6h timeout); ~10k files total.

> **Note on Constitution Deviation**: The Spec (FR-001, FR-002) mandates **Raw Metrics** and **Semgrep**, which conflicts with Constitution Principle VI (Normalized Density) and Principle VII (SonarQube/CodeClimate). The Plan implements the Spec's requirements. A **Constitution Exception** is formally recorded in `data/logs/constitution_exception.log` to satisfy governance requirements.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Resolution / Exception |
|-----------|--------|-----------------------|
| I. Reproducibility | ✅ PASS | Pipeline uses pinned versions, deterministic seeds, and a pinned repo list. |
| II. Verified Accuracy | ⚠️ EXCEPTION | **Task T-VAL**: Implements simplified star-count check and logs to `data/logs/validation.log`. The full Reference-Validator Agent is out of scope; an exception is recorded. |
| III. Data Hygiene | ✅ PASS | Checksums recorded; raw data preserved. |
| IV. Single Source of Truth | ✅ PASS | All stats trace to `data/processed`. |
| V. Versioning Discipline | ✅ PASS | Artifacts hashed. |
| **VI. Metric Normalization** | ⚠️ EXCEPTION | **Spec FR-001** mandates **Raw Metrics** (Log-Log model) with `avg_loc` as covariate. A formal exception is recorded in `data/logs/constitution_exception.log`. |
| **VII. Static Analysis Consistency** | ⚠️ EXCEPTION | **Spec FR-002** mandates **Semgrep v1.30.0**. A formal exception is recorded in `data/logs/constitution_exception.log`. |

## Project Structure

### Documentation (this feature)

```text
specs/089-code-churn-debt/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-089-investigating-the-correlation-between-co/
├── code/
│   ├── main.py              # Orchestration entry point
│   ├── extraction.py        # Git history & Semgrep execution
│   ├── analysis.py          # Statistical models & Meta-analysis
│   ├── reporting.py         # Report generation
│   ├── utils.py             # Helper functions (validation, hashing)
│   └── requirements.txt     # Pinned dependencies
├── data/
│   ├── raw/
│   │   ├── repos_metadata.csv       # PINNED list of 30 repos
│   │   ├── git_history/             # Per-repo log files
│   │   └── static_analysis/         # Per-repo semgrep JSON
│   └── processed/
│       ├── unified_metrics.csv
│       ├── unified_metrics_loc5.csv # Sensitivity analysis (threshold 5)
│       ├── unified_metrics_loc10.csv # Sensitivity analysis (threshold 10)
│       ├── unified_metrics_loc20.csv # Sensitivity analysis (threshold 20)
│       ├── correlation_results.csv
│       └── meta_analysis_results.csv
├── data/logs/
│   ├── constitution_exception.log   # Records deviations from Principles VI, VII, II
│   └── validation.log               # Records simplified tool validation
└── tests/
    ├── test_extraction.py
    └── test_analysis.py
```

**Structure Decision**: Single-project structure. All logic contained in `code/` with data separated into `data/`. This minimizes overhead and fits the 6-hour CI constraint.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Log-Log Model (vs Raw + Covariate) | Raw metrics are statistically flawed for avoiding spurious correlation (Pearson). Log-Log model is the standard robust method. | Raw + Covariate was rejected by the Methodological Correction as insufficient. |
| Semgrep (vs SonarQube) | Spec FR-002 and SC-001 (feasibility) require a lightweight, fast tool; SonarQube is too heavy for 6h CI. | SonarQube requires heavy infrastructure and exceeds the 6h timeout. |
| Meta-analysis (vs Bonferroni) | Spec FR-006 mandates meta-analysis for better effect size aggregation. | Bonferroni is too conservative for heterogeneous data. |
| Pinned Repo List (vs Dynamic Selection) | Constitution Principle I requires reproducibility; dynamic selection introduces non-determinism. | Dynamic selection fails the reproducibility gate. |
