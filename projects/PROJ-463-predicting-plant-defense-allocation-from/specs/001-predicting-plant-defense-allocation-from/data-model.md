# Data Model: Predicting Plant Defense Allocation from Publicly Available Transcriptomic Data

## Entities & Relationships

### 1. RNA-Seq Study
Represents a single GEO/SRA experiment.
*   **Attributes**:
    *   `accession_id` (str): GEO (GSE...) or SRA (SRR...) ID.
    *   `organism` (str): Plant species name (e.g., *Arabidopsis thaliana*).
    *   `tissue` (str): Leaf, stem, root.
    *   `herbivore_type` (str): "chewing", "piercing-sucking", "control".
    *   `sequencing_platform` (str): Illumina NovaSeq, etc.
    *   `replicate_count` (int): Number of biological replicates.
    *   `raw_fastq_path` (str): Path to `data/raw/<accession_id>.fastq.gz`.
    *   `checksum` (str): SHA-256 of raw file.

### 2. Herbivore-Response Vector
The predictor feature for a species-tissue pair.
*   **Attributes**:
    *   `species` (str): Species name.
    *   `tissue` (str): Tissue type.
    *   `herbivore_type` (str): "chewing" or "piercing-sucking".
    *   `de_genes` (list): List of gene IDs (top DE genes).
    *   `log2fc_values` (list): Signed log2 fold change values.
    *   `pathway_scores` (dict): Aggregated scores per pathway (≤50 features).

### 3. Defense Allocation Index
The outcome variable for a species.
*   **Attributes**:
    *   `species` (str): Species name.
    *   `chemical_traits` (dict): { "Glucosinolates": value, "Alkaloids": value, "Phenolics": value }.
    *   `physical_traits` (dict): { "Trichome Density": value, "Leaf Tensile Strength": value }.
    *   `index_value` (float): Ratio of standardized chemical mean to physical mean.
    *   `data_source` (str): "TRY", "Phenoscape", "GBIF", "Literature".

### 4. Species
Aggregated entity linking transcriptomic and trait data.
*   **Attributes**:
    *   `species_name` (str).
    *   `has_chewing_data` (bool).
    *   `has_piercing_data` (bool).
    *   `has_trait_data` (bool).
    *   `included_in_model` (bool): True if all conditions met.

## Data Flow

1.  **Raw Ingestion**: NCBI GEO/SRA → `data/raw/` (FASTQ).
2.  **Preprocessing**: FASTQ → (fastp) → Trimmed → (HISAT2) → BAM → (featureCounts) → TPM Matrix.
3.  **Batch Correction**: TPM Matrix → (ComBat-seq) → Corrected Matrix.
4.  **Feature Derivation**: Corrected Matrix → (DESeq2) → DE Genes → (Pathway Aggregation) → Herbivore-Response Vector.
5.  **Trait Integration**: Species List → (TRY/GBIF) → Defense Traits → Defense Allocation Index.
6.  **Modeling**: Response Vector + Index → (LOSO CV) → Model Performance Metrics.

## Storage & Versioning

*   **Raw Data**: `data/raw/` (Immutable, checksummed).
*   **Processed Data**: `data/processed/` (Derived files: TPM, DE results, trait tables).
*   **Manifests**: `data/manifests/real_data_manifest.json` (Tracks all data lineage).
*   **Versioning**: All files in `data/` are versioned via content hash in `state/`.
