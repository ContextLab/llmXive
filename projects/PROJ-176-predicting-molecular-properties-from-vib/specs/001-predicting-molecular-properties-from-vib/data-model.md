# Data Model: Predicting Molecular Properties from Vibrational Spectra

## Overview

This document defines the data structures used throughout the pipeline, from raw ingestion to final evaluation. All data flows are immutable; raw data is preserved, and derived data is written to new files.

## Entity Definitions

### 1. Raw Molecule Record (QM9)
Source: `data/raw/qm9.parquet`
- **`InChIKey`**: String (Primary Key). Unique identifier for the molecule.
- **`mu`**: Float. Dipole moment (Debye).
- **`alpha`**: Float. Isotropic polarizability (Å³).
- **`homo`**: Float. HOMO energy (eV).
- **`lumo`**: Float. LUMO energy (eV).
- **`gap`**: Float. HOMO-LUMO gap (eV) (derived from `homo` and `lumo` if not present).
- **`dft_method`**: String. DFT functional/basis set (e.g., "B3LYP/6-31G*").

### 2. Raw Spectrum Record (IR-Spectra)
Source: `data/raw/ir_spectra.parquet`
- **`InChIKey`**: String (Primary Key).
- **`wavenumbers`**: Array of Floats. Wavenumber values (cm⁻¹).
- **`intensities`**: Array of Floats. Absorption intensities.
- **`dft_method`**: String. DFT functional/basis set used to generate spectra.

### 3. Preprocessed Tensor (Aligned)
Output: `data/processed/aligned_dataset.npz`
- **`spectra`**: Float32 Array `[N, 1, 3601]`. Normalized, smoothed, interpolated spectra.
- **`dipole`**: Float32 Array `[N]`. Target dipole moment.
- **`polarizability`**: Float32 Array `[N]`. Target polarizability.
- **`gap`**: Float32 Array `[N]`. Target HOMO-LUMO gap.
- **`InChIKeys`**: Array of Strings `[N]`. IDs for traceability.
- **`selection_bias_stats`**: Object. KS-test statistics comparing this subset to full QM9.

### 4. Model Checkpoint
Output: `models/checkpoint_best.pt`
- **`model_state_dict`**: Dict. Weights of the 1-D CNN.
- **`optimizer_state_dict`**: Dict. Optimizer state.
- **`epoch`**: Int. Training epoch number.
- **`val_loss`**: Float. Validation loss at this epoch.
- **`config`**: Dict. Hyperparameters (lr, batch_size, etc.).

### 5. Evaluation Results
Output: `results/evaluation_metrics.json`
- **`dipole`**: Object.
  - `mae`: Float.
  - `r2`: Float.
  - `tost_p_value`: Float. (p-value for equivalence test).
  - `ci_lower`: Float.
  - `ci_upper`: Float.
- **`polarizability`**: Object. (Same structure).
- **`gap`**: Object. (Same structure).
- **`multivariate`**: Object.
  - `hotelling_t2`: Float.
  - `p_value`: Float.
- **`metadata`**: Object.
  - `test_size`: Int.
  - `seed`: Int.
  - `dft_method_train`: String.
  - `dft_method_val`: String (or "simulated" if domain shift).
  - `selection_bias_detected`: Boolean.

## Data Flow Diagram

```mermaid
graph TD
    A[Raw QM9 Parquet] -->|Load & Filter| B(Alignment & Join)
    C[Raw IR-Spectra Parquet] -->|Load & Filter| B
    B -->|Check DFT Methods| D{Method Match?}
    D -->|No| E[Flag: Domain Shift Candidate]
    D -->|Yes| F[Flag: Direct Match]
    B -->|Inner Join on InChIKey| G{Match Found?}
    G -->|Yes| H[Preprocessing: Interpolate/Smooth/Normalize]
    G -->|No| I[Log & Discard]
    H --> J[Selection Bias Audit: KS-Test]
    J --> K[Aligned NPZ Tensor]
    K --> L[Train/Val/Test Split]
    L --> M[1-D CNN Training]
    M --> N[Model Checkpoint]
    N --> O[Evaluation on Test Set]
    O --> P[TOST & Hotelling's T2]
    P --> Q[Evaluation JSON]
    Q --> R[Independent Validation (if available)]
    R --> S[Validation JSON]
```

## Constraints & Invariants

- **Grid Invariant**: All spectra in `aligned_dataset.npz` MUST have exactly 3601 points.
- **Range Invariant**: Wavenumbers MUST be in [400, 4000] cm⁻¹.
- **Normalization Invariant**: Sum of intensities for each spectrum MUST be 1.0 (within floating point tolerance).
- **Type Invariant**: All target variables MUST be non-negative (or handled with appropriate sign logic if dipole is vector magnitude).
- **Traceability**: Every row in `aligned_dataset.npz` MUST have a corresponding `InChIKey` in the raw source files.
- **Bias Audit**: The `selection_bias_stats` object MUST be populated with KS-test results before training begins.