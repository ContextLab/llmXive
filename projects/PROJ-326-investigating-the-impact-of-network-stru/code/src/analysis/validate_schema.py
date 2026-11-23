"""
Schema validation utility for simulation results.

This module provides functions to validate simulation results against the
defined JSON schema, ensuring data integrity before further processing.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from code.src.analysis.schema import (
    SIMULATION_RESULTS_SCHEMA,
    validate_simulation_results,
    save_schema_definition
)

logger = logging.getLogger(__name__)

def validate_file(file_path: Path) -> bool:
    """
    Validate a JSON file against the simulation results schema.
    
    Args:
        file_path: Path to the JSON file to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        validate_simulation_results(data)
        logger.info(f"✓ Validation passed for {file_path}")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return False
    except ValueError as e:
        logger.error(f"Schema validation failed for {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating {file_path}: {e}")
        return False

def validate_directory(directory: Path) -> int:
    """
    Validate all JSON files in a directory against the schema.
    
    Args:
        directory: Path to the directory containing JSON files.
        
    Returns:
        Number of valid files.
    """
    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return 0
    
    valid_count = 0
    for json_file in directory.glob("*.json"):
        if validate_file(json_file):
            valid_count += 1
    
    logger.info(f"Validated {valid_count}/{len(list(directory.glob('*.json')))} files in {directory}")
    return valid_count

def main() -> None:
    """
    Main entry point for schema validation.
    
    Validates the default simulation results file and saves the schema definition.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Save schema definition for reference
    save_schema_definition()
    
    # Validate default simulation results file
    results_path = Path("data/analysis/simulation_results.json")
    if results_path.exists():
        validate_file(results_path)
    else:
        logger.warning(f"Simulation results file not found: {results_path}")
        logger.info("Schema definition saved for future validation.")

if __name__ == "__main__":
    main()