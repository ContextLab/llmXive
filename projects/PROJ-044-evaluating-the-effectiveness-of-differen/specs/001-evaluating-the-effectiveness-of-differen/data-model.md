# Data Model: Evaluating the Effectiveness of Differential Privacy in Federated Learning

## Overview
All artifacts conform to JSON‑Schema contracts in `contracts/`. Artifact hashes are recorded in the project state file to satisfy **Principle III (Data Hygiene)** and **Principle IV (Single Source of Truth)**.

### 1. Raw FEMNIST Parquet (Source)
| Field | Type | Description |
|-------|------|-------------|
| `image` | `array<int>` (length = 784) | Flattened grayscale pixel values (0‑255). |
| `label` | `int` (0 – 61) | Class index (digits, lowercase, uppercase). |
| `client_id` | `string` | Original LEAF client identifier (kept for provenance only). |

*Location*: `data/raw/femnist.parquet` (produced by **T011**).

### 2. Client Partition Metadata (Derived)
| Field | Type | Description |
|-------|------|-------------|
| `partition_id` | `string` | `{dataset}_{alpha}_{seed}` (e.g., `femnist_0.1_42`). |
| `client_id` | `int` | Simulated client index (0‑N‑1). |
| `samples` | `list<int>` | Row indices in the raw parquet belonging to the client. |
| `label_dist` | `dict<string,int>` | Per‑label counts for the client. |
| `entropy` | `float` | Empirical label‑entropy (bits). |
| `is_minority` | `bool` | `True` if client falls in the bottom 30 % of entropy **within its partition**. |
| `samples_per_class` | `dict<string,int>` | Auxiliary covariate for collinearity checks. |

*Location*: `data/partitions/partition_femnist_{seed}_{alpha}.json` (**T012**).

### 3. Training Log (Per‑Round CSV)
| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `string` | `{alpha}_{epsilon}_{seed}_{DP|NODP}` (e.g., `0.1_1.0_42_DP`). |
| `dataset` | `string` | `"FEMNIST"`. |
| `alpha` | `float` | Dirichlet concentration. |
| `epsilon` | `string|number` | Target ε or `"inf"` for baseline. |
| `seed` | `int` | Random seed. |
| `round` | `int` | Communication round number. |
| `global_accuracy` | `float` (0‑1) | Test accuracy over the full test set. |
| `majority_accuracy` | `float` (0‑1) | Mean accuracy of majority clients. |
| `minority_accuracy` | `float` (0‑1) | Mean accuracy of minority clients. |
| `delta` | `float` | Fixed privacy δ = 1e‑5. |
| `actual_epsilon` | `float` | Cumulative ε from Moments Accountant. |
| `is_dp` | `bool` | `True` for DP runs, `False` for baseline. |
| `is_time_limited` | `bool` | `True` if early‑stop was triggered. |
| `degradation` | `float` | `accuracy_nonDP - accuracy_DP` (computed post‑hoc). |

*Aggregated by*: **T018c** → `results/raw_logs.csv`. This file is the **Single Source of Truth** for all downstream analysis.

### 4. Filtered Datasets
- **Utility‑Collapse Filter** (`T035`): removes rows where `global_accuracy < 1/62 ≈ 0.01613`. Output: `results/filtered_data.csv`.  
- **Time‑Limit Filter** (`T025`): removes rows with `is_time_limited=True`. Output: `results/filtered_time.csv`.

### 5. Final Statistics & Summary
| Field | Type | Description |
|-------|------|-------------|
| `alpha` | `float` | Dirichlet concentration. |
| `epsilon` | `string|number` | Privacy budget (`"inf"` or numeric). |
| `test_name` | `string` | `"paired_t_test"` or `"lmm_minor_vs_major"` etc. |
| `statistic` | `float` | t‑value or LMM coefficient. |
| `p_value` | `float` | Raw p‑value (Bonferroni‑adjusted). |
| `significant` | `bool` | `p_value < 0.05` after correction. |
| `effect_size` | `float` | Cohen’s d (t‑tests) or standardized LMM coefficient. |

*Location*: `results/final_stats.csv` (**T024a**, **T024b**).

### 6. Summary & Validation Artifacts
- `results/summary.csv` – per (α, ε) mean accuracies, degradation, and `rounds_to_80`.  
- `results/validation_report.md` – checksum verification, seed completeness, and any excluded runs.  
- `results/p_values_by_seed.json` – mapping seed → raw p‑values for auditability.

### Data Flow Diagram (conceptual)
1. **Download** → `data/raw/femnist.parquet` (**T011**)  
2. **Partition** → `data/partitions/...json` (**T012**)  
3. **Training** (DP & non‑DP) → `results/raw_logs.csv` (**T018c**)  
4. **Filtering** → `results/filtered_data.csv`, `results/filtered_time.csv` (**T035**, **T025**)  
5. **Statistical Tests** → `results/final_stats.csv` (**T024a**, **T024b**)  
6. **Plotting** → `figures/*.png` (**T026**)  
7. **Aggregation** → `results/summary.csv`, `validation_report.md`, `p_values_by_seed.json` (**T028**)

All files are version‑controlled; any modification updates the hash map in `state/projects/PROJ-044‑...yaml`.

---
