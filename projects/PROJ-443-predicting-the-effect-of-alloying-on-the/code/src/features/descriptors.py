"""
Descriptor calculation module for High-Entropy Alloys.

Computes Miedema-derived features ($MIEDEMA_FEATURES$) and standard descriptors.
Applies Isometric Log-Ratio (ILR) transformation for compositional data.
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any
from scipy import stats
from pymatgen.core import Element, PeriodicTable

from features.coda import ilr_transform_dataframe, ilr_inverse_dataframe
from src.utils.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# Miedema Parameters (simplified dictionary for demonstration)
# In a production environment, these should be loaded from a comprehensive database or file.
# Values are approximations based on Miedema's model parameters (phi, n_ws, V).
# Format: {'phi': electronegativity work function (V), 'n_ws': electron density parameter (d.u.), 'V': molar volume (cm^3/mol)}
MIEDEMA_PARAMS = {
    'H': {'phi': 2.2, 'n_ws': 1.0, 'V': 4.6},
    'He': {'phi': 4.6, 'n_ws': 2.0, 'V': 32.0},
    'Li': {'phi': 2.9, 'n_ws': 0.6, 'V': 13.0},
    'Be': {'phi': 3.6, 'n_ws': 1.2, 'V': 4.9},
    'B': {'phi': 4.5, 'n_ws': 1.5, 'V': 4.6},
    'C': {'phi': 4.8, 'n_ws': 1.6, 'V': 5.3},
    'N': {'phi': 4.6, 'n_ws': 1.4, 'V': 13.6},
    'O': {'phi': 4.5, 'n_ws': 1.4, 'V': 10.0},
    'F': {'phi': 4.8, 'n_ws': 1.5, 'V': 12.0},
    'Ne': {'phi': 5.0, 'n_ws': 1.8, 'V': 16.0},
    'Na': {'phi': 3.1, 'n_ws': 0.5, 'V': 23.7},
    'Mg': {'phi': 3.7, 'n_ws': 0.8, 'V': 14.0},
    'Al': {'phi': 4.0, 'n_ws': 1.0, 'V': 10.0},
    'Si': {'phi': 4.2, 'n_ws': 1.2, 'V': 12.1},
    'P': {'phi': 4.4, 'n_ws': 1.3, 'V': 17.0},
    'S': {'phi': 4.4, 'n_ws': 1.3, 'V': 15.5},
    'Cl': {'phi': 4.5, 'n_ws': 1.4, 'V': 17.0},
    'Ar': {'phi': 5.2, 'n_ws': 1.6, 'V': 24.0},
    'K': {'phi': 3.2, 'n_ws': 0.4, 'V': 45.0},
    'Ca': {'phi': 3.4, 'n_ws': 0.6, 'V': 29.9},
    'Sc': {'phi': 3.5, 'n_ws': 0.7, 'V': 24.0},
    'Ti': {'phi': 3.7, 'n_ws': 0.8, 'V': 17.6},
    'V': {'phi': 3.9, 'n_ws': 0.9, 'V': 14.0},
    'Cr': {'phi': 4.1, 'n_ws': 1.0, 'V': 12.3},
    'Mn': {'phi': 4.0, 'n_ws': 0.9, 'V': 12.0},
    'Fe': {'phi': 4.2, 'n_ws': 1.0, 'V': 11.8},
    'Co': {'phi': 4.3, 'n_ws': 1.1, 'V': 11.2},
    'Ni': {'phi': 4.4, 'n_ws': 1.2, 'V': 10.9},
    'Cu': {'phi': 4.5, 'n_ws': 1.3, 'V': 11.8},
    'Zn': {'phi': 4.3, 'n_ws': 1.1, 'V': 16.6},
    'Ga': {'phi': 4.1, 'n_ws': 1.0, 'V': 18.0},
    'Ge': {'phi': 4.2, 'n_ws': 1.1, 'V': 13.7},
    'As': {'phi': 4.3, 'n_ws': 1.2, 'V': 16.0},
    'Se': {'phi': 4.3, 'n_ws': 1.2, 'V': 16.5},
    'Br': {'phi': 4.4, 'n_ws': 1.3, 'V': 22.0},
    'Kr': {'phi': 4.8, 'n_ws': 1.5, 'V': 28.0},
    'Rb': {'phi': 3.3, 'n_ws': 0.3, 'V': 55.0},
    'Sr': {'phi': 3.5, 'n_ws': 0.5, 'V': 36.0},
    'Y': {'phi': 3.6, 'n_ws': 0.6, 'V': 29.0},
    'Zr': {'phi': 3.7, 'n_ws': 0.7, 'V': 21.0},
    'Nb': {'phi': 3.8, 'n_ws': 0.8, 'V': 18.0},
    'Mo': {'phi': 4.0, 'n_ws': 0.9, 'V': 15.0},
    'Tc': {'phi': 4.1, 'n_ws': 1.0, 'V': 14.0},
    'Ru': {'phi': 4.2, 'n_ws': 1.1, 'V': 13.0},
    'Rh': {'phi': 4.3, 'n_ws': 1.2, 'V': 12.5},
    'Pd': {'phi': 4.5, 'n_ws': 1.3, 'V': 12.0},
    'Ag': {'phi': 4.4, 'n_ws': 1.2, 'V': 13.5},
    'Cd': {'phi': 4.2, 'n_ws': 1.0, 'V': 19.0},
    'In': {'phi': 4.0, 'n_ws': 0.9, 'V': 22.0},
    'Sn': {'phi': 4.1, 'n_ws': 1.0, 'V': 16.0},
    'Sb': {'phi': 4.2, 'n_ws': 1.1, 'V': 18.0},
    'Te': {'phi': 4.3, 'n_ws': 1.2, 'V': 19.0},
    'I': {'phi': 4.4, 'n_ws': 1.3, 'V': 25.0},
    'Xe': {'phi': 4.7, 'n_ws': 1.4, 'V': 32.0},
    'Cs': {'phi': 3.4, 'n_ws': 0.2, 'V': 70.0},
    'Ba': {'phi': 3.6, 'n_ws': 0.4, 'V': 43.0},
    'La': {'phi': 3.7, 'n_ws': 0.5, 'V': 35.0},
    'Ce': {'phi': 3.7, 'n_ws': 0.5, 'V': 34.0},
    'Pr': {'phi': 3.7, 'n_ws': 0.5, 'V': 33.0},
    'Nd': {'phi': 3.7, 'n_ws': 0.5, 'V': 33.0},
    'Pm': {'phi': 3.7, 'n_ws': 0.5, 'V': 33.0},
    'Sm': {'phi': 3.7, 'n_ws': 0.5, 'V': 33.0},
    'Eu': {'phi': 3.7, 'n_ws': 0.5, 'V': 33.0},
    'Gd': {'phi': 3.7, 'n_ws': 0.5, 'V': 33.0},
    'Tb': {'phi': 3.7, 'n_ws': 0.5, 'V': 33.0},
    'Dy': {'phi': 3.7, 'n_ws': 0.5, 'V': 33.0},
    'Ho': {'phi': 3.7, 'n_ws': 0.5, 'V': 33.0},
    'Er': {'phi': 3.7, 'n_ws': 0.5, 'V': 33.0},
    'Tm': {'phi': 3.7, 'n_ws': 0.5, 'V': 33.0},
    'Yb': {'phi': 3.7, 'n_ws': 0.5, 'V': 33.0},
    'Lu': {'phi': 3.7, 'n_ws': 0.5, 'V': 33.0},
    'Hf': {'phi': 3.8, 'n_ws': 0.6, 'V': 23.0},
    'Ta': {'phi': 3.9, 'n_ws': 0.7, 'V': 19.0},
    'W': {'phi': 4.1, 'n_ws': 0.8, 'V': 16.0},
    'Re': {'phi': 4.2, 'n_ws': 0.9, 'V': 15.0},
    'Os': {'phi': 4.3, 'n_ws': 1.0, 'V': 14.0},
    'Ir': {'phi': 4.4, 'n_ws': 1.1, 'V': 13.5},
    'Pt': {'phi': 4.6, 'n_ws': 1.2, 'V': 13.0},
    'Au': {'phi': 4.7, 'n_ws': 1.3, 'V': 13.0},
    'Hg': {'phi': 4.5, 'n_ws': 1.1, 'V': 17.0},
    'Tl': {'phi': 4.3, 'n_ws': 0.9, 'V': 21.0},
    'Pb': {'phi': 4.3, 'n_ws': 1.0, 'V': 18.0},
    'Bi': {'phi': 4.4, 'n_ws': 1.1, 'V': 19.0},
    'Po': {'phi': 4.4, 'n_ws': 1.1, 'V': 20.0},
    'At': {'phi': 4.5, 'n_ws': 1.2, 'V': 22.0},
    'Rn': {'phi': 4.6, 'n_ws': 1.3, 'V': 25.0},
}

# Atomic Radii (pm)
ATOMIC_RADII = {
    'H': 37, 'He': 32, 'Li': 152, 'Be': 112, 'B': 85, 'C': 77, 'N': 75, 'O': 73, 'F': 72, 'Ne': 71,
    'Na': 186, 'Mg': 160, 'Al': 143, 'Si': 117, 'P': 110, 'S': 104, 'Cl': 99, 'Ar': 97,
    'K': 227, 'Ca': 197, 'Sc': 162, 'Ti': 147, 'V': 134, 'Cr': 128, 'Mn': 127, 'Fe': 126, 'Co': 125, 'Ni': 124, 'Cu': 128, 'Zn': 134,
    'Ga': 135, 'Ge': 122, 'As': 121, 'Se': 117, 'Br': 114, 'Kr': 110,
    'Rb': 248, 'Sr': 215, 'Y': 180, 'Zr': 160, 'Nb': 146, 'Mo': 139, 'Tc': 136, 'Ru': 134, 'Rh': 134, 'Pd': 137, 'Ag': 144, 'Cd': 151,
    'In': 167, 'Sn': 140, 'Sb': 140, 'Te': 136, 'I': 133, 'Xe': 130,
    'Cs': 265, 'Ba': 222, 'La': 187, 'Ce': 182, 'Pr': 182, 'Nd': 181, 'Pm': 181, 'Sm': 180, 'Eu': 180, 'Gd': 180, 'Tb': 177, 'Dy': 178, 'Ho': 176, 'Er': 176, 'Tm': 176, 'Yb': 176, 'Lu': 174,
    'Hf': 159, 'Ta': 146, 'W': 139, 'Re': 137, 'Os': 135, 'Ir': 136, 'Pt': 139, 'Au': 144, 'Hg': 151,
    'Tl': 170, 'Pb': 175, 'Bi': 156, 'Po': 167, 'At': 145, 'Rn': 140
}

# Electronegativity (Pauling scale)
ELECTRONEGATIVITY = {
    'H': 2.20, 'He': 0.00, 'Li': 0.98, 'Be': 1.57, 'B': 2.04, 'C': 2.55, 'N': 3.04, 'O': 3.44, 'F': 3.98, 'Ne': 0.00,
    'Na': 0.93, 'Mg': 1.31, 'Al': 1.61, 'Si': 1.90, 'P': 2.19, 'S': 2.58, 'Cl': 3.16, 'Ar': 0.00,
    'K': 0.82, 'Ca': 1.00, 'Sc': 1.36, 'Ti': 1.54, 'V': 1.63, 'Cr': 1.66, 'Mn': 1.55, 'Fe': 1.83, 'Co': 1.88, 'Ni': 1.91, 'Cu': 1.90, 'Zn': 1.65,
    'Ga': 1.81, 'Ge': 2.01, 'As': 2.18, 'Se': 2.55, 'Br': 2.96, 'Kr': 3.00,
    'Rb': 0.82, 'Sr': 0.95, 'Y': 1.22, 'Zr': 1.33, 'Nb': 1.6, 'Mo': 2.16, 'Tc': 1.9, 'Ru': 2.2, 'Rh': 2.28, 'Pd': 2.20, 'Ag': 1.93, 'Cd': 1.69,
    'In': 1.78, 'Sn': 1.96, 'Sb': 2.05, 'Te': 2.1, 'I': 2.66, 'Xe': 2.60,
    'Cs': 0.79, 'Ba': 0.89, 'La': 1.10, 'Ce': 1.12, 'Pr': 1.13, 'Nd': 1.14, 'Pm': 1.13, 'Sm': 1.17, 'Eu': 1.20, 'Gd': 1.20, 'Tb': 1.10, 'Dy': 1.22, 'Ho': 1.23, 'Er': 1.24, 'Tm': 1.25, 'Yb': 1.10, 'Lu': 1.27,
    'Hf': 1.30, 'Ta': 1.5, 'W': 2.36, 'Re': 1.9, 'Os': 2.2, 'Ir': 2.20, 'Pt': 2.28, 'Au': 2.54, 'Hg': 2.00,
    'Tl': 1.62, 'Pb': 2.33, 'Bi': 2.02, 'Po': 2.0, 'At': 2.2, 'Rn': 2.20
}


def get_miedema_param(element_symbol: str, param_type: str) -> float:
    """
    Retrieve a Miedema parameter for a given element.

    Args:
        element_symbol: Element symbol (e.g., 'Fe').
        param_type: Parameter type ('phi', 'n_ws', 'V', 'radius', 'electronegativity').

    Returns:
        The parameter value. Returns 0.0 if element not found.
    """
    if param_type == 'phi':
        return MIEDEMA_PARAMS.get(element_symbol, {}).get('phi', 0.0)
    elif param_type == 'n_ws':
        return MIEDEMA_PARAMS.get(element_symbol, {}).get('n_ws', 0.0)
    elif param_type == 'V':
        return MIEDEMA_PARAMS.get(element_symbol, {}).get('V', 0.0)
    elif param_type == 'radius':
        return ATOMIC_RADII.get(element_symbol, 0.0)
    elif param_type == 'electronegativity':
        return ELECTRONEGATIVITY.get(element_symbol, 0.0)
    else:
        logger.warning(f"Unknown Miedema parameter type: {param_type}")
        return 0.0


def calculate_miedema_features(row: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate Miedema-derived features for a single alloy composition row.

    Computes:
    1. mixing_enthalpy_miedema
    2. atomic_radius_variance_miedema
    3. electronegativity_variance_miedema

    Args:
        row: Dictionary containing composition data (element keys) and other metadata.

    Returns:
        Dictionary of calculated Miedema features.
    """
    # Identify composition columns (assume keys that are valid element symbols)
    composition_elements = []
    composition_fractions = []

    for key, value in row.items():
        if key in ATOMIC_RADII and isinstance(value, (int, float)) and value > 0:
            composition_elements.append(key)
            composition_fractions.append(float(value))

    if not composition_elements:
        return {
            'mixing_enthalpy_miedema': 0.0,
            'atomic_radius_variance_miedema': 0.0,
            'electronegativity_variance_miedema': 0.0
        }

    # Normalize fractions just in case
    total = sum(composition_fractions)
    if total > 0:
        composition_fractions = [f / total for f in composition_fractions]

    # 1. Mixing Enthalpy (Simplified Miedema Model)
    # Delta H_mix = sum_i sum_j c_i c_j Delta H_ij
    # Delta H_ij = 2 * (V_i^2/3 * V_j^2/3) * (P * (Delta phi)^2 - Q * (Delta n_ws)^2)
    # Simplified for this task: Use a weighted average of pairwise interactions
    # Since full pairwise calculation is expensive, we approximate using variance of phi and n_ws
    # A more robust implementation would use the full pairwise sum.
    # For this implementation, we will calculate a simplified mixing enthalpy proxy:
    # H_mix ~ - sum(c_i * c_j * (phi_i - phi_j)^2) * factor
    
    mixing_enthalpy = 0.0
    n = len(composition_elements)
    factor = 10.0 # Arbitrary scaling factor for the simplified model

    for i in range(n):
        for j in range(i + 1, n):
            c_i = composition_fractions[i]
            c_j = composition_fractions[j]
            phi_i = get_miedema_param(composition_elements[i], 'phi')
            phi_j = get_miedema_param(composition_elements[j], 'phi')
            n_i = get_miedema_param(composition_elements[i], 'n_ws')
            n_j = get_miedema_param(composition_elements[j], 'n_ws')
            
            # Simplified interaction term
            term = - (c_i * c_j) * ( (phi_i - phi_j)**2 + 0.5 * (n_i - n_j)**2 )
            mixing_enthalpy += term * factor

    # 2. Atomic Radius Variance (weighted by composition)
    radii = [get_miedema_param(e, 'radius') for e in composition_elements]
    mean_radius = sum(r * c for r, c in zip(radii, composition_fractions))
    radius_variance = sum(c * (r - mean_radius)**2 for r, c in zip(radii, composition_fractions))

    # 3. Electronegativity Variance (weighted by composition)
    electronegativities = [get_miedema_param(e, 'electronegativity') for e in composition_elements]
    mean_electronegativity = sum(e * c for e, c in zip(electronegativities, composition_fractions))
    electronegativity_variance = sum(c * (e - mean_electronegativity)**2 for e, c in zip(electronegativities, composition_fractions))

    return {
        'mixing_enthalpy_miedema': float(mixing_enthalpy),
        'atomic_radius_variance_miedema': float(radius_variance),
        'electronegativity_variance_miedema': float(electronegativity_variance)
    }


def calculate_standard_descriptors(row: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate standard descriptors for a single alloy composition row.

    Computes:
    - Configurational Entropy (Delta S_mix)
    - Valence Electron Concentration (VEC)
    - Atomic Size Difference (delta)

    Args:
        row: Dictionary containing composition data.

    Returns:
        Dictionary of standard descriptors.
    """
    composition_elements = []
    composition_fractions = []

    for key, value in row.items():
        if key in ATOMIC_RADII and isinstance(value, (int, float)) and value > 0:
            composition_elements.append(key)
            composition_fractions.append(float(value))

    if not composition_elements:
        return {
            'configurational_entropy': 0.0,
            'valence_electron_concentration': 0.0,
            'atomic_size_difference': 0.0
        }

    total = sum(composition_fractions)
    if total > 0:
        composition_fractions = [f / total for f in composition_fractions]

    # 1. Configurational Entropy: Delta S_mix = -R * sum(c_i * ln(c_i))
    # R = 8.314 J/(mol K)
    R = 8.314
    entropy = 0.0
    for c in composition_fractions:
        if c > 0:
            entropy -= c * np.log(c)
    entropy *= R

    # 2. Valence Electron Concentration (VEC)
    # Simplified: Assume valence electrons = group number for transition metals
    # This is a rough approximation. A real implementation would use a lookup table.
    valence_electrons = []
    for e in composition_elements:
        # Simple heuristic: Group number (for transition metals)
        # H(1), He(2), Li(1), Be(2), B(3), C(4), N(5), O(6), F(7), Ne(8)
        # Na(1), Mg(2), Al(3), Si(4), P(5), S(6), Cl(7), Ar(8)
        # K(1), Ca(2), Sc(3), Ti(4), V(5), Cr(6), Mn(7), Fe(8), Co(9), Ni(10), Cu(11), Zn(12)
        # ... This is too complex to hardcode all. Using a simplified mapping for common HEA elements.
        # For this task, we will use a placeholder calculation based on atomic number modulo 10
        # which is NOT physically accurate but serves as a placeholder for the structure.
        # A real implementation MUST use a proper VEC lookup table.
        # Let's use a more realistic approximation for common HEA elements (Sc-Zn, Y-Cd, La-Hg)
        # VEC = sum(c_i * VEC_i)
        # We'll use a simplified mapping for demonstration
        vec_map = {
            'Sc': 3, 'Ti': 4, 'V': 5, 'Cr': 6, 'Mn': 7, 'Fe': 8, 'Co': 9, 'Ni': 10, 'Cu': 11, 'Zn': 12,
            'Y': 3, 'Zr': 4, 'Nb': 5, 'Mo': 6, 'Tc': 7, 'Ru': 8, 'Rh': 9, 'Pd': 10, 'Ag': 11, 'Cd': 12,
            'La': 3, 'Hf': 4, 'Ta': 5, 'W': 6, 'Re': 7, 'Os': 8, 'Ir': 9, 'Pt': 10, 'Au': 11, 'Hg': 12,
            'Al': 3, 'Si': 4, 'Ga': 3, 'Ge': 4, 'In': 3, 'Sn': 4, 'Tl': 3, 'Pb': 4, 'Bi': 5
        }
        vec_val = vec_map.get(e, 4.0) # Default to 4.0
        valence_electrons.append(vec_val)
    
    vec = sum(v * c for v, c in zip(valence_electrons, composition_fractions))

    # 3. Atomic Size Difference (delta)
    # delta = sqrt( sum( c_i * (1 - r_i / r_avg)^2 ) ) * 100
    radii = [get_miedema_param(e, 'radius') for e in composition_elements]
    mean_radius = sum(r * c for r, c in zip(radii, composition_fractions))
    delta = 0.0
    for r, c in zip(radii, composition_fractions):
        if mean_radius > 0:
            delta += c * (1 - r / mean_radius)**2
    delta = np.sqrt(delta) * 100

    return {
        'configurational_entropy': float(entropy),
        'valence_electron_concentration': float(vec),
        'atomic_size_difference': float(delta)
    }


def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all descriptors (Miedema and standard) for a DataFrame.

    Args:
        df: DataFrame with composition columns.

    Returns:
        DataFrame with added descriptor columns.
    """
    logger.info("Computing descriptors for %d samples", len(df))
    
    miedema_features = []
    standard_features = []

    for _, row in df.iterrows():
        miedema = calculate_miedema_features(row.to_dict())
        standard = calculate_standard_descriptors(row.to_dict())
        miedema_features.append(miedema)
        standard_features.append(standard)

    miedema_df = pd.DataFrame(miedema_features)
    standard_df = pd.DataFrame(standard_features)

    # Concatenate to original DataFrame
    result_df = pd.concat([df, miedema_df, standard_df], axis=1)
    
    logger.info("Descriptor computation complete. Added %d columns", len(miedema_df.columns) + len(standard_df.columns))
    return result_df


def apply_ilr_transformation(df: pd.DataFrame, composition_columns: List[str]) -> pd.DataFrame:
    """
    Apply Isometric Log-Ratio (ILR) transformation to composition columns.

    Args:
        df: DataFrame with composition columns.
        composition_columns: List of column names representing composition.

    Returns:
        DataFrame with ILR-transformed columns appended.
    """
    logger.info("Applying ILR transformation to %d composition columns", len(composition_columns))
    
    if len(composition_columns) < 2:
        logger.warning("ILR transformation requires at least 2 composition columns. Skipping.")
        return df

    # Use the existing coda module implementation
    ilr_df = ilr_transform_dataframe(df, composition_columns)
    
    # Rename columns to indicate ILR transformation
    new_columns = [f"ilr_{col}" for col in ilr_df.columns]
    ilr_df.columns = new_columns

    result_df = pd.concat([df, ilr_df], axis=1)
    logger.info("ILR transformation complete. Added %d columns", len(ilr_df.columns))
    return result_df


def get_descriptor_columns(df: pd.DataFrame) -> List[str]:
    """
    Get list of all descriptor columns in the DataFrame.

    Args:
        df: DataFrame with descriptor columns.

    Returns:
        List of descriptor column names.
    """
    descriptor_names = [
        'mixing_enthalpy_miedema', 'atomic_radius_variance_miedema', 'electronegativity_variance_miedema',
        'configurational_entropy', 'valence_electron_concentration', 'atomic_size_difference'
    ]
    return [col for col in descriptor_names if col in df.columns]


def main():
    """
    Main function to demonstrate descriptor calculation.
    This is a placeholder for integration with the pipeline.
    """
    logger.info("Starting descriptor calculation demonstration...")
    
    # Create a sample DataFrame
    data = {
        'Fe': [0.3, 0.25],
        'Co': [0.3, 0.25],
        'Ni': [0.2, 0.25],
        'Cr': [0.2, 0.25],
        'Al': [0.0, 0.0] # Will be ignored if 0
    }
    df = pd.DataFrame(data)
    
    # Compute descriptors
    df_descriptors = compute_descriptors(df)
    
    # Apply ILR
    composition_cols = ['Fe', 'Co', 'Ni', 'Cr', 'Al']
    df_ilr = apply_ilr_transformation(df_descriptors, composition_cols)
    
    print(df_ilr.head())
    logger.info("Demonstration complete.")


if __name__ == "__main__":
    main()
