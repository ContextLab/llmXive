# Implementation Plan: Exploring the Correlation Between Musical Preference and Personality Traits

**Branch**: `001-music-personality-correlation` | **Date**: 2024-05-21 | **Spec**: `specs/001-music-personality-correlation/spec.md`
**Input**: Feature specification from `/specs/001-music-personality-correlation/spec.md`

## Summary

This project investigates the statistical association between the Big Five personality traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) and musical genre preferences. The technical approach involves ingesting personality data (BFI-2) and listening history (Last.fm), standardizing genre tags, and performing Spearman rank correlations and Mixed-Effects Regression (LMM) with demographic covariates to account for non-independence of observations. All analyses will be corrected for multiple comparisons using the Benjamini-Hochberg FDR procedure. The pipeline is designed to run entirely on CPU within the GitHub Actions free-tier constraints (limited cores, constrained RAM, a time limit).

**Critical Data Note**: No single public merged dataset exists containing both BFI-2 and Last.fm data for the same users. The pipeline will attempt to join OpenML BFI-2 (ID: 42473) and HuggingFace Last.fm 1K on `user_id`. If the join fails (no common users), the pipeline will log a critical warning and halt, or proceed with a synthetic proxy for testing only (clearly marked).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `seaborn`, `matplotlib`, `openml`, `requests`, `pingouin` (for LMM)  
**Storage**: Local CSV files in `data/raw/`, `data/processed/`, and `results/`  
**Testing**: `pytest` with unit tests for data ingestion, correlation logic, and schema validation  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Data analysis / Research pipeline  
**Performance Goals**: Complete full pipeline execution in < 4 hours on CPU; memory usage < 6GB.  
**Constraints**: No GPU usage; no external API keys required (public datasets only); strict adherence to FDR correction; no fabricated data (must use real or verified open data).  
**Scale/Scope**: Analysis of available open datasets (BFI-2 + Last.fm subsets); expected N < 10,000 users after merging (if join succeeds).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (NON-NEGOTIABLE)**:
    *   **Compliance**: The plan mandates `random.seed` pinning in `code/`, deterministic data loading from fixed URLs (OpenML ID 42473, HF `lastfm/lastfm_1k`), and a `requirements.txt` with pinned versions.
    *   **Action**: Implement `code/setup.py` to set global seeds; verify `data/` files are checksummed in `state/...yaml`.

2.  **Verified Accuracy**:
    *   **Compliance**: Citations for BFI-2 and Last.fm will reference the verified IDs (OpenML 42473, HF `lastfm/lastfm_1k`). If the join fails, the pipeline halts with a clear error.
    *   **Action**: The `research.md` will strictly adhere to the verified dataset IDs, avoiding any fabricated URLs.

3.  **Data Hygiene**:
    *   **Compliance**: Raw data will be stored in `data/raw/` and preserved. All transformations (merging, mapping) will write to new files in `data/processed/`. Checksums will be recorded in `state/...yaml` as a reference to the files in `data/`.
    *   **Action**: Implement `code/data_ingestion.py` to write checksums; ensure no in-place modification of raw files.

4.  **Single Source of Truth**:
    *   **Compliance**: All figures and statistics in the final report will be generated programmatically from `data/processed/` files.
    *   **Action**: The `code/visualization.py` will read directly from `data/processed/analysis_results.csv`.

5.  **Versioning Discipline**:
    *   **Compliance**: Artifacts (CSVs, schemas) will carry content hashes.
    *   **Action**: The pipeline will update the `state/...yaml` timestamp and artifact hashes upon successful completion.

6.  **Statistical Transparency**:
    *   **Compliance**: The plan explicitly includes Spearman correlation, Mixed-Effects Regression (LMM), and Benjamini-Hochberg FDR correction. Effect sizes (rho, bootstrapped CI) and Cohen's d for coefficient deltas will be calculated.
    *   **Action**: `code/analysis.py` will implement these specific statistical methods; no ad-hoc corrections.
    *   **Constitution Note**: Constitution Principle VI mandates "Bonferroni correction". The Spec (FR-005) mandates "Benjamini-Hochberg FDR". As FR-005 is the specific functional requirement for this study design (50+ tests), FDR is the active implementation. The Constitution will be flagged for amendment to align with the specific statistical method required by the study design.

7.  **Ethical Use of Public Behavioral Data**:
    *   **Compliance**: User IDs will be hashed or removed before merging. No PII will be committed.
    *   **Action**: `code/data_ingestion.py` will drop or hash `user_id` columns immediately after the merge.

## Project Structure

### Documentation (this feature)

```text
specs/001-music-personality-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── analysis_results.schema.yaml
│   ├── report.schema.yaml
│   ├── analysis_output.schema.yaml
│   └── results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, constants
├── data_ingestion.py    # Download, clean, merge, hash PII
├── analysis.py          # Correlation, LMM, FDR, effect sizes
├── visualization.py     # Heatmaps, report generation
└── utils.py             # Genre mapping, imputation logic

data/
├── raw/                 # Downloaded raw files
├── processed/           # Merged, cleaned, standardized data
└── README.md            # Data dictionary, checksums

results/
├── correlation_heatmap.png
└── results_report.csv

tests/
├── test_ingestion.py
├── test_analysis.py
└── test_schemas.py
```

**Structure Decision**: A single `code/` directory is selected for this research pipeline. It separates concerns into ingestion, analysis, and visualization modules, which aligns with the linear flow of the research (Download -> Clean -> Analyze -> Visualize). This structure avoids unnecessary complexity of a web app or mobile architecture while maintaining modularity for testing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations detected. | N/A |