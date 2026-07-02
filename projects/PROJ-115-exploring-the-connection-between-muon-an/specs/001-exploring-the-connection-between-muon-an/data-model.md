# Data Model: Exploring the Connection Between Muon Anomalous Magnetic Dipole Moment and Dark Matter Interactions

## 1. Entity Definitions

### 1.1 ParameterPoint
Represents a single point in the parameter space and its derived physics quantities.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `m_chi` | float | Dark Matter mass (MeV) | $> 0$ |
| `m_V` | float | Mediator mass (MeV) | $> 0$ |
| `g` | float | Coupling constant ($g_\chi = g_\mu$) | $0 < g \le 1.0$ |
| `delta_a_mu` | float | One-loop contribution to $g-2$ | Calculated value |
| `omega_chi_h2` | float | Relic density $\Omega_\chi h^2$ | Calculated value |
| `sigma_SI` | float | Spin-independent cross-section (cm$^2$) | Calculated value |
| `pass_g2` | bool | $|\Delta a_\mu - \Delta a_\mu^{exp}| \le 2.51 \times 10^{-9}$ | Derived |
| `pass_relic` | bool | $\Omega_\chi h^2 \le 0.12$ | Derived |
| `pass_direct` | bool | $\sigma_{SI} \le \sigma_{Xenon1T}$ | Derived |
| `pass_lep` | bool | LEP mono-photon limit respected | Derived |
| `is_viable` | bool | All constraints pass | Logical AND of above |
| `status` | str | "viable", "excluded", "undefined" | Enum |

### 1.2 ConstraintDataset
Immutable collection of external limits used for validation.

| Field | Type | Description |
| :--- | :--- | :--- |
| `source` | str | "Planck_2018", "Xenon1T_2014", "LEP" |
| `limit_value` | float | The numerical limit (e.g., 0.12, cross-section value) |
| `mass_range` | tuple | (min_mass, max_mass) where limit applies |
| `formula_ref` | str | Reference to the formula or paper used |

### 1.3 LookupTable
Pre-computed table for relic density to enable fast interpolation.

| Field | Type | Description |
| :--- | :--- | :--- |
| `m_chi` | float | DM mass |
| `m_V` | float | Mediator mass |
| `g` | float | Coupling |
| `omega_chi_h2` | float | Pre-computed relic density |
| `s_factor` | float | Sommerfeld enhancement factor |

## 2. Data Flow

1. **Input**: Grid parameters ($m_\chi$ range, $m_V$ range, $g$ range).
2. **Pre-computation**: `relic_density.py` generates `LookupTable` (CSV) using RK4.
3. **Scan**: `run_scan.py` iterates grid points, interpolates `omega_chi_h2` from `LookupTable`, calculates $\Delta a_\mu$ and $\sigma_{SI}$.
4. **Filtering**: Apply constraints (FR-005) to generate `ParameterPoint` list.
5. **Output**: `viable_points.csv` (filtered `ParameterPoint`), `viable_region.png` (plot).

## 3. File Formats

- **CSV**: Comma-separated values with headers. Used for `viable_points.csv`, `relic_lookup.csv`.
- **Parquet**: Used for raw LEP data (read-only).
- **PNG**: 300 DPI, RGB, with labels and legends.
- **JSON**: `checksums.json` for data hygiene.
