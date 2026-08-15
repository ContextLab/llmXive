# Implementation Plan: Investigating the Impact of Soil Microbiome Diversity on Plant Disease Resistance

**Branch**: `001-soil-microbiome-diversity-disease-resistance` | **Date**: 2024-01-15 | **Spec**: `specs/001-soil-microbiome-diversity-disease-resistance/spec.md`
**Input**: Feature specification from `/specs/001-soil-microbiome-diversity-disease-resistance/spec.md`

## Summary

This project investigates the associational relationship between soil microbiome alpha-diversity and plant disease incidence. The technical approach involves downloading 16S rRNA amplicon tables and matched disease metadata, preprocessing data (filtering, rarefaction), computing diversity metrics, and fitting binomial generalized linear mixed-effects models (GLMM) with permutation testing.

**Critical Feasibility Finding**: A comprehensive search of verified open-source datasets confirms that **no single dataset exists** that simultaneously contains matched 16S rRNA amplicon tables AND plant disease incidence records with sufficient metadata (GPS/Date) for joining.

**Revised Strategy**: The plan adopts a **Data Availability Gate** approach:
1.  **Phase 0**: Verify data availability. If matched data is not found, generate a `verification_report.json` documenting the missing variables and halt the analysis pipeline.
2.  **Phase 1**: If data is available, proceed with acquisition and preprocessing.
3.  **Phase 2**: Statistical modeling.
4.  **No Synthetic Data**: The plan explicitly **DOES NOT** generate synthetic disease labels for the research analysis. Synthetic data is only used for unit testing the code logic (separate from the research pipeline). If the data is missing, the research question is declared unanswerable with current open data, and a Feasibility Report is generated instead of statistical findings.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `statsmodels`, `biom-format`, `qiime2` (via subprocess or API), `networkx`, `ancombc`, `numpy`, `scipy`, `datasets`.  
**Storage**: Local file system (`data/raw/`, `data/processed/`), CSV/TSV/JSON formats.  
**Testing**: `pytest` (unit tests for data parsing, integration tests for pipeline stages).  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM).  
**Project Type**: Scientific Analysis Pipeline / CLI.  
**Performance Goals**: End-to-end pipeline execution < 6 hours on CPU (if data available); memory usage < 6GB.  
**Constraints**: Must run on CPU-first; no local GPU. Must handle datasets that may not perfectly match (FR-008).  
**Scale/Scope**: Target a sufficient number of samples (if matched), otherwise generate Feasibility Report.  
**ANCOM Implementation**: The plan uses `ancombc` as the implementation for the ANCOM requirement (FR-006).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/analysis/`. Data sources cited. |
| **II. Verified Accuracy** | **FAIL (Data Unavailable)** | The hypothesis test cannot be performed due to missing data. The *process* of verifying the missing source is accurate, but the *outcome* (hypothesis test) is unverified. |
| **III. Data Hygiene** | **FAIL (Data Unavailable)** | No real disease data is available to maintain hygiene for the analysis. The pipeline halts to prevent fabrication. |
| **IV. Single Source of Truth** | **PASS** | All stats trace to `data/processed/` artifacts (if produced). |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes. |
| **VI. Ecological Data Provenance** | **PASS** | Raw EMP/OTU data stored in `data/raw/` with metadata. |
| **VII. Statistical Analysis Transparency** | **PASS** | Model specs (fixed/random effects) recorded in `code/analysis/`. |

**Resolution**: The plan explicitly handles the "FAIL" status by generating a `verification_report.json` and halting. This prevents the fabrication of results and adheres to the spirit of the constitution by being transparent about data limitations.

## Project Structure

### Documentation (this feature)

```text
specs/001-soil-microbiome-diversity-disease-resistance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-136-investigating-the-impact-of-soil-microbi/
├── data/
│   ├── raw/
│   │   ├── otu_tables/          # Downloaded OTU/ASV tables
│   │   └── verification_report.json  # Generated if data is missing
│   └── processed/
│       ├── rarefied-table.qza   # Rarefied OTU table (if data available)
│       ├── alpha-diversity.tsv  # Computed alpha diversity (if data available)
│       └── matched_samples.csv  # Merged dataset (if data available)
├── code/
│   ├── __init__.py
│   ├── data_acquisition.py      # Downloads and verifies data (T012, T014)
│   ├── preprocessing.py         # Rarefaction, filtering (T018)
│   ├── matching.py              # Joins OTU and Disease data (T016)
│   ├── analysis/
│   │   ├── diversity_metrics.py # Shannon, Simpson, Faith's PD
│   │   ├── models.py            # GLMM, Beta Regression, Permutation tests
│   │   ├── network.py           # ANCOM, CoNet
│   │   └── power_analysis.py    # A priori power calculation
│   └── utils/
│       └── config.py            # Seeds, paths, thresholds
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen. The workflow is linear (Acquire -> Preprocess -> Match -> Analyze), making a monolithic `code/` directory with sub-packages for analysis phases optimal. This minimizes cross-module dependencies and simplifies the Docker containerization for CI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Data Availability Gate** | No single verified dataset contains both OTU and Disease data. | Using a single "fake" dataset would violate Constitution Principle II (Verified Accuracy) and III (Data Hygiene). We must halt and report. |
| **No Synthetic Fallback** | Generating synthetic disease labels invalidates the biological hypothesis. | Synthetic data cannot support the research question. The pipeline must stop to avoid false conclusions. |
| **Unit Testing Separation** | Code must be validated without real data. | Unit tests use mocks, but the research pipeline requires real data. Separating these ensures code quality without compromising scientific integrity. |

## Task List (Revised)

### Phase 0: Verification & Planning
- **T000**: **Amend Spec**. Align terminology ('Disease Resistance' vs 'disease incidence') in the spec title and text to ensure traceability.
- **T012**: **Verify Data Availability**. Check for matched OTU and Disease data. If missing, generate `verification_report.json` and halt. This task MUST pass for T013/T014 to execute.
- **T015**: Perform A priori Power Analysis (FR-015) using actual sample count (if available) or report 'Insufficient Data'.

### Phase 1: Data Acquisition & Preprocessing (Conditional on T012 Pass)
- **T013**: Download OTU data (if T012 passed). Logic: Attempt to download from verified sources (EMP/MG-RAST). If no source found, generate `verification_report.json` with `[MISSING_VARIABLE: otu_data]` and halt.
- **T014**: Download Disease data (if T012 passed). Logic: Attempt to download from verified sources. If no source found, generate `verification_report.json` with `[MISSING_VARIABLE: disease_incidence]` and halt.
- **T016**: Match data (if T013/T014 passed). Logic: Join on GPS/Date. If match fails (<30 samples), generate `verification_report.json` and halt.
- **T018**: Preprocess (Rarefaction, Filtering). Logic: Run QIIME rarefaction to a standardized sequencing depth.. Handle edge cases (e.g., varying depth >10x) by logging warnings and proceeding with available depth. Output `data/processed/rarefied-table.qza`.

### Phase 2: Analysis (Conditional on T016 Pass)
- **T033A**: Create reference meta-analysis values file.
- **T033**: Measure correlation coefficient (skip comparison if T033A unverified).
- **T037**: ANCOM (Depends on T040).
- **T038**: CoNet (Depends on T040).
- **T040**: High/Low disease group stratification.

### Phase 3: Reporting
- **T051**: Generate final report (or Feasibility Report).