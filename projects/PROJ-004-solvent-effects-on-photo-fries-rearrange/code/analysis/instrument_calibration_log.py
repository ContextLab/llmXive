"""Instrument Calibration Log Generation.

Generates a machine-readable calibration log for the transient absorption spectrometer.
This task fulfills the requirement to explicitly document the instrument model,
detector type, detection limit, and calibration certificate details.

Dependencies:
    - T035: Instrument Registry (provides base config)
    - T045: Calibration Protocol (generates certificates)
    - T045b: Calibration Verification (ensures certificate validity)
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Import shared utilities and config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logging import setup_logging
from config import get_chemicals_path, get_processed_data_path

# Constants
INSTRUMENT_CONFIG_PATH = "data/chemicals/instrument_config.yaml"
CALIBRATION_CERT_DIR = "data/processed/calibration_certificates"
OUTPUT_PATH = "data/processed/instrument_calibration_log.json"

logger = logging.getLogger(__name__)


def load_instrument_config() -> Dict[str, Any]:
    """Load instrument configuration from the YAML file.

    Returns:
        Dict containing instrument_model, detector_type, detection_limit_absorbance.

    Raises:
        FileNotFoundError: If the config file is missing.
        KeyError: If required fields are missing from the config.
    """
    config_path = get_chemicals_path() / INSTRUMENT_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"Instrument config missing at {config_path}")

    try:
        import yaml
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except ImportError:
        raise ImportError("PyYAML is required to load instrument config.")

    required_fields = ["instrument_model", "detector_type", "detection_limit_absorbance"]
    missing = [f for f in required_fields if f not in config]
    if missing:
        raise KeyError(f"Missing required fields in instrument config: {missing}")

    return config


def find_latest_certificate(cert_dir: Path) -> Optional[Path]:
    """Find the most recent valid calibration certificate in the directory.

    Args:
        cert_dir: Path to the directory containing certificate JSON files.

    Returns:
        Path to the latest certificate, or None if none found.
    """
    if not cert_dir.exists():
        logger.warning(f"Calibration certificate directory not found: {cert_dir}")
        return None

    certs = list(cert_dir.glob("*_cert.json"))
    if not certs:
        logger.warning("No calibration certificates found in directory.")
        return None

    # Sort by modification time (newest first)
    certs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return certs[0]


def validate_certificate(cert_path: Path) -> Dict[str, Any]:
    """Validate and load a calibration certificate.

    Args:
        cert_path: Path to the certificate JSON file.

    Returns:
        Dict containing certificate data.

    Raises:
        ValueError: If the certificate is invalid or missing required fields.
    """
    try:
        with open(cert_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in certificate {cert_path}: {e}")

    required = ["calibration_date", "hash", "standards_used"]
    missing = [f for f in required if f not in data]
    if missing:
        raise ValueError(f"Certificate {cert_path} missing fields: {missing}")

    return data


def generate_calibration_log(instrument_config: Dict[str, Any], cert_data: Dict[str, Any], cert_path: Path) -> Dict[str, Any]:
    """Construct the calibration log entry.

    Args:
        instrument_config: The loaded instrument configuration.
        cert_data: The loaded and validated certificate data.
        cert_path: The path to the certificate file.

    Returns:
        Dict representing the full calibration log.
    """
    return {
        "instrument_model": instrument_config["instrument_model"],
        "detector_type": instrument_config["detector_type"],
        "detection_limit_absorbance": instrument_config["detection_limit_absorbance"],
        "calibration_date": cert_data["calibration_date"],
        "calibration_certificate_path": str(cert_path),
        "certificate_hash": cert_data["hash"],
        "standards_used": cert_data["standards_used"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "valid"
    }


def write_calibration_log(log_data: Dict[str, Any], output_path: Path) -> None:
    """Write the calibration log to a JSON file.

    Args:
        log_data: The calibration log dictionary.
        output_path: The path to write the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Calibration log written to {output_path}")


def run_calibration_log_generation() -> Dict[str, Any]:
    """Main execution function to generate the calibration log.

    Returns:
        The generated calibration log dictionary.

    Raises:
        FileNotFoundError: If instrument config or certificates are missing.
        ValueError: If certificate validation fails.
    """
    # 1. Load Instrument Config
    logger.info("Loading instrument configuration...")
    config = load_instrument_config()

    # 2. Locate Latest Certificate
    logger.info("Searching for latest calibration certificate...")
    cert_dir = get_processed_data_path() / CALIBRATION_CERT_DIR
    latest_cert = find_latest_certificate(cert_dir)

    if latest_cert is None:
        # Fallback: If no certificate exists, we cannot proceed as per strict requirements.
        # The task requires reading from T045/T045b outputs.
        raise FileNotFoundError(
            f"No calibration certificates found in {cert_dir}. "
            "Run T045 (calibration_protocol) and T045b (verification) first."
        )

    # 3. Validate Certificate
    logger.info(f"Validating certificate: {latest_cert.name}")
    cert_data = validate_certificate(latest_cert)

    # 4. Generate Log
    log_entry = generate_calibration_log(config, cert_data, latest_cert)

    # 5. Write Output
    output_path = get_processed_data_path() / OUTPUT_PATH
    write_calibration_log(log_entry, output_path)

    return log_entry


def main() -> int:
    """CLI entry point."""
    setup_logging(level=logging.INFO)
    try:
        result = run_calibration_log_generation()
        print(json.dumps(result, indent=2))
        return 0
    except (FileNotFoundError, ValueError, KeyError) as e:
        logger.error(f"Failed to generate calibration log: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())