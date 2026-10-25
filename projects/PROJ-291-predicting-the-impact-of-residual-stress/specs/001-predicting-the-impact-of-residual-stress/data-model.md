# Data Model: Predicting the Impact of Residual Stress on Fatigue Life

## Unified Dataset Schema (`DatasetRecord`)
The pipeline produces a single CSV (`data/processed/unified_fatigue.csv`) that conforms to the following schema. All columns are required unless marked optional.

| Column | Type | Description | Derived / Flag |
|--------|------|-------------|----------------|
| `sample_id` | string | Unique identifier for the observation | — |
| `material_class` | categorical (`steel`, `aluminum`) | Material family | — |
| `heat_input` | number (MJ) | Process heat input | — |
| `cooling_rate` | number (K/s) | Process cooling rate | — |
| `other_process_params` | string (JSON) | JSON‑encoded dictionary of additional numeric process parameters | — |
| `stress_unit` | string (`MPa`, `psi`) | Original unit of the residual stress measurement before conversion | **Derived** (source column) |
| `elastic_modulus` | number (GPa) | Elastic modulus (optional) | Optional |
| `yield_strength` | number (MPa) | Yield strength (optional) | Optional |
| `residual_stress_measured` | number (MPa) | Directly measured residual stress (optional) | Optional |
| `is_proxy` | boolean | `True` if the proxy value is used as the stress feature in place of a missing measured stress; `False` otherwise | Flag |
| `residual_stress_proxy` | number (MPa) | Proxy‑computed residual stress (`σ_res = k·heat_input·cooling_rate`), computed for all rows but used as a stress feature only when `is_proxy` is true; never overwritten with measured values. | Derived |
| `fatigue_life_cycles` | integer | Number of cycles to failure (target) | — |
| `source` | string | Origin of the record (`synthetic`, `verification`, or name of a real open dataset) | — |
| `checksum` | string | SHA‑256 checksum of the raw row for provenance | Derived |

### Data Hygiene Rules
1. **Immutability** – Raw files under `data/raw/` are never altered. Every transformation writes a new file under `data/processed/` and records its checksum in `state/projects/...yaml`.  
2. **Missing‑value flags** – Original missingness captured in `data/processed/missing_flags.json`; imputed values are median‑filled.  
3. **Unit consistency** – All stress values stored in MPa; any source in psi is converted using the explicit `stress_unit` column.  
4. **Proxy integrity** – Proxy computed for all rows (enabling FR‑014 agreement evaluation) but **used as the stress feature only for rows where measured stress is missing** (`is_proxy=True`). For rows with measured stress, the measured value is used for modeling, `is_proxy=False`, and the proxy column retains its independently computed value. Proxy–measured agreement (Pearson r, R²) is reported descriptively with an explicit circularity caveat.

---


