# Data Model: Statistical Properties of Simulated Black Hole Mergers

## Entities & Attributes

### 1. GWTC_Catalog (observational)
- `event_id`: string  
- `component_mass_1`: number ≥ 0 (M⊙)  
- `component_mass_2`: number ≥ 0 (M⊙)  
- `mass_ratio`: number (0 < q ≤ 1)  
- `effective_spin`: number (‑1 ≤ χ_eff ≤ 1)  
- `formation_channel`: enum `"GWTC_observed"`  
- `data_status`: enum `"real"`

### 2. Simulation_Dataset (derived from IllustrisTNG/EAGLE)
- `event_id`: string (`SIM_001`…)  
- `component_mass_1`: number ≥ 0  
- `component_mass_2`: number ≥ 0  
- `mass_ratio`: number (0 < q ≤ 1)  
- `effective_spin`: number (‑1 ≤ χ_eff ≤ 1)  
- `formation_channel`: enum `"derived_from_IllustrisTNG_EAGLE"`  
- `generation_method`: string (`"Rodriguez2022_mapping"` )  
- `data_status`: enum `"synthetic"`

### 3. Data_Availability_Report
- `source_name`: string (`"GWTC-1"` / `"GWTC-2"` / `"Simulation_Catalog"` / `"Efficiency_Curves"`)  
- `status`: enum `"verified"` | `"unavailable"`  
- `reason`: string (explanation when status is `"unavailable"`)  
- `checksum`: string | null (SHA‑256)

### 4. Selection_Weights
- `event_id`: string  
- `weight`: number ≥ 0 (inverse detection probability or model‑based probability)  
- `scope`: enum `"detection_space"` | `"intrinsic_space"`

### 5. Statistical_Test_Result
- `parameter_name`: `"mass_ratio"` | `"effective_spin"` | `"joint"`  
- `ks_statistic`: number [0, 1] *(null for joint test)*  
- `energy_distance`: number [0, ∞] *(null for marginal tests)*  
- `p_value`: number [0, 1]  
- `bonferroni_adjusted_p_value`: number [0, 1] *(null for joint test)*  
- `significance_flag`: boolean  
- `borderline_flag`: boolean  
- `alpha_sweep_results`: array of `{alpha: number, is_significant: boolean}`  
- `scope`: `"detection_space"` | `"intrinsic_space"`  
- `data_status`: `"real"` | `"synthetic"`  
- `power_analysis`: object  
  - `observational_sample_size`: integer ≥ 0  
  - `simulation_sample_size`: integer ≥ 0  
  - `power_limitation_flag`: boolean  
  - `monte_carlo_mdes`: number *(Monte‑Carlo estimated MDES)*  
  - `limitation_note`: string  
- `performance_metrics` *(optional)*: object  
  - `runtime_seconds`: number  
  - `peak_memory_gb`: number  
  - `peak_disk_gb`: number  

### 6. Visualization_Output
- `figure_id`: string (`"mass_ratio_kde"` | `"effective_spin_kde"` | `"joint_density"` )  
- `parameter_name`: `"mass_ratio"` | `"effective_spin"` | `"joint"`  
- `format`: `"PNG"`  
- `resolution_dpi`: integer ≥ 300  
- `file_path`: string (relative)  
- `divergence_regions`: array of `{lower_bound: number, upper_bound: number}` *(empty for joint figure)*

### 7. Performance_Metrics *(new)*
- `runtime_seconds`: number  
- `peak_memory_gb`: number  
- `peak_disk_gb`: number  

## Data Flow Overview

1. **T001** → raw GWTC files → `raw_gwtc.schema.yaml`  
2. **T002** → `data_availability.json` → `data_availability.schema.yaml`  
3. **T004a** → raw community simulation file → `raw_gwtc.schema.yaml` (re‑used)  
4. **T004b** → derived BBH catalog from IllustrisTNG/EAGLE → `simulation_catalog.schema.yaml`  
5. **T005a/T005b** → `selection_weights.csv` → `dataset.schema.yaml`  
6. **T003** → `obs_catalog.csv` → `dataset.schema.yaml` (validated against `gwtc_catalog.schema.yaml` via T003b)  
7. **T006 / T006b** → `ks_results.json` → `statistical_test_result.schema.yaml`  
8. **T007 / T008b** → augment `ks_results.json` (same schema)  
9. **T009** → PNG figures + `figure_manifest.json` → `visualization_output.schema.yaml`  
10. **T011** → `performance_metrics.json` (validated via optional fields in `statistical_test_result.schema.yaml`)  
11. **T010** → `final_report.md` (free‑form).

All intermediate files are version‑hashed and recorded in project state.

---


