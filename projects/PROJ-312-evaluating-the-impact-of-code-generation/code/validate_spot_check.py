"""
Spot-check validation script for User Story 1.

Performs a stratified random sample (n=50) of non-AI-labeled PRs to estimate
the false-negative rate of the classification logic.

Stratification is based on:
1. Repository (repo_name)
2. PR size (number of files changed)

The script reads processed data from data/processed/, performs the sampling,
and outputs a validation report to data/spot_check/validation_report.csv.
"""

import csv
import json
import logging
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import get_logger

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "pr_data.csv"
SPOT_CHECK_OUTPUT_PATH = PROJECT_ROOT / "data" / "spot_check" / "validation_report.csv"
SAMPLE_SIZE = 50
RANDOM_SEED = 42

logger = get_logger(__name__)

def load_processed_data() -> List[Dict[str, Any]]:
    """Load the processed PR data from CSV."""
    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(f"Processed data not found at {PROCESSED_DATA_PATH}. "
                                "Please run fetch_data.py first.")

    logger.info(f"Loading processed data from {PROCESSED_DATA_PATH}")
    data = []
    with open(PROCESSED_DATA_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse turnaround_hours as float
            if row.get('turnaround_hours'):
                row['turnaround_hours'] = float(row['turnaround_hours'])
            # Parse files_changed as int
            if row.get('files_changed'):
                row['files_changed'] = int(row['files_changed'])
            data.append(row)
    logger.info(f"Loaded {len(data)} records.")
    return data

def stratify_data(data: List[Dict[str, Any]]) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    """
    Stratify data by repository and PR size category.

    PR size categories:
    - small: 1-5 files
    - medium: 6-20 files
    - large: > 20 files
    """
    strata = defaultdict(list)

    for pr in data:
        # Only consider non-AI labeled PRs for this spot check
        if pr.get('is_ai_labeled') == 'True' or pr.get('is_ai_labeled') is True:
            continue

        repo_name = pr.get('repo_name', 'unknown')
        files_changed = pr.get('files_changed', 0)

        if files_changed <= 5:
            size_category = 'small'
        elif files_changed <= 20:
            size_category = 'medium'
        else:
            size_category = 'large'

        key = (repo_name, size_category)
        strata[key].append(pr)

    logger.info(f"Stratified into {len(strata)} groups.")
    return dict(strata)

def perform_stratified_sampling(strata: Dict[Tuple[str, str], List[Dict[str, Any]]],
                                n: int) -> List[Dict[str, Any]]:
    """
    Perform stratified random sampling.
    Allocates sample size proportionally to stratum size, ensuring at least 1 per stratum if possible.
    """
    total_records = sum(len(items) for items in strata.values())
    if total_records < n:
        logger.warning(f"Total available records ({total_records}) is less than requested sample size ({n}). "
                       "Sampling all available records.")
        n = total_records

    sample = []
    random.seed(RANDOM_SEED)

    # Calculate proportional allocation
    strata_keys = list(strata.keys())
    strata_sizes = {k: len(v) for k, v in strata.items()}

    # Initial allocation based on proportion
    allocations = {}
    remaining_n = n

    # First pass: proportional allocation
    for k, size in strata_sizes.items():
        if size == 0:
            allocations[k] = 0
            continue
        prop = size / total_records
        alloc = int(prop * n)
        if alloc > size:
            alloc = size
        allocations[k] = alloc
        remaining_n -= alloc

    # Second pass: distribute remaining to largest strata
    sorted_strata = sorted(strata_sizes.items(), key=lambda x: x[1], reverse=True)
    for k, _ in sorted_strata:
        if remaining_n <= 0:
            break
        current_alloc = allocations[k]
        current_size = strata_sizes[k]
        if current_alloc < current_size:
            take = min(remaining_n, current_size - current_alloc)
            allocations[k] += take
            remaining_n -= take

    # Ensure minimum of 1 per stratum if possible and we have remaining
    if remaining_n > 0:
        for k, size in strata_sizes.items():
            if remaining_n <= 0:
                break
            if allocations[k] == 0 and size > 0:
                allocations[k] = 1
                remaining_n -= 1

    # Final sampling
    for k, count in allocations.items():
        if count > 0:
          pool = strata[k]
          # Shuffle to ensure randomness
          random.shuffle(pool)
          sample.extend(pool[:count])

    logger.info(f"Selected {len(sample)} samples for spot check.")
    return sample

def simulate_manual_review(pr: Dict[str, Any]) -> bool:
    """
    Simulate manual review to determine if the PR was actually AI-assisted.
    
    In a real scenario, this would involve a human reviewing the code.
    For this implementation, we use the existing classification logic
    with stricter rules to identify potential false negatives.
    
    A false negative occurs when:
    1. The PR was labeled as non-AI (is_ai_labeled = False)
    2. BUT the manual review (simulated here) finds AI indicators
    
    We simulate this by checking for keywords in commit messages that might have
    been missed or misclassified.
    """
    # In a real implementation, this would be a human review result.
    # For simulation purposes, we check for specific patterns that indicate
    # AI generation but might have been missed by the initial classifier.
    
    commit_messages = pr.get('commit_messages', [])
    labels = pr.get('labels', [])
    
    # Stricter AI indicators for false negative detection
    strict_ai_keywords = [
        'copilot', 'github copilot', 'ai generated', 'llm generated',
        'generated by', 'copilot suggested', 'copilot code',
        'ai-assisted', 'llm code', 'automated code'
    ]
    
    # Check commit messages
    for msg in commit_messages:
        msg_lower = msg.lower()
        for keyword in strict_ai_keywords:
            if keyword in msg_lower:
                return True # Likely AI, so this is a false negative if labeled non-AI
    
    # Check labels (more comprehensive set)
    strict_ai_labels = [
        'ai-generated', 'copilot-assisted', 'llm-code', 'ai-code',
        'generated-by-copilot', 'copilot-generated'
    ]
    
    for label in labels:
        if label in strict_ai_labels:
            return True # Likely AI, so this is a false negative if labeled non-AI
    
    return False # No strong evidence of AI, so likely correctly classified

def calculate_false_negative_rate(sample: List[Dict[str, Any]]) -> float:
    """
    Calculate the false-negative rate from the spot-check sample.
    
    False Negative Rate = (Number of misclassified AI PRs) / (Total sample size)
    """
    if not sample:
        return 0.0
    
    misclassified_count = 0
    for pr in sample:
        # If the PR is labeled as non-AI but our manual review says it's AI
        if pr.get('is_ai_labeled') == 'False' or pr.get('is_ai_labeled') is False:
            if simulate_manual_review(pr):
                misclassified_count += 1
    
    return misclassified_count / len(sample)

def save_validation_report(sample: List[Dict[str, Any]], false_negative_rate: float):
    """Save the spot-check results to a CSV file."""
    SPOT_CHECK_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving validation report to {SPOT_CHECK_OUTPUT_PATH}")
    
    with open(SPOT_CHECK_OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow([
            'pr_id', 'repo_name', 'is_ai_labeled', 'files_changed',
            'turnaround_hours', 'manual_review_result', 'is_false_negative'
        ])
        
        for pr in sample:
            manual_result = simulate_manual_review(pr)
            is_fn = (
                (pr.get('is_ai_labeled') == 'False' or pr.get('is_ai_labeled') is False)
                and manual_result
            )
            
            writer.writerow([
                pr.get('pr_id', ''),
                pr.get('repo_name', ''),
                pr.get('is_ai_labeled', 'False'),
                pr.get('files_changed', 0),
                pr.get('turnaround_hours', 0.0),
                'AI' if manual_result else 'Human',
                'Yes' if is_fn else 'No'
            ])
    
    # Save summary stats as well
    summary_path = SPOT_CHECK_OUTPUT_PATH.parent / 'validation_summary.json'
    summary_data = {
        'total_sample_size': len(sample),
        'false_negative_rate': false_negative_rate,
        'sample_timestamp': str(Path(__file__).parent.parent / 'state' / 'timestamp'), # Placeholder
        'stratification_criteria': ['repository', 'pr_size']
    }
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2)
    
    logger.info(f"Validation report saved. False-negative rate: {false_negative_rate:.2%}")

def main():
    """Main entry point for the spot-check validation."""
    try:
        # Load processed data
        data = load_processed_data()
        
        # Filter for non-AI labeled PRs (candidates for false negatives)
        non_ai_prs = [
            pr for pr in data
            if pr.get('is_ai_labeled') == 'False' or pr.get('is_ai_labeled') is False
        ]
        
        if not non_ai_prs:
            logger.warning("No non-AI labeled PRs found for spot check.")
            # Create empty report
            SPOT_CHECK_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(SPOT_CHECK_OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['pr_id', 'repo_name', 'is_ai_labeled', 'files_changed', 
                               'turnaround_hours', 'manual_review_result', 'is_false_negative'])
            return
        
        logger.info(f"Found {len(non_ai_prs)} non-AI labeled PRs for spot check.")
        
        # Stratify the data
        strata = stratify_data(non_ai_prs)
        
        if not strata:
            logger.error("No strata found for non-AI labeled PRs.")
            return
        
        # Perform stratified sampling
        sample = perform_stratified_sampling(strata, SAMPLE_SIZE)
        
        if len(sample) < SAMPLE_SIZE:
            logger.warning(f"Could only sample {len(sample)} PRs instead of {SAMPLE_SIZE}.")
        
        # Calculate false-negative rate
        fpr = calculate_false_negative_rate(sample)
        
        # Save results
        save_validation_report(sample, fpr)
        
        logger.info("Spot-check validation completed successfully.")
        
    except Exception as e:
        logger.error(f"Spot-check validation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
