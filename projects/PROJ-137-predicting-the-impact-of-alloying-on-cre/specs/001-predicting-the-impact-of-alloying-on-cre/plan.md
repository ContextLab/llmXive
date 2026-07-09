# Implementation Plan: Predicting the Impact of Alloying on Creep Resistance via Public Data

**Branch**: `001-predicting-impact-of-alloying-on-creep-resistance` | **Date**: 2026-07-10 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predicting-impact-of-alloying-on-creep-resistance/spec.md`

## Summary

This project implements a machine learning pipeline to predict creep resistance (rupture time) of alloys using public data. The core approach involves downloading the NIMS Creep Data Center dataset (or generating synthetic data if unavailable), augmenting it with thermodynamic descriptors (mixing enthalpy, atomic radius mismatch) calculated via `pymatgen`, and training Gradient Boosting Regressors. A strict comparison is performed between a model using these physics-informed descriptors against **two baselines**: one using raw elemental **Atomic%** fractions and another using raw Atomic% plus polynomial features. The workflow enforces **Strict Intersection** (all models trained on identical sample sets) and Nested Cross-Validation to mitigate overfitting on the small dataset. Specific statistical tests (Corrected Resampled t-test or Bootstrap) are employed to validate the predictive gain of the thermodynamic features.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `pymatgen`, `shap`, `requests`, `jsonschema`  
**Storage**: Local CSV/Parquet files in `data/`  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM, No GPU)  
**Project Type**: Data Science / Machine Learning Pipeline  
**Performance Goals**: Complete full pipeline (download, process, train, evaluate, plot) within 6 hours on CPU.  
**Constraints**: No GPU usage; strict memory management (<7GB RAM); no deep learning; must handle API rate limits and missing data gracefully.  
**Scale/Scope**: Small dataset regime (N < 100 expected); single-feature importance analysis; comparative model evaluation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`; external datasets fetched from canonical sources or generated synthetically; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | No verified URL for NIMS Creep Data exists in the prompt. The plan correctly identifies the **Synthetic Fallback** (FR-008) as the **primary execution path** to ensure reproducibility and accuracy without relying on unverified or mismatched sources. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/`; processed data written to `data/processed/` with checksums; no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in final report trace to `data/processed/` rows and `code/` scripts. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes tracked in state file; `updated_at` timestamp updated on artifact change. |
| **VI. Physics-Informed Feature Integrity** | **PASS** | Descriptors (mixing enthalpy, radius mismatch) computed strictly via `pymatgen` local elemental properties; no manual calculation. |
| **VII. Microstructure-Agnostic Scope** | **PASS** | Input features limited to composition and thermodynamic descriptors; microstructural data explicitly excluded. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-impact-of-alloying-on-creep-resistance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Schema files generated here)
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, API keys
├── data/
│   ├── __init__.py
│   ├── download.py      # NIMS & Materials Project fetching
│   ├── preprocess.py    # Composition parsing, feature engineering
│   └── synthetic.py     # Synthetic data generation fallback
├── models/
│   ├── __init__.py
│   ├── train.py         # Nested CV, model training
│   └── evaluate.py      # Statistical testing, SHAP analysis
├── utils/
│   ├── __init__.py
│   └── logging.py
├── main.py              # Orchestration script
└── requirements.txt

tests/
├── __init__.py
├── contract/
│   └── test_schemas.py  # Validates against contracts/*.schema.yaml (Phase 1 output)
├── integration/
│   └── test_pipeline.py # End-to-end synthetic run
└── unit/
    ├── test_preprocess.py
    └── test_models.py

data/
├── raw/
│   └── nims_creep.parquet
├── processed/
│   └── alloy_features.csv
└── checksums.json
```

**Structure Decision**: Single project structure (`code/`) chosen. The project is a linear data science pipeline (Download -> Process -> Train -> Evaluate) without separate frontend/backend services. This minimizes overhead and aligns with the "Scriptable Research" pattern required for GitHub Actions execution.

**Note on Contracts**: The `contracts/` directory contains schema definitions (`dataset.schema.yaml`, `model_output.schema.yaml`, `output.schema.yaml`) generated as **Phase 1** outputs. These files are explicitly validated against synthetic data in **Phase 2** (Step 2b) before training begins, ensuring `tests/contract/test_schemas.py` can validate the data integrity.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Nested Cross-Validation** | Required by FR-007 for unbiased performance estimation on small N (<100). | Simple hold-out test set would lead to high variance and unreliable performance estimates due to small sample size. |
| **Strict Intersection** | Required to ensure paired statistical testing (FR-005). Models must be trained on identical sample sets. | Training on different sample sizes (N_thermo < N_baseline) invalidates the statistical test for 'marginal gain'. |
| **Two Baselines (Polynomial)** | Required to isolate physics-based features from generic non-linearity (Scientific Soundness). | A single linear baseline would not account for the model's ability to learn non-linear transforms from raw features. The comparison is strictly against the **Polynomial Baseline** (Atomic% + Poly). |
| **Synthetic Fallback** | Required by FR-008 to ensure pipeline executability if external APIs fail. | Hard-failing on API errors would make the CI pipeline flaky and untestable in isolated environments. |
| **Statistical Test Switching** | Required by FR-005 to handle small N (<20) vs. larger N (>=20) appropriately. | Using a standard t-test on overlapping folds violates independence assumptions; using Wilcoxon on small N lacks power. |
| **Joint Stratification** | Required to control for variance in both Temperature and Stress. | Stratifying by Temperature alone leaves Stress distribution unbalanced. |
| **Synthetic Fallback to Schema Validation** | Required by FR-008 to ensure the generated data matches the expected schema before training. | **Step 2b** explicitly maps the Synthetic Fallback to the validation against `contracts/dataset.schema.yaml`, ensuring the execution flow is clear and consistent with the Edge Cases in spec.md. |

## Data Flow & Execution Order

1.  **Step 1: Data Acquisition**: Attempt to fetch NIMS data and Materials Project thermodynamics.
    *   If NIMS URL is unreachable or schema mismatched (e.g., MedQuad), **immediately trigger Synthetic Data Generation**.
2.  **Step 2: Preprocessing & Feature Engineering**:
    *   Parse compositions to **Atomic%** for ALL samples.
    *   Compute thermodynamic descriptors.
    *   **Strict Intersection**: Drop any row missing thermodynamic data from **ALL** models (Thermo, Linear, Polynomial).
3.  **Step 2b: Synthetic Data Schema Validation** (Explicit FR-008 Step):
    *   If synthetic data was generated, validate it against `contracts/dataset.schema.yaml`.
    *   **Block** training if validation fails.
4.  **Step 3: Model Training**:
    *   Train Thermodynamic Model, Linear Baseline (Atomic%), and Polynomial Baseline (Atomic% + Poly).
    *   Execute Nested CV (Joint Stratification by Temperature and Stress).
5.  **Step 4: Evaluation**:
    *   Compute metrics and statistical tests on the strict intersection.
    *   Generate SHAP plots.
6.  **Step 5: Reporting**:
    *   Generate final report and save artifacts.

## FR/SC Mapping

| Spec ID | Plan Step | Notes |
| :--- | :--- | :--- |
| FR-001 | Step 1 | Data Acquisition & Fallback. |
| FR-002 | Step 2 | Atomic% conversion & **Strict Intersection** (Exclusion from ALL models). |
| FR-003 | Step 2 | Feature Engineering. |
| FR-004 | Step 3 | Three-model training (Thermo, Linear, Polynomial) & Joint Stratification. |
| FR-005 | Step 4 | Statistical testing on intersection. |
| FR-006 | Step 4 | SHAP Analysis. |
| FR-007 | Step 3 | Nested CV. |
| FR-008 | Step 2b | **Explicit Synthetic Data Schema Validation**. |
| SC-001 | Step 4 | R² comparison against **Polynomial Baseline**. |
| SC-002 | Step 4 | Statistical significance. |
| SC-003 | Step 4 | SHAP importance. |
| SC-004 | Step 1 | Data pipeline success rate. |
| SC-005 | Step 5 | Runtime check. |

**Note on Spec Contradiction**: The source spec (User Story 3, FR-002, Assumptions, Edge Cases) currently states that entries missing thermodynamic data should be retained for the composition-only baseline. This contradicts the **Strict Intersection** policy required for valid statistical testing (addressing panel concerns). The plan enforces **Strict Intersection** (exclusion from ALL models) to ensure scientific validity. The source spec requires a kickback to align with this methodology.