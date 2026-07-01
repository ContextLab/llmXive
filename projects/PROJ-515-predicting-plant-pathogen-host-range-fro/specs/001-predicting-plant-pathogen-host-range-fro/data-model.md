# Data Model: Predicting Plant Pathogen Host Range from Publicly Available Genomic and Interaction Data

## Entities and Relationships

### Pathogen
- **Attributes**:  
  - `accession_id` (string): Unique NCBI GenBank accession number (e.g., "GCF_000001234.5").  
  - `taxonomic_group` (string): Taxonomic classification (e.g., "Fungi", "Bacteria").  
  - `genome_path` (string): Local file path to FASTA genome file.  
  - `host_range_breadth` (float): Observed count of unique hosts in the interaction database (ground truth). *Note: This is distinct from the model's predicted mean probability, which is used for ranking but not for validation against this metric.*
- **Relationships**:  
  - One-to-many with `InteractionRecord` (a pathogen can infect multiple hosts).  
  - One-to-one with `FeatureVector` (each pathogen has one genomic feature vector).  

### Host
- **Attributes**:  
  - `species_name` (string): Scientific name of the plant host (e.g., "Solanum lycopersicum").  
  - `taxonomic_id` (string): NCBI Taxonomy ID (e.g., "4113").  
- **Relationships**:  
  - One-to-many with `InteractionRecord` (a host can be infected by multiple pathogens).  

### InteractionRecord
- **Attributes**:  
  - `pathogen_id` (string): Reference to `Pathogen.accession_id`.  
  - `host_id` (string): Reference to `Host.species_name` or `taxonomic_id`.  
  - `infects` (integer): Binary label (1 = infects, 0 = does not infect, -1 = unknown/missing).  
  - `source` (string): Source database (e.g., "PHI-Base", "Interactome3D", "NCBI BioSample").  
  - `retrieval_date` (date): Date of data retrieval (for provenance).  
- **Relationships**:  
  - Many-to-one with `Pathogen` and `Host`.  
  - Composite key: `(pathogen_id, host_id)`.  

### FeatureVector
- **Attributes**:  
  - `pathogen_id` (string): Reference to `Pathogen.accession_id`.  
  - `effector_count` (integer): Number of predicted effector proteins (EffectorP 3.0).  
  - `pfam_counts` (dict): Dictionary of Pfam domain counts (e.g., `{"PF00001": 5, "PF00002": 3}`).  
  - `gc_content` (float): GC percentage (0–100). *Note: May be excluded if k-mer PCA is used.*
  - `kmer_freq` (dict): Normalized 4-mer frequency profile (e.g., `{"AAAA": 0.01, "AAAC": 0.005}`). *Note: Reduced to 20 PCA components before model input.*
  - `sm_cluster_count` (integer): Number of secondary-metabolism clusters (antiSMASH 7.0).  
- **Relationships**:  
  - One-to-one with `Pathogen`.  

### ModelArtifact
- **Attributes**:  
  - `model_path` (string): Local file path to serialized model (`model.pkl`).  
  - `scaler_params` (dict): Scaler parameters (mean, std) for feature normalization.  
  - `hyperparams` (dict): Model hyperparameters (e.g., `{"C": 0.1, "penalty": "l1"}`).  
  - `training_metrics` (dict): Cross-validation metrics (e.g., `{"AUPRC": 0.75, "precision@0.5": 0.80}`).  
- **Relationships**:  
  - One-to-many with `Prediction` (model generates predictions for novel pathogens).  

## Data Flow

1. **Data Ingestion**:  
   - Download pathogen genomes from NCBI GenBank (FR-001).  
   - Fetch interaction records from PHI-Base, Interactome3D, NCBI BioSample (FR-002).  
   - Merge interactions; deduplicate by `(pathogen_id, host_id)`; treat missing records as 'unknown' (FR-013).  

2. **Feature Extraction**:  
   - Compute genomic features (effector count, Pfam, GC, k-mer, SM clusters) for each pathogen (FR-003).  
   - Apply dimensionality reduction (PCA for k-mers, top-50 for Pfam) and VIF analysis; remove collinear features (FR-014).  

3. **Model Training**:  
   - Split data into training and pathogen-stratified hold-out sets (FR-012).  
   - Train logistic regression with inner CV; evaluate with outer CV (FR-004, FR-005).  
   - Conduct permutation testing; generate SHAP values (FR-006, FR-007).  

4. **Prediction & Reporting**:  
   - Predict infection probabilities for novel pathogens (FR-008, US-3).  
   - Generate reports: `significant_features.tsv`, `bias_awareness_report.json`, `prediction.csv` (FR-007, FR-018, US-2, US-3).  

## Data Quality Constraints

- **Completeness**: All pathogen genomes must be complete (no fragmented drafts); missing genomes trigger warnings and skip processing.  
- **Consistency**: Interaction records must have unique `(pathogen_id, host_id)` pairs; duplicates are deduplicated.  
- **Validity**: Feature vectors must not be all zeros; if so, baseline probability (prevalence) is assigned (Edge Case: Zero-Feature Pathogen).  
- **Provenance**: All data sources (NCBI GenBank, PHI-Base, etc.) must be logged with retrieval dates and accession numbers (Constitution VI).  

## Validation Rules

- **Pathogen**: `accession_id` must match NCBI GenBank format; `genome_path` must exist.  
- **Host**: `species_name` must be valid scientific name; `taxonomic_id` must be numeric.  
- **InteractionRecord**: `infects` ∈ {0, 1, -1}; `source` ∈ {"PHI-Base", "Interactome3D", "NCBI BioSample"}.  
- **FeatureVector**: `effector_count` ≥ 0; `gc_content` ∈ [0, 100]; `sm_cluster_count` ≥ 0.  
- **ModelArtifact**: `training_metrics.AUPRC` must be ≥ 0 and ≤ 1; `hyperparams` must include `C` and `penalty`.
