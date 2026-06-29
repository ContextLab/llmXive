# Data Model: Exploring the Connection Between Muon Anomalous Magnetic Dipole Moment and Dark Matter Interactions

## Entity Definitions

### 1. ParameterPoint
Represents a single point in the parameter space being scanned.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `m_chi` | float | Dark Matter mass (MeV) | $1 \le m_\chi \le 1000$ |
| `m_V` | float | Mediator mass (MeV) | $10 \le m_V \le 1000$ |
| `g` | float | Coupling ($g_\chi = g_\mu$) | $10^{-5} \le g \le 1.0$ |
| `delta_a_mu` | float | Calculated $\Delta a_\mu$ | Computed value |
| `omega_chi_h2` | float | Relic density $\Omega_\chi h^2$ | Computed value |
| `sigma_SI` | float | Spin-independent cross-section (cm²) | Computed value |
| `pass_g2` | bool | Passes $|\Delta a_\mu - \Delta a_\mu^{exp}| \le 2.51 \times 10^{-9}$ | Derived |
| `pass_relic` | bool | Passes $\Omega_\chi h^2 \le 0.12$ | Derived |
| `pass_xenon` | bool | Passes Xenon1T limit | Derived |
| `pass_lep` | bool | Passes LEP limit | Derived |
| `is_viable` | bool | Passes ALL constraints | `pass_g2 and pass_relic and pass_xenon and pass_lep` |

### 2. ConstraintDataset
Immutable collection of external limits used for validation.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `planck_limit` | float | Max allowed relic density | 0.12 (Constant) |
| `lepaute_data` | list[dict] | LEP exclusion points | `lepaute_data.json` |
| `xenon_limits` | list[dict] | Xenon1T mass vs. cross-section | CSV (if available) |

### 3. ScanConfiguration
Stores the runtime parameters of the scan for reproducibility (FR-007).

| Field | Type | Description |
| :--- | :--- | :--- |
| `grid_m_chi` | list[float] | Log-spaced array of $m_\chi$ |
| `grid_m_V` | list[float] | Log-spaced array of $m_V$ |
| `grid_g` | list[float] | Log-spaced array of $g$ |
| `seed` | int | Random seed (if any stochasticity) |
| `timestamp` | str | ISO8601 run time |
| `script_hash` | str | SHA-256 of `run_scan.py` |

## Data Flow

1.  **Input**: `ScanConfiguration` + `ConstraintDataset`.
2.  **Process**: Iterate over grid points $\to$ Compute `ParameterPoint` fields $\to$ Apply constraints.
3.  **Output**:
    *   `viable_points.csv`: Filtered `ParameterPoint` rows where `is_viable == True`.
    *   `summary.txt`: Count of viable points, excluded regions, and configuration details.
    *   `viable_region.png`: 2D contour plot of $m_V$ vs $g$ (or $m_\chi$ vs $m_V$).

## File Formats

### Input: `lepaute_data.json`
```json
[
  {"m_V": 100.0, "g_limit": 0.001},
  {"m_V": 200.0, "g_limit": 0.002}
]
```

### Output: `viable_points.csv`
```csv
m_chi,m_V,g,delta_a_mu,omega_chi_h2,sigma_SI,pass_g2,pass_relic,pass_xenon,pass_lep,is_viable
10.0,50.0,1e-4,2.51e-9,0.05,1e-45,true,true,true,true,true
```
