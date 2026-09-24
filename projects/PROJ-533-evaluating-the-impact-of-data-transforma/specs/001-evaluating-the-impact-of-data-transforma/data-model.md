# Data Model: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Entity Relationship Overview

The data model consists of six primary entities: `Dataset`, `Transformation`, `TestResult`, `AggregatedResult`, `SensitivityResult`, and `SimulatedDataset`. These entities capture the lifecycle of data from acquisition to final statistical inference.

### Entity Definitions

#### 1. Dataset
Represents a public data source from UCI/OpenML.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `dataset_id` | String | Unique identifier (hash of URL or name) | Primary Key |
| `source_url` | String | Canonical download URL | Not Null, Verified |
| `filename` | String | Local file path | Not Null |
| `checksum_sha256` | String | SHA-256 hash of raw file | Not Null |
| `sample_size` | Integer | Number of rows (N) | N ≥ 30 |
| `num_continuous_vars` | Integer | Count of continuous variables | ≥ 1 |
| `shapiro_wilk_p` | Float | Minimum p-value across variables | p < 0.05 (if retained) |
| `skewness` | Float | Average skewness across variables | |
| `kurtosis` | Float | Average kurtosis across variables | |
| `missing_pct` | Float | Percentage of missing values | < 10% |
| `status` | Enum | `downloaded`, `filtered_out`, `processed` | |
| `filter_reason` | Enum | `normal`, `small_n`, `missing_too_high`, `no_group` | Only if filtered_out |
| `exclusion_details` | String | Specific reason details | Nullable |

#### 2. Transformation
Represents the application of a transformation method to a variable.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `transformation_id` | String | Unique ID | Primary Key |
| `dataset_id` | String | Reference to Dataset | Foreign Key |
| `variable_name` | String | Name of the continuous variable | Not Null |
| `method` | Enum | `box_cox`, `yeo_johnson`, `rank_based` | Not Null |
| `lambda_param` | Float | Optimized λ (for Box-Cox/Yeo-Johnson) | Null if rank_based |
| `intervention_log` | String | Log of interventions (e.g., log-shift) | Nullable |
| `status` | Enum | `success`, `failed`, `skipped` | |

#### 3. TestResult
Represents the outcome of a statistical test under a specific condition.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `result_id` | String | Unique ID | Primary Key |
| `transformation_id` | String | Reference to Transformation | Foreign Key |
| `test_type` | Enum | `t_test`, `anova` | Not Null |
| `condition` | Enum | `null`, `alternative` | Not Null |
| `effect_size` | Float | Known effect size (for simulated data) | Null for real data |
| `p_value` | Float | P-value from test | 0 ≤ p ≤ 1 |
| `is_significant` | Boolean | `p_value < alpha` | Derived |
| `seed_used` | Integer | Random seed for this run | Not Null |
| `iteration` | Integer | Iteration number (for null simulation) | ≥ 1 |

#### 4. SimulatedDataset
Represents a generated dataset with known ground truth.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `sim_id` | String | Unique ID | Primary Key |
| `source_dataset_id` | String | Reference to real dataset (for shape) | Foreign Key |
| `effect_size` | Float | True Cohen's d | Not Null |
| `skewness` | Float | Skewness of generated data | |
| `kurtosis` | Float | Kurtosis of generated data | |
| `n_samples` | Integer | Number of samples | ≥ 30 |
| `seed_used` | Integer | Random seed | Not Null |

#### 5. AggregatedResult
Represents the summary statistics across datasets and iterations.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `agg_id` | String | Unique ID | Primary Key |
| `transformation` | Enum | Method used | Not Null |
| `test_type` | Enum | Test used | Not Null |
| `metric` | Enum | `type1_error`, `power` | Not Null |
| `mean_value` | Float | Mean error/power rate | 0 ≤ val ≤ 1 |
| `ci_lower` | Float | Lower bound of bootstrap CI | 0 ≤ val ≤ 1 |
| `ci_upper` | Float | Upper bound of bootstrap CI | 0 ≤ val ≤ 1 |
| `ci_half_width` | Float | Half-width of CI | |
| `validation_status` | Enum | `pass`, `fail` (if >0.02) | |
| `n_datasets` | Integer | Number of datasets contributing | ≥ 1 |
| `n_iterations` | Integer | Total iterations | ≥ 1 |

#### 6. SensitivityResult
Represents the results of the alpha-sweep analysis.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `sens_id` | String | Unique ID | Primary Key |
| `transformation` | Enum | Method used | Not Null |
| `test_type` | Enum | Test used | Not Null |
| `alpha` | Float | Significance threshold | |
| `error_rate` | Float | Observed error rate at alpha | |
| `n_iterations` | Integer | Total iterations | ≥ 1 |

## Data Flow

1.  **Ingestion**: `Dataset` entities are created from `data/datasets.csv`.
2.  **Filtering**: `Dataset` status updated to `filtered_out` or `processed` based on Shapiro-Wilk, N, skew/kurtosis, and missing value criteria.
3.  **Simulation**: `SimulatedDataset` entities created for null and alternative conditions, matching real-world shapes.
4.  **Transformation**: `Transformation` entities created for each `SimulatedDataset` x `Method` combination.
5.  **Testing**: `TestResult` entities created for each `Transformation` x `Test` x `Iteration` combination.
6.  **Aggregation**: `AggregatedResult` entities computed from `TestResult` table.
7.  **Sensitivity**: `SensitivityResult` entities computed from `TestResult` table across alpha values.

## Storage Strategy

-   **Raw Data**: Stored in `data/raw/` (Parquet/CSV).
-   **Metadata**: Stored in `data/datasets.csv`, `data/checksums.csv`.
-   **Logs**: `data/imputation_log.csv`, `data/exclusions.csv` (schema: `dataset_id, reason, details`).
-   **Results**: `results/type1_error_results.csv`, `results/power_results.csv`, `results/aggregated_results.csv`, `results/sensitivity_results.csv`.
-   **State**: `state/projects/PROJ-533-evaluating-the-impact-of-data-transforma.yaml` (artifact hashes).
