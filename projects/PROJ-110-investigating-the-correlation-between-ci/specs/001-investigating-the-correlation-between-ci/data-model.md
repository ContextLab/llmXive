# Data Model: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## Overview

This document defines the data structures used throughout the pipeline. The model is designed to support the classification of Metabolic Syndrome, differential expression analysis, predictive modeling, correlation analysis, and sensitivity analysis.

## Key Entities

### 1. Donor (Sample)
Represents a human subject sample from the GTEx dataset.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `sample_id` | string | Unique GTEx sample identifier. | GTEx Phenotype |
| `donor_id` | string | Unique donor identifier (may link multiple tissues). | GTEx Phenotype |
| `age` | int | Age of donor at death. | GTEx Phenotype |
| `sex` | string | 'M' or 'F'. | GTEx Phenotype |
| `tissue` | string | Tissue source (e.g., 'Liver', 'Adipose'). | GTEx Phenotype |
| `bmi` | float | Body Mass Index (kg/m²). | GTEx Phenotype |
| `glucose` | float | Fasting glucose (mg/dL). | GTEx Phenotype |
| `systolic_bp` | float | Systolic blood pressure (mmHg). | GTEx Phenotype |
| `diastolic_bp` | float | Diastolic blood pressure (mmHg). | GTEx Phenotype |
| `triglycerides` | float | Triglycerides (mg/dL). | GTEx Phenotype |
| `hdl` | float | HDL cholesterol (mg/dL). | GTEx Phenotype |
| `metabolic_status` | string | 'MetS' or 'Control'. | Derived (ATP-III) |
| `criteria_count` | int | Number of ATP-III criteria met (0-5). | Derived |

### 2. GeneExpression
Represents the transcript abundance for a specific gene in a specific sample.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `sample_id` | string | FK to Donor. | GTEx RNA-seq |
| `gene_symbol` | string | Gene symbol (e.g., 'PER1', 'BMAL1'). | GTEx RNA-seq |
| `tpm` | float | Transcripts Per Million (raw). | GTEx RNA-seq |
| `log_tpm` | float | Log10(TPM + 1) transformed value. | Derived |

### 3. AnalysisResult (Differential Expression)
Stores the output of statistical tests.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `gene_symbol` | string | Gene tested. |
| `tissue` | string | Tissue type. |
| `test_statistic` | float | Wilcoxon W or U statistic. |
| `raw_p_value` | float | Uncorrected p-value. |
| `adj_p_value` | float | Benjamini-Hochberg adjusted p-value. |
| `effect_size` | float | Rank-biserial correlation or similar. |
| `significant` | bool | True if `adj_p_value` < 0.05. |

### 4. CorrelationResult
Stores the output of correlation analysis (FR-007).

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `gene_symbol` | string | Gene tested. |
| `trait` | string | Trait name (e.g., 'BMI', 'Glucose'). |
| `correlation_method` | string | 'Spearman' or 'Pearson'. |
| `correlation_coefficient` | float | r value. |
| `p_value` | float | Raw p-value. |
| `adj_p_value` | float | FDR adjusted p-value (if applicable). |
| `significant` | bool | True if `adj_p_value` < 0.05. |

### 5. SensitivityAnalysisResult
Stores the output of sensitivity analysis (SC-005).

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `threshold_variant` | string | Description of threshold variation (e.g., "BMI ±5%"). |
| `baseline_metS_count` | int | Number of MetS cases in baseline. |
| `variant_metS_count` | int | Number of MetS cases in variant. |
| `reclassification_rate` | float | % of samples reclassified. |

## Data Flow

1. **Raw Input:** GTEx Phenotype (CSV/TSV) + GTEx RNA-seq TPM (Matrix).
2. **Cleaning:**
   - Filter rows where any of the 5 clinical variables are missing/null/invalid.
   - Apply log transformation: `log_tpm = log10(tpm + 1)`.
   - **Filter Genes**: Keep only core circadian genes.
3. **Classification:**
   - Apply ATP-III rules to `Donor` table to generate `metabolic_status` and `criteria_count`.
   - Exclude samples with missing data (handled in cleaning).
4. **Aggregation:**
   - Merge `Donor` and `GeneExpression` on `sample_id`.
5. **Analysis:**
   - **DE**: Group by `tissue`, run Wilcoxon tests, apply FDR.
   - **Model**: Fit global Logistic Regression with 'tissue' covariate.
   - **Correlation**: Compute correlations for all genes and traits.
   - **Sensitivity**: Re-run classification with varied thresholds.
6. **Output:** Write results to `data/processed/` in schema-defined formats.