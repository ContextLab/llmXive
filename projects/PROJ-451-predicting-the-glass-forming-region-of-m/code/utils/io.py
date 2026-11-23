import csv
import json
import os
import random
from typing import Any, Dict, List, Optional, Union
import logging
from pathlib import Path

from .config import get_processed_data_path, get_raw_data_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_csv(filepath: str) -> List[Dict[str, Any]]:
    """Load a CSV file into a list of dictionaries."""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """Save a list of dictionaries to a CSV file."""
    if not data:
        logger.warning(f"No data to save to {filepath}")
        return
    fieldnames = data[0].keys()
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_json(filepath: str) -> Any:
    """Load a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data: Any, filepath: str) -> None:
    """Save data to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def filter_by_phase_label(data: List[Dict[str, Any]], valid_labels: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Filter compositions by phase label (amorphous/crystalline)."""
    if valid_labels is None:
        valid_labels = ['amorphous', 'crystalline']
    return [row for row in data if row.get('phase', '').lower() in valid_labels]

def load_and_filter_dataset(input_path: str, output_path: str, valid_labels: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Load dataset, filter by phase, and save."""
    data = load_csv(input_path)
    filtered = filter_by_phase_label(data, valid_labels)
    save_csv(filtered, output_path)
    logger.info(f"Filtered dataset: {len(data)} -> {len(filtered)} rows")
    return filtered

def cap_dataset_stratified(
    data: List[Dict[str, Any]],
    target_size: int,
    stratify_col: str = 'alloy_system',
    source_col: str = 'source',
    primary_source: str = 'Science Advances',
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Cap the dataset to `target_size` using stratified random sampling by `stratify_col`.
    
    Priority Logic (FR-010):
    1. Identify records from the primary source (Science Advances).
    2. Calculate the max allowable count per alloy system based on the primary source distribution.
    3. If the primary source count for a system exceeds the system's proportional share, 
       cap it to that share.
    4. Fill remaining slots with secondary source (Materials Project) records if needed, 
       maintaining the stratification ratio as closely as possible.
    
    Args:
        data: List of row dictionaries.
        target_size: Maximum number of rows (e.g., 10,000).
        stratify_col: Column name to stratify by (e.g., 'alloy_system').
        source_col: Column name indicating the data source.
        primary_source: The value in `source_col` considered primary.
        seed: Random seed for reproducibility.
    
    Returns:
        A new list of dictionaries, capped and stratified.
    """
    if not data:
        logger.warning("Input data is empty.")
        return []

    random.seed(seed)
    
    # Separate by source
    primary_rows = [r for r in data if r.get(source_col) == primary_source]
    secondary_rows = [r for r in data if r.get(source_col) != primary_source]

    # Group by alloy_system
    from collections import defaultdict
    primary_groups: Dict[str, List[Dict]] = defaultdict(list)
    secondary_groups: Dict[str, List[Dict]] = defaultdict(list)

    for r in primary_rows:
        key = r.get(stratify_col, 'Unknown')
        primary_groups[key].append(r)
    
    for r in secondary_rows:
        key = r.get(stratify_col, 'Unknown')
        secondary_groups[key].append(r)

    # Calculate total counts per system
    all_systems = set(primary_groups.keys()) | set(secondary_groups.keys())
    total_per_system = {sys: len(primary_groups[sys]) + len(secondary_groups[sys]) for sys in all_systems}
    total_all = len(data)

    if total_all == 0:
        return []

    # Determine target counts per system based on stratified proportion
    # We want to preserve the ratio of each system in the final dataset
    target_counts = {}
    for sys in all_systems:
        proportion = total_per_system[sys] / total_all
        count = int(round(target_size * proportion))
        # Ensure at least 1 if the system exists, unless target is 0
        if count == 0 and total_per_system[sys] > 0:
            count = 1
        target_counts[sys] = count

    # Adjust for rounding errors to hit target_size exactly
    current_sum = sum(target_counts.values())
    diff = target_size - current_sum
    if diff != 0:
        # Sort systems by remaining fractional part or just by size to add/remove
        # Simple approach: add/subtract from largest groups
        sorted_sys = sorted(all_systems, key=lambda s: total_per_system[s], reverse=True)
        for i in range(abs(diff)):
            sys = sorted_sys[i % len(sorted_sys)]
            if diff > 0:
                target_counts[sys] += 1
            else:
                if target_counts[sys] > 0:
                    target_counts[sys] -= 1

    final_data = []
    
    # 1. Process Primary Source first
    for sys in all_systems:
        available_primary = primary_groups[sys]
        needed = target_counts[sys]
        
        # Take all available primary, up to needed
        # If we have more primary than needed, we MUST cap (FR-010 says retain primary first, 
        # but we are capped by total size. If primary > needed, we take 'needed' random ones).
        # Actually, the constraint "Retain records from primary source first" usually means 
        # "Don't drop primary to keep secondary". 
        # So: Take min(available_primary, needed).
        
        take_count = min(len(available_primary), needed)
        if take_count > 0:
            # Shuffle to ensure randomness within the primary set
            random.shuffle(available_primary)
            final_data.extend(available_primary[:take_count])
            needed -= take_count

    # 2. Fill remaining slots with Secondary Source
    for sys in all_systems:
        if needed <= 0:
            # Recalculate needed globally? No, we iterate per system.
            # If we already met the target for this system, skip.
            # But we might have over-allocated in step 1? No, we capped at 'needed' per system.
            # Wait, if primary > needed, we took 'needed'. The system quota is full.
            # If primary < needed, we took all primary, and 'needed' is reduced by what we took.
            # We need to track the remaining quota for this specific system.
            pass
        
        # Recalculate remaining quota for this system
        # We took min(len(primary), original_target). 
        # Remaining needed = original_target - taken
        # But we didn't store original_target per system in the loop easily.
        # Let's re-derive:
        original_target = target_counts[sys]
        taken_primary = min(len(primary_groups[sys]), original_target)
        remaining_quota = original_target - taken_primary
        
        if remaining_quota > 0:
            available_secondary = secondary_groups[sys]
            take_count = min(len(available_secondary), remaining_quota)
            if take_count > 0:
                random.shuffle(available_secondary)
                final_data.extend(available_secondary[:take_count])

    logger.info(f"Capped dataset: {len(data)} -> {len(final_data)} rows (Target: {target_size})")
    return final_data
