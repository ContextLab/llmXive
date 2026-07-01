# Data Model: Predicting Molecular Interactions in Polymer Composites with Graph Neural Networks

## Entities

### 1. MolecularGraph
Represents a single molecule (polymer chain or filler particle) derived from SMILES.

- **Nodes**
  - `atom_type`: String (e.g., "C", "O", "N", "Si")
  - `charge`: Float (default 0.0)
  - `hybridization`: String (e.g., "sp2", "sp3")
- **Edges**
  - `bond_type`: String (e.g., "single", "double", "aromatic")
  - `bond_order`: Float
  - `is_interaction`: Boolean (True for non‑covalent polymer‑filler interactions)

### 2. InterfacePair
Represents a polymer‑filler interface with two MolecularGraph entities.

- `pair_id`: String (unique)
- `polymer_smiles`: String
- `filler_smiles`: String
- `adhesion_energy`: Number (eV or kcal/mol) – **required**
- `source`: String (e.g., "MolNet", "Literature")
- `missing_flags`: Array[String] (columns with >5 % missing)

### 3. TrainedGCN (actually a GAT)
Artifact storing the trained model.

- `weights`: Binary (`.pt` file)
- `architecture_config`: JSON (layers, hidden dims, dropout, attention heads)
- `training_stats`: JSON (final loss, epochs, runtime, peak memory)
- `random_seed`: Integer

### 4. ResultsCSV
Tabular summary of statistical outcomes.

- `metric`: String (e.g., "MSE", "MAE")
- `observed_value`: Number
- `p_value`: Number
- `corrected_p_value`: Number (Bonferroni/Holm if >1 metric)
- `vif_scores`: Object (key = descriptor name, value = VIF)

## Data Flow

1. **Raw Ingestion** – `data/raw/molecular_graphs.csv` (MolNet)  
2. **Cleaning** – `data/curated/curated_dataset.csv` (validated, missing‑value flags)  
3. **Graph Construction** – `data/processed/graphs.pt` (PyG Data objects)  
4. **Training** – `results/model.pt` (trained GAT)  
5. **Statistical Analysis** – `results/stats.csv` (ResultsCSV)  
6. **Audit** – `analysis/topology_audit.md`

## Constraints

- **Missing Data**: Any predictor column with >5 % missing triggers a warning; the column is excluded unless manually imputed. `adhesion_energy` must be present; otherwise the pipeline aborts with **E‑DATA‑001**.
- **Variable Integrity**: All predictor variables (atom types, bond types, handcrafted descriptors) and the outcome variable must be non‑null after cleaning.
- **Graph Consistency**: Node and edge attribute schemas are enforced across the entire batch.
