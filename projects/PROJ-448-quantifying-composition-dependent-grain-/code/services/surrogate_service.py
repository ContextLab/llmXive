"""
Task T013: Surrogate Service for Segregation Energy Calculation.

This service computes literature-calibrated segregation energies.
It MUST load REAL DFT energies from data/raw/dft_energies.json (or placeholders per T018a).
It MUST NOT implement or call any real DFT code.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from code.config import DATA_RAW_PATH, get_logger
from code.errors import DataLoadError, ConfigurationError
from code.models.mclean import McLeanResult

logger = get_logger(__name__)

class SurrogateService:
    """
    Service to manage and retrieve segregation energies based on DFT data.
    """
    
    def __init__(self):
        self._dft_data: Optional[Dict[str, Any]] = None
        self._load_data()

    def _load_data(self) -> None:
        """
        Load pre-computed DFT energies from data/raw/dft_energies.json.
        Handles placeholders per T018a.
        """
        dft_file_path = DATA_RAW_PATH / "dft_energies.json"
        placeholder_path = DATA_RAW_PATH / "dft_energies_no_data.json"

        if dft_file_path.exists():
            logger.info(f"Loading DFT energies from {dft_file_path}")
            try:
                with open(dft_file_path, 'r') as f:
                    self._dft_data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse DFT energies JSON: {e}")
                raise DataLoadError("Invalid DFT energies JSON format")
            except Exception as e:
                logger.error(f"Unexpected error loading DFT energies: {e}")
                raise DataLoadError(f"Error loading DFT energies: {e}")
        elif placeholder_path.exists():
            logger.warning(f"Real DFT data not found. Loading placeholder from {placeholder_path}")
            try:
                with open(placeholder_path, 'r') as f:
                    placeholder_data = json.load(f)
                if placeholder_data.get("status") == "no_data":
                    logger.warning(f"Placeholder indicates no data: {placeholder_data.get('reason')}")
                    self._dft_data = None # Explicitly set to None to signal no data
                else:
                    self._dft_data = placeholder_data
            except Exception as e:
                logger.error(f"Failed to parse placeholder file: {e}")
                raise DataLoadError("Invalid placeholder file")
        else:
            # Per T018a, we might not raise a hard error if the spec amendment is active,
            # but for the core logic, we need data. If neither exists, we treat it as no data.
            logger.warning(f"Neither DFT data nor placeholder found at {dft_file_path} or {placeholder_path}")
            self._dft_data = None

    def get_segregation_energy(self, system: str, temperature: float) -> Optional[float]:
        """
        Retrieve the segregation energy for a given system and temperature.
        
        Args:
            system: System name (e.g., "Fe-Cr-Mo").
            temperature: Temperature in Kelvin.
        
        Returns:
            Segregation energy in eV, or None if data is unavailable.
        """
        if self._dft_data is None:
            logger.warning(f"No DFT data available for system {system}. Returning None.")
            return None

        # Lookup logic:
        # The JSON structure is expected to be:
        # {
        #   "systems": {
        #     "Fe-Cr": { "energies": { "500": 0.1, "600": 0.09, ... } },
        #     "Fe-Cr-Mo": { ... }
        #   }
        # }
        # or a flat list. We adapt to the most common structure found in T045f-Fetch.
        
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
        if self._dft_data is None:
            return {}
        
        systems_data = self._dft_data.get("systems", self._dft_data)
        if system not in systems_data:
            return {}
        
        return systems_data[system].get("energies", {})

def main():
    """Test entry point."""
    service = SurrogateService()
    test_systems = ["Fe-Cr-Mo", "Fe-Cr", "NonExistent"]
    for sys_name in test_systems:
        energy = service.get_segregation_energy(sys_name, 600.0)
        print(f"{sys_name} @ 600K: {energy} eV")

if __name__ == "__main__":
    main()