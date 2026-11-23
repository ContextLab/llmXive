"""
Hard floor enforcer for batch size to prevent OOM.
"""
import logging

logger = logging.getLogger(__name__)

class HardFloorEnforcer:
    """
    Enforces a hard limit of batch_size=1 as a fallback.
    """
    def __init__(self, min_batch_size: int = 1):
        self.min_batch_size = min_batch_size

    def enforce(self, current_batch_size: int, ram_usage_gb: float, hard_limit_gb: float = 7.0) -> int:
        """
        Returns the effective batch size, enforcing the hard floor if necessary.
        """
        if current_batch_size < self.min_batch_size:
            logger.warning(f"Requested batch size {current_batch_size} is below minimum. Setting to {self.min_batch_size}.")
            return self.min_batch_size

        if ram_usage_gb >= hard_limit_gb:
            logger.critical(f"RAM usage ({ram_usage_gb:.2f} GB) at or above hard limit ({hard_limit_gb} GB). Enforcing batch_size=1.")
            return 1

        return current_batch_size
