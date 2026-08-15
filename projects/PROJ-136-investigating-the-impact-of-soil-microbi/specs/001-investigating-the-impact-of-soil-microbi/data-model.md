# Data Model: Investigating the Impact of Soil Microbiome Diversity on Plant Disease Resistance

## Entity-Relationship Overview

The data model is designed to handle the potential mismatch between microbiome data and disease data. It supports the "Ideal" scenario (matched data) and the "Missing Data" scenario (Feasibility Report).

### Core Entities

#### 1. Sample
Represents a single soil collection event.
-   `sample_id` (str): Unique identifier.
-   `gps_lat` (float): Latitude.
-   `gps_lon` (float): Longitude.
-   `plant_species` (str): Plant species name.
-   `soil_type` (str): Soil classification.
-   `sequencing_depth` (int): Total reads.
-   `alpha_shannon` (float): Shannon diversity index.
-   `alpha_simpson` (float): Simpson diversity index.
-   `alpha_faith_pd` (float): Faith's Phylogenetic Diversity.
-   `disease_incidence` (float): Proportion (0.0 - 1.0). **Required for analysis**.
-   `missing_variables` (list[str]): List of variables that could not be matched (e.g., `["disease_incidence"]`).

#### 2. Taxon
Represents a microbial taxonomic unit.
-   `taxon_id` (str): Unique identifier (OTU/ASV ID).
-   `lineage` (str): Taxonomic lineage (e.g., "Bacteria; Firmicutes; ...").
-   `abundance` (float): Relative abundance in a sample.
-   `q_value` (float): Differential abundance q-value (from ANCOM).
-   `is_keystone` (bool): Flag for high centrality in network.

#### 3. StudyMetadata
Represents the provenance of the dataset.
-   `source_url` (str): URL of the dataset.
-   `download_date` (datetime): Date of download.
-   `checksum` (str): SHA256 checksum.
-   `missing_variables` (list[str]): List of variables that could not be matched (e.g., `["disease_incidence"]`).

#### 4. VerificationReport
Generated if data is missing.
-   `status` (str): "HALTED" or "SUCCESS".
-   `missing_variables` (list[str]): List of missing variables.
-   `message` (str): Explanation of why the pipeline halted.

## Data Flow

1.  **Raw Ingestion**:
    -   `data/raw/otu_table.tsv`: Raw OTU counts.
    -   `data/raw/verification_report.json`: (If data missing) Generated instead of disease records.
2.  **Preprocessing**:
    -   `data/processed/rarefied-table.qza`: Rarefied OTU table (if data available).
    -   `data/processed/alpha_diversity.tsv`: Computed diversity metrics (if data available).
3.  **Matching/Enrichment**:
    -   `data/processed/matched_samples.csv`: Joined data (if data available).
    -   *Missing*: If join fails, `verification_report.json` is generated.
4.  **Analysis Output**:
    -   `data/processed/model_results.json`: GLMM coefficients, p-values (if data available).
    -   `data/processed/network_nodes.csv`: Network centrality metrics (if data available).

## Constraints & Validation

-   **Disease Incidence**: Must be between 0.0 and 1.0. If missing, the pipeline halts.
-   **Sequencing Depth**: Must be > 0.
-   **Missing Variables**: If `disease_incidence` is missing in the source, the system MUST generate `verification_report.json` with `[MISSING_VARIABLE: disease_incidence]` and halt.