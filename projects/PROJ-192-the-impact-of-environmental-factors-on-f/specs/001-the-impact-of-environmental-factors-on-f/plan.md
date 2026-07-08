# Implementation Plan: Impact of Environmental Factors on Fungal Community Structure in Soil

**Branch**: `001-impact-of-environmental-factors` | **Date**: 2024-05-21 | **Spec**: `specs/001-impact-of-environmental-factors/spec.md`
**Input**: Feature specification from `/specs/001-impact-of-environmental-factors/spec.md`

## Summary
This project implements a reproducible, CPU-tractable workflow to analyze the impact of abiotic soil variables (pH, nutrients, temperature, moisture) on fungal community composition using ITS amplicon sequencing data. The workflow ingests public data, harmonizes metadata, performs beta-diversity analysis (PERMANOVA, db-RDA), handles collinearity (VIF), imputes missing data (MICE), and stratifies results by biome. It strictly adheres to computational constraints (≤7 GB RAM, ≤6h runtime) and constitutional principles regarding data integrity and reproducibility.

**Execution Modes**:
1.  **Pipeline Validation Mode**: Uses synthetic data to test pipeline logic. Skips the "minimum 3 real datasets" abort condition. Used for CI/CD verification of code paths.
2.  **Research Mode**: Requires real, verified ITS datasets. Aborts with a `FATAL` error if < 3 valid datasets are found or if minimum power requirements are not met. This is the mode required for scientific publication.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `scipy`, `skbio` (for ecological stats), `miceforest` (for MICE), `pyyaml`, `dask` (for memory management), `matplotlib`, `seaborn`.  
**Storage**: Local file system (`data/`, `results/`), checksummed via `sha256sum`.  
**Testing**: `pytest` with contract tests against YAML schemas.  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, 7 GB RAM).  
**Project Type**: Computational Biology Pipeline / CLI Tool.  
**Performance Goals**: Runtime ≤ 6 hours, Peak RAM ≤ 7 GB, Disk ≤ 14 GB.  
**Constraints**: No GPU usage; no deep learning; strict memory subsampling if limits approached; dataset exclusion if variables missing.  
**Scale/Scope**: Analysis of ≥3 distinct public ITS datasets (real data required for Research Mode).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: The plan mandates pinned `requirements.txt`, random seed setting in all scripts, and immutable raw data storage in `data/raw-seq/`. All transformations produce new files with provenance logs.
- **Principle II (Verified Accuracy)**: The plan requires that any dataset cited in `research.md` must be from the "Verified datasets" block. The plan explicitly defines two modes: 'Pipeline Validation Mode' (synthetic data, no abort) and 'Research Mode' (real data, hard abort if < 3 valid datasets). The current execution path for development is 'Pipeline Validation Mode' to ensure code correctness before data availability.
- **Principle III (Data Hygiene)**: The plan specifies `sha256sum` generation for all files in `data/` and forbids in-place modification. Raw FASTQs are preserved; derived ASV tables are new files.
- **Principle IV (Single Source of Truth)**: All statistics in the final report will be generated programmatically from `results/` CSVs, not hand-typed.
- **Principle V (Versioning Discipline)**: The plan includes a script to update `state/` YAML files with content hashes upon artifact generation.
- **Principle VI (Wet-lab Data Integrity)**: The plan enforces a `data/raw-seq/` directory for raw FASTQs and a `data/qc/` directory for QC reports, with strict separation from processed data.
- **Principle VII (Environmental Metadata Standardization)**: The plan includes a `harmonize_metadata` phase that maps biome labels to a controlled ontology (ENVO) and standardizes units for pH, nutrients, etc., logging all transformations. This explicitly addresses FR-001's requirement for automated ontology mapping.

## Project Structure

### Documentation (this feature)

```text
specs/001-impact-of-environmental-factors/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Existing design artifacts (Phase 0)
│   ├── dataset.schema.yaml
│   ├── asv_table.schema.yaml
│   └── results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── cli/
│   └── main.py              # Entry point for workflow execution
├── pipelines/
│   ├── ingest.py            # Data download and validation
│   ├── preprocess.py        # DADA2/QIIME2 wrapper (CPU mode) - Pure Python
│   ├── analysis.py          # PERMANOVA, db-RDA, VIF, MICE
│   └── report.py            # Sensitivity analysis and plotting
├── models/
│   └── schemas.py           # Pydantic models for validation
├── utils/
│   ├── logging.py
│   └── checksums.py
└── config/
    └── constants.yaml       # Thresholds (VIF>5, p<0.05, etc.)

tests/
├── contract/
│   └── test_schemas.py      # Validates JSON/YAML against contracts
├── integration/
│   └── test_workflow.py     # End-to-end run on sample data
└── unit/
    └── test_analysis.py     # Mocked statistical tests

data/
├── raw-seq/                 # Immutable raw FASTQs (if available)
├── metadata/                # Harmonized CSVs
└── qc/                      # QC reports
```

**Structure Decision**: Single project structure (`src/`) selected to minimize overhead for a CLI-based scientific pipeline. The `pipelines/` directory isolates the heavy computational steps, while `models/` and `contracts/` ensure data integrity. This aligns with the requirement for a reproducible, version-controlled pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| MICE Imputation | Required by FR-008 to preserve covariance structure; median imputation introduces bias. | Simple median/mean imputation fails to capture study-specific correlations, violating the "Data Integrity" principle for ecological data. |
| VIF-based Collinearity Handling | Required by FR-007 and Edge Cases to prevent spurious independent effect claims. | Removing one variable arbitrarily without VIF calculation risks retaining highly correlated predictors, invalidating the variance partitioning results. |
| Stratified Analysis | Required by FR-005 to address biome-specific driver ranking. | A single global model would mask context-dependent effects, failing to answer the core research question about "effect heterogeneity". |
| Variance Partitioning | Required by FR-004 to quantify unique vs. shared variance. | Simple regression coefficients cannot separate shared variance in collinear predictors. |
| Homogeneity of Dispersion Check | Required to ensure PERMANOVA results reflect location, not dispersion. | Ignoring dispersion differences can lead to false positives in PERMANOVA. |

## Output Artifacts

The workflow generates the following artifacts in `results/`:
- `results/permanova_summary.csv`: Global PERMANOVA results (R², p-value, FDR).
- `results/db_rda_variance.csv`: Variance explained by each predictor.
- `results/db_rda_biome_<NAME>.csv`: Stratified results per biome.
- `results/sensitivity_analysis.csv`: Stability of top driver ranking.
- `results/robustness_summary.md`: Narrative summary of findings.
- `results/plots/`: PNG figures (db-RDA triplots, etc.).
- `results/sampling_report.csv`: **Mandatory** log of subsampling ratios (FR-009).
- `results/power_analysis_report.md`: Summary of sample size and power adequacy.
