# Data Model Specification

## Overview

This document defines the data structures, schemas, and relationships used throughout the epigenetic drift analysis pipeline. It ensures consistency between data acquisition, preprocessing, analysis, and reporting.

## Core Entities

### Dataset

Represents a single multi-generational omics study.

| Field | Type | Description |
|:--- |:--- |:--- |
| `accession` | string | Unique identifier (e.g., GSE12345) |
| `title` | string | Original study title |
| `organism` | string | Organism name (normalized) |
| `data_types` | list | Types of data present (e.g., ["methylation", "rna_seq"]) |
| `generations` | int | Number of generations studied |
| `metadata` | dict | Raw metadata from source |

### VarianceMatrix

The unified analysis-ready matrix containing variance metrics for both layers.

| Column | Type | Description |
|:--- |:--- |:--- |
| `gene_id` | string | Gene identifier |
| `organism` | string | Organism name |
| `condition` | string | Environmental condition (e.g., "fluctuating", "constant") |
| `methyl_variance` | float | LOGO-derived methylation variance |
| `expr_variance` | float | LOGO-derived expression variance |
| `methyl_missing` | bool | Flag for missing methylation data |
| `expr_missing` | bool | Flag for missing expression data |
| `fluctuation_timescale` | float | Environment fluctuation period (if available) |
| `drift_timescale` | float | Calculated drift slope (variance vs. generation) |

### CorrelationResult

Output of the correlation analysis module.

| Field | Type | Description |
|:--- |:--- |:--- |
| `condition` | string | Environmental condition subset |
| `rho` | float | Spearman's rank correlation coefficient |
| `p_value_theoretical` | float | P-value from theoretical distribution |
| `p_value_empirical` | float | P-value from permutation test |
| `n_samples` | int | Number of gene pairs analyzed |
| `temporal_resolution_flag` | string | "sufficient" or "insufficient" |
| `convergence_warning` | bool | True if permutation test hit hard cap |

### TimescaleAlignment

Output of the timescale alignment validation module (Phase 6).

| Field | Type | Description |
|:--- |:--- |:--- |
| `dataset_accession` | string | Source dataset ID |
| `env_timescale` | float | Extracted environmental fluctuation period |
| `drift_timescale` | float | Calculated drift rate (slope) |
| `alignment_status` | string | "Aligned", "Mismatched", or "Insufficient Data" |
| `temporal_validation_status` | string | "VALID" or "INSUFFICIENT" |

### FinalReport

The consolidated output merging all analysis stages.

| Field | Type | Description |
|:--- |:--- |:--- |
| `discovery_status` | object | Status from discovery phase |
| `correlation_results` | list | List of `CorrelationResult` objects |
| `timescale_alignment` | list | List of `TimescaleAlignment` objects |
| `sensitivity_results` | object | Results from threshold sweep |
| `stability_flags` | object | Flags from stability check |
| `hypothesis_refinement` | string | Updated hypothesis reflecting timescale alignment |

## Hypothesis Section Update

The study hypothesis has been refined to incorporate the **Timescale Alignment** requirement (Phase 6).

**Original Hypothesis**:
"Epigenetic drift facilitates adaptive landscape exploration by enabling rapid phenotypic shifts in fluctuating environments."

**Refined Hypothesis**:
"Epigenetic drift facilitates adaptive landscape exploration **only when the timescale of drift aligns with the timescale of environmental fluctuations**. Specifically, we hypothesize that a strong positive correlation between epigenetic and expression variance will be observed primarily in datasets where the drift rate (variance slope per generation) matches the environmental fluctuation frequency within a 10% margin. Datasets exhibiting 'Mismatched' or 'Insufficient' timescale alignment will not support the mechanism of adaptive exploration, suggesting that drift in those cases is noise rather than a functional adaptation mechanism."

This refinement strictly forbids causal assertions. The pipeline outputs a `temporal_validation_status` flag:
- **"VALID"**: Timescales are aligned or mismatched (data sufficient for comparison).
- **"INSUFFICIENT"**: Data missing or temporal resolution too low (N < 3 generations).

## Data Flow

1. **Discovery**: `query_geno.py` -> `output/discovery_results.json`
2. **Preprocessing**: `rna_seq.py` + `methyl.py` -> `data/processed/variance_matrix.csv`
3. **Correlation**: `correlation.py` -> `output/correlation_results.json`
4. **Timescale**: `timescale_align.py` -> `output/timescale_alignment.json`
5. **Sensitivity**: `sensitivity.py` -> `output/sensitivity_results.json`
6. **Report**: `main.py` -> `output/final_report.json`

## Constraints

- **CPU Only**: All calculations must run on 2 cores, <2GB RAM.
- **Real Data**: No synthetic data in final outputs.
- **Observational**: No tasks assert causality; only correlation and alignment flags are produced.
- **Runtime**: Pipeline must complete within 6 hours.