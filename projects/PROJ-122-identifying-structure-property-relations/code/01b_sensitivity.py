"""
Sensitivity Sweep Script for Weight-Fraction Tolerance.

This script runs a comprehensive sensitivity sweep over a range of weight-fraction
tolerance values to analyze how the validation pass rate changes.

It reads the harmonized raw data produced by T014-T018 and re-applies the
weight-fraction validation logic with different tolerance thresholds.

Output: data/tolerance_sensitivity_report.json
"""

import os
import json
import logging
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logger import setup_logging, get_logger
from utils.ingest_utils import validate_weight_fractions

# Configuration defaults
DEFAULT_DATA_PATH = "data/raw/harmonized_data.json"
DEFAULT_OUTPUT_PATH = "data/tolerance_sensitivity_report.json"

# Default tolerance values if not specified in config
DEFAULT_TOLERANCE_VALUES = [0.01, 0.02, 0.05, 0.10, 0.15]

def load_harmonized_data(data_path: str) -> List[Dict[str, Any]]:
    """Load the harmonized data from the raw data file."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Harmonized data file not found: {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    logging.info(f"Loaded {len(data)} records from {data_path}")
    return data

def run_sensitivity_sweep(
    data: List[Dict[str, Any]], 
    tolerance_values: List[float]
) -> List[Dict[str, Any]]:
    """
    Run the sensitivity sweep over the specified tolerance values.
    
    For each tolerance value, count how many records pass the weight-fraction
    validation and calculate the pass rate.
    
    Args:
        data: List of harmonized records
        tolerance_values: List of tolerance thresholds to test
        
    Returns:
        List of dictionaries containing threshold, pass_rate, and valid_count
    """
    results = []
    total_records = len(data)
    
    if total_records == 0:
        logging.warning("No records found in data. Returning empty results.")
        return [{"threshold": t, "pass_rate": 0.0, "valid_count": 0} for t in tolerance_values]
    
    for tolerance in sorted(tolerance_values):
        valid_count = 0
        
        for record in data:
            # Extract weight fractions from the record
            # The structure depends on how T016 stored the composition
            weights = []
            
            if "composition" in record and isinstance(record["composition"], dict):
                # Extract weight fractions from composition dict
                weights = [v for k, v in record["composition"].items() 
                           if isinstance(v, (int, float)) and v >= 0]
            elif "weight_fractions" in record and isinstance(record["weight_fractions"], list):
                weights = record["weight_fractions"]
            
            # Validate weight fractions with current tolerance
            is_valid, _ = validate_weight_fractions(weights, tolerance)
            
            if is_valid:
                valid_count += 1
        
        pass_rate = (valid_count / total_records) * 100 if total_records > 0 else 0.0
        
        results.append({
            "threshold": tolerance,
            "pass_rate": round(pass_rate, 2),
            "valid_count": valid_count
        })
        
        logging.info(f"Tolerance {tolerance}: {valid_count}/{total_records} records passed ({pass_rate:.2f}%)")
    
    return results

def save_report(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save the sensitivity report to a JSON file."""
    report = {
        "sweep_type": "weight_fraction_tolerance",
        "total_records_analyzed": results[0]["valid_count"] + sum(
            r["valid_count"] for r in results if r["threshold"] != results[0]["threshold"]
        ) // len(results) if results else 0,  # Approximate total
        "results": results,
        "metadata": {
            "script": "01b_sensitivity.py",
            "description": "Sensitivity analysis of weight-fraction validation tolerance"
        }
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"Report saved to {output_path}")

def main():
    """Main entry point for the sensitivity sweep script."""
    parser = argparse.ArgumentParser(description="Run sensitivity sweep on weight-fraction tolerance")
    parser.add_argument("--data", type=str, default=None, help="Path to harmonized data JSON")
    parser.add_argument("--output", type=str, default=None, help="Path to output report JSON")
    parser.add_argument("--tolerances", type=str, default=None, 
                      help="Comma-separated list of tolerance values (e.g., '0.01,0.02,0.05')")
    parser.add_argument("--log-level", type=str, default="INFO", 
                      choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                      help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level.upper())
    logger = setup_logging(level=log_level)
    
    try:
        # Determine data path
        data_path = args.data or os.getenv("HARMONIZED_DATA_PATH", 
                        str(PROJECT_ROOT / DEFAULT_DATA_PATH))
        
        # Determine output path
        output_path = args.output or os.getenv("SENSITIVITY_REPORT_PATH",
                        str(PROJECT_ROOT / DEFAULT_OUTPUT_PATH))
        
        # Determine tolerance values
        if args.tolerances:
            tolerance_values = [float(x.strip()) for x in args.tolerances.split(",")]
        else:
            # Try to load from config if available, otherwise use defaults
            config_path = PROJECT_ROOT / "code" / "config.py"
            if config_path.exists():
                # Try to import tolerance values from config
                try:
                    # We'll use defaults for now as config.py in the API surface
                    # doesn't expose tolerance values yet
                    tolerance_values = DEFAULT_TOLERANCE_VALUES
                except (ImportError, AttributeError):
                    tolerance_values = DEFAULT_TOLERANCE_VALUES
            else:
                tolerance_values = DEFAULT_TOLERANCE_VALUES
        
        logger.info(f"Starting sensitivity sweep with tolerances: {tolerance_values}")
        logger.info(f"Data path: {data_path}")
        logger.info(f"Output path: {output_path}")
        
        # Load data
        data = load_harmonized_data(data_path)
        
        # Run sensitivity sweep
        results = run_sensitivity_sweep(data, tolerance_values)
        
        # Save report
        save_report(results, output_path)
        
        logger.info("Sensitivity sweep completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during sensitivity sweep: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()