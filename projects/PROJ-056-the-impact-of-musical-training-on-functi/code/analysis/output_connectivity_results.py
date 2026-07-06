"""
Output connectivity statistical results to CSV.

This module generates the final results file for User Story 2,
containing t-statistics, p-values, FDR-corrected q-values,
effect sizes (Cohen's d), and 95% confidence intervals.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional

# Import from existing project API surface
from analysis.stats import (
    process_connectivity_statistics,
    welch_t_test,
    fdr_correction_benjamini_hochberg,
    calculate_cohens_d,
    calculate_confidence_interval
)
from utils.logging import get_logger
from utils.memory_monitor import check_memory_limit

logger = get_logger(__name__)

def load_processed_connectivity_data(input_path: str) -> pd.DataFrame:
    """
    Load the processed connectivity data from previous steps.
    
    Args:
        input_path: Path to the connectivity data CSV (from T024/T025)
        
    Returns:
        DataFrame with connectivity metrics per subject
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If required columns are missing
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Connectivity data not found: {input_path}")
    
    df = pd.read_csv(input_path)
    required_cols = ['subject_id', 'group', 'connection_id', 'z_score']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    logger.info(f"Loaded {len(df)} connectivity records from {input_path}")
    return df

def compute_group_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute group-level statistics for each connection.
    
    Performs Welch's t-test, FDR correction, Cohen's d, and CI calculation
    for each connection_id across musician vs non-musician groups.
    
    Args:
        df: DataFrame with subject connectivity data
        
    Returns:
        DataFrame with aggregated statistics per connection
    """
    check_memory_limit()
    
    # Group by connection_id and compute statistics
    results = []
    
    for conn_id, group_df in df.groupby('connection_id'):
        musician_data = group_df[group_df['group'] == 'musician']['z_score']
        non_musician_data = group_df[group_df['group'] == 'non_musician']['z_score']
        
        if len(musician_data) < 2 or len(non_musician_data) < 2:
            logger.warning(f"Insufficient data for connection {conn_id}, skipping")
            continue
        
        # Welch's t-test
        t_stat, p_value = welch_t_test(musician_data, non_musician_data)
        
        # Effect size
        effect_size = calculate_cohens_d(musician_data, non_musician_data)
        
        # Confidence interval
        ci_lower, ci_upper = calculate_confidence_interval(
            effect_size, 
            len(musician_data), 
            len(non_musician_data)
        )
        
        results.append({
            'connection_id': conn_id,
            't_stat': t_stat,
            'p_value': p_value,
            'n_musician': len(musician_data),
            'n_non_musician': len(non_musician_data)
        })
    
    if not results:
        logger.error("No valid connections found for statistical analysis")
        return pd.DataFrame()
    
    results_df = pd.DataFrame(results)
    
    # FDR correction across all connections
    results_df['q_value'] = fdr_correction_benjamini_hochberg(
        results_df['p_value'].values
    )
    
    # Add effect size and CI to the results
    # Recalculate per connection for accuracy
    effect_sizes = []
    ci_lowers = []
    ci_uppers = []
    
    for _, row in results_df.iterrows():
        conn_id = row['connection_id']
        group_df = df[df['connection_id'] == conn_id]
        musician_data = group_df[group_df['group'] == 'musician']['z_score']
        non_musician_data = group_df[group_df['group'] == 'non_musician']['z_score']
        
        es = calculate_cohens_d(musician_data, non_musician_data)
        ci_l, ci_u = calculate_confidence_interval(
            es, len(musician_data), len(non_musician_data)
        )
        effect_sizes.append(es)
        ci_lowers.append(ci_l)
        ci_uppers.append(ci_u)
    
    results_df['effect_size'] = effect_sizes
    results_df['ci_lower'] = ci_lowers
    results_df['ci_upper'] = ci_uppers
    
    return results_df

def write_connectivity_results(results_df: pd.DataFrame, output_path: str) -> None:
    """
    Write the connectivity results to CSV.
    
    Args:
        results_df: DataFrame with computed statistics
        output_path: Path for the output CSV file
    """
    check_memory_limit()
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Select and order columns as specified in task
    output_columns = [
        'connection_id', 't_stat', 'p_value', 'q_value', 
        'effect_size', 'ci_lower', 'ci_upper'
    ]
    
    # Verify all required columns exist
    missing_cols = [col for col in output_columns if col not in results_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required output columns: {missing_cols}")
    
    results_df[output_columns].to_csv(output_path, index=False)
    logger.info(f"Wrote {len(results_df)} results to {output_path}")

def main():
    """Main entry point for generating connectivity results."""
    logger.info("Starting connectivity results generation (T030)")
    
    # Define paths relative to project root
    # Assuming script runs from project root or code/ directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent if script_dir.name == 'analysis' else script_dir.parent.parent.parent
    
    input_path = project_root / 'data' / 'processed' / 'connectivity_matrices_processed.csv'
    output_path = project_root / 'data' / 'processed' / 'connectivity_results.csv'
    
    # Fallback paths if running from different directory
    if not input_path.exists():
        input_path = Path('data/processed/connectivity_matrices_processed.csv')
        output_path = Path('data/processed/connectivity_results.csv')
    
    try:
        # Load processed data
        logger.info(f"Loading data from {input_path}")
        df = load_processed_connectivity_data(str(input_path))
        
        # Compute statistics
        logger.info("Computing group statistics")
        results_df = compute_group_statistics(df)
        
        if results_df.empty:
            logger.error("No results generated. Check input data.")
            sys.exit(1)
        
        # Write output
        logger.info(f"Writing results to {output_path}")
        write_connectivity_results(results_df, str(output_path))
        
        logger.info("T030 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == '__main__':
    sys.exit(main())