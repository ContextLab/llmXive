# Data Model: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Overview

This document defines the data entities, schemas, and transformation logic for the project. All data flows from raw OQMD/MP bulk configurations to processed GB descriptors and simulated energies, finally aggregating into a training dataset.

## Entity Definitions

### 1. BulkConfiguration
Represents a raw bulk crystal structure from OQMD/MP.
- **id**: Unique identifier (e.g., OQMD material ID or MP ID).
- **formula**: Chemical formula (e.g., "FeSi").
- **lattice**: Lattice parameters (a, b, c, alpha, beta, gamma).
- **atoms**: List of atomic species and coordinates.
- **source_url**: URL of the OQMD/MP entry.
- **source_type**: Enum ["OQMD", "MaterialsProject"].

### 2. GrainBoundaryStructure
Represents a constructed GB supercell.
- **id**: Unique ID (generated).
- **bulk_id**: Reference to `BulkConfiguration`.
- **boundary_plane**: Miller indices (hkl).
- **misorientation_angle**: Angle in degrees.
- **supercell_atoms**: Atoms in the supercell (bulk + interface).
- **interface_region_mask**: Boolean mask identifying atoms in the GB interface region.

### 3. ClusteringDescriptor
Computed metrics for impurity clustering at the interface.
- **gb_id**: Reference to `GrainBoundaryStructure`.
- **impurity_species**: Element symbol (e.g., "Si").
- **descriptor_type**: Enum ["rdf_peak", "pair_correlation", "voronoi_count"].
- **value**: Numeric value.
- **interface_only**: Boolean (true, computed only within interface region).
- **principal_component**: Numeric value (after PCA transformation).

### 4. Covariate
Additional features to control for confounding.
- **gb_id**: Reference to `GrainBoundaryStructure`.
- **local_lattice_strain**: Numeric value (trace of strain tensor).
- **atomic_radius**: Numeric value (from periodic table).
- **electronegativity**: Numeric value (from periodic table).

### 5. SegregationEnergy
Simulated thermodynamic driving force.
- **gb_id**: Reference to `GrainBoundaryStructure`.
- **impurity_species**: Element symbol.
- **energy_eV**: Segregation energy in eV (calculated via Leave-One-Out).
- **potential_used**: String (e.g., "NIST_EAM_FeCr_v1").
- **simulation_time_s**: Wall-clock time for simulation.
- **simulation_status**: Enum ["SUCCESS", "FAILED", "RETRY_EXHAUSTED"].

### 6. TrainingSample
Aggregated row for regression.
- **sample_id**: Unique ID.
- **features**: Vector of descriptors (PCA-transformed RDF, PC, Voronoi) + covariates.
- **target**: Segregation energy (eV).
- **alloy_system**: Alloy family (e.g., "Fe-Cr").
- **vif_scores**: Dict of VIF scores for each feature.
- **descriptive_framing**: String (pre-formatted text for VIF >= 10).

## Data Flow

1.  **Ingestion**: `download.py` fetches OQMD/MP bulk configs → `data/raw/bulk.csv`.
    *   *Validation*: `validate_citations()` checks source URL.
2.  **Construction**: `gb_builder.py` reads bulk, constructs GBs → `data/processed/gb_structures.json`.
3.  **Descriptor Calc**: `descriptors.py` reads GBs, computes interface metrics → `data/processed/descriptors.csv`.
    *   *Preprocessing*: Apply PCA to descriptors.
4.  **Simulation**: `simulate_energy.py` reads GBs, computes energy → `data/processed/energies.csv`.
    *   *Retry*: Up to 3 retries.
5.  **Aggregation**: `train_model.py` joins descriptors, covariates, and energies → `data/processed/training_set.csv`.
    *   *Power Analysis*: Loop to determine sample size.
6.  **Output**: Metrics and plots → `results/`.

## Data Hygiene & Provenance

- **Checksums**: Every file in `data/raw/` and `data/processed/` is checksummed (SHA-256).
- **Immutability**: Raw data is never modified. Derivations create new files.
- **Metadata**: `data/metadata.yaml` tracks:
  - Source URLs (OQMD/MP).
  - Simulation parameters (potential: "NIST_EAM_FeCr_v1", cutoff).
  - Random seeds.
  - Code version hash.
  - `validate_citations()` results.

## Constraints & Validation

- **Missing Data**: Entries with missing segregation energy are excluded (logged).
- **Zero Impurity**: Bulk configs with no impurities are filtered (logged).
- **Collinearity**: VIF ≥ 10 triggers a descriptive framing string, not removal.
- **Units**: Energy in eV; distances in Å.
- **Potential**: Default potential string is "NIST_EAM_FeCr_v1".
- **Covariates**: Local lattice strain and species properties are computed and included.
- **PCA**: Descriptors are PCA-transformed to ensure orthogonality.
- **Validation**: Ground truth DFT subset is used to validate potential before full training.