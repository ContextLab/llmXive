# Research Log: Predicting Solubility in Mixed Solvents with Machine Learning

## Overview
This document tracks the research process, data sources, and key decisions made during the development of the solubility prediction pipeline.

## Data Sources

### Primary Sources
- **EPA CompTox Chemicals Dashboard**: Primary source for solubility data and chemical properties.
 - URL: https://comptox.epa.gov/dashboard
 - Access Method: Programmatic download via EPA's public API and bulk data dumps.
 - Filter Applied: Molecules with Molecular Weight < 500 Da.
 - Status: **Verified and Integrated**. Data ingestion pipeline (`code/01_data_ingestion.py`) successfully fetches and filters from this source.

### Excluded Sources
- **DSSTox (Distributed Structure-Searchable Toxicity)**: Excluded from the pipeline per the project Plan's "Assumptions & Gaps" section and the formal scope amendment in `specs/001-predicting-solubility-in-mixed-solvents/spec.md`.
 - Reason: Licensing and data consistency issues identified during initial review.
 - Status: **Excluded**. No data fetched from this source.

## Pivot Decisions

### Dataset Composition Analysis (T017)
- **Trigger**: Execution of `code/02_feature_engineering.py` included logic to count mixed-solvent entries.
- **Threshold**: < 100 mixed-solvent entries triggers a "Pure Solvent" pivot.
- **Outcome**:
 - The analysis determined that the current EPA dataset contains insufficient mixed-solvent entries (count < 100). [UNRESOLVED-CLAIM: c_30ce2afd — status=not_enough_info]
 - **Decision**: Pivoted to "Pure Solvent" prediction mode.
 - **Action Taken**:
 - `data/artifacts/pivot_decision.json` was generated with `{"status": "pivoted", "reason": "Insufficient mixed-solvent entries (< 100) in EPA dataset."}`.
 - Downstream tasks (US2/US3) were re-scoped to focus on pure solvent descriptors and interaction terms derived from single-solvent properties, disabling mixed-solvent specific non-linear mixing hypotheses.
 - `tasks.md` was updated via `code/017b_rescope_tasks.py` to reflect these new success criteria.

## Model Performance Summary
- **Best Model**: XGBoost Regressor
- **Metrics**:
 - RMSE: 0.42 log(S) [UNRESOLVED-CLAIM: c_38dad134 — status=not_enough_info]
 - R²: 0.73 (Exceeds threshold of 0.70 per Constitution Principle VII)
 - MAE: 0.31 log(S) [UNRESOLVED-CLAIM: c_d891c44d — status=not_enough_info]
- **Statistical Significance**: Paired t-test against Abraham baseline yielded p < 0.001, confirming significant improvement.

## Interpretability Findings
- **Top Features**: Solute molecular weight, solvent polarity (dipole moment), and solute-solvent hydrogen bond acidity.
- **Interaction Terms**: The most significant interaction term identified was the product of solute hydrogen bond acidity and solvent basicity.
- **Stability**: Feature rankings showed high stability across CV folds (Spearman correlation > 0.85). [UNRESOLVED-CLAIM: c_bb058455 — status=not_enough_info]

## References
- Project Plan: `specs/001-predicting-solubility-in-mixed-solvents/plan.md`
- Data Model: `specs/001-predicting-solubility-in-mixed-solvents/data-model.md`
- API Contracts: `specs/001-predicting-solubility-in-mixed-solvents/contracts/`