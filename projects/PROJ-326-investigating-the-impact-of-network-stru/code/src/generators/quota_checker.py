"""
Quota checker for stratified sampling.
"""

from typing import Dict, Any


def check_quotas(current_counts: Dict[str, int], target_counts: Dict[str, int]) -> bool:
    """
    Check if all bin quotas are met.
    
    Args:
        current_counts: Current counts per bin.
        target_counts: Target counts per bin.
    
    Returns:
        True if all targets are met (current >= target), False otherwise.
    """
    for bin_id, target in target_counts.items():
        current = current_counts.get(bin_id, 0)
        if current < target:
            return False
    return True
