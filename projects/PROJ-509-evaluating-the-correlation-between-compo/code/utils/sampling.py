from typing import Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np
from .logging import get_logger

logger = get_logger(__name__)

# Periodic table groups for chemical family classification
# Simplified mapping for common elements found in materials
CHEMICAL_FAMILY_MAP = {
    # Alkali Metals
    'Li': 'Alkali', 'Na': 'Alkali', 'K': 'Alkali', 'Rb': 'Alkali', 'Cs': 'Alkali',
    # Alkaline Earth
    'Be': 'Alkaline Earth', 'Mg': 'Alkaline Earth', 'Ca': 'Alkaline Earth', 
    'Sr': 'Alkaline Earth', 'Ba': 'Alkaline Earth',
    # Transition Metals (Grouped broadly for this task)
    'Sc': 'Transition', 'Ti': 'Transition', 'V': 'Transition', 'Cr': 'Transition',
    'Mn': 'Transition', 'Fe': 'Transition', 'Co': 'Transition', 'Ni': 'Transition',
    'Cu': 'Transition', 'Zn': 'Transition', 'Y': 'Transition', 'Zr': 'Transition',
    'Nb': 'Transition', 'Mo': 'Transition', 'Tc': 'Transition', 'Ru': 'Transition',
    'Rh': 'Transition', 'Pd': 'Transition', 'Ag': 'Transition', 'Cd': 'Transition',
    'Hf': 'Transition', 'Ta': 'Transition', 'W': 'Transition', 'Re': 'Transition',
    'Os': 'Transition', 'Ir': 'Transition', 'Pt': 'Transition', 'Au': 'Transition',
    'Hg': 'Transition',
    # Lanthanides
    'La': 'Lanthanide', 'Ce': 'Lanthanide', 'Pr': 'Lanthanide', 'Nd': 'Lanthanide',
    'Pm': 'Lanthanide', 'Sm': 'Lanthanide', 'Eu': 'Lanthanide', 'Gd': 'Lanthanide',
    'Tb': 'Lanthanide', 'Dy': 'Lanthanide', 'Ho': 'Lanthanide', 'Er': 'Lanthanide',
    'Tm': 'Lanthanide', 'Yb': 'Lanthanide', 'Lu': 'Lanthanide',
    # Actinides
    'Ac': 'Actinide', 'Th': 'Actinide', 'Pa': 'Actinide', 'U': 'Actinide',
    'Np': 'Actinide', 'Pu': 'Actinide', 'Am': 'Actinide', 'Cm': 'Actinide',
    'Bk': 'Actinide', 'Cf': 'Actinide', 'Es': 'Actinide', 'Fm': 'Actinide',
    'Md': 'Actinide', 'No': 'Actinide', 'Lr': 'Actinide',
    # Poor Metals
    'Al': 'Poor Metal', 'Ga': 'Poor Metal', 'In': 'Poor Metal', 'Sn': 'Poor Metal',
    'Tl': 'Poor Metal', 'Pb': 'Poor Metal', 'Bi': 'Poor Metal',
    # Metalloids
    'B': 'Metalloid', 'Si': 'Metalloid', 'Ge': 'Metalloid', 'As': 'Metalloid',
    'Sb': 'Metalloid', 'Te': 'Metalloid', 'Po': 'Metalloid',
    # Nonmetals
    'H': 'Nonmetal', 'C': 'Nonmetal', 'N': 'Nonmetal', 'O': 'Nonmetal',
    'F': 'Nonmetal', 'P': 'Nonmetal', 'S': 'Nonmetal', 'Cl': 'Nonmetal',
    'Se': 'Nonmetal', 'Br': 'Nonmetal', 'I': 'Nonmetal', 'At': 'Nonmetal',
    'He': 'Noble Gas', 'Ne': 'Noble Gas', 'Ar': 'Noble Gas', 'Kr': 'Noble Gas',
    'Xe': 'Noble Gas', 'Rn': 'Noble Gas',
}

def get_chemical_family(composition: Any) -> str:
    """
    Determine the primary chemical family of a composition.
    The primary family is determined by the most abundant element.
    
    Args:
        composition: A dictionary of element symbols to counts, or a string representation.
        
    Returns:
        The chemical family string, or 'Unknown' if parsing fails.
    """
    if isinstance(composition, str):
        try:
            import ast
            composition = ast.literal_eval(composition)
        except Exception:
            return 'Unknown'
    
    if not isinstance(composition, dict):
        return 'Unknown'
        
    if not composition:
        return 'Unknown'
        
    # Find the element with the highest count
    most_abundant_element = max(composition, key=composition.get)
    
    return CHEMICAL_FAMILY_MAP.get(most_abundant_element, 'Unknown')

def sample_by_chemical_family(df: pd.DataFrame, target_rows: int, random_state: Optional[int] = None) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Perform stratified sampling on the dataframe based on the chemical family.
    
    This function ensures that the relative distribution of chemical families
    is preserved in the sampled dataset.
    
    Args:
        df: The input DataFrame.
        target_rows: The desired number of rows in the output.
        random_state: Random seed for reproducibility.
        
    Returns:
        A tuple containing:
            - The sampled DataFrame.
            - A dictionary of counts per chemical family in the original dataset.
    """
    if random_state is not None:
        np.random.seed(random_state)
        
    # Add a temporary column for chemical family
    df_temp = df.copy()
    df_temp['chemical_family'] = df_temp['composition'].apply(get_chemical_family)
    
    # Calculate distribution
    family_counts = df_temp['chemical_family'].value_counts().to_dict()
    
    # Determine sample size per family
    total_rows = len(df_temp)
    sampling_ratio = target_rows / total_rows
    
    sampled_dfs = []
    
    for family, count in family_counts.items():
        # Calculate how many rows to take from this family
        sample_count = max(1, int(count * sampling_ratio))
        
        family_df = df_temp[df_temp['chemical_family'] == family]
        
        # Ensure we don't take more than available
        sample_count = min(sample_count, len(family_df))
        
        if sample_count > 0:
            sampled_family = family_df.sample(n=sample_count, random_state=random_state)
            sampled_dfs.append(sampled_family)
    
    if not sampled_dfs:
        logger.warning("No data could be sampled. Returning empty DataFrame.")
        return pd.DataFrame(), family_counts
        
    sampled_df = pd.concat(sampled_dfs, ignore_index=True)
    
    # Drop the temporary column
    sampled_df = sampled_df.drop(columns=['chemical_family'])
    
    logger.info(f"Stratified sampling completed. Target: {target_rows}, Actual: {len(sampled_df)}")
    return sampled_df, family_counts
