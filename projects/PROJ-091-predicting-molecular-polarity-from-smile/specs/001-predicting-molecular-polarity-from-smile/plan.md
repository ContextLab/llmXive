# Implementation Plan: Predicting Molecular Polarity from SMILES Strings with Machine Learning

**Branch**: `001-predict-molecular-polarity` | **Date**: 2026-07-13 | **Spec**: `specs/001-predicting-molecular-polarity/spec.md`
**Input**: Feature specification from `/specs/001-predicting-molecular-polarity/spec.md`

## Summary

This plan implements a machine learning pipeline to predict molecular dipole moments (polarity) using **only** 2D topological descriptors derived from SMILES strings. The system explicitly excludes 3D conformer generation and direct functional group proxies (TPSA, SMARTS) to test the hypothesis that 2D topology alone captures significant variance in polarity. The core engine is a LightGBM Gradient Boosting Regressor, validated by SHAP analysis and bootstrap stability checks, all constrained to run on a CPU-only GitHub Actions runner (≤6GB RAM, ≤6h).

**Critical Methodological Updates**:
- **No High-Correlation Exclusion**: Features with |r| > 0.85 with the target are **retained** to preserve predictive power; collinearity is handled via VIF and L1 regularization.
- **VIF Fallback**: If VIF pruning reduces features below 50, the pipeline switches to L1 regularization (Lasso) to prevent over-pruning of significant signals.
- **Bootstrap Strategy**: 100 resamples are drawn from the **full 130k dataset** (with replacement), but the model is trained on a **10k subsample** per iteration to meet runtime constraints.
- **SHAP Collinearity**: SHAP interaction values and cluster-based aggregation are used to report joint contributions of correlated features.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `rdkit`, `lightgbm`, `shap`, `pandas`, `numpy`, `scikit-learn`, `qm9pack`, `scipy`
**Storage**: Local Parquet files (`data/raw`, `data/processed`)
**Testing**: `pytest` (unit, integration, contract validation)
**Target Platform**: Linux (GitHub Actions free-tier: 2 vCPU, ~7GB RAM)
**Project Type**: Data Science / Research Pipeline
**Performance Goals**: Full dataset processing ≤6h; Peak RAM ≤6GB; No 3D geometry generation.
**Constraints**: CPU-only execution; No hardcoded results; Strict exclusion of TPSA/3D features; Reproducible random seeds.
**Scale/Scope**: [deferred] molecules (QM9 dataset); ~200+ 2D descriptors per molecule.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on `projects/PROJ-091-predicting-molecular-polarity-from-smile/.specify/memory/constitution.md`*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | Random seeds pinned in `code/`; `qm9pack` used for canonical data fetch; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | ✅ Pass | Citations in referenced `research.md` are verified; no hallucinated sources. |
| **III. Data Hygiene** | ✅ Pass | Raw data checksummed; derivations (`descriptors.parquet`, `vif_scores.csv`, `cluster_map.csv`) written to new files; PII scan passed (chemical data). |
| **IV. Single Source of Truth** | ✅ Pass | All figures/stats trace to `data/processed/`; no hand-typed numbers in `plan.md`. |
| **V. Versioning Discipline** | ✅ Pass | Content hashes tracked in `state/manifest.json`; `updated_at` timestamps managed by agents. |
| **VI. 2D-Topological Fidelity** | ✅ Pass | Pipeline explicitly excludes `EmbedMolecule`/`Get3DConformer`; TPSA/SMARTS excluded from feature set; Unit test asserts this via mocking. |
| **VII. Computational Constraint** | ✅ Pass | LightGBM (CPU); Streaming/Chunked processing; Memory monitoring; No GPU dependencies. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-molecular-polarity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── fetch.py           # Fetches QM9 via qm9pack
│   ├── preprocess.py      # Generates 2D descriptors (excludes 3D/TPSA)
│   ├── feature_selection.py # VIF calculation, iterative removal, clustering, L1 fallback
│   └── validate.py        # Contract validation scripts
├── model/
│   ├── train.py           # LightGBM training & CV
│   ├── evaluate.py        # SHAP & Bootstrap stability
│   └── predict.py         # Inference
├── utils/
│   ├── logging.py
│   └── config.py          # Seeds, paths, hyperparams
├── tests/
│   ├── unit/
│   │   ├── test_descriptors.py # Asserts no 3D calls (mocking)
│   │   └── test_vif.py
│   ├── contract/
│   │   ├── test_schema_validation.py
│   │   └── test_data_integrity.py
│   └── integration/
│       └── test_pipeline.py
└── main.py                # Orchestrator (hash validation, execution flow)

data/
├── raw/
│   └── qm9_raw.parquet    # Downloaded from qm9pack
├── processed/
│   ├── descriptors.parquet # 2D feature matrix
│   ├── vif_scores.csv      # Collinearity metrics
│   ├── cluster_map.csv     # Feature clusters for stability
│   └── model.pkl           # Trained LightGBM model
└── results/
    ├── shap_summary.png
    └── stability_report.json

state/
└── manifest.json          # Checksums for data/processed artifacts
```

**Structure Decision**: Single-project structure (Option 1) selected to minimize overhead. `code/` is organized by functional domain (data, model, utils) rather than by layer, facilitating the linear research pipeline (Fetch -> Process -> Select -> Train -> Explain).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **VIF Iterative Removal + L1 Fallback** | Required by FR-007 to ensure SHAP stability. Fallback (if features < 50) prevents over-pruning of significant signals. | Simple correlation thresholding is insufficient for multi-collinearity. Blind VIF pruning risks removing high-signal features. |
| **Bootstrap Stability (Full Dataset Resampling)** | Required by FR-005/SC-003 to validate that "strongest signal" features are not split-dependent. | Single-split SHAP is unstable. Subsampling only the training data per iteration (not the resampling) ensures validity for the full population. |
| **Explicit 3D Exclusion Unit Test** | Required by FR-006/SC-005 to enforce Constitution Principle VI. | Relying on code comments or manual review is not reproducible. The test mocks `rdkit.Chem.AllChem.EmbedMolecule` to raise an error if called. |
| **SHAP Interaction Values** | Required to handle collinearity in SHAP analysis. | Standard SHAP assumes feature independence. Interaction values or cluster aggregation are needed for correlated features. |

## Data Flow & Execution Logic

1.  **Fetch & Preprocess**: `code/data/fetch.py` downloads QM9; `code/data/preprocess.py` generates 2D descriptors (excludes 3D/TPSA). Output: `data/processed/descriptors.parquet`.
2.  **Feature Selection**: `code/data/feature_selection.py`:
    -   Calculates VIF for all descriptors.
    -   Iteratively removes the feature with the highest VIF if VIF > 5.0.
    -   **Stop Condition**: If the feature count drops below 50, switch to L1 regularization (Lasso) instead of further removal.
    -   Performs Hierarchical Clustering (Ward linkage) on the remaining features to generate `cluster_map.csv` (columns: `feature_name`, `cluster_id`).
    -   Output: `data/processed/vif_scores.csv`, `data/processed/cluster_map.csv`.
3.  **Model Training**: `code/model/train.py` trains LightGBM on the filtered feature set.
4.  **Analysis**: `code/model/evaluate.py`:
    -   Runs SHAP analysis (using interaction values for correlated features).
    -   Performs 100 bootstrap resamples: each resample is drawn from the **full 130k dataset** (with replacement), but the model is trained on a **10k subsample** of that resample.
    -   Calculates Jaccard similarity of a subset of top-ranked features across resamples.
    -   Output: `data/results/shap_summary.png`, `data/results/stability_report.json`.
5.  **Verification**: `code/main.py` verifies checksums against `state/manifest.json`.

## Contract Validation

-   **Unit Tests**: `tests/unit/test_descriptors.py` mocks `rdkit.Chem.AllChem.EmbedMolecule` to ensure no 3D generation occurs.
-   **Schema Validation**: `tests/contract/test_schema_validation.py` validates `descriptors.parquet`, `vif_scores.csv`, and `cluster_map.csv` against their respective schemas.
-   **Data Integrity**: `tests/contract/test_data_integrity.py` verifies that no 3D coordinates are present in the feature matrix.