# Data Model: Statistical Properties of Simulated Black Hole Mergers

## Entities & Attributes

### 1. GWTC_Catalog (observational)
- `event_id`: string (e.g., "GW150914")
- `component_mass_1`, `component_mass_2`: float (Mₛᵤₙ)
- `mass_ratio`: float (0 < q ≤ 1)
- `effective_spin`: float (‑1 ≤ χ_eff ≤ 1)
- `formation_channel`: string = "GWTC_observed"
- `data_status`: string = "real"

### 2. Simulation_Dataset (synthetic)
- `event_id`: string ("SIM_001" …)
- `component_mass_1`, `component_mass_2`: float
- `mass_ratio`: float (0 < q ≤ 1)
- `effective_spin`: float (‑1 ≤ χ_eff ≤ 1)
- `formation_channel`: string = "synthetic_power_law"
- `generation_method`: string = "power_law_mass_independent_spin"
- `data_status`: string = "synthetic"

### 3. Data_Availability_Report
- `source_name`: string (e.g., "GWTC-1")
- `status`: string ("verified" | "unavailable")
- `reason`: string (explanation for failure)
- `checksum`: string (SHA‑256 of accepted file, or null)

### 4. Selection_Weights
- `event_id`: string
- `weight`: float (inverse detection probability)
- `scope`: string ("detection_space" | "intrinsic_space")

### 5. Statistical_Test_Result
- `parameter_name`: string ("mass_ratio" | "effective_spin")
- `ks_statistic`, `p_value`, `bonferroni_adjusted_p_value`: float
- `significance_flag`, `borderline_flag`: boolean
- `alpha_sweep_results`: list of {`alpha`: float, `is_significant`: boolean}
- `scope`: string ("detection_space" | "intrinsic_space")
- `data_status`: string ("real" | "synthetic")
- `power_analysis`: object with fields:
  - `observational_sample_size`: integer
  - `simulation_sample_size`: integer
  - `power_limitation_flag`: boolean (true if simulation size < 50 % of observational)
  - `minimum_detectable_effect_size`: float (minimum detectable Kolmogorov distance D at 80 % power, α = 0.05)
  - `limitation_note`: string (human‑readable warning about Type II error risk)

### 6. Visualization_Output
- `figure_id`: string
- `parameter_name`: string ("mass_ratio" | "effective_spin")
- `format`: "PNG"
- `resolution_dpi`: integer (≥ 300)
- `file_path`: string (relative path)
- `divergence_regions`: list of {`lower_bound`: float, `upper_bound`: float}

## Data Flow

1. **T001** – Download raw GWTC files → `data/raw/` (validated against `raw_gwtc.schema.yaml`).
2. **T002** – Record checksums & availability → `data/results/data_availability.json` (validated against `data_availability.schema.yaml`).
3. **T003** – Preprocess → `data/processed/obs_catalog.csv` (validated against `dataset.schema.yaml`).
4. **T004** – Synthetic simulation generation → `data/processed/sim_catalog.csv` (validated against `simulation_catalog.schema.yaml`).
5. **T005** – Selection‑bias correction → `data/processed/selection_weights.csv`.
6. **T006** – Weighted KS & KDE → `data/results/ks_results.json` (validated against `statistical_test_result.schema.yaml`), with nested `power_analysis`.
7. **T007** – Sensitivity sweep → updates `ks_results.json`.
8. **T009** – Plotting → PNGs in `outputs/figures/` + manifest (`visualization_output.schema.yaml`).
9. **T010** – Orchestration & final report → `data/results/final_report.md`.

## Notes

- The synthetic observational stand‑in described in earlier drafts has been **removed** from the primary analysis; the pipeline aborts if GWTC data cannot be obtained, as required by the spec.
- For **verification mode only**, a synthetic observational dataset can be generated from a **different** distribution (mass‑power‑law index = ‑2.0, spin uniform [‑0.3, 0.3]) to exercise both significant and non‑significant paths.
- All `data_status` values are now aligned across schemas: `'real'` for observational rows and `'synthetic'` for simulated rows.
