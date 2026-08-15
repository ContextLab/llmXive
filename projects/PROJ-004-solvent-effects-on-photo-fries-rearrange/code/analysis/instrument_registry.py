"""
Instrument Registry Module

This module defines and logs instrument configuration for the Photo-Fries
rearrangement kinetics pipeline. It ensures that the instrument model is
loaded from a configuration file, falling back to a generic vendor-agnostic
definition if the file is missing or incomplete. This satisfies the
requirement to avoid hard-coding specific hardware dependencies.
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_chemicals_path

# Logger setup
logger = logging.getLogger(__name__)

DEFAULT_INSTRUMENT_MODEL = "Generic Transient Absorption Spectrometer"
CONFIG_FILENAME = "instrument_config.yaml"

def load_instrument_config() -> Dict[str, Any]:
    """
    Loads instrument configuration from the YAML file.

    Returns:
        dict: A dictionary containing instrument details. If the file is missing
              or the 'model' key is absent, returns a default generic configuration.
    """
    config_path = get_chemicals_path() / CONFIG_FILENAME
    config = {
        "model": DEFAULT_INSTRUMENT_MODEL,
        "vendor": "Unknown",
        "serial_number": "N/A",
        "calibration_date": None,
        "detection_limit": None,
        "units": "OD",
        "temporal_resolution_ns": None,
        "wavelength_range_nm": None,
        "notes": "Loaded from default fallback configuration."
    }

    if not config_path.exists():
        logger.warning(
            f"Instrument config file not found at {config_path}. "
            f"Using default: {DEFAULT_INSTRUMENT_MODEL}"
        )
        return config

    try:
        import yaml
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)

        if not data or 'instrument' not in data:
            logger.warning(
                f"Instrument config at {config_path} is missing 'instrument' key. "
                f"Using default: {DEFAULT_INSTRUMENT_MODEL}"
            )
            return config

        instrument_data = data['instrument']

        # Extract model, enforcing the constraint
        model = instrument_data.get('model')
        if not model:
            logger.warning(
                f"Model key missing in {config_path}. "
                f"Defaulting to: {DEFAULT_INSTRUMENT_MODEL}"
            )
            config['model'] = DEFAULT_INSTRUMENT_MODEL
        else:
            config['model'] = model

        # Extract other optional fields
        config['vendor'] = instrument_data.get('vendor', config['vendor'])
        config['serial_number'] = instrument_data.get('serial_number', config['serial_number'])
        config['calibration_date'] = instrument_data.get('calibration_date')
        config['detection_limit'] = instrument_data.get('detection_limit')
        config['units'] = instrument_data.get('units', config['units'])
        config['temporal_resolution_ns'] = instrument_data.get('temporal_resolution_ns')
        config['wavelength_range_nm'] = instrument_data.get('wavelength_range_nm')
        config['notes'] = instrument_data.get('notes', config['notes'])

        logger.info(f"Instrument config loaded: {config['model']}")

    except Exception as e:
        logger.error(f"Error parsing instrument config at {config_path}: {e}")
        logger.warning(f"Reverting to default: {DEFAULT_INSTRUMENT_MODEL}")

    return config

def log_instrument_config(log_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Logs the current instrument configuration to a JSON file and returns it.

    Args:
        log_path: Optional path to write the log. If None, writes to
                  data/processed/instrument_log.json.

    Returns:
        dict: The instrument configuration used.
    """
    config = load_instrument_config()
    
    # Add runtime metadata
    config['logged_at'] = datetime.now(timezone.utc).isoformat()
    config['logged_by'] = "instrument_registry"

    if log_path is None:
        from config import get_processed_data_path
        log_path = get_processed_data_path() / "instrument_log.json"

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, 'w') as f:
        json.dump(config, f, indent=2)

    logger.info(f"Instrument configuration logged to {log_path}")
    return config

def get_instrument_model() -> str:
    """
    Convenience function to get just the instrument model string.
    
    Returns:
        str: The instrument model name.
    """
    config = load_instrument_config()
    return config['model']

def main():
    """
    CLI entry point to log instrument configuration.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Log instrument configuration")
    parser.add_argument(
        "--output", 
        type=str, 
        default=None, 
        help="Path to output log file (default: data/processed/instrument_log.json)"
    )
    args = parser.parse_args()

    log_path = Path(args.output) if args.output else None
    config = log_instrument_config(log_path)
    print(f"Logged instrument: {config['model']}")
    print(f"Output written to: {log_path or 'data/processed/instrument_log.json'}")

if __name__ == "__main__":
    main()