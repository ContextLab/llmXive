"""
T019a: Generate the experiment manifest.

This script creates a stratified sample of 100 task IDs from the annotated failures.
The sample is balanced by failure type (Syntactic, Logical, Semantic, etc.).

Output: data/derived/experiment_manifest.csv
"""
import json
import csv
import sys
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

from utils.logging import get_logger, log_stage_start, log_stage_end

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ANNOTATED_FAILURES_PATH = PROJECT_ROOT / "data" / "derived" / "failure_cases.json"
MANIFEST_PATH = PROJECT_ROOT / "data" / "derived" / "experiment_manifest.csv"

logger = get_logger(__name__)

def load_annotated_failures(path: Path) -> Dict[str, Dict[str, Any]]:
    """Load the annotated failure cases JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Annotated failures not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Assume data is a dict mapping task_id to failure_case
    return data

def stratified_sample(
    failures: Dict[str, Dict[str, Any]],
    target_size: int = 100
) -> List[Dict[str, Any]]:
    """
    Create a stratified sample of task IDs, balanced by failure_type.
    
    Returns a list of dicts: [{"task_id": "...", "failure_type": "..."}, ...]
    """
    # Group by failure type
    by_type: Dict[str, List[str]] = defaultdict(list)
    for task_id, case in failures.items():
        failure_type = case.get("failure_type", "Unknown")
        by_type[failure_type].append(task_id)
    
    logger.info(f"Found {len(by_type)} failure types: {list(by_type.keys())}")
    
    # Calculate sample size per type
    total_items = len(failures)
    if total_items == 0:
        logger.warning("No failure cases found for stratification.")
        return []
    
    # Simple proportional stratification
    sample_per_type = {}
    remaining = target_size
    
    types = list(by_type.keys())
    # Sort types by count descending to handle rounding better
    types.sort(key=lambda t: len(by_type[t]), reverse=True)
    
    for i, f_type in enumerate(types):
        count = len(by_type[f_type])
        proportion = count / total_items
        sample_count = int(round(proportion * target_size))
        
        # Ensure at least 1 if there are items and we still have budget
        if sample_count == 0 and count > 0 and remaining > 0:
            sample_count = 1
        
        if sample_count > count:
            sample_count = count
        
        sample_per_type[f_type] = min(sample_count, remaining)
        remaining -= sample_count
    
    # Adjust if we have leftover budget (due to rounding)
    if remaining > 0:
        # Add to the largest group
        if types:
            largest_type = types[0]
            max_addable = len(by_type[largest_type]) - sample_per_type.get(largest_type, 0)
            add = min(remaining, max_addable)
            sample_per_type[largest_type] = sample_per_type.get(largest_type, 0) + add
            remaining -= add
    
    # Sample
    sample = []
    for f_type, count in sample_per_type.items():
        tasks = by_type[f_type]
        sampled_tasks = random.sample(tasks, min(count, len(tasks)))
        for t_id in sampled_tasks:
            sample.append({
                "task_id": t_id,
                "failure_type": f_type
            })
    
    logger.info(f"Generated stratified sample of {len(sample)} tasks.")
    return sample

def write_manifest(sample: List[Dict[str, Any]], output_path: Path) -> None:
    """Write the manifest to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "failure_type"])
        writer.writeheader()
        writer.writerows(sample)
    
    logger.info(f"Manifest written to {output_path}")

def main():
    """Entry point."""
    log_stage_start(logger, "T019a: Generate Manifest")
    
    try:
        failures = load_annotated_failures(ANNOTATED_FAILURES_PATH)
        sample = stratified_sample(failures, target_size=100)
        write_manifest(sample, MANIFEST_PATH)
    except Exception as e:
        logger.error(f"Failed to generate manifest: {e}", exc_info=True)
        sys.exit(1)
    finally:
        log_stage_end(logger, "T019a: Generate Manifest")

if __name__ == "__main__":
    main()
