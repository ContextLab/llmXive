"""
T047c, T052: Instrument registry and precision lookup.
"""
import csv
import logging
import os
from pathlib import Path
from typing import Optional, Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REGISTRY_PATH = Path(__file__).parent.parent.parent / "data" / "raw" / "instrument_registry.csv"
DEFAULT_PRECISION = 10.0
FALLBACK_LOG = Path(__file__).parent.parent.parent / "data" / "raw" / "unmapped_instruments.log"

_registry: Dict[str, Dict] = {}

def reload_registry():
    global _registry
    _registry = {}
    if not REGISTRY_PATH.exists():
        logger.warning(f"Registry file not found: {REGISTRY_PATH}. Using defaults.")
        return

    with open(REGISTRY_PATH, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            model = row['instrument_model']
            precision = float(row['precision_celsius'])
            _registry[model] = {'manufacturer': row['manufacturer'], 'precision': precision}
    
    logger.info(f"Loaded {len(_registry)} instruments from registry.")

def get_precision(instrument_model: str) -> float:
    if not _registry:
        reload_registry()
    
    model = instrument_model.strip()
    if model in _registry:
        return _registry[model]['precision']
    
    # Fallback
    logger.warning(f"Instrument '{instrument_model}' not found in registry. Using default {DEFAULT_PRECISION}°C.")
    with open(FALLBACK_LOG, "a") as f:
        f.write(f"{instrument_model}\n")
    return DEFAULT_PRECISION

def get_registry_details() -> List[Dict]:
    if not _registry:
        reload_registry()
    return [{"model": k, **v} for k, v in _registry.items()]

def main():
    reload_registry()
    print(get_registry_details())

if __name__ == "__main__":
    main()
