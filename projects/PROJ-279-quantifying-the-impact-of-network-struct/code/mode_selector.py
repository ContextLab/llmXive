"""
Mode selector module to determine execution mode (Full vs Structure-Only).

Implements T007b logic.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from models.atomic_config import AtomicConfiguration
from logging_config import get_logger

logger = get_logger(__name__)

MODE_FULL = "Full"
MODE_STRUCTURE_ONLY = "Structure-Only"


class ModeSelector:
    """
    Determines the execution mode based on available data.
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
    
    def check_vdos_availability(self, config_id: str) -> bool:
        """
        Check if VDOS data exists for a configuration.
        
        In a real scenario, this would check for pre-calculated VDOS files.
        For this implementation, we assume VDOS is missing (triggering Structure-Only mode).
        """
        # Placeholder: assume VDOS is missing
        logger.info(f"VDOS check for {config_id}: Missing (Structure-Only mode)")
        return False
    
    def determine_mode(self, configs: List[AtomicConfiguration]) -> Tuple[str, Dict[str, Any]]:
        """
        Determine the execution mode.
        
        Returns:
            Tuple of (mode, metadata)
        """
        has_vdos = False
        for config in configs:
            if self.check_vdos_availability(config.id):
                has_vdos = True
                break
        
        if has_vdos:
            mode = MODE_FULL
            logger.info("Mode: Full (VDOS available)")
        else:
            mode = MODE_STRUCTURE_ONLY
            logger.info("Mode: Structure-Only (VDOS missing)")
        
        metadata = {
            "mode": mode,
            "vdos_available": has_vdos,
            "reason": "VDOS data missing for all configurations" if not has_vdos else "VDOS data available"
        }
        
        return mode, metadata


def check_mode_selector(configs: List[AtomicConfiguration], data_dir: Path) -> Dict[str, Any]:
    """
    Convenience function to run mode selection.
    """
    selector = ModeSelector(data_dir)
    mode, metadata = selector.determine_mode(configs)
    
    output_path = Path(data_dir) / "processed" / "mode_config.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Mode selection complete: {mode}. Saved to {output_path}")
    return metadata


if __name__ == "__main__":
    # Example usage
    from models.atomic_config import AtomicConfiguration
    from ase.build import bulk
    
    atoms = bulk('Si', 'diamond', a=5.43, cubic=True)
    configs = [AtomicConfiguration(id="test", atoms=atoms, source="mock_zenodo", size=8)]
    
    metadata = check_mode_selector(configs, Path("data"))
    print(f"Mode: {metadata['mode']}")
