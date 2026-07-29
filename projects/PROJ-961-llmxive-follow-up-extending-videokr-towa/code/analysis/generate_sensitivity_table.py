"""
Generate the sensitivity thresholds comparison table (T026a).

This script reads the sensitivity analysis results produced by T025 (sensitivity.py),
formats the p-values, effect sizes, and significance flags, and writes them to a CSV file.

Output:
    data/processed/sensitivity_thresholds.csv
        Columns: threshold_hop, p_value, effect_size, is_significant
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Import from sibling modules using the provided API surface
from utils.config import get_project_root, get_path, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_sensitivity_results() -> List[Dict[str, Any]]:
    """
    Load the sensitivity analysis results from the JSON file produced by T025.

    Returns:
        List of dictionaries containing threshold_hop, p_value, effect_size, is_significant.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file contains invalid JSON or missing keys.
    """
    input_path = get_path('data/processed/sensitivity_results.json')
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T025 (sensitivity.py) has been run successfully."
        )

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {input_path}, got {type(data)}")

    # Validate required keys
    required_keys = {'threshold_hop', 'p_value', 'effect_size', 'is_significant'}
    for i, record in enumerate(data):
        if not isinstance(record, dict):
            raise ValueError(f"Record {i} is not a dictionary")
        missing = required_keys - set(record.keys())
        if missing:
            raise ValueError(f"Record {i} missing keys: {missing}")

    return data

def format_p_value(p_value: float) -> str:
    """
    Format a p-value for CSV output.

    Args:
        p_value: The raw p-value.

    Returns:
        String formatted to 6 decimal places.
    """
    return f"{p_value:.6f}"

def format_effect_size(effect_size: float) -> str:
    """
    Format an effect size for CSV output.

    Args:
        effect_size: The raw effect size.

    Returns:
        String formatted to 6 decimal places.
    """
    return f"{effect_size:.6f}"

def format_significance(is_significant: bool) -> str:
    """
    Format the significance flag for CSV output.

    Args:
        is_significant: Boolean indicating significance.

    Returns:
        String 'True' or 'False'.
    """
    return str(is_significant)

def generate_table_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the formatted sensitivity results to a CSV file.

    Args:
        results: List of result dictionaries from load_sensitivity_results.
        output_path: Path to the output CSV file.
    """
    fieldnames = ['threshold_hop', 'p_value', 'effect_size', 'is_significant']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in results:
            writer.writerow({
                'threshold_hop': record['threshold_hop'],
                'p_value': format_p_value(record['p_value']),
                'effect_size': format_effect_size(record['effect_size']),
                'is_significant': format_significance(record['is_significant'])
            })

    logger.info(f"Sensitivity table written to: {output_path}")

def main() -> int:
    """
    Main entry point for T026a.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        # Load results from T025
        logger.info("Loading sensitivity results from T025...")
        results = load_sensitivity_results()
        logger.info(f"Loaded {len(results)} threshold records.")

        # Ensure output directory exists
        output_dir = get_path('data/processed')
        ensure_dir(output_dir)
        
        output_path = output_dir / 'sensitivity_thresholds.csv'

        # Generate the CSV table
        logger.info("Generating sensitivity thresholds table...")
        generate_table_csv(results, output_path)

        logger.info("T026a completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())