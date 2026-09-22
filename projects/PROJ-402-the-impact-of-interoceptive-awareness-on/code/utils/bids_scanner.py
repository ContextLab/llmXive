"""
BIDS Scanner utilities for detecting specific tasks (Schandry, heartbeat, etc.)
in dataset metadata and events files.

This module implements the scanning logic required for T011 (Audit Metadata).
It scans directory structures for BIDS events.tsv files and checks for the presence
of specific task labels.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import pandas as pd

logger = logging.getLogger(__name__)

def find_events_files(root_path: str) -> List[Path]:
    """
    Recursively finds all events.tsv files in a BIDS dataset.
    
    Args:
        root_path: Path to the root of the BIDS dataset.
        
    Returns:
        List of Path objects pointing to events.tsv files.
    """
    root = Path(root_path)
    if not root.exists():
        logger.warning(f"Root path does not exist: {root_path}")
        return []
        
    return list(root.glob("**/*_events.tsv"))

def scan_events_for_tasks(root_path: str, target_tasks: List[str]) -> List[str]:
    """
    Scans all events.tsv files in a BIDS dataset for specific task labels.
    
    Args:
        root_path: Path to the root of the BIDS dataset.
        target_tasks: List of task names to look for (e.g., ['Schandry', 'heartbeat']).
        
    Returns:
        List of found task names from the target list.
    """
    found_tasks: Set[str] = set()
    events_files = find_events_files(root_path)
    
    if not events_files:
        logger.warning(f"No events.tsv files found in {root_path}")
        return []
        
    for event_file in events_files:
        try:
            # Read the TSV file
            df = pd.read_csv(event_file, sep='\t')
            
            if 'task' not in df.columns:
                logger.warning(f"File {event_file} does not have a 'task' column. Skipping.")
                continue
                
            # Check for target tasks
            unique_tasks = df['task'].unique().tolist()
            for task in unique_tasks:
                if task in target_tasks:
                    found_tasks.add(task)
                    
            # Log found tasks for debugging
            if found_tasks:
                logger.info(f"Found tasks in {event_file}: {found_tasks}")
                
        except Exception as e:
            logger.error(f"Error reading {event_file}: {e}")
            continue
            
    result = list(found_tasks)
    
    # Log warnings for missing tasks
    missing = set(target_tasks) - found_tasks
    if missing:
        for task in missing:
            logger.warning(f"Missing task '{task}' in dataset at {root_path}")
    
    return result

def scan_bids_dataset_for_interoception(root_path: str) -> Dict[str, Any]:
    """
    High-level scan to determine if a dataset contains interoception-related tasks.
    
    Args:
        root_path: Path to the root of the BIDS dataset.
        
    Returns:
        Dictionary with scan results.
    """
    target_tasks = ['Schandry', 'heartbeat']
    found = scan_events_for_tasks(root_path, target_tasks)
    
    return {
        "status": "success" if found else "failure",
        "found_tasks": found,
        "missing_tasks": [t for t in target_tasks if t not in found],
        "message": "Interoception tasks found" if found else "Missing Behavioral Task"
    }

def main():
    """CLI entry point for testing the scanner."""
    import argparse
    parser = argparse.ArgumentParser(description="Scan BIDS dataset for interoception tasks")
    parser.add_argument("path", help="Path to BIDS dataset")
    args = parser.parse_args()
    
    result = scan_bids_dataset_for_interoception(args.path)
    print(f"Scan Result: {result}")
    
    if not result["found_tasks"]:
        print("FEASIBILITY FAILURE: Missing Behavioral Task")
        return 1
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())