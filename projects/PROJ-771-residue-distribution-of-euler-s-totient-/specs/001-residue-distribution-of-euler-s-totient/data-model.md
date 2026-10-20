# Data Model: Residue Distribution of Euler's Totient Function Modulo Small Primes

## Overview
The data model defines the JSON artefacts exchanged between pipeline stages. All files must validate against the schemas in `contracts/`.

## Core Entities

### 1. ResidueDataset
Aggregated residue counts for a single prime $p$.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `prime_modulus` | integer | Prime $p$ (e.g., 3, 5, 7, 11) | `enum: [3,5,7,11]` |
| `total_count` | integer | Number of integers processed (`N`) | `minimum: 1` |
| `frequency_map` | object (string → integer) | Mapping residue → count (`0 … p‑1`) | Keys are strings of integers; sum of values equals `total_count`. |
| `computation_seed` | integer | Fixed random seed for reproducibility | `minimum: 0` |

### 2. StatisticalResult
Result of the goodness‑of‑fit test for a given prime, **against the theoretically biased expected counts**.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `test_type` | string | `"chi_squared"`, `"chi_squared_monte_carlo"` or `"exact_multinomial"` |
| `test_statistic` | number | $\chi^{2}$ (or exact) statistic | `minimum: 0` |
| `p_value` | number | Empirical p‑value (proportion of simulated or exact tail probabilities) | `minimum: 0`, `maximum: 1` |
| `degrees_of_freedom` | integer | $p-1$ | `minimum: 1` |
| `method` | string | `"asymptotic"`, `"monte_carlo"` or `"exact"` |
| `expected_counts` | array of numbers | **Theoretically biased expected counts** $E_i$ for each residue (derived from number‑theoretic formulas). |
| `observed_counts` | array of integers | Observed counts $O_i$ for each residue (ordered 0 … p‑1). |
| `uniformity_hypothesis` | boolean | `True` if p‑value > 0.05 (source → Replication‑crisis) |
| `metadata` | object | Execution metadata (see below) |
#### Metadata Sub‑object
| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string (date‑time) | ISO 8601 execution time |
| `python_version` | string | e.g. `"3.11.6"` |
| `n_processed` | integer | Actual $N$ |
| `peak_memory_mb` | number | Peak RAM usage (MB) |
| `wall_time_sec` | number | Total runtime (seconds) |
| `limit_reached` | boolean | `True` if MemoryGuard triggered |

## Data Flow
1. `sieve.compute_residues` → `ResidueDataset` JSON (`data/raw/`).  
2. `stats.run_chi_squared_test` consumes the JSON, produces `StatisticalResult` JSON (`data/processed/`).  
3. `visualize` reads both JSON files to generate PNG/SVG plots.  
4. `flags.generate_pass_fail` reads `StatisticalResult` and writes a tiny JSON flag file (`results/reports/flag_{p}_{N}.json`).  

All files are UTF‑8 JSON, human‑readable, and checksum‑tracked.

---


