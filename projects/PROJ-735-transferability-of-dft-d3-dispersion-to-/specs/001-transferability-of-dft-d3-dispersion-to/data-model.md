# Data Model: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Entity Definitions

### 1. IonPair
Represents a unique cation-anion combination in the benchmark set.
- **pair_id**: `str` (Unique identifier, e.g., "IL-001")
- **cation**: `str` (e.g., "EMIM")
- **anion**: `str` (e.g., "BF4")
- **xyz_file**: `str` (Path to the geometry file)
- **reference_energy**: `float` (kcal/mol, CCSD(T)/CBS value)
- **experimental_density**: `float` (g/cm³, optional)
- **experimental_viscosity**: `float` (cP, optional)
- **experimental_lattice_energy**: `float` (kcal/mol, optional)

### 2. CalculationResult
Stores the output of the DFT-D3 calculation for a single ion pair.
- **pair_id**: `str` (FK to IonPair)
- **dft_total_energy**: `float` (kcal/mol, raw DFT-D3 energy)
- **d3_dispersion_energy**: `float` (kcal/mol, the D3 correction term)
- **bsse_correction**: `float` (kcal/mol, Counterpoise correction)
- **corrected_energy**: `float` (kcal/mol, DFT + D3 + BSSE)
- **signed_error**: `float` (kcal/mol, `corrected_energy` - `reference_energy`)
- **status**: `str` ("success", "failed", "skipped")
- **failure_reason**: `str` (Optional, if status != "success")

### 3. BulkProperty
Experimental macroscopic properties for the IL.
- **pair_id**: `str` (FK to IonPair)
- **density**: `float` (g/cm³)
- **viscosity**: `float` (cP)
- **source**: `str` ("Static_CSV")

## Data Flow

1.  **Raw Input**: User-provided dataset (XYZ files + CSV with reference energies).
2.  **Processing**:
    - `run_psi4.py`: Reads XYZ, runs calculation, outputs `dft_total_energy`, `d3_dispersion_energy`.
    - `analyze_energies.py`: Computes `signed_error`, fits scaling factor `s` (80/20 split), computes bootstrap CI.
    - `analyze_bulk.py`: Joins with `BulkProperty`, computes correlations (pairs bootstrap).
    - `analyze_lattice.py`: Joins with `lattice_energy_benchmark.csv`, computes MAE/MSE.
3.  **Derived Outputs**:
    - `raw_energies.csv`: Aggregated results from `run_psi4.py`.
    - `scaling_factor.txt`: Single value `s` and CI.
    - `correlation_report.md`: Statistical summary.
    - `lattice_energy_report.md`: Lattice energy comparison.

## Constraints & Validation

- **Energy Units**: All energies must be in `kcal/mol`.
- **Missing Data**: If `reference_energy` is missing, the record is skipped. If `experimental_density` is missing, the record is excluded from the density correlation but included in the energy benchmark. If coordinates are missing, the entire pipeline aborts.
- **Scaling Factor**: Must be strictly positive (`s > 0`).
