# Implementation Plan: Investigating Correlations Between Molecular Descriptors and Drug-Likeness Scores

**Branch**: `001-gene-regulation` | **Date**: 2026-09-20 | **Spec**: `specs/001-investigating-correlations-between-molec/spec.md`
**Input**: Feature specification from `/specs/001-investigating-correlations-between-molec/spec.md`

## Summary

This project implements a computational pipeline to investigate the correlation between fundamental 2D molecular descriptors (specifically logP and TPSA) and experimental drug-likeness scores (oral bioavailability, apparent permeability, clearance). The approach involves acquiring the canonical ChEMBL dataset., sanitizing structures via RDKit, calculating descriptors from raw SMILES, and training Linear Regression and Random Forest models. The implementation strictly adheres to the GitHub Actions free-tier constraints (limited CPU cores, restricted RAM, 6-hour limit) by capping the dataset size and using robust stratification logic for sparse targets.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `rdkit`, `pandas`, `scikit-learn`, `sqlite3`, `matplotlib`, `seaborn`  
**Storage**: Local filesystem (CSV/Parquet artifacts) under `data/`  
**Testing**: `pytest` (unit tests for data sanitization, model training, and metric calculation)  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Data Science Pipeline / Research Tool  
**Performance Goals**: Complete full pipeline (download to visualization) within 6 hours; peak memory < 7GB.  
**Constraints**: Dataset size capped at [deferred] molecules (stratified sample) to fit memory; no GPU usage for training; strict handling of duplicate SMILES.
**Scale/Scope**: Analysis of ~15k molecules; 2 models (Linear, RF); 3 target variables (Bioavailability, Papp, Clearance).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Compliance Status | Implementation Strategy |
|-----------|-------------------|-------------------------|
| **I. Reproducibility** | **Compliant** | All random seeds pinned to a fixed value. Dependencies pinned in `requirements.txt`. Data fetched from a canonical ChEMBL source. Pipeline runs end-to-end via script. |
| **II. Verified Accuracy** | **Compliant** | All citations in `research.md` validated against official EMBL-EBI URLs. No external URLs invented. |
| **III. Data Hygiene** | **Compliant** | Raw data downloaded to `data/raw/` with checksums recorded. Sanitized data written to `data/processed/` as new files. No in-place modifications. Descriptors calculated fresh from raw SMILES. |
| **IV. Single Source of Truth** | **Compliant** | All figures and statistics in `paper/` generated programmatically from `data/processed/` and `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **Compliant** | Artifacts under `data/` and `code/` will be hashed. The script `code/utils/update_state.py` updates `state/projects/PROJ-066-investigating-correlations-between-molec.yaml` with artifact hashes after each major stage. |
| **VI. Descriptor-Based Predictive Validity** | **Compliant** | Pipeline explicitly calculates logP and TPSA from raw SMILES. Random Forest feature importance will be analyzed to confirm these descriptors drive predictions. |
| **VII. Computational Resource Conformance** | **Compliant** | Dataset limited to a stratified sample of sufficient size to ensure statistical power. Models trained on CPU. Memory usage monitored; streaming SQL queries used for initial load. |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-correlations-between-molec/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── molecule.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-066-investigating-correlations-between-molec/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── download.py          # Fetches ChEMBL 33, validates file
│   │   └── preprocess.py        # Sanitizes, filters, deduplicates, calculates descriptors, samples
│   ├── models/
│   │   ├── train.py             # Trains LR and RF, saves artifacts
│   │   └── evaluate.py          # Computes metrics, generates plots
│   └── utils/
│       ├── config.py            # Constants (seed, limits)
│       ├── logging.py
│       └── update_state.py      # Updates project state file with hashes
├── data/
│   ├── raw/                     # Downloaded SQLite file
│   └── processed/               # Cleaned CSVs, models, plots
├── tests/
│   ├── test_preprocess.py
│   └── test_models.py
└── docs/                        # Paper artifacts
```

**Structure Decision**: Single project structure selected to minimize overhead. All data processing and modeling scripts reside in `code/` to ensure the `data/` directory remains a pure artifact store. This aligns with the "Data Hygiene" principle by separating transformation logic from stored data.

## Contract Validation Mapping

The following mapping ensures that every output file is validated against the defined schemas:

| Script | Output File | Contract Schema | Validation Step |
| :--- | :--- | :--- | :--- |
| `data/preprocess.py` | `data/processed/molecules_processed.csv` | `contracts/molecule.schema.yaml` | `preprocess.py` validates each row against the schema before writing. |
| `models/evaluate.py` | `data/processed/metrics_summary.json` | `contracts/model_output.schema.yaml` | `evaluate.py` validates the JSON output against the schema before saving. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Stratified Sampling (with binning)** | Required to ensure balanced representation of target variables (Bioavailability, Papp, Clearance) in train/test splits, preventing bias toward the majority class. | Simple random sampling could result in a test set lacking specific target types, invalidating the correlation analysis. |
| **Dual Model Strategy (LR + RF)** | LR provides a baseline for linear relationships (hypothesis testing), while RF captures non-linear interactions and provides feature importance rankings. | Using only one model would fail to distinguish between linear and non-linear predictive power, weakening the conclusion about descriptor validity. |
| **Explicit Deduplication Logic** | Required to handle duplicate SMILES with conflicting values as per FR-009 (keep most recent or average). | Ignoring duplicates would introduce data leakage and artificially inflate model performance metrics. |
| **Pre-Sampling Validation** | Required to check target distribution before sampling to prevent stratification crashes on sparse targets. | Skipping this check could cause `StratifiedShuffleSplit` to fail if a target has < 2 unique values or < 1000 rows. |

## Data Flow & Schema Alignment

The data flow strictly adheres to the `data-model.md` schema:
1.  **Raw Input**: SQLite from ChEMBL 33.
2.  **Sanitized**: Rows with invalid SMILES or missing targets removed.
3.  **Deduplicated**: Duplicate SMILES resolved per FR-009.
4.  **Pre-Sampled**: Validation checks row counts per target.
5.  **Sampled**: Stratified random sample of a substantial number of rows.
6.  **Processed**: `preprocess.py` calculates descriptors and outputs `molecules_processed.csv` (flat structure, matching `molecule.schema.yaml`).
7.  **Split**: Train (majority) / Test (minority) CSVs.
8.  **Output**: Model artifacts (`.pkl`) and Plot images (`.png`).

The streaming logic in `download.py` and `preprocess.py` handles the flat CSV structure defined in the schema, ensuring no nested JSON parsing issues.