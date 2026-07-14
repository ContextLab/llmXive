import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from . import logger
from chemparse import Composition

def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute elemental descriptors for the ceramic data.
    
    1. Mean atomic radius
    2. Electronegativity std
    3. Cation Size Variance
    4. Valence Electron Concentration (VEC)
    
    Args:
        df: Cleaned DataFrame with 'composition' column.
        
    Returns:
        pd.DataFrame: DataFrame with added descriptor columns.
    """
    logger.info("Computing descriptors...")
    df = df.copy()
    
    # Initialize columns
    df['mean_atomic_radius'] = 0.0
    df['electronegativity_std'] = 0.0
    df['valence_electron_concentration'] = 0.0
    df['cation_size_variance'] = 0.0
    df['primary_anion_cation_group'] = 'Unknown'
    
    # Periodic table data (simplified for this implementation)
    # In a real project, this would be loaded from a file or library like mendeleev
    periodic_data = {
        'Al': {'radius': 1.43, 'en': 1.61, 'valence': 3, 'group': 3},
        'Si': {'radius': 1.11, 'en': 1.90, 'valence': 4, 'group': 4},
        'O':  {'radius': 0.66, 'en': 3.44, 'valence': 2, 'group': 16},
        'Zr': {'radius': 1.60, 'en': 1.33, 'valence': 4, 'group': 4},
        'Ti': {'radius': 1.47, 'en': 1.54, 'valence': 4, 'group': 4},
        'Mg': {'radius': 1.60, 'en': 1.31, 'valence': 2, 'group': 2},
        'Ca': {'radius': 1.97, 'en': 1.00, 'valence': 2, 'group': 2},
        'Y':  {'radius': 1.80, 'en': 1.22, 'valence': 3, 'group': 3},
        'La': {'radius': 1.87, 'en': 1.10, 'valence': 3, 'group': 3},
        'Ba': {'radius': 2.16, 'en': 0.89, 'valence': 2, 'group': 2},
        'Sr': {'radius': 2.00, 'en': 0.95, 'valence': 2, 'group': 2},
        'Fe': {'radius': 1.26, 'en': 1.83, 'valence': 2, 'group': 8},
        'Co': {'radius': 1.25, 'en': 1.88, 'valence': 2, 'group': 9},
        'Ni': {'radius': 1.24, 'en': 1.91, 'valence': 2, 'group': 10},
        'Cu': {'radius': 1.28, 'en': 1.90, 'valence': 1, 'group': 11},
        'Zn': {'radius': 1.34, 'en': 1.65, 'valence': 2, 'group': 12},
        'Sn': {'radius': 1.40, 'en': 1.96, 'valence': 2, 'group': 14},
        'Pb': {'radius': 1.75, 'en': 2.33, 'valence': 2, 'group': 14},
        'Nb': {'radius': 1.46, 'en': 1.60, 'valence': 5, 'group': 5},
        'Ta': {'radius': 1.46, 'en': 1.50, 'valence': 5, 'group': 5},
        'Mo': {'radius': 1.39, 'en': 2.16, 'valence': 4, 'group': 6},
        'W':  {'radius': 1.39, 'en': 2.36, 'valence': 4, 'group': 6},
        'V':  {'radius': 1.34, 'en': 1.63, 'valence': 5, 'group': 5},
        'Cr': {'radius': 1.28, 'en': 1.66, 'valence': 3, 'group': 6},
        'Mn': {'radius': 1.27, 'en': 1.55, 'valence': 2, 'group': 7},
        'Sc': {'radius': 1.64, 'en': 1.36, 'valence': 3, 'group': 3},
        'Hf': {'radius': 1.59, 'en': 1.30, 'valence': 4, 'group': 4},
    }
    
    def parse_and_compute(comp_str: str):
        """Parse composition string and compute descriptors."""
        try:
            comp = Composition(comp_str)
            elements = list(comp.elements)
            if not elements:
                return 0, 0, 0, 0, 'Unknown'
            
            radii = []
            ens = []
            valences = []
            cation_radii = []
            cation_groups = []
            
            for elem in elements:
                sym = elem.symbol
                if sym in periodic_data:
                    data = periodic_data[sym]
                    count = comp[sym]
                    radii.extend([data['radius']] * count)
                    ens.extend([data['en']] * count)
                    valences.extend([data['valence']] * count)
                    # Heuristic: Cations are usually metals (groups 1-12, 13-16 metals)
                    # Anions are usually O, N, S, etc.
                    if data['group'] < 16 or sym in ['Al', 'Si']: 
                        cation_radii.append(data['radius'])
                        cation_groups.append(data['group'])
                    else:
                        # It's an anion, check if it's the primary anion
                        pass
                
                else:
                    # Unknown element - skip or default
                    continue
            
            if not radii:
                return 0, 0, 0, 0, 'Unknown'
            
            # Mean Atomic Radius
            mean_radius = sum(radii) / len(radii)
            
            # Electronegativity Std
            mean_en = sum(ens) / len(ens)
            var_en = sum((x - mean_en)**2 for x in ens) / len(ens)
            std_en = var_en ** 0.5
            
            # Valence Electron Concentration (VEC)
            total_valence = sum(valences)
            total_atoms = len(radii)
            vec = total_valence / total_atoms
            
            # Cation Size Variance
            if len(cation_radii) > 1:
                mean_cat = sum(cation_radii) / len(cation_radii)
                var_cat = sum((x - mean_cat)**2 for x in cation_radii) / len(cation_radii)
                cation_var = var_cat
            else:
                cation_var = 0.0
            
            # Primary Anion/Cation Group
            # Simplified: Just return the most common cation group or 'Mixed'
            if cation_groups:
                primary_group = max(set(cation_groups), key=cation_groups.count)
            else:
                primary_group = 'Unknown'
            
            return mean_radius, std_en, vec, cation_var, str(primary_group)
            
        except Exception as e:
            logger.warning(f"Failed to parse composition {comp_str}: {e}")
            return 0, 0, 0, 0, 'Unknown'
    
    # Apply to dataframe
    results = df['composition'].apply(parse_and_compute)
    df['mean_atomic_radius'] = results.apply(lambda x: x[0])
    df['electronegativity_std'] = results.apply(lambda x: x[1])
    df['valence_electron_concentration'] = results.apply(lambda x: x[2])
    df['cation_size_variance'] = results.apply(lambda x: x[3])
    df['primary_anion_cation_group'] = results.apply(lambda x: x[4])
    
    # T020 Validation: Check for missing values in these newly computed descriptors
    descriptor_cols = [
        'mean_atomic_radius', 'electronegativity_std', 
        'valence_electron_concentration', 'cation_size_variance',
        'primary_anion_cation_group'
    ]
    
    for col in descriptor_cols:
        if df[col].isna().any():
            raise ValueError(f"Missing values found in computed descriptor '{col}' after imputation/computation.")
    
    logger.info("Descriptors computed successfully.")
    return df