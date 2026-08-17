"""
Module to output connectivity results to CSV.

This module handles the loading of processed connectivity data,
computation of group statistics, and writing of results to the
data/processed/connectivity_results.csv file.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

# Import from sibling modules using the provided API surface
from utils.logging import get_logger
from analysis.stats import welch_t_test, fdr_correction_benjamini_hochberg, calculate_cohens_d, calculate_confidence_interval

logger = get_logger(__name__)

def load_processed_connectivity_data(
    connectivity_matrix_path: str,
    subject_data_path: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load processed connectivity matrices and subject data.
    
    Args:
        connectivity_matrix_path: Path to the file containing connectivity matrices
        subject_data_path: Path to the cleaned subjects CSV file
        
    Returns:
        Tuple of (connectivity_df, subject_df)
        
    Raises:
        FileNotFoundError: If input files do not exist
        ValueError: If data formats are invalid
    """
    logger.info(f"Loading connectivity data from {connectivity_matrix_path}")
    logger.info(f"Loading subject data from {subject_data_path}")
    
    if not os.path.exists(connectivity_matrix_path):
        raise FileNotFoundError(f"Connectivity matrix file not found: {connectivity_matrix_path}")
    if not os.path.exists(subject_data_path):
        raise FileNotFoundError(f"Subject data file not found: {subject_data_path}")
        
    # Load connectivity matrices (assuming format from T024: subject_id, matrix_data as list/array)
    connectivity_df = pd.read_csv(connectivity_matrix_path)
    
    # Load subject data (from T019: subjects_cleaned.csv)
    subject_df = pd.read_csv(subject_data_path)
    
    logger.info(f"Loaded {len(connectivity_df)} connectivity records")
    logger.info(f"Loaded {len(subject_df)} subject records")
    
    return connectivity_df, subject_df

def compute_group_statistics(
    connectivity_df: pd.DataFrame,
    subject_df: pd.DataFrame,
    group_column: str = 'group',
    subject_id_column: str = 'subject_id'
) -> pd.DataFrame:
    """
    Compute group statistics for connectivity data.
    
    This function:
    1. Merges connectivity data with subject data to get group labels
    2. Reshapes data to have one row per connection with values for each group
    3. Performs Welch's t-test, FDR correction, Cohen's d, and CI calculation
    4. Returns a DataFrame with all statistics
    
    Args:
        connectivity_df: DataFrame with subject_id and connectivity data
        subject_df: DataFrame with subject_id and group labels
        group_column: Name of the column containing group labels
        subject_id_column: Name of the column containing subject IDs
        
    Returns:
        DataFrame with connection_id, t_stat, p_value, q_value, effect_size, ci_lower, ci_upper
    """
    logger.info("Computing group statistics for connectivity data")
    
    # Merge to get group labels for each subject
    merged_df = pd.merge(connectivity_df, subject_df[[subject_id_column, group_column]], 
                       on=subject_id_column, how='inner')
    
    if len(merged_df) == 0:
        raise ValueError("No matching subjects found after merging connectivity and subject data")
    
    # Identify connection columns (exclude subject_id and group)
    connection_cols = [col for col in merged_df.columns 
                     if col not in [subject_id_column, group_column]]
    
    if len(connection_cols) == 0:
        raise ValueError("No connection columns found in the data")
    
    logger.info(f"Found {len(connection_cols)} connections to analyze")
    
    results = []
    
    for conn_col in connection_cols:
        # Split data by group
        musician_data = merged_df[merged_df[group_column] == 'musician'][conn_col].values
        non_musician_data = merged_df[merged_df[group_column] == 'non_musician'][conn_col].values
        
        # Skip if either group has insufficient data
        if len(musician_data) < 2 or len(non_musician_data) < 2:
            logger.warning(f"Skipping {conn_col}: insufficient data in one group")
            continue
        
        # Perform Welch's t-test
        t_stat, p_value = welch_t_test(musician_data, non_musician_data)
        
        # Calculate effect size (Cohen's d)
        effect_size = calculate_cohens_d(musician_data, non_musician_data)
        
        # Calculate 95% confidence interval
        ci_lower, ci_upper = calculate_confidence_interval(effect_size, len(musician_data), len(non_musician_data))
        
        results.append({
            'connection_id': conn_col,
            't_stat': t_stat,
            'p_value': p_value,
            'effect_size': effect_size,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        })
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    if len(results_df) == 0:
        raise ValueError("No valid results computed from the data")
    
    # Apply FDR correction to p-values
    logger.info(f"Applying FDR correction to {len(results_df)} p-values")
    results_df['q_value'] = fdr_correction_benjamini_hochberg(results_df['p_value'].values)
    
    logger.info(f"Computed statistics for {len(results_df)} connections")
    return results_df

def write_connectivity_results(
    results_df: pd.DataFrame,
    output_path: str
) -> None:
    """
    Write connectivity results to CSV file.
    
    Args:
        results_df: DataFrame with connection statistics
        output_path: Path to write the results CSV
        
    Raises:
        IOError: If writing fails
    """
    logger.info(f"Writing connectivity results to {output_path}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Define expected columns
    expected_columns = ['connection_id', 't_stat', 'p_value', 'q_value', 'effect_size', 'ci_lower', 'ci_upper']
    
    # Validate columns
    missing_cols = [col for col in expected_columns if col not in results_df.columns]
    if missing_cols:
        raise ValueError(f"Results DataFrame missing required columns: {missing_cols}")
    
    # Write to CSV
    results_df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully wrote {len(results_df)} records to {output_path}")

def main():
    """
    Main function to run the connectivity results output pipeline.
    
    This function:
    1. Loads processed connectivity data and subject data
    2. Computes group statistics (t-test, FDR, effect size, CI)
    3. Writes results to data/processed/connectivity_results.csv
    
    Usage:
        python code/analysis/output_connectivity_results.py
    """
    logger.info("Starting connectivity results output pipeline")
    
    # Define paths
    base_path = Path(__file__).parent.parent.parent
    connectivity_path = base_path / "data" / "processed" / "connectivity_matrices.csv"
    subject_path = base_path / "data" / "processed" / "subjects_cleaned.csv"
    output_path = base_path / "data" / "processed" / "connectivity_results.csv"
    
    try:
        # Load data
        connectivity_df, subject_df = load_processed_connectivity_data(
            str(connectivity_path),
            str(subject_path)
        )
        
        # Compute statistics
        results_df = compute_group_statistics(connectivity_df, subject_df)
        
        # Write results
        write_connectivity_results(results_df, str(output_path))
        
        logger.info("Connectivity results output pipeline completed successfully")
        print(f"Results written to: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
