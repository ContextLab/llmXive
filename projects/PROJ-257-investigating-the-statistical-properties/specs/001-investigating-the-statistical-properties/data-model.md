# Data Model: Statistical Properties of Simulated Black Hole Mergers

## Entities & Attributes

### 1. GWTC_Catalog (Observational)
Represents the preprocessed observational gravitational-wave transient catalog.
- **event_id**: `string` (Unique identifier, e.g., "GW150914")
- **component_mass_1**: `float` (Primary mass in solar masses, $M_\odot$)
- **component_mass_2**: `float` (Secondary mass in solar masses, $M_\odot$)
- **mass_ratio**: `float` ($q = m_2 / m_1$, $0 < q \le 1$)
- **effective_spin**: `float` ($\chi_{eff}$, dimensionless)
- **posterior_samples**: `list[float]` (Optional: Raw samples for uncertainty analysis, flattened or stored separately)

### 2. Simulation_Dataset (Synthetic)
Represents the generated synthetic population based on the Power-law spin hypothesis.
- **event_id**: `string` (Synthetic ID, e.g., "SIM_001")
- **component_mass_1**: `float` ($M_\odot$)
- **component_mass_2**: `float` ($M_\odot$)
- **mass_ratio**: `float` ($q$)
- **effective_spin**: `float` ($\chi_{eff}$)
- **formation_channel**: `string` (Literal: "synthetic_power_law")
- **generation_method**: `string` (Literal: "power_law_spin_distribution")

### 3. Statistical_Test_Result
Output of the KS test and subsequent corrections.
- **parameter_name**: `string` (e.g., "mass_ratio", "effective_spin")
- **ks_statistic**: `float` (D statistic)
- **p_value**: `float` (Raw p-value)
- **bonferroni_adjusted_p_value**: `float` (Corrected p-value)
- **significance_flag**: `boolean` (True if $p < \alpha_{adjusted}$)
- **borderline_flag**: `boolean` (True if significance flips across $\alpha$ sweep)
- **alpha_sweep_results**: `list<object>` (Details of sensitivity analysis)

### 4. Power_Analysis_Result
Output of the power limitation check.
- **observational_sample_size**: `integer`
- **simulation_sample_size**: `integer`
- **power_limitation_flag**: `boolean` (True if sim size < 50% of obs size)
- **minimum_detectable_effect_size**: `float` (MDES value)
- **limitation_note**: `string` (Human-readable warning)

### 5. Visualization_Output
Generated figures.
- **figure_id**: `string` (e.g., "fig_mass_ratio_kde")
- **parameter_name**: `string`
- **format**: `string` (Literal: "PNG")
- **resolution_dpi**: `integer` (Literal: 300)
- **file_path**: `string` (Relative path to output)
- **divergence_regions**: `list<object>` (Regions where $p < 0.05$)

### 6. Selection_Weights
Weights derived from Inverse Probability Weighting (IPW) to correct for selection bias.
- **event_id**: `string` (Reference to the event in GWTC_Catalog)
- **weight**: `float` (Inverse of detection probability)
- **detection_space_flag**: `boolean` (True if weight is only valid within detection space)

## Data Flow

1. **Raw Download** (Zenodo) $\to$ `data/raw/gwtc_1_posteriors.h5` (or similar)
2. **Preprocessing** $\to$ `data/processed/obs_catalog.csv` (GWTC_Catalog schema)
3. **Synthetic Generation** $\to$ `data/processed/sim_catalog.csv` (Simulation_Dataset schema)
4. **Selection Bias Correction** $\to$ `data/processed/selection_weights.csv` (Selection_Weights schema)
5. **Analysis** $\to$ `data/results/ks_results.json` (Statistical_Test_Result schema)
6. **Power Check** $\to$ `data/results/power_analysis.json` (Power_Analysis_Result schema)
7. **Visualization** $\to$ `outputs/figures/*.png` (Visualization_Output schema)