# Implementation Plan: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

**Branch**: `001-gut-microbiome-sleep-architecture` | **Date**: 2023-10-27 | **Spec**: `specs/001-gut-microbiome-sleep-architecture/spec.md`
**Input**: Feature specification from `/specs/001-gut-microbiome-sleep-architecture/spec.md`

## Summary

This project implements a robust analysis pipeline to investigate the **associational** correlation between gut microbiome composition (metagenomic count data) and sleep architecture metrics (polysomnography/actigraphy). The technical approach involves ingesting tabular data, validating variable presence (FR-001), performing statistical distribution checks to select the appropriate correlation method (ZINB, Spearman, or Pearson) per FR-002, applying Benjamini-Hochberg correction (FR-003), and running robustness diagnostics including sensitivity analysis, collinearity checks (VIF), power analysis, and outlier handling (FR-005, FR-006, FR-007). The pipeline explicitly handles compositional data via CLR transformation. The entire pipeline is designed to execute on a CPU-only GitHub Actions runner within 6 hours.

**Critical Scope Note**: Due to the absence of a verified real-world dataset containing both modalities, this phase is scoped as a **Pipeline Validation Study**. The primary goal is to verify the statistical engine's correctness (Type I/II error rates, model selection logic) using synthetic data with known ground truths. Biological construct validity (actual gut-sleep correlations) cannot be established without a real dataset.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scipy`, `statsmodels` (for ZINB), `numpy`, `scikit-learn` (for VIF/standardization), `pyyaml`, `scikit-bio` (for CLR transformation)  
**Storage**: CSV/TSV files (raw, wide-format), Parquet (intermediate processed), JSON (results)  
**Testing**: `pytest` (contract tests, unit tests for data validation logic)  
**Target Platform**: Linux (`ubuntu-latest` GitHub Actions runner)  
**Project Type**: CLI / Data Analysis Pipeline  
**Performance Goals**: Complete full pipeline (ingestion to report) in < 6 hours on 2 CPU cores, 7GB RAM.  
**Constraints**: No GPU usage; no deep learning models; data must be subset to fit RAM; strict adherence to observational framing (no causal claims).  
**Scale/Scope**: Designed for datasets with N < 1000 subjects and < 500 microbial taxa.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` pins versions; `code/` scripts use fixed random seeds; data fetched from canonical sources (or generated via deterministic synthetic logic). |
| **II. Verified Accuracy** | **PASS (Logic Only)** | All dataset citations in `research.md` are restricted to the "Verified datasets" block. Since no real dataset exists, the "Verified Accuracy" applies to the *statistical logic* validated against synthetic ground truth, not biological truth. |
| **III. Data Hygiene** | **PASS** | Raw data is read-only; transformations create new files; checksums recorded in state YAML; PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | All results in `paper/` trace to specific rows in `data/` and blocks in `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes; state YAML updated on change. |
| **VI. Biological Sample Integrity** | **N/A (Synthetic)** | Assumed handled by source dataset provenance for real data; synthetic data generation logic is the SSoT for this phase. |
| **VII. Sleep Metric Standardization** | **PASS** | Pipeline validates column names against a strict schema; rejects non-standardized metrics. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gut-microbiome-sleep-architecture/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── ingest.py            # Data loading, validation, and outlier handling (FR-001)
├── transform.py         # CLR transformation and data cleaning
├── analysis.py          # Correlation logic, method selection, and compositional correction (FR-002, FR-003)
├── diagnostics.py       # VIF (multivariate), Sensitivity, Power, Outlier reporting (FR-005, FR-006)
├── report.py            # Report generation (FR-004)
└── main.py              # Orchestration
tests/
├── contract/
│   ├── test_dataset_schema.py
│   └── test_output_schema.py
├── unit/
│   ├── test_validation.py
│   └── test_method_selection.py
└── integration/
    └── test_pipeline.py
data/
├── raw/                 # Downloaded datasets (checksummed) or synthetic generators
├── processed/           # Cleaned/aligned data (CLR transformed)
└── results/             # Correlation matrices, reports
```

**Structure Decision**: Single `code/` directory with modular scripts for clarity and ease of CI execution. No separate frontend/backend as this is a batch analysis pipeline.

## Complexity Tracking

No violations detected. The complexity is justified by the need to handle zero-inflated data, compositional data (CLR), and perform rigorous statistical diagnostics (VIF, Power, Outlier handling) within strict CI constraints.