import argparse
import os
import sys
import random
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Paths

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_filtered_tasks(input_path: str) -> List[Dict[str, Any]]:
    """Load the filtered tasks CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Filtered tasks file not found: {input_path}")
    
    tasks = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse the constraint list string if it exists
            constraint_list_str = row.get('progressive_constraints', '[]')
            try:
                # Handle string representation of list
                if constraint_list_str.startswith('[') and constraint_list_str.endswith(']'):
                    # Simple eval for list of strings, handling quotes
                    import ast
                    constraints = ast.literal_eval(constraint_list_str)
                else:
                    constraints = []
            except (ValueError, SyntaxError):
                logger.warning(f"Could not parse constraints for task {row.get('task_id')}: {constraint_list_str}")
                constraints = []
            
            tasks.append({
                'task_id': row.get('task_id', ''),
                'raw_prompt': row.get('raw_prompt', ''),
                'progressive_constraints': constraints,
                'constraint_count': int(row.get('constraint_count', 0))
            })
    return tasks

def bin_constraint(count: int) -> str:
    """Assign a bin label based on constraint count."""
    if count < 5:
        return "5" # Should not happen given filtering, but safe
    elif count == 5:
        return "5"
    elif count == 6:
        return "6"
    else:
        return "7+"

def select_random_sample_stratified(
    tasks: List[Dict[str, Any]], 
    sample_size: int, 
    seed: int
) -> List[Dict[str, Any]]:
    """Select a stratified random sample from tasks."""
    random.seed(seed)
    
    # Group tasks by bin
    bins: Dict[str, List[Dict[str, Any]]] = {"5": [], "6": [], "7+": []}
    for task in tasks:
        bin_label = bin_constraint(task['constraint_count'])
        bins[bin_label].append(task)
    
    # Calculate sample size per bin
    total_available = sum(len(b) for b in bins.values())
    if total_available == 0:
        logger.warning("No tasks available for sampling.")
        return []
    
    # Target sample size per bin (roughly equal)
    # If a bin has fewer than the target, take all available
    target_per_bin = sample_size / len(bins)
    
    selected = []
    for bin_label, bin_tasks in bins.items():
        count_to_take = min(len(bin_tasks), int(target_per_bin) + (1 if len(selected) < sample_size and sum(len(b) for b in bins.values()) > sample_size else 0))
        # Ensure we don't exceed total sample size if possible, but prioritize representation
        if len(bin_tasks) < count_to_take:
            count_to_take = len(bin_tasks)
        
        if count_to_take > 0:
            # Shuffle and take
            shuffled = bin_tasks.copy()
            random.shuffle(shuffled)
            selected.extend(shuffled[:count_to_take])
            logger.info(f"Bin '{bin_label}': took {count_to_take} / {len(bin_tasks)} available")
    
    # If we still need more (due to integer rounding or small bins), fill from remaining
    if len(selected) < sample_size:
        remaining = [t for t in tasks if t not in selected]
        random.shuffle(remaining)
        needed = sample_size - len(selected)
        selected.extend(remaining[:needed])
        logger.info(f"Filled remaining {needed} from global pool")
    
    return selected

def save_annotation_sample(tasks: List[Dict[str, Any]], output_path: str):
    """Save the selected sample to a CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['task_id', 'raw_prompt', 'constraint_list', 'constraint_count'])
        
        for task in tasks:
            # Format constraint list as a string for CSV
            constraint_str = str(task['progressive_constraints'])
            writer.writerow([
                task['task_id'],
                task['raw_prompt'],
                constraint_str,
                task['constraint_count']
            ])
    
    logger.info(f"Saved {len(tasks)} tasks to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Select a stratified sample for human annotation.')
    parser.add_argument('--input', required=True, help='Path to filtered tasks CSV (data/processed/filtered_tasks.csv)')
    parser.add_argument('--output', default='data/processed/annotation_sample.csv', help='Path to output annotation sample CSV')
    parser.add_argument('--sample-size', type=int, default=50, help='Target sample size (min 50 or all available)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    logger.info(f"Loading tasks from {args.input}...")
    try:
        tasks = load_filtered_tasks(args.input)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    logger.info(f"Loaded {len(tasks)} tasks.")
    
    if len(tasks) == 0:
        logger.error("No tasks found to sample.")
        sys.exit(1)
    
    # Ensure sample size is reasonable
    actual_sample_size = min(args.sample_size, len(tasks))
    if actual_sample_size < 50 and len(tasks) >= 50:
        logger.warning(f"Requested sample size {args.sample_size} is less than 50, but {len(tasks)} tasks are available. Using 50.")
        actual_sample_size = 50
    
    logger.info(f"Selecting stratified sample of size {actual_sample_size} (seed={args.seed})...")
    sample = select_random_sample_stratified(tasks, actual_sample_size, args.seed)
    
    logger.info(f"Saving sample to {args.output}...")
    save_annotation_sample(sample, args.output)
    
    logger.info("Annotation sample selection complete.")

if __name__ == '__main__':
    main()
