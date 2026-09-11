"""
Script to generate the structured CSV file for graph metrics.

This script loads the processed calibration data (which contains device coupling maps),
computes topological metrics using the graph_builder module, and saves the results
to data/processed/graph_metrics.csv.

Output columns: device_id, metric_name, value, is_finite
"""
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

from graph_builder import process_device_coupling_map
from logger import setup_logger

# Configure logging
logger = setup_logger(__name__)

def load_processed_calibration(csv_path: str) -> pd.DataFrame:
    """
    Load the processed calibration CSV containing device metrics and coupling maps.
    
    Args:
        csv_path: Path to the raw_calibration.csv file.
        
    Returns:
        DataFrame with device metrics.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed calibration file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    required_cols = ['device_id', 'coupling_map']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {csv_path}: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} devices from {csv_path}")
    return df

def compute_device_metrics(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Compute graph metrics for each device and return a list of records.
    
    Args:
        df: DataFrame with device_id and coupling_map.
        
    Returns:
        List of dictionaries containing device_id, metric_name, value, is_finite.
    """
    records = []
    
    for _, row in df.iterrows():
        device_id = row['device_id']
        coupling_map_str = row['coupling_map']
        
        # Parse the coupling map string back to a list of tuples
        # Format expected: "[(0, 1), (1, 2), ...]"
        try:
            import ast
            coupling_map = ast.literal_eval(coupling_map_str)
        except (ValueError, SyntaxError) as e:
            logger.warning(f"Failed to parse coupling map for {device_id}: {e}")
            continue
        
        # Compute metrics using the graph_builder module
        metrics = process_device_coupling_map(coupling_map, device_id)
        
        for metric_name, value in metrics.items():
            is_finite = bool(pd.notna(value) and (not isinstance(value, float) or (value != float('inf') and value != float('-inf'))))
            records.append({
                'device_id': device_id,
                'metric_name': metric_name,
                'value': value,
                'is_finite': is_finite
            })
    
    return records

def main():
    """Main entry point to generate the graph metrics CSV."""
    # Define paths
    base_dir = Path(__file__).parent.parent
    input_csv = base_dir / "data" / "processed" / "raw_calibration.csv"
    output_csv = base_dir / "data" / "processed" / "graph_metrics.csv"
    
    # Ensure output directory exists
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        df = load_processed_calibration(str(input_csv))
        
        # Compute metrics
        records = compute_device_metrics(df)
        
        if not records:
            logger.warning("No metrics computed. Check input data.")
            # Create empty file with headers
            with open(output_csv, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['device_id', 'metric_name', 'value', 'is_finite'])
                writer.writeheader()
            return
        
        # Write to CSV
        with open(output_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['device_id', 'metric_name', 'value', 'is_finite'])
            writer.writeheader()
            writer.writerows(records)
        
        logger.info(f"Successfully wrote {len(records)} metric records to {output_csv}")
        
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during metric generation: {e}")
        raise

if __name__ == "__main__":
    main()
