# Data Model: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

## 1. Overview
The pipeline stores four core artifact types, each validated against a JSON/YAML schema in `contracts/`. All files live under `data/results/`.

## 2. Entities

### 2.1 SimulatedDataset
| Field | Type | Description |
|-------|------|-------------|
| `replicate_id` | integer | Unique identifier for the replicate (1‑based). |
| `tau_squared` | number | Injected between‑study variance (ground truth). |
| `true_effect` | number | Fixed true effect size used for generation (`0.5`). |
| `study_effects` | array[number] | Generated effect sizes $y_{i,r}$. |
| `study_se` | array[number] | Corresponding standard errors $\sigma_i$. |
| `study_sizes` | array[integer] | Sample sizes $N_i$ used to derive SEs. |
| `k` | integer | Number of studies in this replicate. |
| `sweep_type` | string (enum: `primary`, `sensitivity`) | Indicates which sweep the replicate belongs to. |

### 2.2 EstimationResult
| Field | Type | Description |
|-------|------|-------------|
| `dataset_id` | integer | Links to `replicate_id` of the source `SimulatedDataset`. |
| `estimator_type` | string (enum: `FixedEffects`, `DerSimonianLaird`, `REML`) | Which estimator was applied. |
| `pooled_effect` | number | Estimated overall effect. |
| `ci_lower` | number | Lower bound of the 95 % confidence interval. |
| `ci_upper` | number | Upper bound of the 95 % confidence interval. |
| `tau_squared_est` | number | Estimated between‑study variance (≥ 0). |
| `i_squared` | number | $I^2$ heterogeneity statistic (0‑[deferred]). |
| `q_statistic` | number | Cochran’s $Q$. |
| `coverage_flag` | boolean | True if `true_effect` lies within `[ci_lower, ci_upper]`. |
| `convergence_warning` | boolean | True only for REML when convergence failed (fallback used). |

All `EstimationResult` records are stored **exclusively** in the JSON‑lines file `data/results/simulation_raw.jsonl` alongside their originating `SimulatedDataset`. No separate CSV file is used, satisfying Principle IV (Single Source of Truth).

### 2.3 AggregatedMetric
| Field | Type | Description |
|-------|------|-------------|
| `tau_squared` | number | The τ² level being summarised. |
| `estimator_type` | string (enum as above) | Estimator whose metrics are aggregated. |
| `sweep_type` | string (enum: `primary`, `sensitivity`) | Sweep provenance. |
| `mean_bias` | number | Mean of `pooled_effect − true_effect`. |
| `coverage_rate` | number | Proportion of replicates with `coverage_flag=True`. |
| `coverage_deviation` | number | `coverage_rate − 0.95`. |
| `coverage_ci_lower` | number | Wilson‑score lower bound for coverage. |
| `coverage_ci_upper` | number | Wilson‑score upper bound for coverage. |
| `binomial_p_value` | number | Exact binomial test p‑value (Bonferroni‑adjusted α = 0.01). |
| `bias_test_p_value` | number | ANOVA or Kruskal‑Wallis p‑value for bias differences across τ² levels. |
| `report_framing` | string | Must be `"associational"` per SC‑005. |

### 2.4 CoverageTest
| Field | Type | Description |
|-------|------|-------------|
| `estimator_type` | string (enum as above) | Estimator evaluated. |
| `tau_squared` | number | τ² level of the test. |
| `p_value` | number | Exact binomial test p‑value (pre‑adjustment). |
| `alpha_used` | number | Nominal α before Bonferroni correction (`0.01`). |
| `test_type` | string | `"binomial"` (fixed for this project). |

The `CoverageTest` objects are stored in `data/results/coverage_tests.json` (one JSON object per line). This artifact is now part of the data model, fulfilling the Single Source of Truth principle.

## 3. File Formats
* **SimulatedDataset & EstimationResult** – stored together as JSON‑lines (`.jsonl`) in `simulation_raw.jsonl`. Each line conforms to its respective schema.  
* **AggregatedMetric** – CSV (`aggregated_metrics.csv`) with column names matching the table above.  
* **CoverageTest** – JSON‑lines (`coverage_tests.json`) matching `contracts/coverage_test.schema.yaml`.  
* **Plots** – PNG files (`coverage_vs_tau2.png`, `mean_bias_vs_tau2.png`).  
* **Report** – Markdown (`report.md`).  

## 4. Validation Strategy
* **Schema enforcement** – `jsonschema` validates each JSON line on write; `pandas` validates CSV columns against `contracts/aggregated_metric.schema.yaml`.  
* **Checksums** – SHA‑256 hashes of every file recorded in `state/project_state.yaml`.  
* **Unit tests** – Verify that generated objects satisfy schemas (`tests/unit/test_generator.py`, `test_estimators.py`).  

---

