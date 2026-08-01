from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys
from rdkit import DataStructs
import numpy as np
from typing import Union, List
import pandas as pd

def generate_ecfp4(smiles: str, n_bits: int = 2048) -> np.ndarray:
    """Generate ECFP4 fingerprint for a SMILES string."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return np.zeros(n_bits, dtype=np.uint8)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.uint8)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def generate_maccs(smiles: str) -> np.ndarray:
    """Generate MACCS keys fingerprint for a SMILES string."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return np.zeros(167, dtype=np.uint8)
    fp = MACCSkeys.GenMACCSKeys(mol)
    arr = np.zeros((167,), dtype=np.uint8)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def generate_fingerprints_batch(df: pd.DataFrame, smiles_col: str = "canonical_smiles") -> pd.DataFrame:
    """Generate fingerprints for a batch of reactions."""
    df['ecfp4'] = df[smiles_col].apply(generate_ecfp4)
    df['maccs'] = df[smiles_col].apply(generate_maccs)
    return df
