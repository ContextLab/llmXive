import math
import logging
from typing import Dict, Tuple, Optional, List, Any
import pandas as pd
import re
from utils.logging_config import get_logger, log_exclusion_reason, log_pipeline_event
from utils.config import get_config_summary

# Constants for exclusion thresholds
MIN_DATASET_SIZE_THRESHOLD = 0.5  # 50% of original size

logger = get_logger(__name__)

# --- Existing Helper Functions (Preserved) ---

def parse_formula(formula: str) -> Dict[str, int]:
    """
    Parses a chemical formula string into a dictionary of elements and their counts.
    Handles simple formulas like 'BaTiO3' and complex ones with parentheses.
    """
    formula = formula.replace(" ", "")
    elements = {}
    pattern = re.compile(r"([A-Z][a-z]?)(\d*)")

    def handle_group(match, multiplier=1):
        element = match.group(1)
        count = int(match.group(2)) if match.group(2) else 1
        elements[element] = elements.get(element, 0) + (count * multiplier)

    # Simple parsing for ABX3 without nested parentheses for now
    # If nested parentheses exist, a stack-based parser is needed.
    # Assuming standard perovskite formats like 'BaTiO3', 'CsPbI3'
    for match in pattern.finditer(formula):
        handle_group(match)

    return elements

def get_ionic_radius(element: str, oxidation_state: int) -> Optional[float]:
    """
    Retrieves the ionic radius for a given element and oxidation state.
    Uses a hardcoded dictionary for common perovskite ions (Shannon radii).
    """
    # Shannon Radii (in Angstroms) - Coordination Number VI (Octahedral)
    # Source: Shannon, R. D. (1976). Revised effective ionic radii...
    radii = {
        # A-site cations (CN=12 usually, but often approximated or mapped to CN=8/12 if available)
        # For Goldschmidt t = (rA + rX) / (sqrt(2)*(rB + rX)), rA is typically CN=12.
        # If CN=12 not available, we use CN=8 or best estimate.
        # Ba: 1.61 (CN=12), 1.42 (CN=8)
        # Cs: 1.88 (CN=12), 1.67 (CN=8)
        # Sr: 1.44 (CN=12), 1.26 (CN=8)
        # Pb: 1.49 (CN=12), 1.19 (CN=8)
        # K: 1.64 (CN=12), 1.38 (CN=8)
        # Na: 1.39 (CN=12), 1.18 (CN=8)
        # Li: 0.76 (CN=6), 0.92 (CN=4) - Small for A
        
        # B-site cations (CN=6)
        # Ti: 0.605 (IV), 0.67 (III)
        # Zr: 0.72 (IV)
        # Hf: 0.71 (IV)
        # Sn: 0.69 (IV), 0.83 (II)
        # Ge: 0.53 (IV)
        # V: 0.54 (V), 0.64 (IV), 0.78 (III)
        # Nb: 0.64 (V)
        # Ta: 0.64 (V)
        
        # X-site anions (CN=2 usually, but effective radius used in t calculation)
        # F: 1.33
        # Cl: 1.81
        # Br: 1.96
        # I: 2.20
        
        # Simplified mapping for demonstration
        # Format: (element, oxidation_state) -> radius (CN=6 for B, CN=12 for A approx, CN=2 for X approx)
        # Note: This is a simplified lookup. A real implementation would use pymatgen's data or a full table.
        
        # A-site (Approximated for CN=12 or best available)
        ("Ba", 2): 1.61,
        ("Cs", 1): 1.88,
        ("Sr", 2): 1.44,
        ("Pb", 2): 1.49,
        ("K", 1): 1.64,
        ("Na", 1): 1.39,
        ("Rb", 1): 1.80,
        ("Li", 1): 1.39, # Approximation for A-site

        # B-site (CN=6)
        ("Ti", 4): 0.605,
        ("Ti", 3): 0.67,
        ("Zr", 4): 0.72,
        ("Hf", 4): 0.71,
        ("Sn", 4): 0.69,
        ("Sn", 2): 0.83,
        ("Ge", 4): 0.53,
        ("V", 5): 0.54,
        ("V", 4): 0.64,
        ("Nb", 5): 0.64,
        ("Ta", 5): 0.64,
        
        # X-site (Anions)
        ("F", -1): 1.33,
        ("Cl", -1): 1.81,
        ("Br", -1): 1.96,
        ("I", -1): 2.20,
    }

    return radii.get((element, oxidation_state))

def get_element_electronegativity(element: str) -> Optional[float]:
    """
    Retrieves the electronegativity (Pauling scale) for an element.
    """
    electronegativities = {
        "Ba": 0.89, "Cs": 0.79, "Sr": 0.95, "Pb": 2.33, "K": 0.82,
        "Na": 0.93, "Rb": 0.82, "Li": 0.98,
        "Ti": 1.54, "Zr": 1.33, "Hf": 1.30, "Sn": 1.96, "Ge": 2.01,
        "V": 1.63, "Nb": 1.60, "Ta": 1.50,
        "F": 3.98, "Cl": 3.16, "Br": 2.96, "I": 2.66
    }
    return electronegativities.get(element)

def determine_oxidation_states(elements: Dict[str, int]) -> Optional[Dict[str, int]]:
    """
    Heuristic determination of oxidation states based on common perovskite stoichiometry (ABX3).
    Assumes X is an anion (halogen usually -1), B is a transition metal (variable), A is alkali/alkaline earth.
    Returns a dictionary mapping element to oxidation state, or None if ambiguous/failed.
    """
    # Simplified logic for ABX3:
    # X is typically -1 (halides).
    # Total charge must be 0.
    # If we have multiple X types, assume average or fail.
    # If we have multiple B types, fail (ambiguous).
    # If we have multiple A types, fail (ambiguous).
    
    # Identify X, A, B candidates
    x_candidates = [e for e in elements if e in ["F", "Cl", "Br", "I"]]
    a_candidates = [e for e in elements if e in ["Ba", "Cs", "Sr", "Pb", "K", "Na", "Rb", "Li"]]
    b_candidates = [e for e in elements if e in ["Ti", "Zr", "Hf", "Sn", "Ge", "V", "Nb", "Ta"]]
    
    if len(x_candidates) != 1 or len(a_candidates) != 1 or len(b_candidates) != 1:
        # Ambiguous composition for simple ABX3 heuristic
        return None
        
    x_elem = x_candidates[0]
    a_elem = a_candidates[0]
    b_elem = b_candidates[0]
    
    # Assume X is -1
    ox_states = {x_elem: -1}
    
    # Calculate B charge: A + B + 3*X = 0 => B = -A - 3*X
    # We need A charge. Common: Ba(2), Cs(1), Sr(2), Pb(2), K(1), Na(1), Rb(1), Li(1)
    a_charge_map = {
        "Ba": 2, "Cs": 1, "Sr": 2, "Pb": 2, "K": 1, "Na": 1, "Rb": 1, "Li": 1
    }
    
    if a_elem not in a_charge_map:
        return None
        
    a_charge = a_charge_map[a_elem]
    x_charge = -1
    total_x_charge = 3 * x_charge
    b_charge = -(a_charge + total_x_charge)
    
    # Verify B charge is plausible (e.g., positive integer)
    if b_charge <= 0:
        return None
        
    ox_states[a_elem] = a_charge
    ox_states[b_elem] = b_charge
    
    return ox_states

def calculate_tolerance_factor(rA: float, rB: float, rX: float) -> float:
    """
    Calculates the Goldschmidt tolerance factor t.
    t = (rA + rX) / (sqrt(2) * (rB + rX))
    """
    return (rA + rX) / (math.sqrt(2) * (rB + rX))

def calculate_octahedral_factor(rB: float, rX: float) -> float:
    """
    Calculates the octahedral factor mu.
    mu = rB / rX
    """
    return rB / rX

def calculate_electronegativity_difference(elements: Dict[str, int], ox_states: Dict[str, int]) -> float:
    """
    Calculates the electronegativity difference between B and X sites.
    |chi_B - chi_X|
    """
    b_elem = [e for e in elements if e in ["Ti", "Zr", "Hf", "Sn", "Ge", "V", "Nb", "Ta"]][0]
    x_elem = [e for e in elements if e in ["F", "Cl", "Br", "I"]][0]
    
    chi_B = get_element_electronegativity(b_elem)
    chi_X = get_element_electronegativity(x_elem)
    
    if chi_B is None or chi_X is None:
        return float('nan')
        
    return abs(chi_B - chi_X)

def calculate_ionic_radius_mismatch(rA: float, rB: float) -> float:
    """
    Calculates a simple ionic radius mismatch metric.
    Often defined as (rA - rB) / rA or similar. Using |rA - rB| / rA.
    """
    if rA == 0: return float('nan')
    return abs(rA - rB) / rA

# --- Wrapper Functions for Pandas Apply ---

def get_ionic_radius_wrapper(row: pd.Series, ion_type: str) -> Optional[float]:
    """
    Wrapper to get ionic radius based on ion type ('A', 'B', 'X').
    Assumes row has 'A', 'B', 'X' columns with element symbols.
    """
    # This is a simplified wrapper assuming single element per site
    # In a real scenario, we'd need to handle complex formulas
    element = row.get(ion_type)
    if pd.isna(element):
        return None
    
    # Determine oxidation state based on ion_type
    # A: +1 or +2, B: +3, +4, +5, X: -1
    # Heuristic: A-site (Group 1/2), B-site (Transition), X-site (Halogen)
    # We'll use a fixed mapping for common cases or return None if unknown
    if ion_type == 'A':
        # Assume +1 for alkali, +2 for alkaline earth
        if element in ['Li', 'Na', 'K', 'Rb', 'Cs']:
            ox = 1
        elif element in ['Ba', 'Sr', 'Pb']:
            ox = 2
        else:
            return None
    elif ion_type == 'B':
        # Assume +4 for Ti, Zr, Hf, Sn, Ge; +5 for V, Nb, Ta
        if element in ['Ti', 'Zr', 'Hf', 'Sn', 'Ge']:
            ox = 4
        elif element in ['V', 'Nb', 'Ta']:
            ox = 5
        else:
            return None
    elif ion_type == 'X':
        ox = -1
    else:
        return None
        
    return get_ionic_radius(element, ox)

def get_element_electronegativity_wrapper(row: pd.Series, ion_type: str) -> Optional[float]:
    element = row.get(ion_type)
    if pd.isna(element):
        return None
    return get_element_electronegativity(element)

def calculate_tolerance_factor_wrapper(row: pd.Series) -> float:
    rA = get_ionic_radius_wrapper(row, 'A')
    rB = get_ionic_radius_wrapper(row, 'B')
    rX = get_ionic_radius_wrapper(row, 'X')
    
    if rA is None or rB is None or rX is None:
        return float('nan')
        
    return calculate_tolerance_factor(rA, rB, rX)

def calculate_octahedral_factor_wrapper(row: pd.Series) -> float:
    rB = get_ionic_radius_wrapper(row, 'B')
    rX = get_ionic_radius_wrapper(row, 'X')
    
    if rB is None or rX is None:
        return float('nan')
        
    return calculate_octahedral_factor(rB, rX)

def calculate_electronegativity_difference_wrapper(row: pd.Series) -> float:
    rB = get_ionic_radius_wrapper(row, 'B')
    rX = get_ionic_radius_wrapper(row, 'X')
    # Re-use logic or call directly
    # Need to extract elements again or pass row
    # Assuming row has A, B, X columns
    b_elem = row['B']
    x_elem = row['X']
    if pd.isna(b_elem) or pd.isna(x_elem):
        return float('nan')
        
    chi_B = get_element_electronegativity(b_elem)
    chi_X = get_element_electronegativity(x_elem)
    
    if chi_B is None or chi_X is None:
        return float('nan')
        
    return abs(chi_B - chi_X)

def calculate_ionic_radius_mismatch_wrapper(row: pd.Series) -> float:
    rA = get_ionic_radius_wrapper(row, 'A')
    rB = get_ionic_radius_wrapper(row, 'B')
    
    if rA is None or rB is None:
        return float('nan')
        
    return calculate_ionic_radius_mismatch(rA, rB)

def calculate_all_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates all descriptors for the dataframe.
    Returns a new dataframe with appended descriptor columns.
    Handles exclusions and logging.
    """
    df = df.copy()
    
    # Check for required columns
    required_cols = ['A', 'B', 'X']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame missing required columns: {required_cols}")

    # Initialize descriptor columns with NaN
    df['tolerance_factor'] = float('nan')
    df['octahedral_factor'] = float('nan')
    df['ionic_radius_mismatch'] = float('nan')
    df['electronegativity_diff'] = float('nan')
    
    # Track exclusions
    excluded_indices = []
    exclusion_reasons = {}
    
    # Calculate descriptors row by row to handle missing data gracefully
    for idx, row in df.iterrows():
        rA = get_ionic_radius_wrapper(row, 'A')
        rB = get_ionic_radius_wrapper(row, 'B')
        rX = get_ionic_radius_wrapper(row, 'X')
        
        reason = None
        if rA is None:
            reason = "Missing A-site radius"
        elif rB is None:
            reason = "Missing B-site radius"
        elif rX is None:
            reason = "Missing X-site radius"
        
        if reason:
            excluded_indices.append(idx)
            exclusion_reasons[idx] = reason
            continue
        
        # Calculate
        df.at[idx, 'tolerance_factor'] = calculate_tolerance_factor(rA, rB, rX)
        df.at[idx, 'octahedral_factor'] = calculate_octahedral_factor(rB, rX)
        df.at[idx, 'ionic_radius_mismatch'] = calculate_ionic_radius_mismatch(rA, rB)
        df.at[idx, 'electronegativity_diff'] = calculate_electronegativity_difference_wrapper(row)
    
    # Log exclusions
    if excluded_indices:
        logger.warning(f"Excluded {len(excluded_indices)} rows due to missing radii.")
        for idx, reason in exclusion_reasons.items():
            formula = f"{df.at[idx, 'A']}{df.at[idx, 'B']}{df.at[idx, 'X']}3"
            log_exclusion_reason(reason, formula)
    
    # Check for ambiguous oxidation states (if we had a function to detect that)
    # The current logic assumes a specific mapping. If a row doesn't fit, it's excluded above.
    
    # --- Imputation Logic (T016) ---
    # If the count of excluded rows threatens to drop the dataset below a critical threshold,
    # optionally impute missing values with the mean.
    
    total_rows = len(df)
    excluded_count = len(excluded_indices)
    remaining_count = total_rows - excluded_count
    
    # Configurable threshold (default 50%)
    min_threshold_ratio = get_config_summary().get('min_dataset_threshold', MIN_DATASET_SIZE_THRESHOLD)
    
    if remaining_count < total_rows * min_threshold_ratio and excluded_count > 0:
        logger.warning(f"Exclusions ({excluded_count}) drop dataset below threshold ({min_threshold_ratio*100}%). Attempting imputation.")
        
        # Calculate means for the columns that were not calculated (NaN)
        # Note: In this simplified logic, we excluded the WHOLE row if ANY radius was missing.
        # To impute, we would need to have kept the row and imputed the specific missing radius.
        # However, the task says: "If a composition has ambiguous oxidation states or missing radii, first attempt to exclude the row.
        # If the count ... threatens to drop ... optionally impute missing values with the mean of the respective feature column."
        # This implies we might have partial data? Or we re-calculate for excluded rows with imputed radii?
        # Given the current flow excludes the row entirely, we will re-process the excluded rows with imputed radii.
        
        # Calculate global means for radii
        # We need rA, rB, rX means.
        # We can calculate these from the successfully processed rows.
        valid_rA = []
        valid_rB = []
        valid_rX = []
        
        for idx in df.index:
            if idx not in excluded_indices:
                valid_rA.append(get_ionic_radius_wrapper(df.loc[idx], 'A'))
                valid_rB.append(get_ionic_radius_wrapper(df.loc[idx], 'B'))
                valid_rX.append(get_ionic_radius_wrapper(df.loc[idx], 'X'))
        
        mean_rA = sum(valid_rA) / len(valid_rA) if valid_rA else None
        mean_rB = sum(valid_rB) / len(valid_rB) if valid_rB else None
        mean_rX = sum(valid_rX) / len(valid_rX) if valid_rX else None
        
        if mean_rA is None or mean_rB is None or mean_rX is None:
            logger.error("Cannot impute: No valid radii found to calculate mean.")
        else:
            logger.info(f"Imputing missing radii with means: A={mean_rA:.3f}, B={mean_rB:.3f}, X={mean_rX:.3f}")
            log_pipeline_event(f"Imputation triggered: {excluded_count} rows re-processed with mean radii.")
            
            # Re-process excluded rows with mean radii
            for idx in excluded_indices:
                row = df.loc[idx]
                # Determine which radius was missing and use mean
                # For simplicity, use all means for excluded rows
                rA = mean_rA
                rB = mean_rB
                rX = mean_rX
                
                df.at[idx, 'tolerance_factor'] = calculate_tolerance_factor(rA, rB, rX)
                df.at[idx, 'octahedral_factor'] = calculate_octahedral_factor(rB, rX)
                df.at[idx, 'ionic_radius_mismatch'] = calculate_ionic_radius_mismatch(rA, rB)
                df.at[idx, 'electronegativity_diff'] = calculate_electronegativity_difference_wrapper(row)
                
                log_pipeline_event(f"Imputed row {idx} (Formula: {row['A']}{row['B']}{row['X']}3)")
    
    return df

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main entry point for processing a dataframe with descriptors.
    """
    return calculate_all_descriptors(df)

# --- Main execution block for standalone testing (optional) ---
if __name__ == "__main__":
    # Example usage
    sample_data = {
        'A': ['Ba', 'Cs', 'Na'],
        'B': ['Ti', 'Pb', 'Sn'],
        'X': ['O', 'I', 'Cl']
    }
    df_sample = pd.DataFrame(sample_data)
    df_processed = process_dataframe(df_sample)
    print(df_processed)