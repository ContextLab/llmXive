# Data Model: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

## 1. Overview

This document defines the data structures used throughout the pipeline. All data is stored in CSV or Parquet format for portability and version control. Intermediate files are derived from raw simulation data and include provenance metadata.

## 2. Entity Definitions

### 2.1 Halo (Raw & Processed)
Represents a dark matter structure identified in the simulation.
*   **Source**: TNG-100 / Millennium-II FoF Catalog.
*   **Key Fields**:
    *   `halo_id`: Unique integer identifier within the snapshot.
    *   `snapshot_id`: Integer identifier for the simulation snapshot (e.g., 0, 1, 25).
    *   `mass_total`: Total mass of the halo (Msun/h).
    *   `virial_radius`: Radius in kpc/h.
    *   `n_dm_particles`: Count of dark matter particles within virial radius.
    *   `axial_ratio_ba`: $b/a$ (float, 0 < x <= 1).
    *   `axial_ratio_ca`: $c/a$ (float, 0 < x <= 1).
    *   `triaxiality`: $T$ (float, 0 <= T <= 1).
    *   `shape_bin`: Categorical (Prolate, Triaxial, Spherical).
    *   `spin_vector`: 3-element float array (normalized).

### 2.2 Central Galaxy
Represents the most massive subhalo within a halo.
*   **Source**: Subhalo Catalog.
*   **Key Fields**:
    *   `subhalo_id`: Unique integer identifier.
    *   `halo_id`: Foreign key to Halo.
    *   `stellar_mass`: Total stellar mass (Msun/h).
    *   `sfr`: Star Formation Rate (Msun/yr).
    *   `effective_radius`: Half-light radius (kpc).
    *   `galaxy_spin_vector`: 3-element float array (normalized).
    *   `major_axis_vector`: 3-element float array (normalized).

### 2.3 Analysis Result
Aggregated statistical outputs.
*   **Key Fields**:
    *   `test_type`: (Kruskal-Wallis, Mann-Whitney, KS, Regression).
    *   `property`: (SFR, Effective Radius).
    *   `comparison`: (Prolate vs Triaxial, etc.).
    *   `statistic`: Float value of the test statistic.
    *   `p_value_raw`: Raw p-value.
    *   `p_value_adj`: Bonferroni-corrected p-value.
    *   `significant`: Boolean (True if $p_{adj} < 0.01$).
    *   `threshold_set`: The binning thresholds used (e.g., "0.5,0.8").
    *   `effect_size`: Regression coefficient value.
    *   `ci_lower`: Lower bound of 95% CI.
    *   `ci_upper`: Upper bound of 95% CI.

### 2.4 Misalignment Record
Orientation analysis results.
*   **Key Fields**:
    *   `halo_id`: Foreign key.
    *   `angle_spin_spin`: Angle in degrees (0-180).
    *   `angle_major_major`: Angle in degrees (0-180).
    *   `correlation_coeff`: Spearman rho with SFR/Radius.
    *   `p_value`: Significance of correlation.

### 2.5 Null Control Record
Results from the shuffled null simulation.
*   **Key Fields**:
    *   `iteration`: Integer ID of the shuffle.
    *   `statistic`: Test statistic from shuffled data.
    *   `effect_size`: Regression coefficient from shuffled data.

## 3. Data Flow

1.  **Raw Data**: `data/raw/tng100/snapshot_*.hdf5` (Read-only, checksummed).
2.  **Derived Halo Data**: `data/processed/halo_shapes.csv` (Contains computed inertia tensor metrics).
3.  **Derived Galaxy Data**: `data/processed/galaxy_properties.csv` (Joined with halo data).
4.  **Alignment Data**: `data/processed/alignment_angles.csv`.
5.  **Null Control Data**: `data/processed/null_control_results.csv`.
6.  **Final Analysis**: `data/processed/analysis_results.csv`.

## 4. Constraints & Validation

*   **Axial Ratios**: Must be $0 < b/a \le 1$ and $0 < c/a \le 1$.
*   **Triaxiality**: Must be $0 \le T \le 1$.
*   **Angles**: Must be $0 \le \theta \le 180$.
*   **Missing Data**: Haloes with missing spin vectors or insufficient particles are excluded and logged.
*   **Associational Flag**: All output datasets MUST include `associational_only=true` (FR-008).