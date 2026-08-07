import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from models.atomic_config import AtomicConfiguration
from logging_config import get_logger
from config.env_config import get_processed_dir, get_data_dir

logger = get_logger(__name__)

class ModeSelector:
    """
    Determines execution mode (Full vs Structure-Only) based on data availability.
    """
    def __init__(self, processed_dir: Path):
        self.processed_dir = processed_dir
        self.mode_config_path = processed_dir / "mode_config.json"

    def check_vdos_availability(self, config_ids: List[str]) -> Tuple[bool, List[str]]:
        """
        Check if VDOS data exists for the given configuration IDs.
        Returns (all_available, missing_ids).
        """
        missing_ids = []
        # In a real implementation, this would check a VDOS database or files.
        # For now, we assume VDOS is missing if not explicitly present in a manifest.
        # We'll simulate by checking a hypothetical vdos_manifest.json
        manifest_path = self.processed_dir / "vdos_manifest.json"
        
        if not manifest_path.exists():
            logger.warning("VDOS manifest not found. Assuming all VDOS missing.")
            return False, config_ids
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        available_ids = set(manifest.get('available_configs', []))
        
        for cid in config_ids:
            if cid not in available_ids:
                missing_ids.append(cid)
        
        return len(missing_ids) == 0, missing_ids

    def determine_mode(self, config_ids: List[str]) -> str:
        """
        Determine the execution mode.
        - 'Full': VDOS available for all configs.
        - 'Structure-Only': VDOS missing for some or all configs.
        """
        all_available, missing = self.check_vdos_availability(config_ids)
        
        if all_available:
            logger.info("All VDOS data available. Mode: Full")
            return 'Full'
        else:
            logger.warning(f"VDOS missing for {len(missing)} configs. Mode: Structure-Only")
            return 'Structure-Only'

    def save_mode_config(self, mode: str, missing_ids: List[str]) -> Path:
        """
        Save the mode configuration to a JSON file.
        """
        data = {
            'mode': mode,
            'missing_vdos_ids': missing_ids,
            'timestamp': str(Path.now()) if hasattr(Path, 'now') else 'N/A'
        }
        
        self.mode_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.mode_config_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Mode configuration saved to {self.mode_config_path}")
        return self.mode_config_path

def check_mode_selector(config_ids: List[str]) -> Dict[str, Any]:
    """
    Main entry point to check and determine mode.
    """
    processed_dir = get_processed_dir()
    selector = ModeSelector(processed_dir)
    
    mode = selector.determine_mode(config_ids)
    _, missing = selector.check_vdos_availability(config_ids)
    selector.save_mode_config(mode, missing)
    
    return {
        'mode': mode,
        'missing_vdos_count': len(missing),
        'missing_vdos_ids': missing
    }

def main():
    """
    Entry point for T007b-exec: Execution of Mode Selection.
    This should be called after download/validation to set the mode.
    """
    # This is a placeholder for execution logic.
    # In a real pipeline, this would be called with the list of validated config IDs.
    logger.info("Mode Selector logic defined. Execution requires validated config IDs.")
    return 0
