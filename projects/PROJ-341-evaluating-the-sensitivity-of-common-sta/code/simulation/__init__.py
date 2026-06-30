"""
Simulation package initialization.
Provides a deterministic random seed manager to enforce reproducibility
across all modules in the simulation pipeline.
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, Union

# Import metadata schema from the data directory (T005)
# We assume the data directory is accessible relative to the project root.
# Since this is code, we will handle the path resolution dynamically or assume
# the script running it sets the working directory to the project root.
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
METADATA_FILE = os.path.join(DATA_DIR, "simulation_metadata.json")


class SeedManager:
    """
    Manages random seeds to ensure reproducibility across simulation runs.
    
    Features:
    - Generates a deterministic seed from a base seed and a unique run identifier.
    - Logs seed usage to simulation_metadata.json.
    - Provides a method to retrieve the seed for numpy, random, and torch (if available).
    """

    def __init__(self, base_seed: int = 42):
        """
        Initialize the SeedManager with a base seed.
        
        Args:
            base_seed (int): The master seed for the simulation run.
        """
        self.base_seed = base_seed
        self._run_id: Optional[str] = None
        self._current_seed: Optional[int] = None

    def initialize_run(self, run_id: Optional[str] = None) -> str:
        """
        Initialize a new simulation run.
        
        Generates a unique run ID if not provided, derives a specific seed for this run,
        and logs the event to the metadata file.
        
        Args:
            run_id (str, optional): A unique identifier for this run. If None, generated.
            
        Returns:
            str: The run ID used for this initialization.
        """
        if run_id is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            hash_input = f"{self.base_seed}-{timestamp}"
            self._run_id = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
        else:
            self._run_id = run_id

        # Derive a deterministic seed for this specific run based on base_seed and run_id
        # This ensures that the same base_seed + run_id always yields the same sequence
        seed_input = f"{self.base_seed}-{self._run_id}"
        self._current_seed = int(hashlib.sha256(seed_input.encode()).hexdigest(), 16) % (2**32)

        self._log_seed_entry()
        return self._run_id

    def get_seed(self) -> int:
        """
        Get the current seed for the active run.
        
        Returns:
            int: The deterministic seed for the current run.
            
        Raises:
            RuntimeError: If initialize_run has not been called yet.
        """
        if self._current_seed is None:
            raise RuntimeError("SeedManager not initialized. Call initialize_run() first.")
        return self._current_seed

    def reset(self) -> None:
        """
        Reset the manager state to allow a new run initialization.
        """
        self._current_seed = None
        # Keep run_id if we want to reuse it, but usually we want a fresh run
        # self._run_id = None 

    def _log_seed_entry(self) -> None:
        """
        Appends the current seed information to the simulation_metadata.json file.
        Creates the file and directory if they do not exist.
        """
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        metadata = {
            "seeds": []
        }
        
        # Load existing metadata if present
        if os.path.exists(METADATA_FILE):
            try:
                with open(METADATA_FILE, 'r') as f:
                    existing_data = json.load(f)
                    if "seeds" in existing_data:
                        metadata["seeds"] = existing_data["seeds"]
            except (json.JSONDecodeError, IOError):
                # If file is corrupted or unreadable, start fresh for this entry
                pass

        entry = {
            "run_id": self._run_id,
            "base_seed": self.base_seed,
            "derived_seed": self._current_seed,
            "timestamp": datetime.now().isoformat(),
            "status": "initialized"
        }
        
        metadata["seeds"].append(entry)

        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)


# Global singleton instance for convenience in modules
_seed_manager = SeedManager()

def set_base_seed(seed: int) -> None:
    """
    Update the base seed for the global manager.
    """
    _seed_manager.base_seed = seed

def get_seed_manager() -> SeedManager:
    """
    Retrieve the global SeedManager instance.
    """
    return _seed_manager

def initialize_simulation_run(run_id: Optional[str] = None) -> str:
    """
    Convenience function to initialize the global seed manager.
    """
    return _seed_manager.initialize_run(run_id)

def get_current_seed() -> int:
    """
    Convenience function to get the current seed from the global manager.
    """
    return _seed_manager.get_seed()