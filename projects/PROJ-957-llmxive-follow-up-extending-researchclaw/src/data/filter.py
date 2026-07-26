"""
Filter tasks from ResearchClawBench dataset based on failure_mode metadata.

This module implements the logic to select tasks where the metadata field
`failure_mode` equals "experimental protocol mismatch".
"""

import json
import hashlib
import csv
import sys
import os
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any, Optional

# Ensure we can import from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from datasets import load_dataset
from src.config import Config
from src.utils.checksum import compute_sha256, write_checksum
from src.utils.logging import setup_logging, log_with_context, get_global_error_tracker


def load_researchclawbench_data() -> Any:
    """
    Load the ResearchClawBench dataset using the ID from Config.
    Returns the dataset object.
    """
    config = Config()
    dataset_id = config.RESEARCHCLAWBENCH_DATASET_ID
    logger = setup_logging("filter")
    logger.info(f"Loading dataset: {dataset_id}")
    
    try:
        # Load dataset with streaming to handle large sizes efficiently
        # We need to materialize it for counting, so we load fully but efficiently
        dataset = load_dataset(dataset_id, split="train", trust_remote_code=True)
        logger.info(f"Dataset loaded successfully. Total rows: {len(dataset)}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        raise


def filter_by_failure_mode(dataset: Any, target_mode: str = "experimental protocol mismatch") -> List[Dict[str, Any]]:
    """
    Filter dataset rows where metadata['failure_mode'] equals target_mode.
    
    Args:
        dataset: The loaded dataset object
        target_mode: The failure mode to filter for (default: "experimental protocol mismatch")
        
    Returns:
        List of dictionaries representing the filtered tasks
    """
    logger = setup_logging("filter")
    filtered_tasks = []
    
    for item in dataset:
        # Check if the item has the required metadata structure
        if 'metadata' not in item:
            logger.warning(f"Item missing 'metadata' key: {item.get('id', 'unknown')}")
            continue
        
        metadata = item['metadata']
        
        # FR-006: Check if failure_mode key exists
        if 'failure_mode' not in metadata:
            logger.error(f"FR-006 Violation: 'failure_mode' key missing in metadata for item {item.get('id', 'unknown')}")
            raise KeyError("FR-006: 'failure_mode' key is missing entirely from dataset metadata")
        
        failure_mode = metadata['failure_mode']
        
        if failure_mode == target_mode:
            filtered_tasks.append(item)
    
    logger.info(f"Filtered {len(filtered_tasks)} tasks with failure_mode='{target_mode}'")
    return filtered_tasks


def analyze_failure_modes(dataset: Any) -> Dict[str, int]:
    """
    Analyze the distribution of failure modes in the dataset.
    
    Args:
        dataset: The loaded dataset object
        
    Returns:
        Dictionary mapping failure_mode values to their counts
    """
    logger = setup_logging("filter")
    mode_counts = Counter()
    total_tasks = 0
    
    for item in dataset:
        if 'metadata' in item and 'failure_mode' in item['metadata']:
            mode_counts[item['metadata']['failure_mode']] += 1
            total_tasks += 1
        else:
            total_tasks += 1  # Count total even if missing, but don't add to mode_counts
    
    logger.info(f"Analyzed {total_tasks} tasks. Mode distribution: {dict(mode_counts)}")
    return dict(mode_counts)


def write_failure_mode_audit(mode_counts: Dict[str, int], total_tasks: int, output_path: Path) -> None:
    """
    Write the failure mode audit report to CSV.
    
    Args:
        mode_counts: Dictionary of failure mode counts
        total_tasks: Total number of tasks analyzed
        output_path: Path to write the CSV file
    """
    logger = setup_logging("filter")
    
    if not mode_counts:
        logger.warning("No failure modes found to audit")
        return
        
    dominant_mode = max(mode_counts, key=mode_counts.get)
    dominant_count = mode_counts[dominant_mode]
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['dominant_mode', 'count', 'total_tasks'])
        writer.writerow([dominant_mode, dominant_count, total_tasks])
    
    logger.info(f"Failure mode audit written to {output_path}: dominant='{dominant_mode}', count={dominant_count}, total={total_tasks}")


def write_subset_json(tasks: List[Dict[str, Any]], output_path: Path) -> str:
    """
    Write the filtered subset to a JSON file and compute its checksum.
    
    Args:
        tasks: List of task dictionaries to write
        output_path: Path to write the JSON file
        
    Returns:
        SHA256 checksum of the written file
    """
    logger = setup_logging("filter")
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
    
    checksum = compute_sha256(output_path)
    logger.info(f"Wrote {len(tasks)} tasks to {output_path} with checksum {checksum}")
    return checksum


def main():
    """
    Main entry point for the filter task.
    
    This function:
    1. Loads the ResearchClawBench dataset
    2. Verifies the 'failure_mode' key exists (FR-006)
    3. Filters tasks where failure_mode == "experimental protocol mismatch"
    4. Checks if count >= 10 and if it's the dominant mode
    5. Writes the subset to data/processed/protocol_mismatch_subset.json
    6. Writes checksum to data/processed/protocol_mismatch_subset.json.sha256
    7. If edge case conditions are met, writes results/failure_mode_audit.csv
    """
    logger = setup_logging("filter")
    logger.info("Starting T008: Filter tasks by failure_mode")
    
    try:
        # Load dataset
        dataset = load_researchclawbench_data()
        
        # Analyze failure modes first to check conditions
        mode_counts = analyze_failure_modes(dataset)
        total_tasks = sum(mode_counts.values()) if mode_counts else len(dataset)
        
        # Check FR-006: failure_mode key must exist
        # This is already checked in filter_by_failure_mode, but we do a quick check here too
        if not any('failure_mode' in item.get('metadata', {}) for item in dataset):
            logger.error("FR-006 Violation: 'failure_mode' key missing entirely from dataset")
            sys.exit(1)
        
        # Filter tasks
        target_mode = "experimental protocol mismatch"
        filtered_tasks = filter_by_failure_mode(dataset, target_mode)
        filtered_count = len(filtered_tasks)
        
        # Determine dominant mode
        dominant_mode = max(mode_counts, key=mode_counts.get) if mode_counts else None
        dominant_count = mode_counts[dominant_mode] if dominant_mode else 0
        
        # Edge case handling:
        # If count < 10 OR dominant mode differs from target, write audit report
        should_audit = (filtered_count < 10) or (dominant_mode != target_mode)
        
        if should_audit:
            logger.warning(f"Edge case detected: filtered_count={filtered_count}, dominant_mode={dominant_mode}")
            audit_path = Path("results/failure_mode_audit.csv")
            write_failure_mode_audit(mode_counts, total_tasks, audit_path)
            logger.info("Wrote failure mode audit report due to edge case conditions")
        
        # Write the subset
        output_path = Path("data/processed/protocol_mismatch_subset.json")
        checksum = write_subset_json(filtered_tasks, output_path)
        
        # Write checksum file
        checksum_path = Path("data/processed/protocol_mismatch_subset.json.sha256")
        write_checksum(output_path, checksum_path)
        
        logger.info(f"T008 completed successfully. Output: {output_path}, Checksum: {checksum}")
        print(f"T008: Successfully filtered {filtered_count} tasks.")
        print(f"Output: {output_path}")
        print(f"Checksum: {checksum}")
        
        if should_audit:
            print(f"WARNING: Edge case detected. Audit report written to {Path('results/failure_mode_audit.csv')}")
        
        return 0
        
    except KeyError as e:
        logger.error(f"FR-006 Violation: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in T008: {e}")
        get_global_error_tracker().add_error("T008", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
