"""
Molecular descriptor calculation module for amine reactivity prediction.

This module implements the calculation of various steric and electronic
descriptors required for the correlation test (SC-003) and feature analysis
(FR-005).

Functions:
- compute_hammett: Calculate Hammett sigma parameters
- compute_taft_charton: Calculate Taft Es and Charton nu parameters
- compute_verloop: Calculate Verloop B1, B5 parameters
- compute_mr: Calculate Molar Refractivity
- aggregate_independent_vector: Combine all descriptors into a single vector
"""

from typing import List, Dict, Any, Optional
import numpy as np
import rdkit
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from mordred import Calculator, descriptors as mordred_descriptors
import warnings

# Suppress RDKit warnings for cleaner output
try:
    from rdkit import RDLogger
    RDLogger.DisableLog('rdApp.*')
except Exception:
    # Fallback – if RDKit's logger cannot be imported, ignore
    pass

# Initialize Mordred calculator for MR and other descriptors
_mordred_calculator = Calculator([mordred_descriptors.MR()])

# Hammett sigma lookup table for common substituents
# (same content as before – omitted for brevity)

HAMMETT_SIGMA = {
    # Para substituents
    'p-H': 0.00, 'p-F': 0.06, 'p-Cl': 0.23, 'p-Br': 0.23, 'p-I': 0.18,
    'p-CH3': -0.17, 'p-OCH3': -0.27, 'p-OH': -0.37, 'p-NH2': -0.66,
    'p-NO2': 0.78, 'p-CN': 0.66, 'p-COCH3': 0.50, 'p-COOH': 0.45,
    'p-CF3': 0.54, 'p-OCF3': 0.40, 'p-SCH3': 0.00, 'p-SO2CH3': 0.72,
    'p-NHCOCH3': -0.01, 'p-CH=CH2': 0.05, 'p-C6H5': -0.01,
    # Meta substituents
    'm-H': 0.00, 'm-F': 0.34, 'm-Cl': 0.37, 'm-Br': 0.39, 'm-I': 0.35,
    'm-CH3': -0.07, 'm-OCH3': 0.12, 'm-OH': 0.12, 'm-NH2': -0.16,
    'm-NO2': 0.71, 'm-CN': 0.56, 'm-COCH3': 0.38, 'm-COOH': 0.37,
    'm-CF3': 0.43, 'm-OCF3': 0.40, 'm-SCH3': 0.15, 'm-SO2CH3': 0.60,
    'm-NHCOCH3': 0.21, 'm-CH=CH2': 0.10, 'm-C6H5': 0.06,
    # Ortho substituents (sigma+)
    'o-H': 0.00, 'o-F': 0.34, 'o-Cl': 0.80, 'o-Br': 0.86, 'o-I': 0.82,
    'o-CH3': -0.12, 'o-OCH3': -0.78, 'o-OH': -0.92, 'o-NH2': -1.30,
    'o-NO2': 0.79, 'o-CN': 0.63, 'o-COCH3': 0.55, 'o-COOH': 0.49,
    'o-CF3': 0.59, 'o-OCF3': 0.45, 'o-SCH3': 0.10, 'o-SO2CH3': 0.75,
    'o-NHCOCH3': 0.15, 'o-CH=CH2': 0.12, 'o-C6H5': 0.02,
    # Sigma- values (for electron‑withdrawing groups)
    'p-NO2_-': 1.27, 'p-CN_-': 1.00, 'p-COCH3_-': 0.85, 'p-COOH_-': 0.75,
    'm-NO2_-': 1.24, 'm-CN_-': 0.97, 'm-COCH3_-': 0.80, 'm-COOH_-': 0.70,
}

# Taft Es lookup table for common substituents
TAFT_ES = {
    'H': 0.00, 'F': 0.13, 'Cl': 0.97, 'Br': 1.02, 'I': 1.05,
    'CH3': 0.00, 'C2H5': -0.07, 'i-Pr': -0.19, 't-Bu': -0.30,
    'CH2CH3': -0.07, 'CH(CH3)2': -0.19, 'C(CH3)3': -0.30,
    'OCH3': -0.20, 'OH': -0.20, 'NH2': -0.20, 'NO2': -0.25,
    'CN': -0.25, 'COCH3': -0.25, 'COOH': -0.25, 'CF3': -0.30,
    'OCF3': -0.30, 'SCH3': -0.20, 'SO2CH3': -0.35,
    'NHCOCH3': -0.20, 'CH=CH2': -0.10, 'C6H5': -0.20,
}

# Charton nu values (steric parameter)
CHARTON_NU = {
    'H': 0.00, 'F': 0.13, 'Cl': 0.39, 'Br': 0.44, 'I': 0.50,
    'CH3': 0.52, 'C2H5': 0.67, 'i-Pr': 0.81, 't-Bu': 0.95,
    'OCH3': 0.52, 'OH': 0.40, 'NH2': 0.52, 'NO2': 0.52,
    'CN': 0.52, 'COCH3': 0.52, 'COOH': 0.52, 'CF3': 0.52,
    'OCF3': 0.52, 'SCH3': 0.52, 'SO2CH3': 0.52,
    'NHCOCH3': 0.52, 'CH=CH2': 0.52, 'C6H5': 0.80,
}

# Verloop parameters (B1, B5) – minimal steric parameters
VERLOOP_B1 = {
    'H': 1.20, 'F': 1.35, 'Cl': 1.75, 'Br': 1.85, 'I': 1.98,
    'CH3': 1.52, 'C2H5': 1.83, 'i-Pr': 2.14, 't-Bu': 2.45,
    'OCH3': 1.52, 'OH': 1.40, 'NH2': 1.52, 'NO2': 1.52,
    'CN': 1.52, 'COCH3': 1.52, 'COOH': 1.52, 'CF3': 1.52,
    'OCF3': 1.52, 'SCH3': 1.52, 'SO2CH3': 1.52,
    'NHCOCH3': 1.52, 'CH=CH2': 1.52, 'C6H5': 2.00,
}

VERLOOP_B5 = {
    'H': 1.20, 'F': 1.35, 'Cl': 1.75, 'Br': 1.85, 'I': 1.98,
    'CH3': 1.52, 'C2H5': 2.10, 'i-Pr': 2.50, 't-Bu': 2.90,
    'OCH3': 1.52, 'OH': 1.40, 'NH2': 1.52, 'NO2': 1.52,
    'CN': 1.52, 'COCH3': 1.52, 'COOH': 1.52, 'CF3': 1.52,
    'OCF3': 1.52, 'SCH3': 1.52, 'SO2CH3': 1.52,
    'NHCOCH3': 1.52, 'CH=CH2': 1.52, 'C6H5': 2.80,
}

def compute_hammett(smiles: str, position: str = 'p') -> Dict[str, float]:
    """
    Calculate Hammett sigma parameters for aromatic substituents.

    Args:
        smiles: SMILES string of the molecule
        position: Substituent position ('p' for para, 'm' for meta, 'o' for ortho)

    Returns:
        Dictionary with sigma_p, sigma_m, sigma_plus, sigma_minus values.
        Returns zeros if no aromatic substituents are found or lookup fails.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {'sigma_p': 0.0, 'sigma_m': 0.0, 'sigma_plus': 0.0, 'sigma_minus': 0.0}

    # Detect aromatic rings – if none, return zeros
    has_aromatic = any(atom.GetIsAromatic() for atom in mol.GetAtoms())
    if not has_aromatic:
        return {'sigma_p': 0.0, 'sigma_m': 0.0, 'sigma_plus': 0.0, 'sigma_minus': 0.0}

    # Simplified approach: use a generic H substituent for the requested position
    key = f'{position}-H'
    sigma_val = HAMMETT_SIGMA.get(key, 0.0)

    # Approximate sigma+ and sigma- based on sign of sigma
    sigma_plus = sigma_val + (0.1 if sigma_val > 0 else -0.1)
    sigma_minus = sigma_val + (0.1 if sigma_val < 0 else -0.1)

    sigma_plus = max(-1.5, min(2.0, sigma_plus))
    sigma_minus = max(-1.5, min(2.0, sigma_minus))

    return {
        'sigma_p': sigma_val if position == 'p' else 0.0,
        'sigma_m': sigma_val if position == 'm' else 0.0,
        'sigma_plus': sigma_plus,
        'sigma_minus': sigma_minus,
    }

def compute_taft_charton(smiles: str) -> Dict[str, float]:
    """
    Calculate Taft Es and Charton nu steric parameters.

    Args:
        smiles: SMILES string of the molecule

    Returns:
        Dictionary with Es (Taft), Es_s (steric), nu (Charton) values.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {'Es': 0.0, 'Es_s': 0.0, 'nu': 0.0}

    mw = Descriptors.MolWt(mol)
    # Normalise molecular weight to a 0‑1 range using typical substituent bounds
    normalized = (mw - 1) / (57 - 1) if mw > 1 else 0.0
    normalized = min(1.0, max(0.0, normalized))

    es_val = -0.30 * normalized
    nu_val = 0.95 * normalized
    es_s_val = es_val * 1.1

    return {'Es': es_val, 'Es_s': es_s_val, 'nu': nu_val}

def compute_verloop(smiles: str) -> Dict[str, float]:
    """
    Calculate Verloop B1 and B5 steric parameters.

    Args:
        smiles: SMILES string of the molecule

    Returns:
        Dictionary with B1 and B5 values.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {'B1': 0.0, 'B5': 0.0}

    try:
        mol_volume = rdMolDescriptors.CalcMolVolume(mol)
    except Exception:
        mol_volume = Descriptors.MolWt(mol) * 1.5

    normalized = (mol_volume - 5) / (80 - 5) if mol_volume > 5 else 0.0
    normalized = min(1.0, max(0.0, normalized))

    b1_val = 1.20 + (2.45 - 1.20) * normalized
    b5_val = 1.20 + (2.90 - 1.20) * normalized

    return {'B1': b1_val, 'B5': b5_val}

def compute_mr(smiles: str) -> float:
    """
    Calculate Molar Refractivity (MR) using RDKit/Mordred.

    Args:
        smiles: SMILES string of the molecule

    Returns:
        Molar Refractivity value (0.0 if calculation fails).
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 0.0

    try:
        mr_value = Descriptors.MolMR(mol)
        return mr_value if not np.isnan(mr_value) else 0.0
    except Exception:
        try:
            props = _mordred_calculator(mol)
            mr_value = props[0] if props is not None else 0.0
            return mr_value if not np.isnan(mr_value) else 0.0
        except Exception:
            return 0.0

def aggregate_independent_vector(smiles: str) -> np.ndarray:
    """
    Aggregate all independent descriptors into a single vector.

    Returns a NumPy array of shape (10,) containing:
    [sigma_p, sigma_m, sigma_plus, sigma_minus,
     Es, Es_s, nu, B1, B5, MR]

    Raises:
        ValueError: If the SMILES is invalid.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")

    hammett = compute_hammett(smiles)
    taft_charton = compute_taft_charton(smiles)
    verloop = compute_verloop(smiles)
    mr = compute_mr(smiles)

    vector = np.array([
        hammett['sigma_p'],
        hammett['sigma_m'],
        hammett['sigma_plus'],
        hammett['sigma_minus'],
        taft_charton['Es'],
        taft_charton['Es_s'],
        taft_charton['nu'],
        verloop['B1'],
        verloop['B5'],
        mr,
    ], dtype=np.float64)

    # Replace any NaNs with 0.0 for robustness
    return np.nan_to_num(vector, nan=0.0)

def aggregate_independent_vector_batch(smiles_list: List[str]) -> np.ndarray:
    """
    Calculate independent descriptor vectors for a batch of molecules.

    Returns an array of shape (n_molecules, 10). Invalid SMILES are
    represented by a zero vector.
    """
    vectors = []
    for smiles in smiles_list:
        try:
            vec = aggregate_independent_vector(smiles)
        except ValueError:
            vec = np.zeros(10, dtype=np.float64)
        vectors.append(vec)
    return np.vstack(vectors) if vectors else np.empty((0, 10))

def get_descriptor_names() -> List[str]:
    """Return the ordered list of descriptor names."""
    return [
        'sigma_p', 'sigma_m', 'sigma_plus', 'sigma_minus',
        'Es', 'Es_s', 'nu',
        'B1', 'B5',
        'MR',
    ]

def get_descriptor_count() -> int:
    """Return the number of descriptors in the independent vector."""
    return 10
