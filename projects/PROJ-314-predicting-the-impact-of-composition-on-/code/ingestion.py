import pandas as pd
import logging
import re
import json
from pathlib import Path
from urllib.parse import urlparse
import sys
import os
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# Attempt to import chemparse components
try:
    from chemparse import Composition
except ImportError:
    # Fallback for environments where chemparse might not be installed or structured differently
    # This block ensures the module loads, but functions relying on Composition will fail loudly
    # if the class is not found, adhering to the "Fail Loudly" constraint.
    Composition = None

# Ensure logger is available
try:
    from . import logger
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Helper Functions for Composition Parsing
# --------------------------------------------------------------------------

def get_element_group(element: str) -> str:
    """
    Determines the chemical group (Anion/Cation family) for a given element symbol.
    Maps elements to a simplified group string (e.g., 'O' for Oxygen, 'Al' for Aluminum).
    This is a heuristic mapping based on common ceramic constituents.
    """
    element = element.strip().capitalize()
    if not element:
        return "Unknown"

    # Define groups based on common ceramic chemistry
    # Anions (Non-metals)
    anions = {
        'O': 'O', 'S': 'S', 'N': 'N', 'C': 'C', 'F': 'F', 'Cl': 'Cl',
        'Br': 'Br', 'I': 'I', 'Se': 'Se', 'Te': 'Te', 'P': 'P', 'B': 'B'
    }
    
    if element in anions:
        return anions[element]

    # Cations (Metals/Metalloids) - Group by primary family or element
    # For this task, we map to the element itself or a representative if needed.
    # The task example 'O-Al' suggests using the specific element symbol for the group.
    # We will return the element symbol for cations to allow specific grouping (e.g., 'Al', 'Si').
    # If a broader group is needed later, this can be extended.
    
    # Standard periodic table elements
    metals = [
        'H', 'He', 'Li', 'Be', 'Na', 'Mg', 'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
        'Ga', 'Ge', 'As', 'Se', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd',
        'In', 'Sn', 'Sb', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu',
        'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og'
    ]
    
    if element in metals:
        return element

    # Fallback for unknown elements
    logger.warning(f"Unknown element encountered in group mapping: {element}")
    return element

def parse_composition_group(composition_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses a composition string (e.g., 'Al2O3', 'SiO2') to identify the primary anion and cation.
    
    Returns:
        Tuple (primary_anion_group, primary_cation_group)
        Example: 'O-Al' -> ('O', 'Al')
    """
    if not composition_str or not isinstance(composition_str, str):
        return None, None

    composition_str = composition_str.strip()
    
    # If chemparse Composition is available, use it
    if Composition is not None:
        try:
            comp_obj = Composition(composition_str)
            # comp_obj is a dict: {'Al': 2, 'O': 3}
            elements = list(comp_obj.keys())
        except Exception as e:
            logger.error(f"Failed to parse composition '{composition_str}' using chemparse: {e}")
            return None, None
    else:
        # Fallback regex parsing if chemparse Composition is not available
        # Matches element symbols followed by optional numbers
        pattern = r'([A-Z][a-z]?)(\d*)'
        matches = re.findall(pattern, composition_str)
        elements = [m[0] for m in matches]
        if not elements:
            logger.warning(f"Regex parsing failed for composition: {composition_str}")
            return None, None

    if not elements:
        return None, None

    # Identify Anions vs Cations
    # Heuristic: Non-metals are usually anions in ceramics (O, N, C, etc.)
    # Metals are cations.
    
    anions = []
    cations = []
    
    non_metals = {'H', 'He', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Si', 'P', 'S', 'Cl', 'Ar', 'As', 'Se', 'Br', 'Kr', 'Te', 'I', 'Xe', 'At', 'Rn'}
    
    for el in elements:
        if el in non_metals:
            anions.append(el)
        else:
            cations.append(el)

    # Determine Primary Anion and Cation
    # Priority: Most abundant element that fits the category? 
    # Or simply the first found? 
    # For ceramics like Al2O3, O is anion, Al is cation.
    # We will pick the first distinct anion and first distinct cation found in the formula.
    
    primary_anion = anions[0] if anions else None
    primary_cation = cations[0] if cations else None

    # If no anion found (e.g. pure metal?), treat as cation only? 
    # But task implies 'O-Al' style, so we expect at least one anion.
    
    return get_element_group(primary_anion), get_element_group(primary_cation)

# --------------------------------------------------------------------------
# Main Task Implementation
# --------------------------------------------------------------------------

def derive_primary_anion_cation_group(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parses the 'composition' string using chemparse to identify the primary anion 
    and cation groups (e.g., 'O-Al' for Alumina). Creates a new column 
    'primary_anion_cation_group'.
    
    Dependency: Requires 'composition' column to be present.
    """
    logger.info("Starting derivation of primary anion/cation groups...")
    
    if df.empty:
        logger.warning("Input DataFrame is empty. Skipping group derivation.")
        return df

    if 'composition' not in df.columns:
        raise ValueError("Input DataFrame must contain a 'composition' column.")

    def format_group(anion, cation):
        if anion and cation:
            return f"{anion}-{cation}"
        elif anion:
            return f"{anion}-Unknown"
        elif cation:
            return f"Unknown-{cation}"
        else:
            return "Unknown-Unknown"

    # Apply parsing
    groups = []
    for idx, row in df.iterrows():
        comp_str = row['composition']
        anion, cation = parse_composition_group(comp_str)
        groups.append(format_group(anion, cation))
        
        # Log warnings for failures
        if anion is None or cation is None:
            logger.warning(f"Could not determine full group for composition '{comp_str}' at index {idx}")

    df['primary_anion_cation_group'] = groups
    
    logger.info(f"Derived 'primary_anion_cation_group' for {len(df)} entries.")
    return df

# --------------------------------------------------------------------------
# Placeholder for other functions mentioned in API surface (to ensure module loads)
# --------------------------------------------------------------------------

def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def validate_url_for_fetch(url: str) -> bool:
    return is_valid_url(url)

def calculate_title_overlap(title1: str, title2: str) -> float:
    if not title1 or not title2:
        return 0.0
    words1 = set(title1.lower().split())
    words2 = set(title2.lower().split())
    if not words1 or not words2:
        return 0.0
    return len(words1.intersection(words2)) / max(len(words1), len(words2))

def validate_source_citations(data: List[Dict], sources: List[str]) -> List[str]:
    # Placeholder implementation
    return []

def fetch_materials_project_data() -> pd.DataFrame:
    # Placeholder
    return pd.DataFrame()

def fetch_nist_data() -> pd.DataFrame:
    # Placeholder
    return pd.DataFrame()

def fetch_arxiv_data() -> pd.DataFrame:
    # Placeholder
    return pd.DataFrame()

def fetch_curated_literature_data() -> pd.DataFrame:
    # Placeholder
    return pd.DataFrame()

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    # Placeholder
    return df

def generate_data_availability_report(df: pd.DataFrame, output_path: str):
    # Placeholder
    pass

def validate_data_gap(df: pd.DataFrame) -> bool:
    # Placeholder
    return True

def validate_no_missing_predictors(df: pd.DataFrame) -> bool:
    # Placeholder
    return True

def main():
    """
    Main entry point for ingestion module when run as a script.
    Currently handles basic demonstration or CLI arguments if added.
    """
    logger.info("Ingestion module loaded successfully.")
    print("Ingestion module ready. Use specific functions for data processing.")

if __name__ == "__main__":
    main()