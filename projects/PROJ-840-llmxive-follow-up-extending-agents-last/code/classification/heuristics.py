"""
Normalization Protocol Module.

Implements deterministic normalization of state data:
- Float tolerance: loaded from config
- Timestamp/ID stripping: loaded from config
- Reference canonicalization: loaded from config
"""
from typing import Any, Dict, Union
import re
from pathlib import Path
import yaml
import math

# Default values as fallback, but primary source is config
DEFAULT_FLOAT_TOLERANCE = 1e-6
DEFAULT_TIMESTAMP_PLACEHOLDER = "[TIMESTAMP]"
DEFAULT_ID_PLACEHOLDER = "[ID]"
DEFAULT_REF_PLACEHOLDER = "[REF]"

# Default patterns
DEFAULT_TIMESTAMP_PATTERN = r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b"
DEFAULT_UUID_PATTERN = r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
DEFAULT_REFERENCE_PATTERN = r"\b0x[0-9a-fA-F]+\b"

# Cache for loaded config to avoid repeated file I/O
_config_cache = None

def _load_normalization_config() -> Dict[str, Any]:
    """
    Load normalization configuration from config file.
    Falls back to defaults if config file is missing or invalid.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config_path = Path(__file__).parent.parent / "utils" / "config_schema.yaml"
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config and 'normalization' in config:
                    _config_cache = config['normalization']
                    return _config_cache
        # Fallback to defaults
        _config_cache = {
            'float_tolerance': DEFAULT_FLOAT_TOLERANCE,
            'timestamp_placeholder': DEFAULT_TIMESTAMP_PLACEHOLDER,
            'id_placeholder': DEFAULT_ID_PLACEHOLDER,
            'ref_placeholder': DEFAULT_REF_PLACEHOLDER,
            'timestamp_regex': DEFAULT_TIMESTAMP_PATTERN,
            'uuid_regex': DEFAULT_UUID_PATTERN,
            'reference_regex': DEFAULT_REFERENCE_PATTERN
        }
        return _config_cache
    except Exception:
        # On any error, use defaults
        _config_cache = {
            'float_tolerance': DEFAULT_FLOAT_TOLERANCE,
            'timestamp_placeholder': DEFAULT_TIMESTAMP_PLACEHOLDER,
            'id_placeholder': DEFAULT_ID_PLACEHOLDER,
            'ref_placeholder': DEFAULT_REF_PLACEHOLDER,
            'timestamp_regex': DEFAULT_TIMESTAMP_PATTERN,
            'uuid_regex': DEFAULT_UUID_PATTERN,
            'reference_regex': DEFAULT_REFERENCE_PATTERN
        }
        return _config_cache

def _load_patterns() -> Dict[str, re.Pattern]:
    """
    Load regex patterns from config or use defaults.
    Returns compiled regex patterns.
    """
    config = _load_normalization_config()
    
    # Get patterns from config or use defaults
    timestamp_regex = config.get('timestamp_regex', DEFAULT_TIMESTAMP_PATTERN)
    uuid_regex = config.get('uuid_regex', DEFAULT_UUID_PATTERN)
    reference_regex = config.get('reference_regex', DEFAULT_REFERENCE_PATTERN)
    
    return {
        'timestamp': re.compile(timestamp_regex),
        'uuid': re.compile(uuid_regex, re.IGNORECASE),
        'reference': re.compile(reference_regex)
    }

def normalize_state(state: Union[Dict, str, float, int, None]) -> Any:
    """
    Recursively normalizes a state object.
    
    - Floats are rounded to N decimal places based on config (default 1e-6).
    - Timestamps and UUIDs are replaced with canonical placeholders from config.
    - Memory references are stripped/canonicalized using config placeholders.
    """
    config = _load_normalization_config()
    patterns = _load_patterns()
    
    float_tolerance = config['float_tolerance']
    timestamp_placeholder = config['timestamp_placeholder']
    id_placeholder = config['id_placeholder']
    ref_placeholder = config['ref_placeholder']
    
    if state is None:
        return None
    
    if isinstance(state, float):
        # Round based on tolerance (convert tolerance to decimal places)
        if float_tolerance > 0:
            decimal_places = max(0, int(-math.log10(float_tolerance)))
            return round(state, decimal_places)
        return state
    
    if isinstance(state, int):
        return state
    
    if isinstance(state, str):
        # Strip timestamps
        normalized = patterns['timestamp'].sub(timestamp_placeholder, state)
        # Strip UUIDs
        normalized = patterns['uuid'].sub(id_placeholder, normalized)
        # Strip memory references
        normalized = patterns['reference'].sub(ref_placeholder, normalized)
        return normalized
    
    if isinstance(state, dict):
        return {k: normalize_state(v) for k, v in state.items()}
    
    if isinstance(state, (list, tuple)):
        return [normalize_state(item) for item in state]
    
    return state
