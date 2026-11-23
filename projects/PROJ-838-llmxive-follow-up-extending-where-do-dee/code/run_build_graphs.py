import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any

from config import ensure_directories, dataset_url
from graph_builder import load_trajectories_from_directory, build_dag, save_graph, parse_trajectory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point to build and save graphs for all trajectories.
    This script is designed to be run after data has been downloaded to data/raw.
    """
    ensure_directories()
    
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed/graphs")
    
    if not raw_dir.exists():
        logger.error("Raw data directory 'data/raw' does not exist. Run downloader first.")
        return
    
    trajectories = load_trajectories_from_directory(raw_dir)
    
    if not trajectories:
        logger.warning("No trajectories found in data/raw.")
        return
    
    logger.info(f"Processing {len(trajectories)} trajectories...")
    
    success_count = 0
    error_count = 0
    
    for traj in trajectories:
        traj_id = traj.get("id", "unknown")
        try:
            # Build DAG using default cutoff (0.5) or from config if added later
            dag = build_dag(traj, cutoff_depth=0.5)
            
            # Save the graph
            save_graph(dag, traj_id, processed_dir)
            success_count += 1
        except Exception as e:
            logger.error(f"Error processing trajectory {traj_id}: {e}")
            error_count += 1
    
    logger.info(f"Graph building complete. Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    main()