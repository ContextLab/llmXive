# Data Model: Predicting Plant Root System Architecture from Genomic Data

## Entity Definitions

### 1. GenomicDataset
*   **Description**: Raw or processed SNP data for *Arabidopsis thaliana* accessions.
*   **Attributes**:
    *   `accession_id`: Unique string identifier (e.g., "Col-0", "Ws-0").
    *   `variant_id`: String identifier for the SNP (e.g., "chr1:12345").
    *   `allele_count`: Integer (0, 1, 2) representing homozygous ref, heterozygous, homozygous alt.
    *   `missing`: Boolean (True if data missing).

### 2. PhenotypicDataset
*   **Description**: Root architecture measurements linked to accessions and conditions.
*   **Attributes**:
    *   `accession_id`: String identifier matching GenomicDataset.
    *   `nutrient_condition`: Categorical string (e.g., "Low_N", "High_N", "Control").
    *   `root_length`: Float (cm).
    *   `branching_density`: Float (branches/cm).
    *   `angle`: Float (degrees).
    *   `missing`: Boolean.

### 3. UnifiedDataset
*   **Description**: The merged, analysis-ready dataset.
*   **Attributes**:
    *   `accession_id`: Primary key.
    *   `nutrient_condition`: Categorical.
    *   `features`: Dictionary or flattened columns of allele counts (one column per variant).
    *   `target`: Float (selected root trait, e.g., `root_length`).
    *   `split`: Categorical ("train", "val", "test").

### 4. ModelOutput
*   **Description**: Results from a single training run.
*   **Attributes**:
    *   `model_id`: String (e.g., "RF_Low_N_v1").
    *   `algorithm`: String ("LinearRegression", "RandomForest", "GradientBoosting").
    *   `nutrient_condition`: String.
    *   `metrics`: Dictionary (`r2`, `mae`, `cv_score`).
    *   `feature_importance`: List of (feature_name, score) tuples.
    *   `permutation_p_value`: Float.

## Data Flow

1.  **Ingestion**: `raw/` (Genomic, Phenotypic) -> `download.py`.
2.  **Harmonization**: `preprocess.py` matches `accession_id`, filters missing data, encodes genotypes.
3.  **Splitting**: Stratified split by `nutrient_condition` (80/10/10).
4.  **Training**: `train.py` iterates over conditions and algorithms.
5.  **Evaluation**: `evaluate.py` computes metrics, runs permutations, calculates SHAP.
6.  **Artifact**: `data/processed/results.json` and `data/processed/figures/`.
