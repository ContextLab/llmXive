"""
Sampling utilities for stratified sampling by chemical family.
"""
from typing import Optional, Tuple, Dict, Any

import pandas as pd
import numpy as np

from .logging import get_logger

logger = get_logger(__name__)


def get_chemical_family(composition: str) -> Optional[str]:
    """
    Determine the chemical family based on the most abundant element.

    This is a simplified heuristic. In a real production system, this would
    map to a proper periodic table group or a predefined taxonomy.

    Args:
        composition: Composition string (e.g., "Fe2O3").

    Returns:
        A string representing the chemical family (e.g., "Transition Metal Oxide"),
        or None if the element cannot be parsed.
    """
    if not composition or not isinstance(composition, str):
        return None

    # Simple parsing: assume format like "Fe2O3" or "SiO2"
    # We look for the first element symbol (1 or 2 uppercase/lowercase chars)
    # followed by numbers.
    # This is a naive implementation for demonstration.
    # A robust solution would use pymatgen's Composition parser.

    import re
    # Match element symbol: 1 upper + optional 1 lower
    match = re.match(r'([A-Z][a-z]?)', composition)
    if not match:
        return "Unknown"

    element = match.group(1)

    # Heuristic mapping (simplified)
    # Transition metals: Sc, Ti, V, Cr, Mn, Fe, Co, Ni, Cu, Zn, Y, Zr, Nb, Mo, Tc, Ru, Rh, Pd, Ag, Cd, Hf, Ta, W, Re, Os, Ir, Pt, Au, Hg
    transition_metals = {
        'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
        'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd',
        'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg'
    }

    # Alkali metals: Li, Na, K, Rb, Cs, Fr
    alkali_metals = {'Li', 'Na', 'K', 'Rb', 'Cs', 'Fr'}

    # Alkaline earth: Be, Mg, Ca, Sr, Ba, Ra
    alkaline_earth = {'Be', 'Mg', 'Ca', 'Sr', 'Ba', 'Ra'}

    # Lanthanides/Actinides
    f_block = {'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu',
               'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr'}

    # Halogens: F, Cl, Br, I, At
    halogens = {'F', 'Cl', 'Br', 'I', 'At'}

    # Noble gases: He, Ne, Ar, Kr, Xe, Rn
    noble_gases = {'He', 'Ne', 'Ar', 'Kr', 'Xe', 'Rn'}

    # Chalcogens: O, S, Se, Te, Po
    chalcogens = {'O', 'S', 'Se', 'Te', 'Po'}

    # Pnictogens: N, P, As, Sb, Bi
    pnictogens = {'N', 'P', 'As', 'Sb', 'Bi'}

    if element in transition_metals:
        return "Transition Metal"
    elif element in alkali_metals:
        return "Alkali Metal"
    elif element in alkaline_earth:
        return "Alkaline Earth"
    elif element in f_block:
        return "Lanthanide/Actinide"
    elif element in halogens:
        return "Halogen"
    elif element in noble_gases:
        return "Noble Gas"
    elif element in chalcogens:
        return "Chalcogen"
    elif element in pnictogens:
        return "Pnictogen"
    else:
        return "Other"


def sample_by_chemical_family(
    df: pd.DataFrame,
    target_rows: int,
    random_state: Optional[int] = None
) -> pd.DataFrame:
    """
    Perform stratified sampling by the most abundant element (chemical family).

    Args:
        df: Input DataFrame with a 'composition' column.
        target_rows: Target number of rows in the sampled dataset.
        random_state: Random seed for reproducibility.

    Returns:
        A new DataFrame with stratified samples.
    """
    if random_state is not None:
        np.random.seed(random_state)

    if df.empty:
        logger.warning("Input DataFrame is empty.")
        return df

    # Calculate chemical family for each row
    # Assuming 'composition' column exists
    if 'composition' not in df.columns:
        raise ValueError("DataFrame must contain a 'composition' column.")

    df = df.copy()
    df['_chem_family'] = df['composition'].apply(get_chemical_family)

    # Drop rows with unknown family if necessary, or keep them as a group
    # Here we keep them in "Unknown" or "Other"
    df['_chem_family'] = df['_chem_family'].fillna('Unknown')

    # Calculate proportions
    family_counts = df['_chem_family'].value_counts(normalize=True)

    # Determine sample size per family
    sample_sizes = (family_counts * target_rows).round().astype(int)

    # Ensure we don't exceed available rows
    for family in sample_sizes.index:
        available = len(df[df['_chem_family'] == family])
        if sample_sizes[family] > available:
            sample_sizes[family] = available

    # Adjust to hit target_rows exactly if possible (simple proportional adjustment)
    current_total = sample_sizes.sum()
    if current_total != target_rows:
        diff = target_rows - current_total
        # Sort by available count to pick which groups to add/remove from
        # Simple approach: add to largest groups if needed
        if diff > 0:
            # Try to add more from families that have remaining capacity
            sorted_families = family_counts.sort_values(ascending=False).index
            for fam in sorted_families:
                if diff <= 0:
                    break
                available = len(df[df['_chem_family'] == fam])
                needed = available - sample_sizes[fam]
                add = min(needed, diff)
                sample_sizes[fam] += add
                diff -= add
        elif diff < 0:
            # Remove from smallest groups first
            sorted_families = family_counts.sort_values(ascending=True).index
            for fam in sorted_families:
                if diff >= 0:
                    break
                remove = min(sample_sizes[fam], abs(diff))
                sample_sizes[fam] -= remove
                diff += remove

    # Sample
    sampled_dfs = []
    for family, n in sample_sizes.items():
        if n == 0:
            continue
        subset = df[df['_chem_family'] == family]
        if n >= len(subset):
            sampled_dfs.append(subset)
        else:
            sampled_dfs.append(subset.sample(n=n, random_state=random_state))

    result = pd.concat(sampled_dfs, ignore_index=True)

    # Drop the helper column
    result = result.drop(columns=['_chem_family'])

    logger.info(f"Sampled {len(result)} rows from {len(df)} original rows by chemical family.")

    return result
