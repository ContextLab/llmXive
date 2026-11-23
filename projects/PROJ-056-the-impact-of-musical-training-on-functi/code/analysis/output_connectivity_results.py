"""
Module to output connectivity results to CSV.
Handles loading processed data, computing statistics (if needed), and writing the final results.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger

logger = get_logger(__name__)

INPUT_FILE = Path("data/processed/connectivity_metrics_stats.csv")
OUTPUT_FILE = Path("data/processed/connectivity_results.csv")

def load_processed_connectivity_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads the connectivity statistics dataframe.
    Expects a CSV with columns: connection_id, t_stat, p_value, q_value, effect_size, ci_lower, ci_upper.
    
    Args:
        input_path: Path to the input CSV. Defaults to INPUT_FILE.
        
    Returns:
        pd.DataFrame: The loaded data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    if input_path is None:
        input_path = INPUT_FILE
        
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                              "Ensure US2 stats tasks (T027-T030) have run and produced the stats file.")
    
    logger.info(f"Loading connectivity stats from {input_path}")
    df = pd.read_csv(input_path)
    
    required_cols = ['connection_id', 't_stat', 'p_value', 'q_value', 'effect_size', 'ci_lower', 'ci_upper']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Input file missing required columns: {missing_cols}")
        
    return df

def compute_group_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder for statistics computation if the input file is raw metrics.
    In this pipeline, T027-T030 are expected to have already computed these stats.
    This function validates and ensures the dataframe is ready for output.
    
    Args:
        df: The dataframe containing connectivity metrics and stats.
        
    Returns:
        pd.DataFrame: The validated dataframe.
    """
    # If the input already has the stats, just return it.
    # If the input is raw (e.g. only connection_id, metric_value), we would compute stats here.
    # Based on task dependencies, we assume stats are present.
    return df

def write_connectivity_results(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Writes the connectivity results to a CSV file.
    
    Args:
        df: The dataframe to write.
        output_path: Path to the output file. Defaults to OUTPUT_FILE.
        
    Returns:
        Path: The path to the written file.
    """
    if output_path is None:
        output_path = OUTPUT_FILE
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sort by p_value or q_value for readability
    if 'q_value' in df.columns:
        df = df.sort_values(by='q_value')
    elif 'p_value' in df.columns:
        df = df.sort_values(by='p_value')
        
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote connectivity results to {output_path}")
    return output_path

def main():
    """
    Main entry point for the output_connectivity_results script.
    Loads stats from the intermediate file and writes the final results CSV.
    """
    logger.info("Starting connectivity results output process.")
    
    try:
        # Load data
        df = load_processed_connectivity_data()
        
        # Validate/Process (currently just validation)
        df = compute_group_statistics(df)
        
        # Write output
        output_path = write_connectivity_results(df)
        
        logger.info(f"Task T031 completed. Output written to {output_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    sys.exit(main())