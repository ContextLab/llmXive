# Implementation Plan: Predicting Molecular Polarity from SMILES Strings with Machine Learning

**Branch**: `001-predict-molecular-polarity` | **Date**: 2026-07-13 | **Spec**: `specs/001-predicting-molecular-polarity/spec.md`
**Input**: Feature specification from `/specs/001-predicting-molecular-polarity/spec.md`

## Summary
This project implements a machine learning pipeline to predict molecular dipole moments (polarity) using **exclusively** 2D topological descriptors derived from SMILES strings. The system will utilize the QM dataset as the source of truth for both SMILES strings and target dipole values. The core innovation is the strict exclusion of 3D conformer generation, TPSA, and functional group SMARTS patterns to isolate the information content of 2D topology. The pipeline involves data ingestion, rigorous 2D feature engineering (RDKit), LightGBM regression training, and **Cluster-Aware SHAP** interpretability. All operations are constrained to run on CPU-only CI resources (≤6GB RAM, ≤6h runtime).

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `rdkit`, `lightgbm`, `pandas`, `numpy`, `scikit-learn`, `shap`, `pyyaml`, `pytest`  
**Storage**: Local file system (Parquet/CSV) for data; `.pkl` for model artifacts  
**Testing**: `pytest` (unit, integration, contract tests)  
**Target Platform**: GitHub Actions free-tier runner (Linux, CPU-only)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Peak memory < 6 GB; Runtime < 6 hours; **R² must be statistically significantly greater than 0.0 (Null Model) via permutation test (p < 0.05)**.  
**Constraints**: NO 3D geometry generation (`EmbedMolecule`, `Get3DConformer`); NO GPU; NO TPSA/Functional Group features; **NO arbitrary feature removal based on VIF** (VIF used for diagnostic clustering only).  
**Scale/Scope**: QM9 dataset (sampled to fit memory); A set of 2D descriptors; **Cluster-Aware SHAP analysis with multiple bootstrap iterations (SHAP-only resampling)**.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Verification Method | Reference in Constitution |
|-----------|---------------------|---------------------------|
| **I. Reproducibility** | `requirements.txt` pins all deps; random seeds hardcoded in `code/`; dataset source pinned to verified URL. | [Section I](constitution.md#i-reproducibility-non-negotiable) |
| **II. Verified Accuracy** | Dataset URLs in `research.md` strictly limited to the "Verified datasets" block provided in the prompt. | [Section II](constitution.md#ii-verified-accuracy-inherits-parent-principle-ii) |
| **III. Data Hygiene** | Raw QM9 data downloaded to `data/raw/` with checksum; derived features written to `data/processed/` with new filenames. | [Section III](constitution.md#iii-data-hygiene) |
| **IV. Single Source of Truth** | All metrics (R², RMSE, SHAP values) generated programmatically from `data/processed/` and `code/`; no hand-typed numbers in paper. | [Section IV](constitution.md#iv-single-source-of-truth-inherits-parent-principle-i) |
| **V. Versioning Discipline** | Content hashes for data artifacts tracked in `state/`; `updated_at` timestamps managed by advancement evaluator. | [Section V](constitution.md#v-versioning-discipline) |
| **VI. 2D-Topological Fidelity** | Pipeline explicitly excludes 3D functions (FR-006, FR-001); unit test asserts no 3D calls. | [Section VI](constitution.md#vi-2d-topological-fidelity) |
| **VII. Computational Constraint Adherence** | Memory checks (FR-006) and CPU-only LightGBM (FR-002) ensure feasibility on free-tier CI. | [Section VII](constitution.md#vii-computational-constraint-adherence) |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-molecular-polarity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── model_output.schema.yaml
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── download_qm9.py          # Fetches and checksums raw data
│   ├── preprocess_2d.py         # Generates 2D descriptors (excludes 3D/TPSA)
│   ├── feature_clustering.py    # Computes correlation matrix and clusters (VIF diagnostic only)
│   └── split_data.py            # Train/test split
├── models/
│   ├── train_lightgbm.py        # Model training and CV
│   ├── evaluate.py              # Metrics calculation
│   └── interpret.py             # Cluster-Aware SHAP and bootstrapping
├── utils/
│   ├── config.py                # Global seeds and paths
│   └── validators.py            # Assertions for 3D exclusion
├── main.py                      # Orchestration script
└── requirements.txt

tests/
├── contract/
│   ├── test_dataset_schema.py   # Validates input/output schemas
│   └── test_model_output.py     # Validates prediction formats
├── unit/
│   ├── test_preprocess.py       # Tests descriptor generation logic
│   └── test_3d_exclusion.py     # Asserts no 3D functions are called
└── integration/
    └── test_full_pipeline.py    # End-to-end run on small batch

data/
├── raw/                         # Downloaded QM9 parquet (immutable)
└── processed/                   # Feature matrices and splits
```

**Structure Decision**: A linear, script-based pipeline (`code/data`, `code/models`) is selected over a library pattern to ensure strict control over execution order and resource usage for the CI environment. The `code/` directory is self-contained within the project root for simplicity.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Cluster-Aware SHAP** | Required by FR-005/SC-003 to validate signal in correlated clusters without arbitrary pruning. | Simple VIF pruning removes signal; correlation filtering ignores multi-variable dependencies. |
| **Two-Stage Bootstrap** | Required to meet 6h runtime on CPU while maintaining statistical validity for stability. | Full re-training 100x exceeds runtime; single-split SHAP is unstable. |
| **Strict 3D Exclusion Test** | Required by Constitution Principle VI and FR-006. | Relying on documentation alone is insufficient; automated assertion is needed to prevent accidental 3D leakage. |
| **SHAP Interaction Values** | Required to attribute signal within correlated clusters (methodology concern). | Standard SHAP splits credit arbitrarily; Interaction values provide a rigorous attribution for collinear features. |

## Functional Requirements (Updated)

- **FR-001**: System MUST parse SMILES strings and generate a feature matrix of ≥200 2D topological descriptors using `rdkit.Chem.Descriptors` and `rdkit.Chem.rdMolDescriptors` (excluding 3D functions). The system MUST explicitly exclude: (a) TPSA, TPSA_E, and any surface-area proxies; (b) direct functional group identifiers (SMARTS patterns for -OH, -C=O, etc.). **CRITICAL: The system MUST NOT exclude features based on correlation with the target (|r| > 0.85) as this would invalidate the hypothesis test.** (See US-1).
- **FR-002**: System MUST train a Gradient Boosting Regressor (LightGBM) on the 2D feature matrix to predict dipole moments, ensuring strict separation between training and test sets using a standard random split (no target binning or stratification) (See US-2).
- **FR-003**: System MUST implement k-fold cross-validation to tune hyperparameters and prevent overfitting, logging all random seeds for reproducibility (See US-2).
- **FR-004**: System MUST apply SHAP analysis to the trained model to quantify the contribution of individual 2D descriptors to the dipole moment prediction (See US-3).
- **FR-005**: System MUST perform a feature-set stability analysis by bootstrapping the dataset multiple times (sample size [deferred]) and verifying that the **top clusters of correlated features** remain consistent (Jaccard similarity ≥ 0.7) across resamples. **Method: Two-Stage Bootstrap (SHAP-only resampling) to ensure runtime feasibility.** (See US-3).
- **FR-006**: System MUST process the QM dataset in batches to ensure peak memory usage remains within feasible operational limits. The system MUST implement NaN handling (median imputation or record drop) as a prerequisite for stable batch processing, and MUST include a runtime assertion and a dedicated unit test that asserts no 3D conformer generation functions (e.g., `rdkit.Chem.AllChem.EmbedMolecule`, `Get3DConformer`) are called during the descriptor generation pipeline (See US-1, Edge Cases: NaN handling).
- **FR-007**: System MUST calculate Variance Inflation Factor (VIF) for all generated descriptors **for diagnostic clustering purposes only**. The system MUST group highly correlated descriptors (|r| > 0.8) into clusters and report the aggregate importance of these clusters. **No features are removed based on VIF thresholds.** This logic resides in `code/data/feature_clustering.py` (See US-3).

## Success Criteria (Updated)

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The variance explained (R²) by the 2D-only model is measured against the variance explained by a null model that predicts the mean dipole moment of the training set (R²=0.0) (See US-2).
- **SC-002**: The contribution of specific 2D descriptors is measured against the SHAP value magnitude to identify the "strongest signal" features **within clusters** (See US-3).
- **SC-003**: The sensitivity of the model to the feature set is measured by the Jaccard similarity of the **top 10 feature clusters** across 100 bootstrap resamples (See US-3).
- **SC-004**: The computational feasibility is measured by the total runtime on the GitHub Actions free-tier runner (CPU only, ≤6h) and peak memory usage (≤6 GB) (See US-1, US-2).
- **SC-005**: The methodological validity is measured by an automated unit test that asserts no function in the pipeline calls RDKit's `EmbedMolecule` or `Get3DConformer`, verifying the absence of 3D geometry leakage (See US-1).

## Assumptions

- The QM9 dataset is available via `wget`/`curl` from the Maxwell Institute or Zenodo without requiring authentication or paid access.
- The QM9 dataset contains the necessary dipole moment values (target variable) and SMILES strings (source) for all molecules required for the analysis.
- RDKit is available in the GitHub Actions environment with sufficient functionality to compute 200+ 2D descriptors without 3D conformer generation.
- The GitHub Actions free-tier runner provides at least 2 CPU cores and 6 GB of RAM, sufficient for the LightGBM training on the sampled dataset.
- The relationship between 2D topological features and dipole moments is empirically testable without requiring random assignment (observational study framing).
- The QM9 dataset's dipole moments are calculated using a consistent quantum mechanical method, ensuring the target variable is homogeneous.
- No GPU acceleration is required or available; all computations must be CPU-tractable.
- The dataset variables (predictors and outcomes) are fully contained within the QM9 release; no external data sources are needed for the 2D descriptors.
- Schema contracts reside in `tests/contract/` relative to the project root, ensuring compatibility with the `quickstart.md` and `data-model.md` test runners.