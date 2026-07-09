# Implementation Plan: Statistical Analysis of Publicly Available Stack Overflow Question Tags

**Branch**: `001-stat-so-tag-trends` | **Date**: 2023-10-27 | **Spec**: `specs/001-statistical-analysis-of-publicly-availab/spec.md`
**Input**: Feature specification from `/specs/001-statistical-analysis-of-publicly-availab/spec.md`

## Summary

This feature implements a statistical analysis pipeline to quantify technology growth and decline trajectories using Stack Overflow question tags. The core approach involves downloading the `PostsTags` table, aggregating monthly frequencies, applying the Modified Mann-Kendall test with pre-whitening for trend detection, and performing time series decomposition. The plan strictly adheres to CPU-only constraints for GitHub Actions runners and ensures all statistical claims are associational with mandatory limitation disclosures.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `nbformat`  
**Storage**: Local file system (CSV/Parquet intermediates), GitHub Actions ephemeral storage  
**Testing**: `pytest` (unit tests for statistical functions, integration tests for pipeline, contract validation)  
**Target Platform**: Linux server (GitHub Actions `ubuntu-latest`)  
**Project Type**: Data analysis pipeline / CLI tool / Jupyter Notebooks  
**Performance Goals**: Complete analysis of top 50 tags within 6 hours on 2 CPU cores / 7GB RAM  
**Constraints**: No GPU, no external API rate-limit violations (GitHub/NPM), strict memory limits (streaming/processing in chunks)  
**Scale/Scope**: Top tags, multi-year time range, A sufficient number of data points per series to ensure statistical robustness

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; `requirements.txt` pins versions; data fetched from canonical source (see Research); API results cached. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` and `paper/` will be validated against primary sources before review. |
| **III. Data Hygiene** | PASS | SHA-256 checksums recorded for all artifacts in `state/`; raw data preserved; derivations written to new files. |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to `data/` rows and `code/` blocks; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | PASS | Content hashes used for invalidation; `state/` updated on artifact changes. |
| **VI. Statistical Validity & Limitation Disclosure** | PASS | All reports include mandatory "Limitation: All findings are associational..." header/footer via `code/viz/templates.py` (FR-011); methods document assumptions. |
| **VII. Temporal Data Integrity** | PASS | No look-ahead bias; future frequencies excluded from past trend classifications. |

## Project Structure

### Documentation (this feature)

```text
specs/001-stat-so-tag-trends/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   ├── post_tags.schema.yaml
│   ├── trend_results.schema.yaml
│   └── cluster_results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-298-statistical-analysis-of-publicly-availab/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py          # Downloads raw data (FR-001)
│   │   ├── preprocess.py        # Aggregates to monthly bins (FR-002)
│   │   ├── external.py          # Fetches GitHub/NPM metrics (FR-007)
│   │   └── generate_taxonomies.py # Generates/validates reference calendars (FR-008, SC-003)
│   ├── analysis/
│   │   ├── trends.py            # Mann-Kendall, Theil-Sen, MDES via Monte Carlo (FR-003, FR-013)
│   │   ├── decomposition.py     # STL, HP, ADF, Ljung-Box, Event Alignment (FR-004, FR-009, SC-003)
│   │   ├── clustering.py        # Jaccard, Hierarchical, Permutation, Alignment Score (FR-005, FR-008)
│   │   └── correlation.py       # External metric correlation (FR-007)
│   ├── viz/
│   │   ├── plots.py             # Generates figures
│   │   └── templates.py         # Injects limitation headers/footers (FR-011)
│   ├── utils/
│   │   ├── hygiene.py           # SHA-256 hashing, state updates (FR-012)
│   │   └── contract_validation.py # Schema enforcement (Constitution Check)
│   ├── main.py                  # Orchestration script
│   └── requirements.txt
├── notebooks/                   # FR-006: Reproducible Jupyter notebooks
│   ├── 01_data_ingestion.ipynb
│   ├── 02_trend_analysis.ipynb
│   ├── 03_decomposition.ipynb
│   └── 04_clustering.ipynb
├── data/
│   ├── raw/                     # Downloaded archives (checksummed)
│   ├── processed/               # Monthly aggregates, derived stats
│   ├── events/
│   │   └── reference_calendar.json
│   └── taxonomy/
│       └── survey_2023.json
├── state/
│   └── projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml
└── tests/
    ├── contract/
    ├── integration/
    └── unit/
```

**Structure Decision**: Single project structure selected to maintain tight coupling between data ingestion, analysis, and visualization, ensuring reproducibility and ease of testing on constrained runners.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Statistical Rigor** | Required by FR-003, FR-009, FR-013 | Simple linear regression fails to handle non-normal distributions and autocorrelation in time series; Mann-Kendall is non-parametric and robust. |
| **External Validation** | Required by FR-007 | Sole reliance on SO data is circular; external metrics (GitHub/NPM) are needed to validate adoption trends (as consistency check). |
| **Power Analysis** | Required by FR-013 | Without MDES via Monte Carlo, "Stable" classifications for non-significant trends are unreliable (Type II error risk). |
| **Jupyter Notebooks** | Required by FR-006 | Scripts alone do not satisfy the "reproducible notebook" requirement for exploratory analysis. |

## Spec Root Cause Notes

*The following discrepancies between this plan and the source spec.md have been identified and require a spec update (kickback) to resolve fully:*

1.  **FR-013 / US-1**: Spec mandates "post-hoc power analysis". Plan implements "Monte Carlo MDES" (statistically valid). Spec must be updated to reflect MDES.
2.  **FR-003**: Spec mandates p < 0.05 but is ambiguous on multiple testing correction. Plan commits to Benjamini-Hochberg. Spec must be updated to mandate BH.
3.  **FR-006**: Spec requires notebooks but does not define the `notebooks/` directory structure. Plan defines it. Spec should reference this structure.
4.  **US-1 / US-3**: Spec frames external validation as proof of "actual adoption" and "external validity". Plan clarifies these are "convergence of interest" and "consistency checks". Spec acceptance criteria must be updated to avoid circular causality claims.
5.  **FR-007**: Spec requires correlation but does not mandate API caching for reproducibility. Plan adds caching. Spec should acknowledge reproducibility risks.