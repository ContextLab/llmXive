# Data Model: Residue Distribution of Euler's Totient Function Modulo Small Primes

## Overview
The data model defines the JSON artefacts exchanged between pipeline stages. All files must validate against the schemas in `contracts/`.

## Core Entities

### 1. ResidueDataset
Aggregated residue counts for a single prime $p$.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `prime_modulus` | integer | Prime $p$ (must be 3, 5, 7, 11) | `enum: [3,5,7,11]` |
| `total_count` | integer | Number of integers processed (`N`) | `minimum: 1` |
| `frequency_map` | object (string→integer) | Mapping residue → count (`0 … p‑1`) | Keys must be strings of integers; sum of values equals `total_count`. |
| `computation_seed` | integer | Fixed random seed used for any stochastic step | `minimum: 0` |

### 2. StatisticalResult
Result of the goodness‑of‑fit test for a given prime.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `test_type` | string | `"chi_squared"` (asymptotic), `"chi_squared_monte_carlo"` or `"exact_multinomial"` | `enum: ["chi_squared","chi_squared_monte_carlo","exact_multinomial"]` |
| `test_statistic` | number | $\chi^{2}$ statistic (or exact test statistic) | `minimum: 0` |
| `p_value` | number | Empirical p‑value | `minimum: 0`, `maximum: 1` |
| `degrees_of_freedom` | integer | $p-1$ | `minimum: 1` |
| `method` | string | `"asymptotic"` / `"monte_carlo"` / `"exact"` | `enum: ["asymptotic","monte_carlo","exact"]` |
| `expected_counts` | array of numbers | Theoretical uniform counts $E_i = N/p$ (length = $p$) | `minItems: 3`, `maxItems: 11` |
| `observed_counts` | array of integers | Ordered list of observed counts $O_i$ (length = $p$) | `minItems: 3`, `maxItems: 11` |
| `uniformity_hypothesis` | boolean | `True` if $p$‑value > 0.05 (source) | — |
| `metadata` | object | Execution metadata (see below) | — |

#### Metadata Sub‑object
| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string (date‑time) | ISO 8601 execution time |
| `python_version` | string | e.g. `"3.11.6"` |
| `n_processed` | integer | Actual $N$ |
| `peak_memory_mb` | number | Peak RAM usage |
| `wall_time_sec` | number | Total runtime |
| `limit_reached` | boolean | `True` if MemoryGuard triggered |

## Data Flow
1. `sieve.compute_residues` → `ResidueDataset` JSON (`data/raw/`).  
2. `stats.run_deviation_test` consumes the JSON, produces `StatisticalResult` JSON (`data/processed/`).  
3. `visualize` reads both JSON files to generate PNG/SVG plots.  
4. `flags.generate_pass_fail` reads `StatisticalResult` and writes a tiny JSON flag file (`results/reports/flag_{p}_{N}.json`).  

All files are stored in UTF‑8 JSON, human‑readable, and checksum‑tracked.

---
