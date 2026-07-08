# Data Model: Assessing the Reliability of Statistical Significance in Openly Available Genomic Datasets

## Entities

### 1. GenomicDataset
Represents a single RNA-seq study.
- **Attributes**:
  - `source` (str): "TCGA", "ENCODE", "GEO", or "Recount".
  - `dataset_id` (str): Unique identifier (e.g., "GEO:GSE12345").
  - `raw_count_matrix` (str): Path to raw CSV/Parquet file.
  - `metadata` (dict): Dictionary of sample attributes (batch, condition, etc.).
  - `n_samples` (int): Total number of samples.
  - `n_genes` (int): Total number of genes.
  - `checksum` (str): SHA256 of the raw file.

### 2. SubsetAnalysis
Represents a partition of a `GenomicDataset`.
- **Attributes**:
  - `subset_id` (int): 0 to 4 (or more).
  - `sample_indices` (list[int]): Indices of samples in this subset.
  - `p_values` (dict): Gene ID -> p-value.
  - `effect_sizes` (dict): Gene ID -> log2 fold-change.
  - `significant_genes` (list[str]): List of gene IDs with adj-p < 0.05.
  - `stability_correlation` (float): Pearson r vs. full set (calculated on ALL genes).

### 3. NullDistribution
Represents the empirical p-value distribution from permutations.
- **Attributes**:
  - `iteration_count` (int): Number of permutations performed.
  - `empirical_p_values` (list[float]): Aggregated p-values across iterations.
  - `inflation_metric` (float): KS statistic $D$ and p-value.
  - `is_low_confidence` (bool): True if iterations were reduced due to time limits or sparse permutation space.
  - `dispersion_fixed` (bool): True if the Fixed-Dispersion approximation was used.

### 4. StabilityMetric
Aggregated result for a dataset.
- **Attributes**:
  - `dataset_id` (str).
  - `mean_stability_r` (float).
  - `std_stability_r` (float).
  - `inflation_d` (float).
  - `inflation_p_value` (float).
  - `inflation_flag` (str): "OK", "Inflated", "Low Confidence", "Sparse Null".

## Data Flow

1. **Ingest**: `GenomicDataset` created from verified URL. Checksum recorded.
2. **Preprocess**: Filter zero-count genes. Split into `SubsetAnalysis` objects.
3. **Analyze**: Run DE on full set and subsets -> `p_values`, `effect_sizes`.
4. **Permute**: Run permutations (Fixed-Dispersion) -> `NullDistribution`.
5. **Aggregate**: Calculate `StabilityMetric` for each dataset.
6. **Report**: Combine `StabilityMetric` from all datasets into final summary.

## Storage Format

- **Raw Data**: CSV or Parquet (preserved in `data/raw/`).
- **Processed Data**: JSON or CSV (in `data/processed/`).
  - Example: `processed/TCGA_PRAD_subsets.json`
- **Results**: JSON (in `artifacts/results/`).
  - Example: `artifacts/results/stability_summary.json`
