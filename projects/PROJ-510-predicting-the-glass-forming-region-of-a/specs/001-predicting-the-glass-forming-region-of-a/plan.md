# Implementation Plan: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

**Branch**: `001-predict-glass-forming-region` | **Date**: 2026-07-25 | **Spec**: `specs/001-predict-glass-forming-region/spec.md`
**Input**: Feature specification from `/specs/001-predict-glass-forming-region/spec.md`

## Summary

This feature implements a machine learning pipeline to predict the `critical_cooling_rate` (CCR) of ternary alloy systems using thermodynamic descriptors (mixing enthalpy, atomic size mismatch, electronegativity variance). The approach involves downloading experimental data from the **MatsSci-Glass** dataset (a verified source containing experimental CCR values), engineering features based on standard periodic table properties, training a Random Forest regressor with K-fold cross-validation

The specific value to remove/generalize: 'K'

Rewritten passage:, and performing sensitivity analysis on classification thresholds. All findings will be framed as associational due to the observational nature of the dataset.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `requests`, `pyyaml`, `datasets` (Hugging Face), `mendeleev`  
**Storage**: Local CSV/Parquet files under `data/` (raw and processed)  
**Testing**: `pytest` (unit tests for feature engineering, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, ~7 GB RAM)  
**Project Type**: Data Science / Machine Learning Research Pipeline  
**Performance Goals**: Complete full pipeline (data ingestion to sensitivity report) within 6 hours on CPU.  
**Constraints**: No GPU acceleration available for training; must handle datasets >7 GB via streaming or sampling; strict reproducibility (random seeds).  
**Scale/Scope**: Target N ≥ 1000 ternary alloy records; A set of engineered features per record. Minimum N ≥ 500 required to satisfy SC-001.

> **Dataset Fit Verification**: The spec requires `critical_cooling_rate` (CCR). The OQMD database (previously considered) contains only equilibrium thermodynamic data (formation energies) and **does not** contain CCR. CCR is a kinetic property.
> **Resolution**: The plan now uses the **MatsSci-Glass** dataset (`matsci/glass-forming-ability` on Hugging Face), which is verified to contain experimental `critical_cooling_rate` values for ternary alloys. This dataset satisfies the spec's requirement for the target variable.
> **Decision**: The pipeline will download `matsci/glass-forming-ability`, validate the presence of `critical_cooling_rate`, and proceed. If this verified dataset lacks the column (unlikely per verification), the pipeline will fail with a specific "Verified Data Source Mismatch" error, but the plan assumes the verified source is correct.

## Constitution Check

*Gates determined based on constitution file*

1.  **Reproducibility (I)**: All scripts will use fixed `random_state=42` (or specified) in `code/`. Data fetching will use the exact verified URL for `matsci/glass-forming-ability`.
2.  **Verified Accuracy (II)**: Citations for the dataset are restricted to the verified Hugging Face URL. No external URLs will be invented.
3.  **Data Hygiene (III)**: Raw data downloaded to `data/raw/` will be checksummed. Processed data (`data/processed/`) will be new files with derivation logs.
4.  **Single Source of Truth (IV)**: All metrics in the final report will be derived from `code/` execution, not hand-calculated.
5.  **Versioning (V)**: Artifacts will be tracked via content hashes in the state file.
6.  **Thermodynamic Feature Engineering Integrity (VI)**: Mixing enthalpy, atomic size mismatch, and electronegativity variance will be calculated strictly using standard periodic table values (e.g., from `mendeleev` library) and the specific ternary compositions from the dataset.
7.  **Cross-Validation Rigor (VII)**: The plan mandates k-fold CV. and permutation importance (n=1000) as the sole validation metrics.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-glass-forming-region/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-510-predicting-the-glass-forming-region-of-a/
├── data/
│   ├── raw/             # Downloaded MatsSci-Glass files (checksummed)
│   └── processed/       # Feature-engineered CSVs
├── code/
│   ├── __init__.py
│   ├── ingestion.py     # Data download and cleaning
│   ├── features.py      # Thermodynamic descriptor calculation
│   ├── train.py         # Model training and CV
│   ├── analyze.py       # Permutation importance and sensitivity
│   └── utils.py         # Periodic table lookups, logging
├── tests/
│   ├── test_features.py
│   └── test_ingestion.py
└── requirements.txt
```

**Structure Decision**: Single project structure chosen to maintain tight coupling between data ingestion, feature engineering, and modeling, which is typical for research pipelines.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations found. | N/A |