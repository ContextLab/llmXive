"""
Metric Aggregation Module (T023).

Aggregates extracted metrics per group (human-written vs LLM-generated),
computes statistics (mean, median, variance), and writes results to CSV
files in the data/metrics/ directory.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import logging configuration
from logging_config import setup_logger, get_logger

# Import data model for schema reference (optional but good practice)
from data_model import MetricResult

# Setup logger specific to this module
logger = setup_logger('metric_aggregation', level=logging.INFO)

def load_metrics_for_group(group_name: str, metrics_dir: Path) -> Optional[pd.DataFrame]:
    """
    Load metric data for a specific group from the metrics directory.
    
    Args:
        group_name: Name of the group (e.g., 'human', 'codegen')
        metrics_dir: Path to the directory containing metric CSV files
        
    Returns:
        DataFrame containing metrics for the group, or None if not found
    """
    # Expected file pattern: {group_name}_{metric_type}_metrics.csv
    # We look for all CSV files matching the group pattern
    pattern = f"{group_name}_*_metrics.csv"
    files = list(metrics_dir.glob(pattern))
    
    if not files:
        logger.warning(f"No metric files found for group '{group_name}'")
        return None
    
    # Concatenate all metric files for this group
    dfs = []
    for file_path in files:
        try:
            df = pd.read_csv(file_path)
            # Ensure group label is present
            if 'group' not in df.columns:
                df['group'] = group_name
            dfs.append(df)
            logger.info(f"Loaded {len(df)} records from {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {e}")
            continue
    
    if not dfs:
        logger.error(f"No valid metric data loaded for group '{group_name}'")
        return None
        
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total records for group '{group_name}': {len(combined_df)}")
    return combined_df

def aggregate_metrics(df: pd.DataFrame, metric_columns: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Compute aggregate statistics (mean, median, variance) for specified metric columns.
    
    Args:
        df: DataFrame containing metric values
        metric_columns: List of column names to aggregate
        
    Returns:
        Dictionary mapping metric name to statistics dict
    """
    aggregates = {}
    
    for col in metric_columns:
        if col not in df.columns:
            logger.warning(f"Metric column '{col}' not found in dataframe")
            continue
            
        values = df[col].dropna()
        if len(values) == 0:
            logger.warning(f"No valid values for metric '{col}'")
            continue
            
        aggregates[col] = {
            'mean': float(values.mean()),
            'median': float(values.median()),
            'variance': float(values.var()),
            'count': int(len(values)),
            'std': float(values.std())
        }
        
        logger.debug(f"Aggregated {col}: mean={aggregates[col]['mean']:.4f}, "
                    f"median={aggregates[col]['median']:.4f}, "
                    f"variance={aggregates[col]['variance']:.4f}")
                    
    return aggregates

def write_aggregate_csv(aggregates: Dict[str, Dict[str, float]], 
                       group_name: str, 
                       output_path: Path) -> bool:
    """
    Write aggregated metrics to a CSV file.
    
    Args:
        aggregates: Dictionary of metric statistics
        group_name: Name of the group for the filename
        output_path: Path to write the CSV file
        
    Returns:
        True if successful, False otherwise
    """
    if not aggregates:
        logger.error("No aggregates to write")
        return False
        
    # Flatten the aggregates dict for CSV
    rows = []
    for metric_name, stats in aggregates.items():
        row = {
            'metric_name': metric_name,
            'group': group_name,
            'mean': stats['mean'],
            'median': stats['median'],
            'variance': stats['variance'],
            'std': stats['std'],
            'count': stats['count']
        }
        rows.append(row)
        
    df_output = pd.DataFrame(rows)
    
    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_output.to_csv(output_path, index=False)
        logger.info(f"Wrote aggregated metrics to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write CSV to {output_path}: {e}")
        return False

def run_aggregation(metrics_dir: Path, output_dir: Path, groups: List[str] = None) -> Dict[str, Path]:
    """
    Main function to run the aggregation workflow for all groups.
    
    Args:
        metrics_dir: Directory containing raw metric CSV files
        output_dir: Directory to write aggregated CSV files
        groups: List of group names to process (default: ['human', 'codegen'])
        
    Returns:
        Dictionary mapping group name to output file path
    """
    if groups is None:
        groups = ['human', 'codegen']
        
    if not metrics_dir.exists():
        logger.error(f"Metrics directory does not exist: {metrics_dir}")
        return {}
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_files = {}
    
    for group_name in groups:
        logger.info(f"Processing aggregation for group: {group_name}")
        
        # Load metrics for this group
        df = load_metrics_for_group(group_name, metrics_dir)
        if df is None or df.empty:
            logger.warning(f"Skipping aggregation for {group_name} - no data")
            continue
            
        # Identify metric columns (exclude metadata columns)
        exclude_cols = ['snippet_id', 'group', 'timestamp', 'source_file']
        metric_columns = [col for col in df.columns if col not in exclude_cols]
        
        if not metric_columns:
            logger.warning(f"No metric columns found for group {group_name}")
            continue
            
        # Aggregate
        aggregates = aggregate_metrics(df, metric_columns)
        
        if not aggregates:
            logger.warning(f"No aggregates computed for group {group_name}")
            continue
            
        # Write output
        output_file = output_dir / f"{group_name}_aggregated_metrics.csv"
        success = write_aggregate_csv(aggregates, group_name, output_file)
        
        if success:
            output_files[group_name] = output_file
            logger.info(f"Successfully aggregated metrics for {group_name}")
        else:
            logger.error(f"Failed to aggregate metrics for {group_name}")
            
    return output_files

def main():
    """Entry point for the metric aggregation script."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    metrics_dir = project_root / "data" / "metrics"
    output_dir = project_root / "data" / "metrics"  # Output to same directory
    
    logger.info("Starting metric aggregation workflow")
    logger.info(f"Metrics directory: {metrics_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    # Run aggregation
    output_files = run_aggregation(metrics_dir, output_dir)
    
    if output_files:
        logger.info(f"Aggregation complete. Output files: {list(output_files.values())}")
        return 0
    else:
        logger.error("Aggregation failed - no output files generated")
        return 1

if __name__ == "__main__":
    exit(main())
