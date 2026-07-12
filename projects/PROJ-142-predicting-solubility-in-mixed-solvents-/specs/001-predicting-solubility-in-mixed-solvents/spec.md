# Solubility Prediction in Mixed Solvents - Specification Document
## Project: PROJ-142-predicting-solubility-in-mixed-solvents

## 1. Introduction

### 1.1 Purpose
This document defines the functional and non-functional requirements for a machine learning system to predict solubility in mixed solvent systems. The system will ingest raw chemical data, engineer features, train predictive models, and provide interpretability analysis.

### 1.2 Scope
The system targets small molecules (MW < 500 Da) and predicts solubility (logS) based on solute descriptors and solvent mixture composition.

---

## 2. Functional Requirements

### FR-001: Data Ingestion
The system must ingest raw solubility data from verified public sources.
- **Primary Source**: EPA CompTox Chemicals Dashboard (via API/FTP).
- **Excluded Sources**: **DSSTox is explicitly excluded** from this pipeline.
 - *Rationale*: Per the project Plan ("Assumptions & Gaps" section), DSSTox data integration requires complex stoichiometry normalization that exceeds the current MVP scope. The system will rely solely on EPA-curated entries to ensure data quality and consistency for the initial release.
- **Input Format**: CSV/TSV files containing Solute SMILES, Solvent SMILES, Composition (mole fraction), and Solubility (logS).
- **Output**: Cleaned, validated records stored in `data/processed/`.

### FR-002: Data Filtering
- Filter molecules with Molecular Weight (MW) < 500 Da.
- Filter records where solvent composition sum != 1.0 (within tolerance 1e-5).
- Handle missing values via KNN imputation (max 15% rate).

### FR-003: Feature Engineering
- Compute RDKit descriptors (Morgan fingerprints, topological indices) for solutes.
- Compute composition-weighted solvent descriptors.
- Generate interaction terms (polynomial, ratio) for mixed solvents.
- **Pivot Condition**: If mixed-solvent entries < 100, pivot to "Pure Solvent" mode and disable non-linear mixing hypotheses.

### FR-004: Model Training
- Train XGBoost and Random Forest regressors.
- Implement Abraham solvation parameter baseline (using `solv` package or fallback).
- Perform 5-fold cross-validation.

### FR-005: Model Evaluation
- Calculate RMSE, MAE, and R² on hold-out test sets.
- Perform statistical significance testing (Constitution Principle VII: Paired t-test).
- **Success Criteria**: Absolute R² > 0.70.

### FR-006: Interpretability
- Generate SHAP summary plots and feature importance tables.
- Analyze top interaction terms.
- Perform sensitivity analysis on SHAP thresholds.

---

## 3. Non-Functional Requirements

### NFR-001: Performance
- Training must complete within 30 minutes per trial on CPU-only CI.
- Resource limits: RAM < 7.0 GB, Disk < 14.0 GB.

### NFR-002: Reproducibility
- All random seeds must be fixed (numpy, pandas, sklearn, xgboost).
- Data checksums must be generated and verified.

### NFR-003: Data Integrity
- All input data must be validated against schemas defined in `specs/contracts/`.
- No synthetic data generation allowed; only real, programmatically accessible sources.

---

## 4. Data Model

### 4.1 Raw Solubility Record
| Field | Type | Description |
|:--- |:--- |:--- |
| solute_smiles | str | Canonical SMILES of solute |
| solvent_smiles | str | Canonical SMILES of solvent(s) |
| composition | list[float] | Mole fractions of solvent components |
| logS | float | Solubility in log(mol/L) |
| mw | float | Molecular weight of solute |

### 4.2 Processed Dataset
| Field | Type | Description |
|:--- |:--- |:--- |
| solute_fp | array[int] | Morgan fingerprint vector |
| solvent_desc | array[float] | Weighted solvent descriptors |
| interaction_terms | array[float] | Generated interaction features |
| logS | float | Target variable |

---

## 5. Assumptions & Gaps

- **DSSTox Exclusion**: As noted in FR-001, DSSTox is excluded due to stoichiometry complexity.
- **Mixed Solvent Data**: If insufficient mixed-solvent data exists (< 100 rows), the system will pivot to pure solvent prediction logic.
- **Abraham Parameters**: If the `solv` package is unavailable, a fallback linear regression using standard Abraham parameters (a, b, c, s, v, r) will be used.

---

## 6. Revision History

| Version | Date | Author | Description |
|:--- |:--- |:--- |:--- |
| 1.0 | 2023-10-27 | System | Initial Draft |
| 1.1 | 2023-10-28 | System | **Amendment T011b**: Explicitly documented DSSTox exclusion in FR-001 citing Plan "Assumptions & Gaps". |