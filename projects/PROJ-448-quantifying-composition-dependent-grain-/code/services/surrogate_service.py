"""
Task T013: Surrogate Service for Segregation Energy Calculation.

This service computes literature-calibrated segregation energies.
It MUST load REAL DFT energies from data/raw/dft_energies.json.
It MUST NOT implement or call any real DFT code.
It MUST raise a hard error if the data file is missing.
It MUST handle the fallback placeholder gracefully if the file exists but contains a 'MISSING_SOURCE' flag.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from code.config import DATA_RAW_PATH, get_logger
from code.errors import DataLoadError, ConfigurationError, SurrogateModelError

logger = get_logger(__name__)

class SurrogateService:
    """
    Service to manage and retrieve segregation energies based on DFT data.
    """
    
    def __init__(self):
        self._dft_data: Optional[Dict[str, Any]] = None
        self._is_fallback: bool = False
        self._load_data()

    def _load_data(self) -> None:
        """
        Load pre-computed DFT energies from data/raw/dft_energies.json.
        Enforces strict presence checks per T013 requirements.
        """
        dft_file_path = DATA_RAW_PATH / "dft_energies.json"

        if not dft_file_path.exists():
            # Per T013: "If `data/raw/dft_energies.json` is missing, raise a hard error."
            error_msg = f"Critical Error: Required DFT data file not found at {dft_file_path}. " \
                        "The pipeline cannot proceed without real DFT energies or a valid fallback placeholder."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        logger.info(f"Loading DFT energies from {dft_file_path}")
        try:
            with open(dft_file_path, 'r') as f:
                self._dft_data = json.load(f)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse DFT energies JSON: {e}"
            logger.error(error_msg)
            raise DataLoadError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error loading DFT energies: {e}"
            logger.error(error_msg)
            raise DataLoadError(error_msg)

        # Check for fallback flag per T013-Exec requirements
        if self._dft_data.get("MISSING_SOURCE", False):
            logger.warning("Data missing: using fallback placeholder. DFT energies will be treated as unavailable.")
            self._is_fallback = True
            self._dft_data = None # Clear data to signal unavailability to callers
        else:
            logger.info("Real DFT data loaded successfully.")
            self._is_fallback = False

    def get_segregation_energy(self, system: str, temperature: float) -> Optional[float]:
        """
        Retrieve the segregation energy for a given system and temperature.
        
        Args:
            system: System name (e.g., "Fe-Cr-Mo").
            temperature: Temperature in Kelvin.
        
        Returns:
            Segregation energy in eV, or None if data is unavailable (including fallback mode).
        
        Raises:
            SurrogateModelError: If called in fallback mode and data is required.
        """
        if self._is_fallback or self._dft_data is None:
            logger.warning(f"Cannot retrieve energy for {system}: Data source is missing/fallback.")
            return None

        # Lookup logic:
        # Expected structure:
        # {
        #   "systems": {
        #     "Fe-Cr": { "energies": { "500": 0.1, "600": 0.09, ... } },
        #     "Fe-Cr-Mo": { ... }
        #   }
        # }
        
        systems_data = self._dft_data.get("systems", self._dft_data)
        
        if system not in systems_data:
            logger.warning(f"System {system} not found in DFT data.")
            return None

        system_entry = systems_data[system]
        energies = system_entry.get("energies", {})
        
        # Find closest temperature
        closest_temp = None
        min_diff = float('inf')
        target_energy = None

        for temp_str, energy_val in energies.items():
            try:
                t_val = float(temp_str)
                diff = abs(t_val - temperature)
                if diff < min_diff:
                    min_diff = diff
                    closest_temp = t_val
                    target_energy = energy_val
            except ValueError:
                continue

        if target_energy is not None:
            logger.debug(f"Found energy {target_energy} eV for {system} at approx {closest_temp}K (target {temperature}K)")
            return target_energy
        
        logger.warning(f"No energy data found for {system} near {temperature}K")
        return None

    def get_all_energies(self, system: str) -> Dict[str, float]:
        """Get all available energies for a system."""
        if self._is_fallback or self._dft_data is None:
            return {}
        
        systems_data = self._dft_data.get("systems", self._dft_data)
        if system not in systems_data:
            return {}
        
        return systems_data[system].get("energies", {})

def main():
    """Test entry point for T013 verification."""
    try:
        service = SurrogateService()
        test_systems = ["Fe-Cr-Mo", "Fe-Cr", "NonExistent"]
        logger.info("Running T013 surrogate service verification...")
        
        for sys_name in test_systems:
            energy = service.get_segregation_energy(sys_name, 600.0)
            if energy is not None:
                print(f"{sys_name} @ 600K: {energy} eV")
            else:
                print(f"{sys_name} @ 600K: No data available")
        
        logger.info("T013 verification complete.")
    except FileNotFoundError as e:
        logger.critical(f"T013 Failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"T013 Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()