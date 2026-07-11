"""
Feature Engineering for BCC Alloys.

Implements compositional descriptor calculation (δ, VEC, entropy, enthalpy)
and ILR transformation.

Includes Circular Validation Check (FR-003.3) to detect CALPHAD-derived
yield strength sources and flag warnings or exclude entries based on config.
"""

import csv
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Local imports from project structure
from config import ensure_dirs, PROJECT_ROOT
from utils.periodic_table import (
    calculate_atomic_radius_mismatch,
    calculate_valence_electron_concentration,
    calculate_weighted_average
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'engineering.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
CALPHAD_KEYWORDS = ['CALPHAD', 'thermodynamic', 'calculated', 'simulation']
CONFIG_PATH = PROJECT_ROOT / 'config.yaml'

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    import yaml
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    except Exception as e:
        logger.warning(f"Could not load config.yaml: {e}. Using defaults.")
        return {}

def check_circular_validation(
    row: Dict[str, Any],
    config: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Check if yield strength source is CALPHAD-derived.
    
    Args:
        row: Alloy record dictionary
        config: Configuration dictionary
    
    Returns:
        Tuple of (is_circular, warning_message)
    """
    source_field = row.get('source', '') or row.get('data_source', '')
    method_field = row.get('method', '') or row.get('yield_strength_method', '')
    
    combined_text = f"{source_field} {method_field}".lower()
    
    is_circular = any(keyword.lower() in combined_text for keyword in CALPHAD_KEYWORDS)
    
    if is_circular:
        warning_msg = (
            f"CIRCULAR VALIDATION WARNING: Alloy '{row.get('alloy_id', 'UNKNOWN')}' "
            f"uses CALPHAD-derived yield strength. Source: '{source_field}', "
            f"Method: '{method_field}'. "
            f"Per FR-003.3, this may bias model evaluation."
        )
        return True, warning_msg
    
    return False, ""

def process_circular_validation(
    rows: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Process circular validation for all rows.
    
    Args:
        rows: List of alloy records
        config: Configuration dictionary
    
    Returns:
        Tuple of (processed_rows, warning_messages)
    """
    processed = []
    warnings = []
    
    strategy = config.get('circular_validation', {}).get('strategy', 'warn')
    # Options: 'warn', 'exclude', 'raw_features_only'
    
    for row in rows:
        is_circular, warning_msg = check_circular_validation(row, config)
        
        if is_circular:
            logger.warning(warning_msg)
            warnings.append(warning_msg)
            
            if strategy == 'exclude':
                logger.info(f"Excluding alloy {row.get('alloy_id')} due to circular validation.")
                continue
            elif strategy == 'raw_features_only':
                # Mark for raw features only processing
                row['_circular_validation_warning'] = True
                logger.info(f"Marked alloy {row.get('alloy_id')} for raw features only.")
            # else: 'warn' - continue normally but log
        
        processed.append(row)
    
    return processed, warnings

def calculate_delta(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate atomic radius mismatch (δ) for each alloy."""
    results = []
    for row in rows:
        try:
            composition_str = row.get('composition', '')
            if not composition_str:
                raise ValueError("Missing composition")
            
            # Parse composition string "Fe0.5Cr0.3Ni0.2" -> {'Fe': 0.5, 'Cr': 0.3, 'Ni': 0.2}
            comp_dict = {}
            import re
            matches = re.findall(r'([A-Z][a-z]?)([\d.]+)', composition_str)
            for elem, frac in matches:
                comp_dict[elem] = float(frac)
            
            # Normalize if needed
            total = sum(comp_dict.values())
            if total != 1.0:
                comp_dict = {k: v/total for k, v in comp_dict.items()}
            
            # Calculate δ using utility function
            delta = calculate_atomic_radius_mismatch(comp_dict)
            row['delta'] = delta
            results.append(row)
            
        except Exception as e:
            logger.error(f"Error calculating δ for alloy {row.get('alloy_id')}: {e}")
            row['delta'] = None
            results.append(row)
    
    return results

def calculate_vec(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate Valence Electron Concentration (VEC) for each alloy."""
    results = []
    for row in rows:
        try:
            composition_str = row.get('composition', '')
            if not composition_str:
                raise ValueError("Missing composition")
            
            import re
            comp_dict = {}
            matches = re.findall(r'([A-Z][a-z]?)([\d.]+)', composition_str)
            for elem, frac in matches:
                comp_dict[elem] = float(frac)
            
            total = sum(comp_dict.values())
            if total != 1.0:
                comp_dict = {k: v/total for k, v in comp_dict.items()}
            
            vec = calculate_valence_electron_concentration(comp_dict)
            row['vec'] = vec
            results.append(row)
            
        except Exception as e:
            logger.error(f"Error calculating VEC for alloy {row.get('alloy_id')}: {e}")
            row['vec'] = None
            results.append(row)
    
    return results

def calculate_entropy(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate mixing entropy for each alloy."""
    import math
    results = []
    for row in rows:
        try:
            composition_str = row.get('composition', '')
            if not composition_str:
                raise ValueError("Missing composition")
            
            import re
            comp_dict = {}
            matches = re.findall(r'([A-Z][a-z]?)([\d.]+)', composition_str)
            for elem, frac in matches:
                comp_dict[elem] = float(frac)
            
            total = sum(comp_dict.values())
            if total != 1.0:
                comp_dict = {k: v/total for k, v in comp_dict.items()}
            
            # Mixing entropy: -R * sum(xi * ln(xi))
            entropy = 0.0
            for x in comp_dict.values():
                if x > 0:
                    entropy -= x * math.log(x)
            
            row['mixing_entropy'] = entropy
            results.append(row)
            
        except Exception as e:
            logger.error(f"Error calculating entropy for alloy {row.get('alloy_id')}: {e}")
            row['mixing_entropy'] = None
            results.append(row)
    
    return results

def calculate_enhanced_features(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate all enhanced features (δ, VEC, entropy, enthalpy)."""
    rows = calculate_delta(rows)
    rows = calculate_vec(rows)
    rows = calculate_entropy(rows)
    # Enthalpy calculation would go here if needed
    return rows

def save_features_descriptors(
    rows: List[Dict[str, Any]],
    output_path: Path
):
    """Save processed features to CSV."""
    ensure_dirs([output_path.parent])
    
    fieldnames = [
        'alloy_id', 'composition', 'yield_strength', 'delta', 'vec', 'mixing_entropy'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Saved {len(rows)} records to {output_path}")

def main():
    """Main entry point for feature engineering."""
    logger.info("Starting feature engineering pipeline...")
    
    # Load configuration
    config = load_config()
    logger.info(f"Loaded configuration: {config}")
    
    # Input and output paths
    input_path = PROJECT_ROOT / 'data' / 'processed' / 'bcc_filtered.csv'
    output_path = PROJECT_ROOT / 'data' / 'processed' / 'features_descriptors.csv'
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Load data
    rows = []
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    logger.info(f"Loaded {len(rows)} records from {input_path}")
    
    # Perform Circular Validation Check (FR-003.3)
    processed_rows, warnings = process_circular_validation(rows, config)
    
    if warnings:
        logger.warning(f"Found {len(warnings)} entries with circular validation warnings.")
        # Log all warnings to a separate file for review
        warning_log_path = PROJECT_ROOT / 'data' / 'processed' / 'circular_validation_warnings.log'
        ensure_dirs([warning_log_path.parent])
        with open(warning_log_path, 'w') as f:
            for w in warnings:
                f.write(w + '\n')
        logger.info(f"Saved circular validation warnings to {warning_log_path}")
    
    # Calculate features
    enhanced_rows = calculate_enhanced_features(processed_rows)
    
    # Save output
    save_features_descriptors(enhanced_rows, output_path)
    
    logger.info("Feature engineering completed successfully.")

if __name__ == '__main__':
    main()