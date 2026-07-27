# Data Model: Investigating the Correlation Between Gut Microbiome Composition and Immune Response to Influenza Vaccination

## Overview

This document defines the data structures, transformations, and file formats used throughout the pipeline. The data model is designed to ensure reproducibility and strict adherence to the functional requirements (FR-001 to FR-008).

## Entity Definitions

### 1. Subject
Represents an individual participant.
- **Attributes**:
  - `subject_id`: Unique string identifier.
  - `age`: Integer (optional).
  - `sex`: String (optional).
  - `titer_pre`: Float (log-transformed baseline antibody titer).
  - `titer_post`: Float (log-transformed post-vaccination antibody titer).
  - `responder_status`: Binary (0=Low, 1=High). Derived from `titer_post` vs `titer_pre`.
  - `shannon_diversity`: Float (calculated diversity metric).

### 2. Taxon
Represents a microbial taxon (e.g., Genus, Species).
- **Attributes**:
  - `taxon_id`: String (e.g., "Bacteroides_fragilis").
  - `abundances`: List of floats (relative abundance per subject).
  - `clr_values`: List of floats (CLR-transformed values per subject).
  - `correlation_coefficient`: Float (Spearman rho).
  - `p_value_raw`: Float (raw p-value).
  - `p_value_adj`: Float (BH-corrected p-value).
  - `is_significant`: Boolean.

### 3. CorrelationResult
Output of the correlation analysis phase.
- **Attributes**:
  - `taxon_id`: String.
  - `metric`: String (e.g., "Spearman").
  - `coefficient`: Float.
  - `p_value_raw`: Float.
  - `p_value_adj`: Float.
  - `significant`: Boolean.

### 4. ModelPerformance
Output of the Random Forest validation.
- **Attributes**:
  - `fold_id`: Integer (0-4).
  - `accuracy`: Float.
  - `precision`: Float.
  - `recall`: Float.
  - `f1_score`: Float.
  - `selected_features`: List of strings (taxa IDs used in this fold).

### 5. LintReport
Output of the T039 linting phase.
- **Attributes**:
  - `status`: String ("PASS" or "FAIL").
  - `errors`: List of strings (error messages).
  - `warnings`: List of strings (warning messages).

## File Schema & Artifacts

### 1. `data/raw/ingested_data.csv`
*Source*: Ingested from verified URLs (or synthetic generator).
*Schema*:
- `subject_id` (str)
- `titer_pre` (float)
- `titer_post` (float)
- `taxa_1` (float) ... `taxa_N` (float)

### 2. `data/processed/cleared_with_diversity.csv`
*Source*: Filtered and transformed from `ingested_data.csv` (T011d).
*Schema*:
- `subject_id` (str)
- `shannon_diversity` (float)
- `titer_pre_log` (float)
- `titer_post_log` (float)
- `responder_status` (int)
- `taxa_1_clr` (float) ... `taxa_N_clr` (float)

*Note*: This file is the single source of truth for the analysis phase. It resolves the "consumer before producer" concern by explicitly merging microbiome and serology data before any transformation.

### 3. `data/results/correlation_results.json`
*Schema*: List of `CorrelationResult` objects.

### 4. `data/results/model_metrics.json`
*Schema*: List of `ModelPerformance` objects + aggregate summary.

### 5. `data/results/lint_report.txt`
*Source*: T039 output.
*Schema*: Plain text log of `ruff` and `black` execution.

## Data Flow Diagram

1. **Ingestion**: `raw` -> `cleared_with_diversity.csv` (Filtering, Merging, CLR, Log-Transform).
2. **Analysis**: `cleared_with_diversity.csv` -> `correlation_results.json` (Spearman, BH).
3. **Modeling**: `cleared_with_diversity.csv` + `correlation_results.json` -> `model_metrics.json` (Nested CV).
4. **Output**: Aggregated results to `data/results/`.
5. **Linting**: `code/` -> `lint_report.txt` (Pre-requisite).

## Assumptions & Constraints

- **Missing Data**: Any subject with missing `titer_pre` or `titer_post` is dropped immediately in Step 1.
- **Zero Abundance**: Taxa with 0 variance (all zeros) are removed before CLR to avoid `log(0)`.
- **LOD**: Values below limit of detection are imputed to `0.5 * LOD` before log-transform.
- **Responer Definition**: High responder = `titer_post / titer_pre >= 4` OR `titer_post >= 40` (HAI units).
- **Zero-Handling**: Pseudo-count 1e-6 added before CLR.