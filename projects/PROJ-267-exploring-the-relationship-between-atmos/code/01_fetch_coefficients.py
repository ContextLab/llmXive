import requests
import yaml
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """Load verified URLs from config/urls.yaml."""
    config_path = Path("config/urls.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}. "
                                "Run T007e to populate URLs before running this script.")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Expected structure based on T007e
    urls = config.get('urls', {})
    degree1_url = urls.get('gracefo_degree1')
    c20_url = urls.get('gracefo_c20')
    
    if not degree1_url or not c20_url:
        raise ValueError("Missing required URLs in config/urls.yaml: "
                         "gracefo_degree1 and gracefo_c20 must be defined.")
    
    return degree1_url, c20_url

def fetch_with_retry(url, max_retries=3, timeout=30):
    """Fetch content from URL with retry logic."""
    for i in range(max_retries):
        try:
            logger.info(f"Fetching {url} (attempt {i+1}/{max_retries})...")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            if i == max_retries - 1:
                raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts: {e}")
            logger.warning(f"Retry {i+1}/{max_retries} for {url} due to: {e}")
            continue

def parse_degree1(text):
    """
    Parse degree-1 coefficients from text.
    Expected format: "x y z" values, typically one line of interest or header.
    We look for the first valid line with 3 float values.
    """
    lines = text.strip().split('\n')
    for line in lines:
        parts = line.split()
        if len(parts) >= 3:
            try:
                x = float(parts[0])
                y = float(parts[1])
                z = float(parts[2])
                return {"x": x, "y": y, "z": z}
            except ValueError:
                continue
    raise ValueError("Could not parse valid Degree 1 data (x, y, z floats) from content.")

def parse_c20(text):
    """
    Parse C20 coefficient from text.
    Expected format: "value uncertainty"
    """
    lines = text.strip().split('\n')
    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            try:
                value = float(parts[0])
                uncertainty = float(parts[1])
                return {"value": value, "uncertainty": uncertainty}
            except ValueError:
                continue
    raise ValueError("Could not parse valid C20 data (value, uncertainty floats) from content.")

def main():
    # Ensure output directory exists
    coeffs_dir = Path("coeffs")
    coeffs_dir.mkdir(exist_ok=True)

    degree1_path = coeffs_dir / "degree1.yaml"
    c20_path = coeffs_dir / "c20.yaml"

    # Load verified URLs
    try:
        degree1_url, c20_url = load_config()
    except (FileNotFoundError, ValueError) as e:
        logger.critical(str(e))
        raise

    # Fetch and parse Degree 1
    logger.info(f"Fetching Degree 1 coefficients from {degree1_url}...")
    try:
        degree1_text = fetch_with_retry(degree1_url)
        degree1_data = parse_degree1(degree1_text)
        with open(degree1_path, "w") as f:
            yaml.dump(degree1_data, f, default_flow_style=False)
        logger.info(f"Degree 1 coefficients saved to {degree1_path}")
    except Exception as e:
        logger.critical(f"Failed to fetch or parse degree 1: {e}")
        raise

    # Fetch and parse C20
    logger.info(f"Fetching C20 coefficients from {c20_url}...")
    try:
        c20_text = fetch_with_retry(c20_url)
        c20_data = parse_c20(c20_text)
        with open(c20_path, "w") as f:
            yaml.dump(c20_data, f, default_flow_style=False)
        logger.info(f"C20 coefficients saved to {c20_path}")
    except Exception as e:
        logger.critical(f"Failed to fetch or parse C20: {e}")
        raise

    logger.info("Coefficient fetching complete.")

if __name__ == "__main__":
    main()