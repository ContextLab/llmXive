# Data Model: Predicting Gene Expression from Chromatin Accessibility

## 1. Overview

This document defines the data structures used throughout the pipeline, from raw ENCODE downloads to final model outputs. All data is stored in CSV, BED, or Pickle formats for compatibility and reproducibility.

## 2. Input Data Models

### 2.1 Raw RNA-seq Counts
**Source**: ENCODE RNA-seq experiments  
**Format**: CSV  
**Schema**:
| Column | Type | Description |
| :--- | :--- | :--- |
| `gene_id` | str | Ensembl gene ID |
| `gene_name` | str | Gene symbol |
| `sample_id` | str | ENCODE sample ID |
| `cell_line` | str | Cell line name (e.g., GM12878) |
| `count` | int | Raw read count |

**Constraints**:
- `gene_id` must be unique per row.
- `count` ≥ 0.

### 2.2 Raw DNase/ATAC-seq Peaks
**Source**: ENCODE peak calls  
**Format**: BED  
**Schema**:
| Column | Type | Description |
| :--- | :--- | :--- |
| `chrom` | str | Chromosome (e.g., chr1) |
| `start` | int | 0-based start position |
| `end` | int | 0-based end position |
| `score` | float | Peak score (e.g., -log10 p-value) |
| `strand` | str | Strand (+/-) |

**Constraints**:
- `start` < `end`.
- `chrom` must match genome assembly (hg38).

### 2.3 Gene Coordinates
**Source**: GENCODE / RefSeq  
**Format**: BED  
**Schema**:
| Column | Type | Description |
| :--- | :--- | :--- |
| `chrom` | str | Chromosome |
| `start` | int | TSS position (0-based) |
| `end` | int | TSS position + 1 |
| `gene_id` | str | Ensembl gene ID |
| `gene_name` | str | Gene symbol |

**Constraints**:
- `start` is the TSS.
- `gene_id` must match RNA-seq data.

## 3. Processed Data Models

### 3.1 Binned Feature Matrix
**Description**: Accessibility signal aggregated into **200 fixed-width bins** within ±50kb of each gene's TSS. The promoter region (TSS ± 2kb) is **excluded**.  
**Format**: CSV (wide format)  
**Schema**:
| Column | Type | Description |
| :--- | :--- | :--- |
| `gene_id` | str | Ensembl gene ID |
| `cell_line` | str | Cell line name |
| `bin_1_score` | float | Aggregated score for bin 1 (e.g., -50kb to -49.5kb) |
| ... | ... | ... |
| `bin_200_score` | float | Aggregated score for bin 200 (e.g., +49.5kb to +50kb) |

**Constraints**:
- Missing values imputed with median per bin (FR-005).
- Genes with zero expression in all samples are filtered (FR-003).
- **Promoter Exclusion**: Bins overlapping TSS ± 2kb are set to 0 or excluded from the matrix.

### 3.2 Target Vector
**Description**: Log-transformed gene expression values.  
**Format**: CSV  
**Schema**:
| Column | Type | Description |
| :--- | :--- | :--- |
| `gene_id` | str | Ensembl gene ID |
| `cell_line` | str | Cell line name |
| `log_count` | float | log(count + 1) |

**Constraints**:
- `log_count` ≥ 0.

### 3.3 Model Artifacts
**Description**: Serialized Elastic Net models and CV scores.  
**Format**: Pickle (`.pkl`) and JSON  
**Schema**:
- **Model**: `sklearn.linear_model.ElasticNet` object.
- **CV Scores**: JSON object with keys: `cell_line`, `fold` (LOOCV), `r2`, `pearson_r`, `p_value`, `p_value_corrected`.

## 4. Derived Data Models

### 4.1 Housekeeping Genes
**Description**: Genes with coefficient of variation (CV) < 0.2 across all cell lines.  
**Format**: CSV  
**Schema**:
| Column | Type | Description |
| :--- | :--- | :--- |
| `gene_id` | str | Ensembl gene ID |
| `gene_name` | str | Gene symbol |
| `cv` | float | Coefficient of variation |

### 4.2 Cell-Type-Specific Genes
**Description**: Genes with CV > 0.5 in at least one cell line.  
**Format**: CSV  
**Schema**:
| Column | Type | Description |
| :--- | :--- | :--- |
| `gene_id` | str | Ensembl gene ID |
| `gene_name` | str | Gene symbol |
| `max_cv` | float | Maximum CV across cell lines |
| `cell_line` | str | Cell line with max CV |

### 4.3 Feature Importance Report (Binned)
**Description**: Top bins ranked by coefficient magnitude.  
**Format**: CSV  
**Schema**:
| Column | Type | Description |
| :--- | :--- | :--- |
| `gene_id` | str | Ensembl gene ID |
| `bin_id` | str | Bin identifier (e.g., "bin_50") |
| `coefficient` | float | Elastic Net coefficient |
| `distance_to_tss` | int | Distance from bin center to TSS (bp) |
| `within_10kb` | bool | True if distance ≤ 10kb |

### 4.4 Performance Gap Report
**Description**: Comparison of R² between housekeeping and cell-type-specific genes.  
**Format**: CSV  
**Schema**:
| Column | Type | Description |
| :--- | :--- | :--- |
| `category` | str | "housekeeping" or "cell_type_specific" |
| `cell_line` | str | Cell line name |
| `r2_mean` | float | Mean R² for the category |
| `r2_std` | float | Standard deviation of R² |

## 5. Data Flow Diagram

```mermaid
flowchart TD
    A[ENCODE RNA-seq] -->|download_encode.py| B(data/raw/encode_counts.csv)
    C[ENCODE Peaks] -->|download_encode.py| D(data/raw/encode_peaks.bed)
    E[GENCODE TSS] -->|download_encode.py| F(data/raw/gene_coords.bed)
    B -->|preprocess.py| G(data/processed/filtered_expression.csv)
    D -->|preprocess.py| H(data/processed/binned_matrix.csv)
    G -->|preprocess.py| I(data/processed/imputed_expression.csv)
    I -->|preprocess.py| J(data/processed/housekeeping_genes.csv)
    I -->|preprocess.py| K(data/processed/cell_type_specific_genes.csv)
    H -->|train.py| L(data/models/elastic_net_{cell_line}.pkl)
    I -->|train.py| L
    L -->|analyze.py| M(data/processed/feature_importance.csv)
    J -->|analyze.py| M
    K -->|analyze.py| M
    M -->|report| N(paper/results.md)
```

**Note**: The "Binned Feature Matrix" (H) is the key intermediate product that reduces dimensionality from ~1M peaks to 200 bins per gene.