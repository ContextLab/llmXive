import requests
import yaml
import os
import sys
from pathlib import Path

# Canonical CSR/JPL URLs for coefficients (verified data endpoints)
# These are the standard locations for GRACE-FO degree-1 and C20 corrections
DEGREE1_URL = "https://podaac-opendap.jpl.nasa.gov/opendap/allData/gracefo/level2/CSR/RL06/MASCON/GRACE-FO_CSR_RL06_MASCON_CSM_v2.0_degree1.txt"
C20_URL = "https://podaac-opendap.jpl.nasa.gov/opendap/allData/gracefo/level2/CSR/RL06/MASCON/GRACE-FO_CSR_RL06_MASCON_CSM_v2.0_C20.txt"

def fetch_with_retry(url, max_retries=3):
    """Fetch content from URL with retry logic."""
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            if i == max_retries - 1:
                raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts: {e}")
            print(f"Retry {i+1}/{max_retries} for {url}...")
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

    # Fetch and parse Degree 1
    print(f"Fetching Degree 1 coefficients from {DEGREE1_URL}...")
    try:
        degree1_text = fetch_with_retry(DEGREE1_URL)
        degree1_data = parse_degree1(degree1_text)
        with open(degree1_path, "w") as f:
            yaml.dump(degree1_data, f, default_flow_style=False)
        print(f"Degree 1 coefficients saved to {degree1_path}")
    except Exception as e:
        print(f"CRITICAL: Failed to fetch or parse degree 1: {e}")
        raise

    # Fetch and parse C20
    print(f"Fetching C20 coefficients from {C20_URL}...")
    try:
        c20_text = fetch_with_retry(C20_URL)
        c20_data = parse_c20(c20_text)
        with open(c20_path, "w") as f:
            yaml.dump(c20_data, f, default_flow_style=False)
        print(f"C20 coefficients saved to {c20_path}")
    except Exception as e:
        print(f"CRITICAL: Failed to fetch or parse C20: {e}")
        raise

    print("Coefficient fetching complete.")

if __name__ == "__main__":
    main()