"""
Outlier handling for transition state graphs.

This module implements logic to flag samples with coordination numbers > 6
for exclusion from training while retaining them in the test set.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

from src.utils.logging import get_logger
from src.data.graph_construction import calculate_coordination_number

logger = get_logger(__name__)

def load_graphs_with_metadata(graphs_path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load processed graphs and their metadata.
    
    Args:
        graphs_path: Path to the graphs.parquet file
        
    Returns:
        Tuple of (graphs DataFrame, metadata dict)
    """
    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found: {graphs_path}")
    
    graphs_df = pd.read_parquet(graphs_path)
    
    # Try to load metadata if it exists
    metadata_path = graphs_path.parent / "graphs_metadata.json"
    metadata = {}
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    
    return graphs_df, metadata

def compute_coordination_numbers(graphs_df: pd.DataFrame) -> pd.Series:
    """
    Compute coordination numbers for each graph in the dataset.
    
    Args:
        graphs_df: DataFrame containing graph data with 'nodes' and 'edges' columns
        
    Returns:
        Series of coordination numbers, one per graph
    """
    coord_numbers = []
    
    for idx, row in graphs_df.iterrows():
        try:
            # Extract node and edge information
            nodes = row.get('nodes')
            edges = row.get('edges')
            
            if nodes is None or edges is None:
                coord_numbers.append(np.nan)
                continue
            
            # Calculate coordination number using the existing function
            # We assume the graph data is structured appropriately for the function
            cn = calculate_coordination_number(nodes, edges, cutoff=3.5)
            coord_numbers.append(cn)
            
        except Exception as e:
            logger.warning(f"Failed to compute coordination number for graph {idx}: {e}")
            coord_numbers.append(np.nan)
    
    return pd.Series(coord_numbers, index=graphs_df.index)

def flag_outliers(
    graphs_df: pd.DataFrame,
    threshold: int = 6,
    max_coord_key: str = 'max_coordination_number',
    is_outlier_key: str = 'is_training_outlier'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Flag samples with coordination numbers > threshold as outliers.
    
    Outliers are marked for exclusion from training but retained in test set.
    
    Args:
        graphs_df: DataFrame containing graph data
        threshold: Coordination number threshold (default: 6)
        max_coord_key: Column name for max coordination number
        is_outlier_key: Column name for outlier flag
        
    Returns:
        Tuple of (updated DataFrame, summary statistics dict)
    """
    logger.info(f"Computing coordination numbers and flagging outliers (threshold={threshold})")
    
    # Compute coordination numbers
    graphs_df[max_coord_key] = compute_coordination_numbers(graphs_df)
    
    # Flag outliers: coordination number > threshold
    graphs_df[is_outlier_key] = graphs_df[max_coord_key] > threshold
    
    # Calculate statistics
    total_samples = len(graphs_df)
    outlier_count = graphs_df[is_outlier_key].sum()
    training_samples = total_samples - outlier_count
    outlier_percentage = (outlier_count / total_samples * 100) if total_samples > 0 else 0
    
    summary = {
        'total_samples': int(total_samples),
        'outlier_count': int(outlier_count),
        'training_samples': int(training_samples),
        'outlier_percentage': float(outlier_percentage),
        'threshold': int(threshold),
        'outlier_indices': graphs_df[graphs_df[is_outlier_key]].index.tolist()
    }
    
    logger.info(f"Outlier handling complete: {outlier_count}/{total_samples} samples flagged ({outlier_percentage:.2f}%)")
    logger.info(f"Training set size: {training_samples} samples")
    
    return graphs_df, summary

def save_outlier_summary(summary: Dict[str, Any], output_path: Path) -> None:
    """
    Save outlier handling summary to JSON file.
    
    Args:
        summary: Summary statistics dictionary
        output_path: Path to save the JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Outlier summary saved to: {output_path}")

def save_flagged_graphs(graphs_df: pd.DataFrame, output_path: Path) -> None:
    """
    Save graphs with outlier flags to parquet file.
    
    Args:
        graphs_df: DataFrame with outlier flags added
        output_path: Path to save the parquet file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    graphs_df.to_parquet(output_path, index=False)
    logger.info(f"Flagged graphs saved to: {output_path}")

def run_outlier_handling(
    input_graphs_path: Path,
    output_graphs_path: Path,
    output_summary_path: Path,
    threshold: int = 6
) -> Dict[str, Any]:
    """
    Main function to run outlier handling on a dataset.
    
    Args:
        input_graphs_path: Path to input graphs.parquet
        output_graphs_path: Path to save flagged graphs.parquet
        output_summary_path: Path to save outlier summary JSON
        threshold: Coordination number threshold (default: 6)
        
    Returns:
        Summary statistics dictionary
    """
    logger.info(f"Starting outlier handling with threshold={threshold}")
    logger.info(f"Input: {input_graphs_path}")
    
    # Load graphs
    graphs_df, metadata = load_graphs_with_metadata(input_graphs_path)
    logger.info(f"Loaded {len(graphs_df)} graphs")
    
    # Flag outliers
    graphs_df, summary = flag_outliers(graphs_df, threshold=threshold)
    
    # Save results
    save_flagged_graphs(graphs_df, output_graphs_path)
    save_outlier_summary(summary, output_summary_path)
    
    logger.info("Outlier handling completed successfully")
    return summary

def main() -> None:
    """Main entry point for outlier handling script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Flag outlier graphs based on coordination number")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/graphs.parquet"),
        help="Path to input graphs.parquet"
    )
    parser.add_argument(
        "--output-graphs",
        type=Path,
        default=Path("data/processed/graphs_flagged.parquet"),
        help="Path to save flagged graphs"
    )
    parser.add_argument(
        "--output-summary",
        type=Path,
        default=Path("data/processed/outlier_summary.json"),
        help="Path to save outlier summary"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=6,
        help="Coordination number threshold for outliers (default: 6)"
    )
    
    args = parser.parse_args()
    
    run_outlier_handling(
        input_graphs_path=args.input,
        output_graphs_path=args.output_graphs,
        output_summary_path=args.output_summary,
        threshold=args.threshold
    )

if __name__ == "__main__":
    main()
