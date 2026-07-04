# Implementation Plan: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

**Branch**: `001-gene-regulation` | **Date**: 2024-05-21 | **Spec**: `specs/001-investigating-the-correlation-between-di/spec.md`
**Input**: Feature specification from `/specs/001-investigating-the-correlation-between-di/spec.md`

## Summary

This project implements a reproducible, CPU-tractable pipeline to investigate the correlation between dietary fiber intake and gut microbiome composition using data from the American Gut Project (AGP) and UK Biobank. The implementation strictly adheres to compositional data analysis principles (CLR transformation), employs robust linear modeling (MaAsLin2) for continuous association, and enforces cross-cohort validation via beta-coefficient comparison. All statistical outputs include FDR correction and power analysis, constrained to run within 6 hours on a free-tier GitHub Actions runner (Multiple CPU, 7 GB RAM).

## Technical Context

**Language/Version**: Python 3.11 (Primary), R 4.3 (via `rpy2` for MaAsLin2)  
**Primary Dependencies**: `pandas`, `scikit-learn`, `scipy`, `numpy`, `maaslin2` (via R), `rpy2`, `requests`, `pyyaml`, `joblib`, `miceforest` (for MICE imputation).  
**Storage**: Local file system (`data/raw/`, `data/processed/`), CSV/TSV intermediates. No external database.  
**Testing**: `pytest` (unit/integration), `pandas.testing` for schema validation.  
**Target Platform**: Linux (GitHub Actions Free Tier).  
**Project Type**: Computational Research Pipeline / Data Analysis.  
**Performance Goals**: Complete end-to-end analysis (ingestion → validation) in ≤6 hours; RAM usage ≤7 GB.  
**Constraints**: No GPU; no large-LLM inference; dataset sampling required if raw sizes exceed RAM; strict adherence to verified dataset IDs only.  
**Scale/Scope**: Two cohorts (AGP, UK Biobank); hundreds of taxa; thousands of samples (sampled if necessary).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. Data fetched from canonical sources (Qiita, UKBB Fields) only. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` limited to specific, verified dataset IDs (Qiita 10160, UKBB 21003/22012). Verification occurs at design phase; pipeline halts if IDs invalid. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/` with checksums. Derived files in `data/processed/` with new names. PII scan integrated. |
| **IV. Single Source of Truth** | **PASS** | All stats in `paper/` trace to specific rows in `data/processed/` via `sample_id` (SHA256 hash of cohort + original_id). No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes recorded in `state/`. Artifact updates trigger state timestamp updates. |
| **VI. Compositional Data** | **PASS** | Mandatory CLR transformation (with a pseudocount) before correlation. MaAsLin2 used for continuous association. |
| **VII. Cross-Cohort Validation** | **PASS** | Pipeline explicitly compares continuous beta-coefficients (direction/magnitude) between cohorts. |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-correlation-between-di/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
src/
├── ingestion/
│   ├── agp_loader.py
│   ├── ukbb_loader.py
│   └── harmonizer.py
├── preprocessing/
│   ├── filter_samples.py
│   ├── clr_transform.py
│   ├── covariate_handler.py  # MICE Imputation
│   └── id_generator.py       # SHA256 Sample ID
├── analysis/
│   ├── correlation_maaslin2.py
│   └── validation_cross_cohort.py
├── utils/
│   ├── power_analysis.py
│   └── logger.py
└── main.py

tests/
├── contract/
│   └── test_schemas.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_harmonizer.py
    └── test_clr.py

data/
├── raw/
│   ├── agp_raw.tsv
│   └── ukbb_raw.tsv
└── processed/
    ├── merged_harmonized.tsv
    ├── clr_transformed.tsv
    └── results/
```

**Structure Decision**: Single project structure (`src/`) selected to minimize overhead. Modular separation of ingestion, preprocessing, and analysis ensures testability and adherence to the "Single Source of Truth" principle. R-based tools (MaAsLin2) will be invoked via `subprocess` or `rpy2` to maintain CPU-only feasibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Continuous Model Only** | Spec requires robustness check. Categorical splits (ANCOM-II/DESeq2) were found to be methodologically flawed (tautological) and biologically incomparable across cohorts. | Single continuous model (MaAsLin2) preserves power and avoids tautology. |
| **MICE Imputation** | Simple median imputation introduces bias in observational studies. | MICE (Multivariate Imputation by Chained Equations) accounts for correlations between covariates. |
| **SHA256 Sample ID** | Constitution Principle IV requires traceable unique IDs. | Deterministic hash ensures reproducibility and SSoT linkage. |
