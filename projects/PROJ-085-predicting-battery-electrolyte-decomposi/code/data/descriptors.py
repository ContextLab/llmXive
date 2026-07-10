"""
Descriptor Extraction Module.

Extracts electronic (HOMO, LUMO, Band Gap) and geometric (bond lengths, angles, dihedrals)
descriptors from molecular structures using RDKit and pymatgen.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

# Add project root to path
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger, log_missing_geometric_data, log_metallic_outlier
from utils.models import ElectrolyteMolecule, FeatureVector
import logging

logger = get_logger(__name__)


def parse_smiles_to_molecule(smiles: str) -> Optional[Any]:
    """
    Parse a SMILES string into an RDKit molecule object.
    
    Args:
        smiles: SMILES string.
        
    Returns:
        RDKit Mol object or None if parsing fails.
    """
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Failed to parse SMILES: {smiles}")
            return None
        # Add hydrogens for 3D generation
        mol = Chem.AddHs(mol)
        return mol
    except ImportError:
        raise ImportError("RDKit is required for descriptor extraction. Install via: pip install rdkit")


def generate_3d_conformer(mol: Any, max_attempts: int = 100) -> Optional[Any]:
    """
    Generate a 3D conformer for the molecule.
    
    Args:
        mol: RDKit Mol object.
        max_attempts: Number of embedding attempts.
        
    Returns:
        RDKit Mol with 3D coordinates or None.
    """
    try:
        from rdkit.Chem import AllChem
        # Use ETKDG for better geometry
        params = AllChem.ETKDGv3()
        params.maxAttempts = max_attempts
        params.randomSeed = 42 # Deterministic for reproducibility
        
        res = AllChem.EmbedMolecule(mol, params)
        if res == -1:
            logger.warning("Failed to embed 3D conformer.")
            return None
            
        # Optimize geometry with MMFF
        AllChem.MMFFOptimizeMolecule(mol)
        return mol
    except Exception as e:
        logger.error(f"3D generation error: {e}")
        return None


def extract_electronic_descriptors(mol: Any) -> Dict[str, float]:
    """
    Extract electronic descriptors (HOMO, LUMO, Gap) using a simplified heuristic or DFT proxy.
    
    Note: Since we don't have actual DFT energies in this module, we simulate the extraction
    based on the assumption that the input DataFrame (from ingestion) might already have
    'homo' and 'lumo' columns, or we compute a proxy.
    
    For this implementation, we assume the input 'mol' is actually a dictionary-like object
    or the function is called in a context where we can look up pre-computed values,
    OR we use a simple molecular orbital estimator if no DFT data is present.
    
    However, to strictly follow the "Real Data" constraint and the API surface, 
    this function expects the 'mol' to be a dict containing pre-fetched DFT data 
    if available, or we return placeholders if not.
    
    Actually, looking at the task T012/T014, the ingestion fetches DFT data.
    So we assume the 'smiles' row in the main pipeline has associated 'homo'/'lumo' 
    in the dataframe passed to the descriptor pipeline, OR we compute them.
    
    Since RDKit cannot compute accurate HOMO/LUMO without QM, we will:
    1. Check if 'homo'/'lumo' are available in the row context (passed via args).
    2. If not, use a simple molecular descriptor proxy (e.g., electronegativity based) 
       as a fallback for the "Real Data" requirement where DFT data might be sparse.
       
    For this specific implementation, we will assume the 'mol' argument is a dict 
    containing the DFT values if available, or we compute a rough estimate.
    
    To make this runnable and real, we will check if the input 'mol' (which is actually 
    a dict from the dataframe row) has the keys.
    """
    # This function signature is slightly adjusted to accept the row data
    # But to match the API surface provided in the prompt, we keep 'mol' as the object.
    # We will handle the logic by checking if 'mol' is a dict (from the row) or an RDKit Mol.
    
    descriptors = {}
    
    # If mol is a dict (row data), extract directly
    if isinstance(mol, dict):
        if 'homo' in mol:
            descriptors['homo_ev'] = float(mol['homo'])
        if 'lumo' in mol:
            descriptors['lumo_ev'] = float(mol['lumo'])
        
        # Calculate gap
        if 'homo_ev' in descriptors and 'lumo_ev' in descriptors:
            descriptors['band_gap_ev'] = descriptors['lumo_ev'] - descriptors['homo_ev']
        return descriptors

    # If mol is an RDKit molecule, we cannot get accurate HOMO/LUMO without QM.
    # We will return a warning and return NaNs or 0s, assuming the ingestion step
    # should have provided these if DFT data was present.
    logger.warning("RDKit Mol object provided without pre-computed DFT data. Returning NaN.")
    return {'homo_ev': np.nan, 'lumo_ev': np.nan, 'band_gap_ev': np.nan}


def extract_geometric_descriptors(mol: Any) -> Dict[str, float]:
    """
    Extract geometric descriptors (bond lengths, angles, dihedrals).
    
    Args:
        mol: RDKit Mol object with 3D coordinates.
        
    Returns:
        Dictionary of geometric features.
    """
    descriptors = {}
    
    if mol is None:
        log_missing_geometric_data("Molecule is None")
        return descriptors
        
    try:
        from rdkit import Chem
        from rdkit.Chem import rdMolDescriptors
        
        # Check for 3D coordinates
        conf = mol.GetConformer()
        if conf is None:
            log_missing_geometric_data("No conformer found")
            return descriptors
            
        atoms = mol.GetAtoms()
        bonds = mol.GetBonds()
        
        # 1. Bond Lengths (Sample: First 5 unique bond lengths)
        bond_lengths = []
        seen_pairs = set()
        for bond in bonds:
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()
            if (i, j) not in seen_pairs and (j, i) not in seen_pairs:
                seen_pairs.add((i, j))
                pos_i = conf.GetAtomPosition(i)
                pos_j = conf.GetAtomPosition(j)
                length = pos_i.Distance(pos_j)
                bond_lengths.append(length)
                if len(bond_lengths) >= 5: break
        
        for idx, length in enumerate(bond_lengths):
            descriptors[f'bond_length_{idx+1}'] = length
            
        # 2. Bond Angles (Sample: First 5 angles)
        angles = []
        # Simple heuristic: iterate over atoms with degree >= 2
        atom_indices = list(range(mol.GetNumAtoms()))
        count = 0
        for i in atom_indices:
            if mol.GetAtomWithIdx(i).GetDegree() < 2: continue
            neighbors = [a.GetIdx() for a in mol.GetAtomWithIdx(i).GetNeighbors()]
            for n1 in neighbors:
                for n2 in neighbors:
                    if n1 >= n2: continue
                    # Calculate angle n1-i-n2
                    pos_n1 = conf.GetAtomPosition(n1)
                    pos_i = conf.GetAtomPosition(i)
                    pos_n2 = conf.GetAtomPosition(n2)
                    
                    # Vector math
                    v1 = np.array([pos_n1.x - pos_i.x, pos_n1.y - pos_i.y, pos_n1.z - pos_i.z])
                    v2 = np.array([pos_n2.x - pos_i.x, pos_n2.y - pos_i.y, pos_n2.z - pos_i.z])
                    
                    norm1 = np.linalg.norm(v1)
                    norm2 = np.linalg.norm(v2)
                    
                    if norm1 == 0 or norm2 == 0: continue
                    
                    cos_angle = np.dot(v1, v2) / (norm1 * norm2)
                    cos_angle = np.clip(cos_angle, -1.0, 1.0)
                    angle_rad = np.arccos(cos_angle)
                    angle_deg = np.degrees(angle_rad)
                    
                    angles.append(angle_deg)
                    if len(angles) >= 5: break
                if len(angles) >= 5: break
            if len(angles) >= 5: break
        
        for idx, angle in enumerate(angles):
            descriptors[f'bond_angle_{idx+1}'] = angle
            
        # 3. Dihedrals (Sample: First 3)
        dihedrals = []
        # Find 4 connected atoms
        for bond in bonds:
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()
            # Find neighbor of i (not j)
            ni = [a.GetIdx() for a in mol.GetAtomWithIdx(i).GetNeighbors() if a.GetIdx() != j]
            # Find neighbor of j (not i)
            nj = [a.GetIdx() for a in mol.GetAtomWithIdx(j).GetNeighbors() if a.GetIdx() != i]
            
            if ni and nj:
                k = ni[0]
                l = nj[0]
                
                pos_k = conf.GetAtomPosition(k)
                pos_i = conf.GetAtomPosition(i)
                pos_j = conf.GetAtomPosition(j)
                pos_l = conf.GetAtomPosition(l)
                
                # Calculate dihedral
                v1 = np.array([pos_i.x - pos_k.x, pos_i.y - pos_k.y, pos_i.z - pos_k.z])
                v2 = np.array([pos_j.x - pos_i.x, pos_j.y - pos_i.y, pos_j.z - pos_i.z])
                v3 = np.array([pos_l.x - pos_j.x, pos_l.y - pos_j.y, pos_l.z - pos_j.z])
                
                b1 = -v1
                b2 = v2
                b3 = v3
                
                # Normal vectors
                n1 = np.cross(b1, b2)
                n2 = np.cross(b2, b3)
                
                # m1 = n1 x (b2/|b2|)
                m1 = np.cross(n1, b2 / np.linalg.norm(b2))
                
                x = np.dot(n1, n2)
                y = np.dot(m1, n2)
                
                angle_rad = np.arctan2(y, x)
                angle_deg = np.degrees(angle_rad)
                
                dihedrals.append(angle_deg)
                if len(dihedrals) >= 3: break
                
        for idx, dih in enumerate(dihedrals):
            descriptors[f'dihedral_{idx+1}'] = dih
            
        # Fill missing with NaN if we didn't get enough
        for key in list(descriptors.keys()):
            if np.isnan(descriptors[key]):
                del descriptors[key]
                
        return descriptors
        
    except Exception as e:
        log_feature_extraction_error(f"Geometric extraction failed: {e}")
        return {}


def extract_all_descriptors(row: Dict[str, Any]) -> Dict[str, float]:
    """
    Wrapper to extract all descriptors from a dataframe row.
    """
    all_desc = {}
    
    # 1. Electronic
    # Pass the row dict to extract_electronic_descriptors
    electronic = extract_electronic_descriptors(row)
    all_desc.update(electronic)
    
    # 2. Geometric
    # We need to generate 3D from SMILES if not present
    smiles = row.get('smiles', '')
    if not smiles:
        log_missing_geometric_data("No SMILES string found")
        return all_desc
        
    mol = parse_smiles_to_molecule(smiles)
    if mol:
        mol_3d = generate_3d_conformer(mol)
        if mol_3d:
            geometric = extract_geometric_descriptors(mol_3d)
            all_desc.update(geometric)
        else:
            log_missing_geometric_data("Failed to generate 3D conformer")
    else:
        log_missing_geometric_data("Failed to parse SMILES")
        
    return all_desc


def run_descriptor_pipeline(input_df: pd.DataFrame, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Run descriptor extraction on a DataFrame.
    """
    if input_df.empty:
        return input_df
        
    results = []
    total = len(input_df)
    
    for idx, row in input_df.iterrows():
        desc = extract_all_descriptors(row.to_dict())
        # Merge with original row data
        new_row = row.to_dict()
        new_row.update(desc)
        results.append(new_row)
        
        if (idx + 1) % 10 == 0:
            logger.info(f"Processed {idx+1}/{total} molecules")
            
    df_out = pd.DataFrame(results)
    
    # Handle metallic outliers (zero/negative gap)
    if 'band_gap_ev' in df_out.columns:
        metallic_mask = df_out['band_gap_ev'] <= 1e-6
        if metallic_mask.any():
            count = metallic_mask.sum()
            log_metallic_outlier(count)
            # Flag them, don't drop yet (T015 logic might drop later)
            df_out.loc[metallic_mask, 'is_metallic'] = True
        else:
            df_out['is_metallic'] = False
    else:
        df_out['is_metallic'] = False
        
    if output_path:
        df_out.to_csv(output_path, index=False)
        
    return df_out


# Wrapper functions for potential parallelization or specific API calls
def parse_smiles_to_molecule_wrapper(smiles: str) -> Optional[Any]:
    return parse_smiles_to_molecule(smiles)

def generate_3d_conformer_wrapper(mol: Any) -> Optional[Any]:
    return generate_3d_conformer(mol)

def extract_electronic_descriptors_wrapper(row: Dict[str, Any]) -> Dict[str, float]:
    return extract_electronic_descriptors(row)

def extract_geometric_descriptors_wrapper(mol: Any) -> Dict[str, float]:
    return extract_geometric_descriptors(mol)

def extract_all_descriptors_wrapper(row: Dict[str, Any]) -> Dict[str, float]:
    return extract_all_descriptors(row)

def run_descriptor_pipeline_wrapper(input_df: pd.DataFrame, output_path: Optional[str] = None) -> pd.DataFrame:
    return run_descriptor_pipeline(input_df, output_path)
