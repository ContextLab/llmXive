# Data Model: Predicting Molecular Ionization Energies

## Key Entities

### 1. MoleculeGraph
Represents a 2‑dimensional molecular graph derived from SMILES.
- **Nodes**
  - `atom_type` (int): Element atomic number (e.g., C = 6).
  - `formal_charge` (int)
  - `is_aromatic` (bool)
  - `num_hydrogens` (int)
- **Edges**
  - `bond_type` (int): 1 = single, 2 = double, 3 = triple, 4 = aromatic.
  - `is_conjugated` (bool)
  - `stereo` (int): 0 = none, 1 = cis, 2 = trans.
- **Connectivity**: PyTorch Geometric `edge_index` (source, target) plus `edge_attr`.

### 2. IonizationEnergyTarget (Proxy)
- `negative_homo_proxy` (float, eV): `-homo_au * 27.2114` (conversion from atomic units).  
- **Source**: QM9 `HOMO_au` column.  
- **Note**: Approximation per Koopmans’ theorem; systematic bias documented in Phase 0.

### 3. AblationConfig
- `feature` (string): e.g., `"bond_type"`.  
- `perturbation_type` (string): `"zeroing"` (features set to zero during training).  
- `sigma` (float, optional): N/A for zeroing.

### 4. AttributionMap
- `indices` (list[int]): Atom or bond indices.  
- `scores` (list[float]): Integrated Gradients magnitudes.  
- `validation` (string): Description of validation method (e.g., qualitative check against known chemical intuition).  
- `normalization` (string): `"min-max"` or `"l2"`.  
- `algorithm` (string, const): `"Integrated Gradients"` (defined in `model_output.schema.yaml`).

## Model Architecture Definition (Single Source of Truth)
- **Type**: Graph Convolutional Network (GCN) – CPU‑compatible.  
- **Input**: `MoleculeGraph` (node + edge features).  
- **Layers**: 3 GCN layers.  
- **Hidden Dimension**: 64.  
- **Node Embedding**: Linear → 64‑dim.  
- **Edge Embedding**: Linear → 32‑dim.  
- **Readout**: Global average pooling → MLP (64 → 1).  
- **Activation**: ReLU after each GCN layer and MLP hidden layer.  
- **Optimizer**: Adam (lr = 0.001).  
- **Loss**: Mean Squared Error (MSE).  
- **Precision**: Float32 (CPU).  
- **Recorded in**: `models/mpnn.py` and referenced by all contracts (FR‑021).

## Data Flow
1. **Ingestion** – `download.py` fetches QM9 via `qm9pack` → raw DataFrame.  
2. **Preprocess** – `preprocess.py` converts SMILES → RDKit Mol → `MoleculeGraph` (PyG `Data`).  
3. **Target Derivation** – `-homo_au * 27.2114` → `IonizationEnergyTarget.negative_homo_proxy`.  
4. **Split** – `split.py` creates scaffold‑based train/val/test assignments (FR‑004) and performs a **post‑hoc covariate balance check** (molecular weight, rotatable bonds); if imbalance > 10 % a stratified re‑split is triggered.  
5. **Training** – `train.py` consumes `train_loader`, updates MPNN, monitors RAM, respects timeout.  
6. **Evaluation** – `evaluate.py` computes metrics, attribution, statistical tests, and writes JSON/CSV conforming to contracts.

## Storage Formats
- **Raw QM9**: Parquet (`data/raw/qm9.parquet`).  
- **Processed Graphs**: PyTorch Geometric `Data` objects serialized as `.pt` files (`data/processed/graphs.pt`).  
- **Splits**: Index lists saved as `data/splits/{train,val,test}.pt`.  
- **Checkpoints**: `code/models/best_model.pth`.  
- **Results**: `results/metrics.csv`, `results/attribution.json`, `results/ablation.json`.  

## Attribution Subset Note
Integrated Gradients attribution maps are generated for a **representative subset of 1 000 test molecules** (stratified by scaffold) to keep CPU runtime within the predefined time limit. The `AttributionMap` entity applies to this subset; full‑set attribution can be generated offline if needed.

## Pairing Strategy for Paired Tests
Each baseline run and its perturbed counterpart share the **same random seed** (recorded in `utils/config.py`). This ensures that per‑molecule absolute errors are directly comparable, satisfying the independence assumptions of the paired t‑test (or Wilcoxon signed‑rank test).
