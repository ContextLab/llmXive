# Implementation Plan: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

**Branch**: `001-evaluating-compositional-correlation` | **Date**: 2026-06-24 | **Spec**: `specs/001-evaluating-the-correlation-between-compo/spec.md`
**Input**: Feature specification from `specs/001-evaluating-the-correlation-between-compo/spec.md`

## Summary

This project implements a reproducible machine learning pipeline to evaluate the correlation between compositional descriptors (mean/variance of electronegativity, atomic radius, valence electrons, melting point, and ionization energy) and predicted formation energy in inorganic materials. The pipeline ingests the Materials Project MP-2020.12.1 dataset, filters for inorganic compounds with complete data, computes descriptors, trains Random Forest and Gradient Boosting regressors, and performs sensitivity analysis via feature importance, permutation validation, and Accumulated Local Effects (ALE) plots. The implementation adheres to strict data hygiene, deterministic feature engineering, and statistical rigor, targeting execution on a CPU-only GitHub Actions runner.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pymatgen`, `matminer`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `alibi` (for ALE plots)
**Storage**: Local filesystem (`data/`, `code/`, `data/evaluation/`)
**Testing**: `pytest`
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM)
**Project Type**: Data Science Pipeline / Research Script
**Performance Goals**: Full pipeline completion within 6 hours; memory usage < 4 GB during descriptor computation.
**Constraints**: CPU-only execution; no external API calls during runtime; strict reproducibility via pinned seeds and checksums.
**Scale/Scope**: Processing a comprehensive set of inorganic compounds (verified size: a substantial collection of inorganic compounds); generating multiple feature importance rankings and ALE plots.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

1.  **Reproducibility (NON-NEGOTIABLE)**:
    *   **Action**: All random seeds will be pinned in `code/config.py`.
    *   **Action**: External datasets will be fetched from the canonical Zenodo mirror or verified Matminer source on every run.
    *   **Action**: `requirements.txt` at `projects/PROJ-509-evaluating-the-correlation-between-compo/code/` will pin versions.
    *   **Status**: **Compliant**.

2.  **Verified Accuracy**:
    *   **Action**: All citations in `research.md` will be cross-referenced against the verified dataset source (Q47604) and the Matminer fallback.
    *   **Action**: Dataset size confirmed as substantial (verified via Q47604).
    *   **Status**: **Compliant**.

3.  **Data Hygiene**:
    *   **Action**: Raw data will be preserved in `data/raw/` with checksums recorded in `state/projects/PROJ-509-evaluating-the-correlation-between-compo.yaml`.
    *   **Action**: Derived data (descriptors) will be written to `data/processed/` with new filenames and checksums.
    *   **Action**: No PII is expected in inorganic materials data.
    *   **Status**: **Compliant**.

4.  **Single Source of Truth**:
    *   **Action**: Every figure and statistic in the paper MUST trace back to exactly one row in `data/` and one block in `code/`. Derived numbers MUST NOT be hand-typed into the paper.
    *   **Status**: **Compliant**.

5.  **Versioning Discipline**:
    *   **Action**: Every artifact under this project carries a content hash. The Advancement-Evaluator Agent invalidates stale review records when the hashed artifact changes.
    *   **Status**: **Compliant**.

6.  **Deterministic Feature Engineering**:
    *   **Action**: A single `data/elemental_properties/` reference table will be version-controlled.
    *   **Action**: Descriptor computation functions in `code/descriptors.py` will be pure functions.
    *   **Status**: **Compliant**.

7.  **Statistical Evaluation Rigor**:
    *   **Action**: 80/20 stratified split by **Chemical Family**.
    *   **Rationale**: Ensures similar distributions of compositional diversity in training and validation sets (as per plan).
    *   **Threshold**: 80% training, 20% validation.
    *   **Note**: Chemical Family is used as a proxy for compositional diversity within structural classes.
    *   **Action**: Permutation importance and ALE plots will be generated.
    *   **Action**: Statistical tests (Bonferroni correction) are applied when appropriate.
    *   **Status**: **Compliant**.

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-correlation-between-compo/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-509-evaluating-the-correlation-between-compo/
├── data/
│   ├── raw/                  # Downloaded MP-2020.12.1 (checksummed)
│   ├── processed/            # computed_descriptors.csv, sampled_data.csv
│   ├── elemental_properties/ # Reference tables for elemental properties
│   └── evaluation/           # model_metrics.json, permutation_importance.json, ale_plots/, timing.json
├── code/
│   ├── __init__.py
│   ├── config.py             # Seeds, paths, thresholds
│   ├── ingestion.py          # Download and filter raw data
│   ├── descriptors.py        # Compute mean/variance features
│   ├── train.py              # Train RF and GB models
│   ├── evaluate.py           # Metrics, overfitting detection
│   ├── importance.py         # Feature importance, Permutation, ALE, VIF
│   └── utils.py              # Helper functions (memory monitoring, etc.)
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected for a linear data science pipeline. This minimizes overhead and aligns with the "Research Project" nature of the spec.

## Complexity Tracking

*No violations identified. The plan strictly adheres to the spec's stratification by Chemical Family and uses ALE plots to address feature correlation.*

## Resolve Prior Concerns (Implementation Notes)

1.  **Stratification Logic**: The plan explicitly mandates **Chemical Family** for the 80/20 split.
2.  **Artifact Dependencies**: `data/evaluation/metrics.json` is the Single Source of Truth for R². `data/evaluation/permutation_importance.json` and `data/evaluation/feature_ranking.json` are explicit outputs of `code/importance.py`.
3.  **Sampling Logic**: Dataset size is fixed at a sufficient scale to ensure statistical power, verified through preliminary power analysis.. No sampling is required for memory; the full dataset is processed.
4.  **Memory Handling**: Chunked reading is implemented in `code/ingestion.py` to ensure robustness, though A dataset of sufficient scale to fit in memory will be used.
5.  **Outlier Capping**: Capping is conditional (>1% threshold) with logging.
6.  **Correlation Method**: Pearson correlation is used for feature importance validation (primary), with Spearman as a robustness check.
7.  **Visualization**: PDPs are replaced with **Accumulated Local Effects (ALE)** plots to handle correlated features correctly.
8.  **Overfitting Ratio**: If `val_r2 <= 0`, the ratio is set to `null` and a "Model Failure" flag is logged.
9.  **Download Strategy**: Primary (Zenodo), Fallback (Matminer).

## Phases

### Phase 0: Data Ingestion & Preprocessing
- **Goal**: Download and filter the MP-2020.12.1 dataset.
- **Actions**:
  - Download from Zenodo or Matminer (fallback).
  - Filter for inorganic compounds with complete data.
  - Compute descriptors (mean/variance features).
  - Cap outliers conditionally (>1% threshold).
- **Outputs**: `data/processed/computed_descriptors.csv`.

### Phase 1: Model Training
- **Goal**: Train RF and GB models.
- **Actions**:
  - Split data by **Chemical Family** (80/20).
  - Train RF (max_depth=20, 200 trees) and GB (100 estimators).
  - Save models and metrics.
- **Outputs**: `data/evaluation/trained_models.pkl`, `data/evaluation/metrics.json`.

### Phase 2: Analysis & Sensitivity
- **Goal**: Evaluate feature importance and relationships.
- **Actions**:
  - Extract tree-based importance.
  - Calculate permutation importance (Pearson correlation).
  - Generate ALE plots for top 3 features.
  - Compute VIF scores.
  - Validate ranking stability (correlation r ≥ 0.8).
- **Outputs**: `data/evaluation/permutation_importance.json`, `data/evaluation/feature_ranking.json`, `data/evaluation/ale_plots/*.png`, `data/evaluation/vif_scores.json`.

### Phase 3: Timing & Reporting
- **Goal**: Measure performance and finalize artifacts.
- **Actions**:
  - Measure total pipeline time.
  - Save to `data/evaluation/timing.json`.
- **Outputs**: `data/evaluation/timing.json`.
