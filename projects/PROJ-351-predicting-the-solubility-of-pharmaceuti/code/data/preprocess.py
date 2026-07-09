import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem
import pandas as pd
import numpy as np

# Setup logging
logger = logging.getLogger(__name__)

# --- Feature Extraction Constants (from API surface context) ---
# Atom features: Atomic number, degree, num_h, formal_charge, num_radical_electrons, hybridization, is_aromatic
ATOM_FEATURES = {
    'atomic_num': list(range(1, 120)), # 0 to 119
    'degree': [0, 1, 2, 3, 4, 5, 6],
    'formal_charge': [-1, -2, 1, 2, 0],
    'num_radical_electrons': [0, 1, 2, 3, 4],
    'hybridization': [
        Chem.HybridizationType.SP,
        Chem.HybridizationType.SP2,
        Chem.HybridizationType.SP3,
        Chem.HybridizationType.SP3D,
        Chem.HybridizationType.SP3D2
    ],
    'is_aromatic': [False, True]
}

# Bond features: Bond type, conjugation, ring, stereo
BOND_FEATURES = {
    'bond_type': [
        Chem.BondType.SINGLE,
        Chem.BondType.DOUBLE,
        Chem.BondType.TRIPLE,
        Chem.BondType.AROMATIC
    ],
    'is_conjugated': [False, True],
    'is_in_ring': [False, True],
    'stereo': [
        Chem.BondStereo.STEREONONE,
        Chem.BondStereo.STEREOANY,
        Chem.BondStereo.STEREOZ,
        Chem.BondStereo.STEREOE,
        Chem.BondStereo.STEREOCIS,
        Chem.BondStereo.STEREOTRANS
    ]
}

# --- Helper Functions ---

def get_atom_features(atom: Any) -> List[int]:
    """
    Extracts a feature vector for a single atom.
    Returns a list of one-hot encoded indices for each feature dimension.
    """
    features = []

    # Atomic Number
    atomic_num = atom.GetAtomicNum()
    try:
        features.append(ATOM_FEATURES['atomic_num'].index(atomic_num))
    except ValueError:
        features.append(len(ATOM_FEATURES['atomic_num']) - 1) # OOV

    # Degree
    degree = atom.GetDegree()
    try:
        features.append(ATOM_FEATURES['degree'].index(degree))
    except ValueError:
        features.append(len(ATOM_FEATURES['degree']) - 1)

    # Formal Charge
    f_charge = atom.GetFormalCharge()
    try:
        features.append(ATOM_FEATURES['formal_charge'].index(f_charge))
    except ValueError:
        features.append(len(ATOM_FEATURES['formal_charge']) - 1)

    # Radical Electrons
    rad_e = atom.GetNumRadicalElectrons()
    try:
        features.append(ATOM_FEATURES['num_radical_electrons'].index(rad_e))
    except ValueError:
        features.append(len(ATOM_FEATURES['num_radical_electrons']) - 1)

    # Hybridization
    hyb = atom.GetHybridization()
    try:
        features.append(ATOM_FEATURES['hybridization'].index(hyb))
    except ValueError:
        features.append(len(ATOM_FEATURES['hybridization']) - 1)

    # Is Aromatic
    is_arom = atom.GetIsAromatic()
    try:
        features.append(ATOM_FEATURES['is_aromatic'].index(is_arom))
    except ValueError:
        features.append(len(ATOM_FEATURES['is_aromatic']) - 1)

    return features

def get_bond_features(bond: Any) -> List[int]:
    """
    Extracts a feature vector for a single bond.
    """
    features = []

    # Bond Type
    b_type = bond.GetBondType()
    try:
        features.append(BOND_FEATURES['bond_type'].index(b_type))
    except ValueError:
        features.append(len(BOND_FEATURES['bond_type']) - 1)

    # Conjugation
    is_conj = bond.GetIsConjugated()
    try:
        features.append(BOND_FEATURES['is_conjugated'].index(is_conj))
    except ValueError:
        features.append(len(BOND_FEATURES['is_conjugated']) - 1)

    # In Ring
    in_ring = bond.IsInRing()
    try:
        features.append(BOND_FEATURES['is_in_ring'].index(in_ring))
    except ValueError:
        features.append(len(BOND_FEATURES['is_in_ring']) - 1)

    # Stereo
    stereo = bond.GetStereo()
    try:
        features.append(BOND_FEATURES['stereo'].index(stereo))
    except ValueError:
        features.append(len(BOND_FEATURES['stereo']) - 1)

    return features

def process_molecule(smiles: str, logS: float) -> Optional[Dict[str, Any]]:
    """
    Parses a SMILES string into a graph representation.
    Returns a dictionary with node features, edge indices, edge features, and target.
    Returns None if the SMILES is invalid.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    # Ensure hydrogens are implicit (RDKit handles this, but good practice)
    mol = Chem.AddHs(mol) # Add explicit Hs for better graph representation if needed, 
                          # but standard GNNs often use implicit Hs. 
                          # For ESOL, standard RDKit MolFromSmiles is usually sufficient.
    # Revert to standard for simplicity unless explicit Hs are required by specific GNN architecture
    # mol = Chem.MolFromSmiles(smiles) 

    num_nodes = mol.GetNumAtoms()
    
    # Node Features: (N, F)
    node_features = []
    for atom in mol.GetAtoms():
        node_features.append(get_atom_features(atom))
    
    node_features = np.array(node_features, dtype=np.int32)

    # Edges: (2, E) and Edge Features (E, F)
    edge_indices = []
    edge_features = []

    # Add bidirectional edges for undirected graph
    for bond in mol.GetBonds():
        start = bond.GetBeginAtomIdx()
        end = bond.GetEndAtomIdx()
        
        feat = get_bond_features(bond)
        
        edge_indices.append([start, end])
        edge_features.append(feat)
        
        edge_indices.append([end, start])
        edge_features.append(feat) # Symmetric

    # Handle molecules with no bonds (single atom)
    if not edge_indices:
        # Create a self-loop or handle as isolated node depending on GNN impl
        # For now, create a dummy self-loop if needed, but usually GNNs handle isolated nodes
        pass

    edge_indices = np.array(edge_indices, dtype=np.int32).T # (2, E)
    edge_features = np.array(edge_features, dtype=np.int32)

    return {
        'smiles': smiles,
        'logS': logS,
        'num_nodes': num_nodes,
        'node_features': node_features.tolist(),
        'edge_index': edge_indices.tolist(),
        'edge_features': edge_features.tolist()
    }

def load_and_preprocess(input_path: str, output_dir: str) -> Dict[str, int]:
    """
    Loads the raw CSV, validates SMILES and logS, processes molecules,
    and saves the cleaned graphs to the output directory.
    Returns a dictionary of exclusion counts.
    """
    logger.info(f"Loading raw data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Raw data file not found: {input_path}")

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows.")

    # Validate columns
    if 'smiles' not in df.columns or 'logS' not in df.columns:
        # ESOL dataset usually has 'smiles' and 'measured logS' or similar
        # Check for common variations
        cols = df.columns.tolist()
        if 'smiles' not in cols and 'SMILES' in cols:
            df['smiles'] = df['SMILES']
        if 'logS' not in cols and 'measured logS' in cols:
            df['logS'] = df['measured logS']
        
        if 'smiles' not in df.columns or 'logS' not in df.columns:
            raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")

    # Filter NaN logS
    initial_count = len(df)
    df = df.dropna(subset=['logS'])
    nan_logS_count = initial_count - len(df)
    logger.info(f"Excluded {nan_logS_count} rows with NaN logS.")

    # Filter Invalid SMILES
    valid_indices = []
    invalid_smiles_count = 0
    processed_data = []

    for idx, row in df.iterrows():
        smiles = str(row['smiles'])
        logS = float(row['logS'])
        
        graph = process_molecule(smiles, logS)
        if graph is not None:
            processed_data.append(graph)
            valid_indices.append(idx)
        else:
            invalid_smiles_count += 1
    
    logger.info(f"Excluded {invalid_smiles_count} rows with invalid SMILES.")
    logger.info(f"Successfully processed {len(processed_data)} molecules.")

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save processed data as JSON
    output_file = output_path / "processed_graphs.json"
    logger.info(f"Saving processed graphs to {output_file}")
    
    with open(output_file, 'w') as f:
        json.dump(processed_data, f)

    return {
        'initial_rows': initial_count,
        'nan_logS_excluded': nan_logS_count,
        'invalid_smiles_excluded': invalid_smiles_count,
        'final_rows': len(processed_data)
    }

def main():
    """
    Main entry point for the preprocessing script.
    Expects raw data at data/raw/esol.csv and outputs to data/processed/
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/logs/preprocess.log')
        ]
    )

    # Paths
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_data_path = project_root / "data" / "raw" / "esol.csv"
    processed_dir = project_root / "data" / "processed"

    if not raw_data_path.exists():
        logger.error(f"Raw data file not found at {raw_data_path}. Please run download_esol.py first.")
        sys.exit(1)

    try:
        stats = load_and_preprocess(str(raw_data_path), str(processed_dir))
        logger.info("Preprocessing completed successfully.")
        logger.info(f"Stats: {stats}")
        
        # Log exclusion counts to the logging infrastructure if available
        # Assuming setup_logging is configured elsewhere or we just log to file
        with open(project_root / "data" / "logs" / "preprocessing_stats.json", 'w') as f:
            json.dump(stats, f, indent=2)
            
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()