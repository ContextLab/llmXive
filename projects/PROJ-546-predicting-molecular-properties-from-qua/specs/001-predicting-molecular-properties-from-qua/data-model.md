# Data Model: Predicting Molecular Properties from Quantum Chemical Calculations

## Overview

This document defines the data structures, schemas, and transformations for the project. It ensures that all data artifacts are consistent, checksummed, and traceable.

## Input Data

### Source: Zenodo Experimental Barrier Dataset

*   **File**: `data/raw/barrier_dataset.csv`
*   **Format**: CSV
*   **Columns**:
    *   `molecule_id` (string): Unique identifier for the molecule.
    *   `smiles` (string): Canonical SMILES representation.
    *   `experimental_barrier` (float): Experimental barrier height in kcal/mol (or eV, as per Zenodo).
*   **Verification**:
    *   Checksum: SHA-256 of the raw file.
    *   Source: Zenodo (verified URL fetched from `idea.md`).

## Intermediate Data

### Optimized Geometries

*   **Directory**: `data/optimized_geometries/`
*   **Files**: `molecule_id.xyz`
*   **Format**: XYZ (Cartesian coordinates).
*   **Content**: Optimized geometry from DFTB+.
*   **Schema**:
    *   Line 1: Number of atoms.
    *   Line 2: Comment (e.g., "Optimized by DFTB+").
    *   Lines 3+: `Element X Y Z`.

### Confound Data (FR-008)

*   **File**: `data/confounds.csv`
*   **Format**: CSV
*   **Columns**:
    *   `molecule_id` (string)
    *   `mw` (float): Molecular Weight.
    *   `atom_count` (int): Total number of atoms.
    *   `functional_groups` (string): Comma-separated list of identified functional groups.
*   **Derivation**: Calculated from `data/raw/barrier_dataset.csv` using RDKit.

### Semi-Empirical Descriptors

*   **File**: `data/descriptors_semi.csv`
*   **Format**: CSV
*   **Columns**:
    *   `molecule_id` (string)
    *   `HOMO_energy` (float, eV)
    *   `LUMO_energy` (float, eV)
    *   `mayer_bond_order` (float, dimensionless)
    *   `status` (string): "success", "failed_after_retry"
*   **Derivation**: Computed from `data/optimized_geometries/` using DFTB+.

### DFT Descriptors (Subset)

*   **File**: `data/descriptors_dft.csv`
*   **Format**: CSV
*   **Columns**: Same as `descriptors_semi.csv`, plus `method`.
*   **Derivation**: Computed from `data/optimized_geometries/` using Psi4 for the 50-sample subset.
*   **Population Logic**: The `method` field is populated by the subset selection logic in `code/train_models.py`, which selects 50 samples and assigns `method="Psi4"`.

## Output Data

### Evaluation Report

*   **File**: `reports/evaluation.json`
*   **Format**: JSON
*   **Content**:
    *   `mae_semi`: Mean Absolute Error of Semi-Empirical RF (out-of-fold).
    *   `mae_dft`: Mean Absolute Error of DFT RF (out-of-fold).
    *   `t_test`:
        *   `statistic`: float
        *   `p_value`: float
        *   `null_hypothesis`: "No difference in error distribution between Semi-Empirical RF and DFT RF models"
        *   `significance_level`: 0.05
        *   `models_compared`: ["Semi-Empirical RF", "DFT RF"]
    *   `confound_analysis`:
        *   `partial_corr_mw`: float
        *   `r2_delta`: float
    *   `models_compared`: list of strings.

### Sensitivity Report

*   **File**: `reports/sensitivity.csv`
*   **Format**: CSV
*   **Columns**:
    *   `cutoff`: float (0.01, 0.05, 0.1)
    *   `noise_sigma`: float (0.01, 0.05)
    *   `top_3_descriptors`: string (comma-separated list)
    *   `rank_correlation`: float (Spearman's rho)
    *   `stable`: boolean (True if rho >= 0.9)

## Logs

### Convergence Failures

*   **File**: `logs/convergence_failures.log`
*   **Format**: CSV (or JSONL)
*   **Columns**: `molecule_id`, `timestamp`, `error_code`, `error_message`, `status` ("failed_after_retry").

### OOM Failures

*   **File**: `logs/oom_failures.log`
*   **Format**: CSV
*   **Columns**: `molecule_id`, `timestamp`, `error_message`.

### Structural Failures

*   **File**: `logs/structural_failures.log`
*   **Format**: CSV
*   **Columns**: `molecule_id`, `timestamp`, `error_message`, `status` ("failed_after_retry").

## Data Flow Traceability

1.  **Fetch**: `fetch_data.py` downloads Zenodo CSV -> `data/raw/`.
2.  **Confound**: `confound_analysis.py` reads `data/raw/` -> calculates MW, atom count, functional groups -> `data/confounds.csv`.
3.  **Optimize**: `geometry_opt.py` reads `data/raw/` -> runs DFTB+ -> writes `data/optimized_geometries/` and logs failures.
4.  **Descriptor (Semi)**: `descriptor_calc.py` reads `data/optimized_geometries/` -> runs DFTB+ -> writes `data/descriptors_semi.csv`.
5.  **Subset**: `train_models.py` selects 50 samples from `data/descriptors_semi.csv` -> assigns `method="Psi4"` -> triggers `descriptor_calc.py` for DFT -> writes `data/descriptors_dft.csv`.
6.  **Train**: `train_models.py` performs 5-fold CV on the 50-sample subset -> generates out-of-fold predictions -> trains models -> writes `reports/evaluation.json` (including t-test metadata and confound analysis).
7.  **Sensitivity**: `sensitivity.py` reads RF models -> runs sweep -> computes rank correlation -> enforces >= 0.9 threshold -> writes `reports/sensitivity.csv`.
