"""
T032b: Baseline Scalar Extraction

Extracts the specific 'GPU-Tuned' baseline value for each dataset from 
data/artifacts/gpu_tuned_baselines.csv (produced by T032a) and formats 
it into a JSON structure data/artifacts/gpu_tuned_scalars.json.

Output: JSON file with keys dataset_id -> baseline_value (float).
Validation: Ensures output is a dictionary of floats compatible with 
scipy.stats.ttest_1samp input requirements.
"""
import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

# Default paths relative to project root
DEFAULT_INPUT_PATH = "data/artifacts/gpu_tuned_baselines.csv"
DEFAULT_OUTPUT_PATH = "data/artifacts/gpu_tuned_scalars.json"

def load_gpu_tuned_baselines(input_path: str) -> Dict[str, float]:
    """
    Load the GPU-Tuned baselines from the CSV file produced by T032a.
    
    Args:
        input_path: Path to the gpu_tuned_baselines.csv file.
        
    Returns:
        Dictionary mapping dataset_id to baseline_value (float).
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or has invalid structure.
    """
    path = Path(input_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if path.stat().st_size == 0:
        raise ValueError(f"Input file is empty: {input_path}")
    
    baselines = {}
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate headers
            if reader.fieldnames is None:
                raise ValueError("CSV file has no headers")
            
            required_headers = {'dataset_id', 'baseline_value'}
            if not required_headers.issubset(set(reader.fieldnames)):
                raise ValueError(f"CSV must contain headers: {required_headers}, found: {reader.fieldnames}")
            
            row_count = 0
            for row in reader:
                dataset_id = row['dataset_id'].strip()
                if not dataset_id:
                    logger.warning("Skipping row with empty dataset_id")
                    continue
                
                try:
                    baseline_value = float(row['baseline_value'])
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid baseline_value '{row['baseline_value']}' for dataset '{dataset_id}': {e}")
                    continue
                
                if dataset_id in baselines:
                    logger.warning(f"Duplicate dataset_id found: {dataset_id}. Overwriting previous value.")
                
                baselines[dataset_id] = baseline_value
                row_count += 1
            
            if row_count == 0:
                raise ValueError("No valid data rows found in the CSV file")
            
            logger.info(f"Loaded {row_count} baseline values from {input_path}")
            
    except csv.Error as e:
        raise ValueError(f"Error parsing CSV file: {e}")
    
    return baselines

def validate_scalars(scalars: Dict[str, float]) -> None:
    """
    Validate that the extracted scalars are compatible with scipy.stats.ttest_1samp.
    
    Args:
        scalars: Dictionary of dataset_id -> baseline_value.
        
    Raises:
        ValueError: If validation fails.
    """
    if not scalars:
        raise ValueError("Scalars dictionary is empty")
    
    for dataset_id, value in scalars.items():
        if not isinstance(value, (int, float)):
            raise ValueError(f"Baseline value for '{dataset_id}' is not numeric: {type(value)}")
        
        if not (float('-inf') < value < float('inf')):
            raise ValueError(f"Baseline value for '{dataset_id}' is infinite or NaN: {value}")
    
    logger.info(f"Validation passed: {len(scalars)} valid scalar entries")

def save_scalars_json(scalars: Dict[str, float], output_path: str) -> None:
    """
    Save the scalars to a JSON file.
    
    Args:
        scalars: Dictionary of dataset_id -> baseline_value.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(scalars, f, indent=2)
    
    logger.info(f"Saved {len(scalars)} scalars to {output_path}")

def main():
    """Main entry point for the baseline scalar extraction pipeline."""
    parser = argparse.ArgumentParser(
        description="Extract GPU-Tuned baseline scalars from CSV to JSON."
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default=DEFAULT_INPUT_PATH,
        help=f"Path to the input CSV file (default: {DEFAULT_INPUT_PATH})"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to the output JSON file (default: {DEFAULT_OUTPUT_PATH})"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=log_level)
    
    try:
        logger.info(f"Starting baseline scalar extraction from {args.input}")
        
        # Load and extract scalars
        scalars = load_gpu_tuned_baselines(args.input)
        
        # Validate output
        validate_scalars(scalars)
        
        # Save to JSON
        save_scalars_json(scalars, args.output)
        
        logger.info("Baseline scalar extraction completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())