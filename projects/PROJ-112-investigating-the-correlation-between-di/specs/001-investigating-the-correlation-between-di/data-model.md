# Data Model: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Entity Relationship Overview

The system processes three primary data states:
1.  **Raw Data**: Downloaded 16S tables and metadata (unstructured/semi-structured).
2.  **Harmonized Data**: Unified CSV/TSV with consistent units, filtered samples, and imputed covariates.
3.  **Analysis Data**: CLR-transformed taxon matrix and associated metadata.
4.  **Results Data**: Association tables, differential abundance results, and replication flags.

## Data Flow

```mermaid
graph TD
    A[Raw AGP/UKBB] -->|Download & Parse| B(Raw Tables)
    B -->|Filter & Harmonize| C[Harmonized CSV]
    C -->|Exclude >20% Missing| D[Cleaned Data]
    D -->|Impute Remaining| E[Imputed Data]
    E -->|CLR Transform (Bayesian)| F[Analysis Matrix]
    F -->|Spearman ρ (Primary)| G[Association Results]
    F -->|ANCOM-II/DESeq2| H[Differential Results]
    G & H -->|Cross-Cohort Check (Significance)| I[Final Report]
```

## Data Definitions

### 1. Harmonized Sample Record
*Input to analysis phase*

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `sample_id` | string | Unique identifier | AGP/UKBB ID |
| `fiber_intake_g` | float | Daily fiber intake in grams | Metadata (harmonized) |
| `age` | float | Age in years | Metadata (imputed) |
| `sex` | string | 'M' or 'F' | Metadata (imputed) |
| `bmi` | float | Body Mass Index | Metadata (imputed) |
| `antibiotic_use` | string | 'Yes'/'No' | Metadata (imputed) |
| `read_depth` | int | Total sequencing reads | 16S Table |
| `cohort` | string | 'AGP' or 'UKBB' | Source label |

### 2. Taxon Abundance Matrix
*Compositional data*

| Field | Type | Description |
| :--- | :--- | :--- |
| `sample_id` | string | Foreign key to Harmonized Sample |
| `taxon_id` | string | Taxonomic identifier (e.g., Genus_Species) |
| `relative_abundance` | float | Raw relative abundance (0-1) |
| `clr_value` | float | Centered Log-Ratio transformed value (using Bayesian replacement) |

### 3. Association Result
*Output of Spearman ρ Analysis*

| Field | Type | Description |
| :--- | :--- | :--- |
| `taxon_id` | string | Taxon identifier |
| `spearman_rho` | float | **Spearman correlation coefficient**. **Rounded to 3 decimal places**. |
| `spearman_se` | float | Standard Error of Spearman ρ (via Fisher Z). **Rounded to 3 decimal places**. |
| `p_value` | float | Raw p-value |
| `q_value` | float | FDR-adjusted q-value |
| `significant` | bool | `q_value < 0.05` |
| `beta_coefficient` | float | **Beta coefficient** (Linear Regression) on CLR data. Rounded to 3 decimal places. (Secondary metric). |

### 4. Differential Abundance Result
*Output of ANCOM-II / DESeq2*

| Field | Type | Description |
| :--- | :--- | :--- |
| `taxon_id` | string | Taxon identifier |
| `method` | string | 'ANCOM-II' or 'DESeq2' |
| `q_value` | float | Adjusted p-value |
| `effect_size` | float | Log-fold change or W-statistic |
| `direction` | string | 'Positive' or 'Negative' |
| `replicated` | bool | **True** only if significant (q < 0.05) in **BOTH** cohorts AND direction matches. |

## Constraints & Validation

- **Fiber Intake**: Must be `0 <= value <= 200`.
- **Read Depth**: Must be `>= 5000`.
- **Missing Covariates**: Samples with `>20%` missing covariates are **excluded** before imputation.
- **CLR**: `clr_value` is undefined for zero counts without replacement; **Bayesian replacement** must be applied.
- **Replication**: `replicated` flag is only `True` if `q_value < 0.05` in **both** cohorts and `direction` matches.
- **Thresholds**: High-fiber group defined as **Top 25th percentile**; Low-fiber as **Bottom 25th percentile** for primary analysis. Absolute thresholds (>30g/<15g) are secondary only.
