# Implementation Plan: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Branch**: `PROJ-511-predicting-molecular-packing-efficiency` | **Date**: 2026-06-29 | **Spec**: `specs/001-predicting-molecular-packing-efficiency/spec.md`
**Input**: Feature specification from `specs/001-predicting-molecular-packing-efficiency/spec.md`

## Summary

This project implements a CPU-only pipeline to predict the Composition-Adjusted Packing Efficiency (CAPE) of organic crystals from their SMILES representations. The pipeline downloads CIF files from the Crystallography Open Database (COD), filters for organic molecules (≤50 non-hydrogen atoms), generates canonical SMILES via RDKit where missing, and computes 3D geometry descriptors from *gas-phase minimized conformations* to avoid data leakage. A frozen pre-trained SMILES Transformer provides topology features, which are combined with 3D descriptors and environmental covariates (lattice system, temperature, solvent) to train a -layer MLP (≤100k parameters). The model is evaluated using Pearson/Spearman correlation, MAE, and a fixed permutation test with a sufficient number of shuffles to ensure statistical significance while respecting the available GitHub Actions runtime limit.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `torch` (CPU), `scikit-learn`, `pandas`, `datasets`, `pyyaml`, `jinja2` (for HTML report), `transformers` (for SMILES embedding)  
**Storage**: Local filesystem (`data/`, `models/`, `results/`)  
**Testing**: `pytest` (unit tests for parsing and feature extraction), integration tests for pipeline end-to-end  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, ample RAM for standard workloads.)  
**Project Type**: Data Science Pipeline / CLI  
**Performance Goals**: End-to-end pipeline ≤ 6 hours.  
**Constraints**: No GPU usage in default path; All data must be streamed or sampled to fit available RAM.; strict adherence to FR-005 (A multi-layer perceptron (MLP) with a hidden layer.) and FR-016 (k shuffles).  
**Scale/Scope**: Dataset target ≥ 500 records; Model parameters ≤ 100k.

> **Note on Dataset Strategy**: The project relies on the **Crystallography Open Database (COD)** as the primary source, accessed via its public FTP bulk download mechanism (e.g., `ftp://ftp.crystallography.net/pub/cod/`) to ensure programmatic retrieval of ≥500 records. The "Verified datasets" block in the input message does not contain COD data; this plan implements the direct download from the official COD source.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan mandates fixed random seeds, pinned `requirements.txt`, and deterministic data streaming logic.
- **Principle II (Verified Accuracy)**: Plan cites Bondi for van der Waals radii (FR-018) and the COD official source for data (FR-017). No fabricated URLs are used; the COD source is verified as the canonical repository.
- **Principle III (Data Hygiene)**: Plan includes checksumming of raw downloads and immutable derivation steps (raw CIF → processed CSV).
- **Principle IV (Single Source of Truth)**: All metrics in the final report are generated directly from `data/dataset.csv` and model outputs, with no manual entry.
- **Principle V (Versioning)**: Plan requires recording the code hash and data checksums in the final report.
- **Principle VI (Open Crystallographic Data Integrity)**: The pipeline explicitly downloads from COD, retains COD IDs, and flags SMILES generation provenance.
- **Principle VII (Model Transparency)**: The 2-layer MLP architecture and frozen transformer weights are documented; the permutation test logic is explicit ([deferred] shuffles).

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-511-predicting-molecular-packing-efficiency/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── config.py            # Paths, constants, random seeds
├── data/
│   ├── __init__.py
│   ├── download_cif.py  # FR-001: COD download logic
│   ├── parse_cif.py     # FR-002: RDKit SMILES generation, FR-003: PC calculation
│   └── features.py      # FR-004, FR-011, FR-012: Feature engineering
├── models/
│   ├── __init__.py
│   ├── transformer.py   # Frozen SMILES transformer loader
│   └── mlp.py           # FR-005: 2-layer MLP definition
├── training/
│   ├── train.py         # FR-005: Training loop
│   ├── evaluate.py      # FR-006, FR-015: Metrics, Shapiro-Wilk, Permutation test
│   └── sensitivity.py   # FR-007, FR-008: Threshold sweep
├── utils/
│   ├── vif.py           # FR-009: VIF diagnostics
│   └── report.py        # FR-010: HTML report generation
└── main.py              # Orchestration script

tests/
├── test_download.py
├── test_features.py
└── test_pipeline.py

data/
├── raw_cif/             # Downloaded CIF files (excluded from git)
├── dataset.csv          # Processed dataset
└── checksums.txt        # Data hygiene

models/
├── mlp.pt               # Trained weights
└── transformer_cache/   # Frozen weights

results/
├── validation_report.json
├── sensitivity_report.csv
└── report.html
```

**Structure Decision**: The single `src/` directory structure is chosen for simplicity and to match the CLI nature of the project. It separates data ingestion, feature engineering, modeling, and reporting into distinct modules, facilitating unit testing and adherence to the "Single Source of Truth" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Fixed Permutation Test

The research question concerns the statistical significance of the observed effect under the null hypothesis. The method employs a permutation test to generate a null distribution for significance assessment. References: [Insert Citation Here] | Required by FR-016 and SC-002 for statistical validity. | Conditional testing introduces selection bias and violates the spec. |
| 2-Layer MLP (FR-005) | Required by spec for model transparency and parameter count constraints. | A 1-layer model would violate FR-005 and potentially underfit. |
| 3D Geometry Descriptors (Gas-Phase) | Required to supplement SMILES with conformational data without leakage. | Using crystal coordinates would trivially encode the target. |
| Environmental Covariates (FR-013) | Required by spec to control for crystal environment effects. | Excluding them would violate FR-013. |

## Phases & Steps

### Phase 0: Data Acquisition & Validation (Addresses FR-001, FR-002, FR-017)
1.  **Download COD Data**: Implement `download_cif.py` to fetch CIF files from the COD public FTP mirror (`ftp://ftp.crystallography.net/pub/cod/`). Filter for organic molecules with ≤50 non-hydrogen atoms. Log statistics.
    *   **Error Handling**: Log and skip corrupt CIFs. If <500 valid records are obtained, abort with a warning (Assumption check).
2.  **Parse & Generate SMILES**: Implement `parse_cif.py`. Use RDKit to:
    *   Extract `_chemical_structure_SMILES` if present.
    *   Generate canonical SMILES from 3D coordinates if missing (FR-002).
    *   Calculate Unit Cell Volume and sum of Bondi VdW volumes to derive `PC_raw` (FR-003).
    *   Calculate CAPE (FR-011).
    *   **Environment Config**: Ensure RDKit and PyTorch are installed in a virtualenv with pinned versions.
3.  **Dataset Construction**: Aggregate results into `data/dataset.csv`. Ensure ≥500 valid rows (SC-001).
    *   **Power Analysis**: For N=500, alpha=0.05, and target r=0.4, statistical power >99%. N=500 is sufficient.
    *   **Traceability**: This step produces the 'Processed Dataset' entity defined in `data-model.md`.

### Phase 1: Feature Engineering & Model Training (Addresses FR-004, FR-005, FR-009, FR-012, FR-013, FR-014)
1.  **Feature Extraction**:
    *   Load frozen SMILES Transformer (CPU). Encode SMILES to fixed-length vectors.
    *   Compute 3D descriptors (Radius of Gyration, Asphericity, Principal Moments) from *gas-phase minimized conformations* generated by RDKit, NOT from CIF coordinates, to prevent data leakage.
    *   **Flattening**: Expand `principal_moments` into three separate columns (`principal_moment_1`, `principal_moment_2`, `principal_moment_3`).
    *   Extract confounders: Lattice system, temperature, solvent presence (FR-013).
    *   Combine features into a matrix.
2.  **Collinearity Check**: Compute VIF for all features. Flag VIF > 5 (FR-009).
3.  **Model Training**:
    *   Split data into a standard majority training set and a held-out validation set. with fixed seed.
    *   Train a -layer MLP (Input -> Hidden() -> Hidden -> Output) with ≤100k parameters (FR-005).
    *   Save model weights (`models/mlp.pt`).

### Phase 2: Evaluation & Statistical Validation (Addresses FR-006, FR-015, FR-016, SC-002, SC-003)
1.  **Primary Metrics**: Calculate MAE, Pearson r, Spearman ρ on validation set.
2.  **Residual Analysis**: Perform Shapiro-Wilk test on residuals (FR-015).
3.  **Permutation Test**:
    *   Run a fixed large-scale permutation test with a sufficient number of shuffles to ensure robust estimation of the p-value. (FR-016) to calculate the two-sided p-value.
    *   This is a single, non-conditional test to ensure statistical validity and compliance with FR-016.
4.  **Partial Correlation**: Compute correlation between predicted and observed CAPE controlling for atom-type composition (FR-014).

### Phase 3: Sensitivity Analysis (Addresses FR-007, FR-008, SC-004)
1.  **Threshold Sweep**: Evaluate performance at high-packing thresholds {, , a moderate value}.
2.  **Bonferroni Correction**: Apply correction to the three p-values (FR-008).
3.  **Robustness Check**: Verify r variation ≤ ±0.05 (SC-004).

### Phase 4: Reporting (Addresses FR-010, FR-019)
1.  **Generate Report**: Create `results/report.html` including:
    *   Dataset provenance (COD ID, version).
    *   Model architecture and hyperparameters.
    *   All metrics (MAE, r, ρ, p-values, VIF flags, partial_corr).
    *   Sensitivity analysis table.
    *   Source code version hash.
2.  **Schema Validation**: Ensure `results/validation_report.json` matches `contracts/validation_report.schema.yaml`.
