# Implementation Plan: Quantifying the Impact of Data Cleaning on Statistical Inference

**Branch**: `001-quantify-cleaning-impact` | **Date**: 2024-01-15 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-quantify-cleaning-impact/spec.md`

## Summary

This feature quantifies how data cleaning strategies (outlier removal, missing value imputation, data type correction) affect statistical inference metrics (p-values, confidence intervals, effect sizes). The system downloads verified public datasets, applies cleaning interventions, runs statistical tests (t-tests, linear regression), and compares results against baselines. The plan prioritizes CPU-tractable methods suitable for GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn
**Storage**: Local file system (`data/`, `code/`)
**Testing**: pytest
**Target Platform**: Linux (GitHub Actions free-tier)
**Project Type**: Data Analysis Pipeline / CLI
**Performance Goals**: ≤6 hours runtime, ≤7 GB RAM usage
**Constraints**: No GPU/CUDA; CPU-only statistical methods; bootstrap iterations capped for feasibility; verified dataset URLs only.
**Scale/Scope**: Multiple verified datasets (UCI HAR, UCI Shopper); sample sizes varying (n<50 to >200).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Plan Compliance Action |
|:--- |:--- |
| **I. Reproducibility** | All scripts in `code/` use pinned `requirements.txt`; random seeds set in `numpy`/`scipy`; external data fetched from verified URLs only. |
| **II. Verified Accuracy** | Citations in `research.md` validated by Reference-Validator Agent against primary sources; dataset URLs restricted to the `# Verified datasets` block. |
| **III. Data Hygiene** | Raw data downloaded to `data/raw/` with checksums; cleaned data written to `data/processed/`; no in-place modification. |
| **IV. Single Source of Truth** | All statistics in reports generated from `data/processed/` artifacts; no hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | Content hashes recorded for data artifacts; `state/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-.yaml` updated on artifact change. |
| **VI. Sensitivity & Variance** | Bootstrap variance estimates (≥1000 iterations, or jackknife for n<50) included for all metric shifts; sensitivity analysis by dataset size/missingness. |

## Spec Corruption Notice

The source `spec.md` contains corrupted text blocks unrelated to the cleaning-impact research question. These sections are **excluded** from this plan and flagged for kickback to spec author:

- **US-1**: Contains "Can transfer learning improve..." research question (irrelevant to cleaning)
- **FR-001**: Contains "Can LLMs generate data quality reports..." research question (irrelevant to cleaning)
- **FR-006**: Contains "Can we identify robust biomarkers for glioblastoma..." research question (irrelevant to cleaning)

The plan follows the Feature Title and FR-002 through FR-011 which correctly describe the data cleaning impact study.

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-cleaning-impact/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ └── analysis_result.schema.yaml
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py # Entry point
├── acquisition.py # Dataset download (verified URLs)
├── cleaning.py # Outlier/Imputation/Recoding logic
├── analysis.py # t-tests, regression, bootstrap
├── reporting.py # Visuals (forest plot, heatmap)
└── utils.py # Seed pinning, checksums

data/
├── raw/ # Downloaded datasets (checksummed)
└── processed/ # Cleaned variants

tests/
├── unit/ # Cleaning logic tests
└── integration/ # Full pipeline tests
```

**Structure Decision**: Single project structure selected. All analysis logic resides in `code/` to ensure reproducibility and single-source-of-traceability per Constitution Principle IV.

## FR & SC Coverage Map

| ID | Requirement | Plan Phase | Notes |
|:--- |:--- |:--- |:--- |
| **FR-001** | Download representative datasets | Phase 1 (Acquisition) | **Deviation**: OpenML has NO verified source; adapted to UCI HAR/Shopper only. Spec requires kickback. |
| **FR-002** | IQR outlier removal (k=1.5) | Phase 2 (Cleaning) | Log rows removed. |
| **FR-003** | Imputation (mean/median/KNN) | Phase 2 (Cleaning) | Validate zero missing values post-op. |
| **FR-004** | t-tests/linear regression | Phase 3 (Analysis) | Use `scipy.stats`/`statsmodels`. |
| **FR-005** | Compute diffs (p, CI, effect) | Phase 3 (Analysis) | Round to 3/2 decimals. |
| **FR-006** | Sweep outlier thresholds (k) | Phase 3 (Analysis) | **k ∈ {1.0, 1.5, 2.0}** per SC-005 (spec shows {1.5, 2.0} - inconsistency flagged). |
| **FR-007** | BH Correction | Phase 3 (Analysis) | Apply for FDR control at q≤0.05 (controls FDR, not FWER). |
| **FR-008** | Stratify by size/missingness | Phase 3 (Analysis) | Bins: n<50, 50-200, >200. |
| **FR-009** | Bootstrap variance (1000) | Phase 3 (Analysis) | CPU-tractable for small N; jackknife for n<50. |
| **FR-010** | Visualizations (PNG) | Phase 4 (Reporting) | Forest plot, heatmap. |
| **FR-011** | Permutation null datasets | Phase 3 (Analysis) | 1000 permutations per dataset for FPR estimation. |
| **ComparisonReport** | Create comparison outputs | Phase 3 (Analysis) | Maps to FR-005, FR-009, SC-001 through SC-003, SC-008. |
| **SC-001** | Median p-value shift (IQR) | Phase 4 (Reporting) | **Limitation**: Only 2 datasets available; median/IQR not statistically meaningful. Flagged for kickback. |
| **SC-002** | Median CI width change (IQR) | Phase 4 (Reporting) | **Limitation**: Only 2 datasets available. Flagged for kickback. |
| **SC-003** | Median effect-size change | Phase 4 (Reporting) | **Limitation**: Only 2 datasets available. Flagged for kickback. |
| **SC-004** | FDR control q≤0.05 | Phase 3 (Analysis) | BH method controls FDR (not FWER). |
| **SC-005** | FPR variation across k | Phase 4 (Reporting) | Sensitivity analysis. |
| **SC-006** | Baseline metrics ≥10 datasets | Phase 1 (Acquisition) | **Blocking Gap**: Only 2 verified datasets. Requires spec kickback. |
| **SC-007** | Cleaning validation logs | Phase 2 (Cleaning) | Row counts, missing checks. |
| **SC-008** | Bootstrap CI for shifts | Phase 3 (Analysis) | 95% CI on delta. |
| **SC-009** | PNG visualizations | Phase 4 (Reporting) | Save to `output/`. |


## Dataset Feasibility Notice

**Current Verified Datasets**: 2 (UCI HAR, UCI Shopper)
**Required per SC-006**: ≥10 datasets
**Status**: **BLOCKING GAP** - SC-006 requires kickback to spec author. Plan proceeds with available datasets and notes statistical aggregation limitations.

**Available Sources** (from `# Verified datasets` block):
- UCI HAR: `
- UCI Shopper: `

OpenML Small Datasets collection has **NO verified source** in the allowed block. Plan adapts to UCI only.
