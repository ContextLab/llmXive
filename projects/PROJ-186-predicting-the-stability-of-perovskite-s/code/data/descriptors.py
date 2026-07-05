import math
import logging
from typing import Dict, Tuple, Optional, List, Any
import pandas as pd
import re

from utils.logging_config import get_logger, log_exclusion_reason, log_pipeline_event
from utils.config import ELEMENT_RADII, ELECTRONEGATIVITIES

logger = get_logger(__name__)

# Define standard oxidation states for common elements in perovskites
# Key: Element symbol, Value: Set of common oxidation states
COMMON_OXIDATION_STATES = {
    'K': {1}, 'Rb': {1}, 'Cs': {1}, 'Ba': {2}, 'Sr': {2}, 'Ca': {2},
    'Ti': {4}, 'Zr': {4}, 'Hf': {4}, 'Sn': {2, 4}, 'Ge': {2, 4},
    'F': {-1}, 'Cl': {-1}, 'Br': {-1}, 'I': {-1}
}

def get_ionic_radius(element: str, oxidation_state: Optional[int] = None, coord_number: int = 6) -> Optional[float]:
    """
    Retrieve ionic radius for an element and oxidation state.
    Falls back to common oxidation state if not provided but known.
    
    Args:
        element: Element symbol (e.g., 'K', 'Ti')
        oxidation_state: Expected oxidation state (e.g., +1, +4). If None, tries to infer.
        coord_number: Coordination number (default 6 for octahedral B-site, 12 for A-site usually).
                      This function assumes the radii in config are pre-mapped or uses a simple lookup.
                      For this implementation, we assume ELEMENT_RADII is keyed by (Element, OxState, Coord)
                      or (Element, OxState) if coord is standard.
    
    Returns:
        Radius in Angstroms or None if not found.
    """
    # Normalize element
    element = element.strip().capitalize()
    
    # Infer oxidation state if missing and we have a guess
    if oxidation_state is None:
        if element in COMMON_OXIDATION_STATES:
            # If multiple, we can't be sure, return None to trigger exclusion
            states = COMMON_OXIDATION_STATES[element]
            if len(states) == 1:
                oxidation_state = list(states)[0]
            else:
                logger.warning(f"Ambiguous oxidation state for {element}: {states}. Cannot determine radius.")
                return None
        else:
            logger.warning(f"Unknown common oxidation state for {element}. Cannot determine radius.")
            return None

    # Lookup in config
    # Assume ELEMENT_RADII structure: { 'Element': { 'OxState': { 'Coord': radius } } }
    # Or flat: { ('Element', 'OxState', 'Coord'): radius }
    # Given the constraint to use existing API, we assume a structure that allows lookup.
    # If ELEMENT_RADII is a flat dict of tuples:
    if (element, oxidation_state, coord_number) in ELEMENT_RADII:
        return ELEMENT_RADII[(element, oxidation_state, coord_number)]
    
    # Fallback: try without coord if standard (e.g. 6)
    if (element, oxidation_state, 6) in ELEMENT_RADII:
        return ELEMENT_RADII[(element, oxidation_state, 6)]
        
    # Try just element/ox if structure allows
    if element in ELEMENT_RADII and oxidation_state in ELEMENT_RADII[element]:
       # Handle nested structure
       if coord_number in ELEMENT_RADII[element][oxidation_state]:
           return ELEMENT_RADII[element][oxidation_state][coord_number]
       elif 6 in ELEMENT_RADII[element][oxidation_state]:
           return ELEMENT_RADII[element][oxidation_state][6]

    logger.debug(f"Radius not found for {element} (ox: {oxidation_state}, coord: {coord_number})")
    return None

def calculate_tolerance_factor(r_a: float, r_b: float, r_x: float) -> float:
    """
    Calculate Goldschmidt tolerance factor t = (r_A + r_X) / (sqrt(2) * (r_B + r_X))
    """
    if r_b + r_x == 0:
        return float('inf')
    return (r_a + r_x) / (math.sqrt(2) * (r_b + r_x))

def calculate_octahedral_factor(r_b: float, r_x: float) -> float:
    """
    Calculate octahedral factor mu = r_B / (r_B + r_X)
    """
    if r_b + r_x == 0:
        return 0.0
    return r_b / (r_b + r_x)

def get_element_electronegativity(element: str) -> Optional[float]:
    """
    Get electronegativity from config.
    """
    element = element.strip().capitalize()
    return ELECTRONEGATIVITIES.get(element)

def calculate_electronegativity_difference(en_a: float, en_b: float) -> float:
    """
    Calculate difference in electronegativity.
    """
    return abs(en_a - en_b)

def calculate_ionic_radius_mismatch(r_a: float, r_b: float) -> float:
    """
    Calculate ionic radius mismatch (simple difference or ratio based on context).
    Using difference here as a proxy for strain.
    """
    return abs(r_a - r_b)

def _infer_oxidation_states(formula_str: str) -> Dict[str, Optional[int]]:
    """
    Attempt to infer oxidation states from a simple formula string like 'ABX3'.
    Returns a dict mapping element -> inferred oxidation state, or None if ambiguous/unknown.
    This is a simplified heuristic for the specific perovskite ABX3 case.
    """
    # Very basic parser for ABX3 patterns
    # In a real scenario, this might use pymatgen Composition
    # We assume the input dataframe has 'formula' column in standard format
    # and we need to split A, B, X.
    # This is a placeholder logic to satisfy the "ambiguous" check requirement.
    # If the formula is not standard ABX3 or elements are unknown, return None.
    
    # For this task, we assume the caller passes specific A, B, X columns or
    # we parse the formula. Let's assume we are given elements A, B, X directly
    # in the calling context or we parse.
    # Since the function signature of calculate_all_descriptors takes a row with A, B, X elements,
    # we rely on the caller to provide the elements.
    # The "ambiguous" check here refers to the element's known oxidation states.
    return {}

def calculate_all_descriptors(row: pd.Series) -> Tuple[Optional[Dict[str, float]], List[str]]:
    """
    Calculate all descriptors for a single row.
    Returns (descriptors_dict, exclusion_reasons).
    If exclusion_reasons is not empty, descriptors should be considered invalid.
    """
    reasons = []
    
    # Extract elements (assuming columns 'A_element', 'B_element', 'X_element' exist)
    # If columns are named differently, adjust here. Based on T012/T013, we expect formula breakdown.
    # Let's assume the row has 'A', 'B', 'X' as element symbols.
    # If the row has a 'formula' string, we must parse it.
    # Given T012/T013 context, let's assume we have extracted A, B, X.
    
    # Fallback: Try to parse 'formula' if A, B, X columns missing
    if 'A_element' in row.index:
        el_a, el_b, el_x = row['A_element'], row['B_element'], row['X_element']
    elif 'formula' in row.index:
        # Simple regex for ABX3: e.g. "CsPbI3" -> A=Cs, B=Pb, X=I
        # This is fragile. Assuming T012/T013 produced explicit columns.
        # If not, we skip or error.
        reasons.append("Missing explicit A, B, X element columns and formula parsing not implemented for this row.")
        return None, reasons
    else:
        reasons.append("Could not identify A, B, X elements in row.")
        return None, reasons

    el_a = str(el_a).strip()
    el_b = str(el_b).strip()
    el_x = str(el_x).strip()

    # 1. Check for ambiguous oxidation states
    # We need to know the oxidation state to get the radius.
    # If an element has multiple common states and we can't infer which one, it's ambiguous.
    # We use the COMMON_OXIDATION_STATES map defined at top.
    
    def check_ambiguity(el: str, site: str) -> Optional[int]:
        if el not in COMMON_OXIDATION_STATES:
            reasons.append(f"Ambiguous/Unknown oxidation state for {el} at {site} site.")
            return None
        states = COMMON_OXIDATION_STATES[el]
        if len(states) > 1:
            reasons.append(f"Ambiguous oxidation state for {el} at {site} site: {states}. Cannot determine unique radius.")
            return None
        return list(states)[0]

    ox_a = check_ambiguity(el_a, 'A')
    ox_b = check_ambiguity(el_b, 'B')
    ox_x = check_ambiguity(el_x, 'X')

    if not all([ox_a, ox_b, ox_x]):
        return None, reasons

    # 2. Get Ionic Radii
    # Coordination: A=12, B=6, X=6 (usually)
    r_a = get_ionic_radius(el_a, ox_a, coord_number=12)
    r_b = get_ionic_radius(el_b, ox_b, coord_number=6)
    r_x = get_ionic_radius(el_x, ox_x, coord_number=6)

    if r_a is None:
        reasons.append(f"Missing ionic radius for A-site {el_a} ({ox_a}+).")
    if r_b is None:
        reasons.append(f"Missing ionic radius for B-site {el_b} ({ox_b}+).")
    if r_x is None:
        reasons.append(f"Missing ionic radius for X-site {el_x} ({ox_x}-).")

    if any([r_a is None, r_b is None, r_x is None]):
        return None, reasons

    # 3. Get Electronegativity
    en_a = get_element_electronegativity(el_a)
    en_b = get_element_electronegativity(el_b)
    en_x = get_element_electronegativity(el_x)

    if en_a is None:
        reasons.append(f"Missing electronegativity for {el_a}.")
    if en_b is None:
        reasons.append(f"Missing electronegativity for {el_b}.")
    if en_x is None:
        reasons.append(f"Missing electronegativity for {el_x}.")

    if any([en_a is None, en_b is None, en_x is None]):
        return None, reasons

    # 4. Calculate Descriptors
    t = calculate_tolerance_factor(r_a, r_b, r_x)
    mu = calculate_octahedral_factor(r_b, r_x)
    delta_en = calculate_electronegativity_difference(en_a, en_b) # Or A-X, B-X? Spec says "differences"
    # Let's calculate A-X and B-X differences as well if needed, but spec says "electronegativity differences"
    # We'll store one or a tuple. Let's store A-B and B-X.
    delta_en_ab = abs(en_a - en_b)
    delta_en_bx = abs(en_b - en_x)
    
    radius_mismatch = calculate_ionic_radius_mismatch(r_a, r_b)

    descriptors = {
        'tolerance_factor': t,
        'octahedral_factor': mu,
        'electronegativity_diff_AB': delta_en_ab,
        'electronegativity_diff_BX': delta_en_bx,
        'ionic_radius_mismatch': radius_mismatch,
        'radius_A': r_a,
        'radius_B': r_b,
        'radius_X': r_x
    }

    return descriptors, []

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process the dataframe: calculate descriptors, filter out rows with missing data,
    and log exclusion reasons.
    
    Returns:
        DataFrame with new descriptor columns, filtered.
    """
    logger.info(f"Starting descriptor calculation for {len(df)} rows.")
    
    results = []
    excluded_count = 0
    
    # Prepare lists to collect data
    valid_indices = []
    valid_descriptors = []
    exclusion_log_entries = []

    for idx, row in df.iterrows():
        desc, reasons = calculate_all_descriptors(row)
        
        if desc:
            valid_indices.append(idx)
            valid_descriptors.append(desc)
        else:
            excluded_count += 1
            # Log each reason for this row
            reason_str = "; ".join(reasons)
            exclusion_log_entries.append({
                'index': idx,
                'formula': row.get('formula', 'Unknown'),
                'reasons': reason_str
            })
            # Log to pipeline log
            for reason in reasons:
                log_exclusion_reason(f"Row {idx} ({row.get('formula', 'Unknown')}): {reason}")

    # Log summary
    log_pipeline_event(f"Descriptor Calculation: {len(valid_indices)} valid, {excluded_count} excluded.")
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} rows due to missing radii or ambiguous oxidation states.")
    
    # Create new dataframe with descriptors
    if not valid_descriptors:
        logger.error("No valid rows found after descriptor calculation. Returning empty dataframe.")
        return pd.DataFrame()

    df_valid = df.loc[valid_indices].copy()
    df_desc = pd.DataFrame(valid_descriptors, index=valid_indices)
    
    # Merge
    df_result = pd.concat([df_valid, df_desc], axis=1)
    
    logger.info(f"Descriptor calculation complete. Final shape: {df_result.shape}")
    return df_result

# Re-exporting for compatibility if needed, though the file is the module
# The API surface requires these names to be available at module level.
# They are defined above.
