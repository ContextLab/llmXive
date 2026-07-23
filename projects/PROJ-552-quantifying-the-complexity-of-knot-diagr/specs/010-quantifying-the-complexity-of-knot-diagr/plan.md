# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-12 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-knot-complexity-analysis/spec.md`

## Summary

This project implements a computational pipeline to quantify the relationship between combinatorial invariants (crossing number, braid index) and geometric complexity (hyperbolic volume) across the complete census of prime knots with crossing number ≤ 13. The approach involves downloading the Knot Atlas dataset (aggregating multiple separate bulk fetches), validating core invariants against KnotInfo reference values (where available), filtering for hyperbolic knots (volume > 0), and performing descriptive statistical analysis (correlations, Ridge regression models) while strictly adhering to census-data statistical principles (effect sizes over p-values). The plan explicitly addresses data quality, edge cases (API failures, missing invariants), and reproducibility requirements.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `requests` (HTTP), `pandas` (data manipulation), `scikit-learn` (regression models with Ridge), `matplotlib` (plotting), `pyyaml` (schema validation), `datasets` (Hugging Face, for potential streaming if needed).  
**Storage**: Local file system (`data/raw`, `data/processed`, `docs/reproducibility`). No external database.  
**Testing**: `pytest` (unit tests for parsers, validators, model fitting logic).  
**Target Platform**: Linux (GitHub Actions runner: 2 CPU, ~7 GB RAM).  
**Project Type**: CLI / Data Analysis Pipeline.  
**Performance Goals**: Complete pipeline execution within 6 hours on CPU runner; data download and parsing < 30 minutes; analysis < 1 hour.  
**Constraints**: Must handle Knot Atlas API rate limits (exponential backoff + parallel fetch); must not fabricate data; must strictly adhere to census-data statistical interpretation (no p-values for inferential claims).  

**Dataset Scope & Census Definition**:
- **Source Census**: The total count of prime knots with crossing number ≤ 13 is 9,988 (Source: OEIS A002863).
- **Analysis Population**: The regression analysis is restricted to the subset of **hyperbolic prime knots** (volume > 0). Torus and satellite knots (non-hyperbolic) are excluded per FR-012. Therefore, the effective N for the regression models is strictly less than 9,988.
- **Download Strategy**: To ensure the full source census is captured, the system will fetch data for each crossing number (1 through 13) individually (13 separate bulk fetches) and aggregate them. This prevents missing data if the API returns incomplete bulk files.
- **Caching**: A local disk cache (with strict versioning and checksums) will be used. On every CI run, the system checks the cache; if the source version has changed or the cache is stale, it re-fetches. This ensures reproducibility (Principle I) while optimizing CI time.

> **Note**: The dataset size (9988 knots) is the *source census*. The *analysis population* is the hyperbolic subset. All descriptive statistics refer to the analysis population.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan ensures random seeds are pinned in `code/utils/random.py`. **Crucially**, the download step is re-executed (or validated against a strict versioned cache) on **every** CI run to ensure the exact same source data is used, satisfying the requirement to fetch from the canonical source on every run.
- **Principle II (Verified Accuracy)**: Plan includes a validation step against KnotInfo for hyperbolic volume and core invariants. **Crucially**, this integrates the **Reference-Validator Agent** workflow, requiring all external citations to pass a 'Title-token-overlap' check (≥ 0.7) before contributing to review points.
- **Principle III (Data Hygiene)**: Plan mandates raw data preservation, checksumming, and derivation notes for all transformations.
- **Principle IV (Single Source of Truth)**: Plan defines strict data flow from `data/raw` to `data/processed` to `docs/reproducibility` and final reports.
- **Principle V (Versioning)**: Plan includes content hashing for artifacts and timestamped logs.
- **Principle VI (Mathematical Invariant Consistency)**: Plan explicitly states that tabulated values from Knot Atlas are treated as 'computed' for the purpose of this principle, and their source is verified against primary literature via the Reference-Validator Agent.
- **Principle VII (Statistical Significance)**: Plan explicitly acknowledges the census-data exception: no p-values for inferential claims; effect sizes (Cohen's d, r) are the primary metrics.

## Project Structure

### Documentation (this feature)

```text
specs/001-knot-complexity-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── knot_record.schema.yaml
│   ├── regression_model.schema.yaml
│   └── ...
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── download/
│   ├── knot_atlas_loader.py      # Parallel fetch per crossing number, caching, retry logic
│   └── __init__.py
├── data/
│   ├── parser.py                 # JSON parsing, cleaning, flagging
│   ├── validator.py              # Schema validation, consistency checks
│   ├── quality_report.py         # Generates data_quality_report.md
│   └── __init__.py
├── analysis/
│   ├── exploratory.py            # Scatter plots, descriptive stats
│   ├── regression.py             # Model fitting (Ridge, orthogonalized), VIF
│   ├── residual_analysis.py      # Identify outlier families (MAD-based)
│   └── __init__.py
├── reproducibility/
│   ├── checksums.py              # SHA-256 generation
│   ├── logs.py                   # Timestamped logging
│   └── __init__.py
├── utils/
│   ├── random.py                 # Seed pinning
│   └── constants.py              # Thresholds, constants
└── main.py                       # Orchestration script

data/
├── raw/                          # Raw JSON from Knot Atlas (per crossing number)
├── processed/                    # Cleaned CSV/Parquet
└── plots/                        # Generated PNGs

docs/
├── reproducibility/
│   ├── data_quality_report.md
│   ├── validation_scope.md
│   ├── excluded_knots.md
│   ├── random_seeds.md
│   ├── tie_breaking_rules.md
│   ├── residual_analysis.md
│   ├── hyperbolic_volume_validation.md
│   ├── core_precision_consistency.md
│   ├── multicollinearity_assessment.md
│   └── validation_status.md
└── analysis/
    └── (final reports)

tests/
├── unit/
│   ├── test_parser.py
│   ├── test_validator.py
│   └── test_regression.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schema_validation.py
```

**Structure Decision**: Single Python package structure (`code/`) is selected to simplify dependency management and ensure all modules are importable for testing. The `data/` and `docs/` directories are kept separate to maintain the "no in-place modification" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is well-defined and fits within standard data analysis patterns. | N/A |
