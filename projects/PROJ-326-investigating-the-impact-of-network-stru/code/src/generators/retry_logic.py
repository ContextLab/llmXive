"""
Retry logic for disconnected networks.

References T051 as the primary source of truth.
"""

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def retry_on_disconnect(func: Callable, max_retries: int = 10, *args, **kwargs) -> Optional[Any]:
    """
    Decorator or wrapper to retry a function if it returns a disconnected graph.
    
    Note: T051 implements the actual retry loop in base.py. This module
    provides utility functions if needed elsewhere.
    """
    for attempt in range(max_retries):
        result = func(*args, **kwargs)
        # Check connectivity logic would go here if result is a graph
        # For now, this is a placeholder as T051 handles the logic in base.py
        return result
    return None
