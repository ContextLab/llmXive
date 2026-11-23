# Data Model: 001-solar-purification-tradeoff

## 1. Overview

This document defines the data structures used throughout the simulation pipeline. All data is serialized to JSON/CSV/YAML for reproducibility and validation against the contracts defined in `contracts/`.

## 2. Core Entities

### 2.1 MaterialProfile
Represents a construction material with physical and economic properties.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `material_id` | `str` | Unique identifier (e.g., "ALU_001") | Generated |
| `name` | `str` | Common name (e.g., "Aluminum") | Hardcoded |
| `thermal_conductivity` | `float` | W/m·K | NIST |
| `emissivity` | `float` | 0.0–1.0 | NIST |
| `specific_heat` | `float` | J/kg·K | NIST |
| `density` | `float` | kg/m³ | NIST |
| `unit_price` | `float` | USD/kg | Scraped / Fallback |

### 2.2 GeometryConfig
Represents a solar still design configuration.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `geometry_id` | `str` | Unique identifier (e.g., "FLAT_001") | Generated |
| `type` | `str` | Enum: `flat-plate`, `single-slope`, `double-slope` | Spec |
| `inclination_angle` | `float` | Degrees (0–90) | Spec (Swept) |
| `surface_area` | `float` | m² | Spec (fixed for comparison) |
| `view_factor` | `float` | 0.0–1.0 | Calculated (Angle-dependent) |
| `convective_coeff` | `float` | W/m²·K | Calculated (Angle-dependent, calibrated) |
| `fabrication_complexity_factor` | `float` | Cost multiplier for labor/sealing | Derived from literature |

### 2.3 SolarIrradianceProfile
Time-series data for solar input.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `timestamp` | `str` | ISO 8601 | NASA POWER |
| `irradiance` | `float` | W/m² | NASA POWER |
| `air_temperature` | `float` | °C | NASA POWER |

### 2.4 SimulationResult
Output of a single simulation run.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `run_id` | `str` | Unique hash | Generated |
| `material_id` | `str` | FK to MaterialProfile | Input |
| `geometry_id` | `str` | FK to GeometryConfig | Input |
| `steady_state_efficiency` | `float` | η (0.0–1.0) | Calculated (Output/Input) |
| `total_cost` | `float` | USD | Calculated (Mass × Price × FCF) |
| `energy_balance_error` | `float` | % | Calculated (Input - Output - Losses) |
| `convergence_status` | `str` | `success`, `failed`, `invalid_balance` | Validation |
| `time_to_convergence` | `float` | Minutes | Simulation |
| `plausibility_flag` | `str` | `ok`, `warning` | Secondary check (0.30-0.60) |
| `calibration_factor` | `float` | Calibration multiplier applied to convection | Calibration Step |

## 3. Data Flow

1. **Ingestion**: `data_ingestion.py` fetches material properties (hardcoded) and prices → `data/processed/materials.csv`.
2. **Configuration**: `geometry_config.yaml` defines the 3 geometries and angle sweep parameters.
3. **Calibration**: `validation.py` calibrates model parameters against Tiwari et al. (2003) data.
4. **Simulation**: `simulation.py` reads materials + geometries + solar profile → `data/processed/simulation_results.csv`.
5. **Optimization**: `optimization.py` reads results → `data/processed/pareto_frontier.csv`.
6. **Validation**: `validation.py` checks `energy_balance_error` and `plausibility_flag` → updates `convergence_status`.

## 4. File Formats

- **Materials**: CSV (comma-separated, UTF-8).
- **Geometries**: YAML (human-readable config).
- **Solar Data**: JSON (array of objects).
- **Results**: CSV (for plotting and analysis).
- **Plots**: PNG (high-res, 300 DPI).