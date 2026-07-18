import json
import os
from pathlib import Path
from typing import Dict, List, Any
from config import ensure_directories, dataset_url
from graph_builder import load_trajectories_from_directory, build_dag, save_graph, parse_trajectory

def main():
    """
    Main entry point for building and saving graphs from TELBench trajectories.
    Processes all trajectories in data/raw and saves intermediate DAGs to data/processed/graphs/.
    """
    ensure_directories()
    
    # Define paths
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed/graphs")
    
    if not raw_dir.exists():
        print(f"Error: Raw data directory {raw_dir} does not exist.")
        print("Please run downloader.py first to fetch TELBench data.")
        return
    
    # Load trajectories
    trajectories = load_trajectories_from_directory(raw_dir)
    print(f"Loaded {len(trajectories)} trajectories.")
    
    if not trajectories:
        print("No trajectories found to process.")
        return
    
    # Process each trajectory
    success_count = 0
    for traj in trajectories:
        traj_id = traj.get("id", "unknown")
        
        try:
            # Parse early spans
            spans = parse_trajectory(traj, cutoff_depth=0.5)
            
            if not spans:
                print(f"Skipping {traj_id}: No spans found.")
                continue
            
            # Build DAG
            graph = build_dag(spans)
            
            # Save graph
            output_path = save_graph(graph, traj_id, processed_dir)
            print(f"Saved graph for {traj_id} to {output_path} ({graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges)")
            success_count += 1
            
        except Exception as e:
            print(f"Error processing {traj_id}: {e}")
            continue
    
    print(f"Graph generation complete. Processed {success_count}/{len(trajectories)} trajectories.")
    print(f"Output directory: {processed_dir}")

if __name__ == "__main__":
    main()
