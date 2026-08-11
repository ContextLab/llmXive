# Implementation Plan: Submarine Hydrothermal Vent Microbial Communities as Indicators of Ocean Acidification

**Branch**: `001-submarine-hydrothermal-vent-microbial-communities` | **Date**: 2026-07-17 | **Spec**: `specs/001-submarine-hydrothermal-vent-microbial-communities/spec.md`
**Input**: Feature specification from `specs/001-submarine-hydrothermal-vent-microbial-communities/spec.md`

## Summary

This project implements a bioinformatics and statistical pipeline to analyze the correlational relationship between microbial community composition (16S rRNA) and localized pH reductions in submarine hydrothermal vents. The approach involves ingesting raw FASTQ, pH, and temperature logs; preprocessing them into a unified temporal-spatial index; calculating alpha diversity (Shannon, Simpson); and performing multivariate analysis (PERMANOVA, ordination) and linear mixed-effects modeling.

**Key Methodological Updates**:
- **Variance Partitioning**: To address the "indicator" claim, the plan includes a distance-based Redundancy Analysis (dbRDA) to explicitly isolate the unique variance explained by pH after controlling for temperature, distinguishing pH-driven shifts from temperature-driven shifts.
- **Robustness Checks**: The plan incorporates log-ratio transforms (CLR) as a robustness check for compositional data and specifies GLMM or transformed LME to handle non-normality of diversity indices.
- **Data Strategy**: The pipeline is designed to validate code logic using synthetic data (due to lack of verified real-world triad data), but explicitly frames this as "Pipeline Validation" only, not "Scientific Discovery".

The pipeline explicitly handles edge cases such as temporal mismatches, outlier pH values, and collinearity with temperature, while framing all results as associational due to the observational nature of the study.

## Requirements Mapping

This section explicitly maps plan phases to the Functional Requirements (FR) and User Stories (US) from the spec.

| Plan Phase | Primary User Stories | Primary Functional Requirements | Contract/Schema |
|------------|---------------------|--------------------------------|-----------------|
| **Phase 0: Data Ingestion** | US-1 (Data Ingestion) | FR-001, FR-001.1, FR-006 | `sample_schema.schema.yaml` |
| **Phase 1: Preprocessing** | US-1 (Preprocessing) | FR-002, Edge Cases (Rarefaction, Outliers) | `otu_table_schema.schema.yaml` |
| **Phase 2: Alpha Diversity & LME** | US-2 (Diversity Analysis) | FR-003, FR-003.1, SC-002, SC-003 | `analysis_results_schema.schema.yaml` |
| **Phase 3: Beta Diversity & Clustering** | US-3 (Multivariate Clustering) | FR-004, FR-005, SC-001, SC-004 | `analysis_results_schema.schema.yaml` |
| **Phase 4: Reporting** | All | SC-005 (Feasibility) | N/A |

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `statsmodels`, `biopython`, `scipy`, `matplotlib`, `seaborn`, `vegan` (via `rpy2` or `skbio`), `pyrda` (for dbRDA)  
**Storage**: Local file system (CSV, TSV, JSON, Parquet)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner)  
**Project Type**: CLI / Data Pipeline  
**Performance Goals**: Complete analysis within 6 hours on 2 CPU cores, 7 GB RAM.  
**Constraints**: No local GPU; datasets must be streamable or sample-able within 14 GB disk; strict adherence to biologically plausible pH ranges.  
**Scale/Scope**: Single-feature pipeline processing one study's worth of vent samples (estimated < 10k reads per sample for simulation/testing).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Note |
|-----------|--------|-------------|
| **I. Reproducibility** | PASS | Plan mandates pinned seeds, version-locked tools (QIIME2/statsmodels), and deterministic execution on CI. |
| **II. Verified Accuracy** | PASS | Research phase will cite ONLY verified URLs from the `# Verified datasets` block. Synthetic data is generated internally (no external citation), so it does not violate this principle. Any future real data will be validated by the Reference-Validator Agent. |
| **III. Data Hygiene** | PASS | Pipeline will checksum raw inputs, never modify in-place, and log derivation steps. |
| **IV. Single Source of Truth** | PASS | All outputs (figures, stats) derived programmatically from `data/` and `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Content hashes will be tracked in `state/` for all artifacts. |
| **VI. Wet-Lab Sample Provenance** | PASS | Metadata schema includes `deployment_event`, `sensor_id`, `coordinates`, and `timestamp` to link sequence to physical sample. |
| **VII. Bioinformatics Pipeline Determinism** | PASS | Plan specifies exact command-line arguments for diversity/ordination and logs them in `code/`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-submarine-hydrothermal-vent-microbial-communities/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-012-investigating-submarine-hydrothermal-ven/
├── data/
│   ├── raw/             # Raw FASTQ, pH CSV, Temp CSV
│   ├── processed/       # Unified analysis tables, rarefied counts
│   └── checksums.json   # SHA256 hashes of raw files
├── code/
│   ├── __init__.py
│   ├── ingestion.py     # FR-001: Data ingestion & temporal alignment
│   ├── preprocessing.py # FR-002: Rarefaction, diversity calc
│   ├── analysis.py      # FR-003, FR-004, FR-005: LME, PERMANOVA, Ordination, dbRDA
│   ├── utils.py         # Logging, outlier detection (FR-006)
│   └── main.py          # CLI entry point
├── tests/
│   ├── unit/            # Unit tests for ingestion, preprocessing
│   ├── integration/     # End-to-end pipeline test with mock data
│   └── contract/        # Schema validation tests
├── requirements.txt     # Pinned dependencies
└── README.md            # Project overview
```

**Structure Decision**: Single project structure selected. The workflow is linear (Ingest -> Preprocess -> Analyze -> Report), making a monolithic `code/` directory with modular scripts appropriate. This minimizes overhead for the GitHub Actions runner and simplifies dependency management.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Linear Mixed-Effects Model** | Required by FR-003 to account for random site effects in multi-site vent data. | Simple linear regression ignores site-level clustering, violating statistical assumptions for multi-site data. |
| **Temporal Alignment Window** | Required by US-1 to handle asynchronous sensor and sequencing data. | Direct row-matching fails when sensors and sequencers operate on different clocks or intervals. |
| **Rarefaction** | Required by FR-002 and Edge Cases to normalize sequencing depth. | Alternative normalizations (CSS/TMM) are valid but rarefaction is the community standard for alpha diversity in amplicon sequencing; sensitivity analysis (SC-003) will validate this choice. |
| **Variance Partitioning (dbRDA)** | Required to isolate pH effects from temperature (Methodology Concern). | Simple PERMANOVA on pH alone cannot distinguish shared variance between pH and temperature, failing the "indicator" claim. |
| **GLMM / Transformation** | Required for non-normal diversity indices (Scientific Soundness Concern). | Standard LME assumes Gaussian residuals; microbial data is often zero-inflated or skewed, violating assumptions. |

## Compute Feasibility

- **CPU-First**: The pipeline uses `scipy`, `statsmodels`, and `pandas`. These are CPU-tractable.
- **Memory**: Marker-gene count tables are typically sparse matrices.. We will use `scipy.sparse` to handle large datasets within 7 GB RAM.
- **Disk**: Raw FASTQ files are large. The pipeline will stream them or process in chunks. If the full dataset exceeds 14 GB, we will subsample (first N reads) or use streaming.
- **No GPU Required**: No deep learning models (e.g., transformers) are planned. All methods are classical statistics.