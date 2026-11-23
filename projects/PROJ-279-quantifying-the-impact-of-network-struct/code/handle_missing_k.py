"""
Module to handle missing thermal conductivity (k) values in the dataset.
This implements Task T026: Skip configurations with missing k and log the count.
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
    Load the aggregated descriptors from the processed CSV file.
    Returns a list of dictionaries, each representing a configuration.
    """
    processed_dir = get_processed_dir()
    descriptors_path = processed_dir / "descriptors.csv"
    
    if not descriptors_path.exists():
        raise FileNotFoundError(f"Descriptors file not found at {descriptors_path}. "
                                "Run T025/T027 first to generate this file.")
    
    configs = []
    with open(descriptors_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            configs.append(row)
    
    logger.info(f"Loaded {len(configs)} configurations from {descriptors_path}")
    return configs

def identify_missing_k(configs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Identify configurations with missing thermal conductivity (k) values.
    
    Args:
        configs: List of configuration dictionaries.
    
    Returns:
        Tuple of (valid_configs, missing_k_configs)
    """
    valid_configs = []
    missing_k_configs = []
    
    for config in configs:
        # Check for 'k' or 'thermal_conductivity' field
        k_value = config.get('k') or config.get('thermal_conductivity')
        
        if k_value is None or k_value == '' or k_value == 'null' or k_value == 'NaN':
            missing_k_configs.append(config)
        else:
            # Attempt to convert to float to ensure it's a valid number
            try:
                float(k_value)
                valid_configs.append(config)
            except (ValueError, TypeError):
                missing_k_configs.append(config)
    
    return valid_configs, missing_k_configs

def handle_missing_k_values(configs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Process configurations, skipping those with missing k values.
    Logs the count of skipped configurations.
    
    Args:
        configs: List of all configuration dictionaries.
    
    Returns:
        Tuple of (processed_configs, skip_count)
    """
    valid_configs, missing_k_configs = identify_missing_k(configs)
    skip_count = len(missing_k_configs)
    
    if skip_count > 0:
        logger.warning(f"Skipping {skip_count} configuration(s) with missing thermal conductivity (k) values.")
        
        # Log details of skipped configurations for transparency
        for config in missing_k_configs:
            config_id = config.get('config_id', 'UNKNOWN')
            logger.debug(f"Skipped config {config_id}: missing k value")
    else:
        logger.info("No configurations with missing thermal conductivity values found.")
    
    return valid_configs, skip_count

def save_missing_k_report(missing_k_configs: List[Dict[str, Any]], skip_count: int) -> Path:
    """
    Save a report of configurations with missing k values.
    
    Args:
        missing_k_configs: List of configurations with missing k.
        skip_count: Number of skipped configurations.
    
    Returns:
        Path to the saved report file.
    """
    processed_dir = get_processed_dir()
    report_path = processed_dir / "missing_k_report.json"
    
    report_data = {
        "skip_count": skip_count,
        "skipped_configs": [
            {
                "config_id": config.get('config_id', 'UNKNOWN'),
                "reason": "Missing thermal conductivity value"
            }
            for config in missing_k_configs
        ]
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Saved missing k report to {report_path}")
    return report_path

def main():
    """
    Main entry point for handling missing thermal conductivity values.
    """
    logger.info("Starting missing thermal conductivity value handling (T026)...")
    
    try:
        # Load all processed configurations
        configs = load_processed_configs()
        
        # Handle missing k values (skip and log)
        processed_configs, skip_count = handle_missing_k_values(configs)
        
        # Save report of skipped configurations
        report_path = save_missing_k_report(
            [c for c in configs if c not in processed_configs], 
            skip_count
        )
        
        logger.info(f"T026 Complete: Processed {len(processed_configs)} configs, skipped {skip_count}.")
        logger.info(f"Report saved to: {report_path}")
        
        return {
            "processed_count": len(processed_configs),
            "skipped_count": skip_count,
            "report_path": str(report_path)
        }
        
    except Exception as e:
        logger.error(f"Error during missing k handling: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
