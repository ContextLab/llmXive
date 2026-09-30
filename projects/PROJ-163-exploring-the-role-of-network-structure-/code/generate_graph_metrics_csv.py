"""
Script to generate the graph metrics CSV from raw calibration snapshots.

This script implements Task T025b: Generate Graph Metrics CSV.
It reads raw JSON snapshots from data/raw/, builds coupling graphs,
computes metrics, and writes the result to data/processed/graph_metrics.csv.

Entry Point: python code/generate_graph_metrics_csv.py
"""
import os
import csv
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

# Import from local modules using the defined API surface
from graph_builder import (
    build_coupling_graph,
    compute_shortest_path_metrics,
    compute_clustering_and_assortativity,
    compute_edge_betweenness_and_spectral_gap
)
from logging_config import get_logger

logger = get_logger(__name__)

def load_processed_calibration(raw_data_dir: Path) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Load all raw calibration snapshots from the data/raw directory.
    
    Args:
        raw_data_dir: Path to the directory containing raw JSON files.
        
    Returns:
        List of tuples (device_id, coupling_map_data) for each valid snapshot.
        Raises FileNotFoundError if no files are found.
    """
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    files = list(raw_data_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No JSON files found in {raw_data_dir}")
    
    results = []
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract device_id and coupling_map
            # The schema expects 'device_id' and 'coupling_map' in the root
            device_id = data.get('device_id')
            coupling_map = data.get('coupling_map')
            
            if not device_id or not coupling_map:
                logger.warning(f"Skipping {file_path}: missing device_id or coupling_map")
                continue
            
            results.append((device_id, coupling_map))
            logger.info(f"Loaded snapshot for {device_id} from {file_path.name}")
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing {file_path}: {e}")
            continue
    
    if not results:
        raise ValueError("No valid calibration snapshots found to process.")
    
    return results

def compute_device_metrics(coupling_map: List[List[int]]) -> Dict[str, float]:
    """
    Compute all graph metrics for a given coupling map.
    
    Args:
        coupling_map: List of [source, target] edges.
        
    Returns:
        Dictionary of metric_name -> value.
    """
    # Build the graph
    G = build_coupling_graph(coupling_map)
    
    metrics = {}
    
    # Shortest path metrics
    try:
        sp_metrics = compute_shortest_path_metrics(G)
        metrics.update(sp_metrics)
    except Exception as e:
        logger.warning(f"Could not compute shortest path metrics: {e}")
    
    # Clustering and assortativity
    try:
        cluster_metrics = compute_clustering_and_assortativity(G)
        metrics.update(cluster_metrics)
    except Exception as e:
        logger.warning(f"Could not compute clustering/assortativity metrics: {e}")
    
    # Edge betweenness and spectral gap
    try:
        betweenness_metrics = compute_edge_betweenness_and_spectral_gap(G)
        metrics.update(betweenness_metrics)
    except Exception as e:
        logger.warning(f"Could not compute betweenness/spectral gap metrics: {e}")
    
    return metrics

def main():
    """
    Main entry point for generating the graph metrics CSV.
    
    Reads raw JSON files from data/raw/, computes graph metrics,
    and writes the result to data/processed/graph_metrics.csv.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    raw_data_dir = project_root / "data" / "raw"
    output_dir = project_root / "data" / "processed"
    output_file = output_dir / "graph_metrics.csv"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting graph metrics generation. Input: {raw_data_dir}")
    
    # Load raw snapshots
    try:
        snapshots = load_processed_calibration(raw_data_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    all_rows = []
    
    for device_id, coupling_map in snapshots:
        logger.info(f"Processing {device_id}...")
        try:
            metrics = compute_device_metrics(coupling_map)
            
            for metric_name, value in metrics.items():
                is_finite = float('inf') != value and float('-inf') != value and not (value != value) # Check for inf or nan
                # More robust check using math.isfinite if available, but float checks work too
                if isinstance(value, float):
                    import math
                    is_finite = math.isfinite(value)
                else:
                    is_finite = True
                    
                all_rows.append({
                    "device_id": device_id,
                    "metric_name": metric_name,
                    "value": value,
                    "is_finite": is_finite
                })
                
        except Exception as e:
            logger.error(f"Failed to compute metrics for {device_id}: {e}")
            continue
    
    if not all_rows:
        logger.warning("No metrics were computed. Output file will be empty.")
    
    # Write to CSV
    fieldnames = ["device_id", "metric_name", "value", "is_finite"]
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    
    logger.info(f"Successfully wrote {len(all_rows)} rows to {output_file}")
    return output_file

if __name__ == "__main__":
    # Initialize logging for the script run
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
