import os
import sys
import hashlib
from pathlib import Path
import logging
from urllib.request import urlretrieve

def calculate_file_checksum(filepath):
    """Calculates the SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def fetch_thermo_proxy(url, filepath):
    """Downloads the thermodynamic proxy from the given URL to the specified filepath."""
    try:
        logging.info(f"Downloading TCFE.tdb from {url} to {filepath}")
        urlretrieve(url, filepath)
        logging.info("Download complete.")
        return True
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return False

def validate_ternary_parameters(filepath):
    """Validates that the TCFE.tdb file contains ternary parameters for Fe-Cr-Mo, Fe-Cr-V, Fe-Mo-V, Fe-Cr-W, and Fe-Mo-W."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        ternary_systems = ["Fe-Cr-Mo", "Fe-Cr-V", "Fe-Mo-V", "Fe-Cr-W", "Fe-Mo-W"]
        missing_parameters = []

        for system in ternary_systems:
            if system not in content:
                missing_parameters.append(system)

        if missing_parameters:
            error_message = f"Missing ternary parameters for systems: {', '.join(missing_parameters)}"
            logging.error(error_message)
            raise ValueError(error_message) 
        else:
            logging.info("All required ternary parameters found.")
            return True

    except Exception as e:
        logging.error(f"Error validating ternary parameters: {e}")
        return False

def main():
    """Main function to download and validate the TCFE.tdb file."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    url = "https://openalloyfoundation.org/data/TCFE.tdb"  # Replace with the actual URL
    filepath = Path("data/raw/TCFE.tdb")
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if fetch_thermo_proxy(url, filepath):
        try:
            validate_ternary_parameters(filepath)
            print("TCFE.tdb download and validation successful.")
        except ValueError as e:
            logging.error(f"Validation failed: {e}")
            sys.exit(1)  # Exit with an error code if validation fails

    else:
        sys.exit(1) #Exit with an error code for download failure

if __name__ == "__main__":
    main()
