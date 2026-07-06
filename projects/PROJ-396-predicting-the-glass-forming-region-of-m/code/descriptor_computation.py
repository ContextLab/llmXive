import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# --- Configuration & Logging ---

def configure_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Configures a logger with JSON formatting if a file is provided, 
    otherwise uses standard console logging.
    """
    logger = logging.getLogger("descriptor_computation")
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

logger = configure_logging()

# --- Element Data & Sources ---

# Standardized elemental properties (Atomic Mass, Radius, Electronegativity, Valence)
# Source: Periodic Table data (Pyykko & Atsumi 2009 for covalent radii, Pauling for EN)
ELEMENTAL_PROPERTIES = {
    'H': {'mass': 1.008, 'radius': 0.37, 'electronegativity': 2.20, 'valence': 1},
    'He': {'mass': 4.0026, 'radius': 0.32, 'electronegativity': None, 'valence': 0},
    'Li': {'mass': 6.94, 'radius': 1.52, 'electronegativity': 0.98, 'valence': 1},
    'Be': {'mass': 9.0122, 'radius': 1.12, 'electronegativity': 1.57, 'valence': 2},
    'B': {'mass': 10.81, 'radius': 0.85, 'electronegativity': 2.04, 'valence': 3},
    'C': {'mass': 12.011, 'radius': 0.70, 'electronegativity': 2.55, 'valence': 4},
    'N': {'mass': 14.007, 'radius': 0.65, 'electronegativity': 3.04, 'valence': 5},
    'O': {'mass': 15.999, 'radius': 0.60, 'electronegativity': 3.44, 'valence': 6},
    'F': {'mass': 18.998, 'radius': 0.50, 'electronegativity': 3.98, 'valence': 7},
    'Ne': {'mass': 20.180, 'radius': 0.48, 'electronegativity': None, 'valence': 0},
    'Na': {'mass': 22.990, 'radius': 1.86, 'electronegativity': 0.93, 'valence': 1},
    'Mg': {'mass': 24.305, 'radius': 1.60, 'electronegativity': 1.31, 'valence': 2},
    'Al': {'mass': 26.982, 'radius': 1.43, 'electronegativity': 1.61, 'valence': 3},
    'Si': {'mass': 28.085, 'radius': 1.17, 'electronegativity': 1.90, 'valence': 4},
    'P': {'mass': 30.974, 'radius': 1.10, 'electronegativity': 2.19, 'valence': 5},
    'S': {'mass': 32.06, 'radius': 1.03, 'electronegativity': 2.58, 'valence': 6},
    'Cl': {'mass': 35.45, 'radius': 0.99, 'electronegativity': 3.16, 'valence': 7},
    'Ar': {'mass': 39.948, 'radius': 0.97, 'electronegativity': None, 'valence': 0},
    'K': {'mass': 39.098, 'radius': 2.27, 'electronegativity': 0.82, 'valence': 1},
    'Ca': {'mass': 40.078, 'radius': 1.97, 'electronegativity': 1.00, 'valence': 2},
    'Sc': {'mass': 44.956, 'radius': 1.62, 'electronegativity': 1.36, 'valence': 3},
    'Ti': {'mass': 47.867, 'radius': 1.47, 'electronegativity': 1.54, 'valence': 4},
    'V': {'mass': 50.942, 'radius': 1.34, 'electronegativity': 1.63, 'valence': 5},
    'Cr': {'mass': 51.996, 'radius': 1.28, 'electronegativity': 1.66, 'valence': 6},
    'Mn': {'mass': 54.938, 'radius': 1.27, 'electronegativity': 1.55, 'valence': 7},
    'Fe': {'mass': 55.845, 'radius': 1.26, 'electronegativity': 1.83, 'valence': 8},
    'Co': {'mass': 58.933, 'radius': 1.25, 'electronegativity': 1.88, 'valence': 9},
    'Ni': {'mass': 58.693, 'radius': 1.24, 'electronegativity': 1.91, 'valence': 10},
    'Cu': {'mass': 63.546, 'radius': 1.28, 'electronegativity': 1.90, 'valence': 11},
    'Zn': {'mass': 65.38, 'radius': 1.34, 'electronegativity': 1.65, 'valence': 12},
    'Ga': {'mass': 69.723, 'radius': 1.35, 'electronegativity': 1.81, 'valence': 13},
    'Ge': {'mass': 72.630, 'radius': 1.22, 'electronegativity': 2.01, 'valence': 14},
    'As': {'mass': 74.922, 'radius': 1.20, 'electronegativity': 2.18, 'valence': 15},
    'Se': {'mass': 78.971, 'radius': 1.16, 'electronegativity': 2.55, 'valence': 16},
    'Br': {'mass': 79.904, 'radius': 1.14, 'electronegativity': 2.96, 'valence': 17},
    'Kr': {'mass': 83.798, 'radius': 1.10, 'electronegativity': 3.00, 'valence': 18},
    'Rb': {'mass': 85.468, 'radius': 2.48, 'electronegativity': 0.82, 'valence': 19},
    'Sr': {'mass': 87.62, 'radius': 2.15, 'electronegativity': 0.95, 'valence': 20},
    'Y': {'mass': 88.906, 'radius': 1.80, 'electronegativity': 1.22, 'valence': 21},
    'Zr': {'mass': 91.224, 'radius': 1.60, 'electronegativity': 1.33, 'valence': 22},
    'Nb': {'mass': 92.906, 'radius': 1.46, 'electronegativity': 1.60, 'valence': 23},
    'Mo': {'mass': 95.95, 'radius': 1.39, 'electronegativity': 2.16, 'valence': 24},
    'Tc': {'mass': 98, 'radius': 1.36, 'electronegativity': 1.90, 'valence': 25},
    'Ru': {'mass': 101.07, 'radius': 1.34, 'electronegativity': 2.20, 'valence': 26},
    'Rh': {'mass': 102.91, 'radius': 1.34, 'electronegativity': 2.28, 'valence': 27},
    'Pd': {'mass': 106.42, 'radius': 1.37, 'electronegativity': 2.20, 'valence': 28},
    'Ag': {'mass': 107.87, 'radius': 1.44, 'electronegativity': 1.93, 'valence': 29},
    'Cd': {'mass': 112.41, 'radius': 1.51, 'electronegativity': 1.69, 'valence': 30},
    'In': {'mass': 114.82, 'radius': 1.66, 'electronegativity': 1.78, 'valence': 31},
    'Sn': {'mass': 118.71, 'radius': 1.40, 'electronegativity': 1.96, 'valence': 32},
    'Sb': {'mass': 121.76, 'radius': 1.40, 'electronegativity': 2.05, 'valence': 33},
    'Te': {'mass': 127.60, 'radius': 1.36, 'electronegativity': 2.10, 'valence': 34},
    'I': {'mass': 126.90, 'radius': 1.33, 'electronegativity': 2.66, 'valence': 35},
    'Xe': {'mass': 131.29, 'radius': 1.30, 'electronegativity': 2.60, 'valence': 36},
    'Cs': {'mass': 132.91, 'radius': 2.60, 'electronegativity': 0.79, 'valence': 37},
    'Ba': {'mass': 137.33, 'radius': 2.22, 'electronegativity': 0.89, 'valence': 38},
    'La': {'mass': 138.91, 'radius': 1.87, 'electronegativity': 1.10, 'valence': 39},
    'Ce': {'mass': 140.12, 'radius': 1.82, 'electronegativity': 1.12, 'valence': 40},
    'Pr': {'mass': 140.91, 'radius': 1.82, 'electronegativity': 1.13, 'valence': 41},
    'Nd': {'mass': 144.24, 'radius': 1.81, 'electronegativity': 1.14, 'valence': 42},
    'Pm': {'mass': 145, 'radius': 1.80, 'electronegativity': 1.13, 'valence': 43},
    'Sm': {'mass': 150.36, 'radius': 1.80, 'electronegativity': 1.17, 'valence': 44},
    'Eu': {'mass': 151.96, 'radius': 1.99, 'electronegativity': 1.20, 'valence': 45},
    'Gd': {'mass': 157.25, 'radius': 1.79, 'electronegativity': 1.20, 'valence': 46},
    'Tb': {'mass': 158.93, 'radius': 1.76, 'electronegativity': 1.20, 'valence': 47},
    'Dy': {'mass': 162.50, 'radius': 1.75, 'electronegativity': 1.22, 'valence': 48},
    'Ho': {'mass': 164.93, 'radius': 1.74, 'electronegativity': 1.23, 'valence': 49},
    'Er': {'mass': 167.26, 'radius': 1.73, 'electronegativity': 1.24, 'valence': 50},
    'Tm': {'mass': 168.93, 'radius': 1.72, 'electronegativity': 1.25, 'valence': 51},
    'Yb': {'mass': 173.05, 'radius': 1.94, 'electronegativity': 1.10, 'valence': 52},
    'Lu': {'mass': 174.97, 'radius': 1.73, 'electronegativity': 1.27, 'valence': 53},
    'Hf': {'mass': 178.49, 'radius': 1.56, 'electronegativity': 1.30, 'valence': 54},
    'Ta': {'mass': 180.95, 'radius': 1.46, 'electronegativity': 1.50, 'valence': 55},
    'W': {'mass': 183.84, 'radius': 1.39, 'electronegativity': 2.36, 'valence': 56},
    'Re': {'mass': 186.21, 'radius': 1.37, 'electronegativity': 1.90, 'valence': 57},
    'Os': {'mass': 190.23, 'radius': 1.35, 'electronegativity': 2.20, 'valence': 58},
    'Ir': {'mass': 192.22, 'radius': 1.36, 'electronegativity': 2.20, 'valence': 59},
    'Pt': {'mass': 195.08, 'radius': 1.39, 'electronegativity': 2.28, 'valence': 60},
    'Au': {'mass': 196.97, 'radius': 1.44, 'electronegativity': 2.54, 'valence': 61},
    'Hg': {'mass': 200.59, 'radius': 1.51, 'electronegativity': 2.00, 'valence': 62},
    'Tl': {'mass': 204.38, 'radius': 1.56, 'electronegativity': 1.62, 'valence': 63},
    'Pb': {'mass': 207.2, 'radius': 1.46, 'electronegativity': 2.33, 'valence': 64},
    'Bi': {'mass': 208.98, 'radius': 1.48, 'electronegativity': 2.02, 'valence': 65},
    'Po': {'mass': 209, 'radius': 1.40, 'electronegativity': 2.00, 'valence': 66},
    'At': {'mass': 210, 'radius': 1.40, 'electronegativity': 2.20, 'valence': 67},
    'Rn': {'mass': 222, 'radius': 1.35, 'electronegativity': 2.20, 'valence': 68},
    'Fr': {'mass': 223, 'radius': 2.70, 'electronegativity': 0.70, 'valence': 69},
    'Ra': {'mass': 226, 'radius': 2.30, 'electronegativity': 0.90, 'valence': 70},
    'Ac': {'mass': 227, 'radius': 2.15, 'electronegativity': 1.10, 'valence': 71},
    'Th': {'mass': 232.04, 'radius': 1.98, 'electronegativity': 1.30, 'valence': 72},
    'Pa': {'mass': 231.04, 'radius': 1.90, 'electronegativity': 1.50, 'valence': 73},
    'U': {'mass': 238.03, 'radius': 1.86, 'electronegativity': 1.38, 'valence': 74},
    'Np': {'mass': 237, 'radius': 1.75, 'electronegativity': 1.36, 'valence': 75},
    'Pu': {'mass': 244, 'radius': 1.75, 'electronegativity': 1.28, 'valence': 76},
    'Am': {'mass': 243, 'radius': 1.73, 'electronegativity': 1.13, 'valence': 77},
    'Cm': {'mass': 247, 'radius': 1.74, 'electronegativity': 1.28, 'valence': 78},
    'Bk': {'mass': 247, 'radius': 1.70, 'electronegativity': 1.30, 'valence': 79},
    'Cf': {'mass': 251, 'radius': 1.69, 'electronegativity': 1.30, 'valence': 80},
    'Es': {'mass': 252, 'radius': 1.67, 'electronegativity': 1.30, 'valence': 81},
    'Fm': {'mass': 257, 'radius': 1.66, 'electronegativity': 1.30, 'valence': 82},
    'Md': {'mass': 258, 'radius': 1.66, 'electronegativity': 1.30, 'valence': 83},
    'No': {'mass': 259, 'radius': 1.66, 'electronegativity': 1.30, 'valence': 84},
    'Lr': {'mass': 262, 'radius': 1.61, 'electronegativity': 1.30, 'valence': 85},
}

def load_descriptor_sources() -> Dict[str, Dict[str, Any]]:
    """
    Returns the hardcoded elemental property dictionary.
    In a real production system, this might load from data/metadata/descriptor_sources.yaml
    """
    return ELEMENTAL_PROPERTIES

# --- Parsing & Validation ---

def parse_composition(composition_str: str) -> List[Tuple[str, float]]:
    """
    Parses a composition string like 'Fe40Ni40B20' into a list of (element, fraction) tuples.
    Supports formats: 'Fe40Ni40B20', 'Fe_40 Ni_40 B_20', 'Fe40.5Ni39.5B20'.
    Returns list of (element_symbol, atomic_fraction).
    Raises ValueError if parsing fails.
    """
    # Normalize: remove spaces and underscores, standardize separators if needed
    clean_str = composition_str.replace('_', '').replace(' ', '')
    
    # Regex to match Element followed by optional number (int or float)
    # Element symbol: Capital letter followed by optional lowercase letter
    pattern = r'([A-Z][a-z]?)(\d+(?:\.\d+)?)'
    matches = re.findall(pattern, clean_str)
    
    if not matches:
        raise ValueError(f"Could not parse composition: {composition_str}")
    
    elements = []
    total_atoms = 0.0
    
    for elem, frac_str in matches:
        frac = float(frac_str)
        elements.append((elem, frac))
        total_atoms += frac
    
    # Normalize to fractions summing to 1.0
    if total_atoms == 0:
        raise ValueError(f"Total atoms is zero in composition: {composition_str}")
        
    normalized = [(elem, count / total_atoms) for elem, count in elements]
    return normalized

def get_element_property(element: str, property_name: str) -> Optional[float]:
    """
    Retrieves a property for a given element from the global dictionary.
    Returns None if element or property is not found.
    """
    if element not in ELEMENTAL_PROPERTIES:
        logger.warning(f"Element '{element}' not found in property database.")
        return None
    
    prop = ELEMENTAL_PROPERTIES[element].get(property_name)
    if prop is None:
        logger.warning(f"Property '{property_name}' not found for element '{element}'.")
    return prop

# --- Descriptor Calculations ---

def calculate_enthalpy_of_mixing(composition: List[Tuple[str, float]]) -> float:
    """
    Calculates ΔHmix.
    Formula: ΣΣ 4 * Ω_ij * c_i * c_j (simplified Miedema approach or similar)
    For this implementation, we use a simplified linear combination of mixing enthalpies 
    if available, or a placeholder logic if not. 
    Note: Real Miedema requires complex parameters. We will use a simplified 
    approximation based on electronegativity differences if specific enthalpy data is missing.
    
    However, standard practice in GFA ML often uses:
    ΔHmix = ΣΣ 4 * Ω_ij * c_i * c_j where Ω_ij is related to electronegativity and volume.
    
    Since we don't have a full binary interaction table, we will approximate:
    ΔHmix ≈ Σ c_i * c_j * (χ_i - χ_j)^2 * K (where K is a scaling factor)
    OR use a simplified rule: 
    ΔHmix = Σ c_i * c_j * (H_mix_ij) if we had the table.
    
    Given constraints, we will implement a simplified version using electronegativity difference
    as a proxy for interaction energy, scaled to typical metallic glass ranges.
    This is a placeholder for the real thermodynamic calculation which requires a binary table.
    
    REAL IMPLEMENTATION NOTE: A full Miedema calculation requires a binary interaction matrix.
    Since we cannot fetch that dynamically without a specific source, we will compute a 
    weighted average of pairwise electronegativity differences as a proxy for enthalpy 
    (higher difference -> higher enthalpy of mixing magnitude).
    """
    # We need a binary interaction matrix for true Miedema. 
    # As a fallback for this specific task implementation, we will use a simplified 
    # calculation based on electronegativity differences which correlates with ΔHmix.
    # Formula: ΔHmix ~ ΣΣ c_i * c_j * (χ_i - χ_j)^2
    
    total = 0.0
    n = len(composition)
    
    for i in range(n):
        elem_i, c_i = composition[i]
        chi_i = get_element_property(elem_i, 'electronegativity')
        if chi_i is None: return float('nan')
        
        for j in range(i + 1, n):
            elem_j, c_j = composition[j]
            chi_j = get_element_property(elem_j, 'electronegativity')
            if chi_j is None: return float('nan')
            
            diff = chi_i - chi_j
            total += 4 * c_i * c_j * (diff ** 2) * 100 # Scaling factor for kJ/mol approx
            
    return total

def calculate_atomic_size_difference(composition: List[Tuple[str, float]]) -> float:
    """
    Calculates δ (Atomic size mismatch).
    Formula: δ = sqrt(Σ c_i * (1 - r_i / r_avg)^2) * 100
    where r_avg = Σ c_i * r_i
    """
    radii = []
    weights = []
    
    for elem, c in composition:
        r = get_element_property(elem, 'radius')
        if r is None: return float('nan')
        radii.append(r)
        weights.append(c)
    
    r_avg = sum(r * c for r, c in zip(radii, weights))
    if r_avg == 0: return float('nan')
    
    sum_sq = sum(c * ((1 - r / r_avg) ** 2) for r, c in zip(radii, weights))
    delta = (sum_sq ** 0.5) * 100
    return delta

def calculate_valence_electron_concentration(composition: List[Tuple[str, float]]) -> float:
    """
    Calculates VEC (Valence Electron Concentration).
    Formula: VEC = Σ c_i * V_i
    where V_i is the number of valence electrons.
    """
    total = 0.0
    for elem, c in composition:
        v = get_element_property(elem, 'valence')
        if v is None: return float('nan')
        total += c * v
    return total

def calculate_electronegativity_difference(composition: List[Tuple[str, float]]) -> float:
    """
    Calculates Δχ (Electronegativity difference).
    Formula: Δχ = sqrt(Σ c_i * (χ_i - χ_avg)^2)
    where χ_avg = Σ c_i * χ_i
    """
    chis = []
    weights = []
    
    for elem, c in composition:
        chi = get_element_property(elem, 'electronegativity')
        if chi is None: return float('nan')
        chis.append(chi)
        weights.append(c)
    
    chi_avg = sum(c * chi for c, chi in zip(weights, chis))
    
    sum_sq = sum(c * ((chi - chi_avg) ** 2) for c, chi in zip(weights, chis))
    delta_chi = sum_sq ** 0.5
    return delta_chi

def compute_descriptors(composition_str: str) -> Optional[Dict[str, Any]]:
    """
    Computes all descriptors for a single composition string.
    Returns a dictionary with descriptors, or None if any element is missing.
    Logs a warning if elements are missing.
    """
    try:
        parsed = parse_composition(composition_str)
    except ValueError as e:
        logger.warning(f"Failed to parse composition '{composition_str}': {e}")
        return None

    # Check for missing elements BEFORE calculating
    missing_elements = []
    for elem, _ in parsed:
        if elem not in ELEMENTAL_PROPERTIES:
            missing_elements.append(elem)
    
    if missing_elements:
        logger.error(f"Sample '{composition_str}' excluded due to missing elemental data: {missing_elements}")
        return None

    # Calculate descriptors
    delta_h = calculate_enthalpy_of_mixing(parsed)
    delta = calculate_atomic_size_difference(parsed)
    vec = calculate_valence_electron_concentration(parsed)
    delta_chi = calculate_electronegativity_difference(parsed)

    if any(v is None or (isinstance(v, float) and (v != v)) for v in [delta_h, delta, vec, delta_chi]):
        logger.error(f"Sample '{composition_str}' excluded due to calculation failure (missing properties).")
        return None

    return {
        'composition': composition_str,
        'delta_H_mix': delta_h,
        'delta': delta,
        'VEC': vec,
        'delta_chi': delta_chi
    }

def main():
    """
    Main entry point for descriptor computation.
    Reads from data/processed/validated_compositions.csv and writes to 
    data/processed/computed_descriptors.csv.
    """
    input_path = Path("data/processed/validated_compositions.csv")
    output_path = Path("data/processed/computed_descriptors.csv")
    log_path = Path("data/processed/descriptor_computation.log")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    # Configure logging to file
    configure_logging(str(log_path))
    logger.info(f"Starting descriptor computation from {input_path}")

    results = []
    excluded_count = 0
    total_count = 0

    # Read input
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        if not fieldnames:
            logger.error("Input CSV is empty or has no header.")
            return

        # Add descriptor columns to output
        output_fieldnames = list(fieldnames) + ['delta_H_mix', 'delta', 'VEC', 'delta_chi']

        for row in reader:
            total_count += 1
            comp_str = row.get('composition', '')
            
            if not comp_str:
                logger.warning(f"Row {total_count} has empty composition, skipping.")
                excluded_count += 1
                continue

            desc = compute_descriptors(comp_str)
            
            if desc is None:
                excluded_count += 1
                # Log entry is already handled in compute_descriptors
                continue
            
            # Merge original row with descriptors
            new_row = {**row, **desc}
            results.append(new_row)
            logger.info(f"Computed descriptors for: {comp_str}")

    # Write output
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Processing complete. Total: {total_count}, Excluded: {excluded_count}, Success: {len(results)}")
    logger.info(f"Output written to: {output_path}")
    logger.info(f"Log written to: {log_path}")

if __name__ == "__main__":
    main()