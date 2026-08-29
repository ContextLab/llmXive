import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger
from utils.validators import validate_correlation_results_schema

logger = get_logger(__name__)

def load_correlation_results(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load correlation results from a JSON file.
    
    Args:
        input_path: Path to the correlation_results.json file.
        
    Returns:
        List of dictionaries containing correlation data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Correlation results file not found: {input_path}")
        
    with open(input_path, 'r') as f:
        data = json.load(f)
        
    return data

def write_correlation_csv(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write correlation results to a CSV file with specific columns.
    
    Args:
        data: List of dictionaries with keys: taxon, coefficient, raw_pvalue, adj_pvalue.
        output_path: Path to the output CSV file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert list of dicts to DataFrame
    df = pd.DataFrame(data)
    
    # Ensure columns are in the correct order
    required_columns = ['taxon', 'coefficient', 'raw_pvalue', 'adj_pvalue']
    
    # Check if all required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns in data: {missing_columns}")
    
    # Select and order columns
    output_df = df[required_columns]
    
    # Round numeric columns for readability (optional, but good practice)
    output_df['coefficient'] = output_df['coefficient'].round(6)
    output_df['raw_pvalue'] = output_df['raw_pvalue'].round(8)
    output_df['adj_pvalue'] = output_df['adj_pvalue'].round(8)
    
    # Write to CSV
    output_df.to_csv(output_path, index=False)
    logger.info(f"Correlation results written to {output_path}")

def validate_output(output_path: Path) -> bool:
    """
    Validate the output CSV file.
    
    Args:
        output_path: Path to the output CSV file.
        
    Returns:
        True if validation passes, False otherwise.
    """
    if not output_path.exists():
        logger.error(f"Output file does not exist: {output_path}")
        return False
        
    try:
        df = pd.read_csv(output_path)
        
        # Check required columns
        required_columns = {'taxon', 'coefficient', 'raw_pvalue', 'adj_pvalue'}
        if not required_columns.issubset(df.columns):
            logger.error(f"Output CSV missing required columns. Expected: {required_columns}, Found: {set(df.columns)}")
            return False
        
        # Check for non-null values in critical columns
        if df['taxon'].isnull().any():
            logger.error("Output CSV contains null values in 'taxon' column")
            return False
            
        if df['coefficient'].isnull().any() or df['raw_pvalue'].isnull().any() or df['adj_pvalue'].isnull().any():
            logger.warning("Output CSV contains null values in numeric columns")
            
        logger.info(f"Validation passed for {output_path} with {len(df)} rows")
        return True
        
    except Exception as e:
        logger.error(f"Validation failed for {output_path}: {e}")
        return False

def main():
    """Main entry point for writing correlation results to CSV."""
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    results_dir = project_root / "data" / "results"
    
    input_path = results_dir / "correlation_results.json"
    output_path = results_dir / "correlation_results.csv"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        logger.info(f"Loading correlation results from {input_path}")
        data = load_correlation_results(input_path)
        
        if not data:
            logger.warning("Correlation results file is empty. Writing empty CSV.")
            # Write empty CSV with headers
            pd.DataFrame(columns=['taxon', 'coefficient', 'raw_pvalue', 'adj_pvalue']).to_csv(output_path, index=False)
            return
        
        # Write CSV
        logger.info(f"Writing correlation results to {output_path}")
        write_correlation_csv(data, output_path)
        
        # Validate output
        if validate_output(output_path):
            logger.info("Task completed successfully.")
        else:
            logger.error("Task completed but validation failed.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()