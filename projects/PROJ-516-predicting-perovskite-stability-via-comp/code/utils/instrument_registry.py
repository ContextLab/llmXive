"""
Instrument Registry for TGA precision lookup.
Implements T047c and T052.
"""
import csv
import logging
import os
from pathlib import Path
from typing import Optional, Dict, List

project_root = Path(__file__).parent.parent.parent
REGISTRY_PATH = project_root / "data" / "raw" / "instrument_registry.csv"
UNMAPPED_LOG_PATH = project_root / "data" / "raw" / "unmapped_instruments.log"

# Default precision if instrument not found
DEFAULT_PRECISION_CELSIUS = 10.0

logger = logging.getLogger(__name__)

# Global registry cache
_registry: Dict[str, Dict[str, any]] = {}
_loaded = False

def reload_registry():
    """
    Load the instrument registry from the CSV file.
    Schema: instrument_model, manufacturer, precision_celsius
    """
    global _registry, _loaded
    _registry = {}
    
    if not REGISTRY_PATH.exists():
        logger.warning(f"Registry file not found at {REGISTRY_PATH}. Using default precision for all.")
        _loaded = True
        return

    try:
        with open(REGISTRY_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                model = row.get('instrument_model', '').strip()
                if model:
                    _registry[model.lower()] = {
                        'manufacturer': row.get('manufacturer', 'Unknown'),
                        'precision_celsius': float(row.get('precision_celsius', DEFAULT_PRECISION_CELSIUS))
                    }
        _loaded = True
        logger.info(f"Loaded {len(_registry)} instrument models from registry.")
    except Exception as e:
        logger.error(f"Failed to load instrument registry: {e}")
        _loaded = False

def get_precision(instrument_model: Optional[str]) -> float:
    """
    Get the precision for a given instrument model.
    If not found, returns DEFAULT_PRECISION_CELSIUS and logs to unmapped log.
    """
    if not _loaded:
        reload_registry()

    if not instrument_model:
        # Log missing instrumentation
        _log_unmapped("Unknown")
        return DEFAULT_PRECISION_CELSIUS

    model_key = instrument_model.strip().lower()
    
    if model_key in _registry:
        return _registry[model_key]['precision_celsius']
    
    # Not found
    _log_unmapped(instrument_model)
    return DEFAULT_PRECISION_CELSIUS

def _log_unmapped(model_name: str):
    """
    Log unmapped instrument names to the specified log file.
    """
    try:
        with open(UNMAPPED_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f"{model_name}\n")
        logger.warning(f"Instrument '{model_name}' not found in registry. Using default precision {DEFAULT_PRECISION_CELSIUS}°C.")
    except Exception as e:
        logger.error(f"Failed to log unmapped instrument '{model_name}': {e}")

def get_registry_details() -> Dict[str, any]:
    """
    Return the full registry for debugging/inspection.
    """
    if not _loaded:
        reload_registry()
    return _registry

def main():
    """
    CLI entry point to test the registry.
    """
    reload_registry()
    test_models = ["TA Instruments Q500", "Mettler Toledo TGA/DSC 3+", "Unknown Model", None]
    for model in test_models:
        prec = get_precision(model)
        print(f"Model: {model} -> Precision: {prec}°C")

if __name__ == "__main__":
    main()
