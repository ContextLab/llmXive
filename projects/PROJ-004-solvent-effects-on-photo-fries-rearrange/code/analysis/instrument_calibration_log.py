"""Instrument Calibration Log Generation.

Generates a machine-readable calibration log for the transient absorption
spectrometer, aggregating instrument configuration and calibration certificate
data.

Dependencies:
    - T035 (Instrument Registry): Provides instrument configuration.
    - T045 (Calibration Protocol): Generates calibration certificates.
    - T045b (Calibration Verification): Ensures certificates are valid.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from project modules
from config import get_chemicals_path, get_processed_data_path
from data.loaders import SolventDataError  # Reusing import structure if needed, or direct yaml load
from utils.logging import setup_logging, log_operation, get_logger

# Local imports for specific logic
import yaml

# Constants
INSTRUMENT_CONFIG_PATH = "data/chemicals/instrument_config.yaml"
CERTIFICATES_DIR = "data/processed/calibration_certificates"
OUTPUT_PATH = "data/processed/instrument_calibration_log.json"

logger = get_logger(__name__)


def load_instrument_config() -> Dict[str, Any]:
    """Load instrument configuration from the YAML file.

    Returns:
        Dictionary containing instrument model, detector type, and detection limit.

    Raises:
        FileNotFoundError: If the instrument config file is missing.
        ValueError: If required fields are missing from the config.
    """
    config_path = Path(INSTRUMENT_CONFIG_PATH)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Instrument configuration file not found at {config_path}. "
            "Ensure T035 has been executed and data/chemicals/instrument_config.yaml exists."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    required_fields = ["instrument_model", "detector_type", "detection_limit_absorbance"]
    missing = [field for field in required_fields if field not in config]
    if missing:
        raise ValueError(
            f"Instrument configuration missing required fields: {missing}. "
            "Update data/chemicals/instrument_config.yaml with these fields."
        )

    return config


def find_latest_certificate() -> Optional[Dict[str, Any]]:
    """Find the most recent valid calibration certificate.

    Iterates through the calibration certificates directory to find the latest
    JSON certificate file.

    Returns:
        Dictionary containing certificate data, or None if no certificates found.
    """
    certs_dir = Path(CERTIFICATES_DIR)
    if not certs_dir.exists():
        logger.warning(f"Calibration certificates directory not found at {certs_dir}")
        return None

    cert_files = list(certs_dir.glob("*_cert.json"))
    if not cert_files:
        logger.warning("No calibration certificates found in the directory.")
        return None

    # Sort by modification time (newest first) or filename if dates are consistent
    # Assuming filenames or content contain ISO dates for sorting
    latest_cert = None
    latest_time = datetime.min.replace(tzinfo=timezone.utc)

    for cert_file in cert_files:
        try:
            with open(cert_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Extract date from filename or content
            # Filename format: {run_id}_cert.json or similar
            # Content should have 'calibration_date'
            cert_date_str = data.get("calibration_date", "")
            if cert_date_str:
                try:
                    # Parse ISO 8601 date
                    cert_date = datetime.fromisoformat(cert_date_str.replace('Z', '+00:00'))
                except ValueError:
                    # Fallback to file modification time
                    cert_date = datetime.fromtimestamp(cert_file.stat().st_mtime, tz=timezone.utc)
            else:
                cert_date = datetime.fromtimestamp(cert_file.stat().st_mtime, tz=timezone.utc)

            if cert_date > latest_time:
                latest_time = cert_date
                latest_cert = data
                latest_cert["_source_file"] = cert_file.name
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Skipping invalid certificate {cert_file.name}: {e}")
            continue

    return latest_cert


def validate_certificate(cert_data: Dict[str, Any]) -> bool:
    """Validate that a certificate contains necessary fields.

    Args:
        cert_data: Dictionary containing certificate data.

    Returns:
        True if valid, False otherwise.
    """
    required_fields = ["calibration_date", "calibration_standard_hash", "operator_id"]
    missing = [field for field in required_fields if field not in cert_data]
    if missing:
        logger.warning(f"Certificate missing fields: {missing}")
        return False
    return True


def generate_calibration_log(instrument_config: Dict[str, Any], certificate: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate the calibration log dictionary.

    Args:
        instrument_config: The loaded instrument configuration.
        certificate: The latest valid calibration certificate, or None.

    Returns:
        Dictionary representing the calibration log.
    """
    log_entry = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "instrument_model": instrument_config.get("instrument_model"),
        "detector_type": instrument_config.get("detector_type"),
        "detection_limit_absorbance": instrument_config.get("detection_limit_absorbance"),
        "calibration_status": "valid" if certificate else "missing",
    }

    if certificate:
        if validate_certificate(certificate):
            log_entry["calibration_date"] = certificate.get("calibration_date")
            log_entry["calibration_standard_hash"] = certificate.get("calibration_standard_hash")
            log_entry["operator_id"] = certificate.get("operator_id")
            log_entry["calibration_certificate_path"] = certificate.get("_source_file", "unknown")
        else:
            log_entry["calibration_status"] = "invalid"
            log_entry["calibration_certificate_path"] = certificate.get("_source_file", "unknown")
    else:
        log_entry["calibration_date"] = None
        log_entry["calibration_standard_hash"] = None
        log_entry["operator_id"] = None
        log_entry["calibration_certificate_path"] = None
        log_entry["warning"] = "No valid calibration certificate found. Run T045 to generate certificates."

    return log_entry


def write_calibration_log(log_data: Dict[str, Any], output_path: str = OUTPUT_PATH) -> None:
    """Write the calibration log to a JSON file.

    Args:
        log_data: The calibration log dictionary.
        output_path: Path to the output JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Calibration log written to {output_file}")


def run_calibration_log_generation() -> Dict[str, Any]:
    """Main execution function to generate the calibration log.

    Returns:
        The generated calibration log dictionary.
    """
    log_operation("start_calibration_log_generation")
    try:
        # 1. Load Instrument Config
        instrument_config = load_instrument_config()
        logger.info(f"Loaded instrument config: {instrument_config['instrument_model']}")

        # 2. Find Latest Certificate
        certificate = find_latest_certificate()
        if certificate:
            logger.info(f"Found latest certificate: {certificate.get('calibration_date')}")
        else:
            logger.warning("No calibration certificate found.")

        # 3. Generate Log
        log_data = generate_calibration_log(instrument_config, certificate)

        # 4. Write Output
        write_calibration_log(log_data)

        log_operation("finish_calibration_log_generation", status="success")
        return log_data

    except FileNotFoundError as e:
        log_operation("finish_calibration_log_generation", status="error", error=str(e))
        raise
    except Exception as e:
        log_operation("finish_calibration_log_generation", status="error", error=str(e))
        raise


def main() -> None:
    """CLI entry point."""
    setup_logging(level=logging.INFO)
    try:
        run_calibration_log_generation()
    except Exception as e:
        logger.error(f"Failed to generate calibration log: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()