# Data Model: Predicting Molecular Interactions in Protein-Ligand Complexes

## Entity Definitions

### MolecularGraph
Represents a single protein-ligand complex.
- **nodes**: List of atom objects.
  - `atom_type`: String (e.g., "C", "N", "O", "unknown").
  - `charge`: Float.
  - `coordinates`: List of 3 floats [x, y, z] in Angstroms.
  - `hydrophobicity`: Float.
- **edges**: List of edge objects.
  - `source`: Integer (node index).
  - `target`: Integer (node index).
  - `bond_type`: String (covalent, non-covalent).
  - `distance`: Float (Angstroms).
- **global_properties**:
  - `pKd`: Float (binding affinity).
  - `resolution`: Float (Angstroms).
  - `complex_id`: String.
  - `water_flag`: Boolean (True if water-mediated interaction detected per FR-009).

### SubstructureCluster
Represents a group of high-importance substructures.
- `cluster_id`: Integer.
- `centroid_coordinates`: List of 3 floats.
- `member_count`: Integer.
- `pharmacophore_id`: String (or null if no match).
- `rmsd`: Float (RMSD to matched pharmacophore).
- `p_value_ttest`: Float (p-value from two-sample t-test per Constitution VII).
- `p_value_perm`: Float (p-value from permutation test).
- `is_significant`: Boolean (after FDR correction).
- `alignment_method`: String (e.g., "Procrustes").

### FeatureImportanceMap
Maps atoms to their attribution scores.
- `atom_index`: Integer.
- `score`: Float.
- `interaction_type`: String (e.g., "hydrogen_bond", "hydrophobic").
- `baseline_score`: Float (score from ablation baseline).

## Data Flow

1. **Raw Data**: PDBbind v2020 tarball (streamed/downloaded with checksum).
2. **Processed Data**: `MolecularGraph` objects saved to `data/processed/graphs/`.
3. **Model Output**: Predicted pKd values and `FeatureImportanceMap`.
4. **Analysis Output**: `SubstructureCluster` objects saved to `data/results/motifs.json`.

## Constraints

- **Memory**: Total loaded graph data must remain within a feasible memory footprint.
- **Resolution**: Complexes with resolution > 2.5 Å are excluded.
- **Missing Data**: Unknown atom types mapped to "unknown" with zeroed features.
- **Water Flag**: `water_flag` must be set if distance < 3.5 Å to oxygen atoms (FR-009).