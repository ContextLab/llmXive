"""
Module to handle missing thermal conductivity (k) values in the dataset.

This module implements the logic to:
1. Load processed configuration data.
2. Identify configurations with missing thermal conductivity values.
3. Skip these configurations during analysis.
4. Log the count of skipped configurations.

This satisfies Task T026: Handle missing thermal conductivity values.
"""

import json
import logging
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from config.env_config import get_processed_dir
from logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

def load_processed_configs() -> List[Dict[str, Any]]:
    """
    Load processed configuration data from the descriptors CSV file.
    
    Returns:
        List of dictionaries containing configuration data.
    """
    processed_dir = get_processed_dir()
    descriptors_path = processed_dir / "descriptors.csv"
    
    if not descriptors_path.exists():
        logger.error(f"Descriptors file not found: {descriptors_path}")
        raise FileNotFoundError(f"Descriptors file not found: {descriptors_path}")
    
    configs = []
    with open(descriptors_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            configs.append(row)
    
    logger.info(f"Loaded {len(configs)} configurations from {descriptors_path}")
    return configs

def identify_missing_k(configs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Identify configurations with missing thermal conductivity values.
    
    Args:
        configs: List of configuration dictionaries.
    
    Returns:
        Tuple of (valid_configs, missing_k_configs)
    """
    valid_configs = []
    missing_k_configs = []
    
    for config in configs:
        k_value = config.get('thermal_conductivity')
        
        # Check if k_value is missing, None, or empty string
        if k_value is None or k_value == '' or k_value == 'nan' or k_value == 'NaN':
            missing_k_configs.append(config)
        else:
            try:
                # Try to convert to float to ensure it's a valid number
                float(k_value)
                valid_configs.append(config)
            except (ValueError, TypeError):
                # If conversion fails, treat as missing
                missing_k_configs.append(config)
    
    return valid_configs, missing_k_configs

def handle_missing_k_values(configs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Main function to handle missing thermal conductivity values.
    
    This function:
    1. Loads processed configurations if not provided.
    2. Identifies configurations with missing k values.
    3. Logs the count of skipped configurations.
    4. Returns a summary report.
    
    Args:
        configs: Optional list of pre-loaded configurations.
    
    Returns:
        Dictionary containing the handling summary.
    """
    if configs is None:
        configs = load_processed_configs()
    
    valid_configs, missing_k_configs = identify_missing_k(configs)
    
    # Log the results
    logger.info(f"Total configurations: {len(configs)}")
    logger.info(f"Valid configurations (with k): {len(valid_configs)}")
    logger.info(f"Skipped configurations (missing k): {len(missing_k_configs)}")
    
    if len(missing_k_configs) > 0:
        logger.warning(f"Found {len(missing_k_configs)} configurations with missing thermal conductivity values.")
        logger.warning("These configurations will be skipped in downstream analysis.")
        
        # Log individual missing k config IDs for debugging
        for i, config in enumerate(missing_k_configs[:10]):  # Log first 10
            config_id = config.get('config_id', f'unknown_{i}')
            k_value = config.get('thermal_conductivity', 'N/A')
            logger.debug(f"Missing k - Config ID: {config_id}, k value: {k_value}")
        
        if len(missing_k_configs) > 10:
            logger.debug(f"... and {len(missing_k_configs) - 10} more configurations with missing k values.")
    else:
        logger.info("All configurations have valid thermal conductivity values.")
    
    # Create summary report
    summary = {
        'total_configs': len(configs),
        'valid_configs': len(valid_configs),
        'missing_k_configs': len(missing_k_configs),
        'skipped_count': len(missing_k_configs),
        'missing_k_config_ids': [c.get('config_id') for c in missing_k_configs]
    }
    
    return summary

def save_missing_k_report(summary: Dict[str, Any]) -> Path:
    """
    Save the missing k handling report to a JSON file.
    
    Args:
        summary: Dictionary containing the handling summary.
    
    Returns:
        Path to the saved report file.
    """
    processed_dir = get_processed_dir()
    report_path = processed_dir / "missing_k_report.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Missing k report saved to: {report_path}")
    return report_path

def main():
    """
    Main entry point for the missing k handling script.
    """
    logger.info("Starting missing thermal conductivity value handling...")
    
    try:
        summary = handle_missing_k_values()
        report_path = save_missing_k_report(summary)
        
        logger.info("Missing k handling completed successfully.")
        logger.info(f"Summary: {summary}")
        
        return summary, report_path
        
    except Exception as e:
        logger.error(f"Error during missing k handling: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()