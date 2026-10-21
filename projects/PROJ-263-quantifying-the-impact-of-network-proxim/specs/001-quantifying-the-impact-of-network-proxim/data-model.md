# Data Model: Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale‑Free Networks

## 1. Network Data (Derived)
| Field | Type | Description |
|-------|------|-------------|
| `node_id` | integer | Unique identifier for each node (0‑based). |
| `x` | float | X‑coordinate (synthetic or MDS‑derived). |
| `y` | float | Y‑coordinate (synthetic or MDS‑derived). |
| `degree` | integer | Node degree in the graph. |
| `component` | integer | Identifier of the connected component (only LCC kept). |

Stored as `data/derived/nodes.csv`.

## 2. Edge List (Derived)
| Field | Type | Description |
|-------|------|-------------|
| `source` | integer | Source node ID. |
| `target` | integer | Target node ID. |
| `weight` | float (optional) | Edge weight (default = 1). |

Stored as `data/derived/edges.csv`.

## 3. Simulation Output (Primary Contract)
See `contracts/simulation_output.schema.yaml` for the full JSON‑Schema. In brief, each row corresponds to a single Monte‑Carlo run:

| Column | Type | Meaning |
|--------|------|---------|
| `simulation_id` | string | UUID of the run (`{beta}_{lambda}_{seed}`). |
| `beta_0` | float | Base transmission rate used. |
| `lambda` | float | Spatial decay parameter. |
| `seed` | integer | Random seed for reproducibility. |
| `peak_infection` | float | Maximum fraction of infected nodes observed during the run. |
| `final_size` | float | Fraction of nodes ever infected by the end of the run. |
| `threshold_hit` | boolean | Whether the run contributed to crossing the epidemic threshold (peak ≥ 5 %). |
| `runtime_seconds` | float | Wall‑clock time for the run. |

File path: `data/derived/simulation_results.csv`.

## 4. Null Model Output
Same schema as above, stored in `data/derived/null_results.csv`. The `simulation_id` encodes the null iteration index.

## 5. Summary Statistics (Derived)
Aggregated per (`beta_0`, `lambda`) pair:

| Column | Type | Description |
|--------|------|-------------|
| `beta_0` | float | Base transmission rate. |
| `lambda` | float | Spatial decay. |
| `mean_peak` | float | Mean of `peak_infection` across MC runs. |
| `std_peak` | float | Standard deviation of `peak_infection`. |
| `mean_final` | float | Mean final outbreak size. |
| `threshold_estimate` | float or string | Estimated epidemic threshold (or `"undefined"`). |
| `p_value` | float | Permutation test p‑value (null vs. spatial). |
| `effect_size` | float | Cohen’s d (spatial vs. null). |
| `significant` | boolean | Flag per α = 0.05 (Bonferroni‑adjusted). |

Stored as `data/derived/summary_stats.csv`.

---
