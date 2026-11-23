import os
import re
import logging
import sys
from typing import List, Dict, Optional, Tuple
import requests

def fix_seed(seed: int):
    """Fixes the random seed for reproducibility."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    import random
    random.seed(seed)
    import numpy as np
    np.random.seed(seed)

def get_cod_id_list():
    """Retrieves a list of COD IDs from the COD database."""
    # This is a placeholder - replace with actual logic to fetch COD IDs
    # For demonstration purposes, returning a small sample list
    return [
        "COD-1000025", "COD-1000039", "COD-1000047", "COD-1000065",
        "COD-1000081", "COD-1000097", "COD-1000112", "COD-1000123",
        "COD-1000144", "COD-1000156"
    ]

def check_cif_exists(cod_id: str, output_dir: str) -> bool:
    """Checks if a CIF file already exists for the given COD ID."""
    filepath = os.path.join(output_dir, f"{cod_id}.cif")
    return os.path.exists(filepath)

def extract_atom_count_from_cif(cif_file: str) -> int:
    """Extracts the number of atoms from a CIF file."""
    with open(cif_file, 'r') as f:
        content = f.read()
        # Use regex to find the _atom_site_count tag
        match = re.search(r'_atom_site_count\s+(\d+)', content)
        if match:
            return int(match.group(1))
        else:
            return 0  # Or raise an exception if atom count is essential

def download_cif(cod_id: str, output_dir: str, base_url: str = "http://www.ccdc.cam.ac.uk/fcf/"):
    """Downloads a CIF file from the Cambridge Crystallographic Data Centre (CCDC)."""
    file_url = f"{base_url}/cod/{cod_id}.cif"
    filepath = os.path.join(output_dir, f"{cod_id}.cif")

    try:
        response = requests.get(file_url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        with open(filepath, 'wb') as f:
            f.write(response.content)
        logging.info(f"Downloaded CIF file for {cod_id} to {filepath}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading CIF file for {cod_id}: {e}")
        return False

def main():
    """Main function to download organic CIFs."""
    fix_seed(42)
    output_dir = "data/raw_cif"
    os.makedirs(output_dir, exist_ok=True)

    cod_ids = get_cod_id_list()
    downloaded_count = 0

    for cod_id in cod_ids:
        if not check_cif_exists(cod_id, output_dir):
            atom_count = 0  # Initialize atom count. Won't be used if download fails
            if download_cif(cod_id, output_dir):
                atom_count = extract_atom_count_from_cif(os.path.join(output_dir, f"{cod_id}.cif"))
                if atom_count <= 50:
                    downloaded_count += 1
                    logging.info(f"Downloaded and validated {cod_id} with {atom_count} atoms.")
                else:
                    os.remove(os.path.join(output_dir, f"{cod_id}.cif"))  # Remove if too many atoms
                    logging.warning(f"Removing {cod_id} as it has more than 50 atoms ({atom_count}).")

    logging.info(f"Downloaded {downloaded_count} CIF files with <= 50 atoms.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()