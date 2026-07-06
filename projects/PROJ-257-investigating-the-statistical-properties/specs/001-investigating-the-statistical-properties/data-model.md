# Data Model: Statistical Properties of Simulated Black Hole Mergers

## Entities

### GWTC_Catalog
Represents the observational gravitational-wave transient catalog.
- **Attributes**:
  - `event_id`: Unique identifier for the merger event (string).
  - `component_mass_1`: Primary component mass in solar masses (float).
  - `component_mass_2`: Secondary component mass in solar masses (float).
  - `mass_ratio`: Ratio $q = m_2/m_1$ (float, 0 < q ≤ 1).
  - `effective_spin`: Effective aligned spin parameter $\chi_{eff}$ (float, -1 to 1).
  - `posterior_samples`: List of sampled values for uncertain parameters (list of floats, optional for point-estimate CSV).

### Simulation_Dataset
Represents the merger population predictions from a synthetic model.
- **Attributes**:
  - `event_id`: Unique identifier for the synthetic event (string).
  - `component_mass_1`: Primary component mass (float).
  - `component_mass_2`: Secondary component mass (float).
  - `mass_ratio`: Ratio $q$ (float).
  - `effective_spin`: Effective aligned spin (float).
  - `formation_channel`: Source of the event (string, e.g., "synthetic_powerlaw").
  - `generation_method`: Description of the generation hypothesis (string).

### Statistical_Test_Result
Represents the output of a KS test comparison.
- **Attributes**:
  - `parameter_name`: Name of the parameter tested (string, e.g., "mass_ratio").
  - `ks_statistic`: The KS statistic value (float).
  - `p_value`: Raw p-value (float).
  - `bonferroni_adjusted_p_value`: Corrected p-value (float).
  - `significance_flag`: Boolean indicating if $p < \alpha_{adjusted}$.
  - `borderline_flag`: Boolean indicating if significance flips in sensitivity sweep.

### Visualization_Output
Represents generated plots.
- **Attributes**:
  - `figure_id`: Unique identifier (string).
  - `parameter_name`: Parameter plotted (string).
  - `format`: File format (string, "png").
  - `resolution_dpi`: Resolution in dots per inch (integer, ≥300).
  - `file_path`: Relative path to the file (string).

## Data Flow

1. **Raw Data**: Downloaded from Zenodo (if available) or generated synthetically.
2. **Preprocessing**: Filter rows with NaNs in key fields; extract point estimates from posteriors (mean/median).
3. **Analysis**: Compute KDEs, run KS tests, perform sensitivity sweep.
4. **Output**: Save results to JSON/CSV and generate PNG plots.
