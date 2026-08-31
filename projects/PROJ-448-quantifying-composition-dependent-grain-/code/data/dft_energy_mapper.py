import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from code.config import DATA_RAW_PATH
from code.errors import DataLoadError

logger = logging.getLogger(__name__)

def load_dft_energies() -> Dict[str, Any]:
    """
    Load pre-computed DFT segregation energies from the verified source file.
    
    Returns:
        Dict containing the loaded DFT energy data.
        
    Raises:
        DataLoadError: If the file is missing, malformed, or contains no data.
    """
    dft_path = DATA_RAW_PATH / "dft_energies.json"
    
    if not dft_path.exists():
        # Check for the "no_data" placeholder created by T045f-Fetch or T018a
        no_data_path = DATA_RAW_PATH / "dft_energies_no_data.json"
        if no_data_path.exists():
            with open(no_data_path, 'r') as f:
                placeholder_data = json.load(f)
            if placeholder_data.get("status") == "no_data":
                logger.warning(f"DFT data source missing. Placeholder found: {placeholder_data.get('reason', 'unknown')}")
                # Raise a specific error to halt dependent tasks unless spec-amendment T018a is checked
                raise DataLoadError(f"No verified DFT source found: {placeholder_data.get('reason', 'unknown')}")
        raise DataLoadError(f"DFT energy file not found at {dft_path}")
    
    try:
        with open(dft_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataLoadError(f"Malformed JSON in DFT energy file: {e}")
    
    if not data:
        raise DataLoadError("DFT energy file is empty.")
        
    return data

def map_supercell_to_dft_energy(supercell_identifier: str, dft_data: Dict[str, Any]) -> Optional[float]:
    """
    Map a supercell identifier (e.g., 'sigma5_fe_cr.cif') to a DFT segregation energy.
    
    Args:
        supercell_identifier: The filename or key identifying the supercell (e.g., 'sigma5_fe_cr.cif').
        dft_data: The dictionary loaded from dft_energies.json.
        
    Returns:
        The segregation energy in eV if found, otherwise None.
        
    Raises:
        DataLoadError: If no matching entry is found in the DFT data.
    """
    # Normalize the identifier for lookup (remove extension if present)
    lookup_key = supercell_identifier
    if supercell_identifier.endswith('.cif'):
        lookup_key = supercell_identifier[:-4]
    
    # Attempt to find the energy in the data structure
    # Expected structure: {"systems": [{"system": "Fe-Cr", "energy_eV": 0.5, ...}]}
    # or flat: {"Fe-Cr": 0.5, ...}
    
    energy = None
    
    if isinstance(dft_data, dict):
        # Try direct key lookup first
        if lookup_key in dft_data:
            energy = dft_data[lookup_key]
        elif supercell_identifier in dft_data:
            energy = dft_data[supercell_identifier]
        else:
            # Try iterating if it's a list of dicts
            systems_list = dft_data.get("systems", dft_data.get("data", []))
            if isinstance(systems_list, list):
                for item in systems_list:
                    if isinstance(item, dict):
                        # Check common keys for system identification
                        sys_key = item.get("system") or item.get("system_name") or item.get("id")
                        if sys_key and (sys_key == lookup_key or sys_key == supercell_identifier):
                            energy = item.get("energy_eV")
                            break
    
    if energy is None:
        raise DataLoadError(
            f"No DFT energy found for supercell '{supercell_identifier}'. "
            f"Available keys in dataset: {list(dft_data.keys()) if isinstance(dft_data, dict) else 'list of items'}"
        )
        
    return float(energy)

def main():
    """
    CLI entry point to test the mapping logic.
    """
    logging.basicConfig(level=logging.INFO)
    
    try:
        logger.info("Loading DFT energies...")
        dft_data = load_dft_energies()
        logger.info(f"Loaded DFT data with keys: {list(dft_data.keys()) if isinstance(dft_data, dict) else 'list'}")
        
        # Test mapping with a known or example identifier
        # In a real run, this would come from gb_service.py output
        test_id = "sigma5_fe_cr.cif"
        logger.info(f"Attempting to map supercell: {test_id}")
        
        energy = map_supercell_to_dft_energy(test_id, dft_data)
        logger.info(f"Successfully mapped {test_id} to energy: {energy} eV")
        
    except DataLoadError as e:
        logger.error(f"Data loading or mapping failed: {e}")
        # Re-raise to ensure the pipeline fails loudly as required
        raise

if __name__ == "__main__":
    main()