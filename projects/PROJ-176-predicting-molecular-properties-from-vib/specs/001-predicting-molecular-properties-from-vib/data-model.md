# Data Model: Predicting Molecular Properties from Vibrational Spectra

## Overview
Defines immutable data artifacts from raw ingestion to final evaluation. Every transformation produces a new file; raw inputs remain unchanged. All schemas are enforced by contracts in `contracts/`.

## Entity Definitions

### 1. Raw QM9 Record
- **Location**: `data/raw/qm9.parquet` (loaded via `datasets.load_dataset`).  
- **Fields**  
  - `InChIKey` (string, primary key)  
  - `Dipole_debye` (float) → target **dipole**  
  - `Polarizability_bohr3` (float) → target **polarizability** (converted to Å³)  
  - `HOMO_LUMO_gap_au` (float) → target **gap** (converted to eV)  
  - `dft_method` (string) – e.g., “B3LYP/6‑31G*”.

### 2. Raw IR‑Spectra Record
- **Location**: `data/raw/ir_spectra.parquet`.  
- **Fields**  
  - `InChIKey` (string, primary key)  
  - `wavenumbers` (array float, cm⁻¹)  
  - `intensities` (array float)  
  - `dft_method` (string).

### 3. Preprocessed Aligned Dataset
- **Location**: `data/processed/aligned_dataset.npz`.  
- **Arrays**  
  - `spectra` – shape `[N, 1, 3601]`, float32, unit‑area, Gaussian‑smoothed.  
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

### 6. Independent Validation Results
- **Location**: `results/validation_metrics.json`.  
- **Structure**: Same as `evaluation_metrics.json` (property‑wise MAE & R²).

### 7. Control Experiment Results
- **Location**: `results/control_metrics.json`.  
- **Structure**: Same as `evaluation_metrics.json` (MAE & R² for scrambled spectra).

## Data Flow Diagram

```mermaid
graph TD
    A[Raw QM9 Parquet] -->|load via datasets| B[Alignment on InChIKey]
    C[Raw IR‑Spectra Parquet] -->|load via datasets| B
    B -->|preprocess (interp, smooth, normalize)| D[aligned_dataset.npz]
    D -->|train/val/test split| E[1‑D CNN Training]
    E -->|best checkpoint| F[models/checkpoint_best.pt]
    F -->|test‑set inference| G[results/evaluation_metrics.json]
    G -->|control experiment| H[results/control_metrics.json]
    F -->|external validation| I[results/validation_metrics.json]
```

## Constraints & Invariants

| Invariant | Description |
|-----------|-------------|
| **Grid Length** | All spectra have a uniform number of points covering 400–4000 cm⁻¹. |
| **Normalization** | Sum of intensities per spectrum = 1.0 ± 1e‑6. |
| **Type** | Targets are non‑negative floats (dipole, polarizability, gap). |
| **Traceability** | Every row in `aligned_dataset.npz` has a matching `InChIKey` present in both raw sources. |
| **Bias Audit** | `selection_bias_stats` must be populated before training begins. |
| **Checksum** | SHA‑256 hashes of raw files stored in project state (`state/...yaml`). |
| **No In‑Place Mutation** | All processing writes new files; original raw parquet files remain untouched. |

---
