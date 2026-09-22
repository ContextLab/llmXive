import os
import csv
import sys
import json
from typing import Dict, List, Any, Optional, Tuple
from utils.logging import get_logger, log_info, log_warning, log_error
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

def load_elemental_properties(filepath: str = "data/raw/elemental_properties.csv") -> Dict[str, Dict[str, float]]:
    """
    Load elemental properties from CSV into a dictionary keyed by element symbol.
    Expected columns: element, atomic_radius_angstrom, electronegativity_pauling, valence_electrons
    """
    if not os.path.exists(filepath):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Elemental properties file not found: {filepath}")
        raise FileNotFoundError(f"Elemental properties file not found: {filepath}")

    properties = {}
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            element = row['element'].strip()
            try:
                properties[element] = {
                    'atomic_radius_angstrom': float(row['atomic_radius_angstrom']),
                    'electronegativity_pauling': float(row['electronegativity_pauling']),
                    'valence_electrons': int(row['valence_electrons'])
                }
            except (ValueError, KeyError) as e:
                log_warning(ErrorCode.INVALID_DATA_SCHEMA, f"Skipping invalid row in elemental properties: {row} - {e}")
                continue
    return properties

def calculate_mean_atomic_radius(elements: List[str], properties: Dict[str, Dict[str, float]]) -> float:
    """Calculate mean atomic radius for a list of elements."""
    if not elements:
        return 0.0
    radii = []
    for el in elements:
        if el in properties:
            radii.append(properties[el]['atomic_radius_angstrom'])
        else:
            log_warning(ErrorCode.DATA_SOURCE_MISSING, f"Element {el} not found in properties file")
    if not radii:
        return 0.0
    return sum(radii) / len(radii)

def calculate_electronegativity_variance(elements: List[str], properties: Dict[str, Dict[str, float]]) -> float:
    """Calculate variance of electronegativity for a list of elements."""
    if len(elements) < 2:
        return 0.0
    en_values = []
    for el in elements:
        if el in properties:
            en_values.append(properties[el]['electronegativity_pauling'])
    if len(en_values) < 2:
        return 0.0
    mean_en = sum(en_values) / len(en_values)
    variance = sum((x - mean_en) ** 2 for x in en_values) / len(en_values)
    return variance

def calculate_valence_electron_count(elements: List[str], properties: Dict[str, Dict[str, float]]) -> int:
    """Calculate total valence electron count for a list of elements."""
    total = 0
    for el in elements:
        if el in properties:
            total += properties[el]['valence_electrons']
        else:
            log_warning(ErrorCode.DATA_SOURCE_MISSING, f"Element {el} not found in properties file")
    return total

def calculate_hume_rothery_concentration(elements: List[str], concentrations: List[float], properties: Dict[str, Dict[str, float]]) -> float:
    """
    Calculate Hume-Rothery concentration factor.
    Simplified: weighted average of atomic radius differences relative to the largest.
    """
    if not elements or not concentrations:
        return 0.0
    
    radii = []
    for el, conc in zip(elements, concentrations):
        if el in properties:
            radii.append(properties[el]['atomic_radius_angstrom'])
    
    if not radii:
        return 0.0
    
    max_radius = max(radii)
    if max_radius == 0:
        return 0.0
    
    # Calculate weighted deviation
    weighted_deviation = 0.0
    for el, conc in zip(elements, concentrations):
        if el in properties:
            r = properties[el]['atomic_radius_angstrom']
            deviation = abs(r - max_radius) / max_radius
            weighted_deviation += deviation * conc
    
    return weighted_deviation

def generate_descriptors(row: Dict[str, Any], properties: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    Generate compositional descriptors for a single alloy row.
    Expects row to contain 'element_a', 'element_b', and optionally 'concentration_a' (0-1).
    """
    elements = []
    concentrations = []
    
    el_a = row.get('element_a', '').strip()
    el_b = row.get('element_b', '').strip()
    
    if el_a:
        elements.append(el_a)
        conc_a = float(row.get('concentration_a', 0.5))
        concentrations.append(conc_a)
    
    if el_b:
        elements.append(el_b)
        conc_b = 1.0 - conc_a if el_a else float(row.get('concentration_b', 0.5))
        concentrations.append(conc_b)
    
    if not elements:
        log_warning(ErrorCode.INVALID_DATA_SCHEMA, "Row missing element identifiers")
        return {}
    
    # Normalize concentrations if needed
    total_conc = sum(concentrations)
    if total_conc > 0:
        concentrations = [c / total_conc for c in concentrations]
    
    mean_radius = calculate_mean_atomic_radius(elements, properties)
    en_variance = calculate_electronegativity_variance(elements, properties)
    valence_count = calculate_valence_electron_count(elements, properties)
    hume_rothery = calculate_hume_rothery_concentration(elements, concentrations, properties)
    
    return {
        'mean_atomic_radius': mean_radius,
        'electronegativity_variance': en_variance,
        'valence_electron_count': valence_count,
        'hume_rothery_concentration': hume_rothery
    }

def validate_descriptors(descriptors: Dict[str, Any], properties: Dict[str, Dict[str, float]], tolerance: float = 0.01) -> Tuple[bool, List[str]]:
    """
    Validate derived descriptor values against elemental properties.
    Checks if derived values are within reasonable bounds based on input properties.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    # Check mean_atomic_radius
    if 'mean_atomic_radius' in descriptors and descriptors['mean_atomic_radius'] is not None:
        mean_r = descriptors['mean_atomic_radius']
        if mean_r <= 0:
            errors.append(f"Mean atomic radius must be positive: {mean_r}")
        # Check if it falls within the range of available properties
        if properties:
            all_radii = [p['atomic_radius_angstrom'] for p in properties.values()]
            if all_radii:
                min_r, max_r = min(all_radii), max(all_radii)
                if mean_r < min_r * (1 - tolerance) or mean_r > max_r * (1 + tolerance):
                    errors.append(f"Mean atomic radius {mean_r} outside expected range [{min_r}, {max_r}]")
    
    # Check electronegativity_variance
    if 'electronegativity_variance' in descriptors and descriptors['electronegativity_variance'] is not None:
        var_en = descriptors['electronegativity_variance']
        if var_en < 0:
            errors.append(f"Electronegativity variance cannot be negative: {var_en}")
        # Variance should generally be less than the square of the max range
        if properties:
            all_en = [p['electronegativity_pauling'] for p in properties.values()]
            if all_en:
                max_range = max(all_en) - min(all_en)
                max_possible_var = (max_range ** 2) / 4  # Max variance for two points at extremes
                if var_en > max_possible_var * (1 + tolerance):
                    errors.append(f"Electronegativity variance {var_en} exceeds theoretical max {max_possible_var}")
    
    # Check valence_electron_count
    if 'valence_electron_count' in descriptors and descriptors['valence_electron_count'] is not None:
        v_count = descriptors['valence_electron_count']
        if v_count < 0:
            errors.append(f"Valence electron count cannot be negative: {v_count}")
    
    # Check hume_rothery_concentration
    if 'hume_rothery_concentration' in descriptors and descriptors['hume_rothery_concentration'] is not None:
        hr = descriptors['hume_rothery_concentration']
        if hr < 0 or hr > 1:
            errors.append(f"Hume-Rothery concentration must be between 0 and 1: {hr}")
    
    return len(errors) == 0, errors

def process_alloy_dataset(input_path: str, output_path: str, properties_path: str = "data/raw/elemental_properties.csv") -> int:
    """
    Process an alloy dataset, generate descriptors, validate them, and write to CSV.
    Returns the number of successfully processed rows.
    """
    if not os.path.exists(properties_path):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Elemental properties file not found: {properties_path}")
        raise FileNotFoundError(f"Elemental properties file not found: {properties_path}")
    
    properties = load_elemental_properties(properties_path)
    processed_count = 0
    validation_failures = 0
    
    if not os.path.exists(input_path):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    with open(input_path, 'r', newline='', encoding='utf-8') as infile, \
         open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['mean_atomic_radius', 'electronegativity_variance', 
                                          'valence_electron_count', 'hume_rothery_concentration', 
                                          'validation_status', 'validation_errors']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row_num, row in enumerate(reader, 1):
            try:
                descriptors = generate_descriptors(row, properties)
                if not descriptors:
                    log_warning(ErrorCode.INVALID_DATA_SCHEMA, f"Row {row_num}: Could not generate descriptors")
                    continue
                
                is_valid, errors = validate_descriptors(descriptors, properties)
                status = "VALID" if is_valid else "INVALID"
                error_str = "; ".join(errors) if errors else ""
                
                if not is_valid:
                    validation_failures += 1
                    log_warning(ErrorCode.INVALID_DATA_SCHEMA, f"Row {row_num}: Validation failed - {error_str}")
                
                # Merge original row with descriptors
                new_row = {**row, **descriptors}
                new_row['validation_status'] = status
                new_row['validation_errors'] = error_str
                
                writer.writerow(new_row)
                processed_count += 1
                
            except Exception as e:
                log_error(ErrorCode.INVALID_DATA_SCHEMA, f"Row {row_num}: Unexpected error - {e}")
                continue
    
    log_info(ErrorCode.DATA_SOURCE_MISSING, f"Processed {processed_count} rows. Validation failures: {validation_failures}")
    return processed_count

def main():
    """Main entry point for descriptor generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate and validate compositional descriptors for alloy data.")
    parser.add_argument("--input", default="data/processed/raw_phase_data.csv", help="Input CSV file path")
    parser.add_argument("--output", default="data/processed/descriptors.csv", help="Output CSV file path")
    parser.add_argument("--properties", default="data/raw/elemental_properties.csv", help="Elemental properties CSV path")
    
    args = parser.parse_args()
    
    try:
        count = process_alloy_dataset(args.input, args.output, args.properties)
        log_info(ErrorCode.DATA_SOURCE_MISSING, f"Successfully generated descriptors for {count} rows")
    except Exception as e:
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()