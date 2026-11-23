# Data Model: Evaluating the Effectiveness of Differential Privacy in Federated Learning

## Overview
All artifacts conform to JSON‑Schema contracts in `contracts/` where schemas exist. Artifact hashes are recorded in the project state file to satisfy **Principle III (Data Hygiene)** and **Principle IV (Single Source of Truth)**.

### 1. Raw FEMNIST Parquet (Source)
| Field | Type | Description |
|-------|------|-------------|
| `image` | `array<int>` (length = 784) | Flattened grayscale pixel values (0‑255). |
| `label` | `int` (0‑61) | Class label (digits + letters). |
| `client_id` | `string` | Original LEAF client identifier (kept for provenance). |

*Location*: `data/raw/femnist_train.parquet` and `data/raw/femnist_test.parquet` (produced by **T001**).

### 2. Client Partition Metadata (Derived)
| Field | Type | Description |
|-------|------|-------------|
| `partition_id` | `string` | `{dataset}_{alpha}_{seed}` (e.g., `femnist_0.1_42`). |
| `client_id` | `int` | Simulated client index (0‑N‑1). |
| `samples` | `list<int>` | Row indices in the raw parquet belonging to the client. |
| `label_dist` | `dict<string,int>` | Per‑label counts for the client. |
| `entropy` | `float` | Empirical label‑entropy (bits). |
| `is_minority` | `bool` | `True` if client falls in the **global bottom quartile** of entropy (computed once on the full training set). |
| `samples_per_class` | `dict<string,int>` | Auxiliary covariate for collinearity checks. |

*Location*: `data/partitions/partition_femnist_{seed}_{alpha}.json` (**T002**). Each file’s SHA‑256 is recorded for reproducibility (SC‑001).

### 3. Training Log (Per‑Round CSV)
| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `string` | Unique identifier (e.g., `0.1_1.0_42_DP`). |
| `dataset` | `string` | `"FEMNIST"` |
| `alpha` | `number` | Dirichlet concentration parameter. |
| `epsilon` | `anyOf` (number, `"inf"`) | Target privacy budget (ε) or `"inf"` for baseline. |
| `seed` | `integer` | Random seed. |
| `round` | `integer` | Communication round number. |
| `global_accuracy` | `number` (0‑1) | Test accuracy over the full test set. |
| `majority_accuracy` | `number` (0‑1) | Mean accuracy of majority clients. |
| `minority_accuracy` | `number` (0‑1) | Mean accuracy of minority clients. |
| `delta` | `number` | Privacy parameter δ = 1e‑5. |
| `actual_epsilon` | `number` | Cumulative ε from Moments Accountant. |
| `is_dp` | `boolean` | True for DP runs, False for baseline. |
| `is_time_limited` | `boolean` | True if early‑stop triggered by time budget. |
| `utility_collapse` | `boolean` | True if `global_accuracy < 1/62` (random‑guess threshold). |
| `rounds_to_80` | `integer` | First round where `global_accuracy ≥ 0.80`. |
| `matched_rounds` | `integer` | Minimum number of rounds completed between DP and baseline for this seed/α pair. |
| `censoring` | `boolean` | Mirrors `is_time_limited`; used for survival analysis. |

*Aggregated by*: **T006** → `results/raw_logs.csv`. This file is the **Single Source of Truth** for all downstream analysis (Principle IV).

### 4. Filtered Datasets
- **Utility‑Collapse Flag** (`utility_collapse`) and **Time‑Limit Flag** (`is_time_limited`) are retained; no rows are dropped (FR‑007, SC‑009).

### 5. Final Statistics & Summary
| Field | Type | Description |
|-------|------|-------------|
| `alpha` | `float` | Dirichlet concentration. |
| `epsilon` | `anyOf` (number, `"inf"`) | Privacy budget. |
| `test_name` | `string` | `"paired_t_test"` / `"wilcoxon_test"` / `"lmm_minor_vs_major"` etc. |
| `statistic` | `float` | t‑value, rank‑biserial, or LMM coefficient. |
| `p_value` | `float` | Raw p‑value (Bonferroni‑adjusted reported separately). |
| `significant` | `boolean` | `p_value < 0.05` after correction. |
| `effect_size` | `float` | Cohen’s d (t‑tests) or rank‑biserial (Wilcoxon) or standardized LMM coefficient. |
| `interaction_term` | `string` | Name of any interaction term reported (e.g., `"is_minority:alpha"`). |
| `mean_accuracy` | `float` | Mean final global accuracy across seeds. |
| `std_accuracy` | `float` | Standard deviation of final global accuracy. |
| `degradation_mean` | `float` | Mean DP‑vs‑non‑DP degradation across seeds. |
| `collapsed_count` | `integer` | Number of runs with `utility_collapse=True`. |
| `time_limited_count` | `integer` | Number of runs with `is_time_limited=True`. |
| `minority_gap` | `float` | Mean difference between minority and majority accuracy. |
| `power_effect_size` | `float` | Minimum detectable effect size for the achieved seed count (documented per FR‑009). |
| `minority_entropy_correlation` | `float` | Pearson r between client entropy and α (diagnostic). |

*Location*: `results/final_stats.csv` (**T008**, **T008b**).

### 6. Summary & Validation Artifacts
- `results/summary.csv` – per (α, ε) mean/std accuracies, degradation, counts of flagged runs, and power metadata.  
- `results/validation_report.md` – checksum verification, seed completeness, confirmation of Shakespeare‑exclusion verification, minority‑definition correlation diagnostic, and any flagged‑run statistics.  
- `results/p_values_by_seed.json` – mapping seed → raw p‑values for auditability.

## Data Flow Diagram (conceptual)
1. **Download** → `data/raw/femnist_*.parquet` (**T001**)  
2. **Global Entropy & Partition** → `data/partitions/...json` (**T002**)  
3. **Training** (DP & non‑DP) → `results/raw_logs.csv` (**T006**)  
4. **Analysis** → `results/final_stats.csv` (**T008**, **T008b**)  
5. **Plotting** → `figures/*.png` (**T009b**)  
6. **Aggregation** → `results/summary.csv`, `validation_report.md`, `p_values_by_seed.json` (**T009c**)  

All files are version‑controlled; any modification updates the hash map in `state/projects/PROJ-044‑...yaml`.

---

