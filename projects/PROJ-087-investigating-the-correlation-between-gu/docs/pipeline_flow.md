# Pipeline Flow Documentation

This document describes the data flow and execution order of the llmXive automated science pipeline for the Gut Microbiome and Sleep Quality project.

## Overview

The pipeline consists of three primary user stories (US1, US2, US3) executed sequentially, with a critical feasibility check at the start.

## Execution Flow

### 1. Setup & Foundational (Phase 1 & 2)
- **T001-T006**: Initialize project structure, dependencies, logging, and configuration.
- **T009**: Setup hashing utility for reproducibility checks.
- **Status**: Completed.

### 2. User Story 1: Data Ingestion (Phase 3)
- **T012c (Gate)**: Verify the existence and accessibility of the `DATA_URL`.
 - *If Failed*: Generate `data/processed/ingestion_report.json` with status "blocked" and halt.
 - *If Passed*: Proceed to T012d.
- **T012d**: Verify schema (presence of required columns: `antibiotic_use_last_3m`, `sleep_efficiency`, `sleep_duration_hours`).
- **T013**: Download data with exponential backoff.
- **T014**: Filter out samples with `antibiotic_use_last_3m == True`.
- **T015**: Merge OTU tables with metadata (chunked if necessary).
- **T016**: Save cleaned data to `data/processed/cleaned_microbiome_sleep.csv` and record checksum.
- **T017**: Log exclusion rates to `data/processed/ingestion_report.json`.

### 3. User Story 2: Statistical Analysis (Phase 4)
- **T020b**: Compute Alpha-Diversity (Shannon, Simpson, Observed OTUs) with rarefaction.
 - *Input*: `data/processed/cleaned_microbiome_sleep.csv`
 - *Output*: Diversity indices DataFrame.
- **T021**: Compute Spearman rank correlation between diversity indices and sleep metrics.
- **T022**: Apply Benjamini-Hochberg FDR correction.
- **T023**: Flag correlations as `is_moderate` (|r| > 0.3) and `is_meaningful` (q < 0.05 & |r| > 0.3).
- **T024**: Save results to `data/processed/correlation_results.csv`.
- **T025**: Handle cases with no significant associations gracefully.

### 4. User Story 3: Visualization & Reporting (Phase 5)
- **T027**: Generate scatterplots with regression lines for significant correlations.
- **T028**: Generate boxplots by sleep quartile.
- **T029**: Compile summary table of correlations.
- **T030**: Save plots to `data/processed/plots/`.
- **T031**: Generate `data/processed/final_report.html` containing findings and visualizations.

### 5. Blocked State Handling
If T012c fails at any point:
- **T017b**: Generate blocked ingestion report.
- **T025b**: Generate blocked analysis report.
- **T031b**: Generate blocked final report.

## Data Artifacts

| Artifact | Path | Description |
|:--- |:--- |:--- |
| Cleaned Data | `data/processed/cleaned_microbiome_sleep.csv` | Filtered OTU and sleep data |
| Ingestion Report | `data/processed/ingestion_report.json` | Exclusion stats and status |
| Correlation Results | `data/processed/correlation_results.csv` | r, p, q, significance flags |
| Plots | `data/processed/plots/` | Scatterplots and boxplots |
| Final Report | `data/processed/final_report.html` | Comprehensive HTML report |

## Dependencies

- **T012c** blocks all downstream data tasks.
- **T016** (Cleaned Data) is required for **T020b**.
- **T024** (Correlation Results) is required for **T027**, **T028**, **T029**, **T030**, **T031**.
- **T009** (Hashing) is required for **T035** (Reproducibility).
