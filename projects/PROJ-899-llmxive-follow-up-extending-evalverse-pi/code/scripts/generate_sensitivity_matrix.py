"""
Script for Task T028: Generate full sensitivity matrix table.

Reads the sensitivity analysis results from T027 and the raw sweep data from T026,
then constructs a comprehensive matrix showing the classification status for every
dimension at every tested threshold.

Output: data/sensitivity_matrix_full.csv
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils import get_logger, ensure_directories, write_csv
from src.config import get_data_root

logger = get_logger(__name__)

def load_sensitivity_data():
    """
    Loads the raw sweep data (T026) and the analyzed data (T027).
    Returns the DataFrames or raises an error if missing.
    """
    data_root = get_data_root()
    raw_path = data_root / "sensitivity_sweep_raw.csv"
    analysis_path = data_root / "sensitivity_analysis.csv"

    if not raw_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {raw_path}. "
            "Ensure T026 (threshold sweep) has completed successfully."
        )
    
    if not analysis_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {analysis_path}. "
            "Ensure T027 (stability calculation) has completed successfully."
        )

    raw_df = pd.read_csv(raw_path)
    analysis_df = pd.read_csv(analysis_path)

    logger.info(f"Loaded raw sweep data: {len(raw_df)} rows from {raw_path}")
    logger.info(f"Loaded analysis data: {len(analysis_df)} rows from {analysis_path}")

    return raw_df, analysis_df

def generate_full_matrix(raw_df, analysis_df):
    """
    Constructs the full sensitivity matrix.
    
    The matrix should have:
    - Rows: Each unique dimension
    - Columns: Each unique threshold + Status columns (optional, but primarily Status)
    - Cells: The classification status ('feature-sufficient' or 'VLM-required')
    
    We pivot the raw data to create this matrix.
    """
    required_cols = ['dimension', 'threshold', 'status']
    
    # Validate raw data structure
    missing_cols = [c for c in required_cols if c not in raw_df.columns]
    if missing_cols:
        raise ValueError(f"Raw sweep data missing required columns: {missing_cols}")

    # Pivot the table: Index=dimension, Columns=threshold, Values=status
    # This creates a wide format where each threshold is a column
    matrix_df = raw_df.pivot(index='dimension', columns='threshold', values='status')
    
    # Reset index to make 'dimension' a column again for CSV output
    matrix_df = matrix_df.reset_index()
    
    # Ensure thresholds are sorted numerically for readability
    # The columns after 'dimension' are the thresholds
    threshold_cols = [c for c in matrix_df.columns if c != 'dimension']
    try:
        threshold_cols_sorted = sorted(threshold_cols, key=lambda x: float(x))
        matrix_df = matrix_df[['dimension'] + threshold_cols_sorted]
    except (ValueError, TypeError):
        logger.warning("Could not sort thresholds numerically, keeping original order.")

    logger.info(f"Generated sensitivity matrix: {matrix_df.shape[0]} dimensions x {matrix_df.shape[1]-1} thresholds")
    
    return matrix_df

def main():
    """Main entry point for T028."""
    logger.info("Starting T028: Generate full sensitivity matrix table.")
    
    try:
        # 1. Load dependencies
        raw_df, analysis_df = load_sensitivity_data()
        
        # 2. Generate matrix
        matrix_df = generate_full_matrix(raw_df, analysis_df)
        
        # 3. Save output
        data_root = get_data_root()
        output_path = data_root / "sensitivity_matrix_full.csv"
        
        ensure_directories([output_path])
        write_csv(matrix_df, output_path)
        
        logger.info(f"Successfully wrote sensitivity matrix to {output_path}")
        logger.info(f"Content preview:\n{matrix_df.head()}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input data: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during matrix generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())