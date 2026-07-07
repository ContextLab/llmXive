# Data Model: Quantifying the Impact of Transposable Element Activity on Gene Expression Variation in Drosophila

## Overview

This document defines the data structures, schemas, and transformations used in the project. All data is generated synthetically or derived from synthetic inputs. The model is designed to be lightweight, fitting within the memory constraints of a GitHub Actions free-tier runner.

## Key Entities

### 1. TE Insertion
Represents a Transposable Element insertion site and its genotype across lines.

| Field | Type | Description |
| :--- | :--- | :--- |
| `te_id` | string | Unique identifier (e.g., `TE_001`). |
| `chromosome` | string | Chromosome name (e.g., `2L`, `3R`). |
| `start` | integer | Genomic start coordinate. |
| `end` | integer | Genomic end coordinate. |
| `family` | string | TE family (e.g., `P-element`, `copia`). |
| `frequency` | float | Presence frequency across lines (0.0 - 1.0). |
| `monomorphic` | boolean | True if frequency < 0.05 or > 0.95. |

### 2. Gene
Represents a protein-coding gene.

| Field | Type | Description |
| :--- | :--- | :--- |
| `gene_id` | string | Gene identifier (e.g., `FBgn000001`). |
| `chromosome` | string | Chromosome name. |
| `start` | integer | Transcription start site (TSS). |
| `end` | integer | Transcription end site (TES). |
| `strand` | string | `+` or `-`. |
| `symbol` | string | Gene symbol (e.g., `Act5C`). |

### 3. Line
Represents a DGRP line (sample).

| Field | Type | Description |
| :--- | :--- | :--- |
| `line_id` | string | Line identifier (e.g., `DGRP_001`). |
| `pc1` | float | Principal Component 1. |
| `pc2` | float | Principal Component 2. |
| `pc3` | float | Principal Component 3. |

### 4. TE-Gene Pair
The core unit of analysis, linking a TE to a proximal gene.

| Field | Type | Description |
| :--- | :--- | :--- |
| `te_id` | string | FK to TE Insertion. |
| `gene_id` | string | FK to Gene. |
| `distance_bp` | integer | Distance from TE to gene TSS/TES (negative if upstream). |
| `proximal` | boolean | True if `|distance_bp| <= 5000`. |
| `ambiguous` | boolean | True if TE overlaps multiple genes. |

### 5. Expression Matrix
Gene expression values per line.

| Field | Type | Description |
| :--- | :--- | :--- |
| `line_id` | string | FK to Line. |
| `gene_id` | string | FK to Gene. |
| `tpm` | float | Transcripts Per Million. |
| `log2_tpm` | float | Log2 transformed TPM (with offset). |
| `missing` | boolean | True if data is missing for this line/gene. |

### 6. Association Result
Output of the linear model analysis.

| Field | Type | Description |
| :--- | :--- | :--- |
| `te_id` | string | TE identifier. |
| `gene_id` | string | Gene identifier. |
| `effect_size` | float | Coefficient of TE_presence. |
| `ci_lower` | float | Lower bound of 95% CI. |
| `ci_upper` | float | Upper bound of 95% CI. |
| `p_value` | float | Unadjusted p-value. |
| `adj_p_value` | float | Benjamini-Hochberg adjusted p-value. |
| `vif_flag` | boolean | True if VIF > 5. |
| `proximity_flag` | boolean | True if not proximal. |
| `ambiguous_flag` | boolean | True if ambiguous. |
| `significance_status` | string | `significant` or `null`. |

### 7. Population Structure Metrics
Efficacy of PC control.

| Field | Type | Description |
| :--- | :--- | :--- |
| `gene_id` | string | Gene identifier. |
| `r2_with_pc` | float | R² of model with PCs. |
| `r2_without_pc` | float | R² of model without PCs. |
| `r2_reduction` | float | `r2_without_pc - r2_with_pc`. |

### 8. Permutation Result
Null distribution statistics.

| Field | Type | Description |
| :--- | :--- | :--- |
| `te_id` | string | TE identifier. |
| `gene_id` | string | Gene identifier. |
| `observed_t` | float | Observed t-statistic. |
| `null_95th` | float | 95th percentile of null distribution. |
| `perm_p_value` | float | Proportion of null t > observed t. |

## Data Flow

1.  **Generation**: `data_generator.py` creates `TE Insertion`, `Gene`, `Line`, and `Expression Matrix` (Mock).
2.  **Pairing**: `association.py` joins TE and Gene to create `TE-Gene Pair` (filtering by proximity and monomorphism).
3.  **Analysis**: `association.py` fits models, calculates VIF, and generates `Association Result`.
4.  **Correction**: `association.py` applies BH correction.
5.  **Permutation**: `permutation.py` generates `Permutation Result` for significant pairs.
6.  **Replication**: `replication.py` compares Primary and Secondary results.
