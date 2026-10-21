# Data Model: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Entity Relationship Overview
Eight primary entities capture the full lifecycle from raw acquisition to final inference.

| Entity | Primary Key | Key Attributes | Relationships |
|--------|-------------|----------------|---------------|
| **Dataset** | `dataset_id` (hash of source URL) | `source_url`, `filename`, `checksum_sha256`, `sample_size`, `num_continuous_vars`, `shapiro_wilk_p`, `skewness`, `kurtosis`, `missing_pct`, `status`, `filter_reason`, `exclusion_details` | 1‑many **Transformation**, 1‑many **SimulatedDataset**, 1‑many **ImputationLog** |
| **Transformation** | `transformation_id` | `dataset_id` (FK), `variable_name`, `method` (`box_cox`, `yeo_johnson`, `rank_inverse_normal`, `baseline`), `lambda_param`, `intervention_log`, `status` | 1‑many **TestResult** |
| **SimulatedDataset** | `sim_id` | `source_dataset_id` (FK), `effect_size` (null for null sims), `skewness`, `kurtosis`, `n_samples`, `seed_used` | **Per‑dataset shape matching**: `skewness` and `kurtosis` are derived **from the source real dataset**, preserving its distributional characteristics. |
| **TestResult** | `result_id` | `transformation_id` (FK), `test_type` (`t_test`, `anova`), `condition` (`null`, `alternative`), `effect_size`, `p_value`, `is_significant`, `seed_used`, `iteration` | — |
| **AggregatedResult** | `agg_id` | `transformation`, `test_type`, `metric` (`type1_error`, `power`), `mean_value`, `ci_lower`, `ci_upper`, `ci_half_width`, `n_datasets`, `n_iterations` | — |
| **FriedmanResult** | `friedman_id` | `test_type`, `transformation_comparison` (list), `statistic`, `p_value`, `significant`, `posthoc_pairs` (list of `{pair, p_adj}`) | — |
| **SensitivityResult** | `sens_id` | `transformation`, `test_type`, `alpha`, `error_rate`, `n_iterations` | — |
| **ImputationLog** | `log_id` | `dataset_id` (FK), `variable_name`, `method` (`mean` or `median`), `imputed_pct`, `timestamp` | — |

## Data Flow
1. **Ingestion** – `Dataset` rows created from `data/datasets.csv`.  
2. **Filtering** – `status` updated; exclusions logged.  
3. **Imputation** – `ImputationLog` entries recorded for each variable; imputation method (mean/median) stored.  
4. **Simulation** – For each retained `Dataset`, generate one or more `SimulatedDataset` rows (null & alternative) **using that dataset’s own skewness/kurtosis** (per‑dataset shape matching).  
5. **Transformation** – Each `SimulatedDataset` and each real `Dataset` receives three `Transformation` rows (plus a `baseline` row for the untransformed data).  
6. **Testing** – `TestResult` rows produced for every (`Transformation`, `test_type`, `condition`, `iteration`).  
7. **Aggregation** – `AggregatedResult` rows computed from `TestResult`.  
8. **Inference** – `FriedmanResult` rows produced via Friedman test and Bonferroni‑corrected post‑hoc.  
9. **Sensitivity** – `SensitivityResult` rows derived from varying α.  
10. **Imputation Sensitivity** – Results from the mean‑imputation run and the median‑imputation run are compared; differences are logged in `ImputationLog` and reported in the final analysis.

All files conform to the JSON‑Schema contracts in `contracts/`.

---



