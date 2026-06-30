# Data Model: Defect Chemistry and Ionic Conductivity Analysis

## 1. Overview
This document defines the data structures used to store raw inputs, computed defect properties, and statistical analysis results. All data is stored in CSV/JSON formats with checksums for reproducibility. The `analysis_results.json` file contains all data required to regenerate correlation plots, ensuring the Single Source of Truth (SSoT) principle.

## 2. Entity Definitions

### 2.1 ElectrolyteComposition
Represents a solid electrolyte material.
- `composition_id`: Unique identifier (string).
- `formula`: Chemical formula (string, e.g., "Li7La3Zr2O12").
- `structure_file`: Path to the CIF file (string).
- `conductivity_exp`: Experimental ionic conductivity (float, S·cm⁻¹·K).
- `source`: Data source (string, e.g., "OBELiX").

### 2.2 DefectConfiguration
Represents a specific defect type and its computed energy.
- `config_id`: Unique identifier (string).
- `electrolyte_id`: Foreign key to `ElectrolyteComposition`.
- `defect_type`: Enum {"vacancy", "interstitial", "antisite"}.
- `formation_energy_eV`: Computed formation energy (float).
- `supercell_atoms`: Number of atoms in supercell (int).
- `calculation_status`: Enum {"success", "failed", "pending"}.
- `dft_params`: JSON string containing pseudopotential, cutoff, k-points.
- `method`: Enum {"DFT", "semi_empirical"}.

### 2.3 MigrationBarrier
Represents NEB-computed activation energy.
- `barrier_id`: Unique identifier (string).
- `electrolyte_id`: Foreign key to `ElectrolyteComposition`.
- `defect_type`: Enum {"vacancy", "interstitial", "antisite"}.
- `activation_energy_eV`: Computed barrier (float).
- `convergence_status`: Enum {"converged", "diverged"}.
- `force_tolerance`: Final force tolerance (float, eV/Å).
- `method`: Enum {"DFT", "semi_empirical"}.

### 2.4 AnalysisResult
Stores statistical outputs and raw data for plot generation.
- `result_id`: Unique identifier (string).
- `defect_type`: Enum {"vacancy", "interstitial", "antisite"}.
- `R_squared`: Coefficient of determination (float).
- `p_value`: Raw p-value (float).
- `adjusted_p_value`: Corrected p-value (float).
- `significance_flag`: Boolean (True if p < 0.05).
- `vif_score`: Variance Inflation Factor (float, diagnostic only).
- `x_values`: Array of numbers (Total Activation Energy values for the regression).
- `y_values`: Array of numbers (Experimental log(σ) values for the regression).
- `pca_components`: Array of numbers (Principal components used for regression if applicable).

## 3. File Layout

```text
data/
├── raw/
│   ├── structures/           # CIF files
│   ├── obelix_conductivity.csv # Raw download from OBELiX
│   └── mp_ids.txt            # Static list of Materials Project IDs
├── processed/
│   ├── compositions.csv      # Mapped ElectrolyteComposition
│   ├── defect_energies.csv   # Merged DefectConfiguration
│   ├── migration_barriers.csv# Merged MigrationBarrier
│   └── analysis_results.json # Merged AnalysisResult (includes plot data)
└── checksums.txt             # SHA-256 hashes
```

## 4. Data Flow
1.  **Download**: `raw/structures` and `raw/obelix_conductivity.csv` fetched.
2.  **Validate**: `validate.py` checks completeness; logs missing variables.
3.  **Compute**: `dft_runner.py` and `semi_empirical.py` generate `defect_energies.csv` and `migration_barriers.csv`.
4.  **Analyze**: `analysis.py` reads processed CSVs, performs regression (with PCA if needed), and writes `analysis_results.json` (including `x_values`, `y_values`, and `pca_components` for plots).