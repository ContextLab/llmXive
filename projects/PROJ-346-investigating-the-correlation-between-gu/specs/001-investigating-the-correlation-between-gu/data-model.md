# Data Model: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility

## Entities

### MicrobialTaxa
Represents filtered microbial taxa from 16S sequencing data.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `sample_id` | string | Unique identifier for the sample | PK, non-null |
| `taxon_name` | string | Taxonomic name (e.g., "Bacteroides_fragilis") | non-null |
| `abundance` | float | Relative abundance or CLR-transformed value | ≥ 0 (raw), real (CLR) |
| `read_count` | int | Total reads for the sample (pre-filter) | ≥ 10,000 (post-filter) |
| `mean_abundance` | float | Mean abundance across all samples | ≥ 0.001 |

### CognitiveScore
Represents normalized cognitive flexibility task scores.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `participant_id` | string | Unique identifier for the participant | PK, non-null |
| `task_type` | string | Type of task (e.g., "set_shifting", "reversal_learning", "composite") | non-null |
| `raw_score` | float | Raw task score | non-null |
| `z_score` | float | Z-scored cognitive score | non-null |
| `age` | int | Participant age | ≥ 18 |
| `sex` | string | "M" or "F" | non-null |
| `bmi` | float | Body Mass Index | > 0 |

### DemographicCovariates
Represents participant metadata for regression control.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `participant_id` | string | Foreign key to CognitiveScore | FK, non-null |
| `age` | int | Age | ≥ 18 |
| `sex` | string | "M" or "F" | non-null |
| `bmi` | float | BMI | > 0 |

### CorrelationResult
Represents the output of the Spearman correlation analysis.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `taxon_name` | string | Microbial taxon | non-null |
| `r_value` | float | Spearman correlation coefficient | [-1, 1] |
| `p_value` | float | Raw p-value | [0, 1] |
| `q_value` | float | BH-FDR corrected p-value | [0, 1] |
| `significant` | bool | True if q < 0.05 | non-null |

### RegressionResult
Represents the output of the LASSO/Elastic Net regression.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `predictor` | string | Taxon name or covariate | non-null |
| `beta_coef` | float | Regression coefficient | non-null |
| `std_err` | float | Standard error | ≥ 0 |
| `p_value` | float | P-value | [0, 1] |
| `selected` | bool | True if predictor selected by LASSO | non-null |

### DataGapReport
Represents the output of the FR-008 fallback path when paired data is not found.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `status` | string | "Data Linkage Failure" | non-null |
| `reason` | string | Explanation of the data gap | non-null |
| `available_datasets` | list | List of dataset names used | non-null |
| `missing_variables` | list | List of variables not found in paired context | non-null |
| `success_criterion_status` | object | Status of SC-001, SC-004, etc. | non-null |

## Data Flow

1.  **Ingest**: `raw/microbiome_raw.parquet`, `raw/cognitive_raw.parquet`
2.  **Preprocess**: `processed/microbiome_filtered.parquet`, `processed/cognitive_imputed.parquet`
3.  **Merge**: `processed/merged_dataset.parquet` (if possible) OR `qc/linkage_failure_log.json`
4.  **Analyze**: `results/correlation_matrix.csv`, `results/regression_coefficients.csv` (if merged)
5.  **Gap Report**: `data/gap_report.json` (if merge failed)
6.  **Visualize**: `results/heatmap.png`, `results/forest_plot.png` (if merged)

## Constraints & Validation

*   **Microbiome**: `read_count` ≥ 10,000; `mean_abundance` ≥ 0.001.
*   **Cognitive**: `z_score` computed; missing values imputed via MICE.
*   **Correlation**: `q_value` computed via BH-FDR.
*   **Regression**: Only run if merged dataset exists.
*   **Gap Report**: Generated if merged dataset does not exist.
