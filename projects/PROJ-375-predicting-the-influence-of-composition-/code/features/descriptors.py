import re
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter
import math
import logging
import mendeleev

# Configure logger
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper: Parse chemical formula into element: fraction dict
# ---------------------------------------------------------------------------
def parse_formula(formula: str) -> Dict[str, float]:
    """
    Parse a chemical formula string (e.g., 'Zr50Cu40Al10') into a dictionary
    mapping element symbols to their atomic fractions (summing to 1.0).
    
    Args:
        formula: Chemical formula string with element symbols and integer counts.
                
    Returns:
        Dict mapping element symbols to atomic fractions.
        
    Raises:
        ValueError: If the formula is malformed or elements are not found.
    """
    # Pattern to match element symbols followed by optional integer counts
    pattern = re.compile(r'([A-Z][a-z]*)(\d*)')
    matches = pattern.findall(formula)
    
    if not matches:
        raise ValueError(f"Could not parse formula: {formula}")
        
    elements = {}
    total_atoms = 0
    
    for symbol, count_str in matches:
        count = int(count_str) if count_str else 1
        # Mendeleev element lookup to validate
        try:
            _ = mendeleev.element(symbol)
        except Exception:
            raise ValueError(f"Unknown element symbol: {symbol}")
            
        elements[symbol] = count
        total_atoms += count
        
    if total_atoms == 0:
        raise ValueError(f"Formula {formula} has zero atoms.")
        
    return {sym: count / total_atoms for sym, count in elements.items()}

# ---------------------------------------------------------------------------
# Descriptor Calculations
# ---------------------------------------------------------------------------
def calculate_weighted_mean_radius(composition: Dict[str, float], 
                                   radii: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate the weighted mean atomic radius based on atomic fractions.
    
    Args:
        composition: Dict of element symbols to atomic fractions.
        radii: Optional dict of element radii (pm). If None, fetched from mendeleev.
                
    Returns:
        Weighted mean atomic radius in pm.
    """
    if radii is None:
        radii = {}
        for symbol in composition.keys():
            try:
                radii[symbol] = float(mendeleev.element(symbol).radius)
            except Exception:
                raise ValueError(f"Could not retrieve atomic radius for {symbol}")
                
    return sum(frac * radii[sym] for sym, frac in composition.items())

def calculate_weighted_mean_electronegativity(composition: Dict[str, float],
                                              electronegativities: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate the weighted mean electronegativity.
    """
    if electronegativities is None:
        electronegativities = {}
        for symbol in composition.keys():
            try:
                electronegativities[symbol] = float(mendeleev.element(symbol).electronegativity)
            except Exception:
                raise ValueError(f"Could not retrieve electronegativity for {symbol}")
                
    return sum(frac * electronegativities[sym] for sym, frac in composition.items())

def calculate_variance_electronegativity(composition: Dict[str, float],
                                         electronegativities: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate the variance of electronegativity in the alloy.
    """
    if electronegativities is None:
        electronegativities = {}
        for symbol in composition.keys():
            try:
                electronegativities[symbol] = float(mendeleev.element(symbol).electronegativity)
            except Exception:
                raise ValueError(f"Could not retrieve electronegativity for {symbol}")
                
    mean_en = calculate_weighted_mean_electronegativity(composition, electronegativities)
    variance = sum(frac * (electronegativities[sym] - mean_en) ** 2 
                   for sym, frac in composition.items())
    return variance

def calculate_weighted_mean_VEC(composition: Dict[str, float],
                                vec_values: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate the weighted mean Valence Electron Concentration (VEC).
    """
    if vec_values is None:
        vec_values = {}
        for symbol in composition.keys():
            try:
                # Mendeleev doesn't have a direct 'VEC' property, we approximate by group number
                # or use a standard lookup. For now, using group number as proxy for VEC.
                # Note: This might need adjustment based on specific literature definitions.
                el = mendeleev.element(symbol)
                vec_values[symbol] = float(el.group) 
            except Exception:
                raise ValueError(f"Could not retrieve VEC (group) for {symbol}")
                
    return sum(frac * vec_values[sym] for sym, frac in composition.items())

def calculate_atomic_size_mismatch(composition: Dict[str, float],
                                   radii: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate the atomic size mismatch (delta) parameter.
    Formula: delta = 1 - sum(c_i * (r_i / r_bar)) where r_bar is mean radius.
    Often simplified to variance-based or absolute difference metrics in literature.
    Here we use the standard definition: delta = sqrt( sum(c_i * (1 - r_i/r_bar)^2) )
    """
    if radii is None:
        radii = {}
        for symbol in composition.keys():
            try:
                radii[symbol] = float(mendeleev.element(symbol).radius)
            except Exception:
                raise ValueError(f"Could not retrieve atomic radius for {symbol}")
                
    r_bar = calculate_weighted_mean_radius(composition, radii)
    if r_bar == 0:
        return 0.0
        
    delta = math.sqrt(sum(frac * (1 - radii[sym] / r_bar) ** 2 
                          for sym, frac in composition.items()))
    return delta

# ---------------------------------------------------------------------------
# Main Extraction Function
# ---------------------------------------------------------------------------
def extract_descriptors(row: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract all relevant descriptors for a single metallic glass entry.
    
    Args:
        row: Dictionary containing at least 'composition' (string).
                
    Returns:
        Dictionary of calculated descriptors.
    """
    composition_str = row['composition']
    composition = parse_formula(composition_str)
    
    # Calculate descriptors
    mean_radius = calculate_weighted_mean_radius(composition)
    mean_en = calculate_weighted_mean_electronegativity(composition)
    var_en = calculate_variance_electronegativity(composition)
    mean_vec = calculate_weighted_mean_VEC(composition)
    size_mismatch = calculate_atomic_size_mismatch(composition)
    
    return {
        'mean_atomic_radius': mean_radius,
        'mean_electronegativity': mean_en,
        'electronegativity_variance': var_en,
        'mean_VEC': mean_vec,
        'size_mismatch': size_mismatch
    }

# ---------------------------------------------------------------------------
# VIF Check and Constitution Principle VI Handling
# ---------------------------------------------------------------------------
def check_vif_conflict(features: Dict[str, List[float]], 
                       threshold: float = 5.0) -> Dict[str, Any]:
    """
    Check for multicollinearity between 'mean_atomic_radius' and 'size_mismatch'.
    
    According to Constitution Principle VI, 'size_mismatch' MUST be retained
    even if VIF > threshold, as it is physically critical for metallic glass
    stability, despite statistical redundancy.
    
    Args:
        features: Dict of feature names to lists of values.
        threshold: VIF threshold (default 5.0).
                
    Returns:
        Dict with 'vif_warning' boolean and 'vif_value' if warning triggered.
    """
    # Simple VIF calculation for two features: VIF = 1 / (1 - R^2)
    # where R is correlation coefficient.
    x1 = features.get('mean_atomic_radius')
    x2 = features.get('size_mismatch')
    
    if not x1 or not x2 or len(x1) != len(x2):
        return {'vif_warning': False}
        
    n = len(x1)
    if n < 2:
        return {'vif_warning': False}
        
    # Calculate Pearson correlation
    mean_x1 = sum(x1) / n
    mean_x2 = sum(x2) / n
    
    numerator = sum((x1[i] - mean_x1) * (x2[i] - mean_x2) for i in range(n))
    denom_x1 = math.sqrt(sum((xi - mean_x1)**2 for xi in x1))
    denom_x2 = math.sqrt(sum((xi - mean_x2)**2 for xi in x2))
    
    if denom_x1 == 0 or denom_x2 == 0:
        return {'vif_warning': False}
        
    r = numerator / (denom_x1 * denom_x2)
    r_squared = r ** 2
    
    if r_squared >= 1.0:
        vif = float('inf')
    else:
        vif = 1.0 / (1.0 - r_squared)
        
    result = {'vif_value': vif, 'vif_warning': False}
    
    if vif > threshold:
        result['vif_warning'] = True
        # Constitution Principle VI: Retain feature despite high VIF
        logger.warning(
            f"High VIF detected for size_mismatch (VIF={vif:.2f} > {threshold}). "
            "Feature retained per Constitution Principle VI (physical significance > statistical independence)."
        )
        
    return result