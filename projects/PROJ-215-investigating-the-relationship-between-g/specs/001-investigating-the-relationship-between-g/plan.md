# Implementation Plan: Investigating the Relationship Between Gut Microbiome Composition and Mental Health in Public Datasets

**Branch**: `001-gut-microbiome-mental-health` | **Date**: 2026-07-13 | **Spec**: `specs/001-gut-microbiome-mental-health/spec.md`
**Input**: Feature specification from `/specs/001-gut-microbiome-mental-health/spec.md`

## Summary

This project implements a CPU-tractable statistical pipeline to investigate associations between gut microbiome composition (16S rRNA data) and mental health scores (PHQ-9) using public datasets. The approach involves a strict **Data Availability Check**: the pipeline will only proceed if a single verified public dataset containing both 16S rRNA sequencing data and valid mental health questionnaire responses (PHQ-9) for the same individuals is found. If no such linked dataset exists, the analysis phase is skipped, and the project reports a "Data Gap".

If data is available, the pipeline preprocesses via rarefaction or variance-stabilizing transformation (VST), calculates diversity metrics, and performs MaAsLin2-style linear modeling (with covariate adjustment) and PERMANOVA tests. All analyses adhere to the project constitution's requirements for reproducibility, data hygiene, and statistical rigor (Benjamini-Hochberg correction). The implementation is constrained to GitHub Actions free-tier resources (CPU-only, ≤7GB RAM).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `scipy`, `numpy`, `biom-format`, `maaslin2` (or `skbio` equivalents), `matplotlib`, `seaborn`, `requests`  
**Storage**: Local CSV/Parquet files under `data/` (raw and processed)  
**Testing**: `pytest` for unit tests on data transformation logic and statistical output validation (using synthetic data ONLY for unit tests)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Data analysis pipeline / CLI  
**Performance Goals**: Full pipeline execution ≤ 4 hours on 2 CPU cores, ≤ 7 GB RAM  
**Constraints**: No GPU, no large LLM inference, no deep learning training. Data must be sampled if >7GB.  
**Scale/Scope**: A sufficient number of samples (depending on linked dataset availability), Hundreds to thousands of taxa (post-filtering)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Strategy |
|-----------|-------------------|-------------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`. All analysis data fetched from canonical, verified HuggingFace URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | CONDITIONAL | Only verified dataset URLs from the "Verified datasets" block are cited. If no linked dataset exists, the project halts with a "Data Gap" report. Synthetic data is used ONLY for unit tests, not analysis. |
| **III. Data Hygiene** | PASS | Raw data downloaded to `data/raw/` with checksums. Processed data written to `data/processed/`. No in-place modification. |
| **IV. Single Source of Truth** | CONDITIONAL | All figures/stats in reports generated directly from `data/processed/` files via code. If data is unavailable, the report explicitly states "No SSoT available due to data gap". |
| **V. Versioning Discipline** | PASS | Artifacts tracked via content hashes in `state/projects/PROJ-215-.../state.yaml`. The `updated_at` timestamp is updated in the state file on every artifact change. |
| **VI. Microbiome Data Standardization** | PASS | Preprocessing includes rarefaction (or VST fallback) and <0.1% prevalence filtering as per spec. |
| **VII. Statistical Rigor** | PASS | MaAsLin2-style linear modeling (with covariate adjustment) and Benjamini-Hochberg correction implemented. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gut-microbiome-mental-health/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-215-investigating-the-relationship-between-g/
├── code/
│   ├── __init__.py
│   ├── config.py             # Paths, seeds, thresholds
│   ├── data_ingestion.py     # Download, merge, filter, LINK CHECK
│   ├── preprocessing.py      # Rarefaction/VST, diversity calc
│   ├── analysis.py           # MaAsLin2, PERMANOVA, BH correction, KS test
│   ├── visualization.py      # PCoA, heatmaps
│   └── report.py             # Summary generation, SC-005 delta calc
├── data/
│   ├── raw/                  # Downloaded parquet/CSV (checksummed)
│   └── processed/            # Merged, cleaned, transformed data
├── tests/
│   ├── contract/             # Schema validation tests
│   ├── unit/                 # Logic tests (e.g., rarefaction fallback)
│   └── integration/          # End-to-end pipeline tests
├── docs/
│   └── ...
└── requirements.txt
```

**Structure Decision**: Single project structure selected for simplicity and direct data flow. All logic resides in `code/` with clear separation of concerns (ingestion, preprocessing, analysis, viz).

## Implementation Phases

### Phase 0: Data Feasibility Check (Blocking Gate)
- **Task 0.1**: Attempt to locate a single verified public dataset containing both 16S rRNA data and PHQ-9/GAD-7 scores for the same sample IDs.
- **Task 0.2**: If no linked dataset is found, **HALT** and generate a "Data Gap Report" (SC-001, SC-002, SC-003, SC-005 marked as Not Applicable).
- **Task 0.3**: If a linked dataset is found, proceed to Phase 1.

### Phase 1: Data Ingestion & Preprocessing (FR-001, FR-002, FR-003)
- **Task 1.1**: Download the linked dataset to `data/raw/`. Compute and record checksums.
- **Task 1.2**: Merge OTU table with metadata on `sample_id`.
- **Task 1.3**: Filter samples with missing PHQ-9 scores. Log exclusion rate.
- **Task 1.4**: Apply rarefaction. If >20% sample loss, switch to VST (log fallback).
- **Task 1.5**: Filter taxa with <0.1% prevalence.
- **Task 1.6**: Calculate alpha (Shannon, Simpson) and beta (Bray-Curtis) diversity.

### Phase 2: Statistical Analysis (FR-004, FR-005, SC-002, SC-005)
- **Task 2.1**: Perform MaAsLin2-style linear modeling (or `skbio` equivalent) between diversity/taxa and PHQ-9, adjusting for age and BMI (if present).
- **Task 2.2**: Apply Benjamini-Hochberg correction to all p-values.
- **Task 2.3**: Perform PERMANOVA on beta diversity with residualization for covariates.
- **Task 2.4**: **SC-005 Check**: Calculate `|p_adjusted - p_unadjusted|` for each taxon. Report if any delta > 0.01.
- **Task 2.5**: **SC-002 Check**: If no significant taxa (q < 0.05), perform Kolmogorov-Smirnov test on p-value distribution.

### Phase 3: Visualization & Reporting (FR-006, FR-007)
- **Task 3.1**: Generate PCoA plot colored by mental health status (High vs. Low PHQ-9).
- **Task 3.2**: Generate heatmap of top associated taxa.
- **Task 3.3**: Generate summary report listing significant associations (q < 0.05) with effect direction.

### Phase 4: Conditional Validation (FR-008, SC-003)
- **Task 4.1**: Check if an independent cohort (e.g., UK Biobank) is accessible via verified URL.
- **Task 4.2**: **If accessible**: Validate effect direction of significant taxa. Calculate % match (SC-003).
- **Task 4.3**: **If not accessible**: Log "Skip: No independent cohort available". Mark SC-003 as "Not Applicable".

### Phase 5: Final Output
- **Task 5.1**: Update `state/projects/PROJ-215-.../state.yaml` with `updated_at` and artifact hashes.
- **Task 5.2**: Generate final report.

## Complexity Tracking

No violations identified. The pipeline complexity is managed by modularizing data ingestion, preprocessing, and analysis steps, ensuring CPU feasibility. The "Data Availability Check" ensures scientific validity by preventing analysis on unlinked data.