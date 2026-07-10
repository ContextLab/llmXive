# Data Model: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Entity Relationship Overview

The data model is designed to support the strict alignment of genomic features (BGCs) with metabolomic profiles. The core relationship is a **1:1** mapping between a `Species` and its `AlignedProfile`, which is the intersection of valid genomic and metabolomic data.

## Core Entities

### 1. Species
The fundamental unit of analysis.
-   **Attributes**:
    -   `species_id` (string): Unique identifier (e.g., "Arabidopsis_thaliana").
    -   `taxon_id` (string): NCBI Taxonomy ID.
    -   `clade` (string): Phylogenetic family or monophyletic group (for LOCO split).
    -   `genome_path` (string): Path to downloaded FASTA/GFF.
    -   `metabolite_profile_id` (string): ID from PMDB/MetaboLights.
-   **Constraints**: Must have both `genome_path` and `metabolite_profile_id` to be included in the final dataset.

### 2. BGC Feature Matrix
A sparse binary/count matrix derived from antiSMASH.
-   **Rows**: `species_id`
-   **Columns**: `bgc_type` (e.g., "terpene", "alkaloid", "polyketide").
-   **Values**: 0 (absent) or 1 (present) / Count.
-   **Source**: `code/utils/anti_smash_parser.py` (FR-002).

### 3. Metabolite Profile
Quantitative abundance data.
-   **Rows**: `species_id`
-   **Columns**: `inchi_key` (unique chemical identifier).
-   **Values**: Log-transformed abundance (float).
-   **Transformation**: `log10(abundance + 1e-6)` to handle zeros.

### 4. Aligned Dataset (The "Single Source of Truth")
The final feature-target matrix used for modeling.
-   **Structure**: DataFrame where rows are species, columns are BGC types (features) + Metabolite abundances (targets).
-   **Filtering**: Excludes any species with missing data in either source.
-   **Minimum Size**: ≥10 rows (US-1).

## Data Flow & Transformations

1.  **Raw Download**:
    -   `data/raw/genomes/<species_id>.fasta`
    -   `data/raw/metabolites/<species_id>.csv`
2.  **Processing**:
    -   `anti_smash` → `data/processed/bgc_matrix.csv`
    -   `harmonize` → `data/processed/metabolite_matrix.csv`
3.  **Alignment**:
    -   Join on `species_id` → `data/processed/aligned_dataset.csv`
    -   **Validation**: Check for NaNs/Infs. If >50% zero BGCs, raise warning.

## Contract Definitions

The system enforces the following contracts:
-   **Input Contract**: `aligned_dataset.csv` must contain `species_id`, `clade`, and at least one BGC column and one Metabolite column.
-   **Output Contract**: `model_results.json` must contain `r2_test`, `p_permutation`, `p_pic`, and `vif_scores`.

## Schema Constraints

-   **No PII**: No human identifiers.
-   **Immutability**: Raw files are never overwritten.
-   **Checksums**: Every file in `data/raw` and `data/processed` has a SHA-256 hash recorded.
