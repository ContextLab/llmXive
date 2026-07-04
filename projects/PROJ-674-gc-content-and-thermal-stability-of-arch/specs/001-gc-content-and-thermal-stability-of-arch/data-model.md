# Data Model: GC Content and Thermal Stability of Archaeal tRNA Stems

## Overview

This document defines the data structures used for the project, ensuring alignment with the `spec.md` entities and `plan.md` phases. All data is stored in `data/` as CSV/JSON/Parquet files with checksums.

## Entity Definitions

### 1. tRNA_Sequence
Represents a single tRNA molecule from a specific species.
- **species_id**: String (e.g., "Methanocaldococcus_jannaschii")
- **tRNA_type**: String (e.g., "tRNA-Ala", "tRNA-Gly")
- **sequence**: String (A, U, G, C)
- **stem_regions**: Object
  - `acceptor_stem`: String (sequence)
  - `d_stem`: String (sequence)
  - `anticodon_stem`: String (sequence)
  - `t_stem`: String (sequence)
- **gc_per_stem**: Object (float, 0.0-1.0)
  - `acceptor_stem`: float
  - `d_stem`: float
  - `anticodon_stem`: float
  - `t_stem`: float
- **mean_stem_gc**: float (average of all stem GCs)

### 2. Species_Metadata
Represents the host organism's environmental data.
- **species_id**: String (Primary Key)
- **ogt**: float (Optimal Growth Temperature in °C)
- **phylogenetic_lineage**: String (e.g., "Euryarchaeota")
- **source**: String (e.g., "BacDive")
- **data_version**: String (Date/Release of source)
- **tRNA_count**: Integer (Number of tRNA types for this species, used for WLS weighting)
- **tree_coverage**: Boolean (True if species is present in the phylogenetic tree)

### 3. Analysis_Result
Aggregated statistical output per species and global.
- **species_id**: String
- **mean_stem_gc**: float
- **ogt**: float
- **global_stats**: Object
  - `correlation_r`: float
  - `p_value`: float
  - `ci_95_lower`: float
  - `ci_95_upper`: float
  - `permutation_p_value`: float (null if no tree)
  - `pic_adjusted_r`: float (or null)
  - `caution_flag`: String (optional)
  - `m_des`: float (Minimum Detectable Effect Size)
- **sensitivity_sweep**: Array (Results across thresholds)
- **lasso_coefficients**: Object (Coefficients for each stem type)

## Data Flow

1.  **Raw Input**:
    - `data/raw/bacdive_genomes.csv` (Source: BacDive)
    - `data/raw/gtrnadb_sequences.fasta` (Source: GtRNAdb)
2.  **Processed**:
    - `data/processed/species_metadata.csv` (Filtered, joined with OGT, `tRNA_count`, `tree_coverage`)
    - `data/processed/tRNA_features.csv` (Parsed stems, GC%)
    - `data/processed/merged_dataset.csv` (Join of Metadata + Features)
3.  **Output**:
    - `data/results/analysis_summary.json` (Final stats, flags, MDES)
    - `data/results/sensitivity_report.json` (Sweep results)

## Constraints

- **Completeness**: Only species with both OGT and complete stem annotations are included.
- **Immutability**: Raw files are never modified. Derivations are new files.
- **Checksums**: All files in `data/` have a corresponding entry in `data/metadata.json` with SHA-256 hash.
- **Validation**:
    - `download.py` validates `merged_dataset.csv` against `contracts/dataset.schema.yaml`.
    - `analyze.py` validates `analysis_summary.json` against `contracts/analysis_output.schema.yaml`.