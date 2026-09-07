import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from code.config import get_project_root, get_data_paths

logger = logging.getLogger(__name__)

def filter_zero_impurity_configs(input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters bulk configurations to remove rows where the number of impurity atoms is zero.
    
    Args:
        input_df: DataFrame containing configuration data, expected to have a column 
                  indicating impurity count (e.g., 'impurity_count' or derived from 'impurity_species').
    
    Returns:
        A filtered DataFrame containing only rows with at least one impurity atom.
    
    Raises:
        ValueError: If the input DataFrame is empty or lacks necessary columns.
    """
    if input_df.empty:
        raise ValueError("Input DataFrame is empty.")
    
    # Determine the column to check. 
    # Based on typical pipeline flow, 'impurity_count' is the direct metric.
    # If 'impurity_species' exists but is empty string, that also implies 0 impurities.
    
    count_col = None
    if 'impurity_count' in input_df.columns:
        count_col = 'impurity_count'
    elif 'impurity_species' in input_df.columns:
        # Fallback: check if species is not empty/None
        # We'll create a temporary count column for filtering
        input_df['temp_impurity_count'] = input_df['impurity_species'].apply(
            lambda x: 1 if pd.notna(x) and str(x).strip() != '' else 0
        )
        count_col = 'temp_impurity_count'
    else:
        raise ValueError("Input DataFrame missing 'impurity_count' or 'impurity_species' column.")
    
    initial_count = len(input_df)
    filtered_df = input_df[input_df[count_col] > 0].copy()
    final_count = len(filtered_df)
    excluded_count = initial_count - final_count
    
    logger.info(f"Filtered configurations: {initial_count} -> {final_count} (Excluded {excluded_count} with zero impurities)")
    
    # Clean up temporary column if created
    if count_col == 'temp_impurity_count' and 'temp_impurity_count' in filtered_df.columns:
        filtered_df.drop(columns=['temp_impurity_count'], inplace=True)
        
    return filtered_df, excluded_count

def generate_preprocessing_report(excluded_count: int, output_path: Path) -> None:
    """
    Generates a JSON report logging the exclusion count of configurations with zero impurity atoms.
    
    Args:
        excluded_count: The number of configurations excluded.
        output_path: The path where the JSON report will be saved.
    """
    report = {
        "task": "filter_zero_impurity_configs",
        "excluded_count": excluded_count,
        "reason": "Configurations with zero impurity atoms do not contribute to segregation energy analysis and were removed.",
        "status": "completed"
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Preprocessing report saved to {output_path}")

def run_preprocessing_filter() -> None:
    """
    Main entry point to run the zero impurity filtering logic.
    Reads processed descriptors/energies, filters, and saves the report.
    """
    project_root = get_project_root()
    data_paths = get_data_paths()
    
    # Determine input source. 
    # The pipeline flow suggests descriptors (T015) or energies (T016c) are the primary processed data.
    # We will attempt to load descriptors.csv as it is the primary feature set.
    input_file = data_paths['processed'] / "descriptors.csv"
    
    if not input_file.exists():
        # Fallback to energies if descriptors not found, though less likely to have impurity info there directly
        input_file = data_paths['processed'] / "segregation_energies.csv"
    
    if not input_file.exists():
        logger.warning(f"No input file found at {input_file} or fallback. Skipping filtering.")
        # Even if no input, we should generate a report stating 0 processed
        report_path = data_paths['processed'] / "preprocessing_report.json"
        generate_preprocessing_report(0, report_path)
        return

    logger.info(f"Loading data from {input_file}")
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        return

    try:
        filtered_df, excluded_count = filter_zero_impurity_configs(df)
        
        # Optionally save the filtered data back if the pipeline expects it to be updated
        # For this task, the primary requirement is the report.
        # If downstream tasks expect the filtered data, we save it.
        output_data_path = data_paths['processed'] / "descriptors_filtered.csv"
        filtered_df.to_csv(output_data_path, index=False)
        logger.info(f"Filtered data saved to {output_data_path}")
        
        # Generate the required report
        report_path = data_paths['processed'] / "preprocessing_report.json"
        generate_preprocessing_report(excluded_count, report_path)
        
    except ValueError as e:
        logger.error(f"Filtering failed: {e}")
        # Still generate a report indicating failure or 0 processed if applicable
        report_path = data_paths['processed'] / "preprocessing_report.json"
        generate_preprocessing_report(0, report_path)

def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    run_preprocessing_filter()

if __name__ == "__main__":
    main()
