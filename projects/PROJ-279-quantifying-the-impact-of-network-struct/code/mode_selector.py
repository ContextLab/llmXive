"""
Mode Selection Logic for Heat Transport Pipeline.

This module implements the logic to determine the execution mode of the pipeline
based on the availability of pre-calculated VDOS (Vibrational Density of States)
and thermal conductivity (k) data.

Modes:
- 'Full': Both VDOS and k are available. Full analysis (US2 + US3) can proceed.
- 'Structure-Only': VDOS/k missing. Only topological analysis (US1 + US2 descriptors) proceeds.
- 'Unusable': No valid configuration data found.

This task (T007b) defines the logic. Execution (T007b-exec) is deferred to Phase 3.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from models.atomic_config import AtomicConfiguration
from logging_config import get_logger
from config.env_config import get_processed_dir, get_data_dir

# Constants for mode names
MODE_FULL = "Full"
MODE_STRUCTURE_ONLY = "Structure-Only"
MODE_UNUSABLE = "Unusable"

# Output path for the mode configuration (used in T007b-exec)
# Defined here for consistency, though execution is deferred.
MODE_CONFIG_PATH = Path("data/processed/mode_config.json")


class ModeSelector:
    """
    Determines the pipeline execution mode based on data availability.

    This class checks for the presence of VDOS and thermal conductivity data
    to decide if the pipeline should run in 'Full' mode or 'Structure-Only' mode.
    """

    def __init__(self, raw_data_dir: Optional[Path] = None, processed_dir: Optional[Path] = None):
        """
        Initialize the ModeSelector.

        Args:
            raw_data_dir: Path to the raw data directory. Defaults to env config.
            processed_dir: Path to the processed data directory. Defaults to env config.
        """
        self.raw_data_dir = raw_data_dir or get_data_dir()
        self.processed_dir = processed_dir or get_processed_dir()
        self.logger = get_logger(__name__)

    def check_vdos_availability(self, config_ids: List[str]) -> Dict[str, bool]:
        """
        Check which configurations have pre-calculated VDOS data available.

        Args:
            config_ids: List of configuration IDs to check.

        Returns:
            Dictionary mapping config_id to boolean availability.
        """
        availability = {}
        # In a real implementation, this would check for specific VDOS files
        # e.g., f"vdos_{config_id}.npy" or entries in a manifest.
        # For now, we assume the check is against a manifest or directory structure.
        
        vdos_manifest_path = self.processed_dir / "vdos_manifest.json"
        
        if not vdos_manifest_path.exists():
            self.logger.warning(f"VDOS manifest not found at {vdos_manifest_path}. Assuming no VDOS data available.")
            return {cid: False for cid in config_ids}

        try:
            with open(vdos_manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Expecting manifest to be a dict or list of available IDs
            available_ids = set(manifest.keys()) if isinstance(manifest, dict) else set(manifest)
            
            for cid in config_ids:
                availability[cid] = cid in available_ids
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Failed to read VDOS manifest: {e}")
            return {cid: False for cid in config_ids}

        return availability

    def check_k_availability(self, config_ids: List[str]) -> Dict[str, bool]:
        """
        Check which configurations have thermal conductivity (k) data available.

        Args:
            config_ids: List of configuration IDs to check.

        Returns:
            Dictionary mapping config_id to boolean availability.
        """
        availability = {}
        
        # Check for a metadata file or specific k-data files
        metadata_path = self.processed_dir / "metadata_k.json"
        
        if not metadata_path.exists():
            self.logger.warning(f"Thermal conductivity metadata not found at {metadata_path}. Assuming no k data available.")
            return {cid: False for cid in config_ids}

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            available_ids = set(metadata.keys()) if isinstance(metadata, dict) else set(metadata)
            
            for cid in config_ids:
                availability[cid] = cid in available_ids
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Failed to read thermal conductivity metadata: {e}")
            return {cid: False for cid in config_ids}

        return availability

    def determine_mode(self, config_ids: List[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Determine the pipeline execution mode.

        Logic:
        - If ALL configs have both VDOS and k -> 'Full'
        - If SOME or NONE have VDOS/k -> 'Structure-Only' (if at least one valid config exists)
        - If NO valid configs -> 'Unusable'

        Args:
            config_ids: List of configuration IDs to evaluate.

        Returns:
            Tuple of (mode_string, details_dict).
        """
        if not config_ids:
            return MODE_UNUSABLE, {"reason": "No configuration IDs provided."}

        vdos_status = self.check_vdos_availability(config_ids)
        k_status = self.check_k_availability(config_ids)

        vdos_count = sum(1 for v in vdos_status.values() if v)
        k_count = sum(1 for v in k_status.values() if v)
        total = len(config_ids)

        details = {
            "total_configs": total,
            "vdos_available_count": vdos_count,
            "k_available_count": k_count,
            "vdos_missing_ids": [cid for cid, has_v in vdos_status.items() if not has_v],
            "k_missing_ids": [cid for cid, has_k in k_status.items() if not has_k]
        }

        if vdos_count == total and k_count == total:
            mode = MODE_FULL
            reason = "All configurations have complete VDOS and thermal conductivity data."
        else:
            mode = MODE_STRUCTURE_ONLY
            reason = "VDOS or thermal conductivity data is missing for some or all configurations. Switching to Structure-Only mode."

        details["mode"] = mode
        details["reason"] = reason
        
        self.logger.info(f"Mode determined: {mode} - {reason}")

        return mode, details


def check_mode_selector(config_ids: List[str], output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Convenience function to run mode selection and optionally save the result.

    Args:
        config_ids: List of configuration IDs to check.
        output_path: Optional path to save the mode_config.json. If None, does not save.

    Returns:
        Dictionary containing the mode and details.
    """
    selector = ModeSelector()
    mode, details = selector.determine_mode(config_ids)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(details, f, indent=2)
        logging.info(f"Mode configuration saved to {output_path}")

    return details


def main():
    """
    Main entry point for T007b execution (Definition only).
    
    Note: This function is intended to be called by the execution task (T007b-exec)
    once data is downloaded. As per T007b requirements, this task defines the logic
    but does not run it against real data until the data exists.
    
    However, to satisfy the "Definition Only" requirement and allow testing of the logic,
    we provide a dry-run structure that would execute if data were present.
    """
    logger = get_logger(__name__)
    logger.info("Mode Selector Logic Initialized (Definition Only - T007b)")
    logger.info("Execution deferred to Phase 3 (T007b-exec) when data is available.")
    
    # Example of how this would be called in T007b-exec:
    # config_ids = [...] # From validation report
    # selector = ModeSelector()
    # mode, details = selector.determine_mode(config_ids)
    # save to data/processed/mode_config.json
    
    return {"status": "logic_defined", "mode_selector_class": "ModeSelector"}


if __name__ == "__main__":
    main()