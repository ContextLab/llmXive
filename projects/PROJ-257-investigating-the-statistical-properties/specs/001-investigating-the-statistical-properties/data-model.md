# Data Model: Statistical Properties of Simulated Black Hole Mergers

## Overview

This document defines the data schemas and transformations for the analysis pipeline. All data is stored in CSV or JSON formats for simplicity and compatibility with the CPU-tractable environment.

## Entities

### 1. GWTC_Catalog (Observational)

Represents the processed observational gravitational-wave transient catalog.

**Source**: GWTC-1 / GWTC-2 Posterior Samples (Zenodo).
**Transformation**: Download → Parse → Filter NaN → Sample Posteriors → Aggregate.

**Attributes**:
*   `event_id`: String (Unique identifier, e.g., "GW150914")
*   `component_mass_1`: Float (Primary mass in solar masses)
*   `component_mass_2`: Float (Secondary mass in solar masses)
*   `mass_ratio`: Float ($q = m_2 / m_1$, $0 < q \le 1$)
*   `effective_spin`: Float ($\chi_{eff}$, dimensionless)
*   `posterior_sample_count`: Integer (Number of samples drawn per event)

**Constraints**:
*   `mass_ratio` and `effective_spin` must not be NaN.
*   Minimum 100 valid events required for analysis.

### 2. Simulation_Dataset (Synthetic or External)

Represents the theoretical population predictions.

**Source**: Synthetic Generation (Power-law hypothesis) or External Catalog.
**Transformation**: Generate/Download → Validate Schema → Filter.

**Attributes**:
*   `event_id`: String (Generated or from source)
*   `component_mass_1`: Float
*   `component_mass_2`: Float
*   `mass_ratio`: Float
*   `effective_spin`: Float
*   `formation_channel`: String (e.g., "power-law-spin")
*   `generation_method`: String (e.g., "synthetic")
*   `hypothesis_type`: String (e.g., "Null_Hypothesis" or "Alternative_Model")

**Constraints**:
*   Must contain `mass_ratio` and `effective_spin`.
*   Minimum 100 valid events required.

### 3. Statistical_Test_Result

Output of the KS test and sensitivity analysis.

**Attributes**:
*   `parameter_name`: String ("mass_ratio" or "effective_spin")
*   `ks_statistic`: Float
*   `p_value`: Float
*   `bonferroni_adjusted_p_value`: Float
*   `significance_flag`: Boolean (True if $p < \alpha$)
*   `borderline_flag`: Boolean (True if significance flips across $\alpha \in \{0.04, 0.05, 0.06\}$)
*   `alpha_threshold`: Float (The threshold used for this specific result)
*   `scope`: String ("detection_space" or "intrinsic_space")

### 4. Power_Analysis_Result

Output of the power analysis module.

**Attributes**:
*   `obs_sample_size`: Integer
*   `sim_sample_size`: Integer
*   `power_ratio`: Float (sim/obs)
*   `power_limitation_logged`: Boolean
*   `m_des`: Float (Minimum Detectable Effect Size)
*   `m_des_method`: String ("simulation_based")
*   `limitation_note`: String (Text description of the limitation)

### 5. Visualization_Output

Generated plots.

**Attributes**:
*   `figure_id`: String
*   `parameter_name`: String
*   `format`: String ("PNG")
*   `resolution_dpi`: Integer (300)
*   `file_path`: String (Relative path in `output/`)

## Data Flow

1.  **Raw Input**: Zenodo files (HDF5/CSV) → `data/raw/gwtc-1.hdf5`, `data/raw/gwtc-2.hdf5`.
2.  **Preprocessed**: `data/processed/gwtc_catalog.csv` (Schema: GWTC_Catalog).
3.  **Synthetic**: `data/processed/simulation_catalog.csv` (Schema: Simulation_Dataset).
4.  **Analysis**: `output/results/statistical_tests.json` (Schema: Statistical_Test_Result).
5.  **Power**: `output/results/power_analysis.json` (Schema: Power_Analysis_Result).
6.  **Figures**: `output/figures/kde_mass_ratio.png`, `output/figures/kde_effective_spin.png` (Schema: Visualization_Output).