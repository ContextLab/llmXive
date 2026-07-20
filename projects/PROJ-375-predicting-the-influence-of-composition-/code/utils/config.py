import os
from typing import Optional

def get_env_var(key: str, default: Optional[str] = None) -> str:
    """
    Retrieves an environment variable.
    
    Args:
        key: The environment variable name.
        default: The default value if the variable is not set.
    
    Returns:
        The value of the environment variable or the default.
    """
    val = os.environ.get(key)
    if val is None:
        if default is None:
            # Fail loudly if required and missing (optional for this specific function usage)
            # But for T017, we need a fallback for VIF_THRESHOLD
            return default
        return default
    return val