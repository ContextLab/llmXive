"""
Descriptor calculation module for High-Entropy Alloys.

Computes Miedema-derived features and standard descriptors,
then applies ILR transformation for linear model compatibility.
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any
from scipy import stats
from pymatgen.core import Element, PeriodicTable
from utils.logging_config import get_logger
from features.coda import ilr_transform_dataframe
from utils.validators import ValidationError

logger = get_logger(__name__)

# Miedema parameters for elements (simplified lookup)
# These are representative values; in production, use a full database
MIEDEMA_PARAMS = {
    'H': {'phi': 3.30, 'n_ws': 1.24, 'r': 0.37},
    'He': {'phi': 4.16, 'n_ws': 3.00, 'r': 0.31},
    'Li': {'phi': 2.90, 'n_ws': 0.43, 'r': 1.52},
    'Be': {'phi': 3.60, 'n_ws': 0.82, 'r': 1.12},
    'B': {'phi': 5.30, 'n_ws': 1.70, 'r': 0.82},
    'C': {'phi': 5.85, 'n_ws': 2.20, 'r': 0.77},
    'N': {'phi': 4.80, 'n_ws': 1.40, 'r': 0.71},
    'O': {'phi': 6.20, 'n_ws': 2.00, 'r': 0.66},
    'F': {'phi': 6.50, 'n_ws': 2.50, 'r': 0.64},
    'Ne': {'phi': 6.80, 'n_ws': 3.20, 'r': 0.58},
    'Na': {'phi': 3.10, 'n_ws': 0.32, 'r': 1.86},
    'Mg': {'phi': 3.40, 'n_ws': 0.54, 'r': 1.60},
    'Al': {'phi': 4.20, 'n_ws': 0.93, 'r': 1.43},
    'Si': {'phi': 4.80, 'n_ws': 1.30, 'r': 1.17},
    'P': {'phi': 5.10, 'n_ws': 1.50, 'r': 1.10},
    'S': {'phi': 5.40, 'n_ws': 1.70, 'r': 1.04},
    'Cl': {'phi': 5.70, 'n_ws': 1.90, 'r': 0.99},
    'Ar': {'phi': 6.00, 'n_ws': 2.20, 'r': 0.94},
    'K': {'phi': 3.20, 'n_ws': 0.25, 'r': 2.27},
    'Ca': {'phi': 3.30, 'n_ws': 0.38, 'r': 1.97},
    'Sc': {'phi': 3.50, 'n_ws': 0.55, 'r': 1.64},
    'Ti': {'phi': 3.70, 'n_ws': 0.66, 'r': 1.47},
    'V': {'phi': 4.00, 'n_ws': 0.82, 'r': 1.34},
    'Cr': {'phi': 4.20, 'n_ws': 0.93, 'r': 1.28},
    'Mn': {'phi': 4.10, 'n_ws': 0.88, 'r': 1.27},
    'Fe': {'phi': 4.30, 'n_ws': 1.00, 'r': 1.26},
    'Co': {'phi': 4.40, 'n_ws': 1.05, 'r': 1.25},
    'Ni': {'phi': 4.50, 'n_ws': 1.10, 'r': 1.24},
    'Cu': {'phi': 4.60, 'n_ws': 1.20, 'r': 1.28},
    'Zn': {'phi': 4.30, 'n_ws': 0.95, 'r': 1.33},
    'Ga': {'phi': 4.10, 'n_ws': 0.85, 'r': 1.35},
    'Ge': {'phi': 4.40, 'n_ws': 1.00, 'r': 1.22},
    'As': {'phi': 4.60, 'n_ws': 1.10, 'r': 1.19},
    'Se': {'phi': 4.80, 'n_ws': 1.20, 'r': 1.16},
    'Br': {'phi': 5.00, 'n_ws': 1.30, 'r': 1.14},
    'Kr': {'phi': 5.20, 'n_ws': 1.40, 'r': 1.10},
    'Rb': {'phi': 3.30, 'n_ws': 0.20, 'r': 2.48},
    'Sr': {'phi': 3.40, 'n_ws': 0.30, 'r': 2.15},
    'Y': {'phi': 3.50, 'n_ws': 0.45, 'r': 1.80},
    'Zr': {'phi': 3.60, 'n_ws': 0.55, 'r': 1.60},
    'Nb': {'phi': 3.80, 'n_ws': 0.70, 'r': 1.46},
    'Mo': {'phi': 4.00, 'n_ws': 0.85, 'r': 1.39},
    'Tc': {'phi': 4.10, 'n_ws': 0.90, 'r': 1.36},
    'Ru': {'phi': 4.20, 'n_ws': 0.95, 'r': 1.34},
    'Rh': {'phi': 4.30, 'n_ws': 1.00, 'r': 1.34},
    'Pd': {'phi': 4.40, 'n_ws': 1.05, 'r': 1.37},
    'Ag': {'phi': 4.30, 'n_ws': 0.98, 'r': 1.44},
    'Cd': {'phi': 4.20, 'n_ws': 0.92, 'r': 1.51},
    'In': {'phi': 4.00, 'n_ws': 0.80, 'r': 1.66},
    'Sn': {'phi': 4.10, 'n_ws': 0.85, 'r': 1.58},
    'Sb': {'phi': 4.20, 'n_ws': 0.90, 'r': 1.53},
    'Te': {'phi': 4.30, 'n_ws': 0.95, 'r': 1.48},
    'I': {'phi': 4.40, 'n_ws': 1.00, 'r': 1.44},
    'Xe': {'phi': 4.50, 'n_ws': 1.05, 'r': 1.40},
    'Cs': {'phi': 3.40, 'n_ws': 0.18, 'r': 2.65},
    'Ba': {'phi': 3.50, 'n_ws': 0.25, 'r': 2.22},
    'La': {'phi': 3.60, 'n_ws': 0.35, 'r': 1.87},
    'Ce': {'phi': 3.65, 'n_ws': 0.38, 'r': 1.83},
    'Pr': {'phi': 3.70, 'n_ws': 0.40, 'r': 1.82},
    'Nd': {'phi': 3.75, 'n_ws': 0.42, 'r': 1.81},
    'Pm': {'phi': 3.80, 'n_ws': 0.44, 'r': 1.80},
    'Sm': {'phi': 3.85, 'n_ws': 0.46, 'r': 1.80},
    'Eu': {'phi': 3.90, 'n_ws': 0.48, 'r': 1.99},
    'Gd': {'phi': 3.95, 'n_ws': 0.50, 'r': 1.80},
    'Tb': {'phi': 4.00, 'n_ws': 0.52, 'r': 1.79},
    'Dy': {'phi': 4.05, 'n_ws': 0.54, 'r': 1.78},
    'Ho': {'phi': 4.10, 'n_ws': 0.56, 'r': 1.77},
    'Er': {'phi': 4.15, 'n_ws': 0.58, 'r': 1.76},
    'Tm': {'phi': 4.20, 'n_ws': 0.60, 'r': 1.76},
    'Yb': {'phi': 4.25, 'n_ws': 0.62, 'r': 1.94},
    'Lu': {'phi': 4.30, 'n_ws': 0.64, 'r': 1.74},
    'Hf': {'phi': 4.40, 'n_ws': 0.70, 'r': 1.59},
    'Ta': {'phi': 4.50, 'n_ws': 0.78, 'r': 1.46},
    'W': {'phi': 4.60, 'n_ws': 0.86, 'r': 1.39},
    'Re': {'phi': 4.70, 'n_ws': 0.92, 'r': 1.37},
    'Os': {'phi': 4.80, 'n_ws': 0.98, 'r': 1.35},
    'Ir': {'phi': 4.90, 'n_ws': 1.04, 'r': 1.36},
    'Pt': {'phi': 5.00, 'n_ws': 1.10, 'r': 1.39},
    'Au': {'phi': 4.90, 'n_ws': 1.05, 'r': 1.44},
    'Hg': {'phi': 4.80, 'n_ws': 1.00, 'r': 1.51},
    'Tl': {'phi': 4.60, 'n_ws': 0.90, 'r': 1.70},
    'Pb': {'phi': 4.50, 'n_ws': 0.85, 'r': 1.75},
    'Bi': {'phi': 4.40, 'n_ws': 0.80, 'r': 1.70},
    'Po': {'phi': 4.30, 'n_ws': 0.75, 'r': 1.65},
    'At': {'phi': 4.20, 'n_ws': 0.70, 'r': 1.60},
    'Rn': {'phi': 4.10, 'n_ws': 0.65, 'r': 1.55},
}

def get_miedema_param(element_symbol: str, param_name: str) -> float:
    """Get a specific Miedema parameter for an element."""
    symbol = element_symbol.upper()
    if symbol not in MIEDEMA_PARAMS:
        logger.warning(f"Missing Miedema parameters for element: {symbol}. Using defaults.")
        return 1.0
    return MIEDEMA_PARAMS[symbol].get(param_name, 1.0)

def calculate_miedema_features(row: pd.Series, composition_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Miedema-derived features for a single sample.
    
    Args:
        row: DataFrame row containing composition data
        composition_cols: List of columns representing element fractions
        
    Returns:
        Dictionary with Miedema feature names and values
    """
    elements = []
    fractions = []
    
    for col in composition_cols:
        element = col.replace('_fraction', '').replace('_conc', '')
        frac = row[col]
        if pd.notna(frac) and frac > 0:
            elements.append(element)
            fractions.append(frac)
    
    if not elements:
        return {
            'mixing_enthalpy_miedema': np.nan,
            'atomic_radius_variance_miedema': np.nan,
            'electronegativity_variance_miedema': np.nan,
        }
    
    # Normalize fractions to sum to 1.0 (defensive)
    total = sum(fractions)
    if total > 0:
        fractions = [f / total for f in fractions]
    
    # Calculate weighted averages
    phi_avg = sum(f * get_miedema_param(e, 'phi') for e, f in zip(elements, fractions))
    n_ws_avg = sum(f * get_miedema_param(e, 'n_ws') for e, f in zip(elements, fractions))
    r_avg = sum(f * get_miedema_param(e, 'r') for e, f in zip(elements, fractions))
    
    # 1. Mixing Enthalpy (simplified Miedema model)
    # Delta H_mix = sum_i sum_j c_i c_j Delta H_ij
    # Where Delta H_ij is approximated using Miedema parameters
    mixing_enthalpy = 0.0
    for i, (e1, f1) in enumerate(zip(elements, fractions)):
        for j, (e2, f2) in enumerate(zip(elements, fractions)):
            if i >= j:
                continue
            # Simplified interaction term
            phi_diff = get_miedema_param(e1, 'phi') - get_miedema_param(e2, 'phi')
            n_ws_diff = get_miedema_param(e1, 'n_ws') - get_miedema_param(e2, 'n_ws')
            # Approximate interaction energy
            interaction = -abs(phi_diff) * abs(n_ws_diff) * 100  # Scaling factor
            mixing_enthalpy += 2 * f1 * f2 * interaction
    
    # 2. Atomic Radius Variance (weighted by Miedema parameters)
    r_values = [get_miedema_param(e, 'r') for e in elements]
    r_variance = sum(f * (r - r_avg)**2 for f, r in zip(fractions, r_values))
    
    # 3. Electronegativity Variance (using phi as proxy)
    phi_values = [get_miedema_param(e, 'phi') for e in elements]
    phi_variance = sum(f * (phi - phi_avg)**2 for f, phi in zip(fractions, phi_values))
    
    return {
        'mixing_enthalpy_miedema': mixing_enthalpy,
        'atomic_radius_variance_miedema': r_variance,
        'electronegativity_variance_miedema': phi_variance,
    }

def calculate_standard_descriptors(row: pd.Series, composition_cols: List[str]) -> Dict[str, float]:
    """
    Calculate standard HEA descriptors.
    
    Args:
        row: DataFrame row containing composition data
        composition_cols: List of columns representing element fractions
        
    Returns:
        Dictionary with standard descriptor names and values
    """
    elements = []
    fractions = []
    
    for col in composition_cols:
        element = col.replace('_fraction', '').replace('_conc', '')
        frac = row[col]
        if pd.notna(frac) and frac > 0:
            elements.append(element)
            fractions.append(frac)
    
    if not elements:
        return {
            'config_entropy': np.nan,
            'VEC': np.nan,
            'delta': np.nan,
            'omega': np.nan,
        }
    
    # Normalize fractions
    total = sum(fractions)
    if total > 0:
        fractions = [f / total for f in fractions]
    
    # Configurational entropy: Delta S_mix = -R * sum(c_i * ln(c_i))
    R = 8.314
    entropy = 0.0
    for c in fractions:
        if c > 0:
            entropy -= c * np.log(c)
    config_entropy = R * entropy
    
    # Valence Electron Concentration (VEC)
    # Simplified: use group number as proxy
    vec_values = []
    for e in elements:
        try:
            elem = Element(e)
            # Use group number as VEC proxy (simplified)
            vec_values.append(elem.group_number if elem.group_number else 0)
        except Exception:
            vec_values.append(0)
    
    vec_avg = sum(f * v for f, v in zip(fractions, vec_values))
    vec_variance = sum(f * (v - vec_avg)**2 for f, v in zip(fractions, vec_values))
    
    # Atomic size difference (delta)
    radii = []
    for e in elements:
        try:
            elem = Element(e)
            radii.append(elem.atomic_radius)
        except Exception:
            radii.append(get_miedema_param(e, 'r'))
    
    r_avg = sum(f * r for f, r in zip(fractions, radii))
    delta = 100 * np.sqrt(sum(f * (r - r_avg)**2 for f, r in zip(fractions, radii))) / r_avg if r_avg > 0 else 0
    
    # Omega parameter: Omega = (T * Delta S_mix) / Delta H_mix
    # Simplified: assume T=1000K
    T = 1000
    # Reuse mixing enthalpy calculation from Miedema features
    mixing_enthalpy = 0.0
    for i, (e1, f1) in enumerate(zip(elements, fractions)):
        for j, (e2, f2) in enumerate(zip(elements, fractions)):
            if i >= j:
                continue
            phi_diff = get_miedema_param(e1, 'phi') - get_miedema_param(e2, 'phi')
            n_ws_diff = get_miedema_param(e1, 'n_ws') - get_miedema_param(e2, 'n_ws')
            interaction = -abs(phi_diff) * abs(n_ws_diff) * 100
            mixing_enthalpy += 2 * f1 * f2 * interaction
    
    omega = (T * config_entropy) / abs(mixing_enthalpy) if abs(mixing_enthalpy) > 1e-10 else 0
    
    return {
        'config_entropy': config_entropy,
        'VEC': vec_avg,
        'delta': delta,
        'omega': omega,
    }

def compute_descriptors(df: pd.DataFrame, composition_cols: List[str]) -> pd.DataFrame:
    """
    Compute all descriptors for a DataFrame of HEA samples.
    
    Args:
        df: DataFrame with composition columns
        composition_cols: List of composition column names
        
    Returns:
        DataFrame with added descriptor columns
    """
    logger.info(f"Computing descriptors for {len(df)} samples with {len(composition_cols)} composition columns")
    
    # Initialize new columns
    miedema_cols = ['mixing_enthalpy_miedema', 'atomic_radius_variance_miedema', 'electronegativity_variance_miedema']
    standard_cols = ['config_entropy', 'VEC', 'delta', 'omega']
    all_new_cols = miedema_cols + standard_cols
    
    for col in all_new_cols:
        df[col] = np.nan
    
    # Calculate descriptors row by row (vectorization limited by complex logic)
    for idx, row in df.iterrows():
        # Miedema features
        miedema_features = calculate_miedema_features(row, composition_cols)
        for col, val in miedema_features.items():
            df.at[idx, col] = val
        
        # Standard descriptors
        standard_features = calculate_standard_descriptors(row, composition_cols)
        for col, val in standard_features.items():
            df.at[idx, col] = val
    
    logger.info(f"Descriptor calculation complete. Added {len(all_new_cols)} columns.")
    
    return df

def apply_ilr_transformation(df: pd.DataFrame, composition_cols: List[str]) -> pd.DataFrame:
    """
    Apply ILR transformation to composition data for linear model compatibility.
    
    Args:
        df: DataFrame with composition columns
        composition_cols: List of composition column names
        
    Returns:
        DataFrame with ILR-transformed composition features
    """
    logger.info(f"Applying ILR transformation to {len(composition_cols)} composition columns")
    
    # Use the existing ILR transform function from coda module
    ilr_df = ilr_transform_dataframe(df, composition_cols)
    
    # Rename columns to indicate ILR transformation
    ilr_cols = [col for col in ilr_df.columns if col not in df.columns]
    logger.info(f"ILR transformation produced {len(ilr_cols)} new features")
    
    return ilr_df

def get_descriptor_columns() -> List[str]:
    """Return the list of all computed descriptor column names."""
    return [
        'mixing_enthalpy_miedema',
        'atomic_radius_variance_miedema',
        'electronegativity_variance_miedema',
        'config_entropy',
        'VEC',
        'delta',
        'omega',
    ]

def main():
    """Main function for standalone testing of descriptor calculation."""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Create sample data for testing
    sample_data = {
        'Cr_fraction': [0.2, 0.25, 0.2],
        'Mn_fraction': [0.2, 0.2, 0.25],
        'Fe_fraction': [0.2, 0.2, 0.2],
        'Co_fraction': [0.2, 0.2, 0.2],
        'Ni_fraction': [0.2, 0.15, 0.15],
        'Bulk_Modulus': [180, 175, 185],
    }
    df = pd.DataFrame(sample_data)
    
    composition_cols = ['Cr_fraction', 'Mn_fraction', 'Fe_fraction', 'Co_fraction', 'Ni_fraction']
    
    print("Original DataFrame:")
    print(df)
    print("\n" + "="*50 + "\n")
    
    # Compute descriptors
    df_with_desc = compute_descriptors(df, composition_cols)
    print("DataFrame with descriptors:")
    print(df_with_desc[get_descriptor_columns()])
    print("\n" + "="*50 + "\n")
    
    # Apply ILR transformation
    df_ilr = apply_ilr_transformation(df_with_desc, composition_cols)
    print("DataFrame with ILR features:")
    ilr_cols = [col for col in df_ilr.columns if 'ilr' in col.lower() or col.startswith('comp_')]
    print(df_ilr[ilr_cols])

if __name__ == '__main__':
    main()
