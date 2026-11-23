"""
Utility module that proxies environment‑related configuration functions.

The original implementation caused import errors due to missing typing
imports. This lightweight wrapper re‑exports the corresponding functions
from ``config.py`` so that existing import statements (e.g. in
``data.preprocess``) continue to work without modification.
"""

from typing import Dict, Any, Tuple, Optional

# The real implementations live in ``config.py``. We import them lazily
# to avoid circular import issues.


def get_env_config() -> Dict[str, Any]:
    """Return the environment‑constraint dictionary."""
    from config import get_env_config as _get_env_config

    return _get_env_config()


def check_memory_limit(limit_gb: Optional[float] = None) -> Tuple[bool, float]:
    """
    Verify available RAM against a specified or configured limit.

    Returns:
        (is_sufficient, available_gb)
    """
    from config import check_memory_limit as _check_memory_limit

    return _check_memory_limit(limit_gb)


def set_runtime_cap(hours: Optional[float] = None) -> None:
    """
    Set a soft CPU‑time limit (SIGXCPU). This is only a warning mechanism.
    """
    from config import set_runtime_cap as _set_runtime_cap

    _set_runtime_cap(hours)