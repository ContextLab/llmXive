# Data Model: Virtual Reality Exposure Therapy Meta-Analysis

## Overview

This document defines the data structures for the meta-analysis pipeline. All data flows through the system in CSV or JSON format, validated against the schemas defined in `contracts/`.

## Entity Definitions

### 1. Study (Raw & Filtered)
Represents a single RCT record. This entity exists in `data/raw` (unfiltered) and `data/processed` (filtered).

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `study_id` | string | Unique identifier (e.g., DOI or custom ID) | CSV Input |
| `title` | string | Full title of the study | CSV Input |
| `year` | integer | Publication year | CSV Input |
| `population_type` | string | Anxiety subtype (e.g., "GAD", "PTSD", "Social Anxiety") | CSV Input |
| `hardware_type` | string | VR hardware used (e.g., "Headset", "CAVE", "Unknown") | CSV Input |
| `n_treatment` | integer | Sample size of the intervention group | CSV Input |
| `mean_treatment_pre` | float | Pre-intervention mean (Treatment) | CSV Input |
| `mean_treatment_post` | float | Post-intervention mean (Treatment) | CSV Input |
| `sd_treatment_pre` | float | Pre-intervention SD (Treatment) | CSV Input |
| `sd_treatment_post` | float | Post-intervention SD (Treatment) | CSV Input |
| `n_control` | integer | Sample size of the control group | CSV Input |
| `mean_control_pre` | float | Pre-intervention mean (Control) | CSV Input |
| `mean_control_post` | float | Post-intervention mean (Control) | CSV Input |
| `sd_control_pre` | float | Pre-intervention SD (Control) | CSV Input |
| `sd_control_post` | float | Post-intervention SD (Control) | CSV Input |
| `outcome_measure` | string | Name of the anxiety scale (e.g., "STAI", "BAI") | CSV Input |
| `exclusion_reason` | string | Reason for exclusion (if any) | Derived |

### 2. EffectSize (Derived)
Computed for each included study.

| Field | Type | Description | Formula |
|-------|------|-------------|---------|
| `study_id` | string | Reference to Study | - |
| `hedges_g` | float | Standardized mean difference (corrected) | See FR-003 |
| `se_g` | float | Standard error of Hedges' g | Derived |
| `ci_lower` | float | Lower bound of 95% CI | $g - 1.96 \times SE$ |
| `ci_upper` | float | Upper bound of 95% CI | $g + 1.96 \times SE$ |
| `computation_method` | string | "Hedges_Olkin_1985" | Constant |

### 3. MetaAnalysisResult (Aggregated)
The final output of the synthesis.

| Field | Type | Description |
|-------|------|-------------|
| `pooled_hedges_g` | float | Weighted average effect size |
| `se_pooled` | float | Standard error of the pooled estimate |
| `ci_lower` | float | Lower bound of 95% CI |
| `ci_upper` | float | Upper bound of 95% CI |
| `tau_squared` | float | Between-study variance ($\tau^2$) |
| `i_squared` | float | Heterogeneity proportion ($I^2$) |
| `k_studies` | integer | Number of studies included |
| `egger_p_value` | float | p-value from Egger's test (or null if N<10) |
| `publication_bias_flag` | string | "SUSPECTED" if p<0.10, else "NONE" |
| `sensitivity_range` | string | Range of pooled effects in LOO analysis |

## Data Flow

1.  **Ingestion**: `data/raw/studies.csv` (Input)
2.  **Filtering**: `code/search/inclusion_filter.py` $\rightarrow$ `data/processed/included_studies.csv`
3.  **Computation**: `code/extraction/effect_size_calc.py` $\rightarrow$ `data/processed/effect_sizes.csv`
4.  **Synthesis**: `code/synthesis/meta_analysis.py` $\rightarrow$ `data/processed/meta_result.json`
5.  **Reporting**: `code/reporting/pdf_generator.py` $\rightarrow$ `reports/final_report.pdf`

## Data Hygiene Rules

- **Immutability**: `data/raw` files are never modified.
- **Checksums**: Every file in `data/` must have a corresponding SHA-256 hash in `state/`.
- **PII**: No patient names or identifiable info allowed. Only aggregate statistics (N, Mean, SD).
