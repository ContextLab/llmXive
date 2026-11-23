import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def check_quota_status(current_counts: Dict[str, int], target_counts: Dict[str, int], tolerance: float = 0.0) -> Dict[str, bool]:
    """
    Check if quotas for each bin are met.
    Returns a dictionary of bin -> status (True if quota met).
    """
    status = {}
    for bin_label, target in target_counts.items():
        current = current_counts.get(bin_label, 0)
        # Allow tolerance
        required = target * (1 - tolerance)
        status[bin_label] = current >= required
        if not status[bin_label]:
            logger.debug(f"Quota not met for {bin_label}: {current}/{target}")
        else:
            logger.debug(f"Quota met for {bin_label}: {current}/{target}")
    return status
