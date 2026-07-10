# Implementation Plan: Predicting Yield Strength of BCC Alloys

**Branch**: `001-bcc-yield-strength` | **Date**: 2024-05-21 | **Spec**: `specs/001-bcc-yield-strength/spec.md`
**Input**: Feature specification from `/specs/001-bcc-yield-strength/spec.md`

## Summary

This feature implements a machine learning pipeline to predict the yield strength of Body-Centered Cubic (BCC) alloys. The approach involves ingesting public materials datasets (MPEA Database and Materials Project), filtering strictly for BCC phase alloys with valid yield strength values, engineering compositional descriptors (atomic radius mismatch, VEC, mixing entropy/enthalpy, electronegativity difference), applying Isometric Log-Ratio (ILR) transformations to handle compositional closure, and training/evaluating regression models (Random Forest, Gradient Boosting, Ridge) on a CPU-constrained environment. The validation strategy uses **Repeated 5-Fold Cross-Validation (10 repeats)** for all dataset sizes N >= 80 to ensure statistical robustness and eliminate the high variance associated with LOOCV.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `periodictable`, `pyyaml`, `pytest`, `pyrolite` (for ILR)  
**Storage**: CSV/Parquet files in `data/` (raw and processed); JSON logs in `logs/`; SHA256 checksums in `state/`  
**Testing**: `pytest` (unit tests for feature engineering, integration tests for pipeline)  
**Target Platform**: GitHub Actions Free-tier (Linux, 2 CPU, ~7 GB RAM, no GPU)  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Full pipeline execution ≤ 6 hours; Memory usage < 6 GB at peak  
**Constraints**: 
- No GPU; No external API calls during CI (periodic table data must be local/static).
- **Pipeline HALTS with a Data Scarcity Warning** if the filtered dataset contains fewer than 80 BCC entries.
- **Validation Strategy**: Repeated 5-Fold CV (10 repeats) for all N >= 80. (Methodology Deviation from spec's LOOCV threshold).
- **Stratification**: Based on binned compositional ranges (ILR features), NOT yield strength.
**Scale/Scope**: Single dataset ingestion, feature engineering, and model comparison for BCC alloys.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds, and deterministic data download scripts. |
| **II. Verified Accuracy** | **PENDING** | **Action**: The primary data source (MPEA DOI) has no verified URL in the block. The pipeline will attempt runtime resolution. If the DOI cannot be resolved to a valid file containing BCC+YieldStrength data, the pipeline halts. The status remains PENDING until this runtime check succeeds. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming raw data, logging rejected entries, and preserving raw files unchanged. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in the final report will be generated programmatically from `data/` and `code/`. |
| **V. Versioning Discipline** | **PASS** | Plan includes explicit SHA256 checksumming of all artifacts and updates to `state/projects/.../artifact_hashes.yaml` and `updated_at` timestamp after every run. |
| **VI. Compositional Feature Integrity** | **PASS** | Plan explicitly requires consistent periodic table references and documented formulas for δ, VEC, etc. Includes VIF check to prevent redundancy. |
| **VII. Crystal-Structure Specificity** | **PASS** | Plan includes a strict filtering step for BCC phase before any modeling. |

## Project Structure

### Documentation (this feature)

```text
specs/001-bcc-yield-strength/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
projects/PROJ-525-predicting-the-yield-strength-of-bcc-all/
├── data/
│   ├── raw/             # Downloaded raw datasets (parquet/csv)
│   ├── processed/       # Filtered and engineered features
│   └── logs/            # Rejection logs, checksums
├── code/
│   ├── __init__.py
│   ├── config.py        # Paths, seeds, constants
│   ├── ingestion.py     # Download and filter (FR-001, FR-002)
│   ├── features.py      # Descriptor calculation + ILR + VIF (FR-003, FR-003.1)
│   ├── modeling.py      # Train, CV, metrics, importance (FR-005, FR-006)
│   └── main.py          # Pipeline orchestrator
├── tests/
│   ├── test_ingestion.py
│   ├── test_features.py
│   └── test_modeling.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. The pipeline is linear (Ingestion -> Features -> Modeling) and fits within a single repository scope. No separate backend/frontend is required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **ILR Transformation** | Compositional data (sums to 1) violates standard regression assumptions (multicollinearity). | Simple normalization is insufficient; ILR is required for statistical validity per FR-003.1. |
| **Repeated 5-Fold CV** | LOOCV is unstable for small N regression; Stratified 80/20 on target is biased. | Repeated 5-Fold provides a robust, low-variance estimate for all N >= 80. |
| **Strict BCC Filtering** | Research question is specific to BCC alloys; mixed phases introduce noise. | Including non-BCC would invalidate the hypothesis (VII). |
| **Electronegativity Diff** | Required by FR-003 to capture chemical bonding effects. | Omitting it would leave a gap in the compositional descriptor set. |
| **VIF Check** | Prevents redundancy between ILR coordinates and scalar descriptors. | Including both without check risks data leakage and inflated importance. |

## Versioning & Hashing

To satisfy Constitution Principle V:
1.  **Artifact Hashing**: Every file generated in `data/processed/` and `code/` will be checksummed using SHA256.
2.  **State Update**: The `state/projects/PROJ-525-predicting-the-yield-strength-of-bcc-all.yaml` file will be updated with the `updated_at` timestamp and the `artifact_hashes` map after each successful pipeline run.
3.  **Traceability**: The `logs/` directory will contain a `run_manifest.json` linking the input dataset hash to the output model metrics hash.

## Phases

### Phase 0: Data Ingestion & Verification (FR-001, FR-002)
1.  **MPEA Database**: Attempt to resolve DOI `10.1038/s41597-020-00768-9` to a file. If successful, download and parse.
2.  **Materials Project**: Attempt to fetch BCC yield strength data from Materials Project (if a verified API endpoint or dataset is available; otherwise, log "Source Unavailable" and continue with MPEA only, but flag if MPEA N < 80).
3.  **Filtering**: Keep only `crystal_structure == "BCC"` and `yield_strength` is not null.
4.  **Normalization**: Atomic fractions normalized to sum to 1.0.
5.  **Validation**: Check N >= 80. If N < 80, **HALT** with "Data Scarcity Warning".
6.  **Column Verification**: Verify the presence of `crystal_structure` and `yield_strength` columns. If missing, **HALT** with "Data Source Unreachable".

### Phase 1: Feature Engineering (FR-003, FR-003.1)
1.  **Descriptor Calculation**: Compute `delta_radius`, `vec`, `mixing_entropy`, `mixing_enthalpy`, `electronegativity_diff`.
    *   *Note*: `mixing_enthalpy` uses binary interaction parameters from the MPEA paper supplementary data.
2.  **ILR Transformation**: Apply Isometric Log-Ratio transformation to the raw composition vector.
3.  **VIF Check**: Calculate Variance Inflation Factor (VIF) for scalar descriptors. Include scalar descriptors in the final feature set **ONLY IF** VIF < 5. This prevents redundancy between ILR coordinates and derived scalars.
4.  **Circular Check**: Verify that the target variable is experimentally measured and not derived from CALPHAD methods using the same interaction parameters. If not, flag "Circular Validation Risk".

### Phase 2: Modeling & Validation (FR-004, FR-005, FR-006)
1.  **Split**: Stratified 80/20 split based on **binned compositional ranges** (derived from ILR features) to prevent data leakage.
2.  **Cross-Validation**: **Repeated 5-Fold CV (10 repeats)** for all N >= 80. (Note: This deviates from the spec's "LOOCV for N < 100" text to ensure statistical robustness; see Research.md for rationale).
3.  **Models**: Train Random Forest, Gradient Boosting, Ridge Regression.
4.  **Metrics**: Report R², MAE, RMSE. Generate % CI for R² via bootstrap.
5.  **Importance**: Permutation importance for top-ranked features.

### Phase 3: Reporting & Versioning
1.  **Output**: Generate `metrics.json` and `feature_importance.json`.
2.  **Hashing**: Compute SHA256 for all output artifacts.
3.  **State Update**: Update `state/` file with new hashes and timestamp.