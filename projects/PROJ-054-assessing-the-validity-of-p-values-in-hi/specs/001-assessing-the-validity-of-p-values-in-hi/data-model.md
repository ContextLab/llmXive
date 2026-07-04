# Data Model: Assessing the Validity of p-Values in High-Dimensional Data

## Overview

This document defines the data structures used in the simulation study. All data is stored in local files (CSV, JSON, or NumPy arrays) under `data/`.

## Entities

### 1. SyntheticDataset
Represents a generated high-dimensional dataset.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `dataset_id` | `str` | Unique UUID for the dataset. |
| `n` | `int` | Number of samples (rows). |
| `p` | `int` | Number of features (columns). |
| `rho` | `float` | Target correlation coefficient ($\rho$). |
| `distribution` | `str` | Distribution type (e.g., "normal", "t_df3", "skew"). |
| `seed` | `int` | Random seed used for generation. |
| `correlation_matrix` | `np.ndarray` | The $p \times p$ covariance matrix used. |
| `data_matrix` | `np.ndarray` | The $n \times p$ data matrix. |
| `checksum` | `str` | SHA-256 hash of the data matrix. |

**Storage**: `data/synthetic/{dataset_id}.npz` (compressed) + `data/synthetic/{dataset_id}.meta.json`.

### 2. PValueCollection
Represents the results of hypothesis tests on a `SyntheticDataset`.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `collection_id` | `str` | UUID linking to `dataset_id`. |
| `test_type` | `str` | "t-test" or "f-test". |
| `p_values` | `np.ndarray` | Array of $p$ p-values. |
| `ks_statistic` | `float` | KS statistic vs Uniform(0,1). |
| `ks_p_value` | `float` | P-value of the KS test. |
| `permutation_ks` | `float` | KS statistic vs permutation reference. |
| `iteration` | `int` | Iteration number (1-1000). |

**Storage**: `data/results/pvalues/{collection_id}.csv`.

### 3. SimulationResult
Aggregated results for a specific configuration ($n, p, \rho, \text{dist}$).

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `config_id` | `str` | Hash of ($n, p, \rho, \text{dist}$). |
| `mean_ks` | `float` | Mean KS statistic across iterations. |
| `std_ks` | `float` | Standard deviation of KS statistic. |
| `ci_lower` | `float` | 95% Bootstrap CI lower bound. |
| `ci_upper` | `float` | 95% Bootstrap CI upper bound. |
| `num_iterations` | `int` | Count of successful iterations. |

**Storage**: `data/results/summary/{config_id}.json`.

## Relationships

- **1-to-Many**: One `SyntheticDataset` generates many `PValueCollection` (one per iteration).
- **Many-to-1**: Many `PValueCollection` (same config) aggregate into one `SimulationResult`.

## Constraints

- **Data Integrity**: `data_matrix` must be checksummed immediately after generation.
- **Immutability**: Once generated, `SyntheticDataset` files are never modified.
- **Size Limit**: No single `data_matrix` > 1 GB (enforced by $p \le 5000, n \le 500$).
