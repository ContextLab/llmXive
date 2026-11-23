# Data Model: Investigating the Predictive Power of Plant Phylogeny on Secondary Metabolite Profiles

## Entity Definitions

### PlantSpecies
Represents a single plant taxon in the study.
- **Attributes**:
    - `ncbi_tax_id`: Integer (NCBI Taxonomy ID)
    - `kegg_organism_code`: String (e.g., "ath" for Arabidopsis)
    - `species_name`: String (Binomial)
    - `climate_zone`: String (USDA zone code, e.g., "5a")
    - `status`: Enum (retrieved, missing_seq, missing_metabolite, excluded)

### PhylogeneticTree
Represents the evolutionary topology.
- **Attributes**:
    - `newick_string`: String (Standard Newick format)
    - `branch_lengths`: Dict (node -> length)
    - `rooted`: Boolean
    - `method`: String ("FastTree-2.1.10-DOUBLE-OMP")

### MetaboliteProfile
Binary vector of secondary metabolite presence.
- **Attributes**:
    - `species_id`: Reference to PlantSpecies
    - `compounds`: List[String] (KEGG Compound IDs)
    - `vector`: BinaryArray (1 if present, 0 if absent)
    - `source`: String ("KEGG BRITE: Secondary Metabolites")
    - **Construction Logic**: Binary vector is constructed by traversing the KEGG BRITE hierarchy. If a species is listed under a specific compound, the value is 1; otherwise, 0.

### DistanceMatrix
Symmetric matrix of pairwise distances.
- **Attributes**:
    - `type`: Enum ("patristic", "jaccard", "climate")
    - `matrix`: 2D Array (float)
    - `species_order`: List[String] (IDs corresponding to rows/cols)
    - `method`: String (e.g., "Jaccard", "Patristic", "Hamming")
    - **Climate Distance Method**: "Ordinal Difference" (|Zone_A - Zone_B|).

## Data Flow

1.  **Raw Ingestion**:
    - `data/raw/genbank_sequences.fasta` (Multi-locus)
    - `data/raw/kegg_metabolites.json` (Presence/Absence)
    - `data/raw/usda_climate.parquet` (Climate zones)
2.  **Processing**:
    - `data/processed/aligned.fasta` (MAFFT output)
    - `data/processed/tree.nwk` (FastTree output)
    - `data/processed/phylo_dist.npy` (Patristic distances)
    - `data/processed/metab_dist.npy` (Jaccard distances)
    - `data/processed/climate_dist.npy` (Climate distances)
3.  **Output**:
    - `output/results/mantel_stats.json` (r, p-value, permutations, spearman_r)
    - `output/figures/phylo_metabolite_heatmap.png`
    - `output/figures/mantel_results.png`

## Constraints & Validation

- **Completeness**: At least 80% of input species must have both sequence and metabolite data.
- **Matrix Symmetry**: All distance matrices must be symmetric (within floating point tolerance).
- **Diagonal**: All diagonal elements must be 0.0.
- **Climate Control**: Climate distance matrix must be derived from the verified USDA dataset using the ordinal difference metric.
- **Metric Selection**: Jaccard is used for metabolites due to binary data nature. Bray-Curtis is not applicable.