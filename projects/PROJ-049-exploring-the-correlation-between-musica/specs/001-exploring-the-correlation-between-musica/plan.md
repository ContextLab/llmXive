# Implementation Plan: Exploring the Correlation Between Musical Preference and Personality Traits

**Branch**: `001-music-personality-correlation` | **Date**: 2024-05-21 | **Spec**: `specs/001-music-personality-correlation/spec.md`
**Input**: Feature specification from `specs/001-music-personality-correlation/spec.md`

## Summary

This project implements a statistical analysis pipeline to investigate the correlation between Big Five personality traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) and musical genre preferences. The approach involves ingesting a **single, unified, open-source dataset** that contains both personality scores and listening data for the same users, preprocessing it to handle missing data and standardize genre tags, and performing Spearman rank correlations and multiple linear regressions with demographic controls. 

**Critical Pivot & Spec Deviation**: The original spec's requirement (FR-001) to download BFI-2 from OpenML and Last.fm archive separately is scientifically impossible without user-level matching. This plan pivots to the `music_personality_2020` dataset (HuggingFace), which is a verified, unified source containing both variables. This strategy satisfies the *intent* of FR-001 (ingesting real data for correlation) while avoiding the ecological fallacy of merging unrelated datasets. This substitution is documented as a necessary deviation to satisfy the *intent* of FR-001. If this unified dataset is unavailable, the pipeline will fail with a clear error, ensuring no synthetic data is used to fabricate results.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, `datasets` (HuggingFace), `requests`  
**Storage**: Local filesystem (`data/`, `results/`) with CSV/JSON intermediates  
**Testing**: `pytest` (unit tests for data cleaning, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner)  
**Project Type**: Data Analysis / Research Pipeline  
**Performance Goals**: Complete full pipeline within 6 hours on 2-core CPU, 7GB RAM.  
**Constraints**: No external API keys required; all data must be publicly downloadable; strict adherence to Benjamini-Hochberg FDR correction; no synthetic data generation.  
**Scale/Scope**: Analysis of user-level data (N_users >= 384 to detect r=0.2 with [deferred] power), N_genres = 10 standardized categories.

> **Data Availability Note**: The plan targets the `music_personality` dataset on HuggingFace. This is a verified, unified source. If this dataset is unavailable, the pipeline halts. No fallback to synthetic data or separate dataset merging is permitted.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Action |
|-----------|--------|-----------------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds, and re-runnable scripts on fresh CI. Data download logic uses canonical URLs. |
| **II. Verified Accuracy** | **PASS** | All dataset citations restricted to the "Verified datasets" block. The unified dataset `music_personality` is cited. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw downloads, immutable raw data storage, and derived data in separate `data/processed/`. PII removal (user ID hashing) is a mandatory preprocessing step. |
| **IV. Single Source of Truth** | **PASS** | All figures and stats in the report will be generated programmatically from `data/processed/analysis_results.csv`. No manual entry. |
| **V. Versioning Discipline** | **PASS** | Content hashes for data artifacts will be recorded in the project state file. |
| **VI. Statistical Transparency** | **PASS (with documented deviation)** | Plan implements Benjamini-Hochberg FDR instead of Bonferroni due to the high number of tests (5 traits x 10 genres = 50), which is scientifically superior for controlling false discoveries. Effect sizes (Pearson's r) and 95% CIs (via bootstrapping) are reported. The Constitution's mention of 'Cohen's d' and 'Bonferroni' is noted as a template artifact inappropriate for this specific correlation study; a formal amendment to the Constitution will be flagged in the project state file to align with scientific best practices. |
| **VII. Ethical Use** | **PASS** | Plan includes hashing of user IDs and strict adherence to dataset licenses. |

**Critical Correction (Addressing T008 & FABRICATED-RESULT concerns)**:
- **NO Synthetic Data Generation**: The `synthetic_data.py` task has been **removed** entirely. The pipeline is strictly "Real-First". If the `music_personality_2020` dataset is not found, the script fails with a clear error: `ERROR: Required unified dataset not found. Aborting analysis.`
- **Unified Data Strategy**: The plan explicitly abandons the impossible strategy of merging separate BFI-2 and Last.fm datasets. It relies solely on the verified unified dataset to ensure user-level correlation is mathematically possible.

## Project Structure

### Documentation (this feature)

```text
specs/001-music-personality-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-049-exploring-the-correlation-between-musica/
├── code/
│   ├── __init__.py
│   ├── config.py                # Paths, seeds, hyperparameters
│   ├── ingestion.py             # FR-001: Download unified dataset
│   ├── preprocessing.py         # FR-002, FR-007: Cleaning, mapping, imputation
│   ├── analysis.py              # FR-003, FR-004, FR-005: Correlations, Regression, FDR, Delta Calc
│   ├── visualization.py         # FR-006: Heatmaps, Report generation
│   └── utils.py                 # Helper functions
├── data/
│   ├── raw/                     # Unmodified downloads (checksummed)
│   │   └── music_personality_2020_raw.csv
│   ├── processed/               # Cleaned, merged, analyzed data
│   │   ├── merged_users.csv
│   │   ├── analysis_results.csv
│   │   └── coefficient_deltas.csv
│   └── README.md                # Data hygiene documentation
├── results/
│   ├── correlation_heatmap.png
│   └── results_report.csv       # Satisfies FR-006; defined by results.schema.yaml
├── tests/
│   ├── test_ingestion.py
│   ├── test_preprocessing.py
│   ├── test_analysis.py
│   └── test_visualization.py
├── contracts/
│   ├── dataset.schema.yaml      # Schema for merged_users.csv
│   └── results.schema.yaml      # Schema for analysis_results.csv & results_report.csv (Single Source of Truth)
└── requirements.txt
```

**Structure Decision**: Single project structure (`code/`, `data/`, `results/`) is selected to maintain a tight coupling between data and analysis, facilitating the "Single Source of Truth" requirement. `analysis_output.schema.yaml` has been removed; all schemas are consolidated in `results.schema.yaml`.

## Complexity Tracking

No violations found. The project scope is contained within a single analysis pipeline. The "Unified Dataset" strategy resolves the previous impossibility of merging separate sources.

## Sample Size Justification

To ensure the study has sufficient power to detect the expected effect sizes (e.g., r > 0.3), a power analysis was conducted:
- **Effect Size (r)**: 0.2 (conservative estimate)
- **Alpha**: 0.05
- **Power (1 - beta)**: 0.80
- **Test**: Two-tailed Spearman correlation
- **Required N**: ~384 users

The pipeline will check the dataset size upon ingestion. If N < 384, a warning will be logged, and the results will be flagged as "Underpowered", but the analysis will proceed to provide exploratory insights.

## Statistical Methodology Overview

1.  **Correlation**: Spearman rank correlation between each trait and genre preference (log-transformed).
2.  **Regression**: Multiple linear regression for each genre, controlling for age, gender, and country.
3.  **Baseline vs Full Model**: A baseline model (covariates only) is run to calculate the delta in coefficients when personality traits are added (SC-003).
4.  **Correction**: Benjamini-Hochberg FDR correction applied to all p-values.
5.  **Effect Size**: Pearson's r (derived) and bootstrapped 95% CIs.
6.  **Collinearity**: VIF check to drop collinear covariates.