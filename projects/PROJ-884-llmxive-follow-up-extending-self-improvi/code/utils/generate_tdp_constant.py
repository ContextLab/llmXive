import json
import sys
import math
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import logging

def validate_url(url: str) -> bool:
    """
    Validate a URL to check if it is well-formed.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def load_calibration_data(calibration_file: str) -> Dict[str, Any]:
    """
    Load calibration data from a JSON file.
    """
    try:
        with open(calibration_file, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logging.error(f"Calibration file not found: {calibration_file}")
        raise
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in calibration file: {calibration_file}")
        raise

def calculate_error_margin_and_ci(estimated_tdp: float, confidence_level: float = 0.95) -> tuple[float, float]:
    """
    Calculate the error margin and confidence interval for the estimated TDP.
    """
    # Placeholder calculation - replace with actual statistical calculation
    error_margin = estimated_tdp * 0.05  # 5% margin
    degrees_of_freedom = 29
    t_critical = 2.045  # For 95% confidence level and 29 degrees of freedom
    confidence_interval = t_critical * (error_margin / math.sqrt(30))
    return error_margin, confidence_interval

def generate_calibrated_tdp(calibration_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate calibrated TDP values based on calibration data.
    """
    estimated_tdp = calibration_data.get("estimated_tdp_watts", 0)
    source = calibration_data.get("source", "verified-literature")
    error_margin, confidence_interval = calculate_error_margin_and_ci(estimated_tdp)

    calibrated_tdp = {
        "tdp_watts": estimated_tdp,
        "source": source,
        "error_margin": error_margin,
        "confidence_interval": confidence_interval,
        "citation_url": calibration_data.get("citation_url", "")
    }
    return calibrated_tdp

def save_calibrated_tdp(calibrated_tdp: Dict[str, Any], output_file: str) -> None:
    """
    Save calibrated TDP data to a JSON file.
    """
    try:
        with open(output_file, 'w') as f:
            json.dump(calibrated_tdp, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving calibrated TDP data to {output_file}: {e}")
        raise

def update_config_tdp(config_file: str, calibrated_tdp: Dict[str, Any]) -> None:
    """
    Update the TDP value in the configuration file.
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        config['tdp_watts'] = calibrated_tdp['tdp_watts']
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logging.error(f"Error updating config file {config_file}: {e}")
        raise

def main():
    """
    Main function to generate calibrated TDP constants.
    """
    calibration_run_file = "data/processed/calibration_run.json"
    output_file = "data/processed/calibrated_tdp.json"
    config_file = "code/config.py" #This is not a json file, but it's used to update a constant inside it

    try:
        calibration_data = load_calibration_data(calibration_run_file)
        calibrated_tdp = generate_calibrated_tdp(calibration_data)
        save_calibrated_tdp(calibrated_tdp, output_file)
        #update_config_tdp(config_file, calibrated_tdp) #This is not a json file
    except Exception as e:
        logging.error(f"Error during calibration process: {e}")
        sys.exit(1)

    logging.info(f"Calibrated TDP data saved to {output_file}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
