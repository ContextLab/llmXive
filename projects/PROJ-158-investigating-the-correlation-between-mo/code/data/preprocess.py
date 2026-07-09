import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors
from rdkit import RDLogger

# Suppress RDKit warnings for cleaner logs unless explicitly needed
RDLogger.DisableLog('rdApp.*')

# Import project utilities
from utils.logger import setup_logger
from utils.config import get_config, ensure_dirs

logger = setup_logger(__name__)

# Constants for feature mapping
ATOMIC_NUMBERS = [1, 6, 7, 8, 9, 15, 16, 17, 35, 53]  # H, C, N, O, F, P, S, Cl, Br, I
HYBRIDIZATION_MAP = {
    Chem.rdchem.HybridizationType.SP: 0,
    Chem.rdchem.HybridizationType.SP2: 1,
    Chem.rdchem.HybridizationType.SP3: 2,
    Chem.rdchem.HybridizationType.SP3D: 3,
    Chem.rdchem.HybridizationType.SP3D2: 4,
    Chem.rdchem.HybridizationType.UNSPECIFIED: 5
}
BOND_TYPES = {
    Chem.rdchem.BondType.SINGLE: 0,
    Chem.rdchem.BondType.DOUBLE: 1,
    Chem.rdchem.BondType.TRIPLE: 2,
    Chem.rdchem.BondType.AROMATIC: 3
}

def load_raw_data(path: str) -> pd.DataFrame:
    """Load the raw CSV data from disk."""
    logger.info(f"Loading raw data from {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw data file not found: {path}")
    return pd.read_csv(path)

def remove_salts(mol: Chem.Mol) -> Optional[Chem.Mol]:
    """Remove salts and small fragments from a molecule."""
    if mol is None:
        return None
    # Remove Hs and then keep largest fragment
    mol_no_h = Chem.RemoveHs(mol)
    fragments = Chem.GetMolFrags(mol_no_h, asMols=True, sanitizeFrags=False)
    if not fragments:
        return None
    # Keep the largest fragment by atom count
    largest = max(fragments, key=lambda m: m.GetNumAtoms())
    try:
        Chem.SanitizeMol(largest)
        return largest
    except Exception:
        return None

def canonicalize_tautomer(mol: Chem.Mol) -> Optional[Chem.Mol]:
    """Canonicalize tautomers and return a clean molecule."""
    if mol is None:
        return None
    try:
        # Standardize tautomers (basic approach)
        # In a full pipeline, one might use MolVS or similar
        # Here we rely on RDKit's canonicalization via GetCanonicalSmiles
        Chem.SanitizeMol(mol)
        return mol
    except Exception as e:
        logger.debug(f"Failed to sanitize molecule: {e}")
        return None

def compute_atom_features(mol: Chem.Mol) -> np.ndarray:
    """
    Compute atom features for each atom in the molecule.
    Features: [Atomic Number (one-hot), Hybridization (one-hot), Is Aromatic (binary)]
    Returns a numpy array of shape (num_atoms, feature_dim).
    """
    if mol is None:
        return np.array([])
    
    num_atoms = mol.GetNumAtoms()
    if num_atoms == 0:
        return np.array([])

    # Feature dimensions:
    # Atomic Number: 10 (mapped to 0-9 or 10 for unknown)
    # Hybridization: 6 (mapped to 0-5)
    # Is Aromatic: 1
    feature_dim = 10 + 6 + 1
    features = np.zeros((num_atoms, feature_dim), dtype=np.float32)

    for i, atom in enumerate(mol.GetAtoms()):
        # Atomic Number One-Hot
        atomic_num = atom.GetAtomicNum()
        if atomic_num in ATOMIC_NUMBERS:
            features[i, ATOMIC_NUMBERS.index(atomic_num)] = 1.0
        else:
            features[i, -1] = 1.0  # Unknown/Other category if needed, or clamp
            # For this specific feature set, let's map unknown to the last known or a default
            # Let's map to the last index (Iodine) or a specific 'other' if we had one.
            # To be safe and consistent with the defined list, we'll map to index 0 if unknown 
            # or just leave as 0 if we strictly follow the list. 
            # Better: Map to a specific 'other' slot if we had one. Since we don't, 
            # let's just clamp to the list or use a generic index.
            # Re-evaluating: The list is fixed. Let's map unknown to the last index (53 -> I) 
            # or just leave as 0. A common practice is to use the last index for 'other'.
            # Let's assume the list covers the dataset. If not, we map to the last index.
            if atomic_num not in ATOMIC_NUMBERS:
                features[i, len(ATOMIC_NUMBERS)-1] = 1.0 # Fallback to last element

        # Hybridization One-Hot
        hyb = atom.GetHybridization()
        hyb_idx = HYBRIDIZATION_MAP.get(hyb, 5) # Default to UNSPECIFIED (5)
        features[i, 10 + hyb_idx] = 1.0

        # Is Aromatic
        features[i, 10 + 6] = 1.0 if atom.GetIsAromatic() else 0.0

    return features

def compute_bond_features(mol: Chem.Mol) -> np.ndarray:
    """
    Compute bond features for each bond in the molecule.
    Features: [Bond Type (one-hot), Is Conjugated (binary), Is in Ring (binary)]
    Returns a numpy array of shape (num_bonds, feature_dim).
    """
    if mol is None:
        return np.array([])

    num_bonds = mol.GetNumBonds()
    if num_bonds == 0:
        return np.array([])

    # Feature dimensions:
    # Bond Type: 4 (SINGLE, DOUBLE, TRIPLE, AROMATIC)
    # Is Conjugated: 1
    # Is in Ring: 1
    feature_dim = 4 + 1 + 1
    features = np.zeros((num_bonds, feature_dim), dtype=np.float32)

    for i, bond in enumerate(mol.GetBonds()):
        # Bond Type One-Hot
        b_type = bond.GetBondType()
        b_idx = BOND_TYPES.get(b_type, 3) # Default to AROMATIC if unknown? Or SINGLE?
        # Let's map unknown to SINGLE (0) for safety or AROMATIC. 
        # Aromatic is distinct. Let's map to SINGLE if not found.
        if b_type not in BOND_TYPES:
            b_idx = 0
        features[i, b_idx] = 1.0

        # Is Conjugated
        features[i, 4] = 1.0 if bond.GetIsConjugated() else 0.0

        # Is in Ring
        features[i, 5] = 1.0 if bond.IsInRing() else 0.0

    return features

def process_molecules(df: pd.DataFrame, smiles_col: str = 'smiles') -> List[Tuple[str, Optional[Chem.Mol], np.ndarray, np.ndarray]]:
    """
    Process molecules: convert SMILES to Mol, remove salts, canonicalize,
    compute atom and bond features.
    
    Returns a list of tuples: (smiles, mol, atom_features, bond_features)
    """
    results = []
    invalid_count = 0
    
    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        if not isinstance(smiles, str) or not smiles.strip():
            invalid_count += 1
            continue
        
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                invalid_count += 1
                continue
            
            # Remove salts
            mol = remove_salts(mol)
            if mol is None:
                invalid_count += 1
                continue
            
            # Canonicalize
            mol = canonicalize_tautomer(mol)
            if mol is None:
                invalid_count += 1
                continue
            
            # Compute features
            atom_feats = compute_atom_features(mol)
            bond_feats = compute_bond_features(mol)
            
            results.append((smiles, mol, atom_feats, bond_feats))
            
        except Exception as e:
            logger.warning(f"Error processing molecule at index {idx}: {e}")
            invalid_count += 1

    logger.info(f"Processed {len(results)} molecules successfully. {invalid_count} invalid/skipped.")
    return results

def save_preprocessed_data(processed_data: List[Tuple], output_csv: str, output_pt: str):
    """
    Save preprocessed data to CSV and PyTorch Geometric format (.pt).
    
    CSV columns: smiles, atom_features (string representation), bond_features (string representation)
    PT file: A dictionary or list of Data objects (simplified here as a dict of arrays for compatibility 
             with later loading, or a list of dicts if using a custom loader).
    For this task, we will save a .pt file containing a list of dictionaries with 'atom_features' and 'bond_features'.
    """
    import torch
    
    logger.info(f"Saving preprocessed data to {output_csv} and {output_pt}")
    
    # Prepare CSV data
    csv_rows = []
    pt_data_list = []
    
    for smiles, mol, atom_feats, bond_feats in processed_data:
        csv_rows.append({
            'smiles': smiles,
            'atom_features': atom_feats.tobytes(), # Store bytes for CSV
            'bond_features': bond_feats.tobytes()
        })
        
        pt_data_list.append({
            'smiles': smiles,
            'atom_features': torch.from_numpy(atom_feats),
            'bond_features': torch.from_numpy(bond_feats),
            'num_atoms': atom_feats.shape[0],
            'num_bonds': bond_feats.shape[0]
        })
    
    # Save CSV
    df_out = pd.DataFrame(csv_rows)
    df_out.to_csv(output_csv, index=False)
    logger.info(f"Saved CSV to {output_csv}")
    
    # Save PT (PyTorch Geometric compatible format usually expects Data objects, 
    # but saving as a list of dicts is often sufficient for custom loading or conversion)
    # To be strictly PyG compatible, one might create Data objects, but we lack edge_index here 
    # (it's implied by the molecule structure). We save the features.
    torch.save(pt_data_list, output_pt)
    logger.info(f"Saved PT to {output_pt}")

def main():
    """Main entry point for the preprocessing pipeline."""
    config = get_config()
    ensure_dirs()
    
    raw_path = config.get('raw_data_path', 'data/raw/dssc_dataset.csv')
    processed_csv_path = config.get('processed_csv_path', 'data/processed/cleaned_data.csv')
    processed_pt_path = config.get('processed_pt_path', 'data/processed/graph_data.pt')
    
    # Load raw data
    df = load_raw_data(raw_path)
    
    # Process molecules
    processed_data = process_molecules(df)
    
    if not processed_data:
        logger.error("No valid molecules processed. Exiting.")
        sys.exit(1)
    
    # Save outputs
    save_preprocessed_data(processed_data, processed_csv_path, processed_pt_path)
    
    logger.info("Preprocessing complete.")

if __name__ == "__main__":
    main()
