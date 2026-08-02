"""
BIDS Scanner Utilities for Interoceptive Awareness Project.

This module provides functions to scan local BIDS datasets, specifically
looking for 'events.tsv' files and checking their content for specific
task labels (e.g., 'Schandry', 'heartbeat').

Per FR-002: Scan for task column values matching 'Schandry' or 'heartbeat' (case-insensitive).
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

import pandas as pd

logger = logging.getLogger(__name__)

# Target task labels to search for (case-insensitive matching performed)
TARGET_TASKS = {'schandry', 'heartbeat'}

def find_events_files(root_dir: Path) -> List[Path]:
    """
    Recursively find all 'events.tsv' files within a BIDS directory structure.

    Args:
        root_dir: The root directory of the BIDS dataset.

    Returns:
        A list of Path objects pointing to found events.tsv files.
    """
    if not root_dir.exists():
        logger.warning(f"Root directory does not exist: {root_dir}")
        return []

    events_files = list(root_dir.rglob("events.tsv"))
    logger.info(f"Found {len(events_files)} events.tsv files in {root_dir}")
    return events_files

def scan_events_for_tasks(events_file: Path) -> Optional[Dict[str, Any]]:
    """
    Scan a single events.tsv file for target task labels.

    Reads the TSV file and checks the 'task' column (if present) or the
    filename for indications of the task. Per BIDS convention, the task
    label is often in the filename (e.g., sub-01_task-schandry_events.tsv),
    but we strictly check the 'task' column in the TSV content if available
    as per the specific requirement to scan the column.

    Args:
        events_file: Path to the events.tsv file.

    Returns:
        A dictionary with keys:
            - 'file': Path to the file
            - 'found_tasks': Set of found target task labels (lowercase)
            - 'missing': Boolean indicating if any target tasks were found
        Returns None if the file cannot be read or parsed.
    """
    result = {
        'file': events_file,
        'found_tasks': set(),
        'error': None
    }

    try:
        # Read the TSV file
        df = pd.read_csv(events_file, sep='\t')

        # Check if 'task' column exists
        if 'task' in df.columns:
            # Convert to string and lowercase for case-insensitive comparison
            tasks_in_file = df['task'].astype(str).str.lower().unique()
            found = set(tasks_in_file).intersection(TARGET_TASKS)
            result['found_tasks'].update(found)
        else:
            # Fallback: Check filename if column is missing, as BIDS often encodes it there.
            # This ensures we don't miss data if the column is absent but the file is valid.
            stem = events_file.stem
            for target in TARGET_TASKS:
                if target in stem.lower():
                    result['found_tasks'].add(target)

        if not result['found_tasks']:
            result['error'] = "No target tasks ('Schandry', 'heartbeat') found in this file."

    except Exception as e:
        logger.error(f"Error scanning {events_file}: {e}")
        result['error'] = str(e)

    return result

def scan_bids_dataset_for_interoception(root_dir: Path) -> Dict[str, Any]:
    """
    Scan a BIDS dataset directory for interoception-related tasks.

    This function aggregates results from scanning all events.tsv files
    in the dataset.

    Args:
        root_dir: Root directory of the BIDS dataset.

    Returns:
        A summary dictionary containing:
            - 'total_files_scanned': int
            - 'files_with_target_tasks': List of paths
            - 'unique_tasks_found': Set of unique task labels found
            - 'missing_tasks': Set of target tasks not found in the entire dataset
    """
    events_files = find_events_files(root_dir)

    summary = {
        'total_files_scanned': len(events_files),
        'files_with_target_tasks': [],
        'unique_tasks_found': set(),
        'all_files_results': []
    }

    if not events_files:
        logger.warning(f"No events.tsv files found in {root_dir}")
        summary['missing_tasks'] = TARGET_TASKS.copy()
        return summary

    for f_path in events_files:
        scan_result = scan_events_for_tasks(f_path)
        if scan_result and scan_result['error'] is None:
            if scan_result['found_tasks']:
                summary['files_with_target_tasks'].append(f_path)
                summary['unique_tasks_found'].update(scan_result['found_tasks'])
        summary['all_files_results'].append(scan_result)

    # Determine missing tasks
    summary['missing_tasks'] = TARGET_TASKS - summary['unique_tasks_found']

    return summary

def main():
    """
    CLI entry point for scanning a dataset.
    Expects a path argument or uses a default if not provided (for testing).
    """
    import argparse

    parser = argparse.ArgumentParser(description="Scan BIDS dataset for interoception tasks.")
    parser.add_argument("dataset_path", type=Path, nargs="?", default=None, help="Path to BIDS dataset root")
    args = parser.parse_args()

    if args.dataset_path is None:
        # Default to data/processed if available, else current dir
        potential_path = Path("data/processed")
        if potential_path.exists():
            args.dataset_path = potential_path
            logger.info(f"Using default path: {args.dataset_path}")
        else:
            logger.error("No dataset path provided and 'data/processed' does not exist.")
            return 1

    if not args.dataset_path.exists():
        logger.error(f"Dataset path does not exist: {args.dataset_path}")
        return 1

    logger.info(f"Scanning dataset at: {args.dataset_path}")
    results = scan_bids_dataset_for_interoception(args.dataset_path)

    logger.info(f"Scan complete. Found {results['total_files_scanned']} events files.")
    logger.info(f"Tasks found: {results['unique_tasks_found']}")
    if results['missing_tasks']:
        logger.warning(f"Missing target tasks: {results['missing_tasks']}")

    if results['files_with_target_tasks']:
        logger.info("Files containing target tasks:")
        for f in results['files_with_target_tasks']:
            logger.info(f"  - {f}")

    return 0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    exit(main())
