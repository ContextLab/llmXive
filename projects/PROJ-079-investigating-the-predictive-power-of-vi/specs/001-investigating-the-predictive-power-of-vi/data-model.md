# Data Model: Predictive Modeling of Host Immune Response from Viral Sequence Features

## Entities

### 1. ViralGenome
Represents a complete viral nucleotide sequence.
- **Attributes**:
  - `accession_id`: str (NCBI Virus Accession)
  - `virus_family`: str
  - `genome_sequence`: str (FASTA string)
  - `host_species`: str (e.g., "Homo sapiens", "Mus musculus")
  - `source_url`: str (NCBI Virus URL)
  - `download_date`: str (ISO 8601)

### 2. HostExpressionSample
Represents a GEO transcriptomic sample.
- **Attributes**:
  - `gsm_id`: str (GEO Sample ID)
  - `gse_accession`: str (GEO Series ID)
  - `virus_strain_accession`: str (Linked to ViralGenome)
  - `raw_counts`: dict (Gene -> Count)
  - `normalized_counts`: dict (Gene -> Normalized Value)
  - `isg_score`: float (ISG-PC1 score)
  - `host_species`: str
  - `infection_time_point`: str

### 3. FeatureMatrix
Tabular entity linking ViralGenome to HostExpressionSample.
- **Attributes**:
  - `strain_accession`: str (Primary Key)
  - `isg_score`: float (Target Variable)
  - `cai`: float (Codon Adaptation Index)
  - `gc_content_global`: float
  - `gc_content_region_1`: float ... `gc_content_region_N`: float
  - `kmer_3_freq_*`: float (Flattened frequencies for k=3)
  - `kmer_4_freq_*`: float
  - `kmer_5_freq_*`: float
  - `kmer_6_freq_*`: float
  - `repeat_density`: float
  - `protein_stability_score`: float (ESM-1b or Proxy)
  - `vif_score`: float (Calculated post-hoc)
  - `is_collinear`: bool

## Data Flow Diagram

1. **Raw Data**:
   - `data/raw/viral_genomes.fasta` (NCBI Virus)
   - `data/raw/geo_counts.csv` (GEO)
2. **Processed Data**:
   - `data/raw/manifest.json` (Provenance)
   - `data/processed/normalized_counts.csv` (TMM normalized)
   - `data/processed/ortholog_map.csv` (Gene mapping)
   - `data/processed/isg_scores.csv` (PC1 scores)
   - `data/processed/viral_features.csv` (CAI, k-mers, etc.)
   - `data/processed/merged_dataset.csv` (Features + ISG)
3. **Artifacts**:
   - `data/artifacts/model.joblib` (Trained Elastic Net)
   - `data/artifacts/permutation_pvalue.json` (Global test)
   - `data/artifacts/feature_pvalues.json` (Debiased Lasso)
   - `data/artifacts/plots/` (Feature importance, PDP)

## Schema Definitions

- **Manifest**: JSON with checksums, versions, and source URLs.
- **Counts Matrix**: CSV with genes as rows, samples as columns.
- **Feature Matrix**: CSV with strains as rows, features as columns.
- **Permutation Output**: JSON with `observed_r2`, `p_value`, `n_permutations`.

## Constraints

- **Uniqueness**: `strain_accession` must be unique in the merged dataset.
- **Completeness**: No missing values in `isg_score` or `strain_accession`.
- **Range**: `cai` in [0, 1], `gc_content` in [0, 1], `repeat_density` in [0, 1].
- **VIF**: All retained predictors must have VIF <= 5 (FR-008).
