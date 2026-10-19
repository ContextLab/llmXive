# Data Model: Predicting the Impact of Residual Stress on Fatigue Life

## Unified Dataset Schema (`DatasetRecord`)
The pipeline produces a single CSV (`data/processed/unified_fatigue.csv`) that conforms to the following schema. All columns are required unless marked optional.

| Column | Type | Description | Derived / Flag |
|--------|------|-------------|----------------|
| `sample_id` | string | Unique identifier for the observation | — |
| `material_class` | categorical (`steel`, `aluminum`) | Material family | — |
| `heat_input` | float (MJ) | Process heat input | — |
| `cooling_rate` | float (K/s) | Process cooling rate | — |
| `other_process_params` | string (JSON) | JSON‑encoded dictionary of additional numeric process parameters | — |
| `elastic_modulus` | float (GPa) | Material elastic modulus (optional) | Optional |
| `yield_strength` | float (MPa) | Material yield strength (optional) | Optional |
| `residual_stress_measured` | float (MPa) | Directly measured residual stress (optional) | Optional |
| `is_proxy` | boolean | `True` if the **proxy** value is used in place of a missing measured stress; `False` otherwise | Flag indicating proxy usage |
| `residual_stress_proxy` | float (MPa) | Proxy‑computed residual stress, calculated for **all rows** via `σ_res = k·heat_input·cooling_rate`, independently of whether a measured value exists. It is **not expected to match** `residual_stress_measured` — the measured value is generated/observed through a different (stochastic, additive) process, and the proxy–measured agreement is reported separately as a descriptive check (FR-014) | Derived; flagged as proxy |
| `fatigue_life_cycles` | integer | Number of cycles to failure (target variable) | — |
| `source` | string | Original dataset name or “synthetic” | — |
| `checksum` | string | SHA‑256 checksum of the raw row for provenance (recorded during ingestion) | Derived |

### Data Hygiene Rules
1. **Immutability**: Raw files under `data/raw/` are never altered. Every transformation writes a new file under `data/processed/` and records its checksum in `state/projects/PROJ-291-predicting-the-impact-of-residual-stress.yaml`.
2. **Missing-Value Flags**: Original missingness is logged in `data/processed/missing_flags.json`; imputed values are median‑filled.
3. **Unit Consistency**: All stress values are stored in MPa; any source in psi is converted during preprocessing.
4. **Proxy Integrity**: The proxy `σ_res = k·heat_input·cooling_rate` is computed **for all rows**, independently of whether a measured value exists (this guarantees rows with both values exist for the FR-014 agreement check). `is_proxy=True` marks rows where the proxy **replaces** a missing measured value in modeling; for rows with a measured value, the measured value is used for modeling and `is_proxy` remains `False`. The proxy is never assumed to equal the measured value; their agreement is reported descriptively with an explicit circularity caveat.