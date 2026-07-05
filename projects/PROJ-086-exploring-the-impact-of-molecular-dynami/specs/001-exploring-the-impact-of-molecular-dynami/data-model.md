# Data Model: Exploring the Impact of Molecular Dynamics Simulation Parameters on Predicted Protein-Ligand Binding Affinity

## 1. Overview

This document defines the data structures for the MD simulation pipeline. Data flows from raw PDB files and experimental values, through simulation trajectories, to calculated energies and statistical summaries.

## 2. Entity Definitions

### 2.1 SimulationRun
Represents a single execution of an MD simulation.
- **ID**: `run_{complex_id}_{ff}_{duration}_{temp}`
- **Attributes**:
  - `complex_id`: PDB ID (e.g., "1J22")
  - `force_field`: Enum {ff14SB, CHARMM36m}
  - `duration_ns`: Float {0.5, 1.0, 1.5}
  - `temperature_k`: Float {300.0}
  - `status`: Enum {pending, running, completed, failed}
  - `start_time`: ISO8601
  - `end_time`: ISO8601
  - `wall_clock_minutes`: Float

### 2.2 TrajectoryData
Output file from `SimulationRun`.
- **ID**: `traj_{run_id}`
- **Attributes**:
  - `run_id`: FK to `SimulationRun`
  - `file_path`: Relative path to `.nc` or `.xtc` file
  - `file_size_mb`: Float
  - `frame_count`: Int
  - `checksum`: SHA256

### 2.3 AffinityEstimate
Calculated binding free energy for a run.
- **ID**: `energy_{run_id}`
- **Attributes**:
  - `run_id`: FK to `SimulationRun`
  - `method`: Enum {MM-PBSA, MM-GBSA}
  - `delta_g_kcal_mol`: Float
  - `std_error`: Float
  - `num_snapshots`: Int
  - `status`: Enum {success, failed, non_physical}
  - `absolute_error`: Float (calculated as |delta_g - exp_value|)

### 2.4 ExperimentalValue
Ground truth from PDBbind.
- **ID**: `exp_{complex_id}`
- **Attributes**:
  - `complex_id`: PDB ID
  - `value_kcal_mol`: Float
  - `source`: String (e.g., "PDBbind v2020")
  - `original_type`: Enum {Kd, Ki, IC50}

### 2.5 AnalysisResult
Aggregated statistical output from LMM.
- **ID**: `analysis_{timestamp}`
- **Attributes**:
  - `model_type`: String ("LinearMixedEffects")
  - `fixed_effects`: JSON (coefficients, SE, CI for Force_Field, Duration)
  - `random_effects`: JSON (Variance of Complex intercept)
  - `residual_variance`: Float
  - `rmse_summary`: Float (Post-hoc RMSE calculated from model residuals)
  - `mae_baseline`: Float (MAE of the baseline configuration)
  - `cv_total`: Float (Coefficient of Variation)

## 3. File Layout

```text
data/
├── raw/
│   ├── pdbbind_exp.csv           # Experimental values (from PDBbind)
│   └── structures/               # Downloaded PDB files
│       └── {complex_id}.pdb
├── processed/
│   ├── trajectories/
│   │   └── {complex_id}_{ff}_{dur}.nc
│   └── energies/
│       └── energies.csv          # Aggregated Delta G and AE values
└── results/
    ├── lmm_results.json
    └── variance_plot.png
```

## 4. Data Flow

1. **Ingestion**: `load_data.py` fetches PDBbind data and filters for a targeted number of complexes.
2. **Simulation**: `run.py` iterates over `SimulationRun` configurations, generating `.nc` files.
3. **Post-Processing**: `mm_pbsa.py` reads `.nc` files, calculates `delta_g`, computes `absolute_error`, and writes `energies.csv`.
4. **Analysis**: `stats.py` reads `energies.csv` and `pdbbind_exp.csv`, fits the LMM (`AE ~ ForceField + Duration + (1|Complex)`), and writes `lmm_results.json`.

## 5. Constraints & Validations

- **Memory**: Trajectory files must be truncated to ≤ 500 frames to fit in 7GB RAM.
- **Time**: Each `SimulationRun` must complete within 5 minutes.
- **Integrity**: All output files must have SHA256 checksums recorded in `state/`.
- **Error Handling**: If MM-PBSA fails, the row is marked `failed` and excluded from LMM, but logged.