# Implementation Plan: Identifying Structure-Property Relationships in Polymer Blends

**Branch**: `001-structure-property-relationships` | **Date**: 2024-05-21 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-structure-property-relationships/spec.md`

## Summary

This project implements a reproducible, CPU-only pipeline to identify structure-property relationships in polymer blends using public data. The approach aggregates data from Polymer Database, NIST, and Materials Project (subject to verification), harmonizes units (Kelvin, GPa), generates molecular descriptors via RDKit, computes blend interaction features (Fox/Gordon-Taylor), and trains Random Forest/XGBoost models to predict Tg_residual and Young's Modulus. **Critical Constraint**: The pipeline includes a mandatory "Data Verification Gate" (FR-015). If no verified dataset containing SMILES, Composition, Tg, and Modulus is found, the main blend-prediction pipeline halts, and the system switches to a "Monomer-Level Fallback" track (predicting monomer properties from descriptors only) as defined in FR-013. The pipeline includes rigorous statistical validation (paired t-tests, VIF sensitivity analysis, SHAP interpretability) and strict data hygiene (checksums, versioning) as mandated by the project constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `rdkit`, `scikit-learn`, `xgboost`, `shap`, `pyyaml`, `requests`, `joblib`, `hashlib`, `hansen-solubility` (if available), `polymer-properties` (if available)  
**Storage**: Local files (`data/raw/`, `data/processed/`), `state/projects/PROJ-122-identifying-structure-property-relations.yaml` for artifact tracking  
**Seeds**: Pinned in `config.py` (global seed = 42, plus independent runs with seeds -5)  
**Testing**: `pytest` (unit, integration, contract tests)  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 CPU, 7 GB RAM, no GPU)  
**Project Type**: Data Science / Computational Materials Science Pipeline  
**Performance Goals**: Full pipeline execution ≤ 5 hours; memory usage ≤ 6 GB; dataset sampling if > 7 GB RAM  
**Constraints**: No GPU/CUDA; no 8-bit quantization; no large-LLM inference; strict adherence to verified dataset URLs; no un-spec'd constraints  
**Scale/Scope**: Targeting public datasets; N < 1000 samples (expected); + descriptors per monomer; k-fold cross-validation

The specific value to remove/generalize: 'k'

Rewritten passage:
k-fold cross-validation or random split based on N  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Strategy | Status |
|------------------------|---------------------|--------|
| **I. Reproducibility** | All seeds pinned in `config.py`; datasets fetched from canonical sources; `requirements.txt` pinned; CI runs end-to-end. | ✅ Plan includes seed management (config.py) and deterministic splits. |
| **II. Verified Accuracy** | Reference-Validator Agent checks all citations; `CITATION_TITLE_OVERLAP_THRESHOLD` ≥ 0.7 enforced; only verified URLs used. | ✅ Plan mandates URL verification before ingestion (FR-015). **Conditional**: If no verified URL, gate fails and fallback activates. |
| **III. Data Hygiene** | Checksums recorded in `state/projects/PROJ-122-identifying-structure-property-relations.yaml`; raw data immutable; derivations versioned; PII scan passed. | ✅ Plan includes state file tracking (FR-018) and checksum logic. |
| **IV. Single Source of Truth** | All figures/stats trace to `data/` rows and `code/` blocks; no hand-typed numbers. | ✅ Plan enforces artifact tracing and automated reporting. |
| **V. Versioning Discipline** | Content hashes for all `data/` artifacts; `state/projects/PROJ-122-identifying-structure-property-relations.yaml` updated on change. | ✅ FR-018 and FR-019 implemented. |
| **VI. Standardized Units** | All Tg in Kelvin, Modulus in GPa; physical bounds enforced (T > 0, E ≥ 0). | ✅ FR-001 and FR-014 enforce unit harmonization and sensitivity sweeps. |
| **VII. Computational Descriptor Traceability** | RDKit descriptors generated via versioned pipeline; feature importance reproducible. | ✅ FR-003 and FR-008 ensure descriptor traceability and VIF analysis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-structure-property-relationships/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── 01_ingest.py         # Data download, unit harmonization, validation (FR-001, FR-002, FR-010, FR-011)
├── 01b_sensitivity.py   # Weight-fraction tolerance sweep {0.01, 0.02, 0.05} (FR-014)
├── 02_features.py       # Descriptor generation, interaction features, VIF analysis (FR-003, FR-004, FR-008)
├── 02b_fallback.py      # Component-level prediction mode if blend join fails >50% (FR-013)
├── 03_train.py          # Model training, hyperparameter tuning, cross-validation (Source Stratified Split) (FR-005, FR-009, FR-016)
├── 04_evaluate.py       # Paired t-test, SHAP, feature importance stability (FR-006, FR-007, SC-003, SC-008)
├── 05_metrics.py        # SC-004 (Union dedup + pass rate), SC-009 (Rate limit recovery) calculation
├── 05_report.py         # Final report generation, artifact hashing (FR-018, SC-001, SC-002)
├── utils/
│   ├── validators.py    # Unit conversion, SMILES parsing, weight-fraction checks
│   ├── descriptors.py   # RDKit descriptor calculation + Group Contribution methods for FFV/Hansen
│   └── metrics.py       # MAE, R², VIF, t-test utilities
└── config.py            # Seeds, paths, thresholds, verified URLs

tests/
├── contract/
│   ├── test_dataset_schema.py
│   └── test_output_schema.py
├── integration/
│   ├── test_ingest_pipeline.py
│   ├── test_feature_engineering.py
│   └── test_rate_limit.py  # SC-009: 5 consecutive errors within 30s
└── unit/
    ├── test_descriptors.py
    └── test_metrics.py

data/
├── raw/                 # Downloaded raw files (immutable)
├── processed/           # Harmonized, validated, feature-engineered data
└── state.json           # Temporary cache (deprecated, use state/...)

state/
└── projects/PROJ-122-identifying-structure-property-relations.yaml  # SSoT for hashes (FR-018)
```

**Structure Decision**: Single-project structure with modular scripts for each pipeline stage. This ensures clarity, reproducibility, and ease of testing. The `src/` directory contains all executable logic, `tests/` for validation, and `data/` for artifacts.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Multiple model types (RF, XGBoost, Linear)** | Required by FR-005 and SC-001 to compare predictive performance and establish baseline. | Single-model approach would not satisfy the comparative analysis requirement. |
| **VIF sensitivity analysis** | Required by FR-008 to address collinearity and ensure robust feature importance. | Ignoring collinearity could lead to spurious feature rankings and invalid conclusions. |
| **Source Stratified Split** | Required by FR-016 to address domain shift and ensure generalizability. | Random splitting could bias results if sources have different property distributions. |
| **Exponential backoff for APIs** | Required by FR-010 and SC-009 to handle rate limits robustly. | Simple retry without backoff would cause frequent failures and non-reproducible runs. |
| **Five independent training runs** | Required by FR-009 and SC-008 to assess stability of feature importance. | Single run would not capture variability and could lead to overfitting to a specific seed. |
| **Weight-fraction Sensitivity Sweep** | Required by FR-014 to validate robustness of the ±0.02 tolerance. | Single tolerance check does not satisfy the robustness requirement. |
| **Monomer-Level Fallback** | Required by FR-013 if blend data is insufficient. | Without fallback, the project would yield no results if the primary data source is missing. |

## Execution Flow & Gates

1.  **Gate 1: Data Verification (FR-015)**: Check for verified URL containing SMILES, Composition, Tg, Modulus.
    *   **Pass**: Proceed to `01_ingest.py`.
    *   **Fail**: Trigger `02b_fallback.py` (Monomer-Level Prediction) or Halt with "Data Insufficient" if no monomer data exists.
2.  **Gate 2: Data Quality (SC-004)**: Run `01b_sensitivity.py` and `05_metrics.py` to verify ≥95% pass rate.
    *   **Pass**: Proceed to feature engineering.
    *   **Fail**: Report gap, proceed with available data if >50% valid, else halt.
3.  **Gate 3: Target Variable Availability**: Check if `Tg_measured` and `Tg_1`, `Tg_2` exist.
    *   **Pass**: Compute `Tg_residual` and interaction features.
    *   **Fail**: Skip residual calculation, proceed with monomer descriptors only (if applicable).
4.  **Gate 4: Statistical Validity**: Ensure N ≥ 100 (FR-012).
    *   **Pass**: Proceed to training.
    *   **Fail**: Halt with "Data Insufficiency".
5.  **Gate 5: Rate Limit Recovery (SC-009)**: Verify `01_ingest.py` recovers from 5 consecutive errors within 30s.
    *   **Pass**: Continue.
    *   **Fail**: Halt.