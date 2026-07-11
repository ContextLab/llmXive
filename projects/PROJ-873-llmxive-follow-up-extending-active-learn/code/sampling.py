"""
Sampling module for T013b: Stratified random sampling of wasted calls for validation.

This module implements the logic to:
1. Filter logged pairwise comparisons for similarity > 0.95.
2. Calculate the dynamic sample size using the formula from T013c.
3. Select a stratified random sample for LLM consensus validation.
"""
import json
import os
import random
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# Import from project modules as per API surface
from metrics import calculate_dynamic_sample_size
from logging_config import get_comparison_log_path
from config import get_config


def load_comparison_logs() -> List[Dict[str, Any]]:
    """
    Load all pairwise comparison logs from the log file.
    
    Returns:
        List of comparison log entries (dicts).
    """
    log_path = get_comparison_log_path()
    if not os.path.exists(log_path):
        return []
    
    comparisons = []
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                comparisons.append(entry)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue
    return comparisons


def filter_wasted_calls(comparisons: List[Dict[str, Any]], threshold: float = 0.95) -> List[Dict[str, Any]]:
    """
    Filter comparisons to find those flagged as 'wasted' (similarity > threshold).
    
    Args:
        comparisons: List of all comparison logs.
        threshold: The similarity threshold (default 0.95).
        
    Returns:
        List of comparisons where cosine_similarity > threshold.
    """
    wasted = []
    for comp in comparisons:
        # The metric logic uses 'cosine_similarity' key in logs typically
        sim = comp.get('cosine_similarity', comp.get('similarity', 0.0))
        if sim > threshold:
            wasted.append(comp)
    return wasted


def stratify_by_query(wasted_calls: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group wasted calls by their query ID for stratified sampling.
    
    Args:
        wasted_calls: List of wasted call entries.
        
    Returns:
        Dictionary mapping query_id -> list of wasted call entries.
    """
    strata = defaultdict(list)
    for call in wasted_calls:
        # Assuming 'query_id' or 'qid' is present in the log entry
        qid = call.get('query_id') or call.get('qid') or 'unknown'
        strata[qid].append(call)
    return dict(strata)


def select_stratified_sample(
    wasted_calls: List[Dict[str, Any]], 
    target_sample_size: int
) -> List[Dict[str, Any]]:
    """
    Select a stratified random sample of wasted calls.
    
    The sample is drawn proportionally from each query's wasted calls to ensure
    coverage across different queries, while respecting the total target size.
    
    Args:
        wasted_calls: List of all wasted calls.
        target_sample_size: The total number of samples to select.
        
    Returns:
        List of selected sample entries.
    """
    if not wasted_calls:
        return []
    
    if target_sample_size >= len(wasted_calls):
        return wasted_calls[:]  # Return all if target is larger than population
    
    # Stratify by query
    strata = stratify_by_query(wasted_calls)
    
    if not strata:
        return []
    
    # Calculate proportional allocation
    sample_per_stratum = {}
    total_wasted = len(wasted_calls)
    remaining_samples = target_sample_size
    remaining_strata = len(strata)
    
    # Simple proportional allocation: floor(size * (stratum_size / total))
    # Then distribute remainder
    allocations = {}
    for qid, items in strata.items():
        count = len(items)
        alloc = int((count / total_wasted) * target_sample_size)
        allocations[qid] = alloc
        remaining_samples -= alloc
        remaining_strata -= 1
    
    # Distribute remainder randomly to strata with available items
    strata_keys = list(strata.keys())
    random.shuffle(strata_keys)
    
    for qid in strata_keys:
        if remaining_samples <= 0:
            break
        current_alloc = allocations[qid]
        max_available = len(strata[qid])
        if current_alloc < max_available:
            allocations[qid] += 1
            remaining_samples -= 1
    
    # Select items
    selected_samples = []
    for qid, alloc_count in allocations.items():
        items = strata[qid]
        if alloc_count > len(items):
            # Fallback if allocation exceeds available (shouldn't happen with logic above)
            selected_samples.extend(items)
        else:
            selected_samples.extend(random.sample(items, alloc_count))
    
    return selected_samples


def run_sampling_pipeline(output_path: str = "data/validation_sample.json") -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    Execute the full sampling pipeline for T013b.
    
    1. Load logs.
    2. Filter for wasted calls.
    3. Calculate dynamic sample size.
    4. Select stratified sample.
    5. Save to disk.
    
    Args:
        output_path: Path to save the JSON sample file.
        
    Returns:
        Tuple of (total_wasted_count, sample_size, list_of_samples)
    """
    config = get_config()
    
    # 1. Load logs
    comparisons = load_comparison_logs()
    if not comparisons:
        print("No comparison logs found. Cannot perform sampling.")
        return 0, 0, []
    
    # 2. Filter wasted calls (similarity > 0.95)
    wasted_calls = filter_wasted_calls(comparisons, threshold=0.95)
    total_wasted = len(wasted_calls)
    
    if total_wasted == 0:
        print("No wasted calls found (similarity > 0.95).")
        return 0, 0, []
    
    # 3. Calculate dynamic sample size
    # T013c formula: min([deferred] of total flagged, upper bound)
    # We use total_wasted as the 'deferred' count here.
    # We need a reasonable upper bound. Let's use a config value or default to 100.
    upper_bound = config.get('validation_sample_upper_bound', 100)
    sample_size = calculate_dynamic_sample_size(total_wasted, upper_bound)
    
    # 4. Select stratified sample
    sample = select_stratified_sample(wasted_calls, sample_size)
    
    # 5. Save to disk
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample, f, indent=2, default=str)
    
    print(f"Sampling complete: {len(sample)} items selected from {total_wasted} wasted calls.")
    print(f"Output saved to: {output_path}")
    
    return total_wasted, sample_size, sample


if __name__ == "__main__":
    # Default output path as per project conventions
    run_sampling_pipeline("data/validation_sample.json")
