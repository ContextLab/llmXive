import os
import csv
import sys
from typing import Dict, List, Any, Optional, Tuple
from utils.logging import get_logger, log_info, log_warning, log_error
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

# Threshold for validation deviation (1% as per SC-005)
VALIDATION_DEVIATION_THRESHOLD = 0.01

def load_elemental_properties(filepath: str) -> Dict[str, Dict[str, float]]:
    """
    Load elemental properties from a CSV file.
    Expected columns: element, atomic_radius_angstrom, electronegativity_pauling, valence_electrons
    Returns a dict keyed by element symbol.
    """
    properties = {}
    if not os.path.exists(filepath):
        log_error(f"Elemental properties file not found: {filepath}", ErrorCode.DATA_SOURCE_MISSING)
        return properties

    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                element = row['element'].strip()
                if not element:
                    continue
                properties[element] = {
                    'atomic_radius_angstrom': float(row['atomic_radius_angstrom']),
                    'electronegativity_pauling': float(row['electronegativity_pauling']),
                    'valence_electrons': float(row['valence_electrons'])
                }
        log_info(f"Loaded {len(properties)} elemental properties from {filepath}")
    except Exception as e:
        log_error(f"Failed to load elemental properties: {e}", ErrorCode.INVALID_DATA_SCHEMA)
        raise
    
    return properties

def calculate_mean_atomic_radius(atomic_radii: List[float]) -> float:
    if not atomic_radii:
        return 0.0
    return sum(atomic_radii) / len(atomic_radii)

def calculate_electronegativity_variance(electronegativities: List[float]) -> float:
    if not electronegativities:
        return 0.0
    mean_en = sum(electronegativities) / len(electronegativities)
    variance = sum((x - mean_en) ** 2 for x in electronegativities) / len(electronegativities)
    return variance

def calculate_valence_electron_count(valence_counts: List[float], concentrations: List[float]) -> float:
    """
    Calculate weighted average valence electron count.
    valence_counts: list of valence electron counts for each element in the alloy
    concentrations: list of atomic fractions for each element
    """
    if not valence_counts or not concentrations or len(valence_counts) != len(concentrations):
        return 0.0
    return sum(v * c for v, c in zip(valence_counts, concentrations))

def calculate_hume_rothery_concentration(concentrations: List[float]) -> float:
    """
    Simple Hume-Rothery concentration metric: sum of squared concentrations.
    A value of 1.0 indicates a pure element, lower values indicate more mixing.
    """
    if not concentrations:
        return 0.0
    return sum(c ** 2 for c in concentrations)

def generate_descriptors(
    alloy_data: Dict[str, Any],
    elemental_props: Dict[str, Dict[str, float]]
) -> Dict[str, float]:
    """
    Generate compositional descriptors for a single alloy entry.
    
    Args:
        alloy_data: Dictionary containing 'elements' (list of symbols) and 'concentrations' (list of fractions).
        elemental_props: Dictionary of elemental properties loaded from CSV.
        
    Returns:
        Dictionary of calculated descriptors.
    """
    elements = alloy_data.get('elements', [])
    concentrations = alloy_data.get('concentrations', [])
    
    if not elements or not concentrations:
        log_warning("Invalid alloy data: missing elements or concentrations", ErrorCode.INVALID_DATA_SCHEMA)
        return {}

    # Validate that all elements exist in properties
    missing_elements = [e for e in elements if e not in elemental_props]
    if missing_elements:
        log_warning(f"Missing elemental properties for: {missing_elements}", ErrorCode.DATA_SOURCE_MISSING)
        # We could raise, but for robustness we proceed with available data or return empty
        # For strict validation (SC-005), we might want to halt or flag.
        # Here we log and continue, but real production might raise.
    
    radii = []
    en_values = []
    valence_values = []
    
    for elem, conc in zip(elements, concentrations):
        if elem in elemental_props:
            props = elemental_props[elem]
            radii.append(props['atomic_radius_angstrom'])
            en_values.append(props['electronegativity_pauling'])
            valence_values.append(props['valence_electrons'])
        else:
            # Handle missing property gracefully (e.g., skip or use 0)
            # For this implementation, we skip adding to lists to avoid distorting averages
            continue
    
    if not radii:
        log_warning("No valid elemental properties found for alloy", ErrorCode.DATA_SOURCE_MISSING)
        return {}

    descriptors = {
        'mean_atomic_radius': calculate_mean_atomic_radius(radii),
        'electronegativity_variance': calculate_electronegativity_variance(en_values),
        'valence_electron_count': calculate_valence_electron_count(valence_values, concentrations),
        'hume_rothery_concentration': calculate_hume_rothery_concentration(concentrations)
    }
    
    return descriptors

def validate_descriptors(
    descriptors: Dict[str, float],
    alloy_data: Dict[str, Any],
    elemental_props: Dict[str, Dict[str, float]]
) -> bool:
    """
    Validate derived descriptors against source elemental properties.
    
    Checks:
    1. Mean atomic radius deviation from weighted average of source radii <= 1%
    2. Electronegativity variance consistency
    3. Valence electron count consistency
    
    Returns True if validation passes, False otherwise.
    """
    elements = alloy_data.get('elements', [])
    concentrations = alloy_data.get('concentrations', [])
    
    if not elements or not concentrations:
        log_error("Cannot validate: missing alloy data", ErrorCode.INVALID_DATA_SCHEMA)
        return False

    # Re-calculate expected values directly from source data for comparison
    expected_radii_sum = 0.0
    expected_en_sum = 0.0
    expected_valence_sum = 0.0
    total_weight = 0.0
    
    valid_elements_count = 0
    
    for elem, conc in zip(elements, concentrations):
        if elem in elemental_props:
            props = elemental_props[elem]
            expected_radii_sum += props['atomic_radius_angstrom'] * conc
            expected_en_sum += props['electronegativity_pauling'] * conc
            expected_valence_sum += props['valence_electrons'] * conc
            total_weight += conc
            valid_elements_count += 1
    
    if valid_elements_count == 0:
        log_error("No valid elements found for validation", ErrorCode.DATA_SOURCE_MISSING)
        return False

    # Calculate expected weighted averages
    expected_mean_radius = expected_radii_sum / total_weight if total_weight > 0 else 0.0
    expected_valence = expected_valence_sum / total_weight if total_weight > 0 else 0.0
    
    # Validate Mean Atomic Radius
    if 'mean_atomic_radius' in descriptors and expected_mean_radius > 0:
        calc_radius = descriptors['mean_atomic_radius']
        deviation = abs(calc_radius - expected_mean_radius) / expected_mean_radius
        if deviation > VALIDATION_DEVIATION_THRESHOLD:
            log_error(
                f"Mean atomic radius deviation {deviation:.4f} exceeds threshold {VALIDATION_DEVIATION_THRESHOLD}",
                ErrorCode.INVALID_DATA_SCHEMA
            )
            return False
        log_info(f"Mean atomic radius validation passed (deviation: {deviation:.4f})")

    # Validate Valence Electron Count
    if 'valence_electron_count' in descriptors and expected_valence > 0:
        calc_valence = descriptors['valence_electron_count']
        deviation = abs(calc_valence - expected_valence) / expected_valence
        if deviation > VALIDATION_DEVIATION_THRESHOLD:
            log_error(
                f"Valence electron count deviation {deviation:.4f} exceeds threshold {VALIDATION_DEVIATION_THRESHOLD}",
                ErrorCode.INVALID_DATA_SCHEMA
            )
            return False
        log_info(f"Valence electron count validation passed (deviation: {deviation:.4f})")

    # Note: Electronegativity variance is a derived statistic of the set, not a simple weighted average.
    # We assume the calculation logic is consistent. A strict check would require re-computing the variance
    # from the source list and comparing.
    if 'electronegativity_variance' in descriptors:
        en_values = []
        for elem, conc in zip(elements, concentrations):
            if elem in elemental_props:
                en_values.append(elemental_props[elem]['electronegativity_pauling'])
        
        if len(en_values) > 1:
            mean_en = sum(en_values) / len(en_values)
            expected_variance = sum((x - mean_en) ** 2 for x in en_values) / len(en_values)
            calc_variance = descriptors['electronegativity_variance']
            
            # Handle zero variance case
            if expected_variance > 1e-9:
                deviation = abs(calc_variance - expected_variance) / expected_variance
            else:
                deviation = abs(calc_variance - expected_variance) if abs(calc_variance - expected_variance) > 1e-9 else 0.0
                
            if deviation > VALIDATION_DEVIATION_THRESHOLD:
                log_error(
                    f"Electronegativity variance deviation {deviation:.4f} exceeds threshold {VALIDATION_DEVIATION_THRESHOLD}",
                    ErrorCode.INVALID_DATA_SCHEMA
                )
                return False
            log_info(f"Electronegativity variance validation passed (deviation: {deviation:.4f})")

    return True

def process_alloy_dataset(
    input_path: str,
    output_path: str,
    elemental_props_path: str
) -> int:
    """
    Process a dataset of alloys, generate descriptors, and validate them.
    
    Args:
        input_path: Path to input CSV with alloy compositions.
        output_path: Path to write output CSV with descriptors.
        elemental_props_path: Path to elemental properties CSV.
        
    Returns:
        Number of successfully processed rows.
    """
    elemental_props = load_elemental_properties(elemental_props_path)
    if not elemental_props:
        log_error("Failed to load elemental properties", ErrorCode.DATA_SOURCE_MISSING)
        return 0

    processed_count = 0
    
    try:
        with open(input_path, 'r', newline='', encoding='utf-8') as infile, \
             open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames + [
                'mean_atomic_radius',
                'electronegativity_variance',
                'valence_electron_count',
                'hume_rothery_concentration'
            ]
            
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                try:
                    # Parse elements and concentrations
                    # Assuming format: "Cu,Al,Zn" and "0.6,0.3,0.1"
                    elements_str = row.get('elements', '')
                    conc_str = row.get('concentrations', '')
                    
                    if not elements_str or not conc_str:
                        continue
                        
                    elements = [e.strip() for e in elements_str.split(',')]
                    concentrations = [float(c.strip()) for c in conc_str.split(',')]
                    
                    alloy_data = {
                        'elements': elements,
                        'concentrations': concentrations
                    }
                    
                    descriptors = generate_descriptors(alloy_data, elemental_props)
                    
                    if not descriptors:
                        continue
                        
                    # Validate descriptors against source properties (T016)
                    if not validate_descriptors(descriptors, alloy_data, elemental_props):
                        log_warning(f"Validation failed for row: {row.get('id', 'unknown')}. Skipping.", ErrorCode.INVALID_DATA_SCHEMA)
                        continue
                        
                    # Merge original row with descriptors
                    output_row = dict(row)
                    output_row.update(descriptors)
                    writer.writerow(output_row)
                    processed_count += 1
                    
                except Exception as e:
                    log_error(f"Error processing row {row}: {e}", ErrorCode.INVALID_DATA_SCHEMA)
                    continue
                    
    except Exception as e:
        log_error(f"Failed to process dataset: {e}", ErrorCode.INVALID_DATA_SCHEMA)
        raise

    log_info(f"Successfully processed {processed_count} alloy entries with validation.")
    return processed_count

def main():
    """
    Main entry point for descriptor generation and validation.
    Usage: python -m code.features.generate_descriptors --input <path> --output <path> --props <path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate and validate alloy descriptors")
    parser.add_argument('--input', required=True, help='Input CSV path')
    parser.add_argument('--output', required=True, help='Output CSV path')
    parser.add_argument('--props', required=True, help='Elemental properties CSV path')
    
    args = parser.parse_args()
    
    log_info(f"Starting descriptor generation for {args.input}")
    count = process_alloy_dataset(args.input, args.output, args.props)
    log_info(f"Finished. Processed {count} rows.")

if __name__ == "__main__":
    main()