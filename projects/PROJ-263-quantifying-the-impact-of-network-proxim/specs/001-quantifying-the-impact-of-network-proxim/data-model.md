# Data Model: Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale‑Free Networks

## 1. Network Data (Derived)
| Field | Type | Description |
|-------|------|-------------|
| `node_id` | integer | Unique identifier for each node (0‑based). |
| `x` | float | Longitude (or projected X) of the node (real or synthetic). |
| `y` | float | Latitude (or projected Y) of the node (real or synthetic). |
| `degree` | integer | Node degree in the graph. |
| `component` | integer | Identifier of the connected component (only LCC retained). |

Stored as `data/derived/nodes.csv`.

## 2. Edge List (Derived)
| Field | Type | Description |
|-------|------|-------------|
| `source` | integer | Source node ID. |
| `target` | integer | Target node ID. |
| `weight` | float (optional) | Edge weight (default = 1). |

Stored as `data/derived/edges.csv`.

## 3. Simulation Output (Primary Contract)
Each row corresponds to a single Monte‑Carlo run (see `contracts/simulation_output.schema.yaml`).

| Column | Type | Meaning |
|--------|------|---------|
| `simulation_id` | string | UUID formatted as `beta_{beta}_lambda_{lambda}_seed_{seed}`. |
| `beta_0` | float | Base transmission probability used for this run. |
| `lambda` | float | Spatial decay parameter applied to Euclidean distances. |
| `seed` | integer | Random seed ensuring reproducibility. |
| `peak_infection` | float (0‑1) | Maximum fraction of infected nodes during the run. |
| `final_size` | float (0‑1) | Fraction of nodes ever infected by the end of the simulation. |
| `threshold_hit` | boolean | True if the run contributed to crossing the epidemic threshold (average final outbreak size > 5 % of nodes). |
| `runtime_seconds` | float | Wall‑clock time taken by the simulation (seconds). |

File path: `data/derived/simulation_results.csv`.

## 4. Null Model Output
Identical schema to the primary simulation output; stored in `data/derived/null_results.csv`. The `simulation_id` encodes the null iteration index.

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
| `p_value` | float | Permutation test p‑value (spatial vs. null). |
| `effect_size` | float | Cohen’s d (spatial vs. null). |
| `significant` | boolean | Flag after Bonferroni correction (α = 0.05/3). |

Stored as `data/derived/summary_stats.csv`.

---

