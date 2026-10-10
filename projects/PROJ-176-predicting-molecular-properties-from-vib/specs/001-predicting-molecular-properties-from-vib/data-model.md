# Data Model: Predicting Molecular Properties from Vibrational Spectra

## Overview
Defines immutable data artifacts from raw ingestion to final evaluation. Every transformation produces a new file; raw inputs remain unchanged. All schemas are enforced by `contracts/` YAML files.

## Entity Definitions

### 1. Raw Molecule Record (QM9)
- **Location**: `data/raw/qm9.parquet` (loaded via `qm9pack`).  
- **Fields**  
  - `InChIKey` (string, primary key)  
  - `Dipole_debye` (float) → target **dipole**  
  - `Polarizability_bohr3` (float) → target **polarizability** (converted to Å³)  
  - `HOMO_LUMO_gap_au` (float) → target **gap** (converted to eV)  
  - `dft_method` (string) – e.g., “B3LYP/6-31G*”  

### 2. Raw Spectrum Record (IR‑Spectra)
- **Location**: `data/raw/ir_spectra.parquet`.  
- **Fields**  
  - `InChIKey` (string, primary key)  
  - `wavenumbers` (array float, cm⁻¹)  
  - `intensities` (array float)  
  - `dft_method` (string)  

### 3. Preprocessed Tensor (Aligned)
- **Location**: `data/processed/aligned_dataset.npz`.  
- **Arrays**  
  - `spectra` – shape `[N, C, 3601]` where C denotes a singleton channel dimension, float32, unit‑area, Gaussian‑smoothed.  
  - `dipole` – shape `[N]`, float32 (Debye).  
  - `polarizability` – shape `[N]`, float32 (Å³).  
  - `gap` – shape `[N]`, float32 (eV).  
  - `InChIKeys` – shape `[N]`, string identifiers.  
  - `selection_bias_stats` – dict with KS‑test `statistic` and `p_value`.  

### 4. Model Checkpoint
- **Location**: `models/checkpoint_best.pt`.  
- **Contents** (see `contracts/model_output.schema.yaml`):  
  - `model_state_dict`, `optimizer_state_dict`, `epoch`, `val_loss`, `config`.  

### 5. Evaluation Results
- **Location**: `results/evaluation_metrics.json`.  
- **Structure** (see `contracts/evaluation_results.schema.yaml`):  
  - Per‑property blocks (`dipole`, `polarizability`, `gap`) each containing `mae`, `r2`, `tost_p_value`, `ci_lower`, `ci_upper`.  
  - `multivariate` block with `hotelling_t2` and `p_value`.  
  - `metadata` block with `test_size`, `seed`, timestamps, DFT methods, and `selection_bias_detected`.  

## Data Flow Diagram

```mermaid
graph TD
    A[Raw QM9 Parquet] -->|Load via qm9pack| B[Alignment & Join]
    C[Raw IR‑Spectra Parquet] -->|Load via datasets| B
    B -->|Inner join on InChIKey| D[Preprocess (interp, smooth, normalize)]
    D -->|KS‑test audit| E[aligned_dataset.npz]
    E -->|Train/Val/Test split| F[1‑D CNN Training]
    F -->|Best checkpoint| G[models/checkpoint_best.pt]
    G -->|Test‑set inference| H[results/evaluation_metrics.json]
    H -->|Optional external validation| I[results/validation_metrics.json]
```

## Constraints & Invariants

| Invariant | Description |
|-----------|-------------|
| **Grid Length** | All spectra have a uniform number of points covering the intended spectral range with a consistent, fine resolution. |
| **Range** | Wavenumbers are within the lower portion of the relevant spectral range, extending up to 4000 cm⁻¹. |
| **Normalization** | Sum of intensities per spectrum = 1.0 ± 1e‑6. |
| **Type** | Targets are non‑negative floats (dipole magnitude, polarizability, gap). |
| **Traceability** | Every row in `aligned_dataset.npz` has a corresponding `InChIKey` present in both raw sources. |
| **Bias Audit** | `selection_bias_stats` must be populated before training begins. |
| **Checksum** | Raw files’ SHA‑256 hashes stored in project state (`state/...yaml`). |

---
