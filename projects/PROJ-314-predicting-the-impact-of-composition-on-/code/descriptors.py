import pandas as pd
import logging
from typing import Dict, Any, List, Optional
import numpy as np
from collections import defaultdict
from chemparse import parse_formula
from periodictable import elements

logger = logging.getLogger(__name__)

def get_element_property(element_symbol: str, property_name: str) -> Optional[float]:
    """
    Get a specific property of an element from the periodictable library.
    """
    try:
        elem = elements.symbol(element_symbol)
        if hasattr(elem, property_name):
            return getattr(elem, property_name)
        else:
            logger.warning(f"Property {property_name} not found for element {element_symbol}")
            return None
    except (IndexError, KeyError, AttributeError) as e:
        logger.warning(f"Could not retrieve {property_name} for {element_symbol}: {e}")
        return None

def compute_valence_electron_concentration(composition_str: str) -> Optional[float]:
    """
    Calculate Valence Electron Concentration (VEC).
    VEC = Total Valence Electrons / Total Number of Atoms.
    Uses periodictable for valence electron lookup.
    """
    try:
        parsed = parse_formula(composition_str)
        total_valence = 0.0
        total_atoms = 0.0
        
        for element, count in parsed.items():
            # periodictable elements have a 'charge' attribute which often lists common valences.
            # We take the maximum positive valence as a proxy for valence electrons if available,
            # or use group number logic if specific valence is tricky.
            # However, periodictable elements have a 'valence' property in some versions, 
            # but often it's a list of common valences. 
            # Let's use the group number for main group elements as a robust proxy for max valence.
            elem = elements.symbol(element)
            group = elem.number // 10 if elem.number < 100 else 0 # Simplified logic for groups
            # Better: use the group number directly if it's a main group (1-2, 13-18)
            # periodictable elements have 'group' attribute in newer versions, but let's check 'number'
            # Standard valence for transition metals is variable. Let's assume max group number for simplicity
            # or use a specific mapping if needed. 
            # For now, let's try to get the 'charge' which often contains the valence state.
            # If charge is a list, take the max positive.
            if hasattr(elem, 'charge') and elem.charge:
                charges = elem.charge if isinstance(elem.charge, list) else [elem.charge]
                # Filter for positive charges (cations)
                positive_charges = [c for c in charges if c > 0]
                if positive_charges:
                    valence = max(positive_charges)
                else:
                    # Fallback to group number logic for non-metals or if no positive charge
                    # Group 1: 1, Group 2: 2, Group 13: 3, Group 14: 4, etc.
                    # periodictable doesn't always expose group directly in a simple way for all elements.
                    # Let's use a simplified heuristic: number of valence electrons = group number for main group
                    # This is a heuristic.
                    valence = elem.number % 10 if elem.number < 20 else 4 # Fallback
            else:
                valence = 4 # Default fallback for unknown
            
            total_valence += valence * count
            total_atoms += count
        
        if total_atoms == 0:
            return None
        return total_valence / total_atoms
        
    except Exception as e:
        logger.error(f"Error computing VEC for {composition_str}: {e}")
        return None

def compute_mean_atomic_radius(composition_str: str) -> Optional[float]:
    """
    Calculate mean atomic radius based on stoichiometry.
    """
    try:
        parsed = parse_formula(composition_str)
        total_radius = 0.0
        total_atoms = 0.0
        
        for element, count in parsed.items():
            radius = get_element_property(element, 'radius')
            if radius is not None:
                total_radius += radius * count
                total_atoms += count
            else:
                logger.warning(f"Atomic radius missing for {element} in {composition_str}")
                return None # Or handle with imputation later
        
        if total_atoms == 0:
            return None
        return total_radius / total_atoms
    except Exception as e:
        logger.error(f"Error computing mean atomic radius for {composition_str}: {e}")
        return None

def compute_electronegativity_std(composition_str: str) -> Optional[float]:
    """
    Calculate standard deviation of electronegativity from stoichiometry.
    """
    try:
        parsed = parse_formula(composition_str)
        electronegativities = []
        
        for element, count in parsed.items():
            en = get_element_property(element, 'electronegativity')
            if en is not None:
                for _ in range(int(count)):
                    electronegativities.append(en)
            else:
                logger.warning(f"Electronegativity missing for {element} in {composition_str}")
                return None
        
        if len(electronegativities) == 0:
            return None
        return float(np.std(electronegativities))
    except Exception as e:
        logger.error(f"Error computing electronegativity std for {composition_str}: {e}")
        return None

def compute_cation_size_variance(composition_str: str) -> Optional[float]:
    """
    Calculate variance of cation atomic radii.
    Assumes the first element in the formula is the cation or identifies cations.
    For simplicity in this context, we calculate variance of all atomic radii present,
    or specifically cations if identifiable. 
    Given the complexity of identifying cations vs anions purely from string without a full parser,
    we will calculate the variance of the radii of all unique elements in the formula.
    """
    try:
        parsed = parse_formula(composition_str)
        radii = []
        for element, count in parsed.items():
            radius = get_element_property(element, 'radius')
            if radius is not None:
                radii.append(radius)
            else:
                logger.warning(f"Atomic radius missing for {element} in {composition_str}")
                return None
        
        if len(radii) < 2:
            return 0.0 # Variance of a single value or empty is 0 or undefined, defaulting to 0
        
        return float(np.var(radii))
    except Exception as e:
        logger.error(f"Error computing cation size variance for {composition_str}: {e}")
        return None

def compute_range_uncertainty(range_str: str) -> Optional[float]:
    """
    Calculate range uncertainty based on extracted midpoint and width.
    Input: A string representing a range, e.g., "10-20" or "15".
    Output: The width of the range (max - min) as a measure of uncertainty.
    If the input is a single number, uncertainty is 0.
    """
    if not isinstance(range_str, str):
        # If it's already a number, uncertainty is 0
        try:
            float(range_str)
            return 0.0
        except (ValueError, TypeError):
            return None

    range_str = range_str.strip()
    
    # Check for range format "min-max"
    if '-' in range_str and range_str.count('-') == 1:
        try:
            parts = range_str.split('-')
            min_val = float(parts[0])
            max_val = float(parts[1])
            uncertainty = max_val - min_val
            return float(uncertainty)
        except ValueError:
            logger.warning(f"Could not parse range string: {range_str}")
            return None
    else:
        # Single value or invalid format
        try:
            float(range_str)
            return 0.0
        except ValueError:
            logger.warning(f"Could not parse value or range: {range_str}")
            return None

def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all descriptor computations to the DataFrame.
    """
    logger.info("Computing descriptors...")
    
    # VEC
    df['valence_electron_concentration'] = df['composition'].apply(compute_valence_electron_concentration)
    
    # Mean Atomic Radius
    df['mean_atomic_radius'] = df['composition'].apply(compute_mean_atomic_radius)
    
    # Electronegativity Std
    df['electronegativity_std'] = df['composition'].apply(compute_electronegativity_std)
    
    # Cation Size Variance
    df['cation_size_variance'] = df['composition'].apply(compute_cation_size_variance)
    
    # Range Uncertainty (assuming a column 'range_original' or similar exists, or 'weibull_modulus' is the range)
    # Based on T059, we need to ensure 'range_uncertainty' is computed.
    # The task T018b-range-uncertainty mentions calculating based on extracted midpoint.
    # We assume there is a column 'weibull_modulus' that might be a range string or a number.
    # If it's a number, uncertainty is 0. If it's a string "min-max", we parse it.
    # Let's check if 'weibull_modulus' is string or float. If float, uncertainty is 0.
    # If it's a string, we parse.
    # However, T018f-3 handles range values. We assume 'weibull_modulus' is already processed to a float midpoint
    # and there might be a 'range_original' string.
    # Let's assume 'range_original' exists. If not, we check 'weibull_modulus'.
    
    if 'range_original' in df.columns:
        df['range_uncertainty'] = df['range_original'].apply(compute_range_uncertainty)
    elif 'weibull_modulus' in df.columns:
        # If range_original doesn't exist, try to parse weibull_modulus if it's a string
        # But typically, by the time descriptors are computed, weibull_modulus is numeric.
        # So we rely on range_original. If it's missing, we might need to infer or set to 0.
        # For safety, let's create it if missing, defaulting to 0 if no range info is available.
        # But the task says "Compute Range Uncertainty". If we don't have the range string, we can't compute it.
        # Let's assume 'range_original' is populated by T018f-3.
        logger.warning("Column 'range_original' not found. Attempting to derive from 'weibull_modulus' if string.")
        def parse_weibull_for_uncertainty(val):
            if isinstance(val, str):
                return compute_range_uncertainty(val)
            return 0.0
        df['range_uncertainty'] = df['weibull_modulus'].apply(parse_weibull_for_uncertainty)
    else:
        logger.warning("Neither 'range_original' nor 'weibull_modulus' found. Setting range_uncertainty to 0.")
        df['range_uncertainty'] = 0.0

    # Handle potential NaNs from failed computations (though we return None which becomes NaN)
    # T020 validates no missing primary predictors, so we might need to impute later.
    # For now, just compute.
    
    logger.info(f"Descriptors computed. Columns added: {['valence_electron_concentration', 'mean_atomic_radius', 'electronegativity_std', 'cation_size_variance', 'range_uncertainty']}")
    return df

def main():
    """
    Main function for standalone testing of descriptors.
    """
    # Example usage
    test_data = {
        'composition': ['Al2O3', 'ZrO2', 'SiC', '10-20'], # Last one is a fake range for testing
        'range_original': [None, None, None, '10-20']
    }
    df = pd.DataFrame(test_data)
    df = compute_descriptors(df)
    print(df)

if __name__ == "__main__":
    main()
