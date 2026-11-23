"""
Feature generation module for calculating compositional descriptors.
"""
import os
import sys
import json
import csv
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

def load_elemental_properties(filepath: str = "data/raw/elemental_properties.csv") -> Dict[str, Dict[str, float]]:
    """Load elemental properties from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: Elemental properties file not found: {filepath}")

    df = pd.read_csv(filepath)
    properties = {}
    for _, row in df.iterrows():
        element = row['element']
        properties[element] = {
            'atomic_radius': row['atomic_radius_angstrom'],
            'electronegativity': row['electronegativity_pauling'],
            'valence_electrons': row['valence_electrons']
        }
    return properties

def calculate_mean_atomic_radius(composition: Dict[str, float], properties: Dict) -> float:
    """Calculate mean atomic radius based on composition."""
    total_radius = 0
    total_fraction = 0
    for element, fraction in composition.items():
        if element in properties:
            total_radius += properties[element]['atomic_radius'] * fraction
            total_fraction += fraction
    return total_radius / total_fraction if total_fraction > 0 else 0

def calculate_electronegativity_variance(composition: Dict[str, float], properties: Dict) -> float:
    """Calculate variance of electronegativity based on composition."""
    values = []
    weights = []
    for element, fraction in composition.items():
        if element in properties:
            values.append(properties[element]['electronegativity'])
            weights.append(fraction)

    if not values:
        return 0

    weighted_mean = np.average(values, weights=weights)
    variance = np.average((np.array(values) - weighted_mean) ** 2, weights=weights)
    return variance

def calculate_valence_electron_count(composition: Dict[str, float], properties: Dict) -> float:
    """Calculate weighted average valence electron count."""
    total_valence = 0
    total_fraction = 0
    for element, fraction in composition.items():
        if element in properties:
            total_valence += properties[element]['valence_electrons'] * fraction
            total_fraction += fraction
    return total_valence / total_fraction if total_fraction > 0 else 0

def calculate_hume_rothery_concentration(composition: Dict[str, float], properties: Dict) -> float:
    """Calculate Hume-Rothery concentration parameter."""
    # Simplified version: variance in atomic radii
    radii = []
    fractions = []
    for element, fraction in composition.items():
        if element in properties:
            radii.append(properties[element]['atomic_radius'])
            fractions.append(fraction)

    if len(radii) < 2:
        return 0

    mean_radius = np.average(radii, weights=fractions)
    variance = np.average((np.array(radii) - mean_radius) ** 2, weights=fractions)
    return np.sqrt(variance)

def generate_descriptors(row: Dict, properties: Dict) -> Dict[str, float]:
    """Generate descriptors for a single alloy system."""
    # Parse composition from string (e.g., "Cu:0.6,Zn:0.4")
    composition = {}
    comp_str = row.get('composition', '')
    if isinstance(comp_str, str):
        for part in comp_str.split(','):
            if ':' in part:
                elem, frac = part.split(':')
                composition[elem.strip()] = float(frac.strip())

    descriptors = {
        'system_id': row.get('system_id', 'unknown'),
        'element_a': row.get('element_a', ''),
        'element_b': row.get('element_b', ''),
        'temperature': row.get('temperature', 0),
        'composition_raw': row.get('composition', ''),
        'mean_atomic_radius': calculate_mean_atomic_radius(composition, properties),
        'electronegativity_variance': calculate_electronegativity_variance(composition, properties),
        'valence_electron_count': calculate_valence_electron_count(composition, properties),
        'hume_rothery_concentration': calculate_hume_rothery_concentration(composition, properties)
    }

    return descriptors

def validate_descriptors(descriptors: List[Dict], properties: Dict) -> bool:
    """Validate generated descriptors against expected ranges."""
    for desc in descriptors:
        if desc['mean_atomic_radius'] <= 0 or desc['mean_atomic_radius'] > 5:
            log_warning(logger, f"Invalid mean_atomic_radius: {desc['mean_atomic_radius']}")
            return False
        if desc['electronegativity_variance'] < 0:
            log_warning(logger, f"Invalid electronegativity_variance: {desc['electronegativity_variance']}")
            return False
    return True

def process_alloy_dataset(input_path: str, output_path: str, properties: Dict) -> pd.DataFrame:
    """Process the entire alloy dataset and generate descriptors."""
    df_input = pd.read_csv(input_path)
    descriptors = []

    for _, row in df_input.iterrows():
        desc = generate_descriptors(row.to_dict(), properties)
        descriptors.append(desc)

    df_descriptors = pd.DataFrame(descriptors)

    if not validate_descriptors(descriptors, properties):
        log_warning(logger, "Some descriptors failed validation")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_descriptors.to_csv(output_path, index=False)

    log_info(logger, f"Generated {len(df_descriptors)} descriptor rows. Saved to {output_path}")
    return df_descriptors

def main():
    """Entry point for descriptor generation."""
    properties = load_elemental_properties()
    input_path = "data/processed/descriptors.csv"
    output_path = "data/processed/descriptors.csv"

    if not os.path.exists(input_path):
        # If ingestion hasn't run, try to load from raw
        input_path = "data/raw/elemental_properties.csv"
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: Input file not found")

    process_alloy_dataset(input_path, output_path, properties)

if __name__ == "__main__":
    main()
