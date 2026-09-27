"""Instrument Registry Module.

Defines and logs instrument configuration, loading model information from
configuration files to ensure vendor agnosticism.
"""
import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from utils.logging import setup_logging, log_operation
from config import get_chemicals_path


def load_instrument_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load instrument configuration from YAML or use defaults.

    Args:
        config_path: Optional path to instrument_config.yaml. If None,
            defaults to data/chemicals/instrument_config.yaml.

    Returns:
        Dictionary containing instrument configuration.
    """
    if config_path is None:
        config_path = os.path.join(get_chemicals_path(), "instrument_config.yaml")

    defaults = {
        "model": "Generic Transient Absorption Spectrometer",
        "detector_type": "Photomultiplier Tube",
        "detection_limit_absorbance": 1e-5,
        "wavelength_range_nm": [200, 800],
        "temporal_resolution_ns": [1, 1000],
        "calibration_standards": ["NIST Standard Reference"],
        "last_calibration_date": datetime.now(timezone.utc).isoformat()
    }

    if os.path.exists(config_path):
        try:
            import yaml
            with open(config_path, 'r') as f:
                loaded = yaml.safe_load(f)
                return {**defaults, **loaded}
        except Exception as e:
            logging.warning(f"Failed to load instrument config from {config_path}: {e}. Using defaults.")
    else:
        logging.info(f"Instrument config not found at {config_path}. Using defaults.")

    return defaults


def log_instrument_config(config: Dict[str, Any], log_path: Optional[str] = None) -> str:
    """Log the instrument configuration to a JSON file.

    Args:
        config: Instrument configuration dictionary.
        log_path: Optional path for the log file.

    Returns:
        Path to the written log file.
    """
    if log_path is None:
        log_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "..",
            "data",
            "processed",
            "instrument_registry.json"
        )

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "instrument": config
    }

    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    with open(log_path, 'w') as f:
        json.dump(log_entry, f, indent=2, default=str)

    logging.info(f"Instrument registry logged to {log_path}")
    return log_path


def get_instrument_model(config: Optional[Dict[str, Any]] = None) -> str:
    """Get the instrument model name.

    Args:
        config: Optional instrument configuration. If None, loads from file.

    Returns:
        The instrument model name.
    """
    if config is None:
        config = load_instrument_config()
    return config.get("model", "Generic Transient Absorption Spectrometer")


def main() -> None:
    """CLI entry point for logging instrument configuration."""
    parser = argparse.ArgumentParser(
        description="Log instrument configuration to registry."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to instrument configuration YAML."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path for output log file."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level."
    )

    args = parser.parse_args()

    setup_logging(level=args.log_level)

    try:
        config = load_instrument_config(args.config)
        log_path = log_instrument_config(config, args.output)
        logging.info(f"Instrument model: {get_instrument_model(config)}")
        logging.info(f"Registry logged to {log_path}")
    except Exception as e:
        logging.error(f"Error logging instrument configuration: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    main()