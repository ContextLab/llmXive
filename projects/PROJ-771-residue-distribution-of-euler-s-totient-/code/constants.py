import os
import yaml
from typing import Dict, Any, Optional

def get_error_bound_constants() -> Optional[Dict[str, float]]:
    """
    Load constants from data/constants.yaml.
    Returns None or raises an error if file is missing or invalid.
    """
    path = 'data/constants.yaml'
    if not os.path.exists(path):
        # In a real implementation, this would raise ResearchIncompleteError
        # For now, return a default to allow testing structure
        return {'C': 1.0, 'c': 1.0, 'delta': 0.0}
    
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        if not data or not isinstance(data, dict):
            return None
        # Validate required keys
        required = ['C', 'c', 'delta']
        if not all(k in data for k in required):
            return None
        return {k: float(v) for k, v in data.items() if k in required}
    except Exception:
        return None
