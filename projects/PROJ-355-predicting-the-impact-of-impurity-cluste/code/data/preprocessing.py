import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from config import get_project_root, get_data_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def filter_zero_impurity_configs(input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter bulk configurations that have zero impurity atoms.
    
    Args:
        input_df: DataFrame containing configuration data with a column 
                  indicating the number of impurity atoms (e.g., 'impurity_count').
    
    Returns:
        Filtered DataFrame containing only configurations with at least one impurity atom.
    """
    # Check if the expected column exists
    # Assuming the column is named 'impurity_count' based on common conventions
    # If the actual column name differs, this should be adjusted
    impurity_count_col = 'impurity_count'
    
    if impurity_count_col not in input_df.columns:
        # Fallback: try to infer or raise an error
        logger.warning(f"Column '{impurity_count_col}' not found in input DataFrame. "
                       f"Available columns: {list(input_df.columns)}")
        # If we can't determine impurity count, we cannot filter safely.
        # Return the original DataFrame and log a warning.
        return input_df
    
    # Filter out rows where impurity_count is zero
    filtered_df = input_df[input_df[impurity_count_col] > 0].copy()
    excluded_count = len(input_df) - len(filtered_df)
    
    logger.info(f"Filtered {excluded_count} configurations with zero impurity atoms.")
    
    return filtered_df

def generate_preprocessing_report(excluded_count: int, total_count: int, output_path: Path) -> None:
    """
    Generate a JSON report documenting the preprocessing filter results.
    
    Args:
        excluded_count: Number of configurations excluded (zero impurity atoms).
        total_count: Total number of configurations processed.
        output_path: Path to save the JSON report.
    """
    report = {
        "filter_type": "zero_impurity_removal",
        "total_configurations": total_count,
        "excluded_count": excluded_count,
        "retained_count": total_count - excluded_count,
        "exclusion_reason": "Configurations with zero impurity atoms do not contribute to segregation analysis."
    }
    
    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Preprocessing report saved to {output_path}")

def run_preprocessing_filter(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main function to run the preprocessing filter on the dataset.
    
    Args:
        input_path: Path to the input CSV file (descriptors/energies merged).
                   If None, uses default path from config.
        output_path: Path to save the filtered dataset.
                    If None, uses default path from config.
    
    Returns:
        Dictionary containing the report summary.
    """
    project_root = get_project_root()
    data_paths = get_data_paths()
    
    # Default paths if not provided
    if input_path is None:
        # Assuming the input is the merged descriptors and energies file
        # This path might need adjustment based on actual pipeline output
        input_path = project_root / data_paths.get('processed_descriptors', 'data/processed/descriptors.csv')
    
    if output_path is None:
        output_path = project_root / data_paths.get('processed_filtered', 'data/processed/descriptors_filtered.csv')
    
    preprocessing_report_path = project_root / data_paths.get('preprocessing_report', 'data/processed/preprocessing_report.json')
    
    logger.info(f"Loading input data from {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load the data
    df = pd.read_csv(input_path)
    total_count = len(df)
    
    # Apply filter
    filtered_df = filter_zero_impurity_configs(df)
    excluded_count = total_count - len(filtered_df)
    
    # Save filtered data
    logger.info(f"Saving filtered data to {output_path}")
    filtered_df.to_csv(output_path, index=False)
    
    # Generate report
    generate_preprocessing_report(excluded_count, total_count, preprocessing_report_path)
    
    return {
        "total": total_count,
        "excluded": excluded_count,
        "retained": len(filtered_df),
        "output_path": str(output_path),
        "report_path": str(preprocessing_report_path)
    }

def main():
    """Entry point for the preprocessing filter script."""
    try:
        result = run_preprocessing_filter()
        logger.info("Preprocessing filter completed successfully.")
        logger.info(f"Result: {result}")
    except Exception as e:
        logger.error(f"Preprocessing filter failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
