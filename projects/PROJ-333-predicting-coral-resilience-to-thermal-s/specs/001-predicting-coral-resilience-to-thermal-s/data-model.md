# Data Model: Predicting Coral Resilience to Thermal Stress

## Entities

### 1. RawSample
Represents a single biological sample from the NCBI SRA.
- `sample_id` (str): Unique SRA accession (e.g., SRR123456).
- `run_id` (str): SRA Run ID (e.g., SRR123456).
- `fastq_url` (str): Direct URL to the FASTQ file.
- `treatment` (str): "Heat" or "Control".
- `checksum` (str): SHA256 hash of the downloaded file.

### 2. ExpressionMatrix
A sparse matrix of gene counts.
- `gene_id` (str): Ensembl or NCBI gene ID.
- `sample_id` (str): Foreign key to RawSample.
- `count` (int): Raw read count.
- `is_filtered` (bool): True if count < threshold (e.g., 10).

### 3. DGEResult
Results of the differential expression analysis.
- `gene_id` (str): Primary key.
- `log2_fold_change` (float): Log2 fold change (Heat vs Control).
- `p_value` (float): Raw p-value.
- `p_adj` (float): Adjusted p-value (FDR).
- `significant` (bool): True if `p_adj` < 0.05.

### 4. PathwayEnrichment
Results of the pathway analysis.
- `term_id` (str): Pathway ID (e.g., GO:0006954).
- `term_name` (str): Pathway name.
- `p_value` (float): Raw enrichment p-value.
- `p_adj` (float): Adjusted p-value.
- `genes` (list[str]): List of significant genes in this pathway.

## Data Flow

1. **Ingest**: `RawSample` created from NCBI metadata.
2. **Quantify**: `RawSample` -> `ExpressionMatrix` (Sparse).
3. **Filter**: `ExpressionMatrix` -> Filtered `ExpressionMatrix` (counts > 10).
4. **DGE**: Filtered `ExpressionMatrix` -> `DGEResult`.
5. **Enrich**: `DGEResult` (significant genes) -> `PathwayEnrichment`.

## Constraints

- **Memory**: `ExpressionMatrix` MUST be stored as a sparse matrix.
- **Integrity**: `RawSample.checksum` MUST match the downloaded file.
- **Completeness**: `DGEResult` MUST contain all genes in the filtered matrix.
