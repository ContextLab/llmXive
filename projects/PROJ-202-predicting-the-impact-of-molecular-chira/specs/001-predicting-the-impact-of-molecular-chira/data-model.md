# Data Model: Predicting the Impact of Molecular Chirality on Flavor Perception

## Overview

This document defines the data structures, schemas, and file formats used in the project. All data is stored in `data/` and validated against the schemas in `contracts/`.

## Data Flow

1. **Raw Data**: Downloaded from HuggingFace (SMILES, AlphaFold PDB).  
2. **Manual Data**: `data/manual_enantiomer_ratings.csv` (curated sensory differences).  
3. **Processed Data**:  
   - 3D conformers (SDF)  
   - Docking results (CSV)  
   - MD trajectories (PDB/DCD)  
   - Statistical results (CSV)  
   - Experimental binding lookup (CSV)  

## Entity Definitions

### Enantiomeric Pair
- **ID**: Unique compound identifier (e.g., `CHEM-001`).  
- **SMILES_R**: Right‑handed enantiomer SMILES.  
- **SMILES_L**: Left‑handed enantiomer SMILES.  
- **Flavor_Name**: Common name (e.g., “Carvone”).  
- **Sensory_Rating_R**: Human rating for R‑enantiomer (numeric, optional).  
- **Sensory_Rating_L**: Human rating for L‑enantiomer (numeric, optional).  
- **Rating_Source**: `"Manual"` (literature) or `"FlavorDB"` (if available).  
- **Distinct_Profile_Flag**: Binary (1 = distinct sensory profiles, 0 = no known difference).

### Receptor Complex
- **Receptor_ID**: AlphaFold model identifier.  
- **pLDDT**: Confidence score (filtered ≥ 70).  
- **Ligand_ID**: Reference to Enantiomeric Pair.  
- **Enantiomer_Type**: `"R"` or `"L"`.  
- **Docking_Score_Vina**: kcal/mol.  
- **Docking_Score_SMINA**: kcal/mol (optional, present for top 5 pairs).  
- **Docking_Score_PLANTS**: kcal/mol (optional, present for top 5 pairs).  
- **RMSD**: Ångströms.  
- **MD_Stability**: Boolean (stable if avg RMSD < 2.0 Å over 100 ps).  
- **Interaction_Fingerprint**: JSON‑encoded hash of interaction counts.

### ExperimentalBinding
- **Ligand_ID**: Reference to Enantiomeric Pair.  
- **Receptor_ID**: Reference to Receptor Complex.  
- **Experimental_Kd**: Numeric (µM) – optional.  
- **Source**: `"BindingDB"` or `"Literature"`.

## File Formats

### `data/raw/smiles.parquet`
- Source: Verified HuggingFace URL.  
- Columns: `smiles`, `compound_id`.

### `data/raw/alphafold.tar.gz`
- Source: Verified HuggingFace URL.  
- Contains PDB files of AlphaFold models.

### `data/manual_enantiomer_ratings.csv`
- **Purpose**: Manually curated sensory ratings for the selected pairs.  
- Columns: `compound_id`, `enantiomer_type`, `sensory_rating`, `rating_source`, `distinct_profile_flag`.

### `data/processed/docking_results.csv`
- Format: CSV.  
- Columns: `receptor_id`, `ligand_id`, `enantiomer_type`, `binding_affinity_vina`, `binding_affinity_smina`, `binding_affinity_plants`, `rmsd`, `timestamp`.

### `data/processed/md_summary.csv`
- Format: CSV.  
- Columns: `complex_id`, `simulation_time_ps`, `avg_rmsd`, `h_bond_count`, `hydrophobic_count`.

### `data/processed/statistical_analysis.csv`
- Format: CSV.  
- **One row per sensitivity threshold** (0.4, 0.5, 0.6 kcal/mol).  
- Columns: `test_type`, `p_value`, `adjusted_p_value`, `effect_size`, `threshold_kcal_mol`, `significant_count`, `bootstrap_iterations`, `bootstrap_ci_lower`, `bootstrap_ci_upper`.

### `data/processed/experimental_comparison.csv`
- Format: CSV.  
- Columns: `ligand_id`, `receptor_id`, `computed_affinity`, `experimental_kd`, `source`.