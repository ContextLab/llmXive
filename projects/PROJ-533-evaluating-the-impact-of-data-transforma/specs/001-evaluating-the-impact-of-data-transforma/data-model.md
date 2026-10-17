# Data Model: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Entity Relationship Overview
The data model captures the full lifecycle from raw dataset acquisition to final aggregated statistics. Seven primary entities are defined.

### Entity Definitions

| Entity | Primary Key | Key Attributes | Relationships |
|--------|-------------|----------------|---------------|
| **Dataset** | `dataset_id` (hash of URL) | `source_url`, `filename`, `checksum_sha256`, `sample_size`, `num_continuous_vars`, `shapiro_wilk_p`, `skewness`, `kurtosis`, `missing_pct`, `status`, `filter_reason`, `exclusion_details` | 1‑many **Transformation**, 1‑many **SimulatedDataset** |
| **Transformation** | `transformation_id` | `dataset_id` (FK), `variable_name`, `method` (`box_cox`, `yeo_johnson`, `rank_based`), `lambda_param`, `intervention_log`, `status` | 1‑many **TestResult** |
| **SimulatedDataset** | `sim_id` | `source_dataset_id` (FK), `effect_size` (null for null simulations), `skewness`, `kurtosis`, `n_samples`, `seed_used` | 1‑many **Transformation** (applied to each simulated column) |
| **TestResult** | `result_id` | `transformation_id` (FK), `test_type` (`t_test`, `anova`), `condition` (`null`, `alternative`), `effect_size`, `p_value`, `is_significant`, `seed_used`, `iteration` | — |
| **AggregatedResult** | `agg_id` | `transformation`, `test_type`, `metric` (`type1_error`, `power`), `mean_value`, `ci_lower`, `ci_upper`, `ci_half_width`, `validation_status`, `n_datasets`, `n_iterations` | — |
| **FriedmanResult** | `friedman_id` | `test_type`, `transformation_comparison` (list of methods compared), `statistic`, `p_value`, `significant`, `posthoc_pairs` (list of pairwise comparisons with Bonferroni‑adjusted p‑values) | — |
| **SensitivityResult** | `sens_id` | `transformation`, `test_type`, `alpha`, `error_rate`, `n_iterations` | — |

## Data Flow
1. **Ingestion** – `Dataset` rows created from `data/datasets.csv`.  
2. **Filtering** – `status` updated; excluded rows logged in `data/exclusions.csv`.  
3. **Simulation** – For each retained `Dataset`, one or more `SimulatedDataset` rows are generated (null & alternative).  
4. **Transformation** – Each `SimulatedDataset` column receives three `Transformation` rows.  
5. **Testing** – `TestResult` rows created for every (`Transformation`, `test_type`, `condition`, `iteration`) combination.  
6. **Aggregation** – `AggregatedResult` rows computed from `TestResult`.  
7. **Inference** – `FriedmanResult` rows produced by the Friedman test and Bonferroni post‑hoc analysis.  
8. **Sensitivity** – `SensitivityResult` rows derived from `TestResult` across α values.

## Storage Strategy
- **Raw Data**: `data/raw/` (CSV/Parquet) – immutable.  
- **Metadata**: `data/datasets.csv`, `data/checksums.csv`.  
- **Logs**: `data/imputation_log.csv`, `data/exclusions.csv`.  
- **Simulated Data**: `data/simulated/` (Parquet).  
- **Results**: CSV files under `results/`.  
- **State**: `state/projects/PROJ-533-evaluating-the-impact-of-data-transforma.yaml` (artifact hashes, checkpoint).  

All files conform to the JSON‑Schema contracts in `contracts/`.

---

