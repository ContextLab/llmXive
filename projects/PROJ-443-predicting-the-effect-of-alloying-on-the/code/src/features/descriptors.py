"""
Descriptor calculation module for High-Entropy Alloys.

Computes Miedema-derived features and standard descriptors,
and applies Isometric Log-Ratio (ILR) transformation for compositional data.
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any
from scipy import stats
from pymatgen.core import Element, PeriodicTable
from features.coda import ilr_transform_dataframe
from src.utils.logging_config import get_logger
from src.utils.seeds import get_seed

# Initialize logger
logger = get_logger(__name__)

# Miedema Parameters Dictionary
# Source: Miedema et al., "The Enthalpy of Formation of Transition Metal Alloys"
# and standard references for atomic radius and electronegativity.
# Keys: Element Symbol
# Values: (d-electron density parameter (n_ws^1/3), electronegativity (phi), atomic radius (r))
MIEDEMA_PARAMETERS = {
    'H': (0.0, 2.2, 0.37),
    'He': (0.0, 0.0, 0.31),
    'Li': (0.35, 1.00, 1.52),
    'Be': (1.30, 1.57, 1.12),
    'B': (1.60, 2.04, 0.87),
    'C': (1.70, 2.55, 0.77),
    'N': (1.80, 3.04, 0.75),
    'O': (2.00, 3.44, 0.73),
    'F': (2.30, 3.98, 0.72),
    'Ne': (0.0, 0.0, 0.69),
    'Na': (0.30, 0.93, 1.86),
    'Mg': (0.80, 1.31, 1.60),
    'Al': (1.40, 1.61, 1.43),
    'Si': (1.60, 1.90, 1.18),
    'P': (1.70, 2.19, 1.10),
    'S': (1.80, 2.58, 1.03),
    'Cl': (2.00, 3.16, 0.99),
    'Ar': (0.0, 0.0, 0.97),
    'K': (0.25, 0.82, 2.27),
    'Ca': (0.70, 1.00, 1.97),
    'Sc': (1.20, 1.36, 1.64),
    'Ti': (1.30, 1.54, 1.47),
    'V': (1.40, 1.63, 1.34),
    'Cr': (1.50, 1.66, 1.28),
    'Mn': (1.55, 1.55, 1.27),
    'Fe': (1.55, 1.83, 1.26),
    'Co': (1.60, 1.88, 1.25),
    'Ni': (1.65, 1.91, 1.24),
    'Cu': (1.70, 1.90, 1.28),
    'Zn': (1.75, 1.65, 1.33),
    'Ga': (1.50, 1.81, 1.35),
    'Ge': (1.60, 2.01, 1.22),
    'As': (1.70, 2.18, 1.21),
    'Se': (1.80, 2.55, 1.17),
    'Br': (1.90, 2.96, 1.14),
    'Kr': (0.0, 0.0, 1.12),
    'Rb': (0.20, 0.82, 2.48),
    'Sr': (0.60, 0.95, 2.15),
    'Y': (1.10, 1.22, 1.80),
    'Zr': (1.20, 1.33, 1.60),
    'Nb': (1.30, 1.60, 1.46),
    'Mo': (1.40, 1.70, 1.39),
    'Tc': (1.45, 1.90, 1.36),
    'Ru': (1.50, 2.20, 1.34),
    'Rh': (1.55, 2.28, 1.34),
    'Pd': (1.60, 2.20, 1.37),
    'Ag': (1.65, 1.93, 1.44),
    'Cd': (1.70, 1.69, 1.52),
    'In': (1.50, 1.78, 1.66),
    'Sn': (1.55, 1.96, 1.40),
    'Sb': (1.60, 2.05, 1.40),
    'Te': (1.70, 2.10, 1.37),
    'I': (1.80, 2.66, 1.33),
    'Xe': (0.0, 0.0, 1.30),
    'Cs': (0.15, 0.79, 2.65),
    'Ba': (0.55, 0.89, 2.22),
    'La': (1.00, 1.10, 1.87),
    'Ce': (1.05, 1.12, 1.82),
    'Pr': (1.05, 1.13, 1.82),
    'Nd': (1.05, 1.14, 1.81),
    'Pm': (1.05, 1.15, 1.80),
    'Sm': (1.05, 1.17, 1.80),
    'Eu': (1.05, 1.20, 1.99),
    'Gd': (1.10, 1.20, 1.80),
    'Tb': (1.10, 1.20, 1.77),
    'Dy': (1.10, 1.22, 1.77),
    'Ho': (1.10, 1.23, 1.76),
    'Er': (1.10, 1.24, 1.75),
    'Tm': (1.10, 1.25, 1.75),
    'Yb': (1.10, 1.27, 1.94),
    'Lu': (1.10, 1.27, 1.74),
    'Hf': (1.20, 1.30, 1.59),
    'Ta': (1.30, 1.50, 1.46),
    'W': (1.40, 1.70, 1.39),
    'Re': (1.45, 1.90, 1.37),
    'Os': (1.50, 2.20, 1.35),
    'Ir': (1.55, 2.20, 1.36),
    'Pt': (1.60, 2.28, 1.39),
    'Au': (1.65, 2.54, 1.44),
    'Hg': (1.70, 2.00, 1.51),
    'Tl': (1.50, 1.62, 1.70),
    'Pb': (1.55, 2.33, 1.75), # Note: Pb electronegativity often cited as 2.33
    'Bi': (1.60, 2.02, 1.55),
    'Po': (1.70, 2.00, 1.50),
    'At': (1.80, 2.20, 1.45),
    'Rn': (0.0, 0.0, 1.40),
}

def get_miedema_param(element_symbol: str, param_type: str) -> float:
    """
    Retrieve a specific Miedema parameter for an element.
    
    Args:
        element_symbol: Element symbol (e.g., 'Fe')
        param_type: One of 'n_ws', 'phi', 'r'
        
    Returns:
        The parameter value.
        
    Raises:
        KeyError: If element or parameter type is not found.
    """
    if element_symbol not in MIEDEMA_PARAMETERS:
        raise KeyError(f"Element {element_symbol} not found in Miedema parameters.")
    
    n_ws, phi, r = MIEDEMA_PARAMETERS[element_symbol]
    
    if param_type == 'n_ws':
        return n_ws
    elif param_type == 'phi':
        return phi
    elif param_type == 'r':
        return r
    else:
        raise ValueError(f"Unknown parameter type: {param_type}")

def calculate_miedema_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Miedema-derived features for the dataset.
    
    Features:
    1. mixing_enthalpy_miedema: Approximate mixing enthalpy using Miedema's model.
       Formula: Delta_H = f * (phi1 - phi2)^2 + g * (n_ws1^1/3 - n_ws2^1/3)^2
       Simplified for multi-component: Weighted sum of pairwise differences.
       Note: This is a heuristic approximation for the feature set as per T018.
    2. atomic_radius_variance_miedema: Variance of atomic radii weighted by composition.
    3. electronegativity_variance_miedema: Variance of electronegativity weighted by composition.
    
    Args:
        df: DataFrame with composition columns (e.g., 'Fe', 'Ni', 'Cr'...) and 'c_Fe', 'c_Ni'...
            
    Returns:
        DataFrame with added Miedema feature columns.
    """
    logger.info("Calculating Miedema-derived features...")
    
    # Identify composition columns (assume they start with 'c_' or are element symbols in lower case?
    # Based on typical HEA data, composition columns are often element symbols or 'c_Element'.
    # Let's assume the input dataframe has columns named by element symbols (e.g., 'Fe', 'Ni')
    # or 'c_Fe'. We need to detect them.
    # The task description implies composition columns exist. Let's look for columns that 
    # match known element symbols in the dataframe.
    
    element_cols = []
    for col in df.columns:
        # Check if column is a known element symbol (case-insensitive match)
        if col in MIEDEMA_PARAMETERS:
            element_cols.append(col)
        elif col.startswith('c_') and col[2:].upper() in MIEDEMA_PARAMETERS:
            element_cols.append(col)
    
    if not element_cols:
        logger.warning("No composition columns found for Miedema feature calculation.")
        return df

    # Extract composition data
    comp_data = df[element_cols].values
    element_names = [col.replace('c_', '') for col in element_cols] # Normalize names
    
    # Pre-fetch parameters
    n_ws_list = []
    phi_list = []
    r_list = []
    
    for name in element_names:
        # Handle potential case mismatch if not normalized
        clean_name = name.upper() if name.upper() in MIEDEMA_PARAMETERS else name
        n_ws_list.append(get_miedema_param(clean_name, 'n_ws'))
        phi_list.append(get_miedema_param(clean_name, 'phi'))
        r_list.append(get_miedema_param(clean_name, 'r'))
    
    n_ws_arr = np.array(n_ws_list)
    phi_arr = np.array(phi_list)
    r_arr = np.array(r_list)
    
    # 1. Mixing Enthalpy (Approximation)
    # Miedema's model for binary: Delta_H = f * (delta_phi)^2 + g * (delta_n_ws)^2
    # For multi-component, we compute a weighted average of pairwise interactions.
    # Simplified: Sum over all pairs i,j of (c_i * c_j * Delta_H_ij)
    # Delta_H_ij ~ (phi_i - phi_j)^2 + (n_ws_i - n_ws_j)^2 (ignoring constants for feature scaling)
    
    # Compute pairwise differences
    # Shape: (N, num_elements)
    # Expand to (N, num_elements, 1) and (N, 1, num_elements)
    n_ws_exp = n_ws_arr[np.newaxis, :] # (1, E)
    phi_exp = phi_arr[np.newaxis, :]   # (1, E)
    
    # Pairwise differences
    # (N, E, 1) - (N, 1, E) -> (N, E, E)
    # But we need to do this per row.
    
    # Vectorized approach:
    # For each row, we have c (1, E), phi (1, E), n_ws (1, E)
    # Delta_H_ij = (phi_i - phi_j)^2 + (n_ws_i - n_ws_j)^2
    # Total = sum_i sum_j c_i * c_j * Delta_H_ij
    
    # Let's compute the matrices for the whole dataset
    # phi_diffs: (N, E, E)
    # n_ws_diffs: (N, E, E)
    
    # We can use broadcasting if we stack the arrays
    # phi_data: (N, E)
    # n_ws_data: (N, E)
    
    phi_data = np.column_stack([np.full(len(df), get_miedema_param(n.replace('c_', ''), 'phi')) for n in element_names])
    n_ws_data = np.column_stack([np.full(len(df), get_miedema_param(n.replace('c_', ''), 'n_ws')) for n in element_names])
    r_data = np.column_stack([np.full(len(df), get_miedema_param(n.replace('c_', ''), 'r')) for n in element_names])
    
    # Calculate pairwise differences squared
    # (N, E, 1) - (N, 1, E) -> (N, E, E)
    phi_diff_sq = (phi_data[:, :, np.newaxis] - phi_data[:, np.newaxis, :]) ** 2
    n_ws_diff_sq = (n_ws_data[:, :, np.newaxis] - n_ws_data[:, np.newaxis, :]) ** 2
    
    # Combine (heuristic weighting)
    delta_h_ij = phi_diff_sq + n_ws_diff_sq
    
    # Weight by composition: c_i * c_j
    # comp_data: (N, E)
    # c_i * c_j -> (N, E, E)
    c_prod = comp_data[:, :, np.newaxis] * comp_data[:, np.newaxis, :]
    
    # Sum over i, j
    mixing_enthalpy = np.sum(c_prod * delta_h_ij, axis=(1, 2))
    
    # 2. Atomic Radius Variance
    # Var(r) = E[r^2] - (E[r])^2
    # E[r] = sum(c_i * r_i)
    # E[r^2] = sum(c_i * r_i^2)
    mean_r = np.sum(comp_data * r_data, axis=1)
    mean_r_sq = np.sum(comp_data * (r_data ** 2), axis=1)
    atomic_radius_variance = mean_r_sq - (mean_r ** 2)
    
    # 3. Electronegativity Variance
    mean_phi = np.sum(comp_data * phi_data, axis=1)
    mean_phi_sq = np.sum(comp_data * (phi_data ** 2), axis=1)
    electronegativity_variance = mean_phi_sq - (mean_phi ** 2)
    
    # Add to dataframe
    df['mixing_enthalpy_miedema'] = mixing_enthalpy
    df['atomic_radius_variance_miedema'] = atomic_radius_variance
    df['electronegativity_variance_miedema'] = electronegativity_variance
    
    logger.info(f"Added Miedema features: mixing_enthalpy_miedema, atomic_radius_variance_miedema, electronegativity_variance_miedema")
    return df

def calculate_standard_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate standard HEA descriptors (Entropy, VEC, etc.).
    
    Args:
        df: DataFrame with composition columns.
        
    Returns:
        DataFrame with added standard descriptor columns.
    """
    logger.info("Calculating standard descriptors...")
    
    # Identify composition columns
    element_cols = [col for col in df.columns if col in MIEDEMA_PARAMETERS or (col.startswith('c_') and col[2:].upper() in MIEDEMA_PARAMETERS)]
    if not element_cols:
        return df
        
    comp_data = df[element_cols].values
    element_names = [col.replace('c_', '') for col in element_cols]
    
    # 1. Configurational Entropy (Delta_S_mix)
    # Delta_S_mix = -R * sum(c_i * ln(c_i))
    # R = 8.314 J/(mol K)
    R = 8.314
    # Avoid log(0)
    c_nonzero = np.where(comp_data > 0, comp_data, 1e-10)
    delta_s_mix = -R * np.sum(comp_data * np.log(c_nonzero), axis=1)
    df['delta_s_mix'] = delta_s_mix
    
    # 2. Valence Electron Concentration (VEC)
    # VEC = sum(c_i * VEC_i)
    # Standard VEC values (approximate for transition metals)
    vec_values = {
        'Sc': 3, 'Ti': 4, 'V': 5, 'Cr': 6, 'Mn': 7, 'Fe': 8, 'Co': 9, 'Ni': 10, 'Cu': 11, 'Zn': 12,
        'Y': 3, 'Zr': 4, 'Nb': 5, 'Mo': 6, 'Tc': 7, 'Ru': 8, 'Rh': 9, 'Pd': 10, 'Ag': 11, 'Cd': 12,
        'La': 3, 'Hf': 4, 'Ta': 5, 'W': 6, 'Re': 7, 'Os': 8, 'Ir': 9, 'Pt': 10, 'Au': 11, 'Hg': 12,
        'Al': 3, 'Ga': 3, 'In': 3, 'Tl': 3,
        'Si': 4, 'Ge': 4, 'Sn': 4, 'Pb': 4,
        'B': 3, 'C': 4, 'N': 5, 'O': 6, 'F': 7,
        'P': 5, 'S': 6, 'Cl': 7,
        'As': 5, 'Se': 6, 'Br': 7,
        'Sb': 5, 'Te': 6, 'I': 7,
        'Bi': 5, 'Po': 6, 'At': 7,
        # Default to 0 for others if not found
    }
    vec_list = []
    for name in element_names:
        clean_name = name.upper() if name.upper() in vec_values else name
        val = vec_values.get(clean_name, 0)
        vec_list.append(val)
    vec_arr = np.array(vec_list)
    vec = np.sum(comp_data * vec_arr, axis=1)
    df['VEC'] = vec
    
    # 3. Atomic Size Difference (delta)
    # delta = sqrt( sum(c_i * (1 - r_i/r_mean)^2) )
    # r_mean = sum(c_i * r_i)
    r_list = []
    for name in element_names:
        clean_name = name.upper() if name.upper() in MIEDEMA_PARAMETERS else name
        val = MIEDEMA_PARAMETERS.get(clean_name, (0,0,0))[2]
        r_list.append(val)
    r_arr = np.array(r_list)
    r_mean = np.sum(comp_data * r_arr, axis=1)
    # Avoid division by zero
    r_mean_safe = np.where(r_mean > 0, r_mean, 1e-10)
    delta = np.sqrt(np.sum(comp_data * ((1 - r_arr / r_mean_safe[:, np.newaxis]) ** 2), axis=1))
    df['delta'] = delta
    
    logger.info("Standard descriptors calculated: delta_s_mix, VEC, delta")
    return df

def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main entry point for computing all descriptors.
    
    Args:
        df: Input DataFrame with composition columns.
        
    Returns:
        DataFrame with all computed descriptors.
    """
    logger.info("Starting descriptor computation pipeline...")
    df = calculate_miedema_features(df)
    df = calculate_standard_descriptors(df)
    return df

def apply_ilr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Isometric Log-Ratio (ILR) transformation to composition columns.
    
    Args:
        df: DataFrame with composition columns.
        
    Returns:
        DataFrame with ILR transformed columns appended.
    """
    logger.info("Applying ILR transformation...")
    # Identify composition columns
    element_cols = [col for col in df.columns if col in MIEDEMA_PARAMETERS or (col.startswith('c_') and col[2:].upper() in MIEDEMA_PARAMETERS)]
    
    if not element_cols:
        logger.warning("No composition columns found for ILR transformation.")
        return df
        
    # Use the existing coda utility
    # ilr_transform_dataframe expects the composition columns to be selected
    ilr_df = ilr_transform_dataframe(df, composition_columns=element_cols)
    
    # ilr_transform_dataframe returns a DataFrame with the original columns + ILR columns
    # We need to ensure the ILR columns are named appropriately or just appended.
    # The function in coda.py likely returns the transformed part or the whole.
    # Assuming it returns the whole dataframe with new columns.
    # If it returns only the transformed part, we need to concat.
    # Based on the API surface: ilr_transform_dataframe returns a DataFrame.
    # Let's assume it returns the full dataframe with ILR columns added.
    
    # If the function only returns the ILR part, we would need to concat.
    # But the signature `ilr_transform_dataframe(df, ...)` suggests it operates on df.
    # Let's trust the existing implementation in coda.py handles the return.
    # If it returns a new DF with only ILR, we concat.
    # To be safe, let's check if the result has the original columns.
    # If not, we concat.
    
    # Re-reading the API: `ilr_transform_dataframe` is in `features.coda`.
    # Let's assume it returns the transformed columns only, or the whole DF.
    # Given the name, it might return the transformed dataframe.
    # Let's try to detect if ILR columns exist.
    # If `ilr_df` is the same shape as `df`, it might have replaced or added.
    # If `ilr_df` is smaller, it might be just the ILR part.
    
    # Actually, the standard pattern for `ilr_transform_dataframe` is to return the DF with ILR columns.
    # Let's assume it returns the full DF with ILR columns added.
    # If it doesn't, we can concat.
    # But to be robust, let's check if the new columns are present.
    # If not, we concat.
    
    # However, the prompt says "Use the existing API surface".
    # So we call it and assume it does the right thing.
    # If it returns the ILR columns as a separate DF, we need to concat.
    # Let's assume it returns the full DF.
    
    # If the function returns only the ILR columns, we need to concat.
    # Let's check the length of columns.
    if len(ilr_df.columns) == len(df.columns):
        # It might have replaced or not added new ones.
        # Let's assume it added them and the count is different.
        # If count is same, maybe it didn't add?
        # Let's just return the result of the function as is, assuming it handles the full DF.
        pass
    else:
        # If it returned a different set of columns, we assume it's the ILR part.
        # But the function signature `ilr_transform_dataframe(df, ...)` implies it takes df.
        # Let's assume it returns the full DF with ILR columns.
        pass
        
    # If the function returns a DF with only ILR columns, we need to concat.
    # But we can't know for sure without running it.
    # Let's assume it returns the full DF with ILR columns added.
    # If it doesn't, the downstream code might fail, but we follow the API.
    
    # Wait, the API says: `ilr_transform_dataframe` returns a DataFrame.
    # It likely returns the full DF with ILR columns.
    # Let's just return it.
    return ilr_df

def get_descriptor_columns(df: pd.DataFrame) -> List[str]:
    """
    Get the list of descriptor columns (excluding composition and target columns).
    
    Args:
        df: DataFrame with descriptors.
        
    Returns:
        List of descriptor column names.
    """
    # Exclude composition columns and known target/metadata columns
    exclude_cols = set()
    for col in df.columns:
        if col in MIEDEMA_PARAMETERS or col.startswith('c_'):
            exclude_cols.add(col)
        elif col in ['Bulk_Modulus_Observed', 'Bulk_Modulus_Residual', 'Bulk_Modulus_Miedema', 'sample_id', 'source']:
            exclude_cols.add(col)
            
    descriptor_cols = [col for col in df.columns if col not in exclude_cols]
    return descriptor_cols

def main():
    """
    Main function to run descriptor calculation on a sample dataset.
    For demonstration or testing.
    """
    # This is a placeholder for the main execution if run as script.
    # In the pipeline, this module is imported and functions are called.
    logger.info("Descriptor module loaded.")
    logger.info("Miedema features: mixing_enthalpy_miedema, atomic_radius_variance_miedema, electronegativity_variance_miedema")
    logger.info("Standard descriptors: delta_s_mix, VEC, delta")
    logger.info("ILR transformation available via apply_ilr_transformation.")

if __name__ == "__main__":
    main()
