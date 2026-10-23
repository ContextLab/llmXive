# Data Model: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Entity Relationship Overview
| Entity | Primary Key | Key Attributes | Relationships |
|--------|-------------|----------------|---------------|
| **Dataset** | `dataset_id` (hash of source URL) | `source_url`, `filename`, `checksum_sha256`, `sample_size`, `num_continuous_vars`, `shapiro_wilk_p`, `skewness`, `kurtosis`, `missing_pct`, `status`, `filter_reason`, `exclusion_details` | 1‑many **Transformation**, 1‑many **SimulatedDataset**, 1‑many **ImputationLog** |
| **Transformation** | `transformation_id` | `dataset_id` (FK), `variable_name`, `method` (`baseline`, `box_cox`, `yeo_johnson`, `rank_inverse_normal`), `lambda_param`, `intervention_log`, `status` | 1‑many **TestResult** |
| **SimulatedDataset** | `sim_id` | `source_dataset_id` (FK), `effect_size` (null for null sims), `skewness`, `kurtosis`, `n_samples`, `seed_used` | Used by **Transformation** (baseline + three transformed versions) |
| **TestResult** | `result_id` | `transformation_id` (FK), `test_type` (`t_test`, `anova`), `condition` (`null`, `alternative`), `effect_size`, `p_value`, `is_significant`, `seed_used`, `iteration` | — |
| **AggregatedResult** | `agg_id` | `transformation`, `test_type`, `metric` (`type1_error`, `power`), `mean_value`, `ci_lower`, `ci_upper`, `ci_half_width`, `n_datasets`, `n_iterations` | — |
| **FriedmanResult** | `friedman_id` | `test_type`, `transformation_comparison` (list), `statistic`, `p_value`, `significant`, `posthoc_pairs` (list of `{pair, p_adj}`) | — |
| **SensitivityResult** | `sens_id` | `transformation`, `test_type`, `alpha`, `error_rate`, `n_iterations` | — |
| **ImputationLog** | `log_id` | `dataset_id` (FK), `variable_name`, `method` (`mean`/`median`), `imputed_pct`, `timestamp` | — |

## Data Flow
1. **Ingestion** – `Dataset` rows created from `data/datasets.csv`.  
2. **Filtering** – `status` updated; exclusions logged.  
3. **Imputation** – `ImputationLog` entries recorded; missing values filled.  
4. **Simulation (null & power)** – For each retained `Dataset`, create `SimulatedDataset` rows preserving that dataset’s skewness/kurtosis.  
5. **Transformation** – Each `Dataset` and each `SimulatedDataset` receives four `Transformation` rows (baseline + three methods).  
6. **Testing** – `TestResult` rows generated for every (`Transformation`, `test_type`, `condition`, `iteration`).  
7. **Aggregation** – `AggregatedResult` rows computed from `TestResult`.  
8. **Inference** – `FriedmanResult` and `SensitivityResult` rows produced.  
9. **Reporting** – Tables/figures reference the corresponding rows; all contracts validated against the schemas in `contracts/`.  

All files conform to the JSON‑Schema contracts listed under `contracts/`.

---
