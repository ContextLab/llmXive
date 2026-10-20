# Data Model: Predicting Molecular Properties from Vibrational Spectra  

## Overview  
Defines immutable data artifacts from raw ingestion to final evaluation. Every transformation creates a new file; raw inputs remain unchanged. Schemas are enforced by contracts in `contracts/`.

## Entity Definitions  

### 1. Raw QM9 Property Record  
- **Location**: `data/raw/qm9.parquet` (downloaded via `datasets.load_dataset`).  
- **Fields**  
  - `InChIKey` (string, primary key)  
  - `dipole_debye` (float) – target dipole moment (Debye)  
  - `polarizability_angstrom3` (float) – isotropic polarizability (Å³)  
  - `gap_ev` (float) – HOMO‑LUMO gap (eV)  
  - `dft_method` (string) – e.g., “B3LYP/6‑31G*”  

### 2. Raw IR‑spectra Record  
- **Location**: `data/raw/ir_spectra.parquet` (Lamblador/IRSpectra).  
- **Fields**  
  - `InChIKey` (string, primary key)  
  - `wavenumbers` (array float, cm⁻¹)  
  - `intensities` (array float)  
  - `dft_method` (string) – DFT method used to generate the spectrum (may be *unspecified*).  

### 3. Generated IR‑spectra Record *(optional)*  
- **Location**: `data/generated/generated_spectra.npz`.  
- **Arrays**  
  - `spectra` – shape `[N, 1, 3601]`, `float32`, unit‑area, Gaussian‑smoothed, generated from QM9 geometries using the **same B3LYP functional** via PySCF (Phase 0.5).  
  - `InChIKeys` – shape `[N]`, string identifiers matching the QM9 records.  
  - `generation_metadata` – dict with keys `method` (e.g., “B3LYP‑PySCF”), `timestamp`, and `software_version`.  

### 4. Preprocessed Aligned Dataset  
- **Location**: `data/processed/aligned_dataset.npz`.  
- **Arrays**  
  - `spectra` – shape `[N, 1, 3601]`, `float32`, unit‑area, Gaussian‑smoothed.  
  - `dipole` – shape `[N]`, `float32` (Debye).  
  - `polarizability` – shape `[N]`, `float32` (Å³).  
  - `gap` – shape `[N]`, `float32` (eV).  
  - `InChIKeys` – shape `[N]`, string identifiers.  
  - `selection_bias_stats` – dict with KS‑test `statistic` and `p_value`.  

### 5. Model Checkpoint  
- **Location**: `models/checkpoint_best.pt`.  
- **Contents** (see `contracts/model_output.schema.yaml`):  
  - `model_state_dict`  
  - `optimizer_state_dict`  
  - `epoch` (int)  
  - `val_loss` (float)  
  - `config` (hyperparameters)  

### 6. Evaluation Results  
- **Location**: `results/evaluation_metrics.json`.  
- **Structure** (see `contracts/evaluation_results.schema.yaml`):  
  - Per‑property blocks (`dipole`, `polarizability`, `gap`) each with `mae`, `r2`, `tost_p_value`, `ci_lower`, `ci_upper`.  
  - `multivariate` block with `hotelling_t2` and `p_value`.  
  - `metadata` block with `test_size`, `seed`, timestamps, DFT method identifiers, and `selection_bias_detected`.  

### 7. Independent Validation Results  
- **Location**: `results/validation_metrics.json`.  
- **Structure**: Same as `results/evaluation_metrics.json` (property‑wise MAE and R²).  

### 8. Control Experiment Results  
- **Location**: `results/control_metrics.json`.  
- **Structure**: Same as `results/evaluation_metrics.json` (MAE & R² for scrambled spectra).  
- **Location**: `results/control_random_metrics.json`.  
- **Structure**: Same as `results/evaluation_metrics.json` (MAE & R² for random‑noise spectra).  

### 9. Runtime & Profile Artifacts  
- `results/pipeline_runtime.json` – total elapsed seconds, status.  
- `results/profile_report.txt` – peak memory/CPU usage.  
- `results/structure_report.txt` – SHA‑256 hashes of all major artifacts (required for T001).

## Data Flow Diagram  

```mermaid
graph TD
    A[Raw QM9 Properties] --> B[Align on InChIKey]
    C[Raw IR Spectra] --> B
    D[Generated IR Spectra] --> B
    B --> E[Preprocess (interp, smooth, normalize)]
    E --> F[aligned_dataset.npz]
    F --> G[Train 1‑D CNN]
    G --> H[Best checkpoint.pt]
    H --> I[Evaluation on test set]
    I --> J[evaluation_metrics.json]
    G --> K[Independent validation (B3LYP)]
    K --> L[validation_metrics.json]
    G --> M[Scrambled‑order control]
    M --> N[control_metrics.json]
    G --> O[Random‑noise control]
    O --> P[control_random_metrics.json]
    H --> Q[Structure report & runtime logs]
```

## Constraints & Invariants  

| Invariant | Description |
|-----------|-------------|
| **Grid Length** | All spectra have a uniform number of points covering the full spectral range of interest with a consistent fine spectral step. |
| **Normalization** | Sum of intensities per spectrum = 1.0 ± 1e‑6. |
| **Type Consistency** | Targets are non‑negative `float32`. |
| **Traceability** | Every row in `aligned_dataset.npz` has a matching `InChIKey` present in both raw sources **or** in the generated spectra. |
| **Bias Audit** | `selection_bias_stats` must be present before training. |
| **Checksum** | SHA‑256 of each raw parquet file recorded in `state/projects/...yaml`. |
| **No In‑Place Mutation** | All processing writes new files; raw parquet files remain untouched. |
| **Schema Validation** | All JSON/NPZ artifacts must pass their respective contract schemas. |