import csv
import logging
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
from .config_manager import load_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REGISTRY_PATH = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'instrument_registry.csv'
DEFAULT_PRECISION = 10.0  # ±10°C as per spec

_registry_cache: Optional[Dict[str, Dict[str, Any]]] = None

def reload_registry() -> Dict[str, Dict[str, Any]]:
    """
    Load or reload the instrument registry from CSV.
    Returns a dict keyed by instrument_model.
    """
    global _registry_cache
    _registry_cache = {}

    if not REGISTRY_PATH.exists():
        logger.warning(f"Registry file not found at {REGISTRY_PATH}. Using empty registry.")
        return _registry_cache

    try:
        with open(REGISTRY_PATH, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                model = row.get('instrument_model', '').strip()
                if model:
                    _registry_cache[model] = {
                        'manufacturer': row.get('manufacturer', 'Unknown'),
                        'precision_celsius': float(row.get('precision_celsius', DEFAULT_PRECISION))
                    }
        logger.info(f"Loaded {len(_registry_cache)} instruments from registry.")
    except Exception as e:
        logger.error(f"Error loading registry: {e}")
    
    return _registry_cache

def get_precision(instrument_model: str) -> Optional[float]:
    """
    Get the precision for a given instrument model.
    Returns the precision in Celsius, or None if not found (caller should handle default).
    """
    if _registry_cache is None:
        reload_registry()
    
    # Case-insensitive lookup
    model_lower = instrument_model.lower()
    for key, data in _registry_cache.items():
        if key.lower() == model_lower:
            return data['precision_celsius']
    
    return None

def get_registry_details(instrument_model: str) -> Optional[Dict[str, Any]]:
    """Get full details for an instrument model."""
    if _registry_cache is None:
        reload_registry()
    
    model_lower = instrument_model.lower()
    for key, data in _registry_cache.items():
        if key.lower() == model_lower:
            return data
    return None

def generate_missing_instrumentation_report(missing_models: List[str]) -> None:
    """Log a report of instruments that were not found in the registry."""
    if not missing_models:
        return
    
    logger.warning("Instruments not found in registry:")
    for model in set(missing_models):
        logger.warning(f"  - {model}")

def main():
    """Test the registry loading."""
    logger.info("Testing instrument registry...")
    reload_registry()
    
    test_models = ["TA Instruments Q500", "Mettler Toledo TGA/DSC 1", "Unknown Model"]
    for model in test_models:
        prec = get_precision(model)
        logger.info(f"Precision for '{model}': {prec if prec is not None else 'Not Found'}")

if __name__ == '__main__':
    main()
