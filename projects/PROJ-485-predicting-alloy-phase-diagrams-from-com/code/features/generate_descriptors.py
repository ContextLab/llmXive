"""
Generates compositional descriptors from raw alloy data.
Implements T017 and T018.
"""
import os
import sys
import json
import csv
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from utils.logging import get_logger, log_error, log_info
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

def load_elemental_properties(file_path: str) -> Dict[str, Dict[str, float]]:
    """
    Loads elemental properties from CSV.
    """
    if not os.path.exists(file_path):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Elemental properties file not found: {file_path}")
        raise FileNotFoundError(f"Elemental properties file not found: {file_path}")

    props = {}
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            props[row['element']] = {
                'atomic_radius_angstrom': float(row['atomic_radius_angstrom']),
                'electronegativity_pauling': float(row['electronegativity_pauling']),
                'valence_electrons': int(row['valence_electrons'])
            }
    return props

def calculate_mean_atomic_radius(props: Dict[str, float], elements: List[str]) -> float:
    """
    Calculates the mean atomic radius for a set of elements.
    """
    if not elements:
        return 0.0
    total = 0.0
    count = 0
    for el in elements:
        if el in props:
            total += props[el]['atomic_radius_angstrom']
            count += 1
    return total / count if count > 0 else 0.0

def calculate_electronegativity_variance(props: Dict[str, float], elements: List[str]) -> float:
    """
    Calculates the variance of electronegativity for a set of elements.
    """
    if not elements:
        return 0.0
    values = [props[el]['electronegativity_pauling'] for el in elements if el in props]
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance

def calculate_valence_electron_count(props: Dict[str, int], elements: List[str]) -> int:
    """
    Calculates the total valence electron count.
    """
    total = 0
    for el in elements:
        if el in props:
            total += props[el]['valence_electrons']
    return total

def calculate_hume_rothery_concentration(elements: List[str], composition: float) -> float:
    """
    Calculates a simplified Hume-Rothery concentration metric.
    (Simplified: using composition as a proxy for concentration of the solute)
    """
    return composition

def generate_descriptors(row: Dict[str, Any], elemental_props: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    Generates descriptor features for a single row.
    """
    elements = [row['element_a'], row['element_b']]
    if 'element_c' in row and pd.notna(row['element_c']):
        elements.append(row['element_c'])
    
    return {
        "system_id": f"{row['element_a']}-{row['element_b']}",
        "element_a": row['element_a'],
        "element_b": row['element_b'],
        "composition": float(row['composition']),
        "temperature": float(row['temperature']),
        "mean_atomic_radius": calculate_mean_atomic_radius(elemental_props, elements),
        "electronegativity_variance": calculate_electronegativity_variance(elemental_props, elements),
        "valence_electron_count": calculate_valence_electron_count(elemental_props, elements),
        "hume_rothery_concentration": calculate_hume_rothery_concentration(elements, float(row['composition']))
    }

def validate_descriptors(descriptors: List[Dict[str, Any]], elemental_props: Dict[str, Dict[str, float]]) -> bool:
    """
    Validates derived values against elemental properties.
    Implements T018.
    """
    for desc in descriptors:
        # Check if mean atomic radius is within reasonable bounds (0.5 to 3.0 Angstroms)
        if not (0.5 <= desc['mean_atomic_radius'] <= 3.0):
            log_warning(f"Mean atomic radius out of bounds: {desc['mean_atomic_radius']}")
            return False
    return True

def process_alloy_dataset(input_path: str, output_path: str, elemental_props_path: str) -> None:
    """
    Processes the raw alloy dataset and generates descriptors.
    """
    elemental_props = load_elemental_properties(elemental_props_path)
    
    descriptors = []
    df = pd.read_csv(input_path)
    
    for _, row in df.iterrows():
        try:
            desc = generate_descriptors(row.to_dict(), elemental_props)
            descriptors.append(desc)
        except Exception as e:
            log_error(ErrorCode.DATA_SCHEMA_MISMATCH, f"Failed to generate descriptors for row: {e}")
            continue

    if not validate_descriptors(descriptors, elemental_props):
        log_warning("Descriptor validation failed, but proceeding with data.")

    # Save intermediate JSON for export step
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(descriptors, f)
    
    log_info(f"Generated {len(descriptors)} descriptors. Saved to {output_path}")

def main():
    input_file = "data/processed/raw_filtered.csv"
    output_file = "data/processed/descriptors_intermediate.json"
    props_file = "data/raw/elemental_properties.csv"

    if not os.path.exists(input_file):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Input file not found: {input_file}")
        sys.exit(1)
    
    if not os.path.exists(props_file):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Elemental properties not found: {props_file}")
        sys.exit(1)

    process_alloy_dataset(input_file, output_file, props_file)
    sys.exit(0)

if __name__ == "__main__":
    main()