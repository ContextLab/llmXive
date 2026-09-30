import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def check_trigger(quota_status: Dict[str, bool], target_counts: Dict[str, int]) -> Optional[str]:
    """
    Check if generation should be triggered for a specific bin.
    Returns the bin label that needs generation, or None if all quotas are met.
    """
    for bin_label, met in quota_status.items():
        if not met:
            logger.info(f"Triggering generation for {bin_label} (quota not met)")
            return bin_label

    logger.info("All quotas met. No generation triggered.")
    return None
