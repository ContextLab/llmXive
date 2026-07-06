import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from config import get_project_root, get_data_paths
from data.descriptors import run_descriptor_computation

logger = logging.getLogger(__name__)

def filter_zero_impurity_configs(input_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Filters bulk configurations that have zero impurity atoms.
    
    This function reads the raw or intermediate dataset, checks for the presence
    of impurity atoms (based on 'impurity_species' or specific atom counts if
    the data structure implies it), and removes rows where the impurity count is 0.
    
    Args:
        input_path: Path to the input CSV (e.g., descriptors.csv or raw data).
        output_path: Path to save the filtered CSV.
        
    Returns:
        A dictionary containing the exclusion count and paths.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} records from {input_path}")

    # Determine column to check. 
    # Based on T015, descriptors.csv has columns [species, rdf_peak, pair_corr, voronoi_count].
    # 'species' likely refers to the impurity species. If it's empty or NaN, it implies no impurity.
    # Alternatively, if the dataset comes from a simulation where impurities were inserted,
    # we look for a specific column or infer from 'species'.
    
    # Strategy: If 'impurity_species' column exists, check for empty/None.
    # If not, check 'species' (from T015 output).
    
    target_col = None
    if 'impurity_species' in df.columns:
        target_col = 'impurity_species'
    elif 'species' in df.columns:
        target_col = 'species'
    
    if target_col is None:
        logger.warning("No column found to identify impurity species. Skipping filtering.")
        # If we can't determine, we assume all are valid or log an error. 
        # Given the task is specifically for "zero impurity atoms", we must find a way.
        # If the file is the output of T015 (descriptors.csv), 'species' is the impurity.
        # If 'species' is present but empty, it's a zero-impurity case.
        raise ValueError("Could not determine impurity column in input file.")

    # Filter out rows where the impurity species is missing, empty, or NaN
    # This effectively removes configurations with zero impurity atoms
    valid_mask = df[target_col].notna() & (df[target_col].astype(str).str.strip() != '')
    
    filtered_df = df[valid_mask]
    excluded_count = initial_count - len(filtered_df)

    # Save filtered data
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Filtered data saved to {output_path}")
    logger.info(f"Excluded {excluded_count} configurations with zero impurity atoms.")

    return {
        "initial_count": initial_count,
        "filtered_count": len(filtered_df),
        "excluded_count": excluded_count,
        "input_path": str(input_path),
        "output_path": str(output_path)
    }

def generate_preprocessing_report(stats: Dict[str, Any], output_path: Path) -> None:
    """
    Generates the preprocessing report JSON file.
    
    Args:
        stats: Statistics dictionary from filter_zero_impurity_configs.
        output_path: Path to save the report.
    """
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Preprocessing report saved to {output_path}")

def run_preprocessing_filter() -> None:
    """
    Main entry point for the preprocessing filter task.
    Reads descriptors, filters zero-impurity rows, and saves report.
    """
    project_root = get_project_root()
    data_paths = get_data_paths()
    
    # Determine input file
    # The task implies filtering bulk configurations. 
    # In the context of US1, the processed descriptors (T015) are the result of GB construction.
    # However, if the input to T015 (bulk configs) had zero impurities, they wouldn't have GBs.
    # Assuming we are filtering the output of T015 or an intermediate step where 'species' is defined.
    # If T015 output (descriptors.csv) is the target:
    input_file = data_paths.get('processed_descriptors', project_root / 'data' / 'processed' / 'descriptors.csv')
    
    if not input_file.exists():
        # Fallback: check if we are running before descriptors are generated, 
        # but the task T019 is in Phase 3, after T015. 
        # If descriptors.csv doesn't exist, we can't filter it.
        # We will assume the file exists as per the pipeline flow.
        raise FileNotFoundError(f"Expected input file {input_file} not found. Run T015 first.")

    output_file = project_root / 'data' / 'processed' / 'descriptors_filtered.csv'
    report_file = project_root / 'data' / 'processed' / 'preprocessing_report.json'

    logger.info(f"Starting preprocessing filter on {input_file}")
    
    try:
        stats = filter_zero_impurity_configs(input_file, output_file)
        generate_preprocessing_report(stats, report_file)
        logger.info("Preprocessing filter completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing filter failed: {e}")
        raise

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_preprocessing_filter()

if __name__ == '__main__':
    main()
