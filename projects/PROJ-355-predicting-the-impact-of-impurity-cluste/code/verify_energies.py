import os
import sys
import logging
import pandas as pd
from pathlib import Path
from config import get_project_root, get_data_paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_segregation_energies(input_path: Path) -> bool:
    """
    Verifies that segregation energies are non-empty and valid.
    """
    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
        return False
    
    df = pd.read_csv(input_path)
    if df.empty:
        logger.error("Energy file is empty.")
        return False
    
    if 'segregation_energy' not in df.columns:
        logger.error("Missing 'segregation_energy' column.")
        return False
    
    logger.info(f"Verified {len(df)} energy entries.")
    return True

def main():
    """
    Main entry point for the verify energies script.
    """
    logger.info("Verifying segregation energies...")
    data_paths = get_data_paths()
    energy_path = data_paths['processed'] / "segregation_energies.csv"
    if verify_segregation_energies(energy_path):
        print("Verification successful.")
        return 0
    else:
        print("Verification failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())