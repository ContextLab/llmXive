# Implementation Plan: Statistical Analysis of Publicly Available Climate Model Output Ensembles

**Branch**: `001-climate-fPCA-robustness` | **Date**: 2026-07-19 | **Spec**: `specs/001-climate-fPCA-robustness/spec.md`

## Summary
This project implements a robust statistical pipeline to analyze CMIP6 climate model ensembles. It ingests raw temperature and precipitation data, transforms discrete time-series into smooth continuous functions via B-spline basis expansion (adhering to **FR-001**, **FR-002**), and performs Functional Principal Component Analysis (fPCA) to extract dominant spatiotemporal modes (**FR-003**). The core innovation is a **Leave-One-Out (LOO) Jackknife** protocol (**FR-004**, **FR-005**) to quantify the stability of these modes against the removal of specific models or model families, ensuring results are not driven by single model lineages (**Constitution Principle VI**). The pipeline is designed to run entirely on CPU within GitHub Actions free-tier constraints (**SC-003**).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scikit-fda` (exclusive library for fPCA/B-splines), `matplotlib`, `seaborn`, `datasets` (HuggingFace), `pyyaml`, `procrustes` (for subspace alignment).  
**Storage**: Local filesystem (`data/` for raw/processed, `artifacts/` for results). No external DB.  
**Testing**: `pytest` with `pytest-randomly` for reproducibility checks.  
**Target Platform**: Linux (GitHub Actions Runner: multiple CPUs, ample RAM).  
**Project Type**: Data analysis pipeline / CLI tool.  
**Performance Goals**: Complete full pipeline (ingestion -> fPCA -> LOO Jackknife) within 6 hours on CPU. Memory usage < 6 GB.  
**Constraints**: Must handle missing data via spline-based imputation; Global basis dimension $K$ determined via Pilot GCV/AIC; No GPU dependency.  
**Scale/Scope**: CMIP6 ensemble (variable size, processed via streaming/stratified sampling to fit memory).

> **Dataset Variable Fit & Feasibility Note**: The verified datasets provided are small test files. The plan assumes these are representative samples of the full CMIP6 structure. For the full analysis, the implementation will use the `datasets` library to stream the full HuggingFace dataset `sungduk/wip_cmip6` (or the specific version referenced). If the full dataset exceeds RAM, a **fixed-seed stratified random sample** (stratified by model family) will be used. This stratified sample serves as the fixed "full ensemble" baseline for the LOO Jackknife, ensuring the baseline is not a random variable.

## Constitution Check

| Principle | Compliance Status | Action / Mapping |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/`. `requirements.txt` pins versions. Data fetched from canonical HF URLs. |
| **II. Verified Accuracy** | **Compliant** | Citations in `research.md` will only use verified HF URLs. No external URLs invented. |
| **III. Data Hygiene** | **Compliant** | Raw data checksummed on download. Derivations written to new files in `data/processed/`. |
| **IV. Single Source of Truth** | **Compliant** | All metrics (variance, stability) computed from `data/processed/` and logged; no hand-typed values. |
| **V. Versioning Discipline** | **Compliant** | **New Step**: `code/update_state.py` computes artifact hashes and updates `state/projects/...yaml` with the new hash and timestamp. |
| **VI. Ensemble Robustness** | **Compliant** | **FR-004** & **FR-005** now implement LOO Jackknife (and Block Jackknife) to test sensitivity to specific model removal, replacing circular bootstrap. |
| **VII. Spatiotemporal Structure** | **Compliant** | **FR-002** mandates B-spline basis expansion with spline-based imputation to preserve continuity; **FR-003** uses fPCA for structure. |

## Project Structure

### Documentation (this feature)
```text
specs/001-climate-fPCA-robustness/
├── plan.md              # This file
├── research.md          # Phase 0: Dataset strategy, methodological rigor
├── data-model.md        # Phase 1: Schemas, data flow
├── quickstart.md        # Phase 1: Setup, run instructions
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 (Generated later)
```

### Source Code (repository root)
```text
projects/PROJ-231-statistical-analysis-of-publicly-availab/
├── code/
│   ├── __init__.py
│   ├── config.py          # Paths, seeds, hyperparams
│   ├── ingestion.py       # FR-001: Download, schema check, spline impute, standardize
│   ├── basis.py           # FR-002: Pilot GCV/AIC -> Global K, B-spline expansion
│   ├── fpca.py            # FR-003: fPCA execution
│   ├── robustness.py      # FR-004, FR-005: LOO Jackknife, Procrustean stability metrics
│   ├── visualize.py       # FR-006: Plotting dominant modes
│   ├── update_state.py    # V5: Hash artifacts, update state YAML
│   └── main.py            # Orchestration script
├── data/
│   ├── raw/               # Downloaded parquet files (checksummed)
│   ├── processed/         # B-spline coefficients, standardized arrays
│   └── artifacts/         # Jackknife results, plots
├── tests/
│   ├── unit/
│   │   ├── test_ingestion.py
│   │   └── test_basis.py
│   └── contract/
│       └── test_schemas.py  # Validates data/raw vs dataset.schema.yaml AND data/processed vs output.schema.yaml
└── requirements.txt
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) is selected. The analysis is a linear pipeline (Ingest -> Transform -> Analyze -> Validate) rather than a service, making a modular CLI structure most appropriate for reproducibility and testing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **LOO Jackknife (N iterations)** | Required by **FR-004** to assess stability against specific model/family removal. Replaces circular bootstrap. | Simple random bootstrap fails to test sensitivity to specific model families and creates circular validation. |
| **Pilot-based Global Basis Selection** | Required by **FR-002** to handle irregular time steps while maintaining memory feasibility. | Streaming global GCV/AIC is impossible; local selection destroys global comparability. |
| **Stratified Sampling** | Required to maintain ensemble diversity if full data exceeds memory. | Simple random sampling risks excluding critical model families, biasing the LOO results. |
| **Spline-based Imputation** | Required to preserve derivative structure for fPCA. | Linear interpolation introduces artificial linearity and biases high-frequency modes. |

## Versioning Workflow (Constitution Principle V)

To ensure the Single Source of Truth (SSoT) is maintained:
1.  Upon completion of the analysis, `code/main.py` triggers `code/update_state.py`.
2.  `update_state.py` computes SHA256 hashes for all files in `data/processed/` and `artifacts/`.
3.  The script updates `state/projects/PROJ-231-statistical-analysis-of-publicly-availab.yaml` with the new `artifact_hashes` map and `updated_at` timestamp.
4.  The Advancement-Evaluator Agent uses this state file to validate the stage transition.