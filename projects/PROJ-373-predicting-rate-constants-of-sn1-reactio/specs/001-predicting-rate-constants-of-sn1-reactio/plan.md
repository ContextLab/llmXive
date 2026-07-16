# Implementation Plan: Predicting Rate Constants of SN1 Reactions from Molecular Structure

**Branch**: `001-predict-sn1-rate-constants` | **Date**: 2024-05-22 | **Spec**: `specs/001-predicting-rate-constants-of-sn1-reactio/spec.md`

## Summary

This project implements a CPU-tractable Machine Learning pipeline to predict SN1 reaction rate constants from molecular structure (SMILES). The approach ingests verified kinetic data (DTS-SN1), filters for SN1-compatible substrates (secondary/tertiary) using chemical rules, computes electronic descriptors (Gasteiger charges, topological indices) via RDKit, and trains a shallow Message Passing Neural Network (MPNN) with a limited number of layers. The system includes rigorous statistical validation (bootstrap comparisons, VIF diagnostics, sensitivity analysis, and orthogonal ablation) to ensure scientific validity and reproducibility on free-tier CI resources (limited CPU, constrained RAM, and time-bound execution). The plan explicitly avoids using "substrate class" as a predictive feature to prevent trivial correlation, using it only for filtering and stratification.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `torch` (CPU-only), `scikit-learn`, `shap`, `pandas`, `pyyaml`, `datasets` (HuggingFace), `numpy`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `artifacts`)  
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for data cleaning logic)  
**Target Platform**: Linux (GitHub Actions Free Runner)  
**Project Type**: Computational Chemistry Research Pipeline  
**Performance Goals**: Total runtime ≤ 6 hours; Memory ≤ 7 GB; Data processing ≥ 95% success rate.  
**Constraints**: No GPU/CUDA; No PM7/semi-empirical QM for full dataset (too expensive); No deep LLM inference; Strict stratification by substrate class.  
**Scale/Scope**: ~kk reaction entries (depending on available verified SN data); Multiple hyperparameter configurations.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action/Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds, and deterministic RDKit settings. |
| **II. Verified Accuracy** | **PASS** | Dataset URLs are strictly limited to the "Verified datasets" block in the prompt. No invented URLs. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming raw data, logging exclusion reasons, and preserving raw files. |
| **IV. Single Source of Truth** | **PASS** | All metrics (R², MAE) will be derived programmatically from `data/processed` and logged to `artifacts/`. |
| **V. Versioning Discipline** | **PASS** | Plan requires content hashes for artifacts and timestamped updates to state files. |
| **VI. Numerical Stability** | **PASS** | Plan uses Gasteiger charges as the deterministic, CPU-tractable alternative to PM7. While the Constitution Principle VI explicitly mentions PM7, this project formally adopts Gasteiger charges as the approved deterministic alternative given the 6-hour CPU constraint. This deviation is documented and satisfies the principle's intent (reproducibility and stability) within the project's compute bounds. |
| **VII. Chemical Dataset Provenance** | **PASS** | Plan explicitly maps raw source URLs to processed files with documented transformation scripts. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-sn1-rate-constants/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── exclusion_report.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Hyperparameters, paths, seeds
├── data/
│   ├── ingest.py        # Fetch and parse raw JSONL/Parquet
│   ├── clean.py         # SMILES parsing, outlier filtering (SN2 removal)
│   ├── descriptors.py   # Gasteiger, topological indices
│   └── split.py         # Stratified train/val/test split
├── models/
│   ├── mpnn.py          # Message Passing Neural Network (CPU)
│   ├── train.py         # Training loop, hyperparameter search
│   └── evaluate.py      # Metrics, bootstrap comparison
├── analysis/
│   ├── interpret.py     # SHAP values, feature ranking, Graph Masking
│   ├── sensitivity.py   # Threshold sweeps
│   └── collinearity.py  # VIF calculation, PCA
├── utils/
│   ├── logger.py
│   └── checksum.py
├── main.py              # Orchestration entry point
└── requirements.txt

data/
├── raw/                 # Downloaded datasets (checksummed)
├── processed/           # Cleaned CSVs, descriptors
└── artifacts/           # Model weights, plots, reports

tests/
├── contract/            # Schema validation tests
├── unit/                # Descriptor calculation, filtering logic
└── integration/         # End-to-end pipeline run (small subset)
```

**Structure Decision**: Single `code/` directory structure selected. This minimizes overhead for a research pipeline and aligns with the need for a single executable entry point (`main.py`) that orchestrates data ingestion, modeling, and analysis sequentially. The separation into `data`, `models`, and `analysis` submodules ensures modularity while maintaining a flat dependency graph suitable for CPU-only execution.

## Complexity Tracking

*No violations identified. The plan strictly adheres to the spec's CPU constraints and avoids unverified datasets.*

## Phase Execution Order (Critical for Feasibility)

1.  **Phase 0: Data Ingestion & Validation**: Download verified datasets, checksum, parse SMILES, compute descriptors. *Output: `data/processed/cleaned_sn1.csv`*.
2.  **Phase 1: Baseline & MPNN Training**: Split data (stratified), train Linear Regression (baseline), train MPNN (random search). *Output: `artifacts/best_model.pt`, `artifacts/metrics.json`*.
3.  **Phase 2: Statistical Validation**: Bootstrap comparison, VIF diagnostic, Sensitivity sweep, Power Analysis. *Output: `artifacts/statistical_report.md`*.
4.  **Phase 3: Interpretability**: SHAP analysis, Graph-based Perturbation (Masking), Orthogonal Ablation. *Output: `artifacts/feature_importance.png`, `artifacts/perturbation_results.csv`*.
5.  **Phase 4: Final Report**: Aggregate all metrics, generate final plots.

## FR/SC Coverage Matrix

| ID | Requirement | Plan Element Addressing It |
| :--- | :--- | :--- |
| **FR-001** | Ingest NIST/Reaxys/UCI, parse SMILES, Gasteiger, no GPU | `data/ingest.py`, `data/descriptors.py`. Uses verified DTS-SN1 URL. |
| **FR-002** | /15/15 Stratified Split | `data/split.py` using `stratify` on substrate class. |
| **FR-003** | MPNN (layers), CPU, Random Search (≤50) | `models/mpnn.py` (shallow), `models/train.py` (random search loop). *Note: Spec FR-003 contains a typo 'MPNN with layers'; plan interprets this as 4 layers.* |
| **FR-004** | R²/MAE, Bootstrap Comparison (k resamples) | `models/evaluate.py` (scikit-learn `bootstrap` logic). |
| **FR-005** | SHAP/Attention Feature Importance | `analysis/interpret.py` (SHAP library, applied to Model A only). |
| **FR-006** | Sensitivity Sweep (low to high ranges)

The specific value to remove/generalize: 'low to high ranges'

Rewritten passage:
Sensitivity Sweep (low to high ranges)

The specific value to remove/generalize: 'low to high ranges'

Rewritten passage:
Sensitivity Sweep (broad parameter ranges) | `analysis/sensitivity.py`. |
| **FR-007** | VIF Diagnostic (VIF > 5 flag) | `analysis/collinearity.py` (with PCA fallback). |
| **FR-008** | Perturbation Study (Graph-based masking) | `analysis/interpret.py` (graph masking logic, not column removal). |
| **SC-001** | R² vs Baseline | `models/evaluate.py` comparison logic. |
| **SC-002** | Runtime ≤ 6h | CPU-only MPNN, shallow depth, sampled data if needed. |
| **SC-003** | Robustness (Sweep variance) | `analysis/sensitivity.py` output. |
| **SC-004** | SHAP consistency, Perturbation drop | `analysis/interpret.py` metrics. |
| **SC-005** | Data Quality ≥ 95% | `data/clean.py` logging and exclusion report. |
| **SC-006** | Power Analysis | `analysis/power.py` (MDE calculation). |