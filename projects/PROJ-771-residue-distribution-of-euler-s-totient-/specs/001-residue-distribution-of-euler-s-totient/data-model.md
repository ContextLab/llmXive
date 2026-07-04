# Data Model: Residue Distribution of Euler's Totient Function Modulo Small Primes

## Overview

This document defines the data structures used for computing, storing, and analyzing the residues of Euler's totient function. The model ensures strict adherence to arbitrary-precision arithmetic (Constitution Principle VI) and supports the statistical pipeline defined in the spec, which focuses on deviation magnitude against theoretical error bounds.

## Core Entities

### 1. ResidueDataset
Represents the aggregated counts of $\phi(n) \pmod p$ for a specific prime $p$ and range $N$.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `prime_modulus` | `int` | The prime $p \in \{3, 5, 7, 11\}$. | Must be in allowed set. |
| `total_count` | `int` | Total number of integers processed ($N$). | $N \ge 1$. |
| `frequency_map` | `dict[int, int]` | Mapping of residue $r \to$ count. | Keys $0 \dots p-1$. Values $\ge 0$. Sum = `total_count`. |
| `computation_seed` | `int` | Random seed used for any stochastic elements (e.g., Block Bootstrap). | Fixed for reproducibility. |

### 2. StatisticalResult
Represents the output of the deviation magnitude test.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `test_type` | `str` | Type of test performed (e.g., "block_bootstrap_deviation"). | Enum: ["block_bootstrap_deviation"]. |
| `test_statistic` | `float` | The calculated deviation statistic (e.g., sum of squared residuals). | $\ge 0$. |
| `p_value` | `float` | Probability of observing this statistic under $H_0$ (deviation within bounds). | $0 \le p \le 1$. |
| `degrees_of_freedom` | `int` | $df = p - 1$ (used for reference, though Bootstrap is used). | $df \ge 1$. |
| `method` | `str` | Method used for p-value estimation (block_bootstrap). | Enum: ["block_bootstrap"]. |
| `deviation_magnitude` | `float` | The maximum absolute deviation $|O_k - E_k^{theo}|$ observed. | $\ge 0$. |
| `error_term_residual` | `float` | The ratio of observed deviation to predicted error bound $O(N^{1-\delta})$. | $\ge 0$. |
| `expected_counts` | `list[float]` | List of theoretical expected counts $E_k^{theo}$ for each residue. | Length = $p$. |
| `uniformity_hypothesis` | `bool` | **Deprecated/Secondary**: Result of $H_0$ at $\alpha=0.05$ regarding deviation bounds. | True if $p > 0.05$. |

### 3. ExecutionMetadata
Tracks the runtime environment for reproducibility (Constitution Principle I).

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | `str` | ISO 8601 timestamp of execution. |
| `python_version` | `str` | Version of Python used. |
| `n_processed` | `int` | Actual $N$ processed. |
| `peak_memory_mb` | `float` | Peak RAM usage in MB. |
| `wall_time_sec` | `float` | Total execution time. |
| `limit_reached` | `bool` | Flag indicating if memory limit was reached (FR-007). |

## Data Flow

1.  **Input**: Parameters $N$ (int), $p$ (int).
2.  **Processing**:
    - `sieve.py` generates `ResidueDataset`.
    - `stats.py` consumes `ResidueDataset` to produce `StatisticalResult` using Block Bootstrap.
3.  **Output**:
    - `data/raw/residues_{p}_{N}.json` (ResidueDataset).
    - `data/processed/stats_{p}_{N}.json` (StatisticalResult + Metadata).

## Storage Schema

Files are stored in JSON format for portability and human readability.

**Example `data/raw/residues_3_100.json`:**
```json
{
  "prime_modulus": 3,
  "total_count": 100,
  "frequency_map": {
    "0": 33,
    "1": 34,
    "2": 33
  },
  "computation_seed": 42
}
```

**Example `data/processed/stats_3_100.json`:**
```json
{
  "test_type": "block_bootstrap_deviation",
  "test_statistic": 0.15,
  "p_value": 0.82,
  "degrees_of_freedom": 2,
  "method": "block_bootstrap",
  "deviation_magnitude": 0.02,
  "error_term_residual": 0.95,
  "expected_counts": [33.33, 33.33, 33.33],
  "uniformity_hypothesis": true,
  "metadata": {
    "timestamp": "2026-07-04T12:00:00Z",
    "python_version": "3.11.0",
    "n_processed": 100,
    "peak_memory_mb": 45.2,
    "wall_time_sec": 0.5,
    "limit_reached": false
  }
}
```
