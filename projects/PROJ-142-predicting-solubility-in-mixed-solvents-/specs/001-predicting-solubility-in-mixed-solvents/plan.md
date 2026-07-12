# Implementation Plan: Predicting Solubility in Mixed Solvents with Machine Learning

**Branch**: `001-predicting-solubility-mixed-solvents` | **Date**: 2026-07-08
**Spec**: `specs/001-predicting-solubility-in-mixed-solvents/spec.md`

## Summary

This project implements a machine learning pipeline to predict solubility (logS) of small organic molecules (MW < 500 Da). The approach ingests data from MoleculeNet and EPA sources, engineers features using RDKit (molecular descriptors) and composition-weighted solvent properties, and explicitly constructs interaction terms to capture non-linear mixing effects **IF AND ONLY IF** verified mixed-solvent data is found. 

**Critical Feasibility Note**: The spec references MoleculeNet, EPA DSSTox, and CRC Handbook. The "Verified datasets" block confirms MoleculeNet and EPA CSVs exist. DSSTox and CRC Handbook have **no verified source URLs** in the provided block. MoleculeNet datasets (ESOL, FreeSolv) contain **only pure solvent** data. 
- **If** the EPA dataset contains verified mixed-solvent entries (N ≥ 100), the project proceeds with the "Mixed Solvent" hypothesis.
- **If** the EPA dataset lacks verified mixed-solvent entries, the project **pivots** to "Pure Solvent Prediction" using complex descriptors. In this pivot scenario, the "non-linear mixing" hypothesis is **dropped** as untestable. **No synthetic data generation is permitted.**

The system trains Gradient Boosting (XGBoost) and Random Forest models, comparing them against an Abraham solvation parameter baseline using k-fold cross-validation and a **paired t-test** (per Constitution Principle VII) on absolute errors. Success is defined by a ≥5% RMSE improvement over the baseline, **R² > 0.70**, and statistical significance (p < 0.05).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `xgboost`, `scikit-learn`, `shap`, `pandas`, `numpy`, `pyyaml`, `requests`  
**Storage**: Local filesystem (`data/`, `code/`, `artifacts/`)  
**Testing**: `pytest` (unit, integration, contract)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7 GB RAM, 14 GB disk, no GPU)  
**Project Type**: Data Science / Computational Chemistry Pipeline  
**Performance Goals**: Total runtime ≤ 6 hours; Peak memory ≤ 7 GB; Disk ≤ 14 GB.  
**Constraints**: No GPU; no large-LLM inference; no proprietary data; strict reproducibility (fixed seeds).  
**Scale/Scope**: Dataset size limited by available verified sources; model training constrained to CPU-tractable hyperparameter grids.

## Constitution Check

The following principles from `constitution.md` are addressed in this plan:

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All random seeds (numpy, pandas, sklearn, xgboost) are pinned in `code/`. Data ingestion scripts re-fetch from canonical URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | Citations in `research.md` are limited to the "Verified datasets" block. Any missing source (DSSTox, CRC) is explicitly noted as "NO verified source found" rather than fabricated. |
| **III. Data Hygiene** | Raw data downloaded to `data/raw/` with checksums. Derived data written to `data/processed/`. No in-place modification. PII scan passed (chemical data is non-PII). |
| **IV. Single Source of Truth** | Figures and stats in the final report trace to specific rows in `data/processed/` and code blocks in `code/`. |
| **V. Versioning Discipline** | Artifacts in `data/` and `code/` will be checksummed. State file updated on artifact changes. |
| **VI. Composition-Weighted Feature Engineering** | `research.md` details the exact formula for composition-weighted averages and interaction term generation. **Note**: If no mixed data exists, this principle is applied to pure solvent descriptors only, and the "mixing" hypothesis is dropped. |
| **VII. Baseline Constrained Evaluation** | The plan mandates the Abraham solvation parameter model as the baseline and requires a **paired t-test** on absolute errors (per Constitution Principle VII). **Note**: Spec FR-005 (Wilcoxon) and SC-001 (R² threshold) conflict with the Constitution; the plan implements the Constitution and flags the Spec for amendment. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-solubility-in-mixed-solvents/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── solubility_record.schema.yaml
│   └── processed_dataset.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── 01_data_ingestion.py       # Ingests MoleculeNet/EPA, filters MW, handles missing data
├── 02_feature_engineering.py  # RDKit descriptors, composition-weighted solvent props, interaction terms
├── model_training.py       # XGBoost, RF, Abraham baseline, 5-fold CV
├── 04_evaluation.py           # Metrics, t-test, SHAP analysis, sensitivity analysis
├── utils/
│   ├── constants.py           # Seeds, thresholds, file paths
│   └── logging.py             # Memory/disk monitoring
├── requirements.txt           # Pinned dependencies
└── main.py                    # Orchestration script

data/
├── raw/                       # Downloaded CSVs (checksummed)
├── processed/                 # Cleaned, feature-engineered datasets
└── artifacts/                 # Model weights, SHAP plots, reports

tests/
├── unit/
│   ├── test_feature_engineering.py
│   └── test_model_training.py
├── contract/
│   └── test_schema_validation.py
└── integration/
    └── test_pipeline.py
```

**Structure Decision**: Single-project structure chosen to minimize overhead for a data-science pipeline. All scripts are modular and runnable via `main.py` or individually. Tests are colocated with logic where appropriate but separated for clarity.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Interaction Terms** | Spec requires explicit non-linear mixing effects (FR-003) **IF** data exists. | Simple additive models cannot capture the "non-linear mixing" hypothesis central to the research question. **However**, if no mixed data exists, these terms are used for pure solvent interaction analysis, and the mixing hypothesis is dropped. |
| **SHAP Sensitivity Analysis** | Spec requires robustness check (FR-007, SC-004). | Single-threshold SHAP analysis is insufficient to prove stability of feature importance rankings. |
| **Abraham Baseline** | Spec requires comparison to standard physical model (FR-005). | Comparing only ML models against each other would not establish relative improvement over established physical chemistry methods. |
| **Paired t-test (vs Wilcoxon)** | Constitution Principle VII mandates a paired t-test. | Spec FR-005 requests Wilcoxon. The Constitution takes precedence; the plan implements the t-test and flags the spec for amendment. |
| **R² > 0.70 Threshold** | Constitution Principle VII mandates absolute performance. | Spec SC-001 only requests relative improvement. The plan implements both relative and absolute thresholds. |

## Assumptions & Gaps (Critical)

1.  **Data Gap (DSSTox/CRC)**: No verified URL for DSSTox or CRC Handbook. The plan proceeds with EPA and MoleculeNet data only. This is a known limitation. **Spec FR-001 requires amendment.**
2.  **Mixed Solvent Data Gap**: If the EPA dataset lacks verified mixed-solvent entries (N < 100), the project **pivots** to "Pure Solvent Prediction". **No synthetic data is generated.** The "non-linear mixing" hypothesis is explicitly dropped in this scenario. The research question is re-scoped to pure solvent prediction.
3.  **Spec/Constitution Conflict (Test)**: Spec FR-005 requires Wilcoxon; Constitution VII requires t-test. The plan implements the **t-test** and notes the spec requires amendment.
4.  **Spec/Constitution Conflict (R²)**: Spec SC-001 requires [deferred] improvement; Constitution VII requires R² > 0.70. The plan implements **both**.
5.  **Spec/Constitution Conflict (DSSTox)**: Spec FR-001 requires DSSTox ingestion; no verified source exists. The plan proceeds with EPA only and notes the spec requires amendment.
6.  **Imputation Rate (SC-005)**: SC-005 applies to the **actual data ingested**. If the project pivots to pure solvent data, the imputation rate is measured on that dataset.